from __future__ import annotations

import json
import os
from pathlib import Path
import py_compile
import subprocess
import sys

from ecology_harness.tools.base import ToolContext, ToolDefinition, ToolError, ToolResult
from ecology_harness.tools.registry import ToolRegistry
from ecology_harness.utils import atomic_write_text


def register_system_tools(registry: ToolRegistry) -> None:
    registry.register(
        ToolDefinition(
            name="Bash",
            description="Run a shell command in the workspace.",
            input_schema={
                "type": "object",
                "properties": {
                    "command": {"type": "string"},
                    "cwd": {"type": "string"},
                    "timeout_sec": {"type": "integer"},
                },
                "required": ["command"],
            },
            handler=_bash,
            read_only=False,
            concurrent_safe=False,
        )
    )
    registry.register(
        ToolDefinition(
            name="GetDiagnostics",
            description="Run lightweight diagnostics for Python, JSON, shell, and notebook files.",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                },
                "required": ["path"],
            },
            handler=_get_diagnostics,
            read_only=True,
            concurrent_safe=True,
        )
    )
    registry.register(
        ToolDefinition(
            name="NotebookEdit",
            description="Replace, insert, or delete a Jupyter notebook cell.",
            input_schema={
                "type": "object",
                "properties": {
                    "notebook_path": {"type": "string"},
                    "action": {"type": "string"},
                    "cell_id": {"type": "string"},
                    "new_source": {"type": "string"},
                    "cell_type": {"type": "string"},
                },
                "required": ["notebook_path", "action"],
            },
            handler=_notebook_edit,
            read_only=False,
            concurrent_safe=False,
        )
    )
    registry.register(
        ToolDefinition(
            name="SandboxStatus",
            description="Describe the active sandbox backend and allowed roots.",
            input_schema={"type": "object", "properties": {}},
            handler=_sandbox_status,
            read_only=True,
            concurrent_safe=True,
        )
    )


def _bash(params: dict, context: ToolContext) -> ToolResult:
    command = params["command"]
    cwd = params.get("cwd")
    timeout = params.get("timeout_sec", context.settings.command_timeout_sec)
    sandbox = context.services.get("sandbox")
    shell_env = _build_runtime_shell_env()
    try:
        if sandbox is not None:
            completed = sandbox.run_shell(command, cwd=cwd, timeout_sec=timeout, env=shell_env)
        else:
            completed = subprocess.run(
                command,
                cwd=str(Path(cwd).expanduser().resolve()) if cwd else str(context.settings.workspace_root),
                shell=True,
                executable="/bin/bash",
                capture_output=True,
                text=True,
                timeout=timeout,
                env=shell_env,
            )
    except subprocess.TimeoutExpired as exc:
        raise ToolError("Command timed out after %ss" % timeout) from exc
    except Exception as exc:
        raise ToolError(str(exc)) from exc

    combined = (completed.stdout or "") + (completed.stderr or "")
    truncated = False
    if len(combined) > context.settings.max_command_output:
        combined = combined[: context.settings.max_command_output]
        truncated = True

    content = combined.strip() or "(no output)"
    if truncated:
        content += "\n[output truncated]"

    return ToolResult(
        content=content,
        data={
            "command": command,
            "cwd": cwd or str(context.settings.workspace_root),
            "returncode": completed.returncode,
            "truncated": truncated,
            "python_executable": shell_env.get("ECOLOGY_HARNESS_RUNTIME_PYTHON", ""),
        },
    )


def _build_runtime_shell_env() -> dict[str, str]:
    env = dict(os.environ)
    python_executable = str(Path(sys.executable).resolve())
    python_bin = str(Path(python_executable).parent)
    existing_path = env.get("PATH", "")
    path_parts = [part for part in existing_path.split(os.pathsep) if part]
    if python_bin not in path_parts:
        env["PATH"] = os.pathsep.join([python_bin, *path_parts]) if path_parts else python_bin
    env["ECOLOGY_HARNESS_RUNTIME_PYTHON"] = python_executable

    prefix = str(Path(python_executable).parent.parent)
    prefix_path = Path(prefix)
    if (prefix_path / "conda-meta").exists():
        env["CONDA_PREFIX"] = prefix
        env.setdefault("CONDA_DEFAULT_ENV", prefix_path.name)
    elif (prefix_path / "pyvenv.cfg").exists():
        env["VIRTUAL_ENV"] = prefix
    return env


def _get_diagnostics(params: dict, context: ToolContext) -> ToolResult:
    path = _resolve_path(context, params["path"], access="read")
    if not path.exists():
        raise ToolError("Path does not exist: %s" % params["path"])
    suffix = path.suffix.lower()
    diagnostics = []
    if suffix == ".py":
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            diagnostics.append(str(exc))
    elif suffix == ".json":
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            diagnostics.append("JSON error at line %s column %s: %s" % (exc.lineno, exc.colno, exc.msg))
    elif suffix in {".sh", ".bash"}:
        try:
            completed = subprocess.run(
                ["/bin/bash", "-n", str(path)],
                cwd=str(context.settings.workspace_root),
                capture_output=True,
                text=True,
                timeout=context.settings.command_timeout_sec,
            )
        except subprocess.TimeoutExpired as exc:
            raise ToolError("Shell syntax check timed out.") from exc
        if completed.returncode != 0:
            diagnostics.append((completed.stderr or completed.stdout).strip())
    elif suffix == ".ipynb":
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if "cells" not in raw:
                diagnostics.append("Notebook is missing a top-level `cells` array.")
        except json.JSONDecodeError as exc:
            diagnostics.append("Notebook JSON error at line %s column %s: %s" % (exc.lineno, exc.colno, exc.msg))
    else:
        diagnostics.append("No built-in diagnostics for `%s` files." % suffix)

    if not diagnostics:
        return ToolResult(content="No diagnostics reported.", data={"path": str(path), "diagnostics": []})
    return ToolResult(
        content="\n".join(diagnostics),
        data={"path": str(path), "diagnostics": diagnostics},
    )


def _notebook_edit(params: dict, context: ToolContext) -> ToolResult:
    path = _resolve_path(context, params["notebook_path"], access="write")
    if not path.exists():
        raise ToolError("Notebook does not exist: %s" % params["notebook_path"])
    try:
        notebook = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ToolError("Notebook JSON is invalid: %s" % exc) from exc
    cells = notebook.get("cells")
    if not isinstance(cells, list):
        raise ToolError("Notebook is missing a valid `cells` array.")

    action = params["action"]
    cell_id = params.get("cell_id", "")
    index = _resolve_cell_index(cells, cell_id) if cell_id else None

    if action == "replace":
        if index is None:
            raise ToolError("replace requires `cell_id`.")
        cells[index]["source"] = _normalize_cell_source(params.get("new_source", ""))
    elif action == "insert":
        cell = {
            "cell_type": params.get("cell_type", "code"),
            "metadata": {},
            "source": _normalize_cell_source(params.get("new_source", "")),
            "outputs": [],
            "execution_count": None,
        }
        insert_at = 0 if index is None else index + 1
        cells.insert(insert_at, cell)
    elif action == "delete":
        if index is None:
            raise ToolError("delete requires `cell_id`.")
        cells.pop(index)
    else:
        raise ToolError("Unsupported notebook action: %s" % action)

    atomic_write_text(path, json.dumps(notebook, indent=2, ensure_ascii=False), encoding="utf-8")
    return ToolResult(
        content="Notebook updated: %s" % path.relative_to(context.settings.workspace_root),
        data={"path": str(path), "action": action, "cell_count": len(cells)},
    )


def _sandbox_status(params: dict, context: ToolContext) -> ToolResult:
    del params
    sandbox = context.services.get("sandbox")
    if sandbox is None:
        raise ToolError("sandbox service is unavailable.")
    data = sandbox.describe()
    lines = [
        "enabled: %s" % data["enabled"],
        "active: %s" % data["active"],
        "backend: %s" % data["backend"],
        "mode: %s" % data["mode"],
        "allow_network: %s" % data["allow_network"],
        "read_roots:",
    ]
    lines.extend("  - %s" % item for item in data["read_roots"])
    lines.append("write_roots:")
    lines.extend("  - %s" % item for item in data["write_roots"])
    if data.get("reason"):
        lines.append("reason: %s" % data["reason"])
    return ToolResult(content="\n".join(lines), data=data)


def _resolve_path(context: ToolContext, raw_path: str, access: str) -> Path:
    sandbox = context.services.get("sandbox")
    if sandbox is not None:
        try:
            return sandbox.resolve_path(raw_path, access=access)
        except Exception as exc:
            raise ToolError(str(exc)) from exc
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = context.settings.workspace_root / candidate
    return candidate.resolve()


def _normalize_cell_source(source: str) -> list[str]:
    if not source:
        return []
    lines = source.splitlines(True)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    return lines


def _resolve_cell_index(cells: list[dict], cell_id: str) -> int:
    if cell_id.startswith("cell-") and cell_id[5:].isdigit():
        index = int(cell_id[5:])
        if 0 <= index < len(cells):
            return index
    for index, cell in enumerate(cells):
        if str(cell.get("id", "")) == cell_id:
            return index
    raise ToolError("Cell not found: %s" % cell_id)
