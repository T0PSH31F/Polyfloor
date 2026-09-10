"""Authentication and authorization tests."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from polyfloor.auth import (
    ROLE_SCOPES,
    Principal,
    PrincipalRole,
    get_principal,
    hash_token,
)
from polyfloor.db.models import ApiToken


def test_dev_mode_no_token():
    """Without a token file, dev principal is used."""
    from polyfloor.auth import _DEV_PRINCIPAL

    assert _DEV_PRINCIPAL.role == PrincipalRole.HUMAN_ADMIN


def test_principal_has_scope():
    p = Principal(role=PrincipalRole.WORKER)
    assert p.has_scope("tasks:read")
    assert not p.has_scope("tasks:write")
    assert not p.has_scope("approvals:resolve")


def test_principal_floor_scoping():
    p = Principal(role=PrincipalRole.READONLY, floor_scopes={"floor-a", "floor-b"})
    assert p.can_access_floor("floor-a")
    assert p.can_access_floor("floor-b")
    assert not p.can_access_floor("floor-c")


def test_admin_has_all_scopes():
    admin = Principal(role=PrincipalRole.HUMAN_ADMIN)
    for scope_set in ROLE_SCOPES.values():
        for scope in scope_set:
            assert admin.has_scope(scope), f"HUMAN_ADMIN missing scope: {scope}"


@pytest.mark.asyncio
async def test_db_backed_token_valid(test_engine, test_session):
    raw_token = "secret_worker_token_123"
    token_h = hash_token(raw_token)

    db_token = ApiToken(
        token_hash=token_h,
        name="test_worker",
        role="worker",
        floor_scopes_json=json.dumps(["dev_floor"]),
    )
    test_session.add(db_token)
    await test_session.commit()

    req = MagicMock()
    req.url.path = "/api/v1/tasks"
    req.method = "GET"

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=raw_token)
    settings = MagicMock()
    settings.security.get_api_token.return_value = "static_file_token_456"

    with patch("polyfloor.auth.get_engine", return_value=test_engine):
        principal = await get_principal(request=req, credentials=creds, settings=settings)

    assert principal.role == PrincipalRole.WORKER
    assert principal.can_access_floor("dev_floor")
    assert not principal.can_access_floor("prod_floor")


@pytest.mark.asyncio
async def test_db_backed_token_revoked(test_engine, test_session):
    raw_token = "revoked_token_123"
    token_h = hash_token(raw_token)

    db_token = ApiToken(
        token_hash=token_h,
        name="revoked_worker",
        role="worker",
        revoked=True,
    )
    test_session.add(db_token)
    await test_session.commit()

    req = MagicMock()
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=raw_token)
    settings = MagicMock()
    settings.security.get_api_token.return_value = "static_file_token_456"

    with patch("polyfloor.auth.get_engine", return_value=test_engine):
        with pytest.raises(HTTPException) as exc_info:
            await get_principal(request=req, credentials=creds, settings=settings)
        assert exc_info.value.status_code == 401
        assert "revoked" in exc_info.value.detail


@pytest.mark.asyncio
async def test_db_backed_token_expired(test_engine, test_session):
    raw_token = "expired_token_123"
    token_h = hash_token(raw_token)

    expired_time = datetime.now(UTC) - timedelta(hours=1)
    db_token = ApiToken(
        token_hash=token_h,
        name="expired_worker",
        role="worker",
        expires_at=expired_time,
    )
    test_session.add(db_token)
    await test_session.commit()

    req = MagicMock()
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=raw_token)
    settings = MagicMock()
    settings.security.get_api_token.return_value = "static_file_token_456"

    with patch("polyfloor.auth.get_engine", return_value=test_engine):
        with pytest.raises(HTTPException) as exc_info:
            await get_principal(request=req, credentials=creds, settings=settings)
        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail
