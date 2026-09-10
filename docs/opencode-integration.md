# OpenCode Integration

## MCP Server

Polyfloor exposes a standards-compliant MCP server for tool-calling agents.

### Available Tools

| Tool                | Description                  | Scopes           |
| ------------------- | ---------------------------- | ---------------- |
| `create_task`       | Create a new task on a floor | tasks:write      |
| `list_tasks`        | List tasks for a floor       | tasks:read       |
| `get_sprint_status` | Get current sprint status    | sprints:read     |
| `list_approvals`    | List pending approvals       | approvals:read   |
| `request_approval`  | Request human approval       | approvals:create |
| `floor_status`      | Get floor configuration      | floors:read      |

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

Or using the polyfloor CLI:

```json
{
  "mcpServers": {
    "polyfloor": {
      "command": "polyfloor-mcp",
      "args": [],
      "env": {
        "POLYFLOOR_API_TOKEN_FILE": "/path/to/token"
      }
    }
  }
}
```

### Security

- Requires the same token authentication as the REST API
- Binds to loopback only (stdio transport)
- No raw database access
- No secret access
- No arbitrary file access
- No command execution

### Smoke Test

Verify the MCP server starts and lists tools:

```bash
# Install with MCP support
pip install 'polyfloor[mcp]'

# Test tool listing
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python -m polyfloor.mcp_server
```

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
