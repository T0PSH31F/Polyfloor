"""Tests for the digital-products bootstrap (SPEC §6.3, §7)."""

from __future__ import annotations

from polyfloor.db.models import CompanyContext
from polyfloor.services import bootstrap, repository as repo


async def test_bootstrap_creates_full_org(test_session):
    company = await bootstrap.bootstrap_company(
        test_session,
        company_id="co_dp",
        name="Lumin Press",
        slug="lumin-press",
        goal="ship a digital product",
    )
    assert company.id == "co_dp"
    ctx = CompanyContext("co_dp")

    agents = await repo.list_agents(test_session, ctx)
    roles = {a.role for a in agents}
    assert "ceo" in roles
    assert "hr" in roles
    assert {"cfo", "cto", "coo", "cho"} <= roles
    # Team leads present.
    assert any(a.role == "lead" for a in agents)

    teams = await repo.list_teams(test_session, ctx)
    team_ids = {t.id for t in teams}
    assert "co_dp_team_rnd" in team_ids
    assert "co_dp_team_product" in team_ids
    assert "co_dp_team_qa" in team_ids
    assert "co_dp_team_marketing" in team_ids


async def test_bootstrap_seeds_gated_pipeline(test_session):
    await bootstrap.bootstrap_company(
        test_session, company_id="co_pipe", name="Pipe", slug="pipe", goal="ship"
    )
    ctx = CompanyContext("co_pipe")
    tasks = await repo.list_tasks(test_session, ctx)
    titles = [t.title.lower() for t in tasks]
    # The direct production line is seeded.
    assert any("research" in t for t in titles)
    assert any("spec" in t for t in titles)
    assert any("draft" in t for t in titles)
    assert any("qa" in t for t in titles)
    assert any("campaign" in t for t in titles)
    assert any("publish" in t for t in titles)

    # The publish stage is gated.
    approvals = await repo.list_approvals(test_session, ctx)
    assert any(a.policy_key == "publish" for a in approvals)
    # The final task should be AWAITING_APPROVAL.
    assert any(t.status == "AWAITING_APPROVAL" for t in tasks)


async def test_pipeline_task_chain_has_parents(test_session):
    await bootstrap.bootstrap_company(
        test_session, company_id="co_chain", name="Chain", slug="chain", goal="x"
    )
    ctx = CompanyContext("co_chain")
    tasks = await repo.list_tasks(test_session, ctx)
    # Every stage after the first has a parent_task_id (explicit DAG edge).
    with_parent = [t for t in tasks if t.parent_task_id is not None]
    assert len(with_parent) >= 5  # 5 edges between 6 stages


async def test_rooms_and_desks_created(test_session):
    await bootstrap.bootstrap_company(
        test_session, company_id="co_rooms", name="Rooms", slug="rooms", goal="x"
    )
    ctx = CompanyContext("co_rooms")
    rooms = await repo.list_rooms(test_session, ctx)
    labels = {r.label for r in rooms}
    assert "CEO Suite" in labels
    assert "HR Suite" in labels
    # Each team room has 6 desks (1 lead + 5 workers).
    rnd_room = next(r for r in rooms if r.label == "R&D Suite")
    desks = await repo.list_desks(test_session, ctx, rnd_room.id)
    assert len(desks) == 6
