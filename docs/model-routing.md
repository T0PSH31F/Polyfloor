# Model Routing

## Design Philosophy

Free-first: use the best free models available through ExtremeRouter by default. Paid models are optional and require explicit opt-in at both the global and floor level.

## Routing Priority

1. **Local Hermes/Ollama** — `hermes:<model>` for local execution
2. **ExtremeRouter free models** — `free://best-reasoning`, `free://best-fast` (default)
3. **Paid models** — `paid://gpt-4o` (requires `POLYFLOOR_ALLOW_PAID_MODELS=true` AND floor `paid_models_allowed=true`)

## Logical Aliases

| Alias | Purpose | Default Resolution |
|-------|---------|-------------------|
| `free://best-reasoning` | Complex analysis, planning | Configurable via `POLYFLOOR_EXTREMEROUTER_REASONING_MODEL` |
| `free://best-fast` | Quick tasks, responses | Configurable via `POLYFLOOR_EXTREMEROUTER_FAST_MODEL` |
| `free://best-code` | Code generation | Configurable via `POLYFLOOR_EXTREMEROUTER_CODE_MODEL` |

Aliases are configurable — they map to model IDs via environment variables.

## Configuration

```bash
# ExtremeRouter
POLYFLOOR_EXTREMEROUTER_BASE_URL=https://router.extreme.ai/v1
POLYFLOOR_EXTREMEROUTER_API_KEY_FILE=/path/to/key
POLYFLOOR_EXTREMEROUTER_REASONING_MODEL=qwen-2.5-72b
POLYFLOOR_EXTREMEROUTER_FAST_MODEL=llama-3.1-8b

# Local Hermes
POLYFLOOR_HERMES_BASE_URL=http://127.0.0.1:11434/v1
POLYFLOOR_HERMES_MODEL=hermes3

# Policy
POLYFLOOR_ALLOW_PAID_MODELS=false
POLYFLOOR_PAID_DAILY_BUDGET_USD=0
```

## Per-Floor Configuration

Each floor can configure:
- Default model per role
- Whether paid models are allowed
- Daily budget cap

These are set via the API and stored in `tower.floor_configs` and `tower.roles`.

## Error Handling

If a paid model is requested but not allowed, the router raises a clear error explaining which gate failed (global or floor-level).
