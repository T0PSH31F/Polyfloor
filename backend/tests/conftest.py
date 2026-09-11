"""Test fixtures and configuration."""

from __future__ import annotations

import os
import sys
from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

# Ensure the backend src is importable as `polyfloor`.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Use a temp data dir so avatar composition tests don't touch /var/lib.
os.environ.setdefault("POLYFLOOR_DATA_DIR", "/tmp/polyfloor-test-data")
os.environ.setdefault("POLYFLOOR_STATIC_DIR", "")


@pytest_asyncio.fixture
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """In-memory SQLite async engine sharing one connection (StaticPool).

    StaticPool keeps a single connection so writes from one session are visible
    to another — required for event-bus persistence tests.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Test AsyncSession."""
    factory = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
