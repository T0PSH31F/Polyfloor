"""Tests for the company-as-tenant isolation boundary (SPEC §4)."""

from __future__ import annotations

import pytest

from polyfloor.db.models import CompanyContext, Task
from polyfloor.services import bootstrap, repository as repo


@pytest.fixture
def ctx_a() -> CompanyContext:
    return CompanyContext("co_alpha")


@pytest.fixture
def ctx_b() -> CompanyContext:
    return CompanyContext("co_beta")


async def test_missing_company_context_raises():
    with pytest.raises(ValueError):
        CompanyContext("")


async def test_company_a_cannot_read_company_b_tasks(test_session, ctx_a, ctx_b):
    await bootstrap.bootstrap_company(
        test_session,
        company_id="co_alpha",
        name="Alpha",
        slug="alpha",
        goal="ship widgets",
    )
    await bootstrap.bootstrap_company(
        test_session,
        company_id="co_beta",
        name="Beta",
        slug="beta",
        goal="ship gadgets",
    )
    # Alpha tasks must not appear in Beta's list.
    a_tasks = await repo.list_tasks(test_session, ctx_a)
    b_tasks = await repo.list_tasks(test_session, ctx_b)
    assert all(t.company_id == "co_alpha" for t in a_tasks)
    assert all(t.company_id == "co_beta" for t in b_tasks)
    assert {t.company_id for t in a_tasks} == {"co_alpha"}
    assert {t.company_id for t in b_tasks} == {"co_beta"}


async def test_cross_company_agent_lookup_returns_none(test_session, ctx_a, ctx_b):
    await bootstrap.bootstrap_company(
        test_session, company_id="co_alpha", name="Alpha", slug="alpha", goal="x"
    )
    # Beta's context must NOT resolve Alpha's CEO agent.
    agent = await repo.get_agent(test_session, ctx_b, "co_alpha_ceo")
    assert agent is None


async def test_cross_company_task_get_returns_none(test_session, ctx_a, ctx_b):
    await bootstrap.bootstrap_company(
        test_session, company_id="co_alpha", name="Alpha", slug="alpha", goal="x"
    )
    a_tasks = await repo.list_tasks(test_session, ctx_a)
    first_id = a_tasks[0].id
    assert first_id is not None
    # Beta must not read Alpha's task.
    leaked = await repo.get_task(test_session, ctx_b, first_id)
    assert leaked is None


async def test_cross_company_model_update_rejected(test_session, ctx_a, ctx_b):
    await bootstrap.bootstrap_company(
        test_session, company_id="co_alpha", name="Alpha", slug="alpha", goal="x"
    )
    with pytest.raises(LookupError):
        await repo.update_agent_model(
            test_session, ctx_b, "co_alpha_ceo", "some-model"
        )
