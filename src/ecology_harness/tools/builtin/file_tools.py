from __future__ import annotations

from pathlib import Path

from ecology_harness.tools.base import ToolContext, ToolDefinition, ToolError, ToolResult
from ecology_harness.tools.registry import ToolRegistry


def register_file_tools(registry: ToolRegistry) -> None:
    registry.register(
        ToolDefinition(
            name="Read",
            description="Read a UTF-8 text file inside the workspace with optional line slicing.",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "start_line": {"type": "integer"},
                    "end_line": {"type": "integer"},
                },
                "required": ["path"],
            },
            handler=_read_file,
            read_only=True,
            concurrent_safe=True,
        )
    )
    registry.register(
        ToolDefinition(
            name="Write",
            description="Write a UTF-8 text file inside the workspace.",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                    "append": {"type": "boolean"},
                },
                "required": ["path", "content"],
            },
            handler=_write_file,
            read_only=False,
            concurrent_safe=False,
        )
    )
    registry.register(
        ToolDefinition(
            name="Edit",
            description="Replace text in a file inside the workspace.",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "old_text": {"type": "string"},
                    "new_text": {"type": "string"},
                    "replace_all": {"type": "boolean"},
                },
                "required": ["path", "old_text", "new_text"],
            },
            handler=_edit_file,
            read_only=False,
            concurrent_safe=False,
        )
    )


def _read_file(params: dict, context: ToolContext) -> ToolResult:
    path = _resolve_workspace_path(context, params["path"], access="read")
    if not path.exists():
        raise ToolError(f"File does not exist: {params['path']}")
    if not path.is_file():
        raise ToolError(f"Path is not a file: {params['path']}")

    if path.stat().st_size > context.settings.max_read_bytes:
        raise ToolError(
            f"File exceeds max_read_bytes={context.settings.max_read_bytes}: {params['path']}"
        )

    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    start_line = max(params.get("start_line", 1), 1)
    end_line = params.get("end_line", len(lines))
    if end_line < start_line:
        raise ToolError("end_line must be greater than or equal to start_line.")

    selected = lines[start_line - 1 : end_line]
    rendered = "\n".join(
        f"{line_no:>4}: {line}"
        for line_no, line in enumerate(selected, start=start_line)
    )

    relative_path = path.relative_to(context.settings.workspace_root).as_posix()
    content = rendered if rendered else "(file is empty)"
    return ToolResult(
        content=f"==> {relative_path} <==\n{content}",
        data={
            "path": relative_path,
            "start_line": start_line,
            "end_line": min(end_line, len(lines)),
            "line_count": len(lines),
        },
    )


def _write_file(params: dict, context: ToolContext) -> ToolResult:
    path = _resolve_workspace_path(context, params["path"], access="write")
    path.parent.mkdir(parents=True, exist_ok=True)
    content = params["content"]
    if len(content.encode("utf-8")) > context.settings.max_write_bytes:
        raise ToolError(
            "Content exceeds max_write_bytes=%s." % context.settings.max_write_bytes
        )
    append = params.get("append", False)
    mode = "a" if append else "w"
    with path.open(mode, encoding="utf-8") as handle:
        handle.write(content)
    relative_path = path.relative_to(context.settings.workspace_root).as_posix()
    action = "Appended to" if append else "Wrote"
    return ToolResult(
        content="%s %s" % (action, relative_path),
        data={"path": relative_path, "append": append, "bytes": len(content.encode("utf-8"))},
    )


def _edit_file(params: dict, context: ToolContext) -> ToolResult:
    path = _resolve_workspace_path(context, params["path"], access="write")
    if not path.exists():
        raise ToolError("File does not exist: %s" % params["path"])
    text = path.read_text(encoding="utf-8", errors="replace")
    old_text = params["old_text"]
    new_text = params["new_text"]
    replace_all = params.get("replace_all", False)
    occurrences = text.count(old_text)
    if occurrences == 0:
        raise ToolError("old_text was not found in %s" % params["path"])
    if occurrences > 1 and not replace_all:
        raise ToolError(
            "old_text matched %s occurrences. Set replace_all=true to replace all."
            % occurrences
        )
    updated = text.replace(old_text, new_text) if replace_all else text.replace(old_text, new_text, 1)
    path.write_text(updated, encoding="utf-8")
    relative_path = path.relative_to(context.settings.workspace_root).as_posix()
    return ToolResult(
        content="Edited %s" % relative_path,
        data={"path": relative_path, "occurrences": occurrences, "replace_all": replace_all},
    )


def _resolve_workspace_path(context: ToolContext, raw_path: str, access: str) -> Path:
    sandbox = context.services.get("sandbox")
    if sandbox is not None:
        try:
            return sandbox.resolve_path(raw_path, access=access)
        except Exception as exc:
            raise ToolError(str(exc)) from exc

    workspace_root = context.settings.workspace_root
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = workspace_root / candidate
    candidate = candidate.resolve()
    try:
        candidate.relative_to(workspace_root.resolve())
    except ValueError as exc:
        raise ToolError(f"Path escapes workspace: {raw_path}") from exc
    return candidate
