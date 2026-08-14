"""Event bus — in-process pub/sub for state-change events.

Publishes to the SSE event stream after successful database commits.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Callable, Optional


class EventBus:
    """Simple in-process event bus with async subscribers."""

    def __init__(self):
        self._subscribers: dict[str, list[asyncio.Queue]] = {}
        self._global_subscribers: list[asyncio.Queue] = []
        self._handlers: list[Callable] = []

    def subscribe(self, floor_id: Optional[str] = None) -> asyncio.Queue:
        """Subscribe to events for a specific floor or globally."""
        q: asyncio.Queue = asyncio.Queue(maxsize=200)
        if floor_id:
            self._subscribers.setdefault(floor_id, []).append(q)
        else:
            self._global_subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue, floor_id: Optional[str] = None):
        """Remove a subscriber."""
        if floor_id:
            subs = self._subscribers.get(floor_id, [])
            if q in subs:
                subs.remove(q)
        elif q in self._global_subscribers:
            self._global_subscribers.remove(q)

    async def publish(self, floor_id: str, event_type: str, payload: dict[str, Any], actor: str = "system"):
        """Publish an event to floor-specific and global subscribers."""
        event = {
            "floor_id": floor_id,
            "event_type": event_type,
            "payload": payload,
            "actor": actor,
        }

        # Floor-specific subscribers
        for q in self._subscribers.get(floor_id, []):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                # Drop oldest
                try:
                    q.get_nowait()
                    q.put_nowait(event)
                except (asyncio.QueueEmpty, asyncio.QueueFull):
                    pass

        # Global subscribers
        for q in self._global_subscribers:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                try:
                    q.get_nowait()
                    q.put_nowait(event)
                except (asyncio.QueueEmpty, asyncio.QueueFull):
                    pass

        # Registered handlers
        import inspect

        for handler in self._handlers:
            try:
                if inspect.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception:
                pass  # Don't let handler errors propagate

    def add_handler(self, handler: Callable):
        """Register an event handler."""
        self._handlers.append(handler)

    def remove_handler(self, handler: Callable):
        """Unregister an event handler."""
        if handler in self._handlers:
            self._handlers.remove(handler)


# Module-level singleton
event_bus = EventBus()
