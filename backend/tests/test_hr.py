"""Tests for the HR hire flow (SPEC §5): leads request, only HR creates workers."""

from __future__ import annotations

import pytest

from polyfloor.db.models import CompanyContext
from polyfloor.services import bootstrap, repository as repo
from polyfloor.services import hr


async def test_lead_request_creates_pending_approval(test_session):
    await bootstrap.bootstrap_company(
        test_session, company_id="co_hr", name="HrCo", slug="hrco", goal="x"
    )
    ctx = CompanyContext("co_hr", actor="co_hr_rnd_lead")
    approval = await hr.request_hire(
        test_session,
        ctx,
        team_id="co_hr_team_rnd",
        role="worker",
        requested_by="co_hr_rnd_lead",
        reason="need a drafter",
    )
    assert approval.status == "PENDING"
    assert approval.policy_key == "hire"


async def test_execute_hire_requires_approved_approval(test_session):
    await bootstrap.bootstrap_company(
        test_session, company_id="co_hr2", name="HrCo2", slug="hrco2", goal="x"
    )
    ctx = CompanyContext("co_hr2", actor="co_hr2_rnd_lead")
    approval = await hr.request_hire(
        test_session,
        ctx,
        team_id="co_hr2_team_rnd",
        role="worker",
        requested_by="co_hr2_rnd_lead",
    )
    # Before approval, hiring must be refused.
    with pytest.raises(PermissionError):
        await hr.execute_hire(
            test_session,
            ctx,
            approval_id=approval.id,
            agent_id="co_hr2_worker_1",
            name="Drafter",
            role="worker",
            team_id="co_hr2_team_rnd",
            room_id="co_hr2_team_rnd",
        )

    # Approve, then HR may hire.
    await repo.resolve_approval(test_session, ctx, approval.id, "APPROVED", "user")
    agent = await hr.execute_hire(
        test_session,
        ctx,
        approval_id=approval.id,
        agent_id="co_hr2_worker_1",
        name="Drafter",
        role="worker",
        team_id="co_hr2_team_rnd",
        room_id="co_hr2_team_rnd",
    )
    assert agent.id == "co_hr2_worker_1"
    assert agent.home_room_id == "co_hr2_team_rnd"


async def test_retire_agent_preserves_audit_trail(test_session):
    await bootstrap.bootstrap_company(
        test_session, company_id="co_ret", name="RetCo", slug="retco", goal="x"
    )
    ctx = CompanyContext("co_ret")
    retired = await hr.retire_agent(test_session, ctx, "co_ret_ceo")
    assert retired is not None
    assert retired.state == "retired"
    assert retired.retired_at is not None
    # Still auditable (not deleted).
    again = await repo.get_agent(test_session, ctx, "co_ret_ceo")
    assert again is not None
