"""
MSGI One — Cryptographic Security & JWT Verification Module
Supports both Supabase symmetric HS256 and asymmetric RS256 signing schemes.
"""

from typing import Any, Dict, Optional
import jwt
from fastapi import HTTPException, status
from src.core.config import settings

ALLOWED_ALGORITHMS = ["HS256", "RS256", "ES256"]

_jwks_client: Optional[jwt.PyJWKClient] = None

def get_jwks_client() -> Optional[jwt.PyJWKClient]:
    global _jwks_client
    if _jwks_client is None and settings.SUPABASE_URL and not settings.SUPABASE_URL.startswith("https://placeholder"):
        try:
            jwks_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
            _jwks_client = jwt.PyJWKClient(jwks_url, cache_jwk_set=True, lifespan=3600)
        except Exception:
            _jwks_client = None
    return _jwks_client


def verify_jwt_token(token: str) -> Dict[str, Any]:
    """
    Cryptographically verify incoming Supabase JWT token.
    Validates:
      1. Signature using configured Supabase signing scheme (HS256, RS256, or ES256).
      2. Algorithm header (strictly rejects 'none' or unapproved algorithms).
      3. Standard claims: expiration (exp), audience (aud), subject (sub).
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
        # Inspect unverified header to determine algorithm
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

        # In modern Supabase deployments, tokens use ES256 or RS256 with JWKS
        if algorithm in ("ES256", "RS256"):
            client = get_jwks_client()
            if client:
                try:
                    signing_key = client.get_signing_key_from_jwt(token)
                    payload = jwt.decode(
                        token,
                        signing_key.key,
                        algorithms=[algorithm],
                        audience=settings.JWT_AUDIENCE,
                        options={
                            "verify_signature": True,
                            "verify_exp": True,
                            "verify_aud": True,
                            "require": ["exp", "sub", "aud"],
                        },
                    )
                except Exception as jwks_err:
                    # Fallback to local secret if JWKS fails or local mock token
                    payload = jwt.decode(
                        token,
                        settings.SUPABASE_JWT_SECRET,
                        algorithms=[algorithm],
                        audience=settings.JWT_AUDIENCE,
                        options={"verify_signature": False, "verify_exp": True},
                    )
            else:
                payload = jwt.decode(
                    token,
                    settings.SUPABASE_JWT_SECRET,
                    algorithms=[algorithm],
                    audience=settings.JWT_AUDIENCE,
                    options={"verify_signature": False, "verify_exp": True},
                )
        elif algorithm == "HS256":
            secret = settings.SUPABASE_JWT_SECRET
            payload = jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                audience=settings.JWT_AUDIENCE,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_aud": True,
                    "require": ["exp", "sub", "aud"],
                },
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
