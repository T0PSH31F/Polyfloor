"""Test fixtures and configuration."""

from __future__ import annotations

import os
import sys
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@pytest_asyncio.fixture
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """In-memory SQLite async engine for tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Test AsyncSession."""
    async_session = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.fixture
def mock_pool():
    """Mock asyncpg pool."""
    pool = AsyncMock()
    conn = AsyncMock()
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
    pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)
    return pool, conn


@pytest.fixture
def settings_no_auth():
    """Settings with no auth configured (dev mode)."""
    with patch.dict(os.environ, {}, clear=True):
        from polyfloor.config import Settings

        s = Settings()
        s.security.api_token_file = None
        return s


@pytest.fixture
def dev_principal():
    """Development principal with full access."""
    from polyfloor.auth import Principal, PrincipalRole

    return Principal(role=PrincipalRole.HUMAN_ADMIN)
