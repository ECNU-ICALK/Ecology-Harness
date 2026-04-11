from __future__ import annotations

from dataclasses import dataclass

from ecology_harness.config import HarnessSettings
from ecology_harness.tools import ToolRegistry


@dataclass(frozen=True)
class PermissionDecision:
    allowed: bool
    reason: str
    requestable: bool = False
    grant_key: str = ""
    summary: str = ""


class PermissionPolicy:
    def check(
        self,
        tool_name: str,
        arguments: dict,
        registry: ToolRegistry,
        settings: HarnessSettings,
    ) -> PermissionDecision:
        tool = registry.get(tool_name)
        if tool is None:
            return PermissionDecision(False, "Unknown tool")

        mode = settings.permission_mode.strip().lower()
        if mode == "allow-all":
            return PermissionDecision(True, "allowed")

        if mode == "read-only" and not tool.read_only:
            return PermissionDecision(False, "read-only mode blocks write and execution tools")

        if mode == "ask" and not tool.read_only and tool_name != "Bash":
            return PermissionDecision(
                False,
                "ask mode requires approval for write and execution tools",
                requestable=True,
                grant_key="tool:%s" % tool_name,
                summary=tool_name,
            )

        if tool_name == "Bash":
            command = str(arguments.get("command", ""))
            sandbox = arguments.get("_sandbox")
            if not command.strip():
                return PermissionDecision(False, "empty command")
            if sandbox is not None:
                try:
                    sandbox.validate_command(command)
                except Exception as exc:
                    return PermissionDecision(False, str(exc))
            if mode == "ask":
                compact_command = " ".join(command.strip().split())
                return PermissionDecision(
                    False,
                    "ask mode requires approval before running shell commands",
                    requestable=True,
                    grant_key="bash:%s" % compact_command,
                    summary=compact_command[:160],
                )

        return PermissionDecision(True, "allowed")
