from __future__ import annotations

from typing import Any

from ecology_harness.config import HarnessSettings
from ecology_harness.tools.base import ToolContext, ToolDefinition, ToolError, ToolResult


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        existing = self._tools.get(tool.name)
        if existing is not None:
            raise ValueError(
                "Tool `%s` is already registered (existing source=%s, new source=%s)."
                % (
                    tool.name,
                    existing.source or "builtin",
                    tool.source or "builtin",
                )
            )
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
        _validate_schema_value(tool.name, params, schema, "parameters")


def _validate_schema_value(
    tool_name: str,
    value: Any,
    schema: dict[str, Any],
    path: str,
) -> None:
    expected = schema.get("type")
    expected_types = _normalize_types(expected)
    if expected_types and not any(_matches_type(value, item) for item in expected_types):
        raise ToolError(
            "Parameter '%s' for tool %s must be of type %s."
            % (path, tool_name, _format_expected_types(expected_types))
        )
    if "enum" in schema and value not in schema.get("enum", []):
        raise ToolError(
            "Parameter '%s' for tool %s must be one of: %s."
            % (path, tool_name, ", ".join(str(item) for item in schema.get("enum", [])))
        )
    if isinstance(value, dict):
        _validate_object_value(tool_name, value, schema, path)
    elif isinstance(value, list):
        _validate_array_value(tool_name, value, schema, path)


def _validate_object_value(
    tool_name: str,
    value: dict[str, Any],
    schema: dict[str, Any],
    path: str,
) -> None:
    required = schema.get("required", [])
    if not isinstance(required, list):
        raise ToolError("Tool %s has an invalid required list at '%s'." % (tool_name, path))
    for key in required:
        if key not in value:
            raise ToolError("Missing required parameter '%s' for tool %s." % (_join_path(path, key), tool_name))

    properties = schema.get("properties", {})
    if properties and not isinstance(properties, dict):
        raise ToolError("Tool %s has invalid properties at '%s'." % (tool_name, path))
    additional = schema.get("additionalProperties", True)
    for key, child_value in value.items():
        child_path = _join_path(path, key)
        child_schema = properties.get(key) if isinstance(properties, dict) else None
        if isinstance(child_schema, dict):
            _validate_schema_value(tool_name, child_value, child_schema, child_path)
            continue
        if additional is False:
            raise ToolError("Unknown parameter '%s' for tool %s." % (child_path, tool_name))
        if isinstance(additional, dict):
            _validate_schema_value(tool_name, child_value, additional, child_path)


def _validate_array_value(
    tool_name: str,
    value: list[Any],
    schema: dict[str, Any],
    path: str,
) -> None:
    item_schema = schema.get("items")
    if item_schema is None:
        return
    if not isinstance(item_schema, dict):
        raise ToolError("Tool %s has invalid array item schema at '%s'." % (tool_name, path))
    for index, item in enumerate(value):
        _validate_schema_value(tool_name, item, item_schema, "%s[%s]" % (path, index))


def _normalize_types(expected: Any) -> list[str]:
    if isinstance(expected, str):
        return [expected]
    if isinstance(expected, list):
        return [item for item in expected if isinstance(item, str)]
    return []


def _format_expected_types(expected: list[str]) -> str:
    return " or ".join(expected)


def _join_path(parent: str, key: object) -> str:
    return "%s.%s" % (parent, key) if parent else str(key)


def _matches_type(value: Any, expected: str) -> bool:
    if expected == "null":
        return value is None
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
