"""
MSGI One — Encrypted Admin AI Provider Key Vault (Phase 8)
Security Principles (Silberschatz / Kleppmann / OWASP ASVS):
1. All admin-configured third-party LLM API keys (Gemini, OpenAI, Anthropic, DeepSeek)
   are encrypted at rest using AES-256-GCM with unique 96-bit nonces and Associated
   Authenticated Data (AAD = provider:config_id:key_version).
2. Plaintext API keys are NEVER stored, logged, serialized into API responses, or sent
   back to any admin/mobile client — only masked hints (e.g. 'sk-...a9f2') are exposed.
3. Supports zero-downtime key rotation incrementing key_version with fresh nonces.
"""

from __future__ import annotations

import base64
import hashlib
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pydantic import BaseModel, Field

from src.core.config import settings


SUPPORTED_PROVIDERS = ("gemini", "openai", "anthropic", "deepseek")


class VaultIntegrityError(Exception):
    """Raised when ciphertext authentication fails (wrong master key or tampered AAD/ciphertext)."""


def _derive_aes256_key(master_key: Optional[str] = None) -> Tuple[bytes, bool]:
    """
    Derives a deterministic 256-bit (32-byte) AES-GCM key from AI_VAULT_MASTER_KEY.
    Returns (key_bytes, is_ephemeral_fallback).
    """
    raw_secret = master_key or settings.AI_VAULT_MASTER_KEY
    is_fallback = False
    if not raw_secret:
        is_fallback = True
        raw_secret = f"msgi-one-vault-fallback::{settings.SUPABASE_JWT_SECRET}"

    # Support either raw 32-byte base64 key or arbitrary passphrase via SHA-256 KDF
    domain_material = f"msgi-one-ai-vault-v1::{raw_secret}".encode("utf-8")
    return hashlib.sha256(domain_material).digest(), is_fallback


def mask_api_key(plaintext: str) -> str:
    """Produces a safe non-reversible display hint without leaking secret material."""
    cleaned = (plaintext or "").strip()
    if len(cleaned) <= 8:
        return "****"
    prefix_len = 4 if len(cleaned) >= 12 else 2
    return f"{cleaned[:prefix_len]}...{cleaned[-4:]}"


def redact_key_fragments(text: str) -> str:
    """Defense-in-depth scrub for known API key shapes before error logging."""
    if not text:
        return text
    scrubbed = re.sub(r"AIza[0-9A-Za-z\-_]{16,}", "[REDACTED_GEMINI_KEY]", text)
    scrubbed = re.sub(r"sk-ant-[0-9A-Za-z\-_]{12,}", "[REDACTED_ANTHROPIC_KEY]", scrubbed)
    scrubbed = re.sub(r"sk-[0-9A-Za-z\-_]{12,}", "[REDACTED_API_KEY]", scrubbed)
    return scrubbed


def _build_aad(provider: str, config_id: str, key_version: int) -> bytes:
    return f"{provider}:{config_id}:v{key_version}".encode("utf-8")


def encrypt_api_key(
    plaintext: str,
    provider: str,
    config_id: str,
    key_version: int = 1,
    master_key: Optional[str] = None,
) -> Tuple[str, str, str]:
    """
    Encrypts plaintext API key using AES-256-GCM.
    Returns (ciphertext_b64, nonce_b64, key_hint).
    """
    if not plaintext or not plaintext.strip():
        raise ValueError("API key cannot be empty.")

    key_bytes, _ = _derive_aes256_key(master_key)
    nonce = os.urandom(12)  # 96-bit NIST-recommended GCM nonce
    aad = _build_aad(provider, config_id, key_version)
    ciphertext = AESGCM(key_bytes).encrypt(nonce, plaintext.strip().encode("utf-8"), aad)
    return (
        base64.b64encode(ciphertext).decode("ascii"),
        base64.b64encode(nonce).decode("ascii"),
        mask_api_key(plaintext),
    )


def decrypt_api_key(
    ciphertext_b64: str,
    nonce_b64: str,
    provider: str,
    config_id: str,
    key_version: int = 1,
    master_key: Optional[str] = None,
) -> str:
    """Decrypts AES-256-GCM ciphertext verifying AAD integrity."""
    key_bytes, _ = _derive_aes256_key(master_key)
    try:
        nonce = base64.b64decode(nonce_b64)
        ciphertext = base64.b64decode(ciphertext_b64)
        aad = _build_aad(provider, config_id, key_version)
        plaintext_bytes = AESGCM(key_bytes).decrypt(nonce, ciphertext, aad)
        return plaintext_bytes.decode("utf-8")
    except Exception as exc:
        raise VaultIntegrityError(
            "Failed to decrypt provider key: authentication tag or AAD mismatch."
        ) from exc


class ProviderConfigRecord(BaseModel):
    """Internal encrypted vault record aligned with public.ai_provider_configs."""
    id: str
    provider: str
    display_name: str
    model_id: str
    encrypted_api_key: str
    nonce: str
    key_version: int = 1
    key_hint: str
    capabilities: Dict[str, Any] = Field(default_factory=dict)
    is_enabled: bool = True
    is_primary: bool = False
    fallback_priority: int = 100
    verification_status: str = "unverified"
    last_verified_at: Optional[str] = None
    last_error_message: Optional[str] = None
    daily_budget_usd: Optional[float] = 25.0
    monthly_budget_usd: Optional[float] = 300.0
    requests_per_minute_limit: Optional[int] = 60
    configured_by: Optional[str] = None
    created_at: str
    updated_at: str

    def to_safe_dict(self) -> Dict[str, Any]:
        """Serializes metadata cleanly with ZERO encrypted/plaintext key material."""
        return {
            "id": self.id,
            "provider": self.provider,
            "display_name": self.display_name,
            "model_id": self.model_id,
            "key_version": self.key_version,
            "key_hint": self.key_hint,
            "has_key": bool(self.encrypted_api_key),
            "capabilities": self.capabilities,
            "is_enabled": self.is_enabled,
            "is_primary": self.is_primary,
            "fallback_priority": self.fallback_priority,
            "verification_status": self.verification_status,
            "last_verified_at": self.last_verified_at,
            "last_error_message": self.last_error_message,
            "daily_budget_usd": self.daily_budget_usd,
            "monthly_budget_usd": self.monthly_budget_usd,
            "requests_per_minute_limit": self.requests_per_minute_limit,
            "configured_by": self.configured_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# In-memory vault store mirroring ai_provider_configs for fast sandboxed/unit execution
_PROVIDER_VAULT_STORE: Dict[str, ProviderConfigRecord] = {}


def clear_vault_for_tests() -> None:
    _PROVIDER_VAULT_STORE.clear()


def _default_capabilities_for(provider: str) -> Dict[str, Any]:
    defaults: Dict[str, Dict[str, Any]] = {
        "gemini": {
            "supports_streaming": True,
            "supports_tools": True,
            "supports_structured_json": True,
            "supports_embeddings": True,
            "embedding_dimensions": 1536,
            "max_context_tokens": 1_000_000,
        },
        "openai": {
            "supports_streaming": True,
            "supports_tools": True,
            "supports_structured_json": True,
            "supports_embeddings": True,
            "embedding_dimensions": 1536,
            "max_context_tokens": 128_000,
        },
        "anthropic": {
            "supports_streaming": True,
            "supports_tools": True,
            "supports_structured_json": True,
            "supports_embeddings": False,
            "embedding_dimensions": 1536,
            "max_context_tokens": 200_000,
        },
        "deepseek": {
            "supports_streaming": True,
            "supports_tools": True,
            "supports_structured_json": True,
            "supports_embeddings": False,
            "embedding_dimensions": 1536,
            "max_context_tokens": 64_000,
        },
    }
    return defaults.get(provider, {"supports_streaming": True})


def upsert_provider_config(
    *,
    provider: str,
    display_name: str,
    model_id: str,
    api_key: str,
    configured_by: str,
    config_id: Optional[str] = None,
    is_enabled: bool = True,
    is_primary: bool = False,
    fallback_priority: int = 100,
    daily_budget_usd: Optional[float] = 25.0,
    monthly_budget_usd: Optional[float] = 300.0,
    requests_per_minute_limit: Optional[int] = 60,
    capabilities: Optional[Dict[str, Any]] = None,
    master_key: Optional[str] = None,
) -> ProviderConfigRecord:
    prov = provider.lower().strip()
    if prov not in SUPPORTED_PROVIDERS:
        raise ValueError(f"Unsupported AI provider '{provider}'. Must be one of {SUPPORTED_PROVIDERS}.")

    cid = config_id or f"aicfg-{uuid.uuid4().hex[:12]}"
    existing = _PROVIDER_VAULT_STORE.get(cid)
    key_version = (existing.key_version + 1) if existing else 1
    now_iso = datetime.now(timezone.utc).isoformat()

    ct_b64, nonce_b64, hint = encrypt_api_key(
        plaintext=api_key,
        provider=prov,
        config_id=cid,
        key_version=key_version,
        master_key=master_key,
    )

    # Single-primary invariant across active configurations
    if is_primary:
        for cfg in _PROVIDER_VAULT_STORE.values():
            if cfg.id != cid:
                cfg.is_primary = False

    record = ProviderConfigRecord(
        id=cid,
        provider=prov,
        display_name=display_name.strip(),
        model_id=model_id.strip(),
        encrypted_api_key=ct_b64,
        nonce=nonce_b64,
        key_version=key_version,
        key_hint=hint,
        capabilities=capabilities or _default_capabilities_for(prov),
        is_enabled=is_enabled,
        is_primary=is_primary,
        fallback_priority=fallback_priority,
        verification_status="unverified",
        last_verified_at=None,
        last_error_message=None,
        daily_budget_usd=daily_budget_usd,
        monthly_budget_usd=monthly_budget_usd,
        requests_per_minute_limit=requests_per_minute_limit,
        configured_by=configured_by,
        created_at=existing.created_at if existing else now_iso,
        updated_at=now_iso,
    )
    _PROVIDER_VAULT_STORE[cid] = record
    return record


def rotate_provider_key(
    *,
    config_id: str,
    new_api_key: str,
    configured_by: str,
    master_key: Optional[str] = None,
) -> ProviderConfigRecord:
    existing = _PROVIDER_VAULT_STORE.get(config_id)
    if not existing:
        raise KeyError(f"Provider config '{config_id}' not found.")
    new_ver = existing.key_version + 1
    ct_b64, nonce_b64, hint = encrypt_api_key(
        plaintext=new_api_key,
        provider=existing.provider,
        config_id=existing.id,
        key_version=new_ver,
        master_key=master_key,
    )
    existing.encrypted_api_key = ct_b64
    existing.nonce = nonce_b64
    existing.key_version = new_ver
    existing.key_hint = hint
    existing.verification_status = "unverified"
    existing.last_error_message = None
    existing.configured_by = configured_by
    existing.updated_at = datetime.now(timezone.utc).isoformat()
    return existing


def list_provider_configs(include_disabled: bool = True) -> List[ProviderConfigRecord]:
    items = list(_PROVIDER_VAULT_STORE.values())
    if not include_disabled:
        items = [c for c in items if c.is_enabled]
    return sorted(items, key=lambda c: (0 if c.is_primary else 1, c.fallback_priority, c.created_at))


def get_provider_config(config_id: str) -> Optional[ProviderConfigRecord]:
    return _PROVIDER_VAULT_STORE.get(config_id)


def decrypt_provider_key_for_runtime(
    config: ProviderConfigRecord,
    master_key: Optional[str] = None,
) -> str:
    return decrypt_api_key(
        ciphertext_b64=config.encrypted_api_key,
        nonce_b64=config.nonce,
        provider=config.provider,
        config_id=config.id,
        key_version=config.key_version,
        master_key=master_key,
    )


def update_verification_status(
    config_id: str,
    status_val: str,
    error_message: Optional[str] = None,
) -> Optional[ProviderConfigRecord]:
    cfg = _PROVIDER_VAULT_STORE.get(config_id)
    if not cfg:
        return None
    cfg.verification_status = status_val
    cfg.last_verified_at = datetime.now(timezone.utc).isoformat()
    cfg.last_error_message = redact_key_fragments(error_message) if error_message else None
    cfg.updated_at = cfg.last_verified_at
    return cfg


def delete_provider_config(config_id: str) -> bool:
    return _PROVIDER_VAULT_STORE.pop(config_id, None) is not None
