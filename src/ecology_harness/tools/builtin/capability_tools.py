from __future__ import annotations

from ecology_harness.skills.retrieval import tokenize_text
from ecology_harness.tools.base import ToolContext, ToolDefinition, ToolError, ToolResult
from ecology_harness.tools.registry import ToolRegistry


def register_capability_tools(registry: ToolRegistry) -> None:
    registry.register(
        ToolDefinition(
            name="CapabilityReadinessReport",
            description=(
                "Preflight a user request by ranking relevant skills, MCP servers, "
                "and built-in tools, then summarize readiness gaps and next actions."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "skill_limit": {"type": "integer"},
                    "mcp_limit": {"type": "integer"},
                    "tool_limit": {"type": "integer"},
                    "probe_mcp": {"type": "boolean"},
                    "timeout_sec": {"type": "integer"},
                },
                "required": ["query"],
            },
            handler=_capability_readiness_report,
            read_only=True,
            concurrent_safe=True,
        )
    )


def _capability_readiness_report(params: dict, context: ToolContext) -> ToolResult:
    query = str(params["query"]).strip()
    if not query:
        raise ToolError("query must not be empty.")
    skill_limit = _positive_int(params.get("skill_limit"), 6)
    mcp_limit = _positive_int(params.get("mcp_limit"), 5)
    tool_limit = _positive_int(params.get("tool_limit"), 6)
    timeout_sec = _positive_int(params.get("timeout_sec"), 3)
    probe_mcp = bool(params.get("probe_mcp", False))

    skill_loader = context.services.get("skill_loader")
    mcp_registry = context.services.get("mcp_registry")
    tool_registry = context.services.get("tool_registry")
    if skill_loader is None:
        raise ToolError("skill_loader service is unavailable.")
    if mcp_registry is None:
        raise ToolError("mcp_registry service is unavailable.")
    if tool_registry is None:
        raise ToolError("tool_registry service is unavailable.")

    conversation = context.services.get("conversation")
    skill_report = skill_loader.search(
        query,
        conversation=conversation,
        limit=skill_limit,
        user_invocable_only=True,
    )
    mcp_report = mcp_registry.search(
        query,
        conversation=conversation,
        limit=mcp_limit,
        enabled_only=False,
    )
    mcp_states = {
        item.server_name: item.to_dict()
        for item in mcp_registry.list_server_states(
            probe_remote=probe_mcp,
            timeout_sec=timeout_sec,
        )
    }
    tools = _rank_tools(
        query=skill_report.rewrite.rewritten_query or query,
        tools=tool_registry.list_tools(),
        limit=tool_limit,
    )

    skills = [_skill_hit_to_dict(item) for item in skill_report.hits]
    mcp_servers = [
        _mcp_hit_to_dict(item, mcp_states.get(item.server.name, {}))
        for item in mcp_report.hits
    ]
    summary = _summarize(skills, mcp_servers, tools)
    recommendations = _recommendations(
        skills=skills,
        mcp_servers=mcp_servers,
        probe_mcp=probe_mcp,
    )
    data = {
        "query": query,
        "rewritten_query": skill_report.rewrite.rewritten_query,
        "skills": skills,
        "mcp_servers": mcp_servers,
        "tools": tools,
        "summary": summary,
        "recommendations": recommendations,
        "probe_mcp": probe_mcp,
    }
    return ToolResult(content=_render_capability_report(data), data=data)


def _skill_hit_to_dict(hit) -> dict:
    skill = hit.skill
    return {
        "slug": skill.slug,
        "name": skill.name,
        "description": skill.description,
        "score": round(float(hit.score), 4),
        "readiness": skill.readiness,
        "status": skill.status,
        "hub_pack": skill.hub_pack,
        "missing_requirements": list(skill.missing_requirements),
        "setup": skill.setup,
        "requirements": list(skill.requirements),
        "matched_terms": list(hit.matched_terms),
    }


def _mcp_hit_to_dict(hit, state: dict) -> dict:
    server = hit.server
    return {
        "server_name": server.name,
        "description": server.description,
        "transport": server.transport,
        "auth": server.auth,
        "score": round(float(hit.score), 4),
        "enabled": bool(server.default_enabled),
        "runtime_invokable": bool(state.get("runtime_invokable", False)),
        "status": str(state.get("status", "unknown") or "unknown"),
        "tool_count": len(server.tools),
        "resource_count": len(server.resources),
        "matched_tools": list(hit.matched_tools),
        "matched_resources": list(hit.matched_resources),
        "error_message": str(state.get("error_message", "") or ""),
    }


def _rank_tools(*, query: str, tools: list[ToolDefinition], limit: int) -> list[dict]:
    query_tokens = set(tokenize_text(query))
    if not query_tokens:
        return []
    ranked: list[tuple[float, ToolDefinition, list[str]]] = []
    for tool in tools:
        if tool.name == "CapabilityReadinessReport":
            continue
        document = " ".join(
            [
                tool.name,
                tool.description,
                tool.source,
                tool.origin,
                " ".join(tool.tags),
            ]
        )
        document_tokens = set(tokenize_text(document))
        matched = sorted(query_tokens & document_tokens)
        score = float(len(matched))
        normalized_name = tool.name.lower()
        query_text = query.lower()
        if normalized_name in query_text:
            score += 3.0
        if any(token in normalized_name for token in query_tokens):
            score += 0.5
        if score <= 0:
            continue
        ranked.append((score, tool, matched[:8]))
    ranked.sort(key=lambda item: (-item[0], item[1].name.lower()))
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "source": tool.source,
            "read_only": tool.read_only,
            "concurrent_safe": tool.concurrent_safe,
            "score": round(score, 4),
            "matched_terms": matched,
        }
        for score, tool, matched in ranked[:limit]
    ]


def _summarize(skills: list[dict], mcp_servers: list[dict], tools: list[dict]) -> dict:
    skill_counts = _count_by(skills, "readiness")
    mcp_counts = _count_by(mcp_servers, "status")
    return {
        "skill_count": len(skills),
        "mcp_count": len(mcp_servers),
        "tool_count": len(tools),
        "skill_readiness": skill_counts,
        "mcp_status": mcp_counts,
        "ready_skill_count": skill_counts.get("ready", 0),
        "setup_needed_skill_count": skill_counts.get("setup-needed", 0),
        "runtime_invokable_mcp_count": sum(1 for item in mcp_servers if item["runtime_invokable"]),
    }


def _recommendations(
    *,
    skills: list[dict],
    mcp_servers: list[dict],
    probe_mcp: bool,
) -> list[str]:
    recommendations: list[str] = []
    ready_skills = [item["slug"] for item in skills if item["readiness"] == "ready"]
    if ready_skills:
        recommendations.append(
            "Start with ready skills: %s." % ", ".join(ready_skills[:3])
        )
    setup_skills = [item for item in skills if item["readiness"] == "setup-needed"]
    if setup_skills:
        first = setup_skills[0]
        missing = ", ".join(first["missing_requirements"][:4]) or "follow setup notes"
        recommendations.append(
            "Before executing `%s`, resolve setup requirements: %s."
            % (first["slug"], missing)
        )
    configured_mcp = [
        item["server_name"]
        for item in mcp_servers
        if item["status"] in {"configured", "cataloged", "unknown"}
    ]
    if configured_mcp and not probe_mcp:
        recommendations.append(
            "Run this report with probe_mcp=true or run `eh doctor --probe` before direct MCP calls."
        )
    blocked_mcp = [
        item for item in mcp_servers
        if item["status"] in {"missing-command", "missing-module", "missing-script", "unreachable", "auth-required"}
    ]
    if blocked_mcp:
        recommendations.append(
            "Fix MCP runtime/auth for: %s."
            % ", ".join(item["server_name"] for item in blocked_mcp[:3])
        )
    if not recommendations:
        recommendations.append("Relevant capabilities look usable; proceed with the workflow and keep outputs auditable.")
    return recommendations


def _render_capability_report(data: dict) -> str:
    lines = [
        "Capability readiness for: %s" % data["query"],
        "Rewritten query: %s" % data["rewritten_query"],
        "Summary: skills=%s, mcp=%s, tools=%s"
        % (
            data["summary"]["skill_count"],
            data["summary"]["mcp_count"],
            data["summary"]["tool_count"],
        ),
    ]
    lines.append("Skills:")
    if data["skills"]:
        for item in data["skills"]:
            detail = item["readiness"]
            if item["missing_requirements"]:
                detail += " missing=" + ", ".join(item["missing_requirements"][:3])
            lines.append("- %(slug)s [%(score).3f %(status)s/%(detail)s]: %(description)s" % {**item, "detail": detail})
    else:
        lines.append("- none")
    lines.append("MCP:")
    if data["mcp_servers"]:
        for item in data["mcp_servers"]:
            runtime = "runtime=yes" if item["runtime_invokable"] else "runtime=no"
            lines.append(
                "- %(server_name)s [%(score).3f %(status)s %(transport)s %(runtime)s]: %(description)s"
                % {**item, "runtime": runtime}
            )
    else:
        lines.append("- none")
    lines.append("Tools:")
    if data["tools"]:
        for item in data["tools"]:
            mode = "read-only" if item["read_only"] else "write"
            lines.append("- %(name)s [%(score).3f %(mode)s]: %(description)s" % {**item, "mode": mode})
    else:
        lines.append("- none")
    lines.append("Recommendations:")
    lines.extend("- %s" % item for item in data["recommendations"])
    return "\n".join(lines)


def _count_by(items: list[dict], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = str(item.get(key, "unknown") or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts


def _positive_int(value, default: int) -> int:
    try:
        return max(int(value if value is not None else default), 1)
    except (TypeError, ValueError):
        return default
