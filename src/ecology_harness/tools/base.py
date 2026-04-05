from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from ecology_harness.config import HarnessSettings


class ToolError(Exception):
    """Base exception for tool validation and execution errors."""


@dataclass
class ToolContext:
    settings: HarnessSettings
    services: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResult:
    content: str
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "data": self.data,
        }


ToolHandler = Callable[[dict[str, Any], ToolContext], ToolResult]


@dataclass
class ToolDefinition:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: ToolHandler
    read_only: bool = True
    concurrent_safe: bool = True
    source: str = "native"
    origin: str = ""
    tags: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "read_only": self.read_only,
            "concurrent_safe": self.concurrent_safe,
            "source": self.source,
            "origin": self.origin,
            "tags": list(self.tags),
        }
