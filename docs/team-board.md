# Team Board (Task DAG)

## Task Lifecycle

```
BACKLOG → READY → IN_PROGRESS → REVIEW → AWAITING_APPROVAL → DONE
                         └──→ BLOCKED
```

### Status Descriptions

| Status | Meaning |
| --- | --- |
| `BACKLOG` | Not yet prioritized |
| `READY` | Ready for work, assigned to a team |
| `IN_PROGRESS` | Actively being worked on |
| `REVIEW` | Complete, in QA review |
| `AWAITING_APPROVAL` | Passed QA; awaiting a human/CEO gate (spend/publish) |
| `DONE` | Approved and delivered |
| `BLOCKED` | Stuck (dependency, policy, capacity) |

### Valid Transitions

| From | To |
| --- | --- |
| `BACKLOG` | `READY` |
| `READY` | `IN_PROGRESS`, `BLOCKED` |
| `IN_PROGRESS` | `REVIEW`, `BLOCKED` |
| `REVIEW` | `AWAITING_APPROVAL`, `IN_PROGRESS` (QA fail) |
| `AWAITING_APPROVAL` | `DONE`, `IN_PROGRESS` (rejected) |
| `BLOCKED` | `READY` |

Transitions are validated server-side.

## WIP Limits

Default WIP = **3** concurrent `IN_PROGRESS` tasks per team, configurable per
company/team. Over-capacity work stays `READY` or `BLOCKED` — it must **not**
auto-spawn workers. Covered by `test_wip`.

## Direct Production Line (digital-products)

```
R&D research artifact
  → Product lead accepts spec
    → Writing lead produces draft
      → QA panel evaluates
        → Marketing produces campaign assets
          → Publish agent requests external-release approval
```

Dependencies are explicit task edges, not ambient board reading. Every task has
exactly one owner, `company_id`, `team_id`, acceptance criteria, budget limit,
retry limit, artifact destination, and `trace_id`.

## API

Tasks are company-scoped (`company_id` via query param or `X-Company-Id` header).
See [`API_CONTRACT.md`](./API_CONTRACT.md):

- `POST /api/actions` with `action: "advance_task"` walks a task one stage
  forward, producing an artifact in `REVIEW`, QA pass, and `DONE` unblocks the
  next stage.
- `GET /api/companies/{company_id}/state` returns the full snapshot including
  `tasks`, `events`, `artifacts`, `approvals`, and `metrics`.
