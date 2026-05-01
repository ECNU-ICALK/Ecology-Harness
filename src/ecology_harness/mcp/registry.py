from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
import subprocess
from pathlib import Path
import shutil
import sys
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
    runtime_invokable: bool
    bridge_registered: bool
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
            "runtime_invokable": self.runtime_invokable,
            "bridge_registered": self.bridge_registered,
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
                        "runtime_invokable": self._is_runtime_invokable(server),
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
                raise ToolError(self._runtime_unavailable_message(server, state, operation="resource"))
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
            if self._supports_local_compat(server):
                return self._call_local_compat_tool(server, tool, params, services or {})
            if server.transport != "inprocess":
                state = self._state_for_server(server, probe_remote=True)
                raise ToolError(self._runtime_unavailable_message(server, state, operation="tool"))
            return self._call_inprocess_tool(server, tool, params, services or {})
        raise ToolError("Unknown MCP tool `%s` on server `%s`." % (tool_name, server_name))

    def register_dynamic_tools(self, registry) -> None:
        for server in self.list_servers():
            if not server.default_enabled:
                continue
            if not self._is_runtime_invokable(server):
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
        probe: dict[str, str] | None = None
        if server.transport == "inprocess" and enabled:
            status = "connected"
        elif server.transport == "inprocess":
            status = "installed"
        elif probe_remote:
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
            runtime_invokable=self._is_runtime_invokable(server),
            bridge_registered=enabled and self._is_runtime_invokable(server),
            tool_count=len(server.tools),
            resource_count=len(server.resources),
            auth=server.auth,
            error_message=probe["error_message"] if probe and server.transport != "inprocess" else "",
        )

    @staticmethod
    def _is_runtime_invokable(server: McpServerConfig) -> bool:
        return server.transport == "inprocess" or McpServerRegistry._supports_local_compat(server)

    @staticmethod
    def _supports_local_compat(server: McpServerConfig) -> bool:
        return normalize_name_for_mcp(server.name) == "semantic-scholar"

    def _runtime_unavailable_message(
        self,
        server: McpServerConfig,
        state: McpServerState,
        *,
        operation: str,
    ) -> str:
        detail = "; detail=%s" % state.error_message if state.error_message else ""
        hint = self._runtime_unavailable_hint(server, state)
        noun = "resource" if operation == "resource" else "tool"
        return (
            "MCP server `%s` is cataloged with transport `%s`, but %s execution is not available in this build. "
            "status=%s, runtime_invokable=%s%s. %s"
            % (
                server.name,
                server.transport,
                noun,
                state.status,
                state.runtime_invokable,
                detail,
                hint,
            )
        )

    def _runtime_unavailable_hint(self, server: McpServerConfig, state: McpServerState) -> str:
        if state.status in {"missing-command", "missing-script", "missing-module"}:
            return (
                "Run `eh doctor --probe` or `eh tool ProbeMcpServerTool '{\"server\":\"%s\"}'` "
                "to inspect the missing runtime, then install the required command, script, or Python module."
                % server.name
            )
        if state.status in {"reachable", "configured", "cataloged"}:
            return (
                "Use this MCP entry for planning and discovery, or add a runtime adapter before calling it directly. "
                "For diagnostics run `eh tool ProbeMcpServerTool '{\"server\":\"%s\"}'`."
                % server.name
            )
        if server.auth != "none":
            return "Check the required auth configuration before enabling direct runtime calls."
        return "Use `ListMcpServersTool` with `probe=true` to inspect setup details."

    def _runtime_root(self) -> Path:
        override = os.environ.get("ECOLOGY_HARNESS_MCP_RUNTIME_ROOT", "").strip()
        if override:
            return Path(override).expanduser().resolve()
        settings = getattr(self.app, "settings", None)
        if settings is not None:
            return (settings.user_state_dir / "mcp_runtimes").resolve()
        return (Path.home() / ".ecology_harness" / "mcp_runtimes").resolve()

    @staticmethod
    def _normalize_executable(candidate: str) -> str:
        text = (candidate or "").strip()
        if not text:
            return ""
        path = Path(text)
        if path.is_absolute():
            return str(path) if path.exists() else ""
        resolved = shutil.which(text)
        return str(resolved or "")

    def _conda_env_python(self, env_name: str) -> str:
        env_key = "ECOLOGY_HARNESS_MCP_%s_PYTHON" % env_name.upper()
        override = self._normalize_executable(os.environ.get(env_key, ""))
        if override:
            return override
        candidate = Path.home() / "anaconda" / "envs" / env_name / "bin" / "python"
        return str(candidate) if candidate.exists() else ""

    def _find_existing_python(self, env_names: tuple[str, ...] = ("eh_py", "py310", "mcp311")) -> str:
        candidates = [
            *(self._conda_env_python(name) for name in env_names),
            self._normalize_executable(sys.executable),
            self._normalize_executable("python3"),
        ]
        for candidate in candidates:
            if candidate:
                return candidate
        return ""

    def _python_can_find_module(self, executable: str, module: str) -> bool:
        if not executable or not module:
            return False
        code = "import importlib.util,sys; sys.exit(0 if importlib.util.find_spec(%r) else 3)" % module
        try:
            completed = subprocess.run(
                [executable, "-c", code],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except Exception:
            return False
        return completed.returncode == 0

    def _find_python_with_module(self, module: str, env_names: tuple[str, ...]) -> str:
        for env_name in env_names:
            candidate = self._conda_env_python(env_name)
            if candidate and self._python_can_find_module(candidate, module):
                return candidate
        fallback = self._find_existing_python(env_names)
        if fallback and self._python_can_find_module(fallback, module):
            return fallback
        return ""

    def _preferred_uvx(self) -> str:
        override = self._normalize_executable(os.environ.get("ECOLOGY_HARNESS_MCP_UVX", ""))
        if override:
            return override
        for env_name in ("eh_py", "py310"):
            candidate = Path.home() / "anaconda" / "envs" / env_name / "bin" / "uvx"
            if candidate.exists():
                return str(candidate)
        return self._normalize_executable("uvx")

    def _preferred_node(self) -> str:
        override = self._normalize_executable(os.environ.get("ECOLOGY_HARNESS_MCP_NODE", ""))
        if override:
            return override
        nvm_node = Path.home() / ".nvm" / "versions" / "node" / "v20.19.6" / "bin" / "node"
        if nvm_node.exists():
            return str(nvm_node)
        return self._normalize_executable("node")

    def _resolved_stdio_command_and_args(self, server: McpServerConfig) -> tuple[str, list[str]]:
        command = (server.command or "").strip()
        args = list(server.args or [])
        server_name = normalize_name_for_mcp(server.name)
        runtime_root = self._runtime_root()

        if command == "uvx" or server_name in {
            "eosc-data-commons",
            "jupyter-mcp",
            "stac",
            "swiss-environment",
            "unit-converter",
            "wsl-envidat",
        }:
            command = self._preferred_uvx() or command

        if server_name == "gis-mcp":
            command = (
                self._normalize_executable(os.environ.get("ECOLOGY_HARNESS_MCP_GIS_COMMAND", ""))
                or self._normalize_executable(str(Path.home() / "anaconda" / "envs" / "ecologyharness-gis" / "bin" / "gis-mcp"))
                or self._normalize_executable(str(Path.home() / "anaconda" / "envs" / "mcpgis310" / "bin" / "gis-mcp"))
                or self._normalize_executable(str(Path.home() / "anaconda" / "envs" / "eh_py" / "bin" / "gis-mcp"))
                or self._normalize_executable(str(Path.home() / "anaconda" / "envs" / "py310" / "bin" / "gis-mcp"))
                or self._normalize_executable(command)
                or command
            )

        if command == "python":
            if server_name == "simple-pubmed":
                resolved = self._find_python_with_module("mcp_simple_pubmed", ("eh_py", "py310", "mcp311"))
                command = resolved or command
            elif server_name == "baidu-maps":
                resolved = self._find_python_with_module("mcp_server_baidu_maps", ("eh_py", "mcp311", "py310"))
                command = resolved or command
            elif server_name == "labarchives":
                resolved = self._find_python_with_module("labarchives_mcp", ("eh_py", "mcp311", "py310"))
                command = resolved or command
            elif server_name == "bio-blast":
                resolved_python = self._find_existing_python(("eh_py", "py310", "mcp311"))
                script_path = runtime_root / "bio-mcp-blast" / "src" / "server.py"
                if resolved_python and script_path.exists():
                    command = resolved_python
                    args = [str(script_path)]
                elif resolved_python:
                    command = resolved_python

        if command == "node":
            command = self._preferred_node() or command
            replacements = {
                "gbif": runtime_root / "gbif-mcp" / "build" / "index.js",
                "influxdb3": runtime_root / "influxdb3_mcp_server" / "build" / "index.js",
                "ncbi-datasets": runtime_root / "ncbi-datasets-server" / "build" / "index.js",
                "pubchem": runtime_root / "pubchem-server" / "build" / "index.js",
            }
            replacement = replacements.get(server_name)
            if replacement is not None and args:
                args = [str(replacement), *args[1:]]

        return command, args

    def _probe_remote_server(self, server: McpServerConfig, timeout_sec: int = 3) -> dict[str, str]:
        transport = (server.transport or "").strip().lower()
        if transport == "stdio":
            if self._supports_local_compat(server):
                return {"status": "reachable", "error_message": "local-compat"}
            command, args = self._resolved_stdio_command_and_args(server)
            command = command.strip()
            if not command:
                return {"status": "missing-command", "error_message": "No stdio command configured."}
            executable = shutil.which(command) if not Path(command).is_absolute() else command
            if executable and (not Path(command).is_absolute() or Path(command).exists()):
                entrypoint_probe = self._probe_stdio_entrypoint(
                    server,
                    executable=str(executable),
                    args=args,
                    timeout_sec=timeout_sec,
                )
                if entrypoint_probe is not None:
                    return entrypoint_probe
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

    def _probe_stdio_entrypoint(
        self,
        server: McpServerConfig,
        *,
        executable: str,
        args: list[str],
        timeout_sec: int,
    ) -> dict[str, str] | None:
        if not args:
            return None
        executable_name = Path(executable).name.lower()
        if executable_name.startswith("python"):
            return self._probe_python_stdio_entrypoint(server, executable=executable, args=args, timeout_sec=timeout_sec)
        if executable_name == "node":
            return self._probe_node_stdio_entrypoint(server, args=args)
        return None

    def _probe_python_stdio_entrypoint(
        self,
        server: McpServerConfig,
        *,
        executable: str,
        args: list[str],
        timeout_sec: int,
    ) -> dict[str, str] | None:
        if len(args) >= 2 and args[0] == "-m":
            module = args[1].strip()
            if not module:
                return {"status": "missing-module", "error_message": "Empty Python module name in stdio args."}
            if self._python_can_find_module(executable, module):
                return {"status": "reachable", "error_message": ""}
            return {"status": "missing-module", "error_message": "Python module not found: %s" % module}
        script = self._resolve_entrypoint_path(server, args[0])
        if script is None:
            return None
        if script.exists():
            return {"status": "reachable", "error_message": ""}
        return {"status": "missing-script", "error_message": "Script not found: %s" % args[0]}

    def _probe_node_stdio_entrypoint(
        self,
        server: McpServerConfig,
        *,
        args: list[str],
    ) -> dict[str, str] | None:
        script = self._resolve_entrypoint_path(server, args[0])
        if script is None:
            return None
        if script.exists():
            return {"status": "reachable", "error_message": ""}
        return {"status": "missing-script", "error_message": "Script not found: %s" % args[0]}

    @staticmethod
    def _resolve_entrypoint_path(server: McpServerConfig, value: str) -> Path | None:
        text = (value or "").strip()
        if not text or text.startswith("-"):
            return None
        looks_like_path = (
            "/" in text
            or "\\" in text
            or text.endswith(".py")
            or text.endswith(".js")
        )
        if not looks_like_path:
            return None
        path = Path(text)
        if path.is_absolute():
            return path
        return (server.root / path).resolve()

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

    def _call_local_compat_tool(
        self,
        server: McpServerConfig,
        tool: McpTool,
        params: dict[str, Any],
        services: dict[str, Any],
    ) -> ToolResult:
        if normalize_name_for_mcp(server.name) == "semantic-scholar":
            return self._call_semantic_scholar_tool(server, tool, params, services)
        raise ToolError("No local compatibility runtime is available for MCP server `%s`." % server.name)

    def _call_semantic_scholar_tool(
        self,
        server: McpServerConfig,
        tool: McpTool,
        params: dict[str, Any],
        services: dict[str, Any],
    ) -> ToolResult:
        workflow_name, argv = self._semantic_scholar_invocation(tool.name, params)
        script_path = self._semantic_scholar_script_path(workflow_name)
        if not script_path.is_file():
            raise ToolError(
                "Semantic Scholar compatibility workflow is not available for `%s` (missing %s)."
                % (tool.name, script_path)
            )
        env = self._semantic_scholar_env(server)
        timeout_sec = max(int(getattr(services.get("settings") or self.app.settings, "command_timeout_sec", 20) or 20), 1)
        try:
            python_executable = self._semantic_scholar_python()
            completed = subprocess.run(
                [python_executable, str(script_path), *argv],
                cwd=str(script_path.parent),
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                env=env,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ToolError("Semantic Scholar workflow timed out after %ss." % timeout_sec) from exc
        stdout = (completed.stdout or "").strip()
        stderr = (completed.stderr or "").strip()
        if not stdout:
            raise ToolError(
                "Semantic Scholar compatibility workflow produced no output%s."
                % (": %s" % stderr if stderr else "")
            )
        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise ToolError(
                "Semantic Scholar compatibility workflow returned invalid JSON%s."
                % (": %s" % stderr if stderr else "")
            ) from exc
        if payload.get("status") != "ok":
            error_payload = payload.get("error", {}) if isinstance(payload.get("error"), dict) else {}
            message = str(error_payload.get("message", "") or "Semantic Scholar workflow failed.")
            detail = str(error_payload.get("type", "") or "")
            if detail:
                message = "%s (%s)" % (message, detail)
            raise ToolError(message)
        content = self._format_semantic_scholar_result(
            requested_tool=tool.name,
            workflow_name=workflow_name,
            payload=payload,
        )
        return ToolResult(
            content=content,
            data={
                "server": server.name,
                "tool": tool.name,
                "workflow": workflow_name,
                "runtime": payload.get("runtime", {}),
                "arguments": payload.get("arguments", {}),
                "result": payload.get("result", {}),
                "compat_mode": "local-vendored-workflow",
            },
        )

    def _semantic_scholar_script_path(self, workflow_name: str) -> Path:
        skill_root = Path(__file__).resolve().parents[1] / "skills" / "builtin" / "ecology" / "semantic-scholar"
        return skill_root / workflow_name / "scripts" / "run.py"

    def _semantic_scholar_env(self, server: McpServerConfig) -> dict[str, str]:
        env = dict(os.environ)
        for key, value in server.env.items():
            if value.startswith("<") and value.endswith(">"):
                env.setdefault(key, "")
                continue
            env[key] = value
        return env

    def _semantic_scholar_python(self) -> str:
        override = os.environ.get("ECOLOGY_HARNESS_MCP_PYTHON", "").strip()
        candidates = [
            override,
            str(Path.home() / "anaconda" / "envs" / "eh_py" / "bin" / "python"),
            "/Users/jiezhou/anaconda/envs/py310/bin/python",
            shutil.which("python3.11") or "",
            shutil.which("python3.10") or "",
            sys.executable,
        ]
        for candidate in candidates:
            if not candidate:
                continue
            path = Path(candidate)
            if not path.is_absolute():
                resolved = shutil.which(candidate)
                if not resolved:
                    continue
                path = Path(resolved)
            if not path.exists():
                continue
            try:
                completed = subprocess.run(
                    [str(path), "-c", "import sys; print('%s.%s' % sys.version_info[:2])"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
            except Exception:
                continue
            version = (completed.stdout or "").strip()
            if completed.returncode == 0 and version:
                major_minor = tuple(int(item) for item in version.split(".", 1))
                if major_minor >= (3, 10):
                    return str(path)
        raise ToolError(
            "Semantic Scholar compatibility requires Python 3.10+; set ECOLOGY_HARNESS_MCP_PYTHON or install a compatible interpreter."
        )

    def _semantic_scholar_invocation(self, tool_name: str, params: dict[str, Any]) -> tuple[str, list[str]]:
        normalized = normalize_name_for_mcp(tool_name)
        if normalized == "paper_search":
            query = self._first_string(params, "query", "paper", "title", "topic", "text", "q")
            if not query:
                raise ToolError("semantic-scholar paper_search requires a non-empty query.")
            shortlist = max(int(params.get("limit", 7) or 7), 1)
            return "paper-triage", [
                query,
                "--shortlist-size",
                str(shortlist),
                "--relevance-limit",
                str(max(shortlist * 2, 10)),
            ]
        if normalized == "paper_lookup":
            query = self._first_string(params, "query", "paper", "title", "paper_id", "doi", "identifier")
            if not query:
                raise ToolError("semantic-scholar paper_lookup requires a paper title, DOI, or paper_id.")
            return "paper-triage", [
                query,
                "--shortlist-size",
                "1",
                "--relevance-limit",
                "5",
                "--bulk-candidate-limit",
                "8",
            ]
        if normalized == "paper_recommendations":
            seeds = self._string_list(params, "seeds", "papers", "paper_ids", "titles")
            if not seeds:
                single = self._first_string(params, "query", "paper", "title", "paper_id", "doi", "seed")
                if single:
                    seeds = [single]
            if not seeds:
                raise ToolError("semantic-scholar paper_recommendations requires at least one seed paper.")
            argv = list(seeds[:3])
            for negative in self._string_list(params, "negative_seeds", "negative", "exclude"):
                argv.extend(["--negative", negative])
            pool_name = self._first_string(params, "recommendation_pool", "pool") or "all-cs"
            argv.extend(["--pool", "recent" if pool_name == "recent" else "all-cs"])
            argv.extend(["--limit", str(max(int(params.get("recommendation_limit", params.get("limit", 60)) or 60), 1))])
            argv.extend(["--per-bucket-limit", str(max(int(params.get("per_bucket_limit", 5) or 5), 1))])
            return "expand-references", argv
        if normalized == "paper_citations":
            focal_query = self._first_string(params, "query", "paper", "title", "paper_id", "doi", "identifier")
            if not focal_query:
                raise ToolError("semantic-scholar paper_citations requires a focal paper query.")
            return "trace-citations", [
                focal_query,
                "--depth",
                str(2 if int(params.get("depth", 1) or 1) >= 2 else 1),
                "--max-references",
                str(max(int(params.get("max_references", 50) or 50), 1)),
                "--max-citations",
                str(max(int(params.get("max_citations", 50) or 50), 1)),
                "--second-hop-limit",
                str(max(int(params.get("second_hop_limit", 10) or 10), 1)),
            ]
        if normalized == "paper_snippets":
            query = self._first_string(params, "query", "text", "phrase", "paper", "title", "concept")
            if not query:
                raise ToolError("semantic-scholar paper_snippets requires a query or phrase.")
            shortlist = max(int(params.get("limit", 5) or 5), 1)
            return "paper-triage", [
                query,
                "--shortlist-size",
                str(shortlist),
                "--snippet-candidate-limit",
                str(max(int(params.get("snippet_candidate_limit", shortlist) or shortlist), 1)),
                "--snippet-limit-per-paper",
                str(max(int(params.get("snippet_limit_per_paper", 3) or 3), 1)),
            ]
        raise ToolError("Semantic Scholar compatibility does not support MCP tool `%s` yet." % tool_name)

    def _format_semantic_scholar_result(
        self,
        *,
        requested_tool: str,
        workflow_name: str,
        payload: dict[str, Any],
    ) -> str:
        result = payload.get("result", {}) if isinstance(payload.get("result"), dict) else {}
        runtime = payload.get("runtime", {}) if isinstance(payload.get("runtime"), dict) else {}
        lines = [
            "semantic-scholar/%s via %s (%s)"
            % (
                requested_tool,
                workflow_name,
                runtime.get("mode", "compat"),
            )
        ]
        if workflow_name == "paper-triage":
            shortlist = result.get("shortlist", []) if isinstance(result.get("shortlist"), list) else []
            for index, item in enumerate(shortlist[:5], start=1):
                paper = item.get("paper", {}) if isinstance(item, dict) else {}
                title = str(paper.get("title", "") or "Untitled")
                year = paper.get("year")
                score = item.get("score")
                why = item.get("why", []) if isinstance(item.get("why"), list) else []
                line = "%s. %s" % (index, title)
                if year:
                    line += " (%s)" % year
                if score is not None:
                    line += " score=%.3f" % float(score)
                if why:
                    line += " — " + "; ".join(str(entry) for entry in why[:2])
                lines.append(line)
            if result.get("notes"):
                lines.append("notes: " + "; ".join(str(item) for item in result["notes"][:3]))
        elif workflow_name == "trace-citations":
            focal = result.get("focal", {}) if isinstance(result.get("focal"), dict) else {}
            focal_paper = focal.get("paper", {}) if isinstance(focal.get("paper"), dict) else {}
            if focal_paper.get("title"):
                lines.append("focal: %s" % focal_paper["title"])
            lines.append(
                "foundations=%s direct_descendants=%s bridge_nodes=%s second_hop=%s"
                % (
                    len(result.get("foundations", []) or []),
                    len(result.get("direct_descendants", []) or []),
                    len(result.get("bridge_nodes", []) or []),
                    len(result.get("second_hop", []) or []),
                )
            )
        elif workflow_name == "expand-references":
            for bucket in (
                "closest_neighbors",
                "bridge_papers",
                "foundational",
                "methodological",
                "recent",
                "surveys_or_benchmarks",
            ):
                items = result.get(bucket, []) if isinstance(result.get(bucket), list) else []
                if not items:
                    continue
                pretty_bucket = bucket.replace("_", " ")
                sample_titles = []
                for item in items[:3]:
                    paper = item.get("paper", {}) if isinstance(item, dict) else {}
                    title = str(paper.get("title", "") or "").strip()
                    if title:
                        sample_titles.append(title)
                if sample_titles:
                    lines.append("%s: %s" % (pretty_bucket, " | ".join(sample_titles)))
        if len(lines) == 1:
            lines.append(json.dumps(result, ensure_ascii=False, indent=2)[:2000])
        return "\n".join(lines)

    @staticmethod
    def _first_string(params: dict[str, Any], *keys: str) -> str:
        for key in keys:
            value = params.get(key)
            if value is None:
                continue
            text = str(value).strip()
            if text:
                return text
        return ""

    @staticmethod
    def _string_list(params: dict[str, Any], *keys: str) -> list[str]:
        values: list[str] = []
        for key in keys:
            raw = params.get(key)
            if isinstance(raw, list):
                for item in raw:
                    text = str(item).strip()
                    if text:
                        values.append(text)
                if values:
                    return values
        return values

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
