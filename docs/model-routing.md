# Model Routing

## Design

Polyfloor talks to any **OpenAI-compatible** router: Kong, Extreme Router,
LiteLLM, or a raw OpenAI gateway. The router must expose:

- `GET {routerEndpoint}/models` — model discovery (Polyfloor calls this).
- `POST {routerEndpoint}/chat/completions` — agent inference.

Polyfloor never hardcodes the catalog in the UI; it always enumerates the live
router.

## Configuration

| Setting          | Env var                         | Default                    | Notes                                                                 |
| ---------------- | ------------------------------- | -------------------------- | --------------------------------------------------------------------- |
| Router base URL  | `POLYFLOOR_ROUTER_ENDPOINT`     | `http://127.0.0.1:4000/v1` | Must end in `/v1`. Set via `services.polyfloor.routerEndpoint`.       |
| Router API key   | `POLYFLOOR_ROUTER_API_KEY_FILE` | _(none)_                   | Path to a file containing the key. Never the raw value; never logged. |
| Default HR model | `POLYFLOOR_DEFAULT_HR_MODEL`    | `mimo-v2.5-pro`            | Xiaomi MiMo-V2.5 Pro. Set via `services.polyfloor.defaultHrModel`.    |

Workers default to the free/fast pool models; the HR coordinator uses
`defaultHrModel`.

## API surface

- `GET /api/models` — enumerates the router's models, groups them as
  `free`, `fast`, `reasoning`, `frontier`, and returns
  `{ id, owned_by, tier, context, pricing }` per model plus a `_source` of
  `live` or `mock`. When the router is unreachable, a mock fallback catalog
  (including `mimo-v2.5-pro`) is returned so the UI keeps working.
- `PUT /api/agents/{agent_id}/model?company_id=...` — change an agent's model at
  runtime, scoped to that company (404 if the agent is not in that company).

## Tiers

Polyfloor groups models into four tiers for the UI: `free`, `fast`,
`reasoning`, `frontier`. The HR orchestrator model defaults to
`mimo-v2.5-pro` (reasoning tier). Spend is tracked per company/team/model via
`agent_runs` (SPEC §9.5).

See [`API_CONTRACT.md`](./API_CONTRACT.md) and SPEC §9.2.
