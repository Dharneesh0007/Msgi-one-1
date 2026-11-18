"""
MSGI One — Security & JWT Verification Unit Tests
Tests: Valid tokens, expired tokens, tampered signatures, unsupported 'none' algorithm.
"""

from datetime import datetime, timedelta, timezone
import jwt
import pytest
from fastapi import HTTPException
from src.core.config import settings
from src.core.security import verify_jwt_token


def create_test_token(
    user_id: str = "test-user-1234",
    email: str = "student@example.msgi.edu",
    roles: list = None,
    expires_in_minutes: int = 60,
    algorithm: str = "HS256",
    secret: str = None,
    audience: str = "authenticated",
) -> str:
    """Helper to generate deterministic test JWTs."""
    if roles is None:
        roles = ["student"]
    if secret is None:
        secret = settings.SUPABASE_JWT_SECRET

    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "aud": audience,
        "iss": f"{settings.SUPABASE_URL}/auth/v1",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_in_minutes)).timestamp()),
        "app_metadata": {"roles": roles},
        "user_metadata": {"first_name": "Test", "last_name": "User"},
    }

    if algorithm == "none":
        return jwt.encode(payload, key="", algorithm="none")

    return jwt.encode(payload, secret, algorithm=algorithm)


def test_valid_hs256_token_verifies_successfully():
    """Valid token signed with HS256 must decode subject and email."""
    token = create_test_token()
    claims = verify_jwt_token(token)
    assert claims["sub"] == "test-user-1234"
    assert claims["email"] == "student@example.msgi.edu"
    assert claims["aud"] == "authenticated"


def test_expired_token_raises_401():
    """Token with past exp claim must be rejected with TOKEN_EXPIRED."""
    token = create_test_token(expires_in_minutes=-10)
    with pytest.raises(HTTPException) as exc_info:
        verify_jwt_token(token)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["code"] == "TOKEN_EXPIRED"


def test_tampered_signature_raises_401():
    """Token signed with wrong key must be rejected with INVALID_SIGNATURE."""
    token = create_test_token(secret="completely-wrong-signing-secret-key-32chars")
    with pytest.raises(HTTPException) as exc_info:
        verify_jwt_token(token)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["code"] == "INVALID_SIGNATURE"


def test_prohibited_none_algorithm_raises_401():
    """Token specifying alg='none' must be strictly rejected with INVALID_TOKEN_ALGORITHM."""
    token = create_test_token(algorithm="none")
    with pytest.raises(HTTPException) as exc_info:
        verify_jwt_token(token)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["code"] == "INVALID_TOKEN_ALGORITHM"


def test_invalid_audience_raises_401():
    """Token with mismatched audience must be rejected with INVALID_AUDIENCE."""
    token = create_test_token(audience="wrong-audience")
    with pytest.raises(HTTPException) as exc_info:
        verify_jwt_token(token)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["code"] == "INVALID_AUDIENCE"


def test_empty_token_raises_401():
    """Empty or None token must be rejected with UNAUTHENTICATED."""
    with pytest.raises(HTTPException) as exc_info:
        verify_jwt_token("")
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["code"] == "UNAUTHENTICATED"
