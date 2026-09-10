# Polyfloor — Agent Progress & Run Log

## Architectural Decisions

| Date | Topic | Decision & Rationale |
| :--- | :--- | :--- |
| 2026-09-10 | Assets | Adopted LimeZu 16x16 Modern Interior & Character Sprites in `frontend/static/assets/` |
| 2026-09-10 | Renderer | Plain HTML5 2D Canvas + DOM overlay. Zero WebGL engine dependencies for maximum portability. |
| 2026-09-10 | Transport | Server-Sent Events (`/api/events`) for backend-to-frontend streaming deltas + REST POST (`/api/actions`). |
| 2026-09-10 | Nix Harness | Refactored `flake.nix` to `flake-parts` with `treefmt-nix`, `git-hooks-nix`, and `services.polyfloor` NixOS module. |
| 2026-09-10 | Continuity | Implemented Agentic Continuity Harness (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `feature_list.json`, `init.sh`). |

---

## Session History & Task Log

### Session 2026-09-10 — Infrastructure & Onboarding Harness
- **Goal:** Complete Flake Infrastructure (`flake-parts`, NixOS module, CI) & Agentic Continuity Harness (`AGENTS.md`, `feature_list.json`, `init.sh`).
- **Completed Features:**
  - `INFRA-01`: Hermetic `flake-parts` setup with devShell and `treefmt-nix`.
  - `ASSET-01`: 16x16 orthogonal pixel art tileset and character sprites staged.
  - `NIX-01`: Hardened NixOS service module with `DynamicUser = true`.
- **Status:** Infrastructure harness complete and verified. Ready for UI-01 & BUS-01 implementation.
