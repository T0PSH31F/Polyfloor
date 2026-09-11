# Security

## Tenant isolation (the primary boundary)

`company_id` is the boundary. Every request, event, task, artifact, trace, and
secret lookup requires it — a missing company id is a bug, not a default.

- `company_id` is on every record; queries and writes filter by it.
- An agent belongs to exactly one company; two companies cannot see each other's
  data, memory, credentials, or spend.
- Per-company workspaces live under `dataDir/companies/<company_id>/`.
- Cross-company access returns nothing / 404 (covered by `test_isolation`).

Isolation tiers (SPEC §4): **Development** (shared process, strict `company_id`,
distinct workspace roots) and **Standard** (per-company queue, router key, memory
namespace, workspace, secrets) are implemented; a hardened **High-risk** tier
(per-company container, separate DB role) is designed for, not required for the
MVP.

## Authentication

The API uses an optional platform bearer token, read from a file specified by
`POLYFLOOR_API_TOKEN_FILE`. When no token file is configured, the API runs in
development mode with full access. In production, put a reverse proxy with auth
in front and set the token file via sops.

## Capability-based secrets

Agents never receive raw credentials. They request a **capability**
(`send_customer_email`, `publish_listing`). The platform resolves the
company-scoped secret after policy checks. Secret lookups are logged with
`company_id`, `agent_id`, and `trace_id`.

## Approval gates

All external side effects require human/CEO approval:

- Publishing content
- Sending emails / messages
- Financial transactions / spend
- Irreversible I/O

Agents create approval requests; humans resolve them via the API or frontend.
Agents cannot approve their own requests. Passing artifacts that spend money or
publish go to `AWAITING_APPROVAL` before a capability-gated action runs.

## Output path security

The avatar composer and artifact handlers prevent:

- Path traversal (`..`), absolute paths, symlink escapes
- Writing outside the company's workspace root
- Arbitrary user-supplied filenames or URLs

## CORS & binding

CORS is explicit and configurable (`POLYFLOOR_ALLOWED_ORIGINS`); no wildcard
CORS in production. The backend binds to `127.0.0.1` by default — use a reverse
proxy (Caddy, nginx) for remote access.

## Audit trail

State-changing operations are logged to the append-only `events` table with
`company_id`, `agent_id`, `task_id`, and `trace_id`. `agent_runs` records tokens
and USD per company/team/model.

## Secrets

- Never stored in source code.
- Read from **file paths** (`*_FILE`), never env vars or logs.
- Managed via sops + age in production (`services.polyfloor.environmentFile`).
