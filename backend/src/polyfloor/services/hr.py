"""HR coordinator service.

Team leads request specialists; only HR creates/retires workers and grants
capabilities. Hire/spend routes through the approval queue. See SPEC §5.
"""

from __future__ import annotations

import json

from sqlalchemy.ext.asyncio import AsyncSession

from ..assets.avatar_composer import compose_avatar
from ..db.models import Agent, Approval, CompanyContext
from . import repository as repo
from .event_bus import event_bus


async def request_hire(
    session: AsyncSession,
    ctx: CompanyContext,
    *,
    team_id: str,
    role: str,
    requested_by: str,
    reason: str = "",
    budget_usd: float = 1.0,
) -> Approval:
    """A team lead requests a specialist. Creates a PENDING approval + event.

    Does NOT create the worker — only HR may do that, and only after approval.
    """
    approval = await repo.create_approval(
        session,
        Approval(
            company_id=ctx.company_id,
            requested_by=requested_by,
            policy_key="hire",
            risk_level="medium" if budget_usd <= 5.0 else "high",
            payload_json=json.dumps(
                {"team_id": team_id, "role": role, "reason": reason, "budget_usd": budget_usd}
            ),
        ),
    )
    await event_bus.publish(
        ctx,
        "staffing.requested",
        {"approval_id": approval.id, "team_id": team_id, "role": role, "reason": reason},
        source_agent_id=requested_by,
        target_type="role",
        target_id="hr",
        correlation_id=str(approval.id),
        requires_approval=True,
    )
    return approval


async def execute_hire(
    session: AsyncSession,
    ctx: CompanyContext,
    *,
    approval_id: int,
    agent_id: str,
    name: str,
    role: str,
    team_id: str,
    room_id: str,
    desk_id: str | None = None,
    model_id: str | None = None,
) -> Agent:
    """HR materializes a worker after an approved hire request.

    Assigns a vacant desk, composes an avatar, and binds the default capability
    profile. The hire is logged as an event.
    """
    # Resolve the approval (must be in this company and approved).
    approvals = await repo.list_approvals(session, ctx)
    matching = [a for a in approvals if a.id == approval_id]
    if not matching:
        raise LookupError(f"approval {approval_id} not found in company {ctx.company_id}")
    approval = matching[0]
    if approval.status != "APPROVED":
        raise PermissionError(f"approval {approval_id} is {approval.status}, not APPROVED")

    # Pick the first vacant desk in the room if none specified.
    desks = await repo.list_desks(session, ctx, room_id)
    vacant = [d for d in desks if d.agent_id is None]
    desk = None
    if desk_id:
        desk = next((d for d in vacant if d.id == desk_id), None)
    if desk is None and vacant:
        desk = vacant[0]
    if desk is None:
        raise PermissionError(f"no vacant desk in room {room_id}")

    avatar_uri = compose_avatar(ctx.company_id, agent_id, role)
    agent = Agent(
        id=agent_id,
        company_id=ctx.company_id,
        team_id=team_id,
        role=role,
        name=name,
        model_id=model_id,
        avatar_recipe=json.dumps({"role": role, "seed": f"{ctx.company_id}:{agent_id}"}),
        avatar_uri=avatar_uri,
        state="idle",
        home_room_id=room_id,
        home_desk_id=desk.id,
    )
    await repo.create_agent(session, agent)
    desk.agent_id = agent_id
    session.add(desk)
    await session.commit()

    await event_bus.publish(
        ctx,
        "hr.hired",
        {"agent_id": agent_id, "role": role, "team_id": team_id, "desk_id": desk.id},
        source_agent_id="hr",
        target_type="team",
        target_id=team_id,
        correlation_id=str(approval_id),
    )
    return agent


async def retire_agent(
    session: AsyncSession,
    ctx: CompanyContext,
    agent_id: str,
) -> Agent | None:
    """HR retires a worker (does not delete — preserves audit trail)."""
    from datetime import UTC, datetime

    agent = await repo.set_agent_state(session, ctx, agent_id, "retired")
    if agent is not None:
        agent.retired_at = datetime.now(UTC)
        session.add(agent)
        await session.commit()
        await event_bus.publish(
            ctx,
            "hr.retired",
            {"agent_id": agent_id},
            source_agent_id="hr",
        )
    return agent
