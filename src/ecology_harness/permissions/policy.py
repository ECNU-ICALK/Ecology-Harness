from __future__ import annotations

from ecology_harness.config import HarnessSettings
from ecology_harness.tools import ToolRegistry


class PermissionPolicy:
    def check(
        self,
        tool_name: str,
        arguments: dict,
        registry: ToolRegistry,
        settings: HarnessSettings,
    ) -> tuple[bool, str]:
        tool = registry.get(tool_name)
        if tool is None:
            return False, "Unknown tool"

        mode = settings.permission_mode.strip().lower()
        if mode == "allow-all":
            return True, "allowed"

        if mode == "read-only" and not tool.read_only:
            return False, "read-only mode blocks write and execution tools"

        if tool_name == "Bash":
            command = str(arguments.get("command", ""))
            sandbox = arguments.get("_sandbox")
            if sandbox is not None:
                try:
                    sandbox.validate_command(command)
                except Exception as exc:
                    return False, str(exc)
            elif mode == "workspace-write" and not command.strip():
                return False, "empty command"

        return True, "allowed"
