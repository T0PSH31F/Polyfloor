/**
 * SSE store — subscribes to /api/events?company_id=... and dispatches deltas.
 *
 * Per SPEC invariant: live data via SSE deltas only. Fetch state once on
 * company/room entry, then apply SSE deltas. Do NOT poll the state endpoint.
 */

import { writable, type Writable } from "svelte/store";
import type { SSEEvent } from "../types";

export type { SSEEvent };

export const sseEvents: Writable<SSEEvent[]> = writable([]);
export const sseConnected: Writable<boolean> = writable(false);
export const latestEvent: Writable<SSEEvent | null> = writable(null);

let eventSource: EventSource | null = null;
let currentCompanyId: string | null = null;
const MAX_EVENTS = 200;

export function subscribeSSE(companyId: string): void {
  if (currentCompanyId === companyId && eventSource) return;
  disconnectSSE();
  currentCompanyId = companyId;

  const url = `/api/events?company_id=${encodeURIComponent(companyId)}`;
  eventSource = new EventSource(url);

  eventSource.onopen = () => {
    sseConnected.set(true);
  };

  eventSource.onerror = () => {
    sseConnected.set(false);
    // The browser will auto-reconnect EventSource. If it fails permanently,
    // we keep the store as-is so the UI shows the last known state.
  };

  // Listen for named events and generic messages.
  // The SSE stream uses `event: <type>` / `data: <json>` / `id: <event_id>`.
  // EventSource dispatches a named event for each `event:` type.
  // We also handle the default "message" event for unnamed data.
  const handler = (ev: MessageEvent) => {
    let data: Record<string, unknown>;
    try {
      data = JSON.parse(ev.data);
    } catch {
      data = { raw: ev.data };
    }
    const sseEvent: SSEEvent = {
      id: ev.lastEventId || String(Date.now()),
      event: (ev.type === "message" ? "message" : ev.type) || "message",
      data,
    };
    latestEvent.set(sseEvent);
    sseEvents.update((events) => {
      const next = [...events, sseEvent];
      return next.slice(-MAX_EVENTS);
    });
  };

  // EventSource fires named events for each `event:` line, and "message" for
  // events without an `event:` field. We listen to both.
  eventSource.addEventListener("message", handler);
  // Also listen to common event types from the backend.
  const knownTypes = [
    "heartbeat",
    "company.created",
    "hr.hired",
    "pipeline.seeded",
    "task.advanced",
    "task.created",
    "approval.requested",
    "approval.resolved",
    "agent.paused",
    "agent.resumed",
    "agent.state_changed",
    "artifact.created",
    "agent.run_started",
    "agent.run_finished",
  ];
  for (const t of knownTypes) {
    eventSource.addEventListener(t, handler);
  }
}

export function disconnectSSE(): void {
  if (eventSource) {
    eventSource.close();
    eventSource = null;
  }
  currentCompanyId = null;
  sseConnected.set(false);
}

export function clearEvents(): void {
  sseEvents.set([]);
  latestEvent.set(null);
}
