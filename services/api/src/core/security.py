"""
MSGI One — Cryptographic Security, JWT Verification, Session Revocation & Rate Limiting
Supports HS256 (HMAC) and RS256/ES256 (JWKS or configured public key).
Zero unverified signature fallbacks.
Principles: Sommerville Security Engineering, Saltzer & Schroeder Complete Mediation.
"""

from collections import defaultdict, deque
import hashlib
import re
import time
from typing import Any, Deque, Dict, Optional
import jwt
from fastapi import HTTPException, Request, status
from src.core.config import settings

ALLOWED_ALGORITHMS = ["HS256", "RS256", "ES256"]

_jwks_client: Optional[jwt.PyJWKClient] = None
# In-memory session revocation store: token_id_or_hash -> expiry_epoch
_REVOKED_TOKENS: Dict[str, float] = {}


def get_jwks_client() -> Optional[jwt.PyJWKClient]:
    global _jwks_client
    if _jwks_client is None and settings.SUPABASE_URL and not settings.SUPABASE_URL.startswith("https://placeholder"):
        try:
            jwks_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
            _jwks_client = jwt.PyJWKClient(jwks_url, cache_jwk_set=True, lifespan=3600)
        except Exception:
            _jwks_client = None
    return _jwks_client


def _token_revocation_key(token: str, claims: Optional[Dict[str, Any]] = None) -> str:
    if claims and claims.get("jti"):
        return f"jti:{claims['jti']}"
    return f"sha256:{hashlib.sha256(token.encode('utf-8')).hexdigest()}"


def revoke_token(token: str, claims: Optional[Dict[str, Any]] = None) -> str:
    """Revoke a session JWT until its natural expiration."""
    key = _token_revocation_key(token, claims)
    exp = float(claims.get("exp", time.time() + 86400)) if claims else time.time() + 86400
    _REVOKED_TOKENS[key] = exp
    return key


def is_token_revoked(token: str, claims: Optional[Dict[str, Any]] = None) -> bool:
    now = time.time()
    # Prune expired revocations opportunistically
    expired = [k for k, exp in _REVOKED_TOKENS.items() if exp <= now]
    for k in expired:
        _REVOKED_TOKENS.pop(k, None)

    raw_key = f"sha256:{hashlib.sha256(token.encode('utf-8')).hexdigest()}"
    if raw_key in _REVOKED_TOKENS:
        return True
    if claims and claims.get("jti"):
        if f"jti:{claims['jti']}" in _REVOKED_TOKENS:
            return True
    return False


def clear_revoked_tokens() -> None:
    _REVOKED_TOKENS.clear()


def verify_jwt_token(token: str) -> Dict[str, Any]:
    """
    Cryptographically verify incoming Supabase JWT token.
    Validates:
      1. Signature using configured Supabase signing scheme (HS256, RS256, or ES256).
         NEVER falls back to unverified decoding.
      2. Algorithm header (strictly rejects 'none' or unapproved algorithms).
      3. Standard claims: expiration (exp), audience (aud), subject (sub), and issuer (iss) when present.
      4. Session revocation status.
    """
    if not token or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "UNAUTHENTICATED",
                "message": "Bearer authentication token is missing or empty.",
            },
        )

    try:
        unverified_headers = jwt.get_unverified_header(token)
        algorithm = unverified_headers.get("alg")

        if not algorithm or algorithm not in ALLOWED_ALGORITHMS:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "INVALID_TOKEN_ALGORITHM",
                    "message": f"Unsupported or prohibited JWT algorithm: {algorithm}. Only {ALLOWED_ALGORITHMS} are permitted.",
                },
            )

        decode_options: Dict[str, Any] = {
            "verify_signature": True,
            "verify_exp": True,
            "verify_aud": True,
            "require": ["exp", "sub", "aud"],
        }

        expected_issuer: Optional[str] = None
        if settings.SUPABASE_URL and not settings.SUPABASE_URL.startswith("https://placeholder"):
            expected_issuer = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1"

        if algorithm in ("ES256", "RS256"):
            verification_key: Any = None
            client = get_jwks_client()
            if client is not None:
                try:
                    signing_key = client.get_signing_key_from_jwt(token)
                    verification_key = signing_key.key
                except Exception as jwks_err:
                    if settings.SUPABASE_JWT_PUBLIC_KEY:
                        verification_key = settings.SUPABASE_JWT_PUBLIC_KEY
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={
                                "code": "INVALID_SIGNATURE",
                                "message": f"Asymmetric JWT verification failed: {jwks_err}",
                            },
                        )
            elif settings.SUPABASE_JWT_PUBLIC_KEY:
                verification_key = settings.SUPABASE_JWT_PUBLIC_KEY
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "code": "JWKS_UNAVAILABLE",
                        "message": "No JWKS endpoint or asymmetric public key configured for RS256/ES256 verification.",
                    },
                )

            payload = jwt.decode(
                token,
                verification_key,
                algorithms=[algorithm],
                audience=settings.JWT_AUDIENCE,
                issuer=expected_issuer if settings.JWT_REQUIRE_ISSUER else None,
                options=decode_options,
            )
        elif algorithm == "HS256":
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience=settings.JWT_AUDIENCE,
                issuer=expected_issuer if settings.JWT_REQUIRE_ISSUER else None,
                options=decode_options,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "UNSUPPORTED_ALGORITHM", "message": "Unsupported algorithm."},
            )

        if not payload.get("sub"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "MALFORMED_TOKEN", "message": "Token is missing subject (sub) claim."},
            )

        if expected_issuer and payload.get("iss") and payload.get("iss") != expected_issuer:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_ISSUER", "message": "Token issuer claim (iss) is invalid."},
            )

        if is_token_revoked(token, payload):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "SESSION_REVOKED", "message": "Authentication session has been revoked."},
            )

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_EXPIRED", "message": "Authentication token has expired."},
        )
    except jwt.InvalidAudienceError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_AUDIENCE", "message": "Token audience claim (aud) does not match 'authenticated'."},
        )
    except jwt.InvalidIssuerError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_ISSUER", "message": "Token issuer claim (iss) is invalid."},
        )
    except jwt.InvalidSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_SIGNATURE", "message": "Cryptographic token signature verification failed."},
        )
    except jwt.DecodeError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "MALFORMED_TOKEN", "message": "Authentication token is malformed or tampered."},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTHENTICATION_FAILED", "message": f"Token verification failed: {str(e)}"},
        )


# ==============================================================================
# SENSITIVE LOG REDACTION & RATE LIMITING
# ==============================================================================

_SECRET_PATTERNS = [
    (re.compile(r"Bearer\s+[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+", re.IGNORECASE), "Bearer [REDACTED_JWT]"),
    (re.compile(r"\bsk-[A-Za-z0-9\-_]{16,}\b"), "[REDACTED_API_KEY]"),
    (re.compile(r"\bAIza[0-9A-Za-z\-_]{20,}\b"), "[REDACTED_GOOGLE_KEY]"),
    (re.compile(r"\bsb_(?:secret|publishable)_[A-Za-z0-9_\-]{10,}\b"), "[REDACTED_SUPABASE_KEY]"),
]


def redact_sensitive_text(value: str) -> str:
    redacted = value
    for pattern, replacement in _SECRET_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def redact_sensitive_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    sensitive_keys = {"api_key", "secret", "password", "token", "authorization", "encrypted_api_key", "master_key"}
    clean: Dict[str, Any] = {}
    for k, v in data.items():
        if k.lower() in sensitive_keys:
            clean[k] = "[REDACTED]"
        elif isinstance(v, str):
            clean[k] = redact_sensitive_text(v)
        elif isinstance(v, dict):
            clean[k] = redact_sensitive_dict(v)
        else:
            clean[k] = v
    return clean


class SlidingWindowRateLimiter:
    """In-memory sliding window rate limiter for API, WebSocket, and AI endpoints."""

    def __init__(self, max_requests: int = 120, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)

    def check(self, key: str) -> bool:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        q = self._hits[key]
        while q and q[0] <= cutoff:
            q.popleft()
        if len(q) >= self.max_requests:
            return False
        q.append(now)
        return True

    def enforce(self, key: str) -> None:
        if not self.check(key):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "code": "RATE_LIMITED",
                    "message": f"Rate limit exceeded ({self.max_requests} requests per {self.window_seconds}s).",
                },
            )


api_rate_limiter = SlidingWindowRateLimiter(max_requests=240, window_seconds=60)
auth_rate_limiter = SlidingWindowRateLimiter(max_requests=30, window_seconds=60)


async def enforce_request_rate_limit(request: Request) -> None:
    client_host = request.client.host if request.client else "unknown"
    api_rate_limiter.enforce(f"ip:{client_host}")
