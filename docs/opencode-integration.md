# OpenCode Integration

## MCP Server

Polyfloor exposes a standards-aligned MCP server for tool-calling agents.

### Available Tools

| Tool | Description | Scopes |
|------|-------------|--------|
| `create_task` | Create a new task on a floor | tasks:write |
| `list_tasks` | List tasks for a floor | tasks:read |
| `get_sprint_status` | Get current sprint status | sprints:read |
| `list_approvals` | List pending approvals | approvals:read |
| `request_approval` | Request human approval | approvals:create |
| `floor_status` | Get floor configuration | floors:read |

### Registration

Add to your OpenCode configuration:

```json
{
  "mcpServers": {
    "polyfloor": {
      "command": "python",
      "args": ["-m", "polyfloor.mcp_server"],
      "env": {
        "POLYFLOOR_API_TOKEN_FILE": "/path/to/token"
      }
    }
  }
}
```

### Security

- Requires the same token authentication as the REST API
- Binds to loopback only
- No raw database access
- No secret access
- No arbitrary file access
- No command execution

## REST API

The REST API is the primary integration surface. All MCP tools map to REST endpoints:

```
POST /api/v1/tasks           → create_task
GET  /api/v1/tasks           → list_tasks
GET  /api/v1/floors/{id}/sprints → get_sprint_status
GET  /api/v1/approvals       → list_approvals
POST /api/v1/approvals       → request_approval
GET  /api/v1/floors/{id}     → floor_status
```

## Agent Execution

Polyfloor supports pluggable agent executors:
- **NoopExecutor** — default, does nothing (testing)
- **CrewAIExecutor** — optional, requires `pip install 'polyfloor[agents]'`
- **OpenCodeExecutor** — disabled by default, explicit opt-in

Agents never automatically publish, spend money, or run arbitrary commands.
