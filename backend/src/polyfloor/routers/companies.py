"""Company, room, agent, and avatar endpoints.

All endpoints are company-scoped via :class:`CompanyContext`. Creating a company
materializes the full org + gated pipeline. See SPEC §3, §9.
"""

from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..agents.executor import advance_task
from ..assets.avatar_composer import avatar_file_path, is_path_in_company
from ..db import get_session
from ..db.models import CompanyContext
from ..observability import update_company_metrics
from ..services import bootstrap
from ..services import repository as repo
from ..services.event_bus import event_bus
from ..services.hr import execute_hire, request_hire, retire_agent

router = APIRouter(prefix="/companies", tags=["companies"])

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slugify(name: str) -> str:
    return _SLUG_RE.sub("-", name.lower()).strip("-") or "company"


def _ctx(cid: str) -> CompanyContext:
    return CompanyContext(cid)


# --------------------------------------------------------------------------- #
# Company directory + creation
# --------------------------------------------------------------------------- #
class CompanyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    goal: str = Field(default="", max_length=400)
    template_id: str = Field(default="digital-products")
    grilling_intensity: int = Field(default=1, ge=0, le=3)
    budget_policy: dict = Field(default_factory=dict)
    channels: list = Field(default_factory=list)
    logo: str | None = None


class CompanyCard(BaseModel):
    id: str
    name: str
    slug: str
    template_id: str
    goal: str
    status: str


@router.get("", response_model=list[CompanyCard])
async def list_companies(session: AsyncSession = Depends(get_session)):
    companies = await repo.list_companies(session)
    return [CompanyCard(**c.model_dump()) for c in companies]


@router.post("", response_model=CompanyCard, status_code=status.HTTP_201_CREATED)
async def create_company(
    body: CompanyCreate,
    session: AsyncSession = Depends(get_session),
):
    company_id = f"co_{_slugify(body.name)}"
    # Avoid id collisions on repeated names.
    existing = await repo.list_companies(session)
    ids = {c.id for c in existing}
    n = 2
    base = company_id
    while company_id in ids:
        company_id = f"{base}_{n}"
        n += 1

    company = await bootstrap.bootstrap_company(
        session,
        company_id=company_id,
        name=body.name,
        slug=_slugify(f"{body.name} {company_id[-4:]}"),
        goal=body.goal or f"Build and ship digital products for {body.name}",
        template_id=body.template_id,
        grilling_intensity=body.grilling_intensity,
        budget_policy=body.budget_policy,
        channels=body.channels,
        logo=body.logo,
    )
    return CompanyCard(**company.model_dump())


@router.get("/{company_id}/state")
async def company_state(
    company_id: str,
    session: AsyncSession = Depends(get_session),
):
    ctx = _ctx(company_id)
    try:
        snapshot = await repo.company_state(session, ctx)
    except LookupError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "company not found") from None
    update_company_metrics(company_id, snapshot)
    return snapshot


# --------------------------------------------------------------------------- #
# Rooms + agents
# --------------------------------------------------------------------------- #
@router.get("/{company_id}/rooms/{room_id}")
async def room_detail(
    company_id: str,
    room_id: str,
    session: AsyncSession = Depends(get_session),
):
    ctx = _ctx(company_id)
    room = await repo.get_room(session, ctx, room_id)
    if room is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "room not found")
    desks = await repo.list_desks(session, ctx, room_id)
    agents = await repo.list_agents_in_room(session, ctx, room_id)
    tasks = []
    if room.team_id:
        team_tasks = await repo.list_tasks(session, ctx)
        tasks = [t for t in team_tasks if t.team_id == room.team_id]
    in_progress = sum(1 for t in tasks if t.status == "IN_PROGRESS")
    return {
        "room": room.model_dump(),
        "desks": [d.model_dump() for d in desks],
        "agents": [a.model_dump() for a in agents],
        "tasks": [t.model_dump() for t in tasks],
        "wip": {"in_progress": in_progress, "limit": room.wip_limit},
    }


@router.get("/{company_id}/agents/{agent_id}")
async def agent_dossier(
    company_id: str,
    agent_id: str,
    session: AsyncSession = Depends(get_session),
):
    ctx = _ctx(company_id)
    agent = await repo.get_agent(session, ctx, agent_id)
    if agent is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "agent not found")
    runs = await repo.list_agent_runs(session, ctx)
    agent_runs = [r for r in runs if r.agent_id == agent_id][:20]
    return {
        "agent": agent.model_dump(),
        "runs": [r.model_dump() for r in agent_runs],
    }


@router.get("/{company_id}/avatars/{agent_id}.png")
async def serve_avatar(company_id: str, agent_id: str):
    path = avatar_file_path(company_id, agent_id)
    if not is_path_in_company(company_id, path) or not path.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "avatar not found")
    return Response(content=path.read_bytes(), media_type="image/png")


# --------------------------------------------------------------------------- #
# Action dispatch (POST /api/actions is in actions router; here are the
# company-scoped helpers used by it)
# --------------------------------------------------------------------------- #


async def dispatch_action(
    session: AsyncSession,
    ctx: CompanyContext,
    action: str,
    target_type: str,
    target_id: str,
    payload: dict,
) -> dict:
    """Execute a company-scoped action. Raises on policy violations."""
    if action == "approve":
        approval = await repo.resolve_approval(session, ctx, int(target_id), "APPROVED", ctx.actor)
        await event_bus.publish(
            ctx,
            "approval.resolved",
            {"approval_id": approval.id, "decision": "APPROVED"},
            source_agent_id="user",
        )
        return {"approval": approval.model_dump()}

    if action == "reject":
        approval = await repo.resolve_approval(session, ctx, int(target_id), "REJECTED", ctx.actor)
        await event_bus.publish(
            ctx,
            "approval.resolved",
            {"approval_id": approval.id, "decision": "REJECTED"},
            source_agent_id="user",
        )
        return {"approval": approval.model_dump()}

    if action == "pause":
        agent = await repo.set_agent_state(session, ctx, target_id, "paused")
        if agent is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "agent not found")
        await event_bus.publish(
            ctx, "agent.paused", {"agent_id": target_id}, source_agent_id="user"
        )
        return {"agent": agent.model_dump()}

    if action == "resume":
        agent = await repo.set_agent_state(session, ctx, target_id, "idle")
        if agent is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "agent not found")
        await event_bus.publish(
            ctx, "agent.resumed", {"agent_id": target_id}, source_agent_id="user"
        )
        return {"agent": agent.model_dump()}

    if action == "stop":
        agent = await retire_agent(session, ctx, target_id)
        if agent is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "agent not found")
        return {"agent": agent.model_dump()}

    if action == "advance_task":
        task = await advance_task(session, ctx, int(target_id))
        return {"task": task.model_dump()}

    if action == "request_hire":
        approval = await request_hire(
            session,
            ctx,
            team_id=payload["team_id"],
            role=payload.get("role", "worker"),
            requested_by=ctx.actor,
            reason=payload.get("reason", ""),
            budget_usd=payload.get("budget_usd", 1.0),
        )
        return {"approval": approval.model_dump()}

    if action == "execute_hire":
        agent = await execute_hire(
            session,
            ctx,
            approval_id=int(payload["approval_id"]),
            agent_id=payload.get("agent_id", target_id),
            name=payload.get("name", "New Worker"),
            role=payload.get("role", "worker"),
            team_id=payload["team_id"],
            room_id=payload["room_id"],
            model_id=payload.get("model_id"),
        )
        return {"agent": agent.model_dump()}

    raise HTTPException(status.HTTP_400_BAD_REQUEST, f"unknown action: {action}")
