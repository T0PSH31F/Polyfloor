"""Tests for WIP limit enforcement and task transitions (SPEC §6.2)."""

from __future__ import annotations

import pytest

from polyfloor.db.models import CompanyContext, Task
from polyfloor.services import bootstrap
from polyfloor.services import repository as repo


async def test_wip_limit_blocks_fourth_in_progress(test_session):
    await bootstrap.bootstrap_company(
        test_session,
        company_id="co_wip",
        name="WipCo",
        slug="wipco",
        goal="test wip",
    )
    ctx = CompanyContext("co_wip")
    tasks = await repo.list_tasks(test_session, ctx)
    team_id = tasks[0].team_id
    assert team_id is not None

    # Create three tasks and start them — the limit is 3.
    started = []
    for i in range(3):
        t = await repo.create_task(
            test_session,
            Task(
                company_id="co_wip",
                team_id=team_id,
                owner_agent_id="co_wip_rnd_lead",
                title=f"Extra {i}",
                status="READY",
            ),
        )
        t = await repo.transition_task(test_session, ctx, t.id, "IN_PROGRESS", wip_limit=3, team_id=team_id)  # type: ignore[arg-type]
        started.append(t)
    assert len(started) == 3

    # A fourth IN_PROGRESS must be rejected.
    fourth = await repo.create_task(
        test_session,
        Task(
            company_id="co_wip",
            team_id=team_id,
            owner_agent_id="co_wip_rnd_lead",
            title="Extra 3",
            status="READY",
        )
    )
    with pytest.raises(PermissionError):
        await repo.transition_task(
            test_session, ctx, fourth.id, "IN_PROGRESS", wip_limit=3, team_id=team_id  # type: ignore[arg-type]
        )


async def test_invalid_transition_rejected(test_session):
    await bootstrap.bootstrap_company(
        test_session, company_id="co_t", name="T", slug="t", goal="x"
    )
    ctx = CompanyContext("co_t")
    tasks = await repo.list_tasks(test_session, ctx)
    first = tasks[0]
    # BACKLOG -> DONE is not allowed (must go through READY).
    if first.status == "BACKLOG":
        with pytest.raises(ValueError):
            await repo.transition_task(test_session, ctx, first.id, "DONE")  # type: ignore[arg-type]
