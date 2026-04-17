from __future__ import annotations

import json

from ecology_harness.tools.base import ToolContext, ToolDefinition, ToolError, ToolResult
from ecology_harness.tools.registry import ToolRegistry


def register_integration_tools(registry: ToolRegistry) -> None:
    registry.register(
        ToolDefinition(
            name="IntegrationList",
            description="List configured external integrations such as Feishu webhooks.",
            input_schema={"type": "object", "properties": {}},
            handler=_integration_list,
            read_only=True,
            concurrent_safe=True,
        )
    )
    registry.register(
        ToolDefinition(
            name="FeishuNotify",
            description="Send a message to a configured Feishu or Lark webhook integration.",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "text": {"type": "string"},
                    "title": {"type": "string"},
                },
                "required": ["name", "text"],
            },
            handler=_feishu_notify,
            read_only=False,
            concurrent_safe=False,
        )
    )


def _integration_list(params: dict, context: ToolContext) -> ToolResult:
    del params
    manager = context.services.get("integration_manager")
    if manager is None:
        raise ToolError("integration_manager service is unavailable.")
    payload = manager.list_integrations()
    if not payload:
        return ToolResult(content="No integrations configured.", data={"integrations": []})
    lines = [
        "- %(name)s (%(kind)s, %(status)s, enabled=%(enabled)s)"
        % {
            "name": item["name"],
            "kind": item["kind"],
            "status": item["status"],
            "enabled": item["enabled"],
        }
        for item in payload
    ]
    return ToolResult(content="\n".join(lines), data={"integrations": payload})


def _feishu_notify(params: dict, context: ToolContext) -> ToolResult:
    manager = context.services.get("integration_manager")
    if manager is None:
        raise ToolError("integration_manager service is unavailable.")
    try:
        result = manager.send_feishu_message(
            name=str(params.get("name", "") or ""),
            text=str(params.get("text", "") or ""),
            title=str(params.get("title", "") or ""),
        )
    except ValueError as exc:
        raise ToolError(str(exc)) from exc
    content = {
        "integration": result["integration"]["name"],
        "status_code": result["status_code"],
        "sent_at": result["sent_at"],
        "title": result["title"],
    }
    return ToolResult(
        content=json.dumps(content, ensure_ascii=False, indent=2),
        data=result,
    )
