"""Server-Sent Events stream — company-scoped deltas only.

A subscriber for company A never receives company B's events. The frontend
reconnects on disconnect. See SPEC §8.5.
"""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Depends, Query
from sse_starlette.sse import EventSourceResponse

from ..auth import company_context
from ..db.models import CompanyContext
from ..observability import SSE_CLIENTS
from ..services.event_bus import event_bus

router = APIRouter(tags=["events"])


@router.get("/events")
async def stream_events(
    company_id: str = Depends(company_context),
    _last_id: str | None = Query(default=None, alias="last_event_id"),
):
    """SSE endpoint streaming company-scoped state deltas."""
    ctx: CompanyContext = company_id  # type: ignore[assignment]
    SSE_CLIENTS.labels(company_id=ctx.company_id).inc()
    queue = event_bus.subscribe(ctx.company_id)

    async def event_generator():
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=25.0)
                    yield {
                        "event": event.get("event_type", "message"),
                        "data": json.dumps(event, default=str),
                        "id": str(event.get("id", "")),
                    }
                except TimeoutError:
                    yield {"event": "heartbeat", "data": "{}"}
        except asyncio.CancelledError:
            pass
        finally:
            event_bus.unsubscribe(ctx.company_id, queue)
            SSE_CLIENTS.labels(company_id=ctx.company_id).dec()

    return EventSourceResponse(event_generator())
