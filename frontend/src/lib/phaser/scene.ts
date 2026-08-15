/**
 * Phaser scene — programmatic placeholder graphics for the floor tower.
 *
 * Uses simple rectangles and text. No external sprite assets required.
 * Client-only: must be dynamically imported to avoid SSR errors.
 */

import Phaser from "phaser";
import { bridge, type SvelteToPhaserEvent } from "./bridge";
import type { AgentState } from "$lib/types";

const FLOOR_COLORS: Record<AgentState, number> = {
  idle: 0x4a5568,
  working: 0x48bb78,
  alert: 0xed8936,
  done: 0x4299e1,
};

interface FloorRect {
  id: string;
  rect: Phaser.GameObjects.Rectangle;
  label: Phaser.GameObjects.Text;
  stateIndicator: Phaser.GameObjects.Rectangle;
  state: AgentState;
}

export class TowerScene extends Phaser.Scene {
  private floors: Map<string, FloorRect> = new Map();
  private selectedFloor: string | null = null;
  private unsubscribe: (() => void) | null = null;

  constructor() {
    super({ key: "TowerScene" });
  }

  create(): void {
    const floorIds = ["production", "marketing", "research", "dev", "customer-service"];
    const floorHeight = 80;
    const floorWidth = 300;
    const gap = 10;
    const startY = this.scale.height - 60;

    for (let i = 0; i < floorIds.length; i++) {
      const id = floorIds[i];
      const y = startY - i * (floorHeight + gap);

      // Floor rectangle
      const rect = this.add.rectangle(
        this.scale.width / 2,
        y,
        floorWidth,
        floorHeight,
        FLOOR_COLORS.idle,
      );
      rect.setStrokeStyle(2, 0xffffff);
      rect.setInteractive({ useHandCursor: true });

      // Floor label
      const label = this.add.text(
        this.scale.width / 2,
        y,
        id.toUpperCase(),
        {
          fontSize: "14px",
          fontFamily: "monospace",
          color: "#ffffff",
          align: "center",
        },
      );
      label.setOrigin(0.5);

      // State indicator (small dot)
      const stateIndicator = this.add.rectangle(
        this.scale.width / 2 + floorWidth / 2 - 12,
        y - floorHeight / 2 + 12,
        8,
        8,
        FLOOR_COLORS.idle,
      );

      this.floors.set(id, { id, rect, label, stateIndicator, state: "idle" });

      // Click handler
      rect.on("pointerdown", () => {
        bridge.sendToSvelte({ type: "floor-click", floorId: id });
      });

      rect.on("pointerover", () => {
        bridge.sendToSvelte({ type: "floor-hover", floorId: id });
        if (this.selectedFloor !== id) {
          rect.setFillStyle(0x718096);
        }
      });

      rect.on("pointerout", () => {
        bridge.sendToSvelte({ type: "floor-hover", floorId: null });
        const floor = this.floors.get(id);
        if (floor && this.selectedFloor !== id) {
          rect.setFillStyle(FLOOR_COLORS[floor.state]);
        }
      });
    }

    // Listen for Svelte → Phaser events
    this.unsubscribe = bridge.onSvelteEvent((event) => this.handleSvelteEvent(event));
  }

  private handleSvelteEvent(event: SvelteToPhaserEvent): void {
    switch (event.type) {
      case "navigate-floor":
      case "highlight-floor":
        this.selectFloor(event.floorId);
        break;
      case "agent-state-change":
        this.updateAgentState(event.floorId, event.role, event.state);
        break;
    }
  }

  private selectFloor(floorId: string | null): void {
    // Deselect previous
    if (this.selectedFloor) {
      const prev = this.floors.get(this.selectedFloor);
      if (prev) {
        prev.rect.setFillStyle(FLOOR_COLORS[prev.state]);
        prev.rect.setStrokeStyle(2, 0xffffff);
      }
    }

    this.selectedFloor = floorId;

    // Select new
    if (floorId) {
      const floor = this.floors.get(floorId);
      if (floor) {
        floor.rect.setFillStyle(0x63b3ed);
        floor.rect.setStrokeStyle(3, 0xfbd38d);
      }
    }
  }

  private updateAgentState(floorId: string, _role: string, state: AgentState): void {
    const floor = this.floors.get(floorId);
    if (!floor) return;

    floor.state = state;
    floor.stateIndicator.setFillStyle(FLOOR_COLORS[state]);

    if (this.selectedFloor !== floorId) {
      floor.rect.setFillStyle(FLOOR_COLORS[state]);
    }
  }

  shutdown(): void {
    if (this.unsubscribe) {
      this.unsubscribe();
      this.unsubscribe = null;
    }
  }
}

/**
 * Create a Phaser game instance. Must be called client-side only.
 */
export function createPhaserGame(parent: HTMLElement): Phaser.Game {
  return new Phaser.Game({
    type: Phaser.AUTO,
    parent,
    width: 400,
    height: 500,
    backgroundColor: "#1a202c",
    scene: [TowerScene],
    physics: { default: "arcade" },
    render: {
      pixelArt: false,
      antialias: true,
    },
  });
}
