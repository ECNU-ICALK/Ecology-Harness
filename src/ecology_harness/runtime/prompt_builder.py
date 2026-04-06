from __future__ import annotations

from datetime import datetime
from pathlib import Path
import platform
import subprocess

from ecology_harness.config import HarnessSettings


class PromptBuilder:
    def build(
        self,
        settings: HarnessSettings,
        memory_context: str,
        skill_index: list[dict[str, str]],
        agent_index: list[dict[str, str]],
        plugin_index: list[dict[str, str]],
        mcp_index: list[dict[str, str]],
        runtime_mode: str = "default",
    ) -> str:
        skill_lines = [
            "- %(name)s (%(source)s): %(description)s" % item for item in skill_index[:20]
        ] or ["- No skills available."]
        agent_lines = [
            "- %(name)s: %(description)s" % item for item in agent_index[:20]
        ] or ["- No specialized agent types available."]
        plugin_lines = [
            "- %(name)s (%(source)s): %(description)s" % item for item in plugin_index[:10]
        ] or ["- No active plugins."]
        mcp_lines = [
            "- %(server_name)s (%(transport)s, %(status)s): tools=%(tool_count)s resources=%(resource_count)s"
            % item
            for item in mcp_index[:10]
        ] or ["- No MCP servers configured."]

        prompt = (
            "You are Ecology Harness, a terminal-native agent harness.\n"
            "You can reason, use tools, maintain durable memory, delegate to subagents, and track tasks.\n\n"
            "Guidelines:\n"
            "- Be concise and direct.\n"
            "- Prefer reading current files before making claims about the workspace.\n"
            "- Use memory only for durable context that cannot be derived from code or docs.\n"
            "- When earlier context has been compacted, trust the continuation summary and resume directly.\n"
            "- For multi-step work, create and update tasks.\n"
            "- Use specialized agents when delegation helps.\n"
            "- When delegating, pass crisp ownership, expected output, and dependency context.\n\n"
            "Environment:\n"
            "- Current date: %s\n"
            "- Working directory: %s\n"
            "- Platform: %s\n"
            "- Permission mode: %s\n"
            "- Runtime mode: %s\n"
            "%s%s\n"
            "Available skills:\n%s\n\n"
            "Available agent types:\n%s\n"
            "\nActive plugins:\n%s\n"
            "\nAvailable MCP servers:\n%s\n"
            % (
                datetime.now().strftime("%Y-%m-%d %A"),
                settings.workspace_root,
                platform.system(),
                settings.permission_mode,
                runtime_mode,
                self._get_git_info(settings.workspace_root),
                self._get_claude_md(settings.workspace_root),
                "\n".join(skill_lines),
                "\n".join(agent_lines),
                "\n".join(plugin_lines),
                "\n".join(mcp_lines),
            )
        )
        if memory_context:
            prompt += "\n# Memory\n%s\n" % memory_context
        return prompt

    def _get_git_info(self, workspace_root: Path) -> str:
        try:
            branch = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=str(workspace_root),
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
            status = subprocess.check_output(
                ["git", "status", "--short"],
                cwd=str(workspace_root),
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
            lines = ["- Git branch: %s" % branch]
            if status:
                lines.append("- Git status:\n" + "\n".join("  %s" % line for line in status.splitlines()[:10]))
            return "\n".join(lines) + "\n"
        except Exception:
            return ""

    def _get_claude_md(self, workspace_root: Path) -> str:
        content_parts = []
        global_md = Path.home() / ".claude" / "CLAUDE.md"
        if global_md.exists():
            try:
                content_parts.append("[Global CLAUDE.md]\n%s" % global_md.read_text(encoding="utf-8"))
            except Exception:
                pass
        current = workspace_root
        for _ in range(10):
            candidate = current / "CLAUDE.md"
            if candidate.exists():
                try:
                    content_parts.append("[Project CLAUDE.md: %s]\n%s" % (candidate, candidate.read_text(encoding="utf-8")))
                except Exception:
                    pass
                break
            if current.parent == current:
                break
            current = current.parent
        if not content_parts:
            return ""
        return "# CLAUDE.md\n" + "\n\n".join(content_parts) + "\n"
