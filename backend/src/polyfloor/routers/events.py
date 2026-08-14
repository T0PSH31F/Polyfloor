"""Event stream endpoint using Server-Sent Events."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sse_starlette.sse import EventSourceResponse

from ..auth import Principal, require_floor_access, require_scope
from ..db import get_pool

router = APIRouter(tags=["events"])


class EventBus:
    """Simple in-process pub/sub for SSE event streaming."""

    def __init__(self):
        self._subscribers: dict[str, list[asyncio.Queue]] = {}

    def subscribe(self, floor_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._subscribers.setdefault(floor_id, []).append(q)
        return q

    def unsubscribe(self, floor_id: str, q: asyncio.Queue):
        subs = self._subscribers.get(floor_id, [])
        if q in subs:
            subs.remove(q)

    async def publish(self, floor_id: str, event: dict[str, Any]):
        for q in self._subscribers.get(floor_id, []):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass  # Drop oldest would require different impl

    async def publish_global(self, event: dict[str, Any]):
        for floor_id in list(self._subscribers.keys()):
            await self.publish(floor_id, event)


# Module-level event bus instance
event_bus = EventBus()


@router.get("/events/stream")
async def stream_events(
    floor_id: Optional[str] = Query(None, description="Filter events by floor ID"),
    principal: Principal = Depends(require_scope("events:read")),
):
    """SSE endpoint for real-time event streaming."""
    if floor_id:
        require_floor_access(floor_id, principal)

    async def event_generator():
        q = event_bus.subscribe(floor_id or "__global__")
        try:
            while True:
                try:
                    event = await asyncio.wait_for(q.get(), timeout=30)
                    yield {
                        "event": event.get("event_type", "message"),
                        "data": json.dumps(event),
                        "id": str(event.get("id", "")),
                    }
                except asyncio.TimeoutError:
                    yield {"event": "heartbeat", "data": "{}"}
                except asyncio.CancelledError:
                    break
        finally:
            event_bus.unsubscribe(floor_id or "__global__", q)

    return EventSourceResponse(event_generator())
