from __future__ import annotations

import json
import queue
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

from ecology_harness import __version__
from ecology_harness.tools import ToolError


def call_stdio_jsonrpc(
    *,
    executable: str,
    args: list[str],
    cwd: Path,
    env: dict[str, str],
    method: str,
    params: dict[str, Any],
    timeout_sec: int,
) -> dict[str, Any]:
    proc: subprocess.Popen[str] | None = None
    messages: queue.Queue[dict[str, Any] | tuple[str, str]] = queue.Queue()
    stderr_lines: list[str] = []
    try:
        proc = subprocess.Popen(
            [executable, *args],
            cwd=str(cwd),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=env,
        )
        _start_stdio_reader(proc, messages, stderr_lines)
        next_id = 1
        _stdio_send(
            proc,
            {
                "jsonrpc": "2.0",
                "id": next_id,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "ecology-harness", "version": __version__},
                },
            },
        )
        _stdio_wait_response(proc, messages, next_id, timeout_sec, stderr_lines)
        _stdio_send(
            proc,
            {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {},
            },
        )
        next_id += 1
        _stdio_send(
            proc,
            {
                "jsonrpc": "2.0",
                "id": next_id,
                "method": method,
                "params": params,
            },
        )
        return _stdio_wait_response(proc, messages, next_id, timeout_sec, stderr_lines)
    finally:
        if proc is not None:
            _terminate_stdio_process(proc)


def format_stdio_content(result: dict[str, Any]) -> str:
    blocks = result.get("content")
    if not isinstance(blocks, list):
        return ""
    lines: list[str] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text" and block.get("text") is not None:
            lines.append(str(block["text"]))
        elif block.get("type") == "resource" and isinstance(block.get("resource"), dict):
            resource = block["resource"]
            if resource.get("text") is not None:
                lines.append(str(resource["text"]))
        elif block:
            lines.append(json.dumps(block, ensure_ascii=False))
    return "\n".join(lines).strip()


def format_stdio_resource_result(result: dict[str, Any]) -> str:
    contents = result.get("contents")
    if not isinstance(contents, list):
        return json.dumps(result, ensure_ascii=False, indent=2)
    lines: list[str] = []
    for item in contents:
        if not isinstance(item, dict):
            continue
        if item.get("text") is not None:
            lines.append(str(item["text"]))
        elif item.get("blob") is not None:
            lines.append(str(item["blob"]))
    return "\n".join(lines).strip() or json.dumps(result, ensure_ascii=False, indent=2)


def _start_stdio_reader(
    proc: subprocess.Popen[str],
    messages: queue.Queue[dict[str, Any] | tuple[str, str]],
    stderr_lines: list[str],
) -> None:
    def _read_stdout() -> None:
        assert proc.stdout is not None
        for line in proc.stdout:
            text = line.strip()
            if not text:
                continue
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                messages.put(("stdout", text))
                continue
            if isinstance(payload, dict):
                messages.put(payload)

    def _read_stderr() -> None:
        assert proc.stderr is not None
        for line in proc.stderr:
            text = line.strip()
            if text:
                stderr_lines.append(text)

    threading.Thread(target=_read_stdout, daemon=True).start()
    threading.Thread(target=_read_stderr, daemon=True).start()


def _stdio_send(proc: subprocess.Popen[str], payload: dict[str, Any]) -> None:
    if proc.stdin is None:
        raise ToolError("MCP stdio process stdin is unavailable.")
    proc.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
    proc.stdin.flush()


def _stdio_wait_response(
    proc: subprocess.Popen[str],
    messages: queue.Queue[dict[str, Any] | tuple[str, str]],
    request_id: int,
    timeout_sec: int,
    stderr_lines: list[str],
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_sec
    process_exited = False
    while time.monotonic() < deadline:
        if proc.poll() is not None and messages.empty():
            process_exited = True
            break
        remaining = max(deadline - time.monotonic(), 0.01)
        try:
            message = messages.get(timeout=min(0.1, remaining))
        except queue.Empty:
            continue
        if isinstance(message, tuple):
            continue
        if message.get("id") != request_id:
            continue
        if "error" in message:
            error_payload = message.get("error", {})
            if isinstance(error_payload, dict):
                raise ToolError(str(error_payload.get("message") or error_payload))
            raise ToolError(str(error_payload))
        result = message.get("result")
        return result if isinstance(result, dict) else {"result": result}
    detail = ""
    if stderr_lines:
        detail = " stderr=%s" % " | ".join(stderr_lines[-3:])
    if process_exited:
        raise ToolError("MCP stdio process exited before response id=%s.%s" % (request_id, detail))
    raise ToolError("MCP stdio request timed out after %ss.%s" % (timeout_sec, detail))


def _terminate_stdio_process(proc: subprocess.Popen[str]) -> None:
    try:
        if proc.stdin is not None and not proc.stdin.closed:
            proc.stdin.close()
    except Exception:
        pass
    try:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=1)
    except Exception:
        pass
    finally:
        for stream in (proc.stdout, proc.stderr):
            try:
                if stream is not None and not stream.closed:
                    stream.close()
            except Exception:
                pass
