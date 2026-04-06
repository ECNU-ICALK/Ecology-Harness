from __future__ import annotations

from dataclasses import dataclass
import os
import sys
from typing import Iterable

try:  # pragma: no cover - platform dependent
    import readline
except Exception:  # pragma: no cover - optional dependency fallback
    readline = None  # type: ignore[assignment]

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import Completer, Completion
    from prompt_toolkit.history import InMemoryHistory
    from prompt_toolkit.shortcuts import CompleteStyle
except Exception:  # pragma: no cover - optional dependency fallback
    PromptSession = None  # type: ignore[assignment]
    Completer = object  # type: ignore[assignment]
    Completion = None  # type: ignore[assignment]
    InMemoryHistory = None  # type: ignore[assignment]
    CompleteStyle = None  # type: ignore[assignment]


@dataclass(frozen=True)
class CommandSuggestion:
    text: str
    description: str
    category: str = "command"


SESSION_COMMAND_SUGGESTIONS = [
    CommandSuggestion("/help", "show session commands", "session"),
    CommandSuggestion("/status", "show session status", "session"),
    CommandSuggestion("/config", "show active runtime configuration", "session"),
    CommandSuggestion("/permissions", "show or change permission mode", "session"),
    CommandSuggestion("/model", "show or change the active model", "session"),
    CommandSuggestion("/session", "show saved session information", "session"),
    CommandSuggestion("/cost", "show current session activity summary", "session"),
    CommandSuggestion("/tools", "list built-in tools", "session"),
    CommandSuggestion("/skills", "list available skills", "session"),
    CommandSuggestion("/plugins", "list installed plugins", "session"),
    CommandSuggestion("/mcp", "list configured MCP servers", "session"),
    CommandSuggestion("/memories", "list saved memories", "session"),
    CommandSuggestion("/tasks", "list tracked tasks", "session"),
    CommandSuggestion("/providers", "list configured provider backends", "session"),
    CommandSuggestion("/sandbox", "show sandbox state", "session"),
    CommandSuggestion("/attach", "add an image or document attachment to the next turn", "session"),
    CommandSuggestion("/image", "add an image attachment to the next turn", "session"),
    CommandSuggestion("/doc", "add a document attachment to the next turn", "session"),
    CommandSuggestion("/audio", "add an audio attachment to the next turn", "session"),
    CommandSuggestion("/video", "add a video attachment to the next turn", "session"),
    CommandSuggestion("/attachments", "show pending attachments", "session"),
    CommandSuggestion("/clear-attachments", "remove pending attachments", "session"),
    CommandSuggestion("/trace on", "enable intermediate step trace", "session"),
    CommandSuggestion("/trace off", "disable intermediate step trace", "session"),
    CommandSuggestion("/new", "start a fresh conversation", "session"),
    CommandSuggestion("/reset", "clear the in-memory conversation", "session"),
    CommandSuggestion("/clear", "clear the terminal and redraw the header", "session"),
    CommandSuggestion("/quit", "exit the REPL", "session"),
    CommandSuggestion("/exit", "exit the REPL", "session"),
    CommandSuggestion("/tool", "run a tool with `/tool NAME {json}`", "tool"),
]


def build_repl_suggestions(app) -> list[CommandSuggestion]:
    suggestions: list[CommandSuggestion] = list(SESSION_COMMAND_SUGGESTIONS)
    for skill in app.skill_loader.list_skills():
        if not skill.user_invocable:
            continue
        for trigger in skill.triggers:
            suggestions.append(
                CommandSuggestion(
                    text=trigger,
                    description=skill.description or skill.name,
                    category="skill",
                )
            )
    deduped: dict[str, CommandSuggestion] = {}
    for item in suggestions:
        if item.text not in deduped:
            deduped[item.text] = item
    return list(deduped.values())


def suggest_repl_commands(app, text: str) -> list[CommandSuggestion]:
    stripped = text.strip()
    if not stripped.startswith(("/", "\\")):
        return []

    if stripped in {"/", "/?", "\\", "\\?"}:
        return _top_level_suggestions(app, alias_mode=stripped.startswith("\\"))

    if stripped.startswith("\\"):
        normalized = "/" + stripped[1:]
        if normalized.startswith("/trace "):
            return _trace_suggestions(normalized, alias_mode=True)
        return _match_suggestions(
            _top_level_suggestions(app, alias_mode=True),
            "\\" + stripped[1:],
        )

    if stripped.startswith("/tool "):
        return _tool_suggestions(app, stripped)

    if stripped.startswith("/trace "):
        return _trace_suggestions(stripped, alias_mode=False)

    return _match_suggestions(_top_level_suggestions(app, alias_mode=False), stripped)


def create_repl_reader(app, console, state_getter=None):
    if _should_use_prompt_toolkit():
        completer = ReplCompleter(app)
        session = PromptSession(
            history=InMemoryHistory(),
            completer=completer,
            complete_while_typing=True,
            complete_style=CompleteStyle.MULTI_COLUMN,
            reserve_space_for_menu=10,
        )

        def _read(prompt_text: str) -> str:
            return session.prompt(
                prompt_text,
                bottom_toolbar=lambda: build_toolbar_text(app, state_getter() if state_getter else None),
            )

        return _read

    if _should_use_readline():
        return _readline_reader

    return _fallback_reader


def _fallback_reader(prompt_text: str) -> str:
    return input(prompt_text)


def _readline_reader(prompt_text: str) -> str:
    line = input(prompt_text)
    if line and readline is not None:  # pragma: no branch - tiny guard
        try:
            readline.add_history(line)
        except Exception:
            pass
    return _strip_control_sequences(line)


def _should_use_prompt_toolkit() -> bool:
    if os.environ.get("EH_FORCE_BASIC_REPL") == "1":
        return False
    if PromptSession is None:
        return False
    return bool(getattr(sys.stdin, "isatty", lambda: False)()) and bool(
        getattr(sys.stdout, "isatty", lambda: False)()
    )


def _should_use_readline() -> bool:
    if readline is None:
        return False
    return bool(getattr(sys.stdin, "isatty", lambda: False)()) and bool(
        getattr(sys.stdout, "isatty", lambda: False)()
    )


def _strip_control_sequences(text: str) -> str:
    if not text:
        return text
    sequences = ("\x1b[A", "\x1b[B", "\x1b[C", "\x1b[D")
    cleaned = text
    for sequence in sequences:
        cleaned = cleaned.replace(sequence, "")
    return cleaned


def build_toolbar_text(app, state=None) -> str:
    turns = getattr(state, "turn_count", 0)
    trace_enabled = getattr(state, "trace_enabled", True)
    total_tool_calls = getattr(state, "total_tool_calls", 0)
    attachment_count = len(getattr(state, "pending_attachment_paths", []) or [])
    provider = getattr(app.settings, "provider", "auto") or "auto"
    model = getattr(app.settings, "model", "")
    permission_mode = getattr(app.settings, "permission_mode", "workspace-write")
    sandbox_mode = getattr(app.settings, "sandbox_mode", "workspace-write")
    sandbox_state = "off" if not getattr(app.settings, "sandbox_enabled", True) else sandbox_mode
    runtime_mode = getattr(app, "runtime_mode", "default")
    parts = [
        "/ for commands",
        "model: %s" % model,
        "provider: %s" % provider,
        "mode: %s" % runtime_mode,
        "permissions: %s" % permission_mode,
        "sandbox: %s" % sandbox_state,
        "trace: %s" % ("on" if trace_enabled else "off"),
        "turns: %s" % turns,
        "tools: %s" % total_tool_calls,
        "attachments: %s" % attachment_count,
    ]
    return " \u2502 ".join(parts)


class ReplCompleter(Completer):  # pragma: no cover - exercised through prompt_toolkit at runtime
    def __init__(self, app) -> None:
        self.app = app

    def get_completions(self, document, complete_event) -> Iterable[Completion]:
        del complete_event
        text = document.text_before_cursor
        suggestions = suggest_repl_commands(self.app, text)
        if not suggestions:
            return
        prefix = text.strip()
        if prefix in {"/", "/?", "\\", "\\?"}:
            prefix_length = len(prefix)
        else:
            prefix_length = len(prefix)
        for item in suggestions:
            yield Completion(
                item.text,
                start_position=-prefix_length,
                display=item.text,
                display_meta="%s: %s" % (item.category, item.description),
            )


def _top_level_suggestions(app, alias_mode: bool) -> list[CommandSuggestion]:
    suggestions = build_repl_suggestions(app)
    if not alias_mode:
        return suggestions
    alias_items = []
    for item in suggestions:
        if item.text.startswith("/tool") or item.category == "skill":
            continue
        alias_items.append(
            CommandSuggestion(
                text="\\" + item.text[1:],
                description=item.description,
                category=item.category,
            )
        )
    return alias_items


def _trace_suggestions(prefix: str, alias_mode: bool) -> list[CommandSuggestion]:
    leader = "\\" if alias_mode else "/"
    items = [
        CommandSuggestion("%strace on" % leader, "enable intermediate step trace", "session"),
        CommandSuggestion("%strace off" % leader, "disable intermediate step trace", "session"),
    ]
    return _match_suggestions(items, prefix if not alias_mode else "\\" + prefix[1:])


def _tool_suggestions(app, prefix: str) -> list[CommandSuggestion]:
    items = []
    for tool in app.registry.list_tools():
        items.append(
            CommandSuggestion(
                text="/tool %s" % tool.name,
                description=tool.description,
                category="tool",
            )
        )
    return _match_suggestions(items, prefix)


def _match_suggestions(
    suggestions: list[CommandSuggestion],
    prefix: str,
) -> list[CommandSuggestion]:
    normalized_prefix = prefix.strip()
    if normalized_prefix in {"", "/", "\\"}:
        return suggestions
    return [item for item in suggestions if item.text.startswith(normalized_prefix)]
