"""
MSGI One — Database Session Management & Connection Pooling
Supports both PostgreSQL (asyncpg with pooled timeouts) and local SQLite fallback storage.
Includes explicit RLS user-context propagation helper for least-privilege runtime roles.
"""

from typing import AsyncGenerator, Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from src.core.config import settings

is_postgres = settings.DATABASE_URL.startswith("postgresql")

connect_args: Dict[str, Any] = {}
engine_kwargs: Dict[str, Any] = {
    "echo": settings.DEBUG,
    "future": True,
}

if is_postgres:
    import ssl
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connect_args = {
        "statement_cache_size": 0,
        "ssl": ssl_ctx,
        "command_timeout": 30,
    }
    engine_kwargs.update(
        {
            "pool_size": settings.DATABASE_POOL_SIZE,
            "max_overflow": settings.DATABASE_MAX_OVERFLOW,
            "pool_timeout": 30,
            "pool_recycle": 1800,
            "pool_pre_ping": True,
        }
    )

engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    **engine_kwargs,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def set_db_user_context(session: AsyncSession, user_id: Optional[str]) -> None:
    """
    Propagate authenticated user identity into PostgreSQL transaction-local settings
    so least-privilege runtime roles can evaluate Supabase/custom RLS policies accurately.
    """
    if not is_postgres or not user_id:
        return
    await session.execute(
        text("SELECT set_config('app.current_user_id', :uid, true), set_config('request.jwt.claim.sub', :uid, true)"),
        {"uid": str(user_id)},
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency providing an asynchronous database session with clean commit/rollback boundaries."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
