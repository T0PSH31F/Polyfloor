"""In-process event bus keyed by ``company_id``.

Events are persisted (append-only) and fanned out to SSE subscribers filtered by
company. A subscriber for company A never receives company B's events.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
from typing import Any

import structlog

from ..db import get_engine
from ..db.models import CompanyContext, Event

logger = structlog.get_logger()


class EventBus:
    """Company-scoped async pub/sub with durable persistence."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue[dict[str, Any]]]] = {}
        self._lock = asyncio.Lock()

    def subscribe(self, company_id: str) -> asyncio.Queue[dict[str, Any]]:
        q: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=256)
        self._subscribers.setdefault(company_id, []).append(q)
        return q

    def unsubscribe(self, company_id: str, q: asyncio.Queue[dict[str, Any]]) -> None:
        subs = self._subscribers.get(company_id, [])
        if q in subs:
            subs.remove(q)

    async def publish(
        self,
        ctx: CompanyContext,
        event_type: str,
        payload: dict[str, Any],
        *,
        source_agent_id: str | None = None,
        target_type: str = "system",
        target_id: str | None = None,
        correlation_id: str | None = None,
        requires_approval: bool = False,
    ) -> dict[str, Any]:
        """Persist an event and fan it out to the company's subscribers."""
        from sqlalchemy.ext.asyncio import AsyncSession

        event = Event(
            company_id=ctx.company_id,
            source_agent_id=source_agent_id,
            target_type=target_type,
            target_id=target_id,
            event_type=event_type,
            correlation_id=correlation_id or ctx.trace_id,
            payload_json=json.dumps(payload, default=str),
            trace_id=ctx.trace_id,
            requires_approval=requires_approval,
        )
        engine = get_engine()
        try:
            async with AsyncSession(engine) as session:
                session.add(event)
                await session.commit()
                await session.refresh(event)
        except Exception as exc:  # pragma: no cover
            logger.error("event_bus.persist_failed", error=str(exc), company_id=ctx.company_id)

        envelope = {
            "id": event.id,
            "company_id": ctx.company_id,
            "event_type": event_type,
            "source_agent_id": source_agent_id,
            "target_type": target_type,
            "target_id": target_id,
            "correlation_id": event.correlation_id,
            "payload": payload,
            "trace_id": ctx.trace_id,
            "requires_approval": requires_approval,
            "created_at": event.created_at.isoformat() if event.created_at else None,
        }
        for q in self._subscribers.get(ctx.company_id, []):
            with contextlib.suppress(asyncio.QueueFull):
                q.put_nowait(envelope)
        return envelope


# Module-level singleton.
event_bus = EventBus()
