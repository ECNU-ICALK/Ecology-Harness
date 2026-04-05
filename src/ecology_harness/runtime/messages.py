from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ToolCall":
        return cls(
            id=str(payload.get("id", "")),
            name=str(payload.get("name", "")),
            arguments=dict(payload.get("arguments", {}) or {}),
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
class ChatMessage:
    role: str
    content: str
    name: str = ""
    tool_call_id: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ChatMessage":
        tool_calls = [ToolCall.from_dict(item) for item in payload.get("tool_calls", [])]
        return cls(
            role=str(payload.get("role", "")),
            content=str(payload.get("content", "")),
            name=str(payload.get("name", "")),
            tool_call_id=str(payload.get("tool_call_id", "")),
            tool_calls=tool_calls,
        )

    def to_openai_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "role": self.role,
            "content": self.content,
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
        }


@dataclass
class ModelResponse:
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)
