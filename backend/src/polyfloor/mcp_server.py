"""MCP server — standards-compliant Model Context Protocol server for Polyfloor.

Uses the official Python MCP SDK to expose scoped, safe tools:
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

import httpx

from .config import get_settings


def _get_api_base() -> str:
    """Get the Polyfloor API base URL."""
    settings = get_settings()
    return f"http://{settings.host}:{settings.port}"


def _get_api_token() -> str | None:
    """Get the API token from settings."""
    settings = get_settings()
    return settings.security.get_api_token()


async def _api_request(method: str, path: str, **kwargs) -> dict:
    """Make an authenticated request to the Polyfloor API."""
    token = _get_api_token()
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient() as client:
        resp = await client.request(
            method,
            f"{_get_api_base()}{path}",
            headers=headers,
            **kwargs,
        )
        resp.raise_for_status()
        return resp.json()


async def run_mcp_server():
    """Run the Polyfloor MCP server using the official MCP SDK."""
    try:
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
        from mcp.types import TextContent, Tool
    except ImportError:
        print("MCP server requires the 'mcp' package. Install with: pip install 'polyfloor[mcp]'")
        return

    server = Server("polyfloor")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="create_task",
                description="Create a new task on a floor",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "floor_id": {"type": "string", "description": "Target floor ID"},
                        "title": {"type": "string", "description": "Task title"},
                        "description": {
                            "type": "string",
                            "description": "Task description",
                            "default": "",
                        },
                        "assigned_role": {"type": "string", "description": "Role to assign"},
                        "priority": {
                            "type": "integer",
                            "description": "Task priority (0=normal)",
                            "default": 0,
                        },
                    },
                    "required": ["floor_id", "title"],
                },
            ),
            Tool(
                name="list_tasks",
                description="List tasks for a floor, optionally filtered by status",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "floor_id": {"type": "string", "description": "Floor ID to filter by"},
                        "status": {"type": "string", "description": "Status to filter by"},
                    },
                },
            ),
            Tool(
                name="get_sprint_status",
                description="Get current sprint status for a floor",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "floor_id": {"type": "string", "description": "Floor ID"},
                    },
                    "required": ["floor_id"],
                },
            ),
            Tool(
                name="list_approvals",
                description="List pending approvals, optionally filtered by floor",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "floor_id": {"type": "string", "description": "Floor ID to filter by"},
                    },
                },
            ),
            Tool(
                name="request_approval",
                description="Request human approval for an action",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "floor_id": {"type": "string", "description": "Floor ID"},
                        "approval_type": {
                            "type": "string",
                            "description": "Type of approval needed",
                        },
                        "description": {"type": "string", "description": "What needs approval"},
                        "payload": {
                            "type": "object",
                            "description": "Approval payload",
                            "default": {},
                        },
                    },
                    "required": ["floor_id", "approval_type", "description"],
                },
            ),
            Tool(
                name="floor_status",
                description="Get floor configuration and status",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "floor_id": {"type": "string", "description": "Floor ID"},
                    },
                    "required": ["floor_id"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        try:
            if name == "create_task":
                result = await _api_request(
                    "POST",
                    "/api/v1/tasks",
                    json={
                        "floor_id": arguments["floor_id"],
                        "title": arguments["title"],
                        "description": arguments.get("description", ""),
                        "assigned_role": arguments.get("assigned_role"),
                        "priority": arguments.get("priority", 0),
                    },
                )
            elif name == "list_tasks":
                params = {}
                if "floor_id" in arguments:
                    params["floor_id"] = arguments["floor_id"]
                if "status" in arguments:
                    params["status"] = arguments["status"]
                result = await _api_request("GET", "/api/v1/tasks", params=params)
            elif name == "get_sprint_status":
                result = await _api_request(
                    "GET", f"/api/v1/floors/{arguments['floor_id']}/sprints"
                )
            elif name == "list_approvals":
                params = {}
                if "floor_id" in arguments:
                    params["floor_id"] = arguments["floor_id"]
                params["status"] = "pending"
                result = await _api_request("GET", "/api/v1/approvals", params=params)
            elif name == "request_approval":
                result = await _api_request(
                    "POST",
                    "/api/v1/approvals",
                    json={
                        "floor_id": arguments["floor_id"],
                        "approval_type": arguments["approval_type"],
                        "description": arguments["description"],
                        "payload": arguments.get("payload", {}),
                        "requested_by": "mcp-client",
                    },
                )
            elif name == "floor_status":
                result = await _api_request("GET", f"/api/v1/floors/{arguments['floor_id']}")
            else:
                result = {"error": f"Unknown tool: {name}"}

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except httpx.HTTPStatusError as e:
            return [
                TextContent(
                    type="text", text=f"API error: {e.response.status_code} - {e.response.text}"
                )
            ]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    # Run the server on stdio (standard MCP transport)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def cli():
    """CLI entry point for the MCP server."""
    asyncio.run(run_mcp_server())


if __name__ == "__main__":
    cli()
