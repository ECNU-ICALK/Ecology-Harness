from __future__ import annotations

from ecology_harness.tools.base import ToolContext, ToolDefinition, ToolError, ToolResult
from ecology_harness.tools.registry import ToolRegistry


def register_memory_tools(registry: ToolRegistry) -> None:
    registry.register(
        ToolDefinition(
            name="MemorySave",
            description="Save a persistent memory entry with type and scope.",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "content": {"type": "string"},
                    "type": {"type": "string"},
                    "scope": {"type": "string"},
                },
                "required": ["name", "description", "content"],
            },
            handler=_memory_save,
            read_only=False,
            concurrent_safe=False,
        )
    )
    registry.register(
        ToolDefinition(
            name="MemoryList",
            description="List saved memory items.",
            input_schema={
                "type": "object",
                "properties": {"scope": {"type": "string"}},
            },
            handler=_memory_list,
            read_only=True,
            concurrent_safe=True,
        )
    )
    registry.register(
        ToolDefinition(
            name="MemoryRead",
            description="Read a saved memory item by slug or name.",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "scope": {"type": "string"},
                },
                "required": ["name"],
            },
            handler=_memory_read,
            read_only=True,
            concurrent_safe=True,
        )
    )
    registry.register(
        ToolDefinition(
            name="MemoryDelete",
            description="Delete a saved memory item.",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "scope": {"type": "string"},
                },
                "required": ["name"],
            },
            handler=_memory_delete,
            read_only=False,
            concurrent_safe=False,
        )
    )
    registry.register(
        ToolDefinition(
            name="MemorySearch",
            description="Search memory items by substring.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "scope": {"type": "string"},
                    "max_results": {"type": "integer"},
                },
                "required": ["query"],
            },
            handler=_memory_search,
            read_only=True,
            concurrent_safe=True,
        )
    )


def _manager(context: ToolContext):
    manager = context.services.get("memory_manager")
    if manager is None:
        raise ToolError("memory_manager service is unavailable.")
    return manager


def _memory_save(params: dict, context: ToolContext) -> ToolResult:
    scope = params.get("scope", context.settings.memory_default_scope)
    item = _manager(context).save(
        name=params["name"],
        description=params["description"],
        content=params["content"],
        memory_type=params.get("type", "project"),
        scope=scope,
    )
    return ToolResult(
        content="Saved memory `%s` [%s/%s]." % (item.slug, item.memory_type, item.scope),
        data=item.to_index_dict(),
    )


def _memory_list(params: dict, context: ToolContext) -> ToolResult:
    scope = params.get("scope", "all")
    items = [item.to_index_dict() for item in _manager(context).list_items(scope=scope)]
    if not items:
        return ToolResult(content="No memory items found.", data={"items": []})
    manifest = _manager(context).format_manifest(scope=scope)
    content = manifest or "\n".join(["%(slug)s\t%(description)s" % item for item in items])
    return ToolResult(content=content, data={"items": items})


def _memory_read(params: dict, context: ToolContext) -> ToolResult:
    item = _manager(context).get(params["name"], scope=params.get("scope", "all"))
    if item is None:
        raise ToolError("Memory item not found: %s" % params["name"])
    return ToolResult(
        content=item.content,
        data=item.to_index_dict(),
    )


def _memory_delete(params: dict, context: ToolContext) -> ToolResult:
    deleted = _manager(context).delete(
        params["name"],
        scope=params.get("scope", context.settings.memory_default_scope),
    )
    if not deleted:
        raise ToolError("Memory item not found: %s" % params["name"])
    return ToolResult(content="Deleted memory `%s`." % params["name"], data={"deleted": True})


def _memory_search(params: dict, context: ToolContext) -> ToolResult:
    items = _manager(context).search(
        params["query"],
        scope=params.get("scope", "all"),
        max_results=params.get("max_results", 5),
    )
    if not items:
        return ToolResult(content="No memory matches found.", data={"items": []})
    lines = []
    for item in items:
        freshness = item.get("freshness_text", "")
        block = "[%(type)s/%(scope)s] %(name)s\n  %(description)s\n  %(content)s" % {
            "type": item.get("type", "project"),
            "scope": item.get("scope", "project"),
            "name": item.get("name", item.get("slug", "")),
            "description": item.get("description", ""),
            "content": item.get("content", "")[:200] + ("..." if len(item.get("content", "")) > 200 else ""),
        }
        if freshness:
            block += "\n  %s" % freshness
        lines.append(block)
    return ToolResult(content="\n".join(lines), data={"items": items})
