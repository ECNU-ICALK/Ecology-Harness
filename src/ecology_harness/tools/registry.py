from __future__ import annotations

from typing import Any

from ecology_harness.config import HarnessSettings
from ecology_harness.tools.base import ToolContext, ToolDefinition, ToolError, ToolResult


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def list_tools(self) -> list[ToolDefinition]:
        return sorted(self._tools.values(), key=lambda item: item.name.lower())

    def execute(
        self,
        name: str,
        params: dict[str, Any],
        settings: HarnessSettings,
        services: dict[str, Any] | None = None,
    ) -> ToolResult:
        tool = self.get(name)
        if tool is None:
            raise ToolError(f"Unknown tool: {name}")
        if not isinstance(params, dict):
            raise ToolError("Tool parameters must be a JSON object.")
        self._validate(tool, params)
        return tool.handler(params, ToolContext(settings=settings, services=services or {}))

    def _validate(self, tool: ToolDefinition, params: dict[str, Any]) -> None:
        schema = tool.input_schema
        if schema.get("type") != "object":
            raise ToolError(f"Tool {tool.name} has an invalid input schema.")

        required = schema.get("required", [])
        for key in required:
            if key not in params:
                raise ToolError(f"Missing required parameter '{key}' for tool {tool.name}.")

        properties = schema.get("properties", {})
        for key, value in params.items():
            expected = properties.get(key, {}).get("type")
            if expected is None:
                continue
            if not _matches_type(value, expected):
                raise ToolError(
                    f"Parameter '{key}' for tool {tool.name} must be of type {expected}."
                )


def _matches_type(value: Any, expected: str) -> bool:
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "number":
        return (isinstance(value, int) or isinstance(value, float)) and not isinstance(
            value, bool
        )
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, dict)
    return True
