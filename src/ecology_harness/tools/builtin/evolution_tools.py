from __future__ import annotations

import json

from ecology_harness.evaluation import compress_trajectory_messages
from ecology_harness.tools.base import ToolContext, ToolDefinition, ToolError, ToolResult
from ecology_harness.tools.registry import ToolRegistry


def register_evolution_tools(registry: ToolRegistry) -> None:
    registry.register(
        ToolDefinition(
            name="SessionSearch",
            description="Search historical sessions with query rewriting and BM25 ranking.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer"},
                },
                "required": ["query"],
            },
            handler=_session_search,
            read_only=True,
            concurrent_safe=True,
        )
    )
    registry.register(
        ToolDefinition(
            name="ReviewList",
            description="List stored post-run review reports and candidate counts.",
            input_schema={"type": "object", "properties": {}},
            handler=_review_list,
            read_only=True,
            concurrent_safe=True,
        )
    )
    registry.register(
        ToolDefinition(
            name="ReviewApplyMemory",
            description="Apply a stored memory candidate into project memory.",
            input_schema={
                "type": "object",
                "properties": {
                    "candidate_id": {"type": "string"},
                    "scope": {"type": "string"},
                },
                "required": ["candidate_id"],
            },
            handler=_review_apply_memory,
            read_only=False,
            concurrent_safe=False,
        )
    )
    registry.register(
        ToolDefinition(
            name="ReviewApplySkill",
            description="Apply a stored skill candidate into the project skill directory.",
            input_schema={
                "type": "object",
                "properties": {"candidate_id": {"type": "string"}},
                "required": ["candidate_id"],
            },
            handler=_review_apply_skill,
            read_only=False,
            concurrent_safe=False,
        )
    )
    registry.register(
        ToolDefinition(
            name="MemoryProviderList",
            description="List active memory providers.",
            input_schema={"type": "object", "properties": {}},
            handler=_memory_provider_list,
            read_only=True,
            concurrent_safe=True,
        )
    )
    registry.register(
        ToolDefinition(
            name="MemoryProviderSearch",
            description="Search provider-backed memory and profiles.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer"},
                },
                "required": ["query"],
            },
            handler=_memory_provider_search,
            read_only=True,
            concurrent_safe=True,
        )
    )
    registry.register(
        ToolDefinition(
            name="ProfileWrite",
            description="Write a markdown-backed project or research profile.",
            input_schema={
                "type": "object",
                "properties": {
                    "profile": {"type": "string"},
                    "content": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["profile", "content"],
            },
            handler=_profile_write,
            read_only=False,
            concurrent_safe=False,
        )
    )
    registry.register(
        ToolDefinition(
            name="TrajectoryList",
            description="List exported trajectories.",
            input_schema={"type": "object", "properties": {}},
            handler=_trajectory_list,
            read_only=True,
            concurrent_safe=True,
        )
    )
    registry.register(
        ToolDefinition(
            name="TrajectoryCompress",
            description="Compress a trajectory into a training-friendly summary form.",
            input_schema={
                "type": "object",
                "properties": {"trajectory_id": {"type": "string"}},
                "required": ["trajectory_id"],
            },
            handler=_trajectory_compress,
            read_only=True,
            concurrent_safe=True,
        )
    )
    registry.register(
        ToolDefinition(
            name="BenchmarkRun",
            description="Compute and persist a benchmark summary over exported trajectories.",
            input_schema={"type": "object", "properties": {"name": {"type": "string"}}},
            handler=_benchmark_run,
            read_only=False,
            concurrent_safe=False,
        )
    )
    registry.register(
        ToolDefinition(
            name="BenchmarkReplay",
            description="Score exported trajectories for replay quality and summarize likely training value.",
            input_schema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer"},
                    "task_slice": {"type": "string"},
                },
            },
            handler=_benchmark_replay,
            read_only=True,
            concurrent_safe=True,
        )
    )


def _app(context: ToolContext):
    app = context.services.get("app")
    if app is None:
        raise ToolError("app service is unavailable.")
    return app


def _session_search(params: dict, context: ToolContext) -> ToolResult:
    app = _app(context)
    limit = int(params.get("limit") or getattr(context.settings, "session_search_default_k", 5))
    report = app.search_sessions(
        params["query"],
        conversation=context.services.get("conversation"),
        limit=limit,
    )
    if not report.hits:
        return ToolResult(
            content="No relevant sessions found for: %s" % params["query"],
            data=report.to_dict(),
        )
    lines = [
        "%(session_id)s\t%(score).3f\t%(updated_at)s\t%(excerpt)s" % item.to_index_dict()
        for item in report.hits
    ]
    header = "Rewritten query: %s" % report.rewrite.rewritten_query
    return ToolResult(content=header + "\n" + "\n".join(lines), data=report.to_dict())


def _review_list(params: dict, context: ToolContext) -> ToolResult:
    del params
    app = _app(context)
    reports = app.list_reviews()
    if not reports:
        return ToolResult(content="No review reports available.", data={"reports": []})
    payload = []
    lines = []
    for report in reports:
        row = {
            "review_id": report.review_id,
            "session_id": report.session_id,
            "created_at": report.created_at,
            "candidate_count": len(report.candidates),
            "summary": report.summary,
        }
        payload.append(row)
        lines.append(
            "%(review_id)s\t%(session_id)s\t%(candidate_count)s candidates\t%(summary)s" % row
        )
    return ToolResult(content="\n".join(lines), data={"reports": payload})


def _review_apply_memory(params: dict, context: ToolContext) -> ToolResult:
    manager = context.services.get("review_manager")
    memory_manager = context.services.get("memory_manager")
    if manager is None or memory_manager is None:
        raise ToolError("review_manager or memory_manager service is unavailable.")
    result = manager.apply_memory_candidate(
        params["candidate_id"],
        memory_manager,
        scope=params.get("scope", "project"),
    )
    return ToolResult(
        content="Applied memory candidate %s." % params["candidate_id"],
        data=result,
    )


def _review_apply_skill(params: dict, context: ToolContext) -> ToolResult:
    manager = context.services.get("review_manager")
    skill_loader = context.services.get("skill_loader")
    if manager is None:
        raise ToolError("review_manager service is unavailable.")
    if skill_loader is None:
        raise ToolError("skill_loader service is unavailable.")
    result = manager.apply_skill_candidate(
        params["candidate_id"],
        skill_loader,
        context.settings.skill_dir,
    )
    return ToolResult(
        content="%s skill candidate %s." % (result.get("action", "Applied").capitalize(), params["candidate_id"]),
        data=result,
    )


def _memory_provider_list(params: dict, context: ToolContext) -> ToolResult:
    del params
    manager = context.services.get("memory_provider_manager")
    if manager is None:
        raise ToolError("memory_provider_manager service is unavailable.")
    providers = manager.describe_providers()
    lines = [
        "%(name)s\tprefetch=%(supports_prefetch)s\tsync=%(supports_sync_turn)s" % item
        for item in providers
    ]
    return ToolResult(content="\n".join(lines), data={"providers": providers})


def _memory_provider_search(params: dict, context: ToolContext) -> ToolResult:
    manager = context.services.get("memory_provider_manager")
    if manager is None:
        raise ToolError("memory_provider_manager service is unavailable.")
    limit = int(params.get("limit") or getattr(context.settings, "memory_provider_search_default_k", 5))
    report = manager.search(
        params["query"],
        conversation=context.services.get("conversation"),
        limit=limit,
    )
    if not report.hits:
        return ToolResult(
            content="No provider memory matched: %s" % params["query"],
            data=report.to_dict(),
        )
    lines = [
        "%(provider)s\t%(score).3f\t%(title)s\t%(description)s" % item.to_dict()
        for item in report.hits
    ]
    header = "Rewritten query: %s" % report.rewrite.rewritten_query
    return ToolResult(content=header + "\n" + "\n".join(lines), data=report.to_dict())


def _profile_write(params: dict, context: ToolContext) -> ToolResult:
    manager = context.services.get("memory_provider_manager")
    if manager is None:
        raise ToolError("memory_provider_manager service is unavailable.")
    target = params["profile"]
    for provider in getattr(manager, "providers", []):
        if getattr(provider, "name", "") != target:
            continue
        writer = getattr(provider, "write", None)
        if not callable(writer):
            raise ToolError("Provider %s is not writable." % target)
        writer(params["content"], params.get("description"))
        return ToolResult(
            content="Updated profile %s." % target,
            data={"profile": target},
        )
    raise ToolError("Profile provider not found: %s" % target)


def _trajectory_list(params: dict, context: ToolContext) -> ToolResult:
    del params
    store = context.services.get("trajectory_store")
    if store is None:
        raise ToolError("trajectory_store service is unavailable.")
    records = store.list_records()
    if not records:
        return ToolResult(content="No trajectories exported yet.", data={"trajectories": []})
    payload = []
    lines = []
    for item in records[:50]:
        row = {
            "trajectory_id": item.trajectory_id,
            "session_id": item.session_id,
            "created_at": item.created_at,
            "tool_call_count": len(item.tool_invocations),
            "message_count": len(item.messages),
            "prompt": item.prompt,
        }
        payload.append(row)
        lines.append(
            "%(trajectory_id)s\t%(session_id)s\t%(tool_call_count)s tools\t%(prompt)s" % row
        )
    return ToolResult(content="\n".join(lines), data={"trajectories": payload})


def _trajectory_compress(params: dict, context: ToolContext) -> ToolResult:
    store = context.services.get("trajectory_store")
    if store is None:
        raise ToolError("trajectory_store service is unavailable.")
    record = store.get(params["trajectory_id"])
    if record is None:
        raise ToolError("Trajectory not found: %s" % params["trajectory_id"])
    from ecology_harness.runtime.messages import ChatMessage

    messages = [ChatMessage.from_dict(item) for item in record.messages]
    result = compress_trajectory_messages(messages)
    return ToolResult(
        content=json.dumps(result.to_dict(), ensure_ascii=False, indent=2),
        data=result.to_dict(),
    )


def _benchmark_run(params: dict, context: ToolContext) -> ToolResult:
    runner = context.services.get("benchmark_runner")
    if runner is None:
        raise ToolError("benchmark_runner service is unavailable.")
    name = params.get("name", "latest-benchmark")
    path = runner.write_summary(name=name)
    summary = runner.summarize()
    return ToolResult(
        content="Wrote benchmark summary to %s" % path,
        data={"path": str(path), "summary": summary.to_dict()},
    )


def _benchmark_replay(params: dict, context: ToolContext) -> ToolResult:
    runner = context.services.get("benchmark_runner")
    if runner is None:
        raise ToolError("benchmark_runner service is unavailable.")
    limit = params.get("limit")
    task_slice = params.get("task_slice", "")
    scores = runner.replay(
        limit=int(limit) if limit is not None else None,
        task_slice=str(task_slice or ""),
    )
    payload = [item.to_dict() for item in scores]
    if not payload:
        return ToolResult(content="No trajectories available for replay scoring.", data={"scores": []})
    lines = [
        "%(trajectory_id)s\t%(task_slice)s\t%(score).3f\tsuccess=%(success)s\terrors=%(error_count)s"
        % item
        for item in payload
    ]
    return ToolResult(content="\n".join(lines), data={"scores": payload})
