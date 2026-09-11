"""SQLModel persistence models for Polyfloor.

Every table is company-scoped: ``company_id`` is the isolation boundary. Floors,
rooms and desks are presentation containers, never security boundaries. See
``SPEC_POLYFLOOR.md`` §4 (Isolation) and §9.4 (Core schema).
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


# --------------------------------------------------------------------------- #
# Company tenant
# --------------------------------------------------------------------------- #
class Company(SQLModel, table=True):
    """A tenant. Owns its agents, teams, boards, artifacts, memory, budget."""

    __tablename__ = "companies"

    id: str = Field(primary_key=True)  # e.g. "co_luminpress"
    name: str
    slug: str = Field(unique=True, index=True)
    template_id: str = Field(default="digital-products")
    status: str = Field(default="active", index=True)  # active | paused | retired
    visual_theme: str = Field(default="default")
    goal: str = Field(default="")
    grilling_intensity: int = Field(default=1)  # 0-3
    budget_policy_json: str = Field(default="{}")
    channels_json: str = Field(default="[]")
    logo: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)


class CompanyFloor(SQLModel, table=True):
    """A visual floor belonging to exactly one company."""

    __tablename__ = "company_floors"

    id: str = Field(primary_key=True)
    company_id: str = Field(index=True)
    ordinal: int = Field(default=1)
    label: str = Field(default="Lobby")
    template_id: str | None = Field(default=None)
    layout_json: str = Field(default="{}")
    created_at: datetime = Field(default_factory=utc_now)


class Room(SQLModel, table=True):
    """A room on a company floor (CEO suite, HR, team suite, etc.)."""

    __tablename__ = "rooms"

    id: str = Field(primary_key=True)
    company_id: str = Field(index=True)
    company_floor_id: str = Field(index=True)
    team_id: str | None = Field(default=None, index=True)
    room_type: str = Field(default="team")  # ceo | hr | csuite | team | qa
    label: str
    layout_json: str = Field(default="{}")
    wip_limit: int = Field(default=3)
    created_at: datetime = Field(default_factory=utc_now)


class Team(SQLModel, table=True):
    __tablename__ = "teams"

    id: str = Field(primary_key=True)
    company_id: str = Field(index=True)
    name: str
    role_type: str = Field(default="worker")  # rnd | product | writing | marketing | ...
    lead_agent_id: str | None = Field(default=None)
    room_id: str | None = Field(default=None)
    policy_json: str = Field(default="{}")
    created_at: datetime = Field(default_factory=utc_now)


# --------------------------------------------------------------------------- #
# Agents
# --------------------------------------------------------------------------- #
class Agent(SQLModel, table=True):
    """An agent belongs to exactly one company."""

    __tablename__ = "agents"

    id: str = Field(primary_key=True)
    company_id: str = Field(index=True)
    team_id: str | None = Field(default=None, index=True)
    role: str = Field(index=True)  # ceo | hr | cfo | cto | coo | cho | lead | worker | qa
    name: str
    model_id: str | None = Field(default=None)
    avatar_recipe: str = Field(default="{}")
    avatar_uri: str | None = Field(default=None)
    state: str = Field(default="idle", index=True)  # idle | working | paused | retired
    home_room_id: str | None = Field(default=None)
    home_desk_id: str | None = Field(default=None)
    capability_profile_id: str | None = Field(default=None)
    token_spend: int = Field(default=0)
    created_at: datetime = Field(default_factory=utc_now)
    retired_at: datetime | None = Field(default=None)


class Desk(SQLModel, table=True):
    """A desk in a room. Vacant until HR assigns a worker."""

    __tablename__ = "desks"

    id: str = Field(primary_key=True)
    company_id: str = Field(index=True)
    room_id: str = Field(index=True)
    ordinal: int
    agent_id: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)


# --------------------------------------------------------------------------- #
# Work systems
# --------------------------------------------------------------------------- #
class Task(SQLModel, table=True):
    """Kanban / task DAG node."""

    __tablename__ = "tasks"

    id: int | None = Field(default=None, primary_key=True)
    company_id: str = Field(index=True)
    team_id: str | None = Field(default=None, index=True)
    owner_agent_id: str | None = Field(default=None)
    parent_task_id: int | None = Field(default=None)
    title: str
    description: str = Field(default="")
    status: str = Field(default="BACKLOG", index=True)
    # BACKLOG -> READY -> IN_PROGRESS -> REVIEW -> AWAITING_APPROVAL -> DONE (+ BLOCKED)
    priority: int = Field(default=0)
    acceptance_criteria_json: str = Field(default="[]")
    budget_limit: float = Field(default=0.0)
    retry_limit: int = Field(default=2)
    artifact_id: int | None = Field(default=None)
    trace_id: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Event(SQLModel, table=True):
    """Append-only, targeted event log."""

    __tablename__ = "events"

    id: int | None = Field(default=None, primary_key=True)
    company_id: str = Field(index=True)
    source_agent_id: str | None = Field(default=None)
    target_type: str = Field(default="role")  # role | agent | team | user | system
    target_id: str | None = Field(default=None)
    event_type: str = Field(index=True)
    correlation_id: str | None = Field(default=None)
    payload_json: str = Field(default="{}")
    trace_id: str | None = Field(default=None)
    requires_approval: bool = Field(default=False)
    created_at: datetime = Field(default_factory=utc_now)


class Artifact(SQLModel, table=True):
    """Produced artifact: uri, hash, lineage, review status."""

    __tablename__ = "artifacts"

    id: int | None = Field(default=None, primary_key=True)
    company_id: str = Field(index=True)
    task_id: int | None = Field(default=None, index=True)
    type: str = Field(default="document")  # research | spec | draft | campaign | ...
    title: str = Field(default="")
    uri: str
    content_hash: str | None = Field(default=None)
    lineage_json: str = Field(default="[]")
    review_status: str = Field(default="PENDING")  # PENDING | PASSED | FAILED
    created_at: datetime = Field(default_factory=utc_now)


class Approval(SQLModel, table=True):
    """Human/CEO gate: hire, spend, publish, irreversible I/O."""

    __tablename__ = "approvals"

    id: int | None = Field(default=None, primary_key=True)
    company_id: str = Field(index=True)
    task_id: int | None = Field(default=None)
    requested_by: str
    policy_key: str = Field(default="general")  # hire | spend | publish | io
    risk_level: str = Field(default="medium")  # low | medium | high
    payload_json: str = Field(default="{}")
    status: str = Field(default="PENDING", index=True)  # PENDING | APPROVED | REJECTED
    decided_by: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)
    decided_at: datetime | None = Field(default=None)


class Integration(SQLModel, table=True):
    """Per-company capability binding. Agents never see raw secrets."""

    __tablename__ = "integrations"

    id: int | None = Field(default=None, primary_key=True)
    company_id: str = Field(index=True)
    provider: str = Field(index=True)  # email | telegram | github | ...
    capability: str = Field(index=True)  # send_customer_email | publish_listing | ...
    secret_ref: str  # path/key only, never the secret text
    status: str = Field(default="active")
    created_at: datetime = Field(default_factory=utc_now)


class AgentRun(SQLModel, table=True):
    """A single model invocation by an agent. Spend is tagged per company/agent/task."""

    __tablename__ = "agent_runs"

    id: int | None = Field(default=None, primary_key=True)
    company_id: str = Field(index=True)
    agent_id: str = Field(index=True)
    task_id: int | None = Field(default=None)
    model_id: str | None = Field(default=None)
    trace_id: str | None = Field(default=None)
    started_at: datetime = Field(default_factory=utc_now)
    ended_at: datetime | None = Field(default=None)
    input_tokens: int = Field(default=0)
    output_tokens: int = Field(default=0)
    cost: float = Field(default=0.0)
    outcome: str = Field(default="ok")  # ok | error | blocked | timeout


# --------------------------------------------------------------------------- #
# Company context
# --------------------------------------------------------------------------- #
class CompanyContext:
    """Mandatory isolation context. A missing company id is a bug, not a default.

    Every service/repository method takes a ``CompanyContext`` and scopes every
    query by ``company_id``. See SPEC §4.
    """

    __slots__ = ("company_id", "actor", "trace_id")

    def __init__(
        self,
        company_id: str,
        *,
        actor: str = "system",
        trace_id: str | None = None,
    ) -> None:
        if not company_id:
            raise ValueError("CompanyContext requires a non-empty company_id")
        self.company_id = company_id
        self.actor = actor
        self.trace_id = trace_id

    def __repr__(self) -> str:
        return f"CompanyContext(company_id={self.company_id!r}, actor={self.actor!r})"


ALL_MODELS = [
    Company,
    CompanyFloor,
    Room,
    Team,
    Agent,
    Desk,
    Task,
    Event,
    Artifact,
    Approval,
    Integration,
    AgentRun,
]
