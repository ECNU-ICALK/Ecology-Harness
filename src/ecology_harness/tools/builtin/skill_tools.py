from __future__ import annotations

from ecology_harness.skills import execute_skill
from ecology_harness.tools.base import ToolContext, ToolDefinition, ToolError, ToolResult
from ecology_harness.tools.registry import ToolRegistry


def register_skill_tools(registry: ToolRegistry) -> None:
    registry.register(
        ToolDefinition(
            name="Skill",
            description="Execute a named skill inline or in a forked subagent.",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "args": {"type": "string"},
                },
                "required": ["name"],
            },
            handler=_skill_execute,
            read_only=False,
            concurrent_safe=False,
        )
    )
    registry.register(
        ToolDefinition(
            name="SkillList",
            description="List available skills with descriptions.",
            input_schema={"type": "object", "properties": {}},
            handler=_skill_list,
            read_only=True,
            concurrent_safe=True,
        )
    )
    registry.register(
        ToolDefinition(
            name="SkillRead",
            description="Read a skill by slug or name.",
            input_schema={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
            handler=_skill_read,
            read_only=True,
            concurrent_safe=True,
        )
    )


def _loader(context: ToolContext):
    loader = context.services.get("skill_loader")
    if loader is None:
        raise ToolError("skill_loader service is unavailable.")
    return loader


def _skill_list(params: dict, context: ToolContext) -> ToolResult:
    del params
    skills = [item.to_index_dict() for item in _loader(context).list_skills()]
    if not skills:
        return ToolResult(content="No skills available.", data={"skills": []})
    lines = ["%(slug)s\t%(description)s\t%(context)s\t%(triggers)s" % item for item in skills]
    return ToolResult(content="\n".join(lines), data={"skills": skills})


def _skill_read(params: dict, context: ToolContext) -> ToolResult:
    skill = _loader(context).get(params["name"])
    if skill is None:
        raise ToolError("Skill not found: %s" % params["name"])
    return ToolResult(content=skill.content, data=skill.to_index_dict())


def _skill_execute(params: dict, context: ToolContext) -> ToolResult:
    app = context.services.get("app")
    if app is None:
        raise ToolError("app service is unavailable.")
    depth = int(context.services.get("depth", 0))
    skill = _loader(context).get(params["name"])
    if skill is None:
        raise ToolError("Skill not found: %s" % params["name"])
    result = execute_skill(app, skill, params.get("args", ""), depth=depth)
    return ToolResult(
        content=result.final_text,
        data={"steps": result.steps, "tool_invocations": result.tool_invocations},
    )
