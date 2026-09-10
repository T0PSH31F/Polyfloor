/**
 * Event store — manages SSE subscriptions and event history.
 */

import { writable, derived, get } from "svelte/store";
import type { FloorEvent, AgentState } from "$lib/types";

const MAX_EVENTS = 500;

/** All events, newest first */
export const events = writable<FloorEvent[]>([]);

/** Current SSE connection status */
export const connected = writable(false);

/** Active floor filter for events */
export const activeFloorId = writable<string | null>(null);

/** Filtered events for the active floor */
export const filteredEvents = derived(
  [events, activeFloorId],
  ([$events, $activeFloorId]) => {
    if (!$activeFloorId) return $events;
    return $events.filter((e) => e.floor_id === $activeFloorId);
  },
);

/** Agent states derived from events */
export const agentStates = derived(
  events,
  ($events): Record<string, AgentState> => {
    const states: Record<string, AgentState> = {};

    // Walk events newest-first to get latest state per floor
    for (const event of $events) {
      const key = `${event.floor_id}:${event.actor}`;
      if (states[key]) continue;

      switch (event.event_type) {
        case "task.created":
        case "task.updated":
          if (event.payload?.status === "in_progress") {
            states[key] = "working";
          } else if (event.payload?.status === "done") {
            states[key] = "done";
          } else {
            states[key] = "idle";
          }
          break;
        case "approval.resolved":
          states[key] = event.payload?.status === "approved" ? "done" : "alert";
          break;
        case "config.updated":
        case "role.updated":
          states[key] = "alert";
          break;
        default:
          states[key] = "idle";
      }
    }

    return states;
  },
);

let eventSource: EventSource | null = null;

/** Subscribe to SSE events. Cleans up previous connection. */
export function subscribeEvents(floorId?: string) {
  unsubscribeEvents();

  const url = floorId
    ? `/api/v1/events/stream?floor_id=${encodeURIComponent(floorId)}`
    : "/api/v1/events/stream";

  eventSource = new EventSource(url);

  eventSource.onopen = () => connected.set(true);
  eventSource.onerror = () => connected.set(false);

  eventSource.onmessage = (msg) => {
    try {
      const event: FloorEvent = JSON.parse(msg.data);
      events.update((prev) => [event, ...prev].slice(0, MAX_EVENTS));
    } catch {
      // ignore parse errors
    }
  };

  // Named event types
  const types = [
    "task.created",
    "task.updated",
    "config.updated",
    "role.updated",
    "approval.resolved",
  ];
  for (const type of types) {
    eventSource.addEventListener(type, (msg: MessageEvent) => {
      try {
        const event: FloorEvent = JSON.parse(msg.data);
        events.update((prev) => [event, ...prev].slice(0, MAX_EVENTS));
      } catch {
        // ignore
      }
    });
  }
}

/** Disconnect the current SSE subscription. */
export function unsubscribeEvents() {
  if (eventSource) {
    eventSource.close();
    eventSource = null;
    connected.set(false);
  }
}

/** Clear all stored events. */
export function clearEvents() {
  events.set([]);
}
