# Polyfloor — Project Constitution & Agent Instructions

## Project Overview

Polyfloor is an autonomous multi-floor enterprise engine modeled as a corporate skyscraper with a GBA/DS retro dual-screen UI (HTML5 2D canvas top screen + Pokétch bottom screen), Python/FastAPI backend daemon, and isolated NixOS service modules per floor/department.

- **Top Screen:** $320 \times 240$ base pixel art canvas ($16 \times 16$ tilemap grid, integer scaled) displaying active floor suites, desks, and agent sprites.
- **Bottom Screen:** Pokétch-style telemetry console with bust portraits, dialogue boxes, task approvals, and live event feeds.
- **Backend:** FastAPI event bus streaming SSE deltas (`/api/events`) and handling action dispatches (`/api/actions`).
- **NixOS Layer:** Hermetic `flake-parts` flake exporting `nixosModules.default` for systemd service deployment.

---

## Canonical Architecture Map

```
Polyfloor/
├── frontend/               # SvelteKit + TypeScript + HTML5 2D Canvas
│   ├── src/                # Canvas render loop, Pokétch components, state stores
│   └── static/assets/      # 16x16 pixel tilesets and character spritesheets
├── backend/                # FastAPI + Python 3.12 + SQLite/asyncpg
│   ├── src/polyfloor/      # Core daemon, SSE event bus, agent routers
│   └── tests/              # pytest unit & integration tests
├── modules/                # NixOS service modules
│   ├── nixos/polyfloor.nix # Primary services.polyfloor module definition
│   ├── tower.nix           # Multi-floor company tower orchestration module
│   └── flake-module.nix    # Flake-parts module registration
├── floors/                 # Floor templates and runtime output specs
├── pkgs/                   # Nix package derivations (backend, frontend, default)
├── flake.nix               # Hermetic flake-parts entry point
├── feature_list.json       # Machine-readable task backlog
├── agent-progress.md       # Session run log and architectural decisions
└── init.sh                 # Deterministic session onboarding script
```

---

## Core Commandments & Invariants

1. **Strict $16 \times 16$ Orthogonal Pixel Art:**
   - All environment tiles and character sprites must adhere to $16 \times 16$ grid alignment (or standard multi-tile $16\times32$ bust frames).
   - No 32x32/48x48 assets in the main canvas game loop.
2. **Zero Heavy Engine Dependencies:**
   - HTML5 2D Canvas API + Svelte 5 DOM overlays only.
   - Do NOT add Phaser, Three.js, Pixi.js, or heavy WebGL libraries unless explicitly instructed.
3. **Nix Hermetism & Formatting:**
   - All Nix changes must evaluate cleanly via `nix flake check`.
   - Code formatting must pass `nix fmt -- --check`.
4. **Feature Backlog Synchronization:**
   - Every completed task must be verified against `feature_list.json` and updated to `"passes": true`.
   - Document key decisions and commits in `agent-progress.md`.
5. **Security & Secrets:**
   - Never commit API keys, tokens, or plaintext secrets. Use `sops-nix` or runtime `environmentFile`.

---

## Verification & Tooling Cheatsheet

```bash
just dev         # Run local backend & frontend development servers
just check       # Run full suite: nix fmt check, ruff, mypy, pytest, svelte-check, nix flake check
just fmt         # Format all code via treefmt (nix, python, svelte, json, md)
just test        # Run backend and frontend unit tests
nix flake check  # Evaluate all flake outputs and NixOS module assertions
./init.sh        # Run deterministic onboarding environment check
```

---

## Context Recovery Protocol

When starting or resuming a session:

1. Run `./init.sh` to check tool availability, staged assets, and uncompleted tasks.
2. Read `agent-progress.md` (the last 3 log entries) to understand recent work and decisions.
3. Inspect `feature_list.json` and pick the highest-priority item where `"passes": false`.
4. Implement the feature following project invariants.
5. Run `just check` to verify code quality and tests.
6. Commit changes, log progress in `agent-progress.md`, and set `"passes": true` for the completed feature ID in `feature_list.json`.
