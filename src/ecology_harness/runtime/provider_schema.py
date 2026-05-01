from __future__ import annotations

import copy
from typing import Any

from ecology_harness.tools import ToolDefinition


def normalized_tool_schema(schema: Any) -> dict[str, Any]:
    """Return a provider-safe JSON schema for tool parameters."""

    if not isinstance(schema, dict):
        return {"type": "object", "properties": {}}

    normalized: dict[str, Any] = copy.deepcopy(schema)
    schema_type = str(normalized.get("type", "") or "").strip().lower()

    if schema_type == "object":
        properties = normalized.get("properties")
        if not isinstance(properties, dict):
            properties = {}
        normalized["properties"] = {
            str(name): normalized_tool_schema(value)
            if isinstance(value, dict)
            else {"type": "string"}
            for name, value in properties.items()
        }
        additional = normalized.get("additionalProperties")
        if isinstance(additional, dict):
            normalized["additionalProperties"] = normalized_tool_schema(additional)
    elif schema_type == "array":
        items = normalized.get("items")
        if isinstance(items, dict) and items:
            normalized["items"] = normalized_tool_schema(items)
        else:
            normalized["items"] = {"type": "string"}

    for key in ("allOf", "anyOf", "oneOf"):
        value = normalized.get(key)
        if isinstance(value, list):
            normalized[key] = [
                normalized_tool_schema(item) if isinstance(item, dict) else {"type": "string"}
                for item in value
            ]
    return normalized


def tool_parameters_schema(tool: ToolDefinition) -> dict[str, Any]:
    return normalized_tool_schema(tool.input_schema)
