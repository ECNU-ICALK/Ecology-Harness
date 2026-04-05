from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import sys
import textwrap
from typing import Any
from typing import Iterable

from ecology_harness.runtime.providers import resolve_provider


class ConsoleRenderer:
    def __init__(self, stream=None) -> None:
        self.stream = stream or sys.stdout
        self.is_tty = bool(getattr(self.stream, "isatty", lambda: False)())
        self.color_enabled = self.is_tty and not os.environ.get("NO_COLOR")
        self.width = max(72, min(120, shutil.get_terminal_size((100, 24)).columns))

    def print(self, text: str = "") -> None:
        print(text, file=self.stream, flush=True)

    def rule(self, title: str = "") -> None:
        line_char = "─"
        if title:
            label = " %s " % title
            fill = max(0, self.width - len(label))
            left = fill // 2
            right = fill - left
            rendered = "%s%s%s" % (
                self._style(line_char * left, "muted"),
                self._style(label, "accent"),
                self._style(line_char * right, "muted"),
            )
            self.print(rendered)
            return
        self.print(self._style(line_char * self.width, "muted"))

    def banner(self, app, mode: str, turn_count: int = 0) -> None:
        self._print_topology(app, mode)
        status = self._join_segments(
            [
                "mode: %s" % mode,
                "turns: %s" % turn_count,
            ]
        )
        hint = self._join_segments(
            [
                self._style("/help", "accent") + " commands",
                self._style("/model", "accent") + " switch",
                self._style("/config", "accent") + " details",
                self._style("Ctrl+C", "accent") + " exit",
            ]
        )
        self.print(self._style(status, "muted"))
        self.print(hint)
        self.print()

    def print_repl_welcome(self) -> None:
        self.print(self._style("Start typing naturally, or use / to browse commands.", "muted"))
        self.print()

    def section(self, title: str, lines: Iterable[str]) -> None:
        self.rule(title)
        for line in lines:
            self.print(line)
        self.rule()

    def print_prompt_block(self, prompt: str) -> None:
        wrapped = _wrap_block(prompt, self.width)
        if not wrapped:
            wrapped = [""]
        self.print("%s%s" % (self._style("> ", "user"), wrapped[0]))
        for line in wrapped[1:]:
            self.print("  %s" % line)
        self.print()

    def print_final_block(
        self,
        text: str,
        steps: int = 0,
        tool_calls: int = 0,
        tools_used: list[str] | None = None,
    ) -> None:
        body = list(_wrap_block(text or "<empty>", self.width))
        summary_parts = [
            "steps: %s" % steps,
            "tools: %s" % tool_calls,
        ]
        if tools_used:
            summary_parts.append("used: %s" % ", ".join(tools_used[:5]))
        if not body:
            body = ["<empty>"]
        self.print("%s%s" % (self._style("⏺ ", "role"), body[0]))
        for line in body[1:]:
            self.print("  %s" % line)
        self.print(self._style(self._join_segments(summary_parts), "muted"))
        self.print()

    def print_notice(self, text: str, level: str = "info") -> None:
        label = {
            "info": "ℹ",
            "warn": "▲",
            "error": "✕",
        }.get(level, "[info]")
        style = {"info": "info", "warn": "warn", "error": "error"}.get(level, "info")
        self.print("%s %s" % (self._style(label, style), text))

    def print_table(self, title: str, columns: list[str], rows: list[list[str]]) -> None:
        if not rows:
            self.section(title, ["No items found."])
            return
        normalized = [[str(cell) for cell in row] for row in rows]
        widths = []
        for index, column in enumerate(columns):
            width = len(column)
            for row in normalized:
                width = max(width, len(row[index]))
            widths.append(min(width, max(12, self.width // max(1, len(columns)) + 6)))

        self.rule(title)
        self.print(_format_row(columns, widths, header=True))
        self.print(_format_separator(widths))
        for row in normalized:
            clipped = [_clip_text(row[index], widths[index]) for index in range(len(columns))]
            self.print(_format_row(clipped, widths))
        self.rule()

    def print_tool_description(self, tool) -> None:
        self.section(
            "Tool",
            [
                "name: %s" % tool.name,
                "source: %s" % getattr(tool, "source", "native"),
                "origin: %s" % (getattr(tool, "origin", "") or "-"),
                "description: %s" % tool.description,
                "read_only: %s" % tool.read_only,
                "concurrent_safe: %s" % tool.concurrent_safe,
                "",
                json.dumps(tool.input_schema, indent=2, ensure_ascii=False),
            ],
        )

    def print_sandbox_status(self, result) -> None:
        self.section("Sandbox", result.content.splitlines() or ["<empty>"])

    def print_status_panel(
        self,
        app,
        turn_count: int,
        conversation_messages: int,
        trace_enabled: bool,
        total_tool_calls: int = 0,
        total_steps: int = 0,
    ) -> None:
        self.section(
            "Status",
            [
                "provider: %s" % self.provider_text(app.settings),
                "model: %s" % app.settings.model,
                "permissions: %s" % getattr(app.settings, "permission_mode", "workspace-write"),
                "sandbox: %s" % self.sandbox_text(app.settings),
                "runtime_mode: %s" % getattr(app, "runtime_mode", "default"),
                "trace: %s" % ("on" if trace_enabled else "off"),
                "turns: %s" % turn_count,
                "conversation_messages: %s" % conversation_messages,
                "session_tool_calls: %s" % total_tool_calls,
                "session_steps: %s" % total_steps,
            ],
        )

    def print_config_panel(self, app) -> None:
        settings = app.settings
        self.section(
            "Config",
            [
                self._style("Runtime", "accent"),
                "workspace: %s" % settings.workspace_root,
                "provider: %s" % self.provider_text(settings),
                "model: %s" % settings.model,
                "runtime_mode: %s" % getattr(app, "runtime_mode", "default"),
                "max_agent_loops: %s" % _loop_limit_text(settings.max_agent_loops),
                "max_context_tokens: %s" % settings.max_context_tokens,
                "",
                self._style("Execution", "accent"),
                "command_timeout_sec: %s" % settings.command_timeout_sec,
                "provider_timeout_sec: %s" % settings.provider_timeout_sec,
                "sandbox: %s" % self.sandbox_text(settings),
                "",
                self._style("State", "accent"),
                "session_dir: %s" % settings.session_dir,
                "memory_dir: %s" % settings.memory_dir,
                "skill_dir: %s" % settings.skill_dir,
                "plugin_dir: %s" % settings.plugin_dir,
                "mcp_dir: %s" % settings.mcp_dir,
            ],
        )

    def print_permissions_panel(self, app) -> None:
        settings = app.settings
        self.section(
            "Permissions",
            [
                "permission_mode: %s" % settings.permission_mode,
                "sandbox_enabled: %s" % _bool_text(settings.sandbox_enabled),
                "sandbox_backend: %s" % settings.sandbox_backend,
                "sandbox_mode: %s" % settings.sandbox_mode,
                "network: %s" % ("allowed" if settings.sandbox_allow_network else "blocked"),
                "read_roots: %s" % ", ".join(str(item) for item in settings.resolved_sandbox_read_roots()),
                "write_roots: %s" % ", ".join(str(item) for item in settings.resolved_sandbox_write_roots()),
            ],
        )

    def print_session_panel(self, app, conversation_messages: int, turn_count: int) -> None:
        latest_path = app.latest_session_path()
        exists = latest_path.exists()
        session_count = len(app.list_sessions()) if hasattr(app, "list_sessions") else 0
        lines = [
            "current_turns: %s" % turn_count,
            "conversation_messages: %s" % conversation_messages,
            "latest_session: %s" % latest_path,
            "latest_session_exists: %s" % _bool_text(exists),
            "stored_sessions: %s" % session_count,
            "resume_hint: eh --resume latest",
        ]
        if exists:
            lines.append("latest_session_bytes: %s" % latest_path.stat().st_size)
        self.section("Session", lines)

    def print_cost_panel(self, total_tool_calls: int, total_steps: int, turn_count: int) -> None:
        self.section(
            "Session Activity",
            [
                "turns: %s" % turn_count,
                "steps: %s" % total_steps,
                "tool_calls: %s" % total_tool_calls,
                "token_cost: unavailable in this build",
                "currency_cost: unavailable in this build",
            ],
        )

    def prompt_label(self, app, turn_count: int) -> str:
        del app, turn_count
        return "> "

    def clear_screen(self) -> None:
        if self.is_tty:
            self.print("\033[2J\033[H")
            return
        self.print("\n" * 4)

    def build_trace_printer(self):
        def _handle_event(event) -> None:
            line = self.format_trace_event(event.kind, event.payload)
            if line:
                self.print(line)

        return _handle_event

    def format_trace_event(self, kind: str, payload: dict[str, Any]) -> str:
        if kind == "run_started":
            return "%s working..." % self._style("ℹ", "info")
        if kind == "step_started":
            return ""
        if kind == "assistant_message":
            return ""
        if kind == "tool_call":
            return "  %s%s" % (
                self._style("⏵ ", "tool"),
                summarize_tool_call(
                    payload.get("tool", ""),
                    payload.get("arguments", {}),
                ),
            )
        if kind == "tool_result":
            status = "ok" if payload.get("allowed", True) else "blocked"
            output = summarize_tool_output(payload.get("output", ""))
            if status != "ok":
                return "    %s %s" % (self._style("✕", "error"), output)
            return "    %s" % self._style(output, "muted")
        if kind == "messages_compacted":
            return "%s context compacted, removed %s messages" % (
                self._style("ℹ", "info"),
                payload.get("removed_message_count", 0),
            )
        if kind == "run_completed":
            return ""
        if kind == "run_stopped":
            return "%s %s" % (
                self._style("▲", "warn"),
                _clip_text(payload.get("final_text", "")),
            )
        return ""

    def provider_text(self, settings) -> str:
        try:
            _spec, resolved_provider, _model_name = resolve_provider(settings)
        except Exception:
            return settings.provider
        requested = settings.provider or resolved_provider
        if requested in {"", "auto"}:
            return "auto -> %s" % resolved_provider
        if requested != resolved_provider:
            return "%s -> %s" % (requested, resolved_provider)
        return resolved_provider

    def sandbox_text(self, settings) -> str:
        if not getattr(settings, "sandbox_enabled", True):
            return "disabled"
        mode = getattr(settings, "sandbox_mode", "workspace-write")
        backend = getattr(settings, "sandbox_backend", "internal")
        network = "net" if getattr(settings, "sandbox_allow_network", True) else "no-net"
        return "%s (%s, %s)" % (mode, backend, network)

    def _style(self, text: str, role: str) -> str:
        if not self.color_enabled:
            return text
        codes = {
            "accent": "96",
            "muted": "90",
            "role": "32",
            "tool": "96",
            "user": "97",
            "info": "94",
            "warn": "33",
            "error": "91",
            "brand": "1;97",
            "brand2": "90",
            "key": "96",
            "leaf": "92",
            "core": "1;97",
        }
        code = codes.get(role)
        if not code:
            return text
        return "\033[%sm%s\033[0m" % (code, text)

    def _print_topology(self, app, mode: str) -> None:
        del app
        art = [
            "   ______          __                 ",
            "  / ____/________  / /___  ____ ___  __",
            " / __/ / ___/ __ \\/ / __ \\/ __ `__ \\/ /",
            "/ /___/ /__/ /_/ / / /_/ / / / / / / / ",
            "\\____/\\___/\\____/_/\\____/_/ /_/ /_/_/  ",
            "    __  __                               ",
            "   / / / /___ __________  ___  _____ ___",
            "  / /_/ / __ `/ ___/ __ \\/ _ \\/ ___/ __ \\",
            " / __  / /_/ / /  / / / /  __(__  ) /_/ /",
            "/_/ /_/\\__,_/_/  /_/ /_/\\___/____/\\____/ ",
        ]
        meta = "Ecology Harness  |  self-evolving analysis shell  |  %s mode" % mode
        self.print(self._style("=" * self.width, "accent"))
        for line in art:
            self.print(self._style(_center_plain(line, self.width), "brand"))
        self.print(self._style(_center_plain(meta, self.width), "brand2"))
        self.print(self._style("=" * self.width, "accent"))

    def _topology_counts(self, app) -> dict[str, int]:
        counts = {
            "memory": 0,
            "tools": 0,
            "skills": 0,
            "agents": 0,
            "plugins": 0,
            "mcp": 0,
        }
        try:
            counts["memory"] = len(app.memory_manager.list_items()) if app.memory_manager else 0
        except Exception:
            counts["memory"] = 0
        try:
            counts["tools"] = len(app.registry.list_tools())
        except Exception:
            counts["tools"] = 0
        try:
            counts["skills"] = len(app.skill_loader.list_skills()) if app.skill_loader else 0
        except Exception:
            counts["skills"] = 0
        try:
            counts["agents"] = len(app.subagent_manager.list_agent_definitions()) if app.subagent_manager else 0
        except Exception:
            counts["agents"] = 0
        try:
            counts["plugins"] = len(app.plugin_manager.list_enabled_plugins()) if app.plugin_manager else 0
        except Exception:
            counts["plugins"] = 0
        try:
            counts["mcp"] = len(app.mcp_registry.list_server_states()) if app.mcp_registry else 0
        except Exception:
            counts["mcp"] = 0
        return counts

    def _module_summary(self, counts: dict[str, int]) -> str:
        parts = [
            "memory %s" % counts["memory"],
            "tools %s" % counts["tools"],
            "skills %s" % counts["skills"],
            "agents %s" % counts["agents"],
            "plugins %s" % counts["plugins"],
            "mcp %s" % counts["mcp"],
        ]
        return " · ".join(parts)

    def _join_segments(self, segments: list[str]) -> str:
        sep = self._style(" │ ", "muted")
        return sep.join(segment for segment in segments if segment)


def summarize_tool_output(text: str, limit: int = 160) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return _clip_text(stripped, limit=limit)
    cleaned = text.strip() or "<empty>"
    return _clip_text(cleaned, limit=limit)


def summarize_tool_call(name: str, arguments: dict[str, Any], limit: int = 120) -> str:
    tool_name = name or "tool"
    lower = tool_name.lower()
    if lower in {"bash", "bashtool"} and arguments.get("command"):
        return "%s %s" % (tool_name, _clip_text(str(arguments["command"]), limit=limit))
    for key in ("path", "file_path", "pattern", "uri", "server", "tool", "name", "query"):
        value = arguments.get(key)
        if value:
            return "%s %s" % (tool_name, _clip_text(str(value), limit=limit))
    if arguments:
        rendered = json.dumps(arguments, ensure_ascii=False, sort_keys=True)
        return "%s %s" % (tool_name, _clip_text(rendered, limit=limit))
    return tool_name


def _format_row(cells: list[str], widths: list[int], header: bool = False) -> str:
    rendered = []
    for index, cell in enumerate(cells):
        align = cell.ljust(widths[index])
        rendered.append(align)
    row = " | ".join(rendered)
    if header:
        return row
    return row


def _format_separator(widths: list[int]) -> str:
    return "-+-".join("-" * width for width in widths)


def _wrap_block(text: str, width: int) -> list[str]:
    lines = text.splitlines() or [text]
    wrapped = []
    limit = max(24, width - 4)
    for line in lines:
        normalized = line.rstrip()
        if not normalized:
            wrapped.append("")
            continue
        segments = textwrap.wrap(
            normalized,
            width=limit,
            break_long_words=False,
            break_on_hyphens=False,
            replace_whitespace=False,
            drop_whitespace=False,
        )
        if not segments:
            wrapped.append(normalized)
            continue
        wrapped.extend(segment.rstrip() for segment in segments)
    return wrapped


def _clip_text(text: str, limit: int = 160) -> str:
    cleaned = " ".join(str(text).split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3] + "..."


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


def _pad_or_trim(text: str, width: int) -> str:
    visible = _strip_ansi(text)
    if len(visible) > width:
        trimmed = visible[: max(0, width - 3)] + ("..." if width >= 3 else "")
        return trimmed
    return text + (" " * (width - len(visible)))


def _center_plain(text: str, width: int) -> str:
    if len(text) >= width:
        return text[:width]
    padding = width - len(text)
    left = padding // 2
    right = padding - left
    return (" " * left) + text + (" " * right)


def _shorten_path(path: Path, limit: int) -> str:
    rendered = str(path)
    if len(rendered) <= limit:
        return rendered
    return "..." + rendered[-(limit - 3) :]


def _bool_text(value: bool) -> str:
    return "yes" if value else "no"


def _loop_limit_text(value: int) -> str:
    return "unlimited" if value <= 0 else str(value)
