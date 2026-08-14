"""MCP server — standards-aligned Model Context Protocol server for Polyfloor.

Exposes scoped, safe tools for OpenCode and other MCP clients:
- create_task
- list_tasks
- get_sprint_status
- list_approvals
- request_approval
- floor_status

Requires the same token authentication as the REST API.
Does NOT expose raw database access, secrets, arbitrary file access,
or generic command execution.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any, Optional


async def run_mcp_server(host: str = "127.0.0.1", port: int = 20128):
    """Run the Polyfloor MCP server.

    This is a placeholder implementation. A real MCP server would use the
    Python MCP SDK (from `mcp` package) to implement the protocol.

    For now, this documents the intended tool surface and can be enabled
    by installing with: pip install 'polyfloor[mcp]'
    """
    try:
        import mcp  # noqa: F401
    except ImportError:
        print("MCP server requires the 'mcp' package. Install with: pip install 'polyfloor[mcp]'")
        return

    # MCP tool definitions (for documentation and future implementation)
    TOOLS = {
        "create_task": {
            "description": "Create a new task on a floor",
            "parameters": {
                "floor_id": {"type": "string", "description": "Target floor ID"},
                "title": {"type": "string", "description": "Task title"},
                "description": {"type": "string", "description": "Task description", "default": ""},
                "assigned_role": {"type": "string", "description": "Role to assign", "default": None},
                "priority": {"type": "integer", "description": "Task priority (0=normal)", "default": 0},
            },
            "required_scopes": ["tasks:write"],
        },
        "list_tasks": {
            "description": "List tasks for a floor",
            "parameters": {
                "floor_id": {"type": "string", "description": "Floor ID to filter by", "default": None},
                "status": {"type": "string", "description": "Status to filter by", "default": None},
            },
            "required_scopes": ["tasks:read"],
        },
        "get_sprint_status": {
            "description": "Get current sprint status for a floor",
            "parameters": {
                "floor_id": {"type": "string", "description": "Floor ID"},
            },
            "required_scopes": ["sprints:read"],
        },
        "list_approvals": {
            "description": "List pending approvals",
            "parameters": {
                "floor_id": {"type": "string", "description": "Floor ID to filter by", "default": None},
            },
            "required_scopes": ["approvals:read"],
        },
        "request_approval": {
            "description": "Request human approval for an action",
            "parameters": {
                "floor_id": {"type": "string", "description": "Floor ID"},
                "approval_type": {"type": "string", "description": "Type of approval needed"},
                "description": {"type": "string", "description": "What needs approval"},
                "payload": {"type": "object", "description": "Approval payload", "default": {}},
            },
            "required_scopes": ["approvals:create"],
        },
        "floor_status": {
            "description": "Get floor configuration and status",
            "parameters": {
                "floor_id": {"type": "string", "description": "Floor ID"},
            },
            "required_scopes": ["floors:read"],
        },
    }

    print(f"Polyfloor MCP server would start on {host}:{port}")
    print(f"Available tools: {list(TOOLS.keys())}")
    print("This is a placeholder — implement with mcp SDK for production use.")


if __name__ == "__main__":
    asyncio.run(run_mcp_server())
