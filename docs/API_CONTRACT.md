# Polyfloor MVP API Contract (frozen)

Backend runs on `http://127.0.0.1:8001`. In dev, Vite proxies `/api` to it.
All company-scoped endpoints require `company_id` via query param OR `X-Company-Id` header.

## Health / observability
- `GET /healthz` → `{ "status": "ok" }`
- `GET /metrics` → Prometheus text

## Companies (1F directory + creation)
- `GET /api/companies` → `[{ id, name, slug, template_id, goal, status }]`
- `POST /api/companies` body `{ name, goal?, template_id?, grilling_intensity?, budget_policy?, channels?, logo? }` → 201 `{ id, name, slug, template_id, goal, status }`. Creating a company materializes CEO + HR + c-suite + team leads + rooms + desks + the gated research→spec→draft→QA→marketing→publish pipeline + a publish approval.
- `GET /api/companies/{company_id}/state` → full snapshot:
  ```json
  { "company": {...}, "floors":[...], "rooms":[...], "teams":[...],
    "agents":[...], "tasks":[...], "events":[...], "artifacts":[...],
    "approvals":[...], "metrics": { "tasks_by_status": {...}, "active_agents": N, "total_agents": N, "pending_approvals": N } }
  ```
  Every object has `company_id`. Datetimes are ISO strings.

## Rooms / agents
- `GET /api/companies/{company_id}/rooms/{room_id}` → `{ room, desks:[...], agents:[...], tasks:[...], wip:{ in_progress, limit } }`
  - room has `room_type` ∈ {ceo, hr, csuite, qa, team}, `label`, `wip_limit`, `team_id`.
  - desks have `ordinal`, `agent_id` (null = vacant).
  - Room ids look like `{company_id}_ceo`, `{company_id}_hr`, `{company_id}_csuite`, `{company_id}_qa`, `{company_id}_team_rnd`, `{company_id}_team_product`, `{company_id}_team_qa`, `{company_id}_team_marketing`.
- `GET /api/companies/{company_id}/agents/{agent_id}` → `{ agent: {...}, runs:[...] }`
  - agent has `role` ∈ {ceo, hr, cfo, cto, coo, cho, lead, worker, qa}, `name`, `model_id`, `avatar_uri`, `state` ∈ {idle, working, paused, retired}, `home_room_id`, `home_desk_id`, `token_spend`.
  - `avatar_uri` is `/api/companies/{company_id}/avatars/{agent_id}.png`.
- `GET /api/companies/{company_id}/avatars/{agent_id}.png` → image/png

## Models
- `GET /api/models` → `{ "free":[...], "fast":[...], "reasoning":[...], "frontier":[...], "_source":"live"|"mock" }`
  - each model: `{ id, owned_by, tier, context, pricing }`
  - mock fallback includes `mimo-v2.5-pro` in reasoning.
- `PUT /api/agents/{agent_id}/model?company_id=...` body `{ model_id }` → `{ agent: {...} }` (404 if agent not in that company)

## Events (SSE)
- `GET /api/events?company_id=...` → `text/event-stream`
  - events: `event: <event_type>` / `data: <json>` / `id: <event_id>`
  - `heartbeat` every ~25s. Subscribers only receive their own company's events.

## Actions
- `POST /api/actions` body:
  ```json
  { "company_id": "...", "action": "...", "target_type": "...", "target_id": "...", "payload": {} }
  ```
  - `approve` / `reject` (target_type=approval, target_id=approval id)
  - `pause` / `resume` / `stop` (target_type=agent, target_id=agent id)
  - `advance_task` (target_type=task, target_id=task id) — walks a task one stage forward; produces an artifact in REVIEW, QA passes it, DONE unblocks next stage
  - `request_hire` (payload: team_id, role?, reason?, budget_usd?) → creates PENDING approval
  - `execute_hire` (payload: approval_id, agent_id, name, role, team_id, room_id, model_id?) → HR creates worker after approval
  - Returns `{ "ok": true, "result": {...} }`

## Task statuses
`BACKLOG → READY → IN_PROGRESS → REVIEW → AWAITING_APPROVAL → DONE` (+ `BLOCKED`).
Default WIP = 3 IN_PROGRESS per team; over-capacity does not spawn workers.
