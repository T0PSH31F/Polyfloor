# Polyfloor Frontend — Build Notes

## Overview

Built the complete GBA/DS-style retro dual-screen frontend for Polyfloor, an
autonomous multi-company enterprise engine. The frontend is a SvelteKit SPA
using `@sveltejs/adapter-static` with `fallback: 'index.html'` for SPA routing.

## What was built

### Infrastructure
- **Removed `phaser`** dependency (violated invariants) from `package.json`
- **Switched** from `@sveltejs/adapter-auto` to `@sveltejs/adapter-static`
- **Downgraded** `vite` from `^6.0.0` to `^5.0.0` to resolve peer dependency
  conflicts with `@sveltejs/vite-plugin-svelte@4`
- **`vite.config.ts`** already had the `/api` proxy to `http://127.0.0.1:8001`
- **`svelte.config.js`** updated with `adapter-static({ fallback: 'index.html' })`
- **`app.css`** rewritten with GBA dark palette and "Press Start 2P" pixel font

### Core libraries (`src/lib/`)
- **`types.ts`** — Complete TypeScript interfaces matching the frozen API contract:
  `CompanyCard`, `Company`, `Floor`, `Room`, `Desk`, `Team`, `Agent`,
  `AgentRun`, `AgentDossier`, `Task`, `Approval`, `Artifact`, `FloorEvent`,
  `Metrics`, `CompanyState`, `RoomDetail`, `ModelInfo`, `ModelsResponse`,
  `ActionRequest`, `ActionResult`, `SSEEvent`
- **`api.ts`** — Typed fetch wrapper for all endpoints:
  `getCompanies`, `createCompany`, `getCompanyState`, `getRoom`, `getAgent`,
  `avatarUrl`, `getModels`, `updateAgentModel`, `postAction`, `advanceTask`,
  `approveApproval`, `rejectApproval`, `pauseAgent`, `resumeAgent`,
  `stopAgent`, `requestHire`
- **`stores/sse.ts`** — EventSource subscription that dispatches SSE deltas
  to Svelte stores. Subscribes to `/api/events?company_id=...`, handles named
  events + generic messages, caps event history at 200.
- **`canvas/index.ts`** — HTML5 2D Canvas renderer (320x240 virtual, 16x16
  tiles, nearest-neighbor pixelated scaling). Includes:
  - Asset loading (interiors.png, room_builder.png, character spritesheets)
  - Tile grid background, wall borders, desk/vacant desk drawing
  - Character sprite rendering with 2-frame idle / 4-frame walk animation
  - Lobby layout computation (room tiles with active/blocked/vacant counts)
  - Team room layout (lead desk + 5 worker desks)
  - Hit-testing for clickable room tiles and character sprites
  - Pixel text and KPI badge drawing

### Views (routes)
1. **1F Company Directory** (`/`) — Company cards from `GET /api/companies`
   with "Create Company" button
2. **1F Intake Wizard** (`/new`) — 4-step wizard: goal prompt, grilling
   intensity (4 tiers as multiple choice), name + template + budget,
   confirmation. Submits via `POST /api/companies` and navigates to lobby
3. **Company Lobby** (`/c/{company_id}`) — Top-screen canvas renders lobby
   with company name, KPI badges (active agents, pending approvals), and
   clickable room tiles. SSE subscription applies deltas live. Bottom screen
   has room directory links with counts
4. **Team Room** (`/c/{company_id}/room/{room_id}`) — Top-screen canvas
   renders lead desk + up to 5 worker desks with 2-frame idle/work
   animation. Clicking a sprite opens the agent dossier in the bottom screen.
   Bottom screen includes:
   - Typewriter dialogue box
   - Agent dossier (portrait, name/role/state, token bar, model dropdown
     with `PUT /api/agents/{id}/model`, Pause/Resume/Stop buttons)
   - Kanban drawer (BACKLOG/READY/IN_PROGRESS/REVIEW/AWAITING_APPROVAL/DONE
     + BLOCKED columns, Advance button → `POST /api/actions`)
   - Approvals drawer (pending approvals with Approve/Reject)
   - Event log drawer (recent events from state snapshot)
   - Agent logbook drawer (run history)

### Removed (old scaffold)
- `src/lib/phaser/` — Phaser bridge and scene files
- `src/lib/stores/floors.ts`, `events.ts` — Old floor-based stores
- `src/routes/events/`, `floors/`, `sprint-board/` — Old routes
- All test files referencing the old API

## Verification results
- `npm run check` — **0 errors, 0 warnings**
- `npm run build` — **Succeeded**, produced `build/` with `index.html`
  fallback, `_app/` chunks, and `assets/` directory
