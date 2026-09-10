# Team Board (Sprint Board)

## Task Lifecycle

```
backlog → queued → in_progress → staging → done
                                  → rejected
```

### Status Descriptions

| Status        | Meaning                            |
| ------------- | ---------------------------------- |
| `backlog`     | Not yet prioritized                |
| `queued`      | Ready for work, assigned to a role |
| `in_progress` | Actively being worked on           |
| `staging`     | Complete, awaiting review/approval |
| `done`        | Approved and delivered             |
| `rejected`    | Failed review, needs rework        |

### Valid Transitions

| From        | To                          |
| ----------- | --------------------------- |
| backlog     | queued                      |
| queued      | in_progress, backlog        |
| in_progress | staging, rejected, queued   |
| staging     | done, rejected, in_progress |
| rejected    | backlog, queued             |
| done        | backlog                     |

Transitions are validated server-side in both the API and database triggers.

## Approval Gates

Tasks in `staging` may require approval before moving to `done`:

- External publishing
- Financial transactions
- Configuration changes

## API

```bash
# Create task
POST /api/v1/tasks
{"floor_id": "production", "title": "Write blog post", "assigned_role": "writer"}

# Transition task
PATCH /api/v1/tasks/1
{"status": "in_progress"}

# List by status
GET /api/v1/tasks?floor_id=production&status=backlog
```
