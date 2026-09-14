from collections.abc import AsyncGenerator
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.sql import text

from app.config import get_settings

settings = get_settings()

# Create async engine with connection pooling
async_engine = create_async_engine(
    settings.async_database_url,
    echo=False,
    future=True,
    pool_pre_ping=True,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Sync engine and session factory for synchronous SQLModel operations
from sqlmodel import Session, create_engine

sync_engine = create_engine(
    settings.sync_database_url_resolved,
    echo=False,
    pool_pre_ping=True,
)


def get_db_session():
    """Dependency for providing a synchronous SQLModel database session."""
    with Session(sync_engine) as session:
        yield session


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for providing an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def check_database_connection() -> tuple[bool, Optional[str]]:
    """
    Executes a simple SELECT 1 query to verify live database connectivity.
    Returns (True, None) on success, or (False, error_message) on failure.
    """
    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1;"))
            return True, None
    except Exception as exc:
        return False, str(exc)
