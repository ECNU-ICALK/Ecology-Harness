from __future__ import annotations

from ecology_harness.tools.base import ToolContext, ToolDefinition, ToolError, ToolResult
from ecology_harness.tools.registry import ToolRegistry


def register_plugin_tools(registry: ToolRegistry) -> None:
    registry.register(
        ToolDefinition(
            name="PluginList",
            description="List installed plugins, lifecycle state, and declared capabilities.",
            input_schema={"type": "object", "properties": {}},
            handler=_plugin_list,
            read_only=True,
            concurrent_safe=True,
            source="plugin",
        )
    )
    registry.register(
        ToolDefinition(
            name="PluginRead",
            description="Inspect one plugin manifest by slug or name.",
            input_schema={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
            handler=_plugin_read,
            read_only=True,
            concurrent_safe=True,
            source="plugin",
        )
    )


def _manager(context: ToolContext):
    manager = context.services.get("plugin_manager")
    if manager is None:
        raise ToolError("plugin_manager service is unavailable.")
    return manager


def _plugin_list(params: dict, context: ToolContext) -> ToolResult:
    del params
    manager = _manager(context)
    plugin_rows = {item.slug: item.to_index_dict() for item in manager.list_plugins()}
    states = {item.slug: item.to_dict() for item in manager.list_runtime_states()}
    merged = []
    for slug, item in plugin_rows.items():
        state = states.get(slug, {})
        merged.append(
            {
                **item,
                "enabled": state.get("enabled", item.get("default_enabled", False)),
                "status": state.get("status", "healthy"),
                "last_error": state.get("last_error", ""),
            }
        )
    if not merged:
        return ToolResult(content="No plugins available.", data={"plugins": []})
    lines = []
    for item in merged:
        lines.append(
            "%(slug)s\t%(source)s\t%(status)s\tenabled=%(enabled)s\t%(description)s" % item
        )
    return ToolResult(content="\n".join(lines), data={"plugins": merged})


def _plugin_read(params: dict, context: ToolContext) -> ToolResult:
    plugin = _manager(context).get(params["name"])
    if plugin is None:
        raise ToolError("Plugin not found: %s" % params["name"])
    lines = [
        "name: %s" % plugin.name,
        "slug: %s" % plugin.slug,
        "version: %s" % plugin.version,
        "source: %s" % plugin.source,
        "default_enabled: %s" % plugin.default_enabled,
        "root: %s" % plugin.root,
        "manifest_path: %s" % plugin.manifest_path,
        "description: %s" % plugin.description,
        "tools: %s" % (", ".join(plugin.tools) or "-"),
        "skills: %s" % (", ".join(plugin.skills) or "-"),
        "mcp_servers: %s" % (", ".join(plugin.mcp_servers) or "-"),
        "hooks:",
    ]
    if plugin.hooks:
        for event_name, scripts in plugin.hooks.items():
            lines.append("  %s: %s" % (event_name, ", ".join(scripts)))
    else:
        lines.append("  -")
    return ToolResult(content="\n".join(lines), data=plugin.to_index_dict())
