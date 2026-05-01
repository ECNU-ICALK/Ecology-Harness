from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ToolCall":
        if not isinstance(payload, dict):
            payload = {}
        return cls(
            id=str(payload.get("id", "")),
            name=str(payload.get("name", "")),
            arguments=_coerce_arguments(payload.get("arguments")),
        )

    def to_openai_dict(self) -> dict[str, Any]:
        import json

        return {
            "id": self.id,
            "type": "function",
            "function": {
                "name": self.name,
                "arguments": json.dumps(self.arguments, ensure_ascii=False),
            },
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "arguments": self.arguments,
        }


@dataclass
class MessagePart:
    type: str
    text: str = ""
    path: str = ""
    mime_type: str = ""
    name: str = ""
    size_bytes: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def text_part(cls, text: str) -> "MessagePart":
        return cls(type="text", text=text)

    @classmethod
    def image_part(
        cls,
        path: str,
        mime_type: str,
        name: str = "",
        size_bytes: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> "MessagePart":
        return cls(
            type="image",
            path=path,
            mime_type=mime_type,
            name=name,
            size_bytes=size_bytes,
            metadata=dict(metadata or {}),
        )

    @classmethod
    def audio_part(
        cls,
        path: str,
        mime_type: str,
        name: str = "",
        size_bytes: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> "MessagePart":
        return cls(
            type="audio",
            path=path,
            mime_type=mime_type,
            name=name,
            size_bytes=size_bytes,
            metadata=dict(metadata or {}),
        )

    @classmethod
    def video_part(
        cls,
        path: str,
        mime_type: str,
        name: str = "",
        size_bytes: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> "MessagePart":
        return cls(
            type="video",
            path=path,
            mime_type=mime_type,
            name=name,
            size_bytes=size_bytes,
            metadata=dict(metadata or {}),
        )

    @classmethod
    def document_part(
        cls,
        path: str,
        mime_type: str,
        text: str,
        name: str = "",
        size_bytes: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> "MessagePart":
        return cls(
            type="document",
            path=path,
            mime_type=mime_type,
            text=text,
            name=name,
            size_bytes=size_bytes,
            metadata=dict(metadata or {}),
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MessagePart":
        if not isinstance(payload, dict):
            payload = {}
        return cls(
            type=str(payload.get("type", "")),
            text=str(payload.get("text", "")),
            path=str(payload.get("path", "")),
            mime_type=str(payload.get("mime_type", "")),
            name=str(payload.get("name", "")),
            size_bytes=_coerce_int(payload.get("size_bytes"), default=0),
            metadata=_coerce_dict(payload.get("metadata")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "text": self.text,
            "path": self.path,
            "mime_type": self.mime_type,
            "name": self.name,
            "size_bytes": self.size_bytes,
            "metadata": self.metadata,
        }

    def label(self) -> str:
        if self.name:
            return self.name
        if self.path:
            return Path(self.path).name
        return self.type

    def plain_text(self) -> str:
        if self.type == "text":
            return self.text
        if self.type == "document":
            header = "[Attached document: %s]" % self.label()
            if self.text:
                return "%s\n%s" % (header, self.text)
            return header
        if self.type == "image":
            return "[Attached image: %s]" % self.label()
        if self.type == "audio":
            detail = _format_media_metadata(self.metadata)
            if detail:
                return "[Attached audio: %s | %s]" % (self.label(), detail)
            return "[Attached audio: %s]" % self.label()
        if self.type == "video":
            detail = _format_media_metadata(self.metadata)
            if detail:
                return "[Attached video: %s | %s]" % (self.label(), detail)
            return "[Attached video: %s]" % self.label()
        return self.text or ""

    def summary_text(self, max_document_chars: int = 400) -> str:
        if self.type == "document":
            header = "[Attached document: %s]" % self.label()
            body = (self.text or "").strip()
            if not body:
                return header
            if len(body) > max_document_chars:
                body = body[:max_document_chars].rstrip() + "..."
            return "%s %s" % (header, body)
        if self.type == "image":
            return "[Attached image: %s]" % self.label()
        if self.type == "audio":
            return self.plain_text()
        if self.type == "video":
            return self.plain_text()
        return self.text


@dataclass
class ChatMessage:
    role: str
    content: str
    name: str = ""
    tool_call_id: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    content_parts: list[MessagePart] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ChatMessage":
        if not isinstance(payload, dict):
            payload = {}
        raw_tool_calls = payload.get("tool_calls", [])
        if not isinstance(raw_tool_calls, list):
            raw_tool_calls = []
        tool_calls = [ToolCall.from_dict(item) for item in raw_tool_calls]
        raw_content_parts = payload.get("content_parts", [])
        if not isinstance(raw_content_parts, list):
            raw_content_parts = []
        content_parts = [
            MessagePart.from_dict(item)
            for item in raw_content_parts
            if isinstance(item, dict)
        ]
        return cls(
            role=str(payload.get("role", "")),
            content=str(payload.get("content", "")),
            name=str(payload.get("name", "")),
            tool_call_id=str(payload.get("tool_call_id", "")),
            tool_calls=tool_calls,
            content_parts=content_parts,
        )

    def content_text(self) -> str:
        if not self.content_parts:
            return self.content
        rendered = [item.plain_text() for item in self.content_parts if item.plain_text()]
        if not rendered and self.content:
            return self.content
        return "\n\n".join(rendered)

    def summary_text(self, max_document_chars: int = 400) -> str:
        if not self.content_parts:
            return self.content
        rendered = [
            item.summary_text(max_document_chars=max_document_chars)
            for item in self.content_parts
            if item.summary_text(max_document_chars=max_document_chars)
        ]
        if not rendered and self.content:
            return self.content
        return "\n\n".join(rendered)

    def attachment_labels(self) -> list[str]:
        labels = []
        for part in self.content_parts:
            if part.type in {"image", "document"}:
                labels.append(part.label())
        return labels

    def to_openai_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "role": self.role,
            "content": self.content_text(),
        }
        if self.name:
            payload["name"] = self.name
        if self.role == "assistant" and self.tool_calls:
            payload["tool_calls"] = [item.to_openai_dict() for item in self.tool_calls]
        if self.role == "tool" and self.tool_call_id:
            payload["tool_call_id"] = self.tool_call_id
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "name": self.name,
            "tool_call_id": self.tool_call_id,
            "tool_calls": [item.to_dict() for item in self.tool_calls],
            "content_parts": [item.to_dict() for item in self.content_parts],
        }


@dataclass
class ModelResponse:
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


def _format_media_metadata(metadata: dict[str, Any]) -> str:
    parts = []
    duration = metadata.get("duration_seconds")
    if isinstance(duration, (int, float)) and duration > 0:
        parts.append("duration=%.2fs" % duration)
    frames = metadata.get("sampled_frames")
    if isinstance(frames, int) and frames > 0:
        parts.append("frames=%s" % frames)
    fps = metadata.get("fps")
    if isinstance(fps, (int, float)) and fps > 0:
        parts.append("fps=%.2f" % fps)
    return ", ".join(parts)


def _coerce_arguments(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, dict):
            return dict(parsed)
    return {}


def _coerce_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def _coerce_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
