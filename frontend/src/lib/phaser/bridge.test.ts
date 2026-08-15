/**
 * Phaser bridge tests — lightweight emitter abstraction
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { Bridge } from "./bridge";
import type { FloorEvent, AgentState } from "$lib/types";

describe("Bridge", () => {
  let bridge: Bridge;

  beforeEach(() => {
    bridge = new Bridge();
  });

  it("delivers svelte-to-phaser events", () => {
    const handler = vi.fn();
    bridge.onSvelteEvent(handler);

    bridge.sendToPhaser({
      type: "navigate-floor",
      floorId: "production",
    });

    expect(handler).toHaveBeenCalledWith({
      type: "navigate-floor",
      floorId: "production",
    });
  });

  it("delivers phaser-to-svelte events", () => {
    const handler = vi.fn();
    bridge.onPhaserEvent(handler);

    bridge.sendToSvelte({
      type: "floor-click",
      floorId: "research",
    });

    expect(handler).toHaveBeenCalledWith({
      type: "floor-click",
      floorId: "research",
    });
  });

  it("unsubscribes correctly", () => {
    const handler = vi.fn();
    const unsub = bridge.onSvelteEvent(handler);

    unsub();
    bridge.sendToPhaser({ type: "navigate-floor", floorId: "dev" });

    expect(handler).not.toHaveBeenCalled();
  });

  it("maps task.created to agent state", () => {
    const event: FloorEvent = {
      floor_id: "production",
      event_type: "task.created",
      actor: "writer",
      payload: {},
    };

    const result = bridge.mapEventToAgentState(event);
    expect(result?.type).toBe("agent-state-change");
    if (result?.type === "agent-state-change") {
      expect(result.state).toBe("idle");
    }
  });

  it("maps in_progress to working state", () => {
    const event: FloorEvent = {
      floor_id: "production",
      event_type: "task.updated",
      actor: "writer",
      payload: { status: "in_progress" },
    };

    const result = bridge.mapEventToAgentState(event);
    expect(result?.type).toBe("agent-state-change");
    if (result?.type === "agent-state-change") {
      expect(result.state).toBe("working");
    }
  });

  it("maps done status to done state", () => {
    const event: FloorEvent = {
      floor_id: "production",
      event_type: "task.updated",
      actor: "writer",
      payload: { status: "done" },
    };

    const result = bridge.mapEventToAgentState(event);
    expect(result?.type).toBe("agent-state-change");
    if (result?.type === "agent-state-change") {
      expect(result.state).toBe("done");
    }
  });

  it("maps rejected approval to alert", () => {
    const event: FloorEvent = {
      floor_id: "production",
      event_type: "approval.resolved",
      actor: "editor",
      payload: { status: "rejected" },
    };

    const result = bridge.mapEventToAgentState(event);
    expect(result?.type).toBe("agent-state-change");
    if (result?.type === "agent-state-change") {
      expect(result.state).toBe("alert");
    }
  });

  it("maps approved approval to done", () => {
    const event: FloorEvent = {
      floor_id: "production",
      event_type: "approval.resolved",
      actor: "editor",
      payload: { status: "approved" },
    };

    const result = bridge.mapEventToAgentState(event);
    expect(result?.type).toBe("agent-state-change");
    if (result?.type === "agent-state-change") {
      expect(result.state).toBe("done");
    }
  });

  it("returns null for unmapped event types", () => {
    const event: FloorEvent = {
      floor_id: "production",
      event_type: "config.updated",
      actor: "admin",
      payload: {},
    };

    const result = bridge.mapEventToAgentState(event);
    expect(result).toBeNull();
  });

  it("disposes all handlers", () => {
    const handler1 = vi.fn();
    const handler2 = vi.fn();
    bridge.onSvelteEvent(handler1);
    bridge.onPhaserEvent(handler2);

    bridge.dispose();

    bridge.sendToPhaser({ type: "navigate-floor", floorId: "test" });
    bridge.sendToSvelte({ type: "floor-click", floorId: "test" });

    expect(handler1).not.toHaveBeenCalled();
    expect(handler2).not.toHaveBeenCalled();
  });
});
