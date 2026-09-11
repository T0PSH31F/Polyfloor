# Polyfloor — Agent Progress & Run Log

## Architectural Decisions

| Date | Topic | Decision & Rationale |
| :--- | :--- | :--- |
| 2026-09-10 | Assets | Adopted LimeZu 16x16 Modern Interior & Character Sprites in `frontend/static/assets/` |
| 2026-09-10 | Renderer | Plain HTML5 2D Canvas + DOM overlay. Zero WebGL engine dependencies for maximum portability. |
| 2026-09-10 | Transport | Server-Sent Events (`/api/events`) for backend-to-frontend streaming deltas + REST POST (`/api/actions`). |
| 2026-09-10 | Nix Harness | Refactored `flake.nix` to `flake-parts` with `treefmt-nix`, `git-hooks-nix`, and `services.polyfloor` NixOS module. |
| 2026-09-10 | Continuity | Implemented Agentic Continuity Harness (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `feature_list.json`, `init.sh`). |
| 2026-09-10 | Tenant model | Adopted **company-as-tenant** as canonical (SPEC §1–2). The old department-per-floor model (R&D on 4F, marketing on 3F, HR on 2F as separate companies) is OBSOLETE. `company_id` is the boundary; floors are visual/layout containers only. |
| 2026-09-10 | Storage | SQLite WAL as the default DB so a fresh `nix run` works with zero external services; PostgreSQL optional via `POLYFLOOR_DATABASE_URL`. |
| 2026-09-10 | Model router | OpenAI-compatible client to `POLYFLOOR_ROUTER_ENDPOINT` (Kong/Extreme Router/LiteLLM `/v1`). `GET /api/models` groups free|fast|reasoning|frontier; `PUT /api/agents/{id}/model` is company-scoped. Default HR model: `mimo-v2.5-pro`. Mock fallback catalog. |
| 2026-09-10 | Secrets | Secrets read from file paths (`*_FILE`), never env vars or logs. Agents request capabilities; the platform resolves company-scoped secrets after policy checks. |
| 2026-09-10 | Agent loop | Mock agent executor for the MVP (no live LLM calls in the loop); real router client is wired and tested separately. |
| 2026-09-10 | NFP integration | NFP `76-orchestrators/polyfloor.nix` now imports `inputs.polyfloor.nixosModules.default` (no vendored `fetchFromGitHub`) and points `routerEndpoint` at the NFP LLM router. |

---

## Session History & Task Log

### Session 2026-09-10 — Infrastructure & Onboarding Harness
- **Goal:** Complete Flake Infrastructure (`flake-parts`, NixOS module, CI) & Agentic Continuity Harness (`AGENTS.md`, `feature_list.json`, `init.sh`).
- **Completed Features:**
  - `INFRA-01`: Hermetic `flake-parts` setup with devShell and `treefmt-nix`.
  - `ASSET-01`: 16x16 orthogonal pixel art tileset and character sprites staged.
  - `NIX-01`: Hardened NixOS service module with `DynamicUser = true`.
- **Status:** Infrastructure harness complete and verified. Ready for UI-01 & BUS-01 implementation.

### Session 2026-09-10 — Company-as-Tenant Rewrite, Backend Complete, Docs, NFP
- **Goal:** Land the canonical company-as-tenant model end-to-end: full backend, built frontend, public-repo docs, and NFP integration.
- **Backend (FastAPI + SQLite WAL):** Full SPEC §9.4 schema with `company_id` isolation; four work systems (append-only event log, Kanban/task DAG with WIP limits, artifact registry, approval queue); digital-products bootstrap pipeline; OpenAI-compatible model router (`GET /api/models`, `PUT /api/agents/{id}/model`); dynamic avatar composer (Pillow, deterministic seed, tenant path isolation); SSE event bus (`GET /api/events`, per-company, heartbeat); observability (`/healthz`, `/metrics`, structured logs with `company_id`/`trace_id`).
- **Tests:** 31 passing (isolation, WIP, HR hire flow, event bus, model router, avatar, bootstrap, full API).
- **Frontend:** SvelteKit SPA built and served by the backend (`POLYFLOOR_STATIC_DIR`); dual-screen shell, 1F intake wizard, team rooms, bottom-screen dossier.
- **NixOS module:** `services.polyfloor` hardened (DynamicUser, ProtectSystem=strict, …) with SPEC §11 options (`routerEndpoint`, `defaultHrModel`, `staticDir`); `nixosModules.default` importable downstream.
- **NFP integration:** `76-orchestrators/polyfloor.nix` rewritten to `imports = [ inputs.polyfloor.nixosModules.default ]`, `routerEndpoint` → NFP LLM router `/v1`, `defaultHrModel = "mimo-v2.5-pro"`, secrets via sops `environmentFile`. `78-llm-routers` Kong route exposes `GET /v1/models` for Polyfloor enumeration.
- **Docs:** README rewritten for strangers (quick start, module options, router setup, secrets, creating a company, isolation, LimeZu license, honest verification status). AGENTS.md updated to company-as-tenant. `docs/` de-staled (no department-per-floor / `floor_id`-as-boundary language). `feature_list.json` honest pass flags + new entries (ROUTER-01, AVATAR-01, BOOTSTRAP-01, ISOLATION-01, OBS-01, NFP-01).
- **Verification gaps:** Nix (`nix flake check`, `nix fmt`) could not run in this sandbox — deferred to CI. Backend tests pass locally. NFP module not nix-evaluated here.
- **Status:** Backend MVP complete; docs public-repo quality; NFP integration wired. Follow-ups: live LLM agent loop, extra company templates, high-risk isolation tier.
