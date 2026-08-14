"""Test fixtures and configuration."""

from __future__ import annotations

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


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
