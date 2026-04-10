from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import shutil
from typing import Any
from urllib import error, request

from ecology_harness.claw_compat import CLAW_SKILL_SPECS, list_claw_tools, search_claw_tools
from ecology_harness.mcp.retrieval import McpBM25Retriever, McpSearchHit, McpSearchReport
from ecology_harness.runtime.messages import ChatMessage
from ecology_harness.tools import ToolDefinition, ToolError, ToolResult


def normalize_name_for_mcp(name: str) -> str:
    chars = []
    for ch in name:
        if ch.isalnum() or ch in {"_", "-"}:
            chars.append(ch)
        else:
            chars.append("_")
    return "".join(chars)


def mcp_tool_prefix(server_name: str) -> str:
    return "mcp__%s__" % normalize_name_for_mcp(server_name)


def mcp_tool_name(server_name: str, tool_name: str) -> str:
    return "%s%s" % (mcp_tool_prefix(server_name), normalize_name_for_mcp(tool_name))


@dataclass
class McpTool:
    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=lambda: {"type": "object", "properties": {}})
    handler: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "handler": self.handler,
        }


@dataclass
class McpResource:
    uri: str
    name: str
    description: str = ""
    mime_type: str = "text/plain"
    handler: str = ""
    content: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
            "mime_type": self.mime_type,
            "handler": self.handler,
        }


@dataclass
class McpServerConfig:
    name: str
    transport: str
    description: str
    source: str
    root: Path
    default_enabled: bool = True
    command: str = ""
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    url: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    auth: str = "none"
    tools: list[McpTool] = field(default_factory=list)
    resources: list[McpResource] = field(default_factory=list)

    @property
    def tool_prefix(self) -> str:
        return mcp_tool_prefix(self.name)

    def to_index_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "transport": self.transport,
            "description": self.description,
            "source": self.source,
            "default_enabled": self.default_enabled,
            "tool_prefix": self.tool_prefix,
            "tool_count": len(self.tools),
            "resource_count": len(self.resources),
            "auth": self.auth,
        }


@dataclass
class McpServerState:
    server_name: str
    status: str
    transport: str
    description: str
    enabled: bool
    tool_count: int
    resource_count: int
    auth: str
    error_message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "server_name": self.server_name,
            "status": self.status,
            "transport": self.transport,
            "description": self.description,
            "enabled": self.enabled,
            "tool_count": self.tool_count,
            "resource_count": self.resource_count,
            "auth": self.auth,
            "error_message": self.error_message,
        }


class McpServerRegistry:
    def __init__(
        self,
        app: Any,
        builtin_dir: Path,
        user_dir: Path,
        project_dir: Path,
        history_turns: int = 4,
    ) -> None:
        self.app = app
        self.builtin_dir = builtin_dir
        self.user_dir = user_dir
        self.project_dir = project_dir
        self.history_turns = history_turns
        self.user_dir.mkdir(parents=True, exist_ok=True)
        self.project_dir.mkdir(parents=True, exist_ok=True)

    def list_servers(self) -> list[McpServerConfig]:
        seen: dict[str, McpServerConfig] = {}
        for source, root in (
            ("builtin", self.builtin_dir),
            ("user", self.user_dir),
            ("project", self.project_dir),
        ):
            if not root.exists():
                continue
            for config_path in sorted(root.rglob("*.json")):
                for server in self._load_config_file(config_path, source):
                    seen[server.name] = server
        return sorted(seen.values(), key=lambda item: item.name.lower())

    def list_server_states(
        self,
        *,
        probe_remote: bool = False,
        timeout_sec: int = 3,
    ) -> list[McpServerState]:
        states = []
        for server in self.list_servers():
            states.append(self._state_for_server(server, probe_remote=probe_remote, timeout_sec=timeout_sec))
        return states

    def get_server(self, name: str) -> McpServerConfig | None:
        needle = (name or "").strip().lower()
        for server in self.list_servers():
            if server.name.lower() == needle:
                return server
        return None

    def probe_server(self, name: str, timeout_sec: int = 3) -> dict[str, Any]:
        server = self.get_server(name)
        if server is None:
            raise ToolError("Unknown MCP server: %s" % name)
        state = self._state_for_server(server, probe_remote=True, timeout_sec=timeout_sec)
        return state.to_dict()

    def list_tools(self, server_name: str = "") -> list[dict[str, Any]]:
        servers = self.list_servers()
        rows = []
        for server in servers:
            if server_name and server.name != server_name:
                continue
            for tool in server.tools:
                rows.append(
                    {
                        "server": server.name,
                        "tool": tool.name,
                        "description": tool.description,
                        "bridge_name": mcp_tool_name(server.name, tool.name),
                        "transport": server.transport,
                    }
                )
        return rows

    def search(
        self,
        query: str,
        conversation: list[ChatMessage] | None = None,
        limit: int = 6,
        enabled_only: bool = False,
    ) -> McpSearchReport:
        servers = self.list_servers()
        if enabled_only:
            servers = [item for item in servers if item.default_enabled]
        retriever = McpBM25Retriever(servers, history_turns=self.history_turns)
        return retriever.search(query, conversation=conversation, limit=limit)

    def select_for_prompt(
        self,
        query: str,
        conversation: list[ChatMessage] | None = None,
        limit: int = 6,
    ) -> McpSearchReport:
        report = self.search(
            query=query,
            conversation=conversation,
            limit=limit,
            enabled_only=False,
        )
        if report.hits or not limit:
            return report
        fallback_servers = self.list_servers()[:limit]
        report.hits = [
            McpSearchHit(
                server=item,
                score=0.0,
                matched_terms=[],
                matched_tools=[],
                matched_resources=[],
                exact_match=False,
            )
            for item in fallback_servers
        ]
        report.fallback_used = True
        return report

    def relevant_dynamic_tool_names(
        self,
        query: str,
        conversation: list[ChatMessage] | None = None,
        limit: int = 6,
    ) -> set[str]:
        report = self.select_for_prompt(query=query, conversation=conversation, limit=limit)
        names: set[str] = set()
        query_text = report.rewrite.rewritten_query.lower()
        for hit in report.hits:
            for tool in hit.server.tools:
                bridge_name = mcp_tool_name(hit.server.name, tool.name)
                if bridge_name.lower() in query_text or tool.name.lower() in query_text:
                    names.add(bridge_name)
                elif hit.matched_tools:
                    names.add(bridge_name)
                else:
                    names.add(bridge_name)
        return names

    def prompt_index_from_hits(self, hits: list[McpSearchHit]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for hit in hits:
            item = self._state_for_server(hit.server).to_dict()
            item["score"] = round(hit.score, 4)
            item["matched_tools"] = hit.matched_tools
            item["matched_resources"] = hit.matched_resources
            item["matched_tools_text"] = (
                " matched_tools=" + ", ".join(hit.matched_tools[:4]) if hit.matched_tools else ""
            )
            item["matched_resources_text"] = (
                " matched_resources=" + ", ".join(hit.matched_resources[:3])
                if hit.matched_resources
                else ""
            )
            item["tool_prefix"] = hit.server.tool_prefix
            rows.append(item)
        return rows

    def list_resources(self, server_name: str) -> list[dict[str, Any]]:
        server = self.get_server(server_name)
        if server is None:
            raise ToolError("Unknown MCP server: %s" % server_name)
        return [item.to_dict() for item in server.resources]

    def read_resource(
        self,
        server_name: str,
        uri: str,
        services: dict[str, Any] | None = None,
    ) -> ToolResult:
        server = self.get_server(server_name)
        if server is None:
            raise ToolError("Unknown MCP server: %s" % server_name)
        for resource in server.resources:
            if resource.uri != uri:
                continue
            if server.transport != "inprocess":
                state = self._state_for_server(server, probe_remote=True)
                raise ToolError(
                    "MCP server `%s` is configured with transport `%s`; direct resource execution is not implemented in this build. Current status=%s%s"
                    % (
                        server.name,
                        server.transport,
                        state.status,
                        (", detail=%s" % state.error_message) if state.error_message else "",
                    )
                )
            return self._read_inprocess_resource(server, resource, services or {})
        raise ToolError("MCP resource not found: %s" % uri)

    def call_tool(
        self,
        server_name: str,
        tool_name: str,
        params: dict[str, Any],
        services: dict[str, Any] | None = None,
    ) -> ToolResult:
        server = self.get_server(server_name)
        if server is None:
            raise ToolError("Unknown MCP server: %s" % server_name)
        for tool in server.tools:
            if tool.name != tool_name:
                continue
            if server.transport != "inprocess":
                state = self._state_for_server(server, probe_remote=True)
                raise ToolError(
                    "MCP server `%s` uses transport `%s`; direct remote tool execution is not implemented yet. Current status=%s%s"
                    % (
                        server.name,
                        server.transport,
                        state.status,
                        (", detail=%s" % state.error_message) if state.error_message else "",
                    )
                )
            return self._call_inprocess_tool(server, tool, params, services or {})
        raise ToolError("Unknown MCP tool `%s` on server `%s`." % (tool_name, server_name))

    def register_dynamic_tools(self, registry) -> None:
        for server in self.list_servers():
            if not server.default_enabled:
                continue
            for tool in server.tools:
                registry.register(
                    ToolDefinition(
                        name=mcp_tool_name(server.name, tool.name),
                        description="[MCP:%s] %s" % (server.name, tool.description),
                        input_schema=tool.input_schema,
                        handler=self._make_bridge_handler(server.name, tool.name),
                        read_only=False,
                        concurrent_safe=False,
                        source="mcp",
                        origin=server.name,
                    )
                )

    def _make_bridge_handler(self, server_name: str, tool_name: str):
        def _handler(params, context):
            return self.call_tool(server_name, tool_name, params, services=context.services)

        return _handler

    def _state_for_server(
        self,
        server: McpServerConfig,
        *,
        probe_remote: bool = False,
        timeout_sec: int = 3,
    ) -> McpServerState:
        enabled = bool(server.default_enabled)
        if server.transport == "inprocess" and enabled:
            status = "connected"
        elif server.transport == "inprocess":
            status = "installed"
        elif probe_remote and enabled:
            probe = self._probe_remote_server(server, timeout_sec=timeout_sec)
            status = probe["status"]
        elif enabled:
            status = "configured"
        else:
            status = "cataloged"
        return McpServerState(
            server_name=server.name,
            status=status,
            transport=server.transport,
            description=server.description,
            enabled=enabled,
            tool_count=len(server.tools),
            resource_count=len(server.resources),
            auth=server.auth,
            error_message=probe["error_message"] if probe_remote and enabled and server.transport != "inprocess" else "",
        )

    def _probe_remote_server(self, server: McpServerConfig, timeout_sec: int = 3) -> dict[str, str]:
        transport = (server.transport or "").strip().lower()
        if transport == "stdio":
            command = server.command.strip()
            if not command:
                return {"status": "missing-command", "error_message": "No stdio command configured."}
            executable = shutil.which(command) if not Path(command).is_absolute() else command
            if executable and (not Path(command).is_absolute() or Path(command).exists()):
                return {"status": "reachable", "error_message": ""}
            return {"status": "unreachable", "error_message": "Command not found: %s" % command}
        if transport in {"http", "sse"}:
            if not server.url.strip():
                return {"status": "missing-url", "error_message": "No URL configured."}
            req = request.Request(server.url, headers=server.headers or {}, method="GET")
            try:
                with request.urlopen(req, timeout=timeout_sec) as response:
                    code = getattr(response, "status", 200) or 200
                return {"status": "reachable", "error_message": "HTTP %s" % code if code >= 300 else ""}
            except error.HTTPError as exc:
                if exc.code in {401, 403}:
                    return {"status": "auth-required", "error_message": "HTTP %s" % exc.code}
                if 400 <= exc.code < 500:
                    return {"status": "reachable", "error_message": "HTTP %s" % exc.code}
                return {"status": "unreachable", "error_message": "HTTP %s" % exc.code}
            except Exception as exc:
                return {"status": "unreachable", "error_message": str(exc)}
        return {"status": "configured", "error_message": ""}

    def _load_config_file(self, config_path: Path, source: str) -> list[McpServerConfig]:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and "servers" in raw:
            entries = raw["servers"]
        elif isinstance(raw, list):
            entries = raw
        else:
            entries = [raw]
        servers = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            tools = [
                McpTool(
                    name=str(item.get("name", "")),
                    description=str(item.get("description", "")),
                    input_schema=dict(item.get("input_schema", {"type": "object", "properties": {}})),
                    handler=str(item.get("handler", "")),
                )
                for item in entry.get("tools", []) or []
                if item.get("name")
            ]
            resources = [
                McpResource(
                    uri=str(item.get("uri", "")),
                    name=str(item.get("name", "")),
                    description=str(item.get("description", "")),
                    mime_type=str(item.get("mime_type", "text/plain")),
                    handler=str(item.get("handler", "")),
                    content=str(item.get("content", "")),
                )
                for item in entry.get("resources", []) or []
                if item.get("uri")
            ]
            default_enabled = entry.get("default_enabled")
            if default_enabled is None:
                default_enabled = entry.get("defaultEnabled")
            if default_enabled is None:
                default_enabled = source != "builtin"
            servers.append(
                McpServerConfig(
                    name=str(entry.get("name", config_path.stem)),
                    transport=str(entry.get("transport", "inprocess")),
                    description=str(entry.get("description", "")),
                    source=source,
                    root=config_path.parent,
                    default_enabled=bool(default_enabled),
                    command=str(entry.get("command", "")),
                    args=[str(item) for item in entry.get("args", []) or []],
                    env={str(key): str(value) for key, value in dict(entry.get("env", {})).items()},
                    url=str(entry.get("url", "")),
                    headers={str(key): str(value) for key, value in dict(entry.get("headers", {})).items()},
                    auth=str(entry.get("auth", "none")),
                    tools=tools,
                    resources=resources,
                )
            )
        return servers

    def _call_inprocess_tool(
        self,
        server: McpServerConfig,
        tool: McpTool,
        params: dict[str, Any],
        services: dict[str, Any],
    ) -> ToolResult:
        handler_name = tool.handler
        if handler_name == "list_claw_tools":
            rows = [item.to_dict() for item in list_claw_tools()]
            lines = [
                "%(name)s\t%(availability)s\t%(mapped_tool)s\t%(source_hint)s" % item for item in rows
            ]
            return ToolResult(content="\n".join(lines), data={"tools": rows})
        if handler_name == "find_claw_tools":
            query = str(params.get("query", ""))
            rows = [item.to_dict() for item in search_claw_tools(query)]
            lines = [
                "%(name)s\t%(availability)s\t%(mapped_tool)s\t%(source_hint)s" % item for item in rows
            ] or ["No claw-code compatibility tools matched."]
            return ToolResult(content="\n".join(lines), data={"query": query, "tools": rows})
        if handler_name == "list_claw_skills":
            skills = [
                item.to_index_dict()
                for item in services["app"].skill_loader.list_skills()
                if item.slug in {spec["slug"] for spec in CLAW_SKILL_SPECS}
            ]
            lines = ["%(slug)s\t%(description)s" % item for item in skills] or ["No claw-inspired skills available."]
            return ToolResult(content="\n".join(lines), data={"skills": skills})
        if handler_name == "list_claw_plugins":
            plugins = [item.to_index_dict() for item in services["app"].plugin_manager.list_plugins()]
            lines = ["%(slug)s\t%(source)s\t%(description)s" % item for item in plugins] or ["No plugins available."]
            return ToolResult(content="\n".join(lines), data={"plugins": plugins})
        raise ToolError("Unsupported in-process MCP handler: %s" % handler_name)

    def _read_inprocess_resource(
        self,
        server: McpServerConfig,
        resource: McpResource,
        services: dict[str, Any],
    ) -> ToolResult:
        del server
        if resource.handler == "resource_claw_tools":
            payload = [item.to_dict() for item in list_claw_tools()]
            content = json.dumps(payload, indent=2, ensure_ascii=False)
            return ToolResult(content=content, data={"uri": resource.uri, "mime_type": resource.mime_type})
        if resource.handler == "resource_claw_skills":
            payload = [
                item.to_index_dict()
                for item in services["app"].skill_loader.list_skills()
                if item.slug in {spec["slug"] for spec in CLAW_SKILL_SPECS}
            ]
            content = json.dumps(payload, indent=2, ensure_ascii=False)
            return ToolResult(content=content, data={"uri": resource.uri, "mime_type": resource.mime_type})
        if resource.handler == "resource_claw_plugins":
            payload = [item.to_index_dict() for item in services["app"].plugin_manager.list_plugins()]
            content = json.dumps(payload, indent=2, ensure_ascii=False)
            return ToolResult(content=content, data={"uri": resource.uri, "mime_type": resource.mime_type})
        return ToolResult(
            content=resource.content,
            data={"uri": resource.uri, "mime_type": resource.mime_type},
        )
