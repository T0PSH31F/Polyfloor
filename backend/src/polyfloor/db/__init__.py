"""Database connection management using asyncpg."""

from __future__ import annotations

from typing import Optional

import asyncpg

_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    """Get or create the connection pool."""
    global _pool
    if _pool is None:
        from .config import get_settings

        settings = get_settings()
        _pool = await asyncpg.create_pool(
            dsn=settings.database.dsn,
            min_size=settings.database.pool_min,
            max_size=settings.database.pool_max,
        )
    return _pool


async def close_pool() -> None:
    """Close the connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def get_connection() -> asyncpg.Connection:
    """Get a connection from the pool (for dependency injection)."""
    pool = await get_pool()
    return await pool.acquire()


async def release_connection(conn: asyncpg.Connection) -> None:
    """Release a connection back to the pool."""
    pool = await get_pool()
    await pool.release(conn)
