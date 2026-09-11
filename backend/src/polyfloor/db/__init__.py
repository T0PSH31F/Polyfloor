"""Database engine, session management, and schema initialization.

SQLite (WAL mode) is the default so a fresh ``nix run`` works with zero external
services. The engine is async via ``aiosqlite``.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from .models import ALL_MODELS  # noqa: F401  (registers tables on metadata)


_engine: AsyncEngine | None = None
_session_factory: sessionmaker | None = None


def _build_engine(db_url: str) -> AsyncEngine:
    """Create an async engine. Enable SQLite WAL + foreign keys."""
    connect_args: dict = {}
    if db_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    engine = create_async_engine(db_url, echo=False, future=True, connect_args=connect_args)

    @event.listens_for(engine.sync_engine, "connect")
    def _sqlite_pragma(dbapi_conn, _):  # type: ignore[no-untyped-def]
        if db_url.startswith("sqlite"):
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA foreign_keys=ON")
            cur.close()

    return engine


def get_engine(db_url: str | None = None) -> AsyncEngine:
    """Get or create the async engine (cached)."""
    global _engine, _session_factory
    if _engine is None:
        from ..config import get_settings

        url = db_url or get_settings().database_url
        _engine = _build_engine(url)
        _session_factory = sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
    return _engine


async def init_db(db_url: str | None = None) -> None:
    """Create all tables. Idempotent."""
    engine = get_engine(db_url)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async session."""
    global _session_factory
    if _session_factory is None:
        get_engine()
    assert _session_factory is not None
    async with _session_factory() as session:
        yield session


async def close_engine() -> None:
    """Dispose the engine (shutdown)."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None


# Backwards-compatible aliases used by older scaffold code paths.
close_pool = close_engine


async def get_pool() -> AsyncEngine:  # noqa: D401
    """Return the engine (legacy alias)."""
    return get_engine()


async def close_pool_legacy() -> None:  # pragma: no cover
    await close_engine()
