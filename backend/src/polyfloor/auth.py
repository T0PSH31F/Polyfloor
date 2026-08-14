"""Bearer token authentication and role-based authorization.

The scaffold uses a static API token loaded from a file, mapped to
principal roles and floor scopes. No database-backed tokens in the
initial implementation.
"""

from __future__ import annotations

import hashlib
import hmac
from enum import Enum
from functools import wraps
from typing import Optional, Set

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import Settings, get_settings

security_scheme = HTTPBearer(auto_error=False)


class PrincipalRole(str, Enum):
    """Authorization roles for API principals."""

    HUMAN_ADMIN = "human_admin"
    HR = "hr"
    ORCHESTRATOR = "orchestrator"
    WORKER = "worker"
    READONLY = "readonly"


# Role → allowed scopes
ROLE_SCOPES: dict[PrincipalRole, Set[str]] = {
    PrincipalRole.HUMAN_ADMIN: {
        "floors:read", "floors:write",
        "roles:read", "roles:write",
        "tasks:read", "tasks:write",
        "approvals:read", "approvals:create", "approvals:resolve",
        "sprints:read", "sprints:write",
        "events:read", "config:write",
    },
    PrincipalRole.HR: {
        "floors:read", "floors:write",
        "roles:read", "roles:write",
        "tasks:read", "tasks:write",
        "approvals:read", "approvals:create", "approvals:resolve",
        "sprints:read", "sprints:write",
        "events:read", "config:write",
    },
    PrincipalRole.ORCHESTRATOR: {
        "floors:read",
        "roles:read",
        "tasks:read", "tasks:write",
        "approvals:read", "approvals:create",
        "sprints:read", "sprints:write",
        "events:read",
    },
    PrincipalRole.WORKER: {
        "floors:read",
        "roles:read",
        "tasks:read",
        "events:read",
    },
    PrincipalRole.READONLY: {
        "floors:read",
        "roles:read",
        "tasks:read",
        "approvals:read",
        "sprints:read",
        "events:read",
    },
}


class Principal:
    """Authenticated API principal."""

    def __init__(self, role: PrincipalRole, floor_scopes: Optional[Set[str]] = None):
        self.role = role
        self.floor_scopes = floor_scopes  # None = all floors, set = scoped

    def has_scope(self, scope: str) -> bool:
        return scope in ROLE_SCOPES.get(self.role, set())

    def can_access_floor(self, floor_id: str) -> bool:
        if self.floor_scopes is None:
            return True
        return floor_id in self.floor_scopes


# Default principal for development (no token file configured)
_DEV_PRINCIPAL = Principal(role=PrincipalRole.HUMAN_ADMIN)


def _constant_time_compare(a: str, b: str) -> bool:
    """Constant-time string comparison to prevent timing attacks."""
    return hmac.compare_digest(a.encode(), b.encode())


async def get_principal(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    settings: Settings = Depends(get_settings),
) -> Principal:
    """Extract and validate the authenticated principal from the request."""
    token = settings.security.get_api_token()

    # If no token file configured, use dev principal (development mode)
    if token is None:
        return _DEV_PRINCIPAL

    # Require bearer token
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not _constant_time_compare(credentials.credentials, token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )

    # For the scaffold, the single token maps to human_admin
    # A production system would look up the token in a database
    return Principal(role=PrincipalRole.HUMAN_ADMIN)


def require_scope(scope: str):
    """Dependency that raises 403 if the principal lacks the given scope."""

    async def _check(principal: Principal = Depends(get_principal)) -> Principal:
        if not principal.has_scope(scope):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: requires scope '{scope}'",
            )
        return principal

    return _check


def require_floor_access(floor_id: str, principal: Principal) -> None:
    """Raise 403 if the principal cannot access the given floor."""
    if not principal.can_access_floor(floor_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied to floor '{floor_id}'",
        )
