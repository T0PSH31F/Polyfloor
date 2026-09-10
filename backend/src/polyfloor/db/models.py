"""SQLModel persistence models for Polyfloor."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class Task(SQLModel, table=True):
    """Durable task model."""

    __tablename__ = "tasks"

    id: int | None = Field(default=None, primary_key=True)
    floor_id: str = Field(index=True)
    sprint_id: int | None = Field(default=None)
    title: str
    description: str = ""
    status: str = Field(default="backlog", index=True)
    assigned_role: str | None = Field(default=None)
    priority: int = Field(default=0)
    metadata_json: str = Field(default="{}")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class FloorEvent(SQLModel, table=True):
    """Durable floor event record."""

    __tablename__ = "floor_events"

    id: int | None = Field(default=None, primary_key=True)
    floor_id: str = Field(index=True)
    event_type: str = Field(index=True)
    actor: str = Field(default="system")
    payload_json: str = Field(default="{}")
    created_at: datetime = Field(default_factory=utc_now)


class Approval(SQLModel, table=True):
    """Durable approval queue record."""

    __tablename__ = "approvals"

    id: int | None = Field(default=None, primary_key=True)
    floor_id: str = Field(index=True)
    task_id: int | None = Field(default=None)
    approval_type: str
    description: str
    payload_json: str = Field(default="{}")
    status: str = Field(default="pending", index=True)
    requested_by: str
    resolved_by: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)
    resolved_at: datetime | None = Field(default=None)


class ApiToken(SQLModel, table=True):
    """Database-backed API bearer tokens."""

    __tablename__ = "api_tokens"

    id: int | None = Field(default=None, primary_key=True)
    token_hash: str = Field(unique=True, index=True)
    name: str
    role: str = Field(index=True)  # e.g., "human_admin", "worker"
    floor_scopes_json: str | None = Field(default=None)  # JSON string array or None
    created_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime | None = Field(default=None)
    revoked: bool = Field(default=False, index=True)


class ApiAuditLog(SQLModel, table=True):
    """API request audit trail."""

    __tablename__ = "api_audit_logs"

    id: int | None = Field(default=None, primary_key=True)
    token_id: int | None = Field(default=None)
    principal_role: str
    endpoint: str
    method: str
    timestamp: datetime = Field(default_factory=utc_now)
