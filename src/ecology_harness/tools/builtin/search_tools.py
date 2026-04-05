from __future__ import annotations

import fnmatch
import re
from pathlib import Path

from ecology_harness.tools.base import ToolContext, ToolDefinition, ToolError, ToolResult
from ecology_harness.tools.builtin.file_tools import _resolve_workspace_path
from ecology_harness.tools.registry import ToolRegistry


def register_search_tools(registry: ToolRegistry) -> None:
    registry.register(
        ToolDefinition(
            name="Glob",
            description="List files inside the workspace using a glob pattern.",
            input_schema={
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                },
                "required": ["pattern"],
            },
            handler=_glob_files,
            read_only=True,
            concurrent_safe=True,
        )
    )
    registry.register(
        ToolDefinition(
            name="Grep",
            description="Search text files inside the workspace with a regular expression.",
            input_schema={
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "include": {"type": "string"},
                    "case_sensitive": {"type": "boolean"},
                    "max_results": {"type": "integer"},
                },
                "required": ["pattern"],
            },
            handler=_grep_files,
            read_only=True,
            concurrent_safe=True,
        )
    )


def _glob_files(params: dict, context: ToolContext) -> ToolResult:
    pattern = params["pattern"]
    if Path(pattern).is_absolute():
        raise ToolError("Glob pattern must be relative to the workspace.")

    matches = [
        path.relative_to(context.settings.workspace_root).as_posix()
        for path in context.settings.workspace_root.glob(pattern)
    ]
    matches = sorted(dict.fromkeys(matches))
    limited = matches[: context.settings.max_glob_results]

    if not limited:
        return ToolResult(content="No matches found.", data={"matches": []})

    content = "\n".join(limited)
    return ToolResult(
        content=content,
        data={
            "matches": limited,
            "truncated": len(matches) > len(limited),
        },
    )


def _grep_files(params: dict, context: ToolContext) -> ToolResult:
    pattern = params["pattern"]
    include = params.get("include", "**/*")
    case_sensitive = params.get("case_sensitive", False)
    max_results = min(params.get("max_results", context.settings.max_grep_results), context.settings.max_grep_results)

    try:
        regex = re.compile(pattern, 0 if case_sensitive else re.IGNORECASE)
    except re.error as exc:
        raise ToolError(f"Invalid regex pattern: {exc}") from exc

    matches: list[str] = []
    root = context.settings.workspace_root
    for path in root.rglob("*"):
        if len(matches) >= max_results:
            break
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if not fnmatch.fnmatch(rel, include) and include != "**/*":
            continue
        if _is_binary(path):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for line_no, line in enumerate(text.splitlines(), start=1):
            if regex.search(line):
                matches.append(f"{rel}:{line_no}: {line}")
                if len(matches) >= max_results:
                    break

    if not matches:
        return ToolResult(content="No matches found.", data={"matches": []})

    return ToolResult(
        content="\n".join(matches),
        data={
            "matches": matches,
            "truncated": len(matches) >= max_results,
        },
    )


def _is_binary(path: Path) -> bool:
    raw = path.read_bytes()[:1024]
    return b"\x00" in raw
