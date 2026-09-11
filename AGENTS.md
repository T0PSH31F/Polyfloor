# Polyfloor — Project Constitution & Agent Instructions

## Project Overview

Polyfloor is an **autonomous multi-company enterprise engine** with a GBA/DS
retro dual-screen UI: HTML5 2D canvas top screen (320×240, 16×16 tiles,
integer-scaled, `image-rendering: pixelated`) + DOM Pokétch bottom screen, a
Python/FastAPI backend (SQLite WAL by default), and a hardened NixOS service
module.

The canonical model is **company-as-tenant**, not department-per-floor. A
**company** is the tenant and owns its agents, teams, boards, artifacts, memory,
budgets, credentials, and channels. A **floor** is a visual/layout container
only — never the security or data boundary. `company_id` is the boundary.

- **Top Screen:** 320×240 base pixel art canvas (16×16 tilemap, integer scaled)
  showing company lobby + team rooms, desks, and agent sprites.
- **Bottom Screen:** Pokétch-style telemetry console: bust portraits, dialogue,
  task approvals, model selector, live event feeds.
- **Backend:** FastAPI with an append-only event log, Kanban/task DAG, artifact
  registry, and approval queue; SSE state deltas (`GET /api/events`) and action
  dispatch (`POST /api/actions`). OpenAI-compatible model router.
- **NixOS Layer:** `flake-parts` flake exporting `nixosModules.default` for a
  hardened systemd service deployment.

> The canonical spec is [`SPEC_POLYFLOOR.md`](./SPEC_POLYFLOOR.md). If
> implementation details conflict with older notes, the spec wins.

---

## Canonical Architecture Map

```
Polyfloor/
├── frontend/               # SvelteKit + TypeScript + HTML5 2D Canvas
│   ├── src/                # Canvas render loop, Pokétch components, state stores
│   └── static/assets/      # 16x16 LimeZu Modern Interiors tiles + character sprites
├── backend/                # FastAPI + Python 3.12 + SQLite WAL (asyncpg optional)
│   ├── src/polyfloor/      # main, config, auth, observability, db/models
│   │   ├── routers/        # companies, rooms/agents, models, events (SSE), actions, health
│   │   ├── services/       # repository, bootstrap, hr, model_router, event_bus
│   │   ├── assets/         # avatar_composer.py (Pillow)
│   │   └── agents/         # executor (mock agent loop for MVP)
│   └── tests/              # pytest: isolation, wip, hr, event_bus, model_router, avatar, bootstrap, api
├── modules/                # NixOS service modules
│   ├── nixos/polyfloor.nix # services.polyfloor module (hardened, SPEC §11 options)
│   └── flake-module.nix    # flake-parts module registration (nixosModules.default)
├── pkgs/                   # Nix package derivations (backend, frontend, default)
├── docs/                   # API_CONTRACT.md (frozen), architecture, security, ...
├── flake.nix               # Hermetic flake-parts entry point
├── feature_list.json       # Machine-readable task backlog (honest pass flags)
├── agent-progress.md       # Session run log and architectural decisions
└── init.sh                 # Deterministic session onboarding script
```

The frozen API contract lives at [`docs/API_CONTRACT.md`](./docs/API_CONTRACT.md).

---

## Core Commandments & Invariants

1. **Strict 16×16 orthogonal pixel art:**
   - All environment tiles and character sprites adhere to a 16×16 grid (or
     standard multi-tile 16×32 bust frames).
   - No 32×32/48×48 assets in the main canvas game loop. LimeZu *Modern
     Interiors* 16×16 only.

2. **Zero heavy engine dependencies:**
   - HTML5 2D Canvas API + Svelte DOM overlays only.
   - Do NOT add Phaser, Three.js, Pixi.js, or heavy WebGL libraries unless
     explicitly instructed.

3. **Company is the tenant, not the floor:**
   - Every request, event, task, artifact, trace, and secret lookup requires
     `company_id`. A missing company id is a bug, not a default.
   - The OLD department-per-floor model (R&D on 4F, marketing on 3F, HR on 2F as
     separate companies) is **OBSOLETE**. Do not reintroduce it.
   - Floors are visual/layout containers inside a company, never isolation
     boundaries.

4. **Nix hermetism & formatting:**
   - All Nix changes must evaluate cleanly via `nix flake check`.
   - Code formatting must pass `nix fmt -- --check`.

5. **Feature backlog synchronization:**
   - Every completed task must be verified against `feature_list.json` and
     updated to `"passes": true` — but never mark anything true that is not
     actually done. Use the `"verified"` note field when something exists but
     could not be exercised in the current sandbox.
   - Document key decisions and commits in `agent-progress.md`.

6. **Security & secrets:**
   - Never commit API keys, tokens, or plaintext secrets.
   - Secrets are read from **file paths** (`*_FILE`), never from env vars, and
     never logged. Use `sops-nix` / `environmentFile`.
   - Agents request **capabilities**; they never receive raw credentials. The
     platform resolves the company-scoped secret after policy checks.

---

## Verification & Tooling Cheatsheet

```bash
./init.sh        # Check tool availability, staged assets, and uncompleted tasks
just dev         # Run local backend (:8001) & frontend (:5173, proxies /api)
just test        # Run backend and frontend unit tests
just check       # nix fmt --check, ruff, pytest, svelte-check, nix flake check --no-build
just fmt         # Format all code via treefmt (nix, python, svelte, json, md)
nix flake check  # Evaluate all flake outputs and NixOS module assertions
nix fmt          # Format everything
```

> `nix flake check` / `nix fmt` require Nix, which may be absent in some
> sandboxes. Backend tests (`cd backend && python -m pytest`, 31 passing) and
> `ruff` run without Nix. Rely on CI for full Nix-side verification when Nix is
> unavailable locally.

---

## Context Recovery Protocol

When starting or resuming a session:

1. Run `./init.sh` to check tool availability, staged assets, and uncompleted tasks.
2. Read `SPEC_POLYFLOOR.md` (canonical) and the last 3 entries in
   `agent-progress.md` to understand recent work and decisions.
3. Inspect `feature_list.json` and pick the highest-priority item where
   `"passes": false`.
4. Implement the feature following the project invariants (company-as-tenant,
   16×16 assets, no heavy engines).
5. Run `just check` (or `just test` + `ruff` when Nix is unavailable) to verify.
6. Commit changes, log progress in `agent-progress.md`, and set `"passes": true`
   for the completed feature ID in `feature_list.json` — honestly.
