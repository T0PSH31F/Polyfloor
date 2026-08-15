/**
 * Phaser ↔ Svelte event bridge.
 *
 * Allows Svelte navigation to tell Phaser about floor/elevator changes,
 * and Phaser floor clicks to request Svelte navigation.
 * Keeps Phaser implementation isolated and testable without WebGL.
 */

import type { AgentState, FloorEvent } from "$lib/types";

/** Events emitted from Svelte → Phaser */
export type SvelteToPhaserEvent =
  | { type: "navigate-floor"; floorId: string }
  | { type: "highlight-floor"; floorId: string | null }
  | { type: "agent-state-change"; floorId: string; role: string; state: AgentState };

/** Events emitted from Phaser → Svelte */
export type PhaserToSvelteEvent =
  | { type: "floor-click"; floorId: string }
  | { type: "floor-hover"; floorId: string | null };

type Handler<T> = (event: T) => void;

/**
 * Lightweight event emitter for Phaser ↔ Svelte communication.
 * This abstraction allows testing without a real Phaser/WebGL context.
 */
export class Bridge {
  private svelteHandlers: Handler<SvelteToPhaserEvent>[] = [];
  private phaserHandlers: Handler<PhaserToSvelteEvent>[] = [];

  /** Register a handler for Svelte → Phaser events */
  onSvelteEvent(handler: Handler<SvelteToPhaserEvent>): () => void {
    this.svelteHandlers.push(handler);
    return () => {
      this.svelteHandlers = this.svelteHandlers.filter((h) => h !== handler);
    };
  }

  /** Register a handler for Phaser → Svelte events */
  onPhaserEvent(handler: Handler<PhaserToSvelteEvent>): () => void {
    this.phaserHandlers.push(handler);
    return () => {
      this.phaserHandlers = this.phaserHandlers.filter((h) => h !== handler);
    };
  }

  /** Send an event from Svelte to Phaser */
  sendToPhaser(event: SvelteToPhaserEvent): void {
    for (const handler of this.svelteHandlers) {
      handler(event);
    }
  }

  /** Send an event from Phaser to Svelte */
  sendToSvelte(event: PhaserToSvelteEvent): void {
    for (const handler of this.phaserHandlers) {
      handler(event);
    }
  }

  /** Map a backend FloorEvent to an agent state change */
  mapEventToAgentState(event: FloorEvent): SvelteToPhaserEvent | null {
    let state: AgentState;

    switch (event.event_type) {
      case "task.created":
      case "task.updated":
        if (event.payload?.status === "in_progress") state = "working";
        else if (event.payload?.status === "done") state = "done";
        else state = "idle";
        break;
      case "approval.resolved":
        state = event.payload?.status === "approved" ? "done" : "alert";
        break;
      default:
        return null;
    }

    return {
      type: "agent-state-change",
      floorId: event.floor_id,
      role: event.actor,
      state,
    };
  }

  /** Remove all handlers (cleanup) */
  dispose(): void {
    this.svelteHandlers = [];
    this.phaserHandlers = [];
  }
}

/** Singleton bridge instance */
export const bridge = new Bridge();
