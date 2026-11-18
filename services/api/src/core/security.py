"""
MSGI One — Cryptographic Security & JWT Verification Module
Supports both Supabase symmetric HS256 and asymmetric RS256 signing schemes.
"""

from typing import Any, Dict, Optional
import jwt
from fastapi import HTTPException, status
from src.core.config import settings

ALLOWED_ALGORITHMS = ["HS256", "RS256"]


def verify_jwt_token(token: str) -> Dict[str, Any]:
    """
    Cryptographically verify incoming Supabase JWT token.
    Validates:
      1. Signature using configured Supabase signing scheme (HS256 or RS256).
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
                    "message": f"Unsupported or prohibited JWT algorithm: {algorithm}. Only HS256 and RS256 are permitted.",
                },
            )

        # In standard Supabase deployments, tokens use HS256 with JWT secret
        if algorithm == "HS256":
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
        elif algorithm == "RS256":
            # In RS256 mode, verification requires public key / JWKS
            # For testing/local fallback, we decode with secret if symmetric or public key
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["RS256"],
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
