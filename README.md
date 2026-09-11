# Polyfloor

**Autonomous multi-company enterprise engine with a GBA/DS department-store UI.**

A **company is the tenant.** Each company owns its own agents, teams, boards,
artifacts, memory, budgets, credentials, and user-facing channels — fully
isolated from every other company on the same instance. Agents work
autonomously inside their company; all external side effects (publish, spend,
send) pass through human/CEO approval gates.

> **Status:** Active development. The backend is feature-complete for the MVP
> (company-as-tenant schema, four work systems, model router, avatar composer,
> SSE, 31 passing tests). The frontend SPA is built and served by the backend.
> This is not yet production-grade autonomous-business software — treat every
> agent action as sandboxed and approval-gated.

---

## What Polyfloor is

Polyfloor models an AI company as a tenant inside a virtual department store
rendered like a GBA/Nintendo DS game:

- **Top screen:** HTML5 2D canvas, 320×240 virtual, 16×16 tiles, integer
  nearest-neighbor scaling, `image-rendering: pixelated`. No WebGL, no Three.js.
- **Bottom screen:** DOM Pokétch/communicator — portraits, typewriter text,
  actions, boards, model selector.
- **1F lobby / company directory:** create a company, pick one, start intake.
- **Company lobby + team rooms:** a lobby with clickable team-room tiles; each
  room shows a lead desk + vacant/occupied worker desks. Semantic zoom keeps
  sprite counts small.
- **Four work systems** (never collapsed into one chat log): an append-only
  event log, a Kanban/task DAG with WIP limits, an artifact registry, and an
  approval queue.

A **floor is a visual/layout container, not an isolation boundary.** The old
"R&D on 4F, marketing on 3F, HR on 2F as separate companies" model is
**obsolete** — see [`SPEC_POLYFLOOR.md`](./SPEC_POLYFLOOR.md) §1–2. The backend
never treats a floor as the security or data boundary; `company_id` is.

---

## Quick start

### Run it (Nix)

```bash
nix run github:T0PSH31F/Polyfloor
```

This builds and runs the backend (FastAPI on `127.0.0.1:8001`, SQLite WAL by
default) which also serves the built frontend SPA. Open
`http://127.0.0.1:8001`.

### Install the package

```bash
nix profile install github:T0PSH31F/Polyfloor
```

### NixOS module

```nix
{
  inputs.polyfloor.url = "github:T0PSH31F/Polyfloor";
  # ...

  imports = [ inputs.polyfloor.nixosModules.default ];

  services.polyfloor = {
    enable = true;
    host = "127.0.0.1";
    port = 8001;
    dataDir = "/var/lib/polyfloor";
    # Point at an OpenAI-compatible router (Kong / Extreme Router / LiteLLM).
    # Polyfloor enumerates GET {routerEndpoint}/models and calls
    # POST {routerEndpoint}/chat/completions.
    routerEndpoint = "http://127.0.0.1:4000/v1";
    defaultHrModel = "mimo-v2.5-pro";
    # sops-managed env file (see Secrets below). May also be omitted in dev.
    environmentFile = config.sops.secrets.polyfloor-env.path;
  };
}
```

### Module options

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `enable` | bool | `false` | Enable the Polyfloor systemd service. |
| `package` | package | *(required)* | The Polyfloor package to run (use `inputs.polyfloor.packages.${system}.default`). |
| `host` | str | `127.0.0.1` | Bind address. Loopback by default; put a reverse proxy in front for remote access. |
| `port` | port | `8080` | Backend HTTP port. (`nix run` uses `8001`.) |
| `dataDir` | path | `/var/lib/polyfloor` | Persistent state root; per-company workspaces live under `companies/<company_id>/`. |
| `openFirewall` | bool | `false` | Open the HTTP port in the firewall. |
| `environmentFile` | path\|null | `null` | Path to an env file with secrets (sops). Never put secrets in the module config. |
| `routerEndpoint` | str | `http://127.0.0.1:4000/v1` | OpenAI-compatible router base URL (must end in `/v1`). |
| `defaultHrModel` | str | `mimo-v2.5-pro` | Default model id for the HR coordinator agent. |
| `staticDir` | path\|null | `null` | Directory of the built frontend SPA to serve (used by `nix run`). |

The module is hardened: `DynamicUser`, `ProtectSystem=strict`, `ProtectHome`,
`PrivateTmp`, `NoNewPrivileges`, `StateDirectory=polyfloor`, and a locked-down
`CapabilityBoundingSet`/`RestrictNamespaces`.

---

## Router / model setup

Polyfloor talks to any **OpenAI-compatible** router: Kong, Extreme Router,
LiteLLM, or a raw OpenAI gateway. The router must expose:

- `GET {routerEndpoint}/models` — model discovery (Polyfloor calls this).
- `POST {routerEndpoint}/chat/completions` — agent inference.

Polyfloor exposes these to the UI:

- `GET /api/models` — enumerates the router's models and groups them as
  `free`, `fast`, `reasoning`, `frontier`, returning
  `{ id, owned_by, tier, context, pricing }` per model. When the router is
  unreachable it falls back to a mock catalog that includes `mimo-v2.5-pro`.
- `PUT /api/agents/{agent_id}/model?company_id=...` — change an agent's model
  at runtime, scoped to that company (404 if the agent is not in that company).

The default HR orchestrator model is **Xiaomi MiMo-V2.5 Pro** (`mimo-v2.5-pro`);
workers default to the free/fast pool. The catalog is never hardcoded in the
UI — it always comes from the live router.

See [`docs/model-routing.md`](./docs/model-routing.md) and the frozen
[`docs/API_CONTRACT.md`](./docs/API_CONTRACT.md).

---

## Secrets

Secrets are **never** passed as plain environment variables or committed to the
repo. The backend reads them from **file paths** so they never appear in the
process environment or logs:

- `POLYFLOOR_ROUTER_API_KEY_FILE` — path to a file containing the router API key.
- `POLYFLOOR_API_TOKEN_FILE` — path to a file containing the platform bearer
  token (optional; when unset the API is open in dev).

In NixOS, provide these via a sops-managed `environmentFile`:

```nix
services.polyfloor.environmentFile = config.sops.secrets.polyfloor-env.path;
```

The env file may contain `POLYFLOOR_ROUTER_API_KEY_FILE=/run/secrets/...`,
`POLYFLOOR_API_TOKEN_FILE=/run/secrets/...`, and a
`POLYFLOOR_DATABASE_URL=...` if you use PostgreSQL instead of the default
SQLite. Agents never receive raw secrets — they request a **capability**
(`send_customer_email`, `publish_listing`) and the platform resolves the
company-scoped secret after policy checks. See
[`docs/security.md`](./docs/security.md).

---

## Creating a company

A fresh install starts at the **1F intake wizard**: name the business, state the
goal, pick a grilling intensity, choose a template, and HR materializes the
tenant. You can also create a company directly:

```bash
curl -X POST http://127.0.0.1:8001/api/companies \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Lumin Press",
    "goal": "Ship a digital product end-to-end",
    "template_id": "digital-products"
  }'
```

Creating a company materializes the CEO, HR, C-suite, team leads, rooms, desks,
and the gated research → spec → draft → QA → marketing → publish pipeline, plus
a publish approval. The **digital-products** template is the MVP reference
template; others (freelance agency, e-commerce, creator, investment research,
CAD/3D) are designed for but not required on day one.

---

## Isolation model

`company_id` is the boundary. Every request, event, task, artifact, trace, and
secret lookup requires it — a missing company id is a bug, not a default.

- `company_id` is on every record; queries and writes filter by it.
- An agent belongs to exactly one company.
- Two companies cannot see each other's data, memory, credentials, or spend.
- Per-company workspaces live under `dataDir/companies/<company_id>/`.
- Agents request **capabilities**, never raw secrets; the platform resolves the
  company-scoped secret after policy checks.

Isolation tiers implemented today: **Development** (shared process, strict
`company_id`, distinct workspace roots) and **Standard** (per-company queue,
router key, memory namespace, workspace, secrets). A hardened **High-risk** tier
(per-company container, separate DB role) is designed for, not required for the
MVP. See [`SPEC_POLYFLOOR.md`](./SPEC_POLYFLOOR.md) §4 and
[`docs/security.md`](./docs/security.md).

---

## Assets — LimeZu Modern Interiors (license note)

Polyfloor uses the **LimeZu *Modern Interiors* / *Modern Exteriors* 16×16**
tilesets and character sprites only. 32×32 and 48×48 assets are **not** used.

These assets are **not bundled** in this repository. They are staged at build
time from the original LimeZu releases under their respective licenses (CC-BY —
see the original asset pages for the exact terms). If the license of a given
asset pack forbids redistribution, Polyfloor fetches/stages it at build time
rather than vendoring it into the source tree. Always check the original
LimeZu asset license before redistributing.

---

## Development

```bash
./init.sh        # tool availability, staged assets, next uncompleted features
just dev         # backend :8001 (--reload) + frontend :5173 (Vite proxies /api → :8001)
just check       # nix fmt --check, ruff, pytest, svelte-check, nix flake check --no-build
just test        # backend + frontend tests
nix fmt          # format everything via treefmt
nix flake check  # evaluate flake outputs and NixOS module assertions
```

Backend dev without Nix:

```bash
cd backend && uv sync && uv run uvicorn polyfloor.main:app --reload --host 127.0.0.1 --port 8001
cd frontend && npm install && npm run dev
```

### Honest verification status

- **Backend tests pass:** `cd backend && python -m pytest` → 31 passed (company
  isolation, WIP enforcement, HR hire flow, SSE event bus, model router, avatar
  composer, bootstrap pipeline, full API).
- **`nix flake check` / `nix fmt`** require a Nix installation, which is not
  available in every sandbox. These are wired into `just check` and the repo's
  CI; run them locally or rely on CI for Nix-side verification.
- The frontend SPA is built and served by the backend; UI-level visual checks
  are not automated here.

---

## Documentation

- [`SPEC_POLYFLOOR.md`](./SPEC_POLYFLOOR.md) — canonical specification (wins
  over older notes).
- [`docs/API_CONTRACT.md`](./docs/API_CONTRACT.md) — frozen MVP API contract.
- [`docs/architecture.md`](./docs/architecture.md) — architecture & data flow.
- [`docs/model-routing.md`](./docs/model-routing.md) — router/model setup.
- [`docs/security.md`](./docs/security.md) — isolation, secrets, approval gates.
- [`docs/team-board.md`](./docs/team-board.md) — task lifecycle & WIP.
- [`docs/deployment.md`](./docs/deployment.md) — NixOS module & deployment.
- [`AGENTS.md`](./AGENTS.md) — project constitution for AI contributors.

## License

See [`LICENSE`](./LICENSE).
