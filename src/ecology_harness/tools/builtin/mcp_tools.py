from __future__ import annotations

from ecology_harness.tools.base import ToolContext, ToolDefinition, ToolError, ToolResult
from ecology_harness.tools.registry import ToolRegistry


def register_mcp_tools(registry: ToolRegistry) -> None:
    registry.register(
        ToolDefinition(
            name="ListMcpServersTool",
            description="List configured MCP servers and their connection state.",
            input_schema={"type": "object", "properties": {}},
            handler=_list_mcp_servers,
            read_only=True,
            concurrent_safe=True,
            source="mcp",
        )
    )
    registry.register(
        ToolDefinition(
            name="ListMcpToolsTool",
            description="List MCP tools exposed by one server or by all configured servers.",
            input_schema={
                "type": "object",
                "properties": {"server": {"type": "string"}},
            },
            handler=_list_mcp_tools,
            read_only=True,
            concurrent_safe=True,
            source="mcp",
        )
    )
    registry.register(
        ToolDefinition(
            name="MCPTool",
            description="Call a specific tool exposed by an MCP server.",
            input_schema={
                "type": "object",
                "properties": {
                    "server": {"type": "string"},
                    "tool": {"type": "string"},
                    "arguments": {"type": "object"},
                },
                "required": ["server", "tool"],
            },
            handler=_mcp_call_tool,
            read_only=False,
            concurrent_safe=False,
            source="mcp",
        )
    )
    registry.register(
        ToolDefinition(
            name="ListMcpResourcesTool",
            description="List resources published by an MCP server.",
            input_schema={
                "type": "object",
                "properties": {"server": {"type": "string"}},
                "required": ["server"],
            },
            handler=_list_mcp_resources,
            read_only=True,
            concurrent_safe=True,
            source="mcp",
        )
    )
    registry.register(
        ToolDefinition(
            name="ReadMcpResourceTool",
            description="Read one resource from an MCP server.",
            input_schema={
                "type": "object",
                "properties": {
                    "server": {"type": "string"},
                    "uri": {"type": "string"},
                },
                "required": ["server", "uri"],
            },
            handler=_read_mcp_resource,
            read_only=True,
            concurrent_safe=True,
            source="mcp",
        )
    )
    registry.register(
        ToolDefinition(
            name="McpAuthTool",
            description="Inspect the declared authentication mode for one MCP server.",
            input_schema={
                "type": "object",
                "properties": {"server": {"type": "string"}},
                "required": ["server"],
            },
            handler=_mcp_auth,
            read_only=True,
            concurrent_safe=True,
            source="mcp",
        )
    )


def _manager(context: ToolContext):
    manager = context.services.get("mcp_registry")
    if manager is None:
        raise ToolError("mcp_registry service is unavailable.")
    return manager


def _list_mcp_servers(params: dict, context: ToolContext) -> ToolResult:
    del params
    states = [item.to_dict() for item in _manager(context).list_server_states()]
    if not states:
        return ToolResult(content="No MCP servers configured.", data={"servers": []})
    lines = [
        "%(server_name)s\t%(transport)s\t%(status)s\tenabled=%(enabled)s\ttools=%(tool_count)s\tresources=%(resource_count)s"
        % item
        for item in states
    ]
    return ToolResult(content="\n".join(lines), data={"servers": states})


def _list_mcp_tools(params: dict, context: ToolContext) -> ToolResult:
    rows = _manager(context).list_tools(params.get("server", ""))
    if not rows:
        return ToolResult(content="No MCP tools available.", data={"tools": []})
    lines = [
        "%(server)s\t%(tool)s\t%(bridge_name)s\t%(transport)s" % item
        for item in rows
    ]
    return ToolResult(content="\n".join(lines), data={"tools": rows})


def _mcp_call_tool(params: dict, context: ToolContext) -> ToolResult:
    return _manager(context).call_tool(
        params["server"],
        params["tool"],
        params.get("arguments", {}),
        services=context.services,
    )


def _list_mcp_resources(params: dict, context: ToolContext) -> ToolResult:
    resources = _manager(context).list_resources(params["server"])
    if not resources:
        return ToolResult(content="No MCP resources found.", data={"resources": []})
    lines = [
        "%(uri)s\t%(name)s\t%(mime_type)s" % item
        for item in resources
    ]
    return ToolResult(content="\n".join(lines), data={"resources": resources})


def _read_mcp_resource(params: dict, context: ToolContext) -> ToolResult:
    return _manager(context).read_resource(
        params["server"],
        params["uri"],
        services=context.services,
    )


def _mcp_auth(params: dict, context: ToolContext) -> ToolResult:
    server = _manager(context).get_server(params["server"])
    if server is None:
        raise ToolError("Unknown MCP server: %s" % params["server"])
    content = "server: %s\nauth: %s\ntransport: %s" % (
        server.name,
        server.auth,
        server.transport,
    )
    return ToolResult(
        content=content,
        data={
            "server": server.name,
            "auth": server.auth,
            "transport": server.transport,
        },
    )
