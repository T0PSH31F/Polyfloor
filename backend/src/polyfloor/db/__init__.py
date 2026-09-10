"""Database connection and SQLModel persistence management."""

from __future__ import annotations

from typing import AsyncGenerator, Optional

import asyncpg
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from .models import ApiAuditLog, ApiToken, Approval, FloorEvent, Task  # noqa: F401

_pool: Optional[asyncpg.Pool] = None
_engine: Optional[AsyncEngine] = None
_session_factory: Optional[sessionmaker] = None

DEFAULT_SQLITE_URL = "sqlite+aiosqlite:///polyfloor.db"


def get_engine(db_url: Optional[str] = None) -> AsyncEngine:
    """Get or create the SQLAlchemy/SQLModel async engine."""
    global _engine, _session_factory
    if _engine is None:
        url = db_url or DEFAULT_SQLITE_URL
        _engine = create_async_engine(url, echo=False, future=True)
        _session_factory = sessionmaker(
            _engine, class_=AsyncSession, expire_on_commit=False
        )
    return _engine


async def init_db(db_url: Optional[str] = None) -> None:
    """Initialize SQLModel database tables."""
    engine = get_engine(db_url)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for obtaining an AsyncSession."""
    global _session_factory
    if _session_factory is None:
        get_engine()
    assert _session_factory is not None
    async with _session_factory() as session:
        yield session


async def get_pool() -> asyncpg.Pool:
    """Get or create the asyncpg connection pool."""
    global _pool
    if _pool is None:
        from ..config import get_settings

        settings = get_settings()
        _pool = await asyncpg.create_pool(
            dsn=settings.database.dsn,
            min_size=settings.database.pool_min,
            max_size=settings.database.pool_max,
        )
    return _pool


async def close_pool() -> None:
    """Close the asyncpg connection pool and SQLModel engine."""
    global _pool, _engine
    if _pool is not None:
        await _pool.close()
        _pool = None
    if _engine is not None:
        await _engine.dispose()
        _engine = None


async def get_connection() -> asyncpg.Connection:
    """Get a connection from the pool (for dependency injection)."""
    pool = await get_pool()
    return await pool.acquire()


async def release_connection(conn: asyncpg.Connection) -> None:
    """Release a connection back to the pool."""
    pool = await get_pool()
    await pool.release(conn)
