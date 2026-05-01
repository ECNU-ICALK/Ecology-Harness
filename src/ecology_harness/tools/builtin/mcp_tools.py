from __future__ import annotations

from ecology_harness.tools.base import ToolContext, ToolDefinition, ToolError, ToolResult
from ecology_harness.tools.registry import ToolRegistry


def register_mcp_tools(registry: ToolRegistry) -> None:
    registry.register(
        ToolDefinition(
            name="ListMcpServersTool",
            description="List configured MCP servers and their connection state.",
            input_schema={
                "type": "object",
                "properties": {
                    "probe": {"type": "boolean"},
                    "timeout_sec": {"type": "integer"},
                },
            },
            handler=_list_mcp_servers,
            read_only=True,
            concurrent_safe=True,
            source="mcp",
        )
    )
    registry.register(
        ToolDefinition(
            name="ProbeMcpServerTool",
            description="Probe one MCP server to see whether its configured transport looks reachable.",
            input_schema={
                "type": "object",
                "properties": {
                    "server": {"type": "string"},
                    "timeout_sec": {"type": "integer"},
                },
                "required": ["server"],
            },
            handler=_probe_mcp_server,
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
    registry.register(
        ToolDefinition(
            name="McpSearchTool",
            description="Rewrite a task query with context and rank relevant MCP servers for the request.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer"},
                },
                "required": ["query"],
            },
            handler=_mcp_search,
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
    probe = bool(params.get("probe", False))
    timeout_sec = max(int(params.get("timeout_sec", 3) or 3), 1)
    states = [item.to_dict() for item in _manager(context).list_server_states(probe_remote=probe, timeout_sec=timeout_sec)]
    if not states:
        return ToolResult(content="No MCP servers configured.", data={"servers": []})
    lines = [
        "%(server_name)s\t%(transport)s\t%(status)s\tenabled=%(enabled)s\ttools=%(tool_count)s\tresources=%(resource_count)s"
        % item
        for item in states
    ]
    return ToolResult(content="\n".join(lines), data={"servers": states})


def _probe_mcp_server(params: dict, context: ToolContext) -> ToolResult:
    timeout_sec = max(int(params.get("timeout_sec", 3) or 3), 1)
    state = _manager(context).probe_server(params["server"], timeout_sec=timeout_sec)
    content = "%(server_name)s\t%(transport)s\t%(status)s" % state
    if state.get("error_message"):
        content += "\t" + str(state["error_message"])
    return ToolResult(content=content, data=state)


def _list_mcp_tools(params: dict, context: ToolContext) -> ToolResult:
    rows = _manager(context).list_tools(params.get("server", ""))
    if not rows:
        return ToolResult(content="No MCP tools available.", data={"tools": []})
    lines = [
        "%(server)s\t%(tool)s\t%(bridge_name)s\t%(transport)s\truntime=%(runtime_invokable)s" % item
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


def _mcp_search(params: dict, context: ToolContext) -> ToolResult:
    limit = params.get("limit")
    if limit is None:
        settings = context.services.get("settings") or context.settings
        limit = getattr(settings, "mcp_search_default_k", 6)
    report = _manager(context).search(
        params["query"],
        conversation=context.services.get("conversation"),
        limit=max(int(limit), 1),
        enabled_only=False,
    )
    if not report.hits:
        return ToolResult(
            content="No relevant MCP servers found for: %s" % params["query"],
            data=report.to_dict(),
        )
    lines = []
    for item in report.hits:
        suffix = ""
        if item.matched_tools:
            suffix = " matched_tools=" + ", ".join(item.matched_tools[:4])
        lines.append(
            "%s\t%.3f\t%s%s"
            % (item.server.name, item.score, item.server.description, suffix)
        )
    header = "Rewritten query: %s" % report.rewrite.rewritten_query
    return ToolResult(content=header + "\n" + "\n".join(lines), data=report.to_dict())
