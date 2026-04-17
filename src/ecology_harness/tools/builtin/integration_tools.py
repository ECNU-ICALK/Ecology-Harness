from __future__ import annotations

import json

from ecology_harness.tools.base import ToolContext, ToolDefinition, ToolError, ToolResult
from ecology_harness.tools.registry import ToolRegistry


def register_integration_tools(registry: ToolRegistry) -> None:
    registry.register(
        ToolDefinition(
            name="IntegrationList",
            description="List configured external integrations such as Feishu, DingTalk, or WeCom webhooks.",
            input_schema={"type": "object", "properties": {}},
            handler=_integration_list,
            read_only=True,
            concurrent_safe=True,
        )
    )
    registry.register(
        ToolDefinition(
            name="IntegrationNotify",
            description="Send a message to a configured external integration.",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "text": {"type": "string"},
                    "title": {"type": "string"},
                },
                "required": ["name", "text"],
            },
            handler=_integration_notify,
            read_only=False,
            concurrent_safe=False,
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
    registry.register(
        ToolDefinition(
            name="DingTalkNotify",
            description="Send a message to a configured DingTalk webhook integration.",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "text": {"type": "string"},
                    "title": {"type": "string"},
                },
                "required": ["name", "text"],
            },
            handler=_dingtalk_notify,
            read_only=False,
            concurrent_safe=False,
        )
    )
    registry.register(
        ToolDefinition(
            name="WeComNotify",
            description="Send a message to a configured WeCom webhook integration.",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "text": {"type": "string"},
                    "title": {"type": "string"},
                },
                "required": ["name", "text"],
            },
            handler=_wecom_notify,
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
    return _render_notify_result(result)


def _integration_notify(params: dict, context: ToolContext) -> ToolResult:
    manager = context.services.get("integration_manager")
    if manager is None:
        raise ToolError("integration_manager service is unavailable.")
    try:
        result = manager.send_message(
            name=str(params.get("name", "") or ""),
            text=str(params.get("text", "") or ""),
            title=str(params.get("title", "") or ""),
        )
    except ValueError as exc:
        raise ToolError(str(exc)) from exc
    return _render_notify_result(result)


def _dingtalk_notify(params: dict, context: ToolContext) -> ToolResult:
    return _notify_with_expected_kind(params, context, expected_kind="dingtalk-webhook")


def _wecom_notify(params: dict, context: ToolContext) -> ToolResult:
    return _notify_with_expected_kind(params, context, expected_kind="wecom-webhook")


def _render_notify_result(result: dict) -> ToolResult:
    content = {
        "integration": result["integration"]["name"],
        "kind": result["integration"]["kind"],
        "status_code": result["status_code"],
        "sent_at": result["sent_at"],
        "title": result["title"],
    }
    return ToolResult(content=json.dumps(content, ensure_ascii=False, indent=2), data=result)


def _notify_with_expected_kind(params: dict, context: ToolContext, *, expected_kind: str) -> ToolResult:
    manager = context.services.get("integration_manager")
    if manager is None:
        raise ToolError("integration_manager service is unavailable.")
    item = manager.get_integration(str(params.get("name", "") or ""))
    if item is None:
        raise ToolError("Unknown integration: %s" % str(params.get("name", "") or ""))
    if item["kind"] != expected_kind:
        raise ToolError("Configured integration is not a %s integration." % expected_kind)
    return _integration_notify(params, context)
