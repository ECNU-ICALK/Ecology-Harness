from __future__ import annotations

from ecology_harness.tools.base import ToolContext, ToolDefinition, ToolError, ToolResult
from ecology_harness.tools.registry import ToolRegistry


def register_agent_tools(registry: ToolRegistry) -> None:
    registry.register(
        ToolDefinition(
            name="Agent",
            description="Spawn a delegated subagent task with optional type, background mode, and naming.",
            input_schema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "provider": {"type": "string"},
                    "subagent_type": {"type": "string"},
                    "name": {"type": "string"},
                    "model": {"type": "string"},
                    "wait": {"type": "boolean"},
                    "isolation": {"type": "string"},
                    "depends_on": {"type": "array", "items": {"type": "string"}},
                    "expected_output": {"type": "string"},
                    "ownership": {"type": "string"},
                    "coordination_context": {"type": "string"},
                },
                "required": ["prompt"],
            },
            handler=_run_agent,
            read_only=False,
            concurrent_safe=False,
        )
    )
    registry.register(
        ToolDefinition(
            name="SendMessage",
            description="Send a follow-up message to a running or background subagent.",
            input_schema={
                "type": "object",
                "properties": {
                    "to": {"type": "string"},
                    "message": {"type": "string"},
                },
                "required": ["to", "message"],
            },
            handler=_send_message,
            read_only=False,
            concurrent_safe=True,
        )
    )
    registry.register(
        ToolDefinition(
            name="CheckAgentResult",
            description="Check the status and result of a subagent task.",
            input_schema={
                "type": "object",
                "properties": {"task_id": {"type": "string"}},
                "required": ["task_id"],
            },
            handler=_check_agent_result,
            read_only=True,
            concurrent_safe=True,
        )
    )
    registry.register(
        ToolDefinition(
            name="ListAgentTasks",
            description="List all subagent tasks and their statuses.",
            input_schema={"type": "object", "properties": {}},
            handler=_list_agent_tasks,
            read_only=True,
            concurrent_safe=True,
        )
    )
    registry.register(
        ToolDefinition(
            name="ListAgentTypes",
            description="List all available built-in and custom agent types.",
            input_schema={"type": "object", "properties": {}},
            handler=_list_agent_types,
            read_only=True,
            concurrent_safe=True,
        )
    )


def _run_agent(params: dict, context: ToolContext) -> ToolResult:
    manager = context.services.get("subagent_manager")
    if manager is None:
        raise ToolError("subagent_manager service is unavailable.")
    depth = int(context.services.get("depth", 0))
    result = manager.run(
        prompt=params["prompt"],
        provider_name=params.get("provider", ""),
        depth=depth,
        agent_type=params.get("subagent_type", ""),
        name=params.get("name", ""),
        wait=params.get("wait", True),
        model_override=params.get("model", ""),
        isolation=params.get("isolation", ""),
        depends_on=params.get("depends_on", []),
        expected_output=params.get("expected_output", ""),
        ownership=params.get("ownership", ""),
        coordination_context=params.get("coordination_context", ""),
        parent_conversation=context.services.get("conversation"),
        )
    if hasattr(result, "final_text"):
        return ToolResult(
            content=result.final_text,
            data={"steps": result.steps, "tool_invocations": result.tool_invocations},
        )
    return ToolResult(
        content=(
            "Task ID: %s\nName: %s\nStatus: %s\nUse CheckAgentResult or SendMessage to interact."
            % (result.id, result.name, result.status)
        ),
        data={
            "task_id": result.id,
            "name": result.name,
            "status": result.status,
            "agent_type": result.agent_type,
            "dependencies": result.dependency_ids,
            "task_record_id": result.task_record_id,
        },
    )


def _send_message(params: dict, context: ToolContext) -> ToolResult:
    manager = context.services.get("subagent_manager")
    if manager is None:
        raise ToolError("subagent_manager service is unavailable.")
    ok = manager.send_message(params["to"], params["message"])
    if not ok:
        raise ToolError("No running agent found: %s" % params["to"])
    return ToolResult(content="Message queued for agent `%s`." % params["to"], data={"queued": True})


def _check_agent_result(params: dict, context: ToolContext) -> ToolResult:
    manager = context.services.get("subagent_manager")
    if manager is None:
        raise ToolError("subagent_manager service is unavailable.")
    task = manager.get_task(params["task_id"])
    if task is None:
        raise ToolError("No task found: %s" % params["task_id"])
    content = "Status: %s\nName: %s\nAgent type: %s" % (
        task.status,
        task.name,
        task.agent_type or "-",
    )
    if task.dependency_ids:
        content += "\nDepends on: %s" % ", ".join(task.dependency_ids)
    if task.task_record_id:
        content += "\nTask record: %s" % task.task_record_id
    if task.result:
        content += "\n\nResult:\n%s" % task.result
    return ToolResult(content=content, data=_task_to_dict(task))


def _list_agent_tasks(params: dict, context: ToolContext) -> ToolResult:
    del params
    manager = context.services.get("subagent_manager")
    if manager is None:
        raise ToolError("subagent_manager service is unavailable.")
    tasks = manager.list_tasks()
    if not tasks:
        return ToolResult(content="No subagent tasks.", data={"tasks": []})
    lines = ["ID           | Name     | Status     | Type             | Dependencies | Prompt"]
    lines.append("-------------|----------|------------|------------------|--------------|------")
    for task in tasks:
        short_prompt = task.prompt[:50] + ("..." if len(task.prompt) > 50 else "")
        dependencies = ",".join(task.dependency_ids) or "-"
        lines.append(
            "%s | %-8s | %-10s | %-16s | %-12s | %s"
            % (
                task.id,
                task.name[:8],
                task.status,
                task.agent_type or "-",
                dependencies[:12],
                short_prompt,
            )
        )
    return ToolResult(content="\n".join(lines), data={"tasks": [_task_to_dict(task) for task in tasks]})


def _list_agent_types(params: dict, context: ToolContext) -> ToolResult:
    del params
    manager = context.services.get("subagent_manager")
    if manager is None:
        raise ToolError("subagent_manager service is unavailable.")
    agent_types = [item.to_index_dict() for item in manager.list_agent_definitions()]
    lines = []
    for item in agent_types:
        line = "%s [%s] %s" % (item["name"], item["source"], item["description"])
        if item.get("tools"):
            line += "\n  tools: %s" % item["tools"]
        if item.get("model"):
            line += "\n  model: %s" % item["model"]
        lines.append(line)
    return ToolResult(content="\n".join(lines), data={"agent_types": agent_types})


def _task_to_dict(task) -> dict:
    return {
        "id": task.id,
        "prompt": task.prompt,
        "status": task.status,
        "result": task.result,
        "depth": task.depth,
        "name": task.name,
        "agent_type": task.agent_type,
        "worktree_path": task.worktree_path,
        "worktree_branch": task.worktree_branch,
        "provider": task.provider,
        "model": task.model,
        "expected_output": task.expected_output,
        "ownership": task.ownership,
        "shared_context_summary": task.shared_context_summary,
        "parent_task_id": task.parent_task_id,
        "dependency_ids": task.dependency_ids,
        "child_task_ids": task.child_task_ids,
        "task_record_id": task.task_record_id,
        "handoff_history": task.handoff_history,
        "coordination_notes": task.coordination_notes,
        "steps": task.steps,
        "tool_calls": task.tool_calls,
        "conversation_messages": task.conversation_messages,
    }
