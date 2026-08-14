"""Event bus publish/subscribe tests."""

from __future__ import annotations

import asyncio

import pytest

from polyfloor.services.event_bus import EventBus


@pytest.mark.asyncio
async def test_floor_specific_publish():
    bus = EventBus()
    q = bus.subscribe("floor-a")

    await bus.publish("floor-a", "task.created", {"id": 1}, actor="test")

    event = await asyncio.wait_for(q.get(), timeout=1)
    assert event["floor_id"] == "floor-a"
    assert event["event_type"] == "task.created"
    assert event["payload"] == {"id": 1}

    bus.unsubscribe(q, "floor-a")


@pytest.mark.asyncio
async def test_global_subscriber():
    bus = EventBus()
    q = bus.subscribe()  # global

    await bus.publish("any-floor", "test.event", {})

    event = await asyncio.wait_for(q.get(), timeout=1)
    assert event["floor_id"] == "any-floor"

    bus.unsubscribe(q)


@pytest.mark.asyncio
async def test_floor_isolation():
    bus = EventBus()
    q_a = bus.subscribe("floor-a")
    q_b = bus.subscribe("floor-b")

    await bus.publish("floor-a", "a.event", {})

    event = await asyncio.wait_for(q_a.get(), timeout=1)
    assert event["event_type"] == "a.event"

    # floor-b should not receive it
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(q_b.get(), timeout=0.1)

    bus.unsubscribe(q_a, "floor-a")
    bus.unsubscribe(q_b, "floor-b")


@pytest.mark.asyncio
async def test_handler_called():
    bus = EventBus()
    received = []

    def handler(event):
        received.append(event)

    bus.add_handler(handler)
    await bus.publish("test", "handler.test", {"data": True})

    assert len(received) == 1
    assert received[0]["event_type"] == "handler.test"

    bus.remove_handler(handler)
