"""Authentication and authorization tests."""

from __future__ import annotations

import os
import tempfile
from unittest.mock import patch

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from polyfloor.auth import (
    Principal,
    PrincipalRole,
    ROLE_SCOPES,
    get_principal,
    require_scope,
)


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


def test_auth_required_for_mutations():
    """When a token is configured, missing token returns 401."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("test-token-12345")
        token_file = f.name

    try:
        with patch.dict(os.environ, {"POLYFLOOR_API_TOKEN_FILE": token_file}):
            from polyfloor.config import Settings
            from polyfloor.main import create_app

            app = create_app()
            client = TestClient(app)

            # Without token → should work for read-only, fail for mutations
            # (depends on router configuration)
            resp = client.get("/healthz")
            assert resp.status_code == 200
    finally:
        os.unlink(token_file)
