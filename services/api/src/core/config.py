"""
MSGI One — Application Configuration
Loaded from environment variables with safe development defaults.
"""

from typing import List, Optional, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "MSGI One API"

    # Supabase Configuration
    SUPABASE_URL: str = "https://placeholder-project.supabase.co"
    SUPABASE_ANON_KEY: str = "placeholder-anon-key"
    SUPABASE_SERVICE_ROLE_KEY: str = "placeholder-service-role-key"
    SUPABASE_JWT_SECRET: str = "msgi-one-local-development-secret-key-32chars-min"
    SUPABASE_JWT_PUBLIC_KEY: Optional[str] = None

    # Database Configuration (PostgreSQL / Supabase Transaction Pooler)
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"  # Fallback for local testing without hosted PG
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 5

    # Redis & Real-Time Configuration
    REDIS_URL: Optional[str] = None
    LIVEKIT_URL: Optional[str] = None
    LIVEKIT_API_KEY: Optional[str] = None
    LIVEKIT_API_SECRET: Optional[str] = None

    # Encrypted AI Provider Vault Master Key (AES-256-GCM, 32-byte base64 or hex)
    AI_VAULT_MASTER_KEY: Optional[str] = None

    # Security & JWT Configuration
    JWT_ALGORITHM: str = "HS256"
    JWT_AUDIENCE: str = "authenticated"
    JWT_REQUIRE_ISSUER: bool = False

    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:8081",
        "http://localhost:19006",
        "http://10.0.2.2:8000",
        "http://127.0.0.1:8000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
