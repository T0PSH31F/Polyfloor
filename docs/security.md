# Security

## Authentication

The API uses bearer token authentication. The token is read from a file specified by `POLYFLOOR_API_TOKEN_FILE`.

If no token file is configured, the API runs in development mode with full access.

## Authorization Roles

| Role | Scopes |
|------|--------|
| `human_admin` | All scopes |
| `hr` | floors:write, roles:write, tasks:write, approvals:resolve, config:write |
| `orchestrator` | tasks:write, approvals:create, sprints:write |
| `worker` | tasks:read, events:read |
| `readonly` | Read-only access |

## Floor Scoping

Principals can be scoped to specific floors. A scoped principal cannot access other floors' data.

## Output Path Security

The output service prevents:
- Path traversal (`..`)
- Absolute paths
- Symlink escapes
- Writing outside the floor's output root
- Files exceeding size limits (default 10MB)

## Approval Gate

All external side effects require human approval:
- Publishing content
- Sending emails
- Financial transactions
- Configuration changes

Agents cannot approve their own requests.

## CORS

CORS is explicit and configurable. No wildcard CORS in production.

## Loopback Binding

The backend binds to `127.0.0.1` by default. Use a reverse proxy (Caddy, nginx) for external access.

## Audit Trail

All state-changing operations are logged to `tower.events`. The events table is append-only — updates and deletes are prevented by database triggers.

## Secrets

- Never stored in source code
- Read from files at runtime
- Not printed in logs
- Managed via SOPS + age in production
