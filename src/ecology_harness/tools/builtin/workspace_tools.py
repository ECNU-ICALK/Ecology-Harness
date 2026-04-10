from __future__ import annotations

import json

from ecology_harness.runtime.doctor import HarnessDoctor
from ecology_harness.tools.base import ToolContext, ToolDefinition, ToolError, ToolResult
from ecology_harness.tools.registry import ToolRegistry
from ecology_harness.workspace import WorkspaceBootstrapManager


def register_workspace_tools(registry: ToolRegistry) -> None:
    registry.register(
        ToolDefinition(
            name="DoctorReport",
            description="Run a lightweight environment, bootstrap, skill, and MCP health report for the current workspace.",
            input_schema={
                "type": "object",
                "properties": {
                    "probe_mcp": {"type": "boolean"},
                    "timeout_sec": {"type": "integer"},
                },
            },
            handler=_doctor_report,
            read_only=True,
            concurrent_safe=True,
        )
    )
    registry.register(
        ToolDefinition(
            name="WorkspaceBootstrapStatus",
            description="Show which workspace bootstrap files such as AGENTS.md or HEARTBEAT.md are present.",
            input_schema={"type": "object", "properties": {}},
            handler=_workspace_bootstrap_status,
            read_only=True,
            concurrent_safe=True,
        )
    )
    registry.register(
        ToolDefinition(
            name="WorkspaceBootstrapInit",
            description="Create default workspace bootstrap files such as AGENTS.md, STANDING_ORDERS.md, BOOTSTRAP.md, and HEARTBEAT.md.",
            input_schema={
                "type": "object",
                "properties": {
                    "force": {"type": "boolean"},
                    "files": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
            },
            handler=_workspace_bootstrap_init,
            read_only=False,
            concurrent_safe=False,
        )
    )


def _doctor_report(params: dict, context: ToolContext) -> ToolResult:
    app = context.services.get("app")
    if app is None:
        raise ToolError("app service is unavailable.")
    report = HarnessDoctor(app).run(
        probe_mcp=bool(params.get("probe_mcp", False)),
        timeout_sec=max(int(params.get("timeout_sec", 3) or 3), 1),
    )
    lines = [
        "workspace: %s" % report["workspace"]["root"],
        "provider: %s / %s" % (report["runtime"]["provider"], report["runtime"]["model"]),
        "bootstrap_files: %s present" % report["bootstrap"]["present_count"],
        "skills: %s total" % report["skills"]["total"],
        "mcp_servers: %s total" % report["mcp"]["total"],
    ]
    issues = report.get("issues") or []
    if issues:
        lines.append("issues:")
        lines.extend("- %s" % item for item in issues)
    else:
        lines.append("issues: none")
    suggestions = report.get("suggestions") or []
    if suggestions:
        lines.append("suggestions:")
        for item in suggestions:
            command = str(item.get("command", "") or "")
            reason = str(item.get("reason", "") or "")
            if command:
                lines.append("- %s -> %s" % (item.get("title", ""), command))
            else:
                lines.append("- %s" % item.get("title", ""))
            if reason:
                lines.append("  %s" % reason)
    return ToolResult(content="\n".join(lines), data=report)


def _workspace_bootstrap_status(params: dict, context: ToolContext) -> ToolResult:
    del params
    manager = WorkspaceBootstrapManager(context.settings.workspace_root)
    status = manager.status()
    lines = [
        "workspace: %s" % status["workspace_root"],
        "present: %s" % status["present_count"],
        "missing: %s" % status["missing_count"],
    ]
    for item in status["files"]:
        marker = "yes" if item["exists"] else "no"
        lines.append("- %s: %s" % (item["name"], marker))
    return ToolResult(content="\n".join(lines), data=status)


def _workspace_bootstrap_init(params: dict, context: ToolContext) -> ToolResult:
    manager = WorkspaceBootstrapManager(context.settings.workspace_root)
    result = manager.initialize(
        force=bool(params.get("force", False)),
        selected_files=params.get("files") or None,
    )
    summary = {
        "created": result["created"],
        "updated": result["updated"],
        "skipped": result["skipped"],
        "invalid": result["invalid"],
    }
    return ToolResult(content=json.dumps(summary, ensure_ascii=False, indent=2), data=result)
