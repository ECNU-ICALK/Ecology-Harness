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
    registry.register(
        ToolDefinition(
            name="SkillSearch",
            description="Rewrite a task query with context and rank relevant skills using BM25.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer"},
                },
                "required": ["query"],
            },
            handler=_skill_search,
            read_only=True,
            concurrent_safe=True,
        )
    )
    registry.register(
        ToolDefinition(
            name="SkillGovernanceReport",
            description="Summarize skill usage, stale skills, overlap candidates, and setup-needed items.",
            input_schema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer"},
                    "stale_days": {"type": "integer"},
                    "overlap_threshold": {"type": "number"},
                },
            },
            handler=_skill_governance_report,
            read_only=True,
            concurrent_safe=True,
        )
    )
    registry.register(
        ToolDefinition(
            name="SkillDeprecate",
            description="Mark a skill as deprecated without removing it from disk.",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "reason": {"type": "string"},
                    "superseded_by": {"type": "string"},
                },
                "required": ["name", "reason"],
            },
            handler=_skill_deprecate,
            read_only=False,
            concurrent_safe=False,
        )
    )
    registry.register(
        ToolDefinition(
            name="SkillArchive",
            description="Archive a project or user skill so it no longer participates in retrieval.",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["name", "reason"],
            },
            handler=_skill_archive,
            read_only=False,
            concurrent_safe=False,
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
    lines = [
        "%(slug)s\t%(status)s\t%(readiness)s\tused=%(usage_count)s\t%(description)s\t%(context)s\t%(triggers)s" % item
        for item in skills
    ]
    return ToolResult(content="\n".join(lines), data={"skills": skills})


def _skill_read(params: dict, context: ToolContext) -> ToolResult:
    skill = _loader(context).get(params["name"])
    if skill is None:
        raise ToolError("Skill not found: %s" % params["name"])
    return ToolResult(content=skill.content, data=skill.to_index_dict())


def _skill_search(params: dict, context: ToolContext) -> ToolResult:
    limit = params.get("limit")
    if limit is None:
        settings = context.services.get("settings") or context.settings
        limit = getattr(settings, "skill_search_default_k", 8)
    report = _loader(context).search(
        params["query"],
        conversation=context.services.get("conversation"),
        limit=max(int(limit), 1),
        user_invocable_only=True,
    )
    if not report.hits:
        return ToolResult(
            content="No relevant skills found for: %s" % params["query"],
            data=report.to_dict(),
        )
    lines = [
        "%s\t%.3f\t%s"
        % (item.skill.slug, item.score, item.skill.description)
        for item in report.hits
    ]
    header = "Rewritten query: %s" % report.rewrite.rewritten_query
    return ToolResult(content=header + "\n" + "\n".join(lines), data=report.to_dict())


def _skill_execute(params: dict, context: ToolContext) -> ToolResult:
    app = context.services.get("app")
    if app is None:
        raise ToolError("app service is unavailable.")
    depth = int(context.services.get("depth", 0))
    skill = _loader(context).get(params["name"])
    if skill is None:
        raise ToolError("Skill not found: %s" % params["name"])
    app.skill_loader.record_usage(
        skill,
        query=params.get("args", ""),
        mode="tool",
        session_id=getattr(app, "_active_session_id", ""),
    )
    result = execute_skill(app, skill, params.get("args", ""), depth=depth)
    return ToolResult(
        content=result.final_text,
        data={"steps": result.steps, "tool_invocations": result.tool_invocations},
    )


def _skill_governance_report(params: dict, context: ToolContext) -> ToolResult:
    loader = _loader(context)
    report = loader.governance_report(
        limit=max(int(params.get("limit", 12) or 12), 1),
        stale_days=max(int(params.get("stale_days", 90) or 90), 1),
        overlap_threshold=float(params.get("overlap_threshold", 0.62) or 0.62),
    )
    summary = report["summary"]
    lines = [
        "skills=%s active=%s deprecated=%s archived=%s"
        % (
            summary["skill_count"],
            summary["status_counts"].get("active", 0),
            summary["status_counts"].get("deprecated", 0),
            summary["status_counts"].get("archived", 0),
        ),
        "ready=%s setup-needed=%s unsupported=%s"
        % (
            summary["readiness_counts"].get("ready", 0),
            summary["readiness_counts"].get("setup-needed", 0),
            summary["readiness_counts"].get("unsupported", 0),
        ),
    ]
    if report["stale_candidates"]:
        lines.append("stale:")
        lines.extend(
            "- %(slug)s (%(source)s, used=%(usage_count)s): %(reason)s" % item
            for item in report["stale_candidates"]
        )
    if report["setup_needed"]:
        lines.append("setup-needed:")
        lines.extend(
            "- %(slug)s (%(source)s): %(requirements)s" % item
            for item in report["setup_needed"]
        )
    if report["overlaps"]:
        lines.append("overlaps:")
        lines.extend(
            "- %(secondary_slug)s ~ %(primary_slug)s (score=%(score)s): %(recommendation)s" % item
            for item in report["overlaps"]
        )
    return ToolResult(content="\n".join(lines), data=report)


def _skill_deprecate(params: dict, context: ToolContext) -> ToolResult:
    updated = _loader(context).deprecate_skill(
        params["name"],
        reason=params["reason"],
        superseded_by=params.get("superseded_by", ""),
    )
    return ToolResult(
        content="Deprecated skill %s." % updated["slug"],
        data=updated,
    )


def _skill_archive(params: dict, context: ToolContext) -> ToolResult:
    updated = _loader(context).archive_skill(
        params["name"],
        reason=params["reason"],
    )
    return ToolResult(
        content="Archived skill %s." % updated["slug"],
        data=updated,
    )
