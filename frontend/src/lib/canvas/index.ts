/**
 * Canvas tilemap + sprite renderer for the GBA-style top screen.
 *
 * Virtual resolution: 320x240 (GBA), 16x16 LimeZu tiles, integer
 * nearest-neighbor scale (3x = 960x720). image-rendering: pixelated.
 * NO WebGL, NO Three.js, NO isometric, NO Phaser.
 */

import type { Room, Agent, Desk } from "../types";

export const TILE = 16;
export const VIEW_W = 320;
export const VIEW_H = 240;
export const COLS = VIEW_W / TILE; // 20
export const ROWS = VIEW_H / TILE; // 15

export interface RoomTileInfo {
  room: Room;
  active: number;
  blocked: number;
  vacant: number;
  x: number;
  y: number;
  w: number;
  h: number;
}

// --- GBA dark palette ---
export const PALETTE = {
  bg: "#0f0f1b",
  floor: "#1a1a2e",
  floorAlt: "#16162a",
  wall: "#2d2d44",
  wallTop: "#3d3d5c",
  accent: "#5c8ddf",
  accentDim: "#3a5a8a",
  text: "#e0e0e0",
  textDim: "#8888aa",
  green: "#4caf50",
  yellow: "#ffc107",
  red: "#f44336",
  blue: "#2196f3",
  purple: "#9c27b0",
  orange: "#ff9800",
};

// --- Asset loading ---
let interiorsImg: HTMLImageElement | null = null;
let roomBuilderImg: HTMLImageElement | null = null;
const characterImgs: Record<string, HTMLImageElement> = {};
const loadingPromises: Record<string, Promise<HTMLImageElement>> = {};

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = src;
  });
}

export async function loadAssets(): Promise<void> {
  const tasks: Promise<unknown>[] = [];

  if (!interiorsImg) {
    const p = loadImage("/assets/interiors.png").then((img) => {
      interiorsImg = img;
    });
    tasks.push(p);
  }

  if (!roomBuilderImg) {
    const p = loadImage("/assets/room_builder.png").then((img) => {
      roomBuilderImg = img;
    });
    tasks.push(p);
  }

  const chars = [
    "ceo",
    "hr",
    "executive",
    "facilities",
    "intern",
    "marketing",
    "researcher",
    "dev",
    "sentry",
  ];
  for (const c of chars) {
    if (!characterImgs[c] && !loadingPromises[c]) {
      loadingPromises[c] = loadImage(`/assets/characters/${c}.png`);
      const p = loadingPromises[c].then((img) => {
        characterImgs[c] = img;
      });
      tasks.push(p);
    }
  }

  await Promise.allSettled(tasks);
}

// Map agent role to character sprite name.
const ROLE_TO_SPRITE: Record<string, string> = {
  ceo: "ceo",
  hr: "hr",
  cfo: "executive",
  cto: "executive",
  coo: "executive",
  cho: "hr",
  lead: "marketing",
  worker: "dev",
  qa: "sentry",
};

function getCharacterSprite(role: string): HTMLImageElement | null {
  const name = ROLE_TO_SPRITE[role] || "dev";
  return characterImgs[name] || null;
}

// --- Drawing primitives ---

export function clearCanvas(
  ctx: CanvasRenderingContext2D,
  scale: number,
): void {
  ctx.imageSmoothingEnabled = false;
  ctx.fillStyle = PALETTE.bg;
  ctx.fillRect(0, 0, VIEW_W * scale, VIEW_H * scale);
}

export function drawTile(
  ctx: CanvasRenderingContext2D,
  sx: number,
  sy: number,
  sw: number,
  sh: number,
  dx: number,
  dy: number,
  scale: number,
  img: HTMLImageElement,
): void {
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(
    img,
    sx,
    sy,
    sw,
    sh,
    dx * scale,
    dy * scale,
    sw * scale,
    sh * scale,
  );
}

/** Draw a simple floor tile grid background. */
export function drawFloorTiles(
  ctx: CanvasRenderingContext2D,
  scale: number,
  startX = 0,
  startY = 0,
  cols = COLS,
  rows = ROWS,
): void {
  ctx.imageSmoothingEnabled = false;
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const x = (startX + c * TILE) * scale;
      const y = (startY + r * TILE) * scale;
      ctx.fillStyle = (r + c) % 2 === 0 ? PALETTE.floor : PALETTE.floorAlt;
      ctx.fillRect(x, y, TILE * scale, TILE * scale);
    }
  }
}

/** Draw a wall border around the screen. */
export function drawWalls(ctx: CanvasRenderingContext2D, scale: number): void {
  ctx.imageSmoothingEnabled = false;
  const wallThick = TILE;
  ctx.fillStyle = PALETTE.wall;
  // Top wall
  ctx.fillRect(0, 0, VIEW_W * scale, wallThick * scale);
  // Bottom wall
  ctx.fillRect(
    0,
    (VIEW_H - wallThick) * scale,
    VIEW_W * scale,
    wallThick * scale,
  );
  // Left wall
  ctx.fillRect(0, 0, wallThick * scale, VIEW_H * scale);
  // Right wall
  ctx.fillRect(
    (VIEW_W - wallThick) * scale,
    0,
    wallThick * scale,
    VIEW_H * scale,
  );
  // Wall top highlight
  ctx.fillStyle = PALETTE.wallTop;
  ctx.fillRect(0, 0, VIEW_W * scale, 2 * scale);
  ctx.fillRect(0, (VIEW_H - wallThick) * scale, VIEW_W * scale, 2 * scale);
}

/** Draw a simple desk (furniture) at tile position. */
export function drawDesk(
  ctx: CanvasRenderingContext2D,
  tileX: number,
  tileY: number,
  scale: number,
): void {
  ctx.imageSmoothingEnabled = false;
  const px = tileX * TILE * scale;
  const py = tileY * TILE * scale;
  const s = TILE * scale;
  // Desk top
  ctx.fillStyle = "#4a3a2a";
  ctx.fillRect(px, py + s * 0.3, s, s * 0.5);
  // Desk shadow
  ctx.fillStyle = "#3a2a1a";
  ctx.fillRect(px, py + s * 0.7, s, s * 0.1);
  // Monitor
  ctx.fillStyle = "#1a1a2e";
  ctx.fillRect(px + s * 0.15, py + s * 0.1, s * 0.4, s * 0.25);
  // Monitor screen glow
  ctx.fillStyle = PALETTE.accentDim;
  ctx.fillRect(px + s * 0.2, py + s * 0.15, s * 0.3, s * 0.15);
}

/** Draw a vacant desk (empty). */
export function drawVacantDesk(
  ctx: CanvasRenderingContext2D,
  tileX: number,
  tileY: number,
  scale: number,
): void {
  ctx.imageSmoothingEnabled = false;
  const px = tileX * TILE * scale;
  const py = tileY * TILE * scale;
  const s = TILE * scale;
  // Faded desk
  ctx.fillStyle = "#2a2a3a";
  ctx.fillRect(px, py + s * 0.3, s, s * 0.5);
  ctx.fillStyle = "#222238";
  ctx.fillRect(px + s * 0.15, py + s * 0.1, s * 0.4, s * 0.25);
}

/** Draw a character sprite at a tile position with optional frame offset for animation. */
export function drawCharacter(
  ctx: CanvasRenderingContext2D,
  tileX: number,
  tileY: number,
  scale: number,
  role: string,
  frame: number,
  working: boolean,
): void {
  const img = getCharacterSprite(role);
  if (!img) {
    // Draw a placeholder colored square
    ctx.imageSmoothingEnabled = false;
    const px = tileX * TILE * scale;
    const py = tileY * TILE * scale;
    const s = TILE * scale;
    ctx.fillStyle = PALETTE.blue;
    ctx.fillRect(px + s * 0.2, py + s * 0.1, s * 0.6, s * 0.8);
    return;
  }

  // Character spritesheets are 768x288 (48 cols x 18 rows of 16px tiles).
  // Sprite height is 32px (2 tiles). We'll use the first row (right-facing idle).
  // Frame offset for 2-frame breath animation: alternate between frame 0 and 1.
  const spriteW = 16;
  const spriteH = 32;
  const frameCol = working ? frame % 4 : frame % 2; // 4-frame walk, 2-frame idle
  const row = 0; // first row (right-facing)

  const sx = frameCol * spriteW;
  const sy = row * spriteH;

  const px = tileX * TILE * scale;
  const py = (tileY * TILE - TILE) * scale; // shift up since sprite is 32px tall

  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(
    img,
    sx,
    sy,
    spriteW,
    spriteH,
    px,
    py,
    spriteW * scale,
    spriteH * scale,
  );
}

/** Draw text in pixel font style. */
export function drawText(
  ctx: CanvasRenderingContext2D,
  text: string,
  x: number,
  y: number,
  scale: number,
  color = PALETTE.text,
  size = 8,
): void {
  ctx.imageSmoothingEnabled = false;
  ctx.font = `${size * scale}px "Press Start 2P", monospace`;
  ctx.fillStyle = color;
  ctx.textBaseline = "top";
  ctx.fillText(text, x * scale, y * scale);
}

/** Draw a KPI badge. */
export function drawBadge(
  ctx: CanvasRenderingContext2D,
  label: string,
  value: string,
  x: number,
  y: number,
  scale: number,
  color = PALETTE.accent,
): void {
  ctx.imageSmoothingEnabled = false;
  const w = label.length * 6 + value.length * 6 + 16;
  const h = 14;
  ctx.fillStyle = PALETTE.wall;
  ctx.fillRect(x * scale, y * scale, w * scale, h * scale);
  ctx.strokeStyle = color;
  ctx.lineWidth = 1;
  ctx.strokeRect(x * scale, y * scale, w * scale, h * scale);
  ctx.font = `${6 * scale}px "Press Start 2P", monospace`;
  ctx.fillStyle = PALETTE.textDim;
  ctx.textBaseline = "top";
  ctx.fillText(label, (x + 4) * scale, (y + 3) * scale);
  ctx.fillStyle = color;
  ctx.fillText(value, (x + 4 + label.length * 6 + 4) * scale, (y + 3) * scale);
}

// --- Lobby layout ---
// Rooms are laid out in a grid on the lobby screen.
// Each room tile is a clickable region.

const ROOM_TYPES_ORDER = [
  "ceo",
  "hr",
  "csuite",
  "qa",
  "team_rnd",
  "team_product",
  "team_qa",
  "team_marketing",
];

export interface LobbyLayout {
  rooms: RoomTileInfo[];
}

/**
 * Compute the lobby layout — room tiles arranged in a grid.
 * Returns positioning info for each room.
 */
export function computeLobbyLayout(
  rooms: Room[],
  agents: Agent[],
  desks: Desk[],
): LobbyLayout {
  // Sort rooms by type order
  const sorted = [...rooms].sort((a, b) => {
    const getSortKey = (r: Room) => {
      const suffix = r.id.split("_").slice(-1)[0];
      const fullSuffix = r.id.split("_").slice(1).join("_");
      const idx = ROOM_TYPES_ORDER.indexOf(fullSuffix || suffix);
      return idx === -1 ? 99 : idx;
    };
    return getSortKey(a) - getSortKey(b);
  });

  // Layout: 4 columns x 2 rows of room tiles, each 4 tiles wide x 3 tiles tall.
  const tileW = 4; // tiles
  const tileH = 3; // tiles
  const startX = 2; // tiles from left wall
  const startY = 3; // tiles from top wall (leave room for header)
  const gapX = 1;
  const gapY = 1;
  const colsPerRow = 4;

  const roomTiles: RoomTileInfo[] = sorted.map((room, i) => {
    const col = i % colsPerRow;
    const row = Math.floor(i / colsPerRow);
    const x = (startX + col * (tileW + gapX)) * TILE;
    const y = (startY + row * (tileH + gapY)) * TILE;

    // Count agents in this room
    const roomAgents = agents.filter((a) => a.home_room_id === room.id);
    const roomDesks = desks.filter((d) => d.room_id === room.id);
    const active = roomAgents.filter(
      (a) => a.state === "working" || a.state === "idle",
    ).length;
    const blocked = roomAgents.filter((a) => a.state === "paused").length;
    const vacant = roomDesks.filter((d) => d.agent_id === null).length;

    return {
      room,
      active,
      blocked,
      vacant,
      x,
      y,
      w: tileW * TILE,
      h: tileH * TILE,
    };
  });

  return { rooms: roomTiles };
}

/** Draw the lobby — header info + room tiles. */
export function drawLobby(
  ctx: CanvasRenderingContext2D,
  scale: number,
  layout: LobbyLayout,
  companyName: string,
  goal: string,
  metrics: { activeAgents: number; pendingApprovals: number },
): void {
  clearCanvas(ctx, scale);
  drawFloorTiles(ctx, scale);
  drawWalls(ctx, scale);

  // Header area
  drawText(
    ctx,
    companyName.toUpperCase().slice(0, 24),
    20,
    20,
    scale,
    PALETTE.accent,
    8,
  );
  if (goal) {
    drawText(ctx, goal.slice(0, 40), 20, 34, scale, PALETTE.textDim, 6);
  }

  // KPI badges
  drawBadge(
    ctx,
    "AGT",
    String(metrics.activeAgents),
    200,
    20,
    scale,
    PALETTE.green,
  );
  drawBadge(
    ctx,
    "APR",
    String(metrics.pendingApprovals),
    260,
    20,
    scale,
    PALETTE.yellow,
  );

  // Room tiles
  for (const rt of layout.rooms) {
    drawRoomTile(ctx, scale, rt);
  }
}

/** Draw a single room tile on the lobby. */
function drawRoomTile(
  ctx: CanvasRenderingContext2D,
  scale: number,
  rt: RoomTileInfo,
): void {
  ctx.imageSmoothingEnabled = false;
  // Tile background
  ctx.fillStyle = PALETTE.wall;
  ctx.fillRect(rt.x * scale, rt.y * scale, rt.w * scale, rt.h * scale);
  // Tile border
  ctx.strokeStyle = PALETTE.accent;
  ctx.lineWidth = 1;
  ctx.strokeRect(rt.x * scale, rt.y * scale, rt.w * scale, rt.h * scale);

  // Room label
  const label = rt.room.label.slice(0, 16);
  drawText(ctx, label, rt.x + 4, rt.y + 4, scale, PALETTE.text, 6);

  // Counts
  drawText(
    ctx,
    `ACT:${rt.active}`,
    rt.x + 4,
    rt.y + 20,
    scale,
    PALETTE.green,
    6,
  );
  drawText(
    ctx,
    `BLK:${rt.blocked}`,
    rt.x + 4,
    rt.y + 30,
    scale,
    PALETTE.red,
    6,
  );
  drawText(
    ctx,
    `VAC:${rt.vacant}`,
    rt.x + 4,
    rt.y + 40,
    scale,
    PALETTE.textDim,
    6,
  );

  // Mini desk icons
  const deskIconY = rt.y + TILE * 2;
  for (let i = 0; i < Math.min(rt.active + rt.vacant, 4); i++) {
    const dx = rt.x + 4 + i * 8;
    ctx.fillStyle = i < rt.active ? PALETTE.green : PALETTE.textDim;
    ctx.fillRect(dx * scale, deskIconY * scale, 6 * scale, 4 * scale);
  }
}

/** Hit-test a click on the lobby layout. Returns the room tile or null. */
export function hitTestLobby(
  layout: LobbyLayout,
  px: number,
  py: number,
  scale: number,
): RoomTileInfo | null {
  for (const rt of layout.rooms) {
    const x0 = rt.x * scale;
    const y0 = rt.y * scale;
    const x1 = x0 + rt.w * scale;
    const y1 = y0 + rt.h * scale;
    if (px >= x0 && px <= x1 && py >= y0 && py <= y1) {
      return rt;
    }
  }
  return null;
}

// --- Team room layout ---
// Lead desk is larger (centered top), 5 worker desks below.

export interface RoomLayout {
  leadDesk: { x: number; y: number; agent: Agent | null };
  workerDesks: { x: number; y: number; agent: Agent | null; vacant: boolean }[];
}

/**
 * Compute the team room layout from desks + agents.
 */
export function computeRoomLayout(desks: Desk[], agents: Agent[]): RoomLayout {
  // Desks are sorted by ordinal. Ordinal 0 = lead, 1-5 = workers.
  const sorted = [...desks].sort((a, b) => a.ordinal - b.ordinal);
  const leadDesk = sorted.find((d) => d.ordinal === 0) || sorted[0];
  const workerDesks = sorted.filter((d) => d.ordinal !== 0).slice(0, 5);

  const leadAgent = leadDesk?.agent_id
    ? agents.find((a) => a.id === leadDesk.agent_id) || null
    : null;

  // Lead desk centered at top
  const leadX = VIEW_W / 2 - TILE; // center-ish
  const leadY = TILE * 3;

  // Worker desks in a row below
  const workerSpacing = TILE * 3;
  const workerStartX = TILE * 2;
  const workerY = TILE * 8;

  return {
    leadDesk: { x: leadX, y: leadY, agent: leadAgent },
    workerDesks: workerDesks.map((d, i) => {
      const agent = d.agent_id
        ? agents.find((a) => a.id === d.agent_id) || null
        : null;
      return {
        x: workerStartX + i * workerSpacing,
        y: workerY,
        agent,
        vacant: !agent,
      };
    }),
  };
}

/** Draw the team room. */
export function drawTeamRoom(
  ctx: CanvasRenderingContext2D,
  scale: number,
  layout: RoomLayout,
  roomLabel: string,
  wip: { in_progress: number; limit: number },
  frame: number,
): void {
  clearCanvas(ctx, scale);
  drawFloorTiles(ctx, scale);
  drawWalls(ctx, scale);

  // Header
  drawText(
    ctx,
    roomLabel.slice(0, 20).toUpperCase(),
    20,
    20,
    scale,
    PALETTE.accent,
    8,
  );
  drawText(
    ctx,
    `WIP:${wip.in_progress}/${wip.limit}`,
    200,
    20,
    scale,
    PALETTE.yellow,
    6,
  );

  // Lead desk (larger)
  if (layout.leadDesk.agent) {
    drawDesk(
      ctx,
      layout.leadDesk.x / TILE,
      layout.leadDesk.y / TILE - 1,
      scale,
    );
    drawCharacter(
      ctx,
      layout.leadDesk.x / TILE,
      layout.leadDesk.y / TILE,
      scale,
      layout.leadDesk.agent.role,
      frame,
      layout.leadDesk.agent.state === "working",
    );
  } else {
    drawVacantDesk(
      ctx,
      layout.leadDesk.x / TILE,
      layout.leadDesk.y / TILE - 1,
      scale,
    );
    drawText(
      ctx,
      "LEAD",
      layout.leadDesk.x / TILE,
      layout.leadDesk.y / TILE,
      scale,
      PALETTE.textDim,
      6,
    );
  }

  // Worker desks
  for (const wd of layout.workerDesks) {
    if (wd.agent) {
      drawDesk(ctx, wd.x / TILE, wd.y / TILE - 1, scale);
      drawCharacter(
        ctx,
        wd.x / TILE,
        wd.y / TILE,
        scale,
        wd.agent.role,
        frame,
        wd.agent.state === "working",
      );
    } else {
      drawVacantDesk(ctx, wd.x / TILE, wd.y / TILE - 1, scale);
      drawText(
        ctx,
        "VACANT",
        wd.x / TILE,
        wd.y / TILE,
        scale,
        PALETTE.textDim,
        6,
      );
    }
  }
}

/** Hit-test a click on a character in the room. Returns agent or null. */
export function hitTestRoom(
  layout: RoomLayout,
  px: number,
  py: number,
  scale: number,
): Agent | null {
  // Lead
  if (layout.leadDesk.agent) {
    const x0 = layout.leadDesk.x * scale;
    const y0 = (layout.leadDesk.y - TILE) * scale;
    const x1 = x0 + TILE * scale;
    const y1 = y0 + TILE * 2 * scale;
    if (px >= x0 && px <= x1 && py >= y0 && py <= y1) {
      return layout.leadDesk.agent;
    }
  }
  // Workers
  for (const wd of layout.workerDesks) {
    if (wd.agent) {
      const x0 = wd.x * scale;
      const y0 = (wd.y - TILE) * scale;
      const x1 = x0 + TILE * scale;
      const y1 = y0 + TILE * 2 * scale;
      if (px >= x0 && px <= x1 && py >= y0 && py <= y1) {
        return wd.agent;
      }
    }
  }
  return null;
}
