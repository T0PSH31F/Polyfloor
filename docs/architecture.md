# Polyfloor Architecture

## Overview

Polyfloor is an autonomous multi-company enterprise engine. A **company is the
tenant**: each company owns its agents, teams, boards, artifacts, memory,
budgets, credentials, and channels, fully isolated from every other company on
the same instance. A **floor** is a visual/layout container only — never the
security or data boundary. `company_id` is the boundary.

See [`../SPEC_POLYFLOOR.md`](../SPEC_POLYFLOOR.md) §1–4 (canonical) and
[`API_CONTRACT.md`](./API_CONTRACT.md) (frozen).

## Stack

- **Backend:** FastAPI + SQLite WAL (default; PostgreSQL optional), structured
  JSON logs, Prometheus `/metrics`, OpenAI-compatible model router.
- **Frontend:** SvelteKit + TypeScript + HTML5 2D Canvas (no WebGL/Three.js).
- **Packaging:** Nix `flake-parts`; `nixosModules.default` for a hardened
  systemd service.

## Static vs Runtime Configuration

| Layer                | Managed By              | Examples                                                                                            |
| -------------------- | ----------------------- | --------------------------------------------------------------------------------------------------- |
| **Static (Nix)**     | `nixos-rebuild switch`  | Service enablement, host/port, `dataDir`, `routerEndpoint`, `defaultHrModel`, firewall, persistence |
| **Runtime (DB/API)** | HR/admin agents via API | Companies, teams, agents, tasks, events, artifacts, approvals, model selection                      |

The static layer defines _how the service runs_. The runtime layer defines _what
work happens_, scoped per `company_id`. Agents modify runtime state without
NixOS rebuilds.

## Data Flow

```
User/Agent → FastAPI (company_id-scoped) → SQLite WAL (company_id on every row)
                ↓
          Event Bus → SSE → Frontend (SvelteKit + Canvas)
```

Every request, event, task, artifact, trace, and secret lookup requires
`company_id`. A missing company id is a bug, not a default.

## Work Systems (SPEC §6)

Four systems, never collapsed into one chat log:

1. **Append-only event log** — audit trail (requests, decisions, errors,
   staffing, policy).
1. **Kanban / task DAG** — execution: owner, status, criteria, budget, retries.
1. **Artifact registry** — what was produced: URI, hash, lineage, review status.
1. **Approval queue** — human/CEO gates: spend, hire, publish, irreversible I/O.

Task lifecycle:
`BACKLOG → READY → IN_PROGRESS → REVIEW → AWAITING_APPROVAL → DONE` (+ `BLOCKED`).

## Isolation

`company_id` is on every record; queries and writes filter by it. An agent
belongs to exactly one company. Per-company workspaces live under
`dataDir/companies/<company_id>/`. Agents request **capabilities**; the platform
resolves the company-scoped secret after policy checks. See
[`security.md`](./security.md) and SPEC §4.

## Persistence

Static config lives in Nix modules. Runtime state persists in SQLite (default)
or PostgreSQL. Per-company outputs persist under
`dataDir/companies/<company_id>/`. Impermanence integration is optional and
controlled by the host NixOS configuration.
