"""Database engine and session factory.

Supports SQLite (dev) and PostgreSQL (prod) via SQLAlchemy async.
"""

from sqlalchemy import create_engine as create_sync_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from config.settings import settings

# Create async engine
_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    poolclass=NullPool,
)

# Async session factory
async_session_factory = async_sessionmaker(
    _engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:  # type: ignore[misc]
    """Dependency injection: yield an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def init_db_sync() -> None:
    """Create all tables using a synchronous engine.

    SQLite DDL operations (CREATE TABLE) must run on a sync connection.
    This function should be called once at application startup.
    """
    # Import all ORM models so they register with Base.metadata
    import src.db.models  # noqa: F401

    from src.db.base import Base

    # Derive sync URL from the async URL
    sync_url = settings.DATABASE_URL.replace(
        "sqlite+aiosqlite:///", "sqlite:///"
    ).replace("postgresql+asyncpg://", "postgresql://")

    sync_engine = create_sync_engine(sync_url, echo=False, poolclass=NullPool)

    try:
        Base.metadata.create_all(sync_engine)
        sync_engine.dispose()
    except Exception:
        sync_engine.dispose()
        raise


# Backward-compatible async wrapper
async def init_db() -> None:
    """Async-compatible wrapper. Uses sync engine under the hood for SQLite compatibility."""
    import asyncio
    await asyncio.to_thread(init_db_sync)


async def close_db() -> None:
    """Dispose the database engine. Called at application shutdown."""
    await _engine.dispose()
