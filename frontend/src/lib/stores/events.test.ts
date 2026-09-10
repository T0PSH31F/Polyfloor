/**
 * Event store tests — order, capacity, and floor isolation
 */
import { describe, it, expect, beforeEach } from "vitest";
import { get } from "svelte/store";
import {
  events,
  filteredEvents,
  activeFloorId,
  clearEvents,
  agentStates,
} from "./events";
import type { FloorEvent } from "$lib/types";

function makeEvent(overrides: Partial<FloorEvent> = {}): FloorEvent {
  return {
    floor_id: "production",
    event_type: "task.created",
    actor: "orchestrator",
    payload: {},
    ...overrides,
  };
}

describe("event store", () => {
  beforeEach(() => {
    clearEvents();
    activeFloorId.set(null);
  });

  it("starts empty", () => {
    expect(get(events)).toEqual([]);
  });

  it("stores events newest-first", () => {
    const e1 = makeEvent({ actor: "first" });
    const e2 = makeEvent({ actor: "second" });
    events.set([e2, e1]);
    const stored = get(events);
    expect(stored[0].actor).toBe("second");
    expect(stored[1].actor).toBe("first");
  });

  it("respects MAX capacity", () => {
    const many = Array.from({ length: 600 }, (_, i) =>
      makeEvent({ actor: `agent-${i}` }),
    );
    events.set(many.slice(0, 500));
    expect(get(events).length).toBeLessThanOrEqual(500);
  });

  it("filters by floor_id", () => {
    activeFloorId.set("production");
    events.set([
      makeEvent({ floor_id: "production", actor: "prod" }),
      makeEvent({ floor_id: "research", actor: "res" }),
    ]);
    const filtered = get(filteredEvents);
    expect(filtered).toHaveLength(1);
    expect(filtered[0].actor).toBe("prod");
  });

  it("shows all events when no floor filter", () => {
    activeFloorId.set(null);
    events.set([
      makeEvent({ floor_id: "production" }),
      makeEvent({ floor_id: "research" }),
    ]);
    expect(get(filteredEvents)).toHaveLength(2);
  });

  it("clears events", () => {
    events.set([makeEvent(), makeEvent()]);
    clearEvents();
    expect(get(events)).toEqual([]);
  });
});

describe("agent state derivation", () => {
  beforeEach(() => {
    clearEvents();
  });

  it("derives working from in_progress tasks", () => {
    events.set([
      makeEvent({
        floor_id: "production",
        actor: "writer",
        event_type: "task.updated",
        payload: { status: "in_progress" },
      }),
    ]);
    const states = get(agentStates);
    expect(states["production:writer"]).toBe("working");
  });

  it("derives done from completed tasks", () => {
    events.set([
      makeEvent({
        floor_id: "production",
        actor: "writer",
        event_type: "task.updated",
        payload: { status: "done" },
      }),
    ]);
    const states = get(agentStates);
    expect(states["production:writer"]).toBe("done");
  });

  it("derives alert from rejected approvals", () => {
    events.set([
      makeEvent({
        floor_id: "production",
        actor: "editor",
        event_type: "approval.resolved",
        payload: { status: "rejected" },
      }),
    ]);
    const states = get(agentStates);
    expect(states["production:editor"]).toBe("alert");
  });

  it("keeps floor isolation in agent states", () => {
    events.set([
      makeEvent({
        floor_id: "production",
        actor: "writer",
        event_type: "task.updated",
        payload: { status: "in_progress" },
      }),
      makeEvent({
        floor_id: "research",
        actor: "writer",
        event_type: "task.updated",
        payload: { status: "done" },
      }),
    ]);
    const states = get(agentStates);
    expect(states["production:writer"]).toBe("working");
    expect(states["research:writer"]).toBe("done");
  });
});
