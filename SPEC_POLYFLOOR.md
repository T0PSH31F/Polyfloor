# POLYFLOOR ARCHITECTURAL SPECIFICATION & PRD

**Autonomous multi-company enterprise engine with a GBA/DS department-store UI.**

Status: canonical. If implementation details conflict with older notes, this file wins.

---

## 1. Core Principle

A **company is the tenant**. A tenant owns its agents, teams, boards, artifacts, memory, budgets, credentials, schedules, and user-facing channels.

A **floor is a visual/layout container**, not an isolation boundary. The UI may show one company as one lobby plus rooms, or later as multiple color-coded floors, but the backend never treats a floor as the security or data boundary.

```
Platform (Polyfloor instance)
└── Company (tenant / business entity)
    ├── Identity, policy, budget, model routing, capability grants
    ├── CEO, HR, C-suite, team leads, workers
    ├── Event log, Kanban/task DAG, artifacts, approvals, ledger
    ├── Memory namespace, workspace, secrets, router virtual key
    └── Presentation: lobby, rooms, optional extra visual floors
```

Authority chain:

```
company_id -> role permissions -> capability grants -> action
```

Visual chain (presentation only):

```
company_id -> floor_id -> room_id -> desk_id -> agent_id
```

---

## 2. Why This Model

Department-per-floor (R&D on 4F, marketing on 3F, HR on 2F) is a good office metaphor for a *single* giant organization. It is a bad tenant model. It makes it easy for company B's email, social, memory, or customer queue to leak into company A.

Company-per-tenant with a lobby + clickable team rooms:

- Keeps every credential, inbox, phone number, memory namespace, and ledger inside one company.
- Gives a direct production line: R&D -> product -> QA -> marketing -> publish.
- Scales visually by adding rooms, then extra floors *inside the same company*.
- Starting another company means creating another tenant, not another entangled department.

---

## 3. Platform Layout

```
+================================================================+
| ROOFTOP: platform telemetry only                               |
| Router health, host resources, aggregate spend.                |
| No company content unless a company is explicitly selected.    |
+================================================================+
| 2F+ COMPANY FLOORS                                             |
| Each occupied company floor belongs to exactly one company.    |
| MVP: one lobby floor per company, with clickable team rooms.   |
| Growth: extra visual floors for the same company if crowded.   |
+================================================================+
| 1F LOBBY / COMPANY DIRECTORY                                   |
| Create a company, pick an existing company, start intake.      |
+================================================================+
| B1 TOOL CATALOG                                                |
| Available MCP/runtime templates. Grants are company-scoped.    |
+================================================================+
| B2 FOUNDATION                                                  |
| Service health, encrypted secret *presence*, never secret text.|
+================================================================+
```

### 3.1 Company lobby (MVP overview)

Entering a company opens a lobby, not a packed simulation of every worker.

Lobby contents:

- Company name, logo, health, daily spend, approval count.
- CEO / C-suite room tile.
- HR / coordinator room tile with hiring queue badge.
- One tile per team suite (R&D, product/writing, marketing, customer ops, etc.).
- Directory links to Floor Board, Jobs, Artifacts, Ledger, Memory Health.
- Elevator / company switcher.

Room tiles show counts only: active, blocked, vacant desks. They do not animate every worker.

### 3.2 Team room (detail view)

Clicking a suite renders that team's workspace:

- Lead desk (larger).
- Up to 5 worker desks, vacant until HR assigns a worker.
- Team-relevant furniture from LimeZu 16x16 interiors.
- Live sprites for assigned agents only.
- Current task, WIP `n/limit`, cost today, review queue.

Clicking an agent opens the bottom-screen dossier.

### 3.3 Semantic zoom

| Level | What is rendered | Typical sprite count |
|---|---|---|
| Company directory (1F) | Company cards | 0-12 cards |
| Company lobby | Room tiles + KPI badges | 0-8 overview sprites |
| Team room | Lead + workers at desks | 1-6 sprites |
| Agent dossier | Portrait, metrics, actions | 1 bust |

Do not animate 40 workers on one 320x240 map.

### 3.4 Multi-floor growth inside one company

If a company outgrows one lobby:

- Keep the same `company_id`.
- Add `company_floors` with color-coded tabs.
- Example: Floor 1 lobby/exec/ops, Floor 2 production, Floor 3 creative/distribution.
- Backend grouping remains company-first. UI tabs are views.

Never put two companies on one visual floor.

---

## 4. Isolation Requirements

Every request, event, task, artifact, trace, log, and secret lookup requires `company_id`.

| Resource | Boundary |
|---|---|
| Company identity | Immutable `company_id` on all records |
| Agents | An agent belongs to exactly one company |
| Boards / tasks / events | Queries and writes filter by `company_id` |
| Memory | Separate Honcho/brain-service namespace per company |
| Credentials | Per-company secret path and capability grant; no global email/social agent |
| Tools / MCP | Platform catalog + explicit per-company allowlist and credential binding |
| Router spend | Per-company virtual key, tags, budget, rate limit |
| Workspaces | `/var/lib/polyfloor/companies/<company_id>/` |
| Logs / traces | `company_id`, `agent_id`, `task_id`, `trace_id`; redaction policy |
| User channels | Phone, mailbox, Telegram bot, social account maps to one company |

Agents never receive raw credentials. They request a **capability** (`send_customer_email`, `publish_listing`). The platform resolves the company-scoped secret after policy checks.

Isolation tiers:

| Tier | Model | Use |
|---|---|---|
| Development | Shared process, strict `company_id`, distinct workspace roots | UI/dev, mock companies |
| Standard | Per-company queue, router key, memory namespace, workspace, secrets | Real businesses |
| High-risk | Per-company systemd/container, separate DB role, hardened sandbox | Customer data, money, authenticated publishing |

MVP implements Development + Standard. High-risk is designed for, not required on day one.

---

## 5. Organization and Control Loop

### CEO

- Owns company summary, strategy, and user-facing brief.
- Receives C-suite memos and approval-gated items.
- Cannot bypass budget, policy, or external-action gates.
- May *compose* user notifications; the backend sends them after policy validation.
- Sole company agent allowed to request user-channel dispatch.

### HR Coordinator

- Creates, assigns, pauses, and retires workers.
- Assigns desks, models, token envelopes, skills, and tool capabilities.
- Enforces headcount and WIP.
- Receives staffing requests from team leads.
- Routes approval-gated hires/spend to CEO/user.
- Owns the agent logbook: hire history, prompt versions, model changes, retirements.

Team leads **request** specialists. They never spawn agents or grant tools directly.

### Team leads

- Own their Kanban queue and work allocation.
- Can request workers, skills, tools, budget, or cross-team deliverables via signed events.
- Cannot mutate other teams' workers or unrelated credentials.

### C-suite

- **CFO:** ledger, forecasts, model spend vs revenue, spending alerts.
- **CTO:** model routing, prompt/eval quality, tool reliability, security posture.
- **COO:** WIP, blocked work, throughput, retries, circuit breakers.
- **CHO:** profile quality, team composition, hire/retire recommendations.
- **QA panel:** workflow state and executive review table, not a separate tenant floor. Multi-model review of artifacts against a rubric before release.

### QA / release gate

1. Lead moves work to `REVIEW`.
2. QA panel runs independent reviewers.
3. Outcomes become immutable review records.
4. Failures return to the originating team.
5. Passing artifacts that spend money, publish, or create legal/brand exposure go to `AWAITING_APPROVAL`.
6. Only then may a capability-gated publish/ship run.

---

## 6. Work Systems

Use four systems. Do not collapse them into one chat log.

| System | Purpose |
|---|---|
| Append-only event log | Audit trail: requests, decisions, errors, staffing, policy |
| Kanban / task DAG | Execution: owner, status, criteria, budget, retries |
| Artifact registry | What was produced: URI, hash, lineage, review status |
| Approval queue | Human/CEO gates: spend, hire, publish, irreversible I/O |

### 6.1 Event log

Agents do not continuously read a giant shared board. They receive targeted events.

```json
{
  "event_id": "evt_01",
  "company_id": "co_luminpress",
  "source_agent_id": "rnd_lead_01",
  "target": { "kind": "role", "id": "hr_coordinator" },
  "type": "staffing.requested",
  "correlation_id": "task_product_174",
  "payload": {
    "role": "technical-writer",
    "reason": "approved spec requires long-form drafting",
    "requested_budget_usd": 1.5
  },
  "requires_approval": false
}
```

### 6.2 Task lifecycle

```
BACKLOG -> READY -> IN_PROGRESS -> REVIEW -> AWAITING_APPROVAL -> DONE
                         |---> BLOCKED
```

Every task has exactly one owner, `company_id`, `team_id`, acceptance criteria, budget limit, retry limit, artifact destination, and `trace_id`.

Default WIP: 3 concurrent `IN_PROGRESS` tasks per team, configurable per company/team. Over-capacity work stays `READY` or `BLOCKED`. It must not auto-spawn workers.

### 6.3 Direct production line

Example digital-product path:

```
R&D research artifact
  -> Product lead accepts specification
    -> Writing lead produces draft
      -> QA panel evaluates
        -> Marketing produces campaign assets
          -> Publish agent requests external-release approval
```

Dependencies are explicit task edges, not ambient board reading.

---

## 7. Company Templates

Do not hardcode the same departments into every company. Intake selects a template; HR materializes the org graph.

| Template | Default teams | Hard gates |
|---|---|---|
| Digital products | R&D, product/writing, creative, marketing, distribution, customer ops | Marketplace publish, paid assets |
| Freelance agency | Intake/sales, delivery, QA, client success, finance | Client send, deadline change |
| E-commerce / dropship | Research, supplier ops, storefront, creative, marketing, support | Purchase, ad spend, listing, refund |
| Creator / influencer | Strategy, production, editing, distribution, community | Public post, sponsor reply |
| Investment research | Research, risk, data, compliance | Any trade/execution stays human-approved |
| CAD / 3D assets | Design, production, rendering, QA, marketplace | Publish, paid compute |

Custom/oddball prompts still produce a template-like org: goal, teams, policies, model routes, WIP, required capabilities.

---

## 8. Frontend

### 8.1 Dual-screen shell

- **Top screen:** HTML5 2D canvas, 320x240 virtual, 16x16 tiles, integer nearest-neighbor scale 3x or 4x, `image-rendering: pixelated`.
- **Bottom screen:** DOM Pokétch/communicator: portraits, typewriter text, actions, boards, model selector.
- No WebGL, no Three.js, no isometric engine.
- LimeZu *Modern Interiors* 16x16 only. Use `frontend/static/assets/room_builder.png`, `interiors.png`, `characters/`, and `ASSET_MANIFEST.md`.

### 8.2 Game loop

- Static tiles rendered once to an offscreen/background canvas on room/floor change.
- Dynamic layer: sprites, bubbles, badges.
- Browser animates cosmetic idle locally (2-frame breath/type).
- Backend SSE sends *state deltas only*: assignment, task status, approvals, metrics. No 60 Hz simulation tick.

### 8.3 Bottom-screen dossier

When an agent is selected:

- High-res bust portrait (Fire Emblem / visual-novel style).
- Name, role, team, floor/room, model id, token in/out, cost, context bar, current task.
- Actions: Approve, Reject, Pause/Resume, Stop, Override token cap (gated), Inspect memory traces, Inspect task, Open board.
- Model dropdown populated from `GET /api/models`.
- Hiring/budget/publish controls appear only when policy says the user/CEO must decide.

### 8.4 1F intake wizard

Fresh install / new company:

1. Reception greeting.
2. Business-goal prompt.
3. Grilling intensity: 4 multiple-choice tiers.
4. Name, logo, template, initial teams, budget policy, escalation channels.
5. HR generates the company tenant and lobby.
6. User returns to 1F later to create *another company*. Changes to an existing company go through that company's CEO/HR, not a global wizard overwrite.

### 8.5 Transport

- SSE `GET /api/events` for server -> UI state.
- REST `POST /api/actions` for user commands.
- Do not use WebSockets unless a later requirement proves bidirectional cursor-rate traffic.

---

## 9. Backend

### 9.1 Stack

FastAPI, SQLite WAL, structured JSON logs, Prometheus `/metrics`, OpenAI-compatible router client.

### 9.2 Model routing

- Default router base URL configurable (`services.polyfloor.routerEndpoint`, e.g. Kong / Extreme Router / LiteLLM at `http://127.0.0.1:4000/v1`).
- `GET /api/models` enumerates `GET {router}/models` and returns `{ id, owned_by, tier, context, pricing? }` grouped as `free`, `fast`, `reasoning`, `frontier`.
- `PUT /api/agents/{agent_id}/model` changes an agent's model at runtime inside that company.
- Default HR orchestrator model: Xiaomi **MiMo-V2.5 Pro** when configured; workers default to free/fast pool models.
- Never hardcode the catalog in the UI.

### 9.3 Dynamic avatar composer

Implement `backend/assets/avatar_composer.py` (Pillow):

- Layer sources: allowlisted LimeZu generator parts (`bodies`, `outfits`, `hair`, `accessories`) with identical frame geometry.
- New worker gets immutable `avatar_recipe` + deterministic company/agent seed.
- Output: `/var/lib/polyfloor/companies/<company_id>/avatars/<agent_id>.png` (or frontend-served equivalent).
- Reject arbitrary paths, URLs, or user-supplied filenames.
- Tests: invalid ids, size mismatch, determinism, tenant path isolation.
- MVP fallback: map role -> staged `frontend/static/assets/characters/*.png` if generator parts are absent.

### 9.4 Core schema (minimum)

```
companies(id, name, slug, template_id, status, visual_theme, budget_policy_id)
company_floors(id, company_id, ordinal, label, template_id, layout_json)
rooms(id, company_floor_id, team_id, room_type, layout_json, wip_limit)
teams(id, company_id, name, role_type, lead_agent_id, policy_json)
agents(id, company_id, team_id, role, model_id, avatar_recipe, state,
       capability_profile_id, home_room_id, home_desk_id, token_spend)
tasks(id, company_id, team_id, owner_agent_id, parent_task_id, status,
      priority, acceptance_criteria_json, budget_limit, retry_limit)
events(id, company_id, source_agent_id, target_type, target_id, event_type,
       correlation_id, payload_json, trace_id, created_at)
artifacts(id, company_id, task_id, type, uri, content_hash, review_status)
approvals(id, company_id, task_id, requested_by, policy_key, risk_level,
          payload_json, status, decided_by)
integrations(id, company_id, provider, capability, secret_ref, status)
agent_runs(id, company_id, agent_id, task_id, model_id, trace_id,
           started_at, ended_at, input_tokens, output_tokens, cost, outcome)
```

Repository/service APIs take a mandatory `CompanyContext`. A missing company id is a bug, not a default.

### 9.5 Observability

- Structured logs with `company_id`, `trace_id`, `task_id`, `agent_id`.
- Metrics: agents by company/state, tokens and USD by company/team/model, task latency, WIP, approval age, SSE clients, router errors.
- Agent logbook UI is a filtered view of `events` + `agent_runs` + hire records.

---

## 10. Escalation

| Level | Channel | Examples |
|---|---|---|
| Low | Bottom-screen badge | Task done, idle worker, info |
| Medium | Telegram | Hiring approval, budget threshold, campaign/product ready for review |
| Critical | SMS / Twilio voice | Runaway loop, spend breach, unauthorized I/O, security failure |

Backend policy sends notifications. Agents request them; they do not hold channel tokens.

---

## 11. Nix / OSS packaging

Public GitHub repo. Users must be able to:

```bash
nix run github:T0PSH31F/Polyfloor
nix profile install github:T0PSH31F/Polyfloor
```

Or import the module:

```nix
{
  inputs.polyfloor.url = "github:T0PSH31F/Polyfloor";
  # ...
  imports = [ inputs.polyfloor.nixosModules.default ];
  services.polyfloor = {
    enable = true;
    host = "127.0.0.1";
    port = 8080;
    routerEndpoint = "http://127.0.0.1:4000/v1";
    defaultHrModel = "mimo-v2.5-pro";
    environmentFile = config.sops.secrets.polyfloor_env.path;
  };
}
```

Module options: `enable`, `package`, `host`, `port`, `dataDir`, `openFirewall`, `environmentFile`, `routerEndpoint`, `defaultHrModel`.

Hardened systemd: `DynamicUser` or dedicated user, `ProtectSystem=strict`, `ProtectHome=true`, `PrivateTmp=true`, `NoNewPrivileges=true`, `StateDirectory=polyfloor`.

README must cover: quick start, module options, router/model setup, secrets, creating a company, isolation model, LimeZu license notes, and that 32x32/48x48 assets are not used.

---

## 12. Implementation Order (MVP)

1. Company tenant boundary: schema, `CompanyContext`, workspace roots, memory namespace hook, router labels.
2. Dual-screen shell + lobby directory + 1F intake wizard.
3. Team room canvas + vacant/occupied desks + sprite states.
4. Bottom-screen dossier, model dropdown, approve/pause.
5. Event log + Kanban + approvals APIs and UI drawers.
6. HR staffing: request -> policy/budget -> hire/reuse -> desk + capabilities + avatar.
7. SSE live updates and mock-to-live router client.
8. One digital-products template end-to-end: research -> spec -> draft -> QA -> marketing assets -> gated publish request.
9. Tests, traces, metrics, README, `feature_list.json` pass flags.
10. NFP integration: import `nixosModules.default`, point `routerEndpoint` at Kong/Extreme Router, set HR model to MiMo-V2.5 Pro.
11. Only then: extra visual floors inside a company, extra templates, high-risk process isolation.

---

## 13. Non-goals (MVP)

- Isometric or NDS 2.5D camera.
- Running LimeZu's GUI character generator as a live daemon.
- WebSockets as the primary transport.
- One shared global inbox/agent across companies.
- Unbounded sub-agent spawning by team leads.
- Department-per-floor as the tenant model.
