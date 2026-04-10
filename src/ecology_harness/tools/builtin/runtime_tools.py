from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
import math
import re
import statistics
from typing import Any

from ecology_harness.runtime.compaction import estimate_tokens
from ecology_harness.runtime.messages import ChatMessage
from ecology_harness.tools.base import ToolContext, ToolDefinition, ToolError, ToolResult
from ecology_harness.tools.registry import ToolRegistry


def register_runtime_tools(registry: ToolRegistry) -> None:
    registry.register(
        ToolDefinition(
            name="RuntimeStatus",
            description="Show a live runtime snapshot with context pressure, tasks, agents, and profile state.",
            input_schema={"type": "object", "properties": {}},
            handler=_runtime_status,
            read_only=True,
            concurrent_safe=True,
        )
    )
    registry.register(
        ToolDefinition(
            name="AnalyticsSummary",
            description="Summarize recent session, trajectory, skill usage, MCP, and automation activity.",
            input_schema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer"},
                    "probe_mcp": {"type": "boolean"},
                    "timeout_sec": {"type": "integer"},
                },
            },
            handler=_analytics_summary,
            read_only=True,
            concurrent_safe=True,
        )
    )
    registry.register(
        ToolDefinition(
            name="ExecuteCode",
            description="Execute sandboxed Python snippets with optional access to other tools through call_tool().",
            input_schema={
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "result_var": {"type": "string"},
                    "max_tool_calls": {"type": "integer"},
                },
                "required": ["code"],
            },
            handler=_execute_code,
            read_only=False,
            concurrent_safe=False,
        )
    )
    registry.register(
        ToolDefinition(
            name="SessionStats",
            description="Summarize stored sessions and index state.",
            input_schema={"type": "object", "properties": {}},
            handler=_session_stats,
            read_only=True,
            concurrent_safe=True,
        )
    )
    registry.register(
        ToolDefinition(
            name="CheckpointList",
            description="List lightweight run checkpoints for the current or all sessions.",
            input_schema={"type": "object", "properties": {"session_id": {"type": "string"}, "limit": {"type": "integer"}}},
            handler=_checkpoint_list,
            read_only=True,
            concurrent_safe=True,
        )
    )
    registry.register(
        ToolDefinition(
            name="CheckpointRestore",
            description="Restore conversation state from a stored checkpoint.",
            input_schema={"type": "object", "properties": {"checkpoint_id": {"type": "string"}}, "required": ["checkpoint_id"]},
            handler=_checkpoint_restore,
            read_only=False,
            concurrent_safe=False,
        )
    )
    registry.register(
        ToolDefinition(
            name="ProfileList",
            description="List available work-style profiles and show the active one.",
            input_schema={"type": "object", "properties": {}},
            handler=_profile_list,
            read_only=True,
            concurrent_safe=True,
        )
    )
    registry.register(
        ToolDefinition(
            name="ProfileSelect",
            description="Switch the active work-style profile.",
            input_schema={"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
            handler=_profile_select,
            read_only=False,
            concurrent_safe=False,
        )
    )
    registry.register(
        ToolDefinition(
            name="AutomationList",
            description="List configured recurring automation jobs.",
            input_schema={"type": "object", "properties": {}},
            handler=_automation_list,
            read_only=True,
            concurrent_safe=True,
        )
    )
    registry.register(
        ToolDefinition(
            name="AutomationCreate",
            description="Create a lightweight recurring automation job.",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "prompt": {"type": "string"},
                    "schedule": {"type": "string"},
                    "notes": {"type": "string"},
                },
                "required": ["name", "prompt"],
            },
            handler=_automation_create,
            read_only=False,
            concurrent_safe=False,
        )
    )
    registry.register(
        ToolDefinition(
            name="AutomationRunDue",
            description="Run all due automation jobs once and advance their schedules.",
            input_schema={"type": "object", "properties": {}},
            handler=_automation_run_due,
            read_only=False,
            concurrent_safe=False,
        )
    )
    registry.register(
        ToolDefinition(
            name="HeartbeatStatus",
            description="Inspect the workspace HEARTBEAT.md status and next due time.",
            input_schema={"type": "object", "properties": {}},
            handler=_heartbeat_status,
            read_only=True,
            concurrent_safe=True,
        )
    )
    registry.register(
        ToolDefinition(
            name="HeartbeatRun",
            description="Run the workspace heartbeat instructions once if due, or force a heartbeat pass.",
            input_schema={
                "type": "object",
                "properties": {
                    "force": {"type": "boolean"},
                },
            },
            handler=_heartbeat_run,
            read_only=False,
            concurrent_safe=False,
        )
    )


def _execute_code(params: dict, context: ToolContext) -> ToolResult:
    code = str(params["code"])
    max_tool_calls = min(
        max(int(params.get("max_tool_calls", context.settings.execute_code_max_tool_calls) or 0), 0),
        context.settings.execute_code_max_tool_calls,
    )
    tool_count = 0
    stdout = io.StringIO()
    registry = context.services.get("tool_registry")
    permission_policy = context.services.get("app").permission_policy if context.services.get("app") else None

    def call_tool(name: str, arguments: dict | None = None):
        nonlocal tool_count
        if registry is None:
            raise ToolError("tool_registry service is unavailable.")
        if tool_count >= max_tool_calls:
            raise ToolError("ExecuteCode exceeded max_tool_calls=%s" % max_tool_calls)
        tool_count += 1
        arguments = dict(arguments or {})
        allowed, reason = True, ""
        if permission_policy is not None:
            allowed, reason = permission_policy.check(
                tool_name=name,
                arguments=arguments,
                registry=registry,
                settings=context.settings,
            )
        if not allowed:
            raise ToolError("Permission denied for %s: %s" % (name, reason))
        result = registry.execute(
            name,
            arguments,
            context.settings,
            services=context.services,
        )
        return result.to_dict()

    safe_builtins = {
        "abs": abs,
        "all": all,
        "any": any,
        "bool": bool,
        "dict": dict,
        "enumerate": enumerate,
        "float": float,
        "int": int,
        "len": len,
        "list": list,
        "max": max,
        "min": min,
        "print": print,
        "range": range,
        "reversed": reversed,
        "round": round,
        "set": set,
        "sorted": sorted,
        "str": str,
        "sum": sum,
        "tuple": tuple,
        "zip": zip,
    }
    globals_dict = {
        "__builtins__": safe_builtins,
        "json": json,
        "math": math,
        "re": re,
        "statistics": statistics,
        "call_tool": call_tool,
        "conversation_messages": len(context.services.get("conversation", []) or []),
    }
    locals_dict: dict[str, Any] = {}
    try:
        with redirect_stdout(stdout):
            exec(code, globals_dict, locals_dict)
    except Exception as exc:
        raise ToolError("ExecuteCode failed: %s" % exc) from exc
    result_var = str(params.get("result_var", "result") or "result")
    payload = {
        "stdout": stdout.getvalue()[: context.settings.execute_code_max_output_chars],
        "tool_calls": tool_count,
        "result": locals_dict.get(result_var),
    }
    return ToolResult(content=json.dumps(payload, ensure_ascii=False, indent=2), data=payload)


def _runtime_status(params: dict, context: ToolContext) -> ToolResult:
    del params
    app = context.services.get("app")
    if app is None:
        raise ToolError("app service is unavailable.")
    conversation = context.services.get("conversation") or []
    token_estimate = estimate_tokens(conversation)
    max_context_tokens = max(int(app.settings.max_context_tokens or 0), 1)
    pressure_ratio = min(float(token_estimate) / float(max_context_tokens), 1.0)
    if pressure_ratio >= app.settings.context_pressure_critical_ratio:
        pressure_level = "critical"
    elif pressure_ratio >= app.settings.context_pressure_warn_ratio:
        pressure_level = "warn"
    else:
        pressure_level = "normal"
    tasks = list(app.task_store.list_tasks())
    task_status = _status_counts(item.status for item in tasks)
    subagents = list(app.subagent_manager.list_tasks())
    subagent_status = _status_counts(item.status for item in subagents)
    latest_sessions = app.list_sessions()[:3]
    active_profile = app.profile_manager.get_active().to_dict() if app.profile_manager else {}
    payload = {
        "workspace": str(app.settings.workspace_root),
        "provider": app.settings.provider,
        "model": app.settings.model,
        "runtime_mode": getattr(app, "runtime_mode", "default"),
        "active_profile": active_profile,
        "conversation_messages": len(conversation),
        "context_pressure": {
            "token_estimate": token_estimate,
            "max_context_tokens": max_context_tokens,
            "pressure_ratio": round(pressure_ratio, 4),
            "level": pressure_level,
        },
        "tasks": {
            "total": len(tasks),
            "status_counts": task_status,
        },
        "subagents": {
            "total": len(subagents),
            "status_counts": subagent_status,
        },
        "recent_sessions": [
            {
                "session_id": item.session_id,
                "title": item.title,
                "updated_at": item.updated_at,
                "message_count": item.message_count,
            }
            for item in latest_sessions
        ],
    }
    lines = [
        "workspace: %s" % payload["workspace"],
        "provider: %s / %s" % (payload["provider"], payload["model"]),
        "mode: %s" % payload["runtime_mode"],
        "profile: %s" % (active_profile.get("title", active_profile.get("name", "default")) if active_profile else "default"),
        "context: %s%% (%s/%s tokens, %s)"
        % (
            int(pressure_ratio * 100),
            token_estimate,
            max_context_tokens,
            pressure_level,
        ),
        "tasks: %s %s" % (len(tasks), task_status or {}),
        "subagents: %s %s" % (len(subagents), subagent_status or {}),
    ]
    if latest_sessions:
        lines.append("recent_sessions:")
        for item in latest_sessions:
            lines.append(
                "- %s (%s msgs): %s"
                % (
                    item.session_id,
                    item.message_count,
                    _clip_text(item.title or item.recap or "-", 72),
                )
            )
    return ToolResult(content="\n".join(lines), data=payload)


def _analytics_summary(params: dict, context: ToolContext) -> ToolResult:
    app = context.services.get("app")
    if app is None:
        raise ToolError("app service is unavailable.")
    limit = max(int(params.get("limit", 5) or 5), 1)
    probe_mcp = bool(params.get("probe_mcp", False))
    timeout_sec = max(int(params.get("timeout_sec", 3) or 3), 1)
    sessions = app.list_sessions()
    trajectories = list(app.trajectory_store.list_records())
    skills = app.skill_loader.list_skills(include_archived=True)
    jobs = list(app.automation_manager.list_jobs())
    mcp_states = app.mcp_registry.list_server_states(probe_remote=probe_mcp, timeout_sec=timeout_sec)
    skill_status = _status_counts(item.status for item in skills)
    skill_readiness = _status_counts(item.readiness for item in skills)
    top_used = [
        {
            "slug": item.slug,
            "usage_count": item.usage_count,
            "last_used_at": item.last_used_at,
            "hub_pack": item.hub_pack,
        }
        for item in sorted(
            skills,
            key=lambda skill: (-skill.usage_count, skill.slug),
        )
        if item.usage_count > 0
    ][:limit]
    slice_counts = _status_counts(item.task_slice for item in trajectories)
    job_status = _status_counts(
        (item.last_status or ("scheduled" if item.enabled else "disabled"))
        for item in jobs
    )
    payload = {
        "sessions": app.session_stats(),
        "recent_sessions": [
            {
                "session_id": item.session_id,
                "title": item.title,
                "updated_at": item.updated_at,
                "message_count": item.message_count,
            }
            for item in sessions[:limit]
        ],
        "recent_queries": [
            {
                "trajectory_id": item.trajectory_id,
                "created_at": item.created_at,
                "task_slice": item.task_slice,
                "prompt": item.prompt,
                "quality_tags": item.quality_tags,
            }
            for item in trajectories[:limit]
        ],
        "skills": {
            "total": len(skills),
            "status_counts": skill_status,
            "readiness_counts": skill_readiness,
            "top_used": top_used,
        },
        "trajectories": {
            "total": len(trajectories),
            "slice_counts": slice_counts,
        },
        "automations": {
            "total": len(jobs),
            "status_counts": job_status,
        },
        "mcp": {
            "total": len(mcp_states),
            "status_counts": _status_counts(item.status for item in mcp_states),
            "probed": probe_mcp,
        },
    }
    lines = [
        "sessions: %s stored / %s indexed messages"
        % (
            payload["sessions"].get("session_count", 0),
            (payload["sessions"].get("index") or {}).get("indexed_message_count", 0),
        ),
        "skills: %s total, ready=%s, setup-needed=%s"
        % (
            len(skills),
            skill_readiness.get("ready", 0),
            skill_readiness.get("setup-needed", 0),
        ),
        "trajectories: %s total, slices=%s" % (len(trajectories), slice_counts or {}),
        "automations: %s total, states=%s" % (len(jobs), job_status or {}),
        "mcp: %s server(s), statuses=%s" % (len(mcp_states), payload["mcp"]["status_counts"]),
    ]
    if top_used:
        lines.append("top_used_skills:")
        lines.extend(
            "- %(slug)s used=%(usage_count)s (%(hub_pack)s)" % item
            for item in top_used
        )
    if trajectories:
        lines.append("recent_queries:")
        lines.extend(
            "- [%s] %s" % (item.task_slice, _clip_text(item.prompt, 96))
            for item in trajectories[:limit]
        )
    return ToolResult(content="\n".join(lines), data=payload)


def _session_stats(params: dict, context: ToolContext) -> ToolResult:
    del params
    app = context.services.get("app")
    if app is None:
        raise ToolError("app service is unavailable.")
    stats = app.session_stats()
    lines = [
        "session_count: %s" % stats.get("session_count", 0),
        "message_count: %s" % stats.get("message_count", 0),
        "newest_session_id: %s" % stats.get("newest_session_id", ""),
        "newest_title: %s" % stats.get("newest_title", ""),
    ]
    index = stats.get("index")
    if isinstance(index, dict):
        lines.append("index_fts_enabled: %s" % index.get("fts_enabled"))
        lines.append("indexed_message_count: %s" % index.get("indexed_message_count"))
    return ToolResult(content="\n".join(lines), data=stats)


def _status_counts(values) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value or "unknown")
        counts[key] = counts.get(key, 0) + 1
    return counts


def _clip_text(text: str, limit: int) -> str:
    stripped = str(text or "").strip()
    if len(stripped) <= limit:
        return stripped
    return stripped[: max(limit - 1, 0)].rstrip() + "…"


def _checkpoint_list(params: dict, context: ToolContext) -> ToolResult:
    manager = context.services.get("checkpoint_manager")
    if manager is None:
        raise ToolError("checkpoint_manager service is unavailable.")
    session_id = str(params.get("session_id", "") or "")
    limit = max(int(params.get("limit", 20) or 20), 1)
    records = manager.list(session_id=session_id, limit=limit)
    data = [
        {
            "checkpoint_id": item.checkpoint_id,
            "session_id": item.session_id,
            "created_at": item.created_at,
            "stage": item.stage,
            "summary": item.summary,
            "message_count": len(item.messages),
        }
        for item in records
    ]
    lines = [
        "%(checkpoint_id)s\t%(session_id)s\t%(stage)s\t%(summary)s" % item
        for item in data
    ] or ["No checkpoints available."]
    return ToolResult(content="\n".join(lines), data={"checkpoints": data})


def _checkpoint_restore(params: dict, context: ToolContext) -> ToolResult:
    manager = context.services.get("checkpoint_manager")
    app = context.services.get("app")
    if manager is None or app is None:
        raise ToolError("checkpoint_manager or app service is unavailable.")
    record = manager.get(params["checkpoint_id"])
    if record is None:
        raise ToolError("Checkpoint not found: %s" % params["checkpoint_id"])
    app.save_session(record.messages)
    return ToolResult(
        content="Restored checkpoint %s." % record.checkpoint_id,
        data={"checkpoint_id": record.checkpoint_id, "message_count": len(record.messages)},
    )


def _profile_list(params: dict, context: ToolContext) -> ToolResult:
    del params
    manager = context.services.get("profile_manager")
    if manager is None:
        raise ToolError("profile_manager service is unavailable.")
    active = manager.get_active().name
    profiles = [item.to_dict() for item in manager.list_profiles()]
    lines = [
        "%s\t%s\t%s" % (item["name"], "active" if item["name"] == active else "-", item["description"])
        for item in profiles
    ]
    return ToolResult(content="\n".join(lines), data={"profiles": profiles, "active_profile": active})


def _profile_select(params: dict, context: ToolContext) -> ToolResult:
    manager = context.services.get("profile_manager")
    if manager is None:
        raise ToolError("profile_manager service is unavailable.")
    profile = manager.set_active(params["name"])
    app = context.services.get("app")
    if app is not None:
        app.settings.active_profile = profile.name
    return ToolResult(content="Active profile: %s" % profile.title, data=profile.to_dict())


def _automation_list(params: dict, context: ToolContext) -> ToolResult:
    del params
    manager = context.services.get("automation_manager")
    if manager is None:
        raise ToolError("automation_manager service is unavailable.")
    jobs = [item.to_dict() for item in manager.list_jobs()]
    lines = [
        "%(job_id)s\t%(name)s\t%(schedule)s\t%(next_run_at)s" % item
        for item in jobs
    ] or ["No automation jobs configured."]
    return ToolResult(content="\n".join(lines), data={"jobs": jobs})


def _automation_create(params: dict, context: ToolContext) -> ToolResult:
    manager = context.services.get("automation_manager")
    if manager is None:
        raise ToolError("automation_manager service is unavailable.")
    job = manager.create_job(
        name=params["name"],
        prompt=params["prompt"],
        schedule=str(params.get("schedule", "daily") or "daily"),
        notes=str(params.get("notes", "") or ""),
    )
    return ToolResult(content="Created automation %s." % job.name, data=job.to_dict())


def _automation_run_due(params: dict, context: ToolContext) -> ToolResult:
    del params
    manager = context.services.get("automation_manager")
    app = context.services.get("app")
    if manager is None or app is None:
        raise ToolError("automation_manager or app service is unavailable.")

    def _runner(job):
        previous_mode = getattr(app, "runtime_mode", "default")
        app.runtime_mode = "automation"
        try:
            result = app.run_prompt(job.prompt)
            return {"final_text": result.final_text}
        finally:
            app.runtime_mode = previous_mode

    results = manager.run_due(_runner)
    lines = [
        "%(job_id)s\t%(name)s\t%(status)s\tnext=%(next_run_at)s" % item
        for item in results
    ] or ["No automation jobs were due."]
    return ToolResult(content="\n".join(lines), data={"results": results})


def _heartbeat_status(params: dict, context: ToolContext) -> ToolResult:
    del params
    manager = context.services.get("automation_manager")
    if manager is None:
        raise ToolError("automation_manager service is unavailable.")
    status = manager.heartbeat_status(
        context.settings.workspace_root,
        interval_minutes=context.settings.heartbeat_interval_minutes,
    )
    lines = [
        "enabled: %s" % status.get("enabled", False),
        "path: %s" % status.get("path", ""),
        "prompt_chars: %s" % status.get("prompt_chars", 0),
        "due: %s" % status.get("due", False),
        "last_run_at: %s" % status.get("last_run_at", ""),
        "next_run_at: %s" % status.get("next_run_at", ""),
        "last_status: %s" % status.get("last_status", ""),
    ]
    if status.get("last_error"):
        lines.append("last_error: %s" % status.get("last_error", ""))
    return ToolResult(content="\n".join(lines), data=status)


def _heartbeat_run(params: dict, context: ToolContext) -> ToolResult:
    manager = context.services.get("automation_manager")
    app = context.services.get("app")
    if manager is None or app is None:
        raise ToolError("automation_manager or app service is unavailable.")
    force = bool(params.get("force", False))

    def _runner(prompt: str):
        previous_mode = getattr(app, "runtime_mode", "default")
        app.runtime_mode = "heartbeat"
        try:
            result = app.run_prompt(prompt)
            return {"final_text": result.final_text}
        finally:
            app.runtime_mode = previous_mode

    result = manager.run_heartbeat(
        context.settings.workspace_root,
        _runner,
        interval_minutes=context.settings.heartbeat_interval_minutes,
        force=force,
    )
    if result.get("skipped"):
        message = "Heartbeat skipped: %s" % result.get("reason", "unknown")
    elif result.get("status") == "failed":
        message = "Heartbeat failed: %s" % result.get("error", "unknown error")
    else:
        message = "Heartbeat ran at %s." % result.get("ran_at", "")
        if result.get("noop"):
            message += " No maintenance action was needed."
    return ToolResult(content=message, data=result)
