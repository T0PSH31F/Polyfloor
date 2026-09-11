"""Company templates and tenant bootstrap.

Creating a company materializes the org graph (CEO, HR, C-suite, team leads),
the visual layout (one lobby floor + rooms + desks), and the seed work systems
(tasks, events, approvals). Templates are declarative; HR is the only role that
creates/retires workers and grants capabilities. See SPEC §7, §6.3.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from ..assets.avatar_composer import compose_avatar
from ..db.models import (
    Agent,
    Approval,
    Company,
    CompanyContext,
    CompanyFloor,
    Desk,
    Event,
    Room,
    Task,
    Team,
)
from . import repository as repo

# --------------------------------------------------------------------------- #
# Template definitions
# --------------------------------------------------------------------------- #


@dataclass
class TeamSpec:
    id: str
    name: str
    role_type: str
    lead_role: str


@dataclass
class Template:
    id: str
    label: str
    teams: list[TeamSpec]
    pipeline: list[str] = field(default_factory=list)  # ordered stage labels


DIGITAL_PRODUCTS = Template(
    id="digital-products",
    label="Digital Products",
    teams=[
        TeamSpec("rnd", "R&D", "rnd", "lead"),
        TeamSpec("product", "Product & Writing", "product", "lead"),
        TeamSpec("qa", "QA Panel", "qa", "lead"),
        TeamSpec("marketing", "Marketing", "marketing", "lead"),
    ],
    # Direct production line (SPEC §6.3): research -> spec -> draft -> QA -> campaign -> publish
    pipeline=["research", "spec", "draft", "qa", "campaign", "publish"],
)

TEMPLATES: dict[str, Template] = {
    "digital-products": DIGITAL_PRODUCTS,
}


def get_template(template_id: str) -> Template:
    if template_id not in TEMPLATES:
        # Custom prompt: synthesize a digital-products-like org.
        return DIGITAL_PRODUCTS
    return TEMPLATES[template_id]


# --------------------------------------------------------------------------- #
# Bootstrap
# --------------------------------------------------------------------------- #


async def bootstrap_company(
    session: AsyncSession,
    *,
    company_id: str,
    name: str,
    slug: str,
    goal: str,
    template_id: str = "digital-products",
    grilling_intensity: int = 1,
    budget_policy: dict | None = None,
    channels: list | None = None,
    logo: str | None = None,
) -> Company:
    """Create a company tenant and materialize its org + work systems."""
    template = get_template(template_id)

    company = Company(
        id=company_id,
        name=name,
        slug=slug,
        template_id=template.id,
        goal=goal,
        grilling_intensity=grilling_intensity,
        budget_policy_json=json.dumps(budget_policy or {}),
        channels_json=json.dumps(channels or []),
        logo=logo,
    )
    await repo.create_company(session, company)
    ctx = CompanyContext(company_id, actor="hr")

    # --- Visual layout: one lobby floor + rooms ---
    floor = await repo.create_floor(
        session,
        CompanyFloor(
            id=f"{company_id}_f1",
            company_id=company_id,
            ordinal=1,
            label="Lobby",
            template_id=template.id,
        ),
    )

    rooms: dict[str, Room] = {}
    # C-suite, CEO, HR, QA rooms first.
    for room_id, label, rtype in [
        ("ceo", "CEO Suite", "ceo"),
        ("hr", "HR Suite", "hr"),
        ("csuite", "C-Suite", "csuite"),
        ("qa", "QA Panel", "qa"),
    ]:
        rooms[room_id] = await repo.create_room(
            session,
            Room(
                id=f"{company_id}_{room_id}",
                company_id=company_id,
                company_floor_id=floor.id,
                room_type=rtype,
                label=label,
            ),
        )

    # Team rooms + lead + 5 vacant worker desks.
    for spec in template.teams:
        room = await repo.create_room(
            session,
            Room(
                id=f"{company_id}_team_{spec.id}",
                company_id=company_id,
                company_floor_id=floor.id,
                team_id=f"{company_id}_team_{spec.id}",
                room_type="team",
                label=f"{spec.name} Suite",
                wip_limit=3,
            ),
        )
        rooms[spec.id] = room
        team = await repo.create_team(
            session,
            Team(
                id=f"{company_id}_team_{spec.id}",
                company_id=company_id,
                name=spec.name,
                role_type=spec.role_type,
                room_id=room.id,
            )
        )
        # Lead desk (ordinal 0) + 5 worker desks.
        for ordinal in range(6):
            session.add(
                Desk(
                    id=f"{company_id}_desk_{spec.id}_{ordinal}",
                    company_id=company_id,
                    room_id=room.id,
                    ordinal=ordinal,
                )
            )
        await session.commit()
        # Assign lead to the team.
        team.lead_agent_id = f"{company_id}_{spec.id}_lead"
        session.add(team)
        await session.commit()

    # --- Agents: CEO, HR, C-suite, team leads ---
    agent_specs = [
        ("ceo", "CEO", "ceo", "ceo"),
        ("hr", "HR Coordinator", "hr", "hr"),
        ("cfo", "CFO", "cfo", "csuite"),
        ("cto", "CTO", "cto", "csuite"),
        ("coo", "COO", "coo", "csuite"),
        ("cho", "CHO", "cho", "csuite"),
    ]
    for spec in template.teams:
        agent_specs.append((f"{spec.id}_lead", f"{spec.name} Lead", spec.lead_role, spec.id))

    created_agents: dict[str, Agent] = {}
    for aid, aname, arole, room_key in agent_specs:
        room = rooms[room_key]
        avatar_uri = compose_avatar(company_id, f"{company_id}_{aid}", arole)
        agent = Agent(
            id=f"{company_id}_{aid}",
            company_id=company_id,
            team_id=(
                f"{company_id}_team_{room_key}" if room_key in {t.id for t in template.teams} else None
            ),
            role=arole,
            name=aname,
            model_id=None,  # workers default to free/fast; HR uses mimo-v2.5-pro
            avatar_recipe=json.dumps({"role": arole, "seed": f"{company_id}:{aid}"}),
            avatar_uri=avatar_uri,
            state="idle",
            home_room_id=room.id,
            home_desk_id=f"{company_id}_desk_{room_key}_0",
        )
        await repo.create_agent(session, agent)
        created_agents[aid] = agent

    # Assign the HR model to the HR coordinator.
    from ..config import get_settings

    hr_model = get_settings().default_hr_model
    await repo.update_agent_model(session, ctx, f"{company_id}_hr", hr_model)

    # --- Seed the gated production pipeline as a task DAG ---
    pipeline_stages = list(enumerate(template.pipeline))
    owner_by_stage = {
        "research": ("rnd", f"{company_id}_rnd_lead"),
        "spec": ("product", f"{company_id}_product_lead"),
        "draft": ("product", f"{company_id}_product_lead"),
        "qa": ("qa", f"{company_id}_qa_lead"),
        "campaign": ("marketing", f"{company_id}_marketing_lead"),
        "publish": ("marketing", f"{company_id}_marketing_lead"),
    }
    task_ids: list[int] = []
    prev_id: int | None = None
    last_idx = len(template.pipeline) - 1
    for idx, stage in pipeline_stages:
        team_key, owner = owner_by_stage[stage]
        if idx == 0:
            status = "READY"
        elif idx == last_idx:
            # The publish stage is gated from the start (irreversible I/O).
            status = "AWAITING_APPROVAL"
        else:
            status = "BACKLOG"
        task = Task(
            company_id=company_id,
            team_id=f"{company_id}_team_{team_key}",
            owner_agent_id=owner,
            parent_task_id=prev_id,
            title=f"{stage.capitalize()} — {goal}" if idx == 0 else f"{stage.capitalize()}",
            description=f"Stage {idx + 1}/{len(template.pipeline)}: {stage} for: {goal}",
            status=status,
            priority=10 - idx,
            acceptance_criteria_json=json.dumps(
                [f"{stage} artifact reviewed and approved"]
            ),
            budget_limit=1.0,
            retry_limit=2,
            trace_id=f"{company_id}-pipeline",
        )
        await repo.create_task(session, task)
        task_ids.append(task.id if task.id is not None else 0)
        prev_id = task.id

    # The final publish stage is gated (AWAITING_APPROVAL) — irreversible I/O.
    if task_ids:
        last = task_ids[-1]
        await repo.create_approval(
            session,
            Approval(
                company_id=company_id,
                task_id=last,
                requested_by=f"{company_id}_marketing_lead",
                policy_key="publish",
                risk_level="high",
                payload_json=json.dumps({"stage": "publish", "target": goal}),
            )
        )

    # --- Seed events ---
    for evt_type, payload in [
        ("company.created", {"name": name, "template": template.id}),
        ("hr.hired", {"agents": [a.id for a in created_agents.values()]}),
        ("pipeline.seeded", {"stages": template.pipeline}),
    ]:
        session.add(
            Event(
                company_id=company_id,
                event_type=evt_type,
                payload_json=json.dumps(payload, default=str),
                target_type="system",
            )
        )
    await session.commit()

    return company
