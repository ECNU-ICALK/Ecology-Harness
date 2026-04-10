from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from typing import Any

from ecology_harness.runtime.messages import ChatMessage


def build_chat_completion_payload(app, payload: dict[str, Any]) -> dict[str, Any]:
    model = str(payload.get("model", app.settings.model) or app.settings.model)
    incoming = payload.get("messages", []) or []
    conversation: list[ChatMessage] = []
    prompt = ""
    for item in incoming:
        role = str(item.get("role", "user") or "user")
        content = item.get("content", "")
        if isinstance(content, list):
            content = "\n".join(str(block.get("text", "")) for block in content if isinstance(block, dict))
        text = str(content or "")
        if role == "system":
            conversation.append(ChatMessage(role="system", content=text))
            continue
        if role == "user":
            if text:
                prompt = text
            conversation.append(ChatMessage(role="user", content=text))
            continue
        if role == "assistant":
            conversation.append(ChatMessage(role="assistant", content=text))
            continue
        if role == "tool":
            conversation.append(ChatMessage(role="tool", content=text))
    if not prompt:
        raise ValueError("chat/completions requires at least one user message.")
    app.settings.model = model
    result = app.run_prompt(prompt, conversation=conversation[:-1] if conversation and conversation[-1].role == "user" else conversation)
    return {
        "id": "chatcmpl-ecology-harness",
        "object": "chat.completion",
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": result.final_text},
                "finish_reason": "stop",
            }
        ],
    }


def run_api_server(app, host: str = "127.0.0.1", port: int = 8765) -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/health":
                self._json({"status": "ok", "model": app.settings.model, "provider": app.settings.provider})
                return
            if self.path == "/v1/models":
                self._json({"data": [{"id": app.settings.model, "object": "model"}]})
                return
            self.send_error(HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:  # noqa: N802
            if self.path != "/v1/chat/completions":
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            length = int(self.headers.get("Content-Length", "0") or 0)
            raw = self.rfile.read(length)
            try:
                payload = json.loads(raw.decode("utf-8") or "{}")
                response = build_chat_completion_payload(app, payload)
            except Exception as exc:
                self._json({"error": {"message": str(exc)}}, status=HTTPStatus.BAD_REQUEST)
                return
            self._json(response)

        def log_message(self, format, *args):  # noqa: A003
            del format, args

        def _json(self, payload: dict[str, Any], status: int = HTTPStatus.OK) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(int(status))
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer((host, int(port)), Handler)
    try:
        server.serve_forever()
    finally:
        server.server_close()
