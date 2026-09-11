"""Company-scoped repository functions.

Every function takes a :class:`CompanyContext` and an async session, and scopes
every query by ``company_id``. A query that would cross a company boundary
returns nothing (or raises) — never another tenant's data. See SPEC §4.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func

from ..db.models import (
    Agent,
    AgentRun,
    Approval,
    Artifact,
    Company,
    CompanyContext,
    CompanyFloor,
    Desk,
    Event,
    Room,
    Task,
    Team,
)

VALID_TRANSITIONS: dict[str, set[str]] = {
    "BACKLOG": {"READY"},
    "READY": {"IN_PROGRESS", "BLOCKED", "BACKLOG"},
    "IN_PROGRESS": {"REVIEW", "BLOCKED", "DONE"},
    "REVIEW": {"AWAITING_APPROVAL", "IN_PROGRESS", "DONE"},
    "AWAITING_APPROVAL": {"DONE", "IN_PROGRESS"},
    "BLOCKED": {"READY", "BACKLOG"},
    "DONE": {"BACKLOG"},
}


# --------------------------------------------------------------------------- #
# Companies
# --------------------------------------------------------------------------- #
async def create_company(
    session: AsyncSession,
    company: Company,
) -> Company:
    session.add(company)
    await session.commit()
    await session.refresh(company)
    return company


async def get_company(session: AsyncSession, ctx: CompanyContext) -> Company | None:
    res = await session.execute(select(Company).where(Company.id == ctx.company_id))
    return res.scalar_one_or_none()


async def list_companies(session: AsyncSession) -> list[Company]:
    res = await session.execute(select(Company).where(Company.status == "active"))
    return list(res.scalars().all())


# --------------------------------------------------------------------------- #
# Floors / rooms / teams
# --------------------------------------------------------------------------- #
async def create_floor(session: AsyncSession, floor: CompanyFloor) -> CompanyFloor:
    session.add(floor)
    await session.commit()
    await session.refresh(floor)
    return floor


async def list_floors(session: AsyncSession, ctx: CompanyContext) -> list[CompanyFloor]:
    res = await session.execute(
        select(CompanyFloor)
        .where(CompanyFloor.company_id == ctx.company_id)
        .order_by(CompanyFloor.ordinal)
    )
    return list(res.scalars().all())


async def create_room(session: AsyncSession, room: Room) -> Room:
    session.add(room)
    await session.commit()
    await session.refresh(room)
    return room


async def list_rooms(session: AsyncSession, ctx: CompanyContext) -> list[Room]:
    res = await session.execute(
        select(Room).where(Room.company_id == ctx.company_id).order_by(Room.label)
    )
    return list(res.scalars().all())


async def get_room(session: AsyncSession, ctx: CompanyContext, room_id: str) -> Room | None:
    res = await session.execute(
        select(Room).where(Room.id == room_id, Room.company_id == ctx.company_id)
    )
    return res.scalar_one_or_none()


async def create_team(session: AsyncSession, team: Team) -> Team:
    session.add(team)
    await session.commit()
    await session.refresh(team)
    return team


async def list_teams(session: AsyncSession, ctx: CompanyContext) -> list[Team]:
    res = await session.execute(select(Team).where(Team.company_id == ctx.company_id))
    return list(res.scalars().all())


async def list_desks(session: AsyncSession, ctx: CompanyContext, room_id: str) -> list[Desk]:
    res = await session.execute(
        select(Desk)
        .where(Desk.company_id == ctx.company_id, Desk.room_id == room_id)
        .order_by(Desk.ordinal)
    )
    return list(res.scalars().all())


# --------------------------------------------------------------------------- #
# Agents
# --------------------------------------------------------------------------- #
async def create_agent(session: AsyncSession, agent: Agent) -> Agent:
    session.add(agent)
    await session.commit()
    await session.refresh(agent)
    return agent


async def get_agent(session: AsyncSession, ctx: CompanyContext, agent_id: str) -> Agent | None:
    res = await session.execute(
        select(Agent).where(Agent.id == agent_id, Agent.company_id == ctx.company_id)
    )
    return res.scalar_one_or_none()


async def list_agents(session: AsyncSession, ctx: CompanyContext) -> list[Agent]:
    res = await session.execute(
        select(Agent).where(Agent.company_id == ctx.company_id, Agent.state != "retired")
    )
    return list(res.scalars().all())


async def list_agents_in_room(
    session: AsyncSession, ctx: CompanyContext, room_id: str
) -> list[Agent]:
    res = await session.execute(
        select(Agent).where(
            Agent.company_id == ctx.company_id,
            Agent.home_room_id == room_id,
            Agent.state != "retired",
        )
    )
    return list(res.scalars().all())


async def update_agent_model(
    session: AsyncSession, ctx: CompanyContext, agent_id: str, model_id: str
) -> Agent:
    """Scoped model update. Raises if the agent is not in this company."""
    agent = await get_agent(session, ctx, agent_id)
    if agent is None:
        raise LookupError(f"agent {agent_id} not found in company {ctx.company_id}")
    agent.model_id = model_id
    await session.commit()
    await session.refresh(agent)
    return agent


async def set_agent_state(
    session: AsyncSession, ctx: CompanyContext, agent_id: str, state: str
) -> Agent | None:
    agent = await get_agent(session, ctx, agent_id)
    if agent is None:
        return None
    agent.state = state
    await session.commit()
    await session.refresh(agent)
    return agent


# --------------------------------------------------------------------------- #
# Tasks (Kanban)
# --------------------------------------------------------------------------- #
async def create_task(session: AsyncSession, task: Task) -> Task:
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


async def list_tasks(session: AsyncSession, ctx: CompanyContext) -> list[Task]:
    res = await session.execute(
        select(Task).where(Task.company_id == ctx.company_id).order_by(Task.priority.desc())
    )
    return list(res.scalars().all())


async def get_task(session: AsyncSession, ctx: CompanyContext, task_id: int) -> Task | None:
    res = await session.execute(
        select(Task).where(Task.id == task_id, Task.company_id == ctx.company_id)
    )
    return res.scalar_one_or_none()


async def count_in_progress(session: AsyncSession, ctx: CompanyContext, team_id: str) -> int:
    res = await session.execute(
        select(func.count())
        .select_from(Task)
        .where(
            Task.company_id == ctx.company_id,
            Task.team_id == team_id,
            Task.status == "IN_PROGRESS",
        )
    )
    return int(res.scalar_one())


async def transition_task(
    session: AsyncSession,
    ctx: CompanyContext,
    task_id: int,
    new_status: str,
    *,
    wip_limit: int = 3,
    team_id: str | None = None,
) -> Task:
    """Transition a task, enforcing the WIP limit on entry to IN_PROGRESS.

    Over-capacity work stays READY/BLOCKED; it must never auto-spawn workers.
    """
    task = await get_task(session, ctx, task_id)
    if task is None:
        raise LookupError(f"task {task_id} not found in company {ctx.company_id}")
    if new_status not in VALID_TRANSITIONS.get(task.status, set()):
        raise ValueError(f"invalid transition {task.status} -> {new_status}")
    if new_status == "IN_PROGRESS":
        tid = team_id or task.team_id
        if tid:
            current = await count_in_progress(session, ctx, tid)
            if current >= wip_limit:
                raise PermissionError(
                    f"WIP limit reached ({current}/{wip_limit}) for team {tid}"
                )
    task.status = new_status
    task.updated_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(task)
    return task


# --------------------------------------------------------------------------- #
# Events
# --------------------------------------------------------------------------- #
async def list_events(
    session: AsyncSession, ctx: CompanyContext, limit: int = 100
) -> list[Event]:
    res = await session.execute(
        select(Event)
        .where(Event.company_id == ctx.company_id)
        .order_by(Event.id.desc())
        .limit(limit)
    )
    return list(res.scalars().all())


# --------------------------------------------------------------------------- #
# Artifacts
# --------------------------------------------------------------------------- #
async def create_artifact(session: AsyncSession, artifact: Artifact) -> Artifact:
    session.add(artifact)
    await session.commit()
    await session.refresh(artifact)
    return artifact


async def list_artifacts(session: AsyncSession, ctx: CompanyContext) -> list[Artifact]:
    res = await session.execute(
        select(Artifact).where(Artifact.company_id == ctx.company_id).order_by(Artifact.id.desc())
    )
    return list(res.scalars().all())


async def get_artifact(
    session: AsyncSession, ctx: CompanyContext, artifact_id: int
) -> Artifact | None:
    res = await session.execute(
        select(Artifact).where(
            Artifact.id == artifact_id, Artifact.company_id == ctx.company_id
        )
    )
    return res.scalar_one_or_none()


# --------------------------------------------------------------------------- #
# Approvals
# --------------------------------------------------------------------------- #
async def create_approval(session: AsyncSession, approval: Approval) -> Approval:
    session.add(approval)
    await session.commit()
    await session.refresh(approval)
    return approval


async def list_approvals(
    session: AsyncSession, ctx: CompanyContext, status: str | None = None
) -> list[Approval]:
    stmt = select(Approval).where(Approval.company_id == ctx.company_id)
    if status:
        stmt = stmt.where(Approval.status == status)
    stmt = stmt.order_by(Approval.id.desc())
    res = await session.execute(stmt)
    return list(res.scalars().all())


async def resolve_approval(
    session: AsyncSession,
    ctx: CompanyContext,
    approval_id: int,
    decision: str,
    decided_by: str,
) -> Approval:
    res = await session.execute(
        select(Approval).where(
            Approval.id == approval_id, Approval.company_id == ctx.company_id
        )
    )
    approval = res.scalar_one_or_none()
    if approval is None:
        raise LookupError(f"approval {approval_id} not found in company {ctx.company_id}")
    if approval.status != "PENDING":
        raise ValueError(f"approval {approval_id} already {approval.status}")
    if decision not in ("APPROVED", "REJECTED"):
        raise ValueError(f"invalid decision {decision}")
    approval.status = decision
    approval.decided_by = decided_by
    approval.decided_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(approval)
    return approval


# --------------------------------------------------------------------------- #
# Agent runs
# --------------------------------------------------------------------------- #
async def create_agent_run(session: AsyncSession, run: AgentRun) -> AgentRun:
    session.add(run)
    await session.commit()
    await session.refresh(run)
    return run


async def list_agent_runs(
    session: AsyncSession, ctx: CompanyContext, limit: int = 100
) -> list[AgentRun]:
    res = await session.execute(
        select(AgentRun)
        .where(AgentRun.company_id == ctx.company_id)
        .order_by(AgentRun.id.desc())
        .limit(limit)
    )
    return list(res.scalars().all())


# --------------------------------------------------------------------------- #
# Full state snapshot (for GET /api/companies/{id}/state)
# --------------------------------------------------------------------------- #
async def company_state(session: AsyncSession, ctx: CompanyContext) -> dict[str, Any]:
    """Return the full frontend snapshot for a company."""
    company = await get_company(session, ctx)
    if company is None:
        raise LookupError(f"company {ctx.company_id} not found")
    floors = await list_floors(session, ctx)
    rooms = await list_rooms(session, ctx)
    teams = await list_teams(session, ctx)
    agents = await list_agents(session, ctx)
    tasks = await list_tasks(session, ctx)
    events = await list_events(session, ctx, limit=50)
    artifacts = await list_artifacts(session, ctx)
    approvals = await list_approvals(session, ctx)

    def _model(m: Any) -> dict[str, Any]:
        d = m.model_dump()
        for k, v in list(d.items()):
            if isinstance(v, datetime):
                d[k] = v.isoformat()
        return d

    return {
        "company": _model(company),
        "floors": [_model(f) for f in floors],
        "rooms": [_model(r) for r in rooms],
        "teams": [_model(t) for t in teams],
        "agents": [_model(a) for a in agents],
        "tasks": [_model(t) for t in tasks],
        "events": [_model(e) for e in events],
        "artifacts": [_model(a) for a in artifacts],
        "approvals": [_model(a) for a in approvals],
        "metrics": _metrics(tasks, agents, approvals),
    }


def _metrics(tasks: list[Task], agents: list[Agent], approvals: list[Approval]) -> dict[str, Any]:
    by_status: dict[str, int] = {}
    for t in tasks:
        by_status[t.status] = by_status.get(t.status, 0) + 1
    active_agents = sum(1 for a in agents if a.state == "working")
    pending = sum(1 for a in approvals if a.status == "PENDING")
    return {
        "tasks_by_status": by_status,
        "active_agents": active_agents,
        "total_agents": len(agents),
        "pending_approvals": pending,
    }


# --------------------------------------------------------------------------- #
# Serialization helper
# --------------------------------------------------------------------------- #
def to_dict(model: Any) -> dict[str, Any]:
    d = model.model_dump()
    for k, v in list(d.items()):
        if isinstance(v, datetime):
            d[k] = v.isoformat()
        elif isinstance(v, (list, dict)) and not isinstance(v, str):
            d[k] = v
    return d


def parse_json(field: str | None) -> Any:
    if not field:
        return None
    try:
        return json.loads(field)
    except Exception:
        return None
