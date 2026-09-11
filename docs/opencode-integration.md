# Integration

> **Status:** The primary integration surface for Polyfloor is the **REST API +
> SSE**. A standalone MCP server is **not** part of the MVP backend; it is a
> future item. This document describes what exists today.

## REST API (primary)

Polyfloor exposes a company-scoped REST API. Every company-scoped endpoint
requires `company_id` via query param or `X-Company-Id` header. See the frozen
[`API_CONTRACT.md`](./API_CONTRACT.md) for the full contract. Highlights:

- `GET /healthz`, `GET /metrics` — observability.
- `GET /api/companies`, `POST /api/companies` — company directory + creation
  (materializes the tenant).
- `GET /api/companies/{company_id}/state` — full snapshot.
- `GET /api/companies/{company_id}/rooms/{room_id}`,
  `GET /api/companies/{company_id}/agents/{agent_id}` — rooms, desks, agents.
- `GET /api/models`, `PUT /api/agents/{agent_id}/model` — model router.
- `GET /api/events?company_id=...` — SSE state deltas (per-company, heartbeat).
- `POST /api/actions` — `approve`/`reject`, `pause`/`resume`/`stop`,
  `advance_task`, `request_hire`, `execute_hire`.

## SSE

`GET /api/events?company_id=...` returns `text/event-stream`. Subscribers only
receive their own company's events; a heartbeat fires every ~25s. Use this for
live UI updates instead of polling.

## Authentication

Optional platform bearer token via `POLYFLOOR_API_TOKEN_FILE`. When unset, the
API is open in dev. In production, front it with a reverse proxy and set the
token file via sops.

## Agent execution

The MVP agent loop is **mocked** (`backend/src/polyfloor/agents/executor.py`):
advancing a task emits a deterministic artifact and walks the pipeline one
stage. This keeps the research → spec → draft → QA → marketing path
demonstrable without live model calls. A live OpenAI-compatible loop against
the router is the follow-up. Agents never automatically publish, spend money,
or run arbitrary commands — every external side effect goes through an approval
gate.

## MCP server (future)

A standards-compliant MCP server exposing the above as tool calls is planned
but not yet implemented. When added, it will bind to loopback (stdio transport)
and require the same token authentication as the REST API; it will not have raw
database or secret access.
