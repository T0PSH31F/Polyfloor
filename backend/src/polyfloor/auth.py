"""Bearer token authentication and role-based authorization with DB backing."""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import UTC, datetime
from enum import StrEnum

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from .config import Settings, get_settings
from .db import get_engine
from .db.models import ApiAuditLog, ApiToken

security_scheme = HTTPBearer(auto_error=False)


class PrincipalRole(StrEnum):
    """Authorization roles for API principals."""

    HUMAN_ADMIN = "human_admin"
    HR = "hr"
    ORCHESTRATOR = "orchestrator"
    WORKER = "worker"
    READONLY = "readonly"


ROLE_SCOPES: dict[PrincipalRole, set[str]] = {
    PrincipalRole.HUMAN_ADMIN: {
        "floors:read",
        "floors:write",
        "roles:read",
        "roles:write",
        "tasks:read",
        "tasks:write",
        "approvals:read",
        "approvals:create",
        "approvals:resolve",
        "sprints:read",
        "sprints:write",
        "events:read",
        "config:write",
    },
    PrincipalRole.HR: {
        "floors:read",
        "floors:write",
        "roles:read",
        "roles:write",
        "tasks:read",
        "tasks:write",
        "approvals:read",
        "approvals:create",
        "approvals:resolve",
        "sprints:read",
        "sprints:write",
        "events:read",
        "config:write",
    },
    PrincipalRole.ORCHESTRATOR: {
        "floors:read",
        "roles:read",
        "tasks:read",
        "tasks:write",
        "approvals:read",
        "approvals:create",
        "sprints:read",
        "sprints:write",
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

    def __init__(
        self,
        role: PrincipalRole,
        floor_scopes: set[str] | None = None,
        token_id: int | None = None,
    ):
        self.role = role
        self.floor_scopes = floor_scopes
        self.token_id = token_id

    def has_scope(self, scope: str) -> bool:
        return scope in ROLE_SCOPES.get(self.role, set())

    def can_access_floor(self, floor_id: str) -> bool:
        if self.floor_scopes is None:
            return True
        return floor_id in self.floor_scopes


_DEV_PRINCIPAL = Principal(role=PrincipalRole.HUMAN_ADMIN)


def _constant_time_compare(a: str, b: str) -> bool:
    """Constant-time string comparison to prevent timing attacks."""
    return hmac.compare_digest(a.encode(), b.encode())


def hash_token(raw_token: str) -> str:
    """Compute SHA-256 hash of API token."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


async def get_principal(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    settings: Settings = Depends(get_settings),
) -> Principal:
    """Extract and validate the authenticated principal from DB or static settings."""
    static_token = settings.security.get_api_token()

    # If no credentials provided: check dev fallback
    if credentials is None:
        if static_token is None:
            return _DEV_PRINCIPAL
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    raw_token = credentials.credentials

    # Check static token file fallback if configured
    if static_token and _constant_time_compare(raw_token, static_token):
        return Principal(role=PrincipalRole.HUMAN_ADMIN)

    # Check database-backed tokens
    token_h = hash_token(raw_token)
    try:
        engine = get_engine()
        async with AsyncSession(engine) as session:
            stmt = select(ApiToken).where(ApiToken.token_hash == token_h)
            result = await session.execute(stmt)
            token_record = result.scalar_one_or_none()

            if token_record is not None:
                if token_record.revoked:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token has been revoked",
                    )
                if token_record.expires_at:
                    exp = token_record.expires_at
                    if exp.tzinfo is None:
                        exp = exp.replace(tzinfo=UTC)
                    if exp < datetime.now(UTC):
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token has expired",
                        )

                scopes: set[str] | None = None
                if token_record.floor_scopes_json:
                    scopes = set(json.loads(token_record.floor_scopes_json))

                role = PrincipalRole(token_record.role)
                principal = Principal(role=role, floor_scopes=scopes, token_id=token_record.id)

                # Audit log entry
                audit = ApiAuditLog(
                    token_id=token_record.id,
                    principal_role=role.value,
                    endpoint=request.url.path,
                    method=request.method,
                )
                session.add(audit)
                await session.commit()
                return principal
    except HTTPException:
        raise
    except Exception:
        pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication token",
    )


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
