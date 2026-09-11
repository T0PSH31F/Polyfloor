"""Tests for the company-scoped event bus (SPEC §4, §6.1)."""

from __future__ import annotations

import asyncio

import pytest

from polyfloor.db.models import CompanyContext
from polyfloor.services.event_bus import EventBus


@pytest.mark.asyncio
async def test_subscriber_only_receives_own_company_events():
    bus = EventBus()
    ctx_a = CompanyContext("co_ev_a")
    ctx_b = CompanyContext("co_ev_b")

    q_a = bus.subscribe("co_ev_a")

    # Publish a company B event — A must not see it.
    await bus.publish(ctx_b, "task.done", {"task_id": 1})
    # Publish a company A event — A must see it.
    await bus.publish(ctx_a, "task.done", {"task_id": 2})

    received: list = []
    try:
        for _ in range(5):
            evt = await asyncio.wait_for(q_a.get(), timeout=0.1)
            received.append(evt)
    except TimeoutError:
        pass

    assert len(received) == 1
    assert received[0]["company_id"] == "co_ev_a"
    assert received[0]["payload"]["task_id"] == 2
    bus.unsubscribe("co_ev_a", q_a)


@pytest.mark.asyncio
async def test_event_persisted_with_company_id(test_engine, test_session):
    """An event published through the bus is durably persisted with company_id."""
    import polyfloor.services.event_bus as eb_mod

    eb_mod.get_engine = lambda: test_engine  # type: ignore[assignment]
    bus = EventBus()
    ctx = CompanyContext("co_persist")
    await bus.publish(ctx, "company.created", {"name": "PersistCo"})

    from polyfloor.services import repository as repo

    events = await repo.list_events(test_session, ctx)
    assert any(e.event_type == "company.created" and e.company_id == "co_persist" for e in events)
