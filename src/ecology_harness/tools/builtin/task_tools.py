from __future__ import annotations

from ecology_harness.tools.base import ToolContext, ToolDefinition, ToolError, ToolResult
from ecology_harness.tools.registry import ToolRegistry


def register_task_tools(registry: ToolRegistry) -> None:
    registry.register(
        ToolDefinition(
            name="TaskCreate",
            description="Create a tracked task.",
            input_schema={
                "type": "object",
                "properties": {
                    "subject": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "active_form": {"type": "string"},
                    "metadata": {"type": "object"},
                },
                "required": [],
            },
            handler=_task_create,
            read_only=False,
            concurrent_safe=False,
        )
    )
    registry.register(
        ToolDefinition(
            name="TaskList",
            description="List tracked tasks.",
            input_schema={"type": "object", "properties": {}},
            handler=_task_list,
            read_only=True,
            concurrent_safe=True,
        )
    )
    registry.register(
        ToolDefinition(
            name="TaskGet",
            description="Get one tracked task by id.",
            input_schema={
                "type": "object",
                "properties": {"id": {"type": "string"}},
                "required": ["id"],
            },
            handler=_task_get,
            read_only=True,
            concurrent_safe=True,
        )
    )
    registry.register(
        ToolDefinition(
            name="TaskUpdate",
            description="Update a tracked task.",
            input_schema={
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "subject": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "status": {"type": "string"},
                    "active_form": {"type": "string"},
                    "owner": {"type": "string"},
                    "add_blocks": {"type": "array"},
                    "add_blocked_by": {"type": "array"},
                    "metadata": {"type": "object"},
                },
                "required": ["id"],
            },
            handler=_task_update,
            read_only=False,
            concurrent_safe=False,
        )
    )


def _store(context: ToolContext):
    store = context.services.get("task_store")
    if store is None:
        raise ToolError("task_store service is unavailable.")
    return store


def _task_create(params: dict, context: ToolContext) -> ToolResult:
    subject = params.get("subject") or params.get("title")
    if not subject:
        raise ToolError("TaskCreate requires `subject` (or legacy `title`).")
    task = _store(context).create(
        subject=subject,
        description=params.get("description", ""),
        active_form=params.get("active_form", ""),
        metadata=params.get("metadata"),
    )
    return ToolResult(content="Created task #%s" % task.id, data=task.to_dict())


def _task_list(params: dict, context: ToolContext) -> ToolResult:
    del params
    tasks = [item.to_dict() for item in _store(context).list_tasks()]
    if not tasks:
        return ToolResult(content="No tasks found.", data={"tasks": []})
    resolved = {item["id"] for item in tasks if item["status"] == "completed"}
    lines = [item.one_line(resolved_ids=resolved) for item in _store(context).list_tasks()]
    return ToolResult(content="\n".join(lines), data={"tasks": tasks})


def _task_get(params: dict, context: ToolContext) -> ToolResult:
    task = _store(context).get(params["id"])
    if task is None:
        raise ToolError("Task not found: %s" % params["id"])
    return ToolResult(
        content=(
            "#%s [%s] %s\n%s\nactive_form: %s\nowner: %s\nblocks: %s\nblocked_by: %s"
            % (
                task.id,
                task.status,
                task.subject,
                task.description,
                task.active_form or "-",
                task.owner or "-",
                ", ".join(task.blocks) or "-",
                ", ".join(task.blocked_by) or "-",
            )
        ),
        data=task.to_dict(),
    )


def _task_update(params: dict, context: ToolContext) -> ToolResult:
    task, updated_fields = _store(context).update(
        task_id=params["id"],
        subject=params.get("subject") or params.get("title"),
        description=params.get("description"),
        status=params.get("status"),
        active_form=params.get("active_form"),
        owner=params.get("owner"),
        add_blocks=params.get("add_blocks"),
        add_blocked_by=params.get("add_blocked_by"),
        metadata=params.get("metadata"),
    )
    if task is None:
        raise ToolError("Task not found: %s" % params["id"])
    return ToolResult(
        content="Updated task #%s (%s)" % (task.id, ", ".join(updated_fields) or "no changes"),
        data=task.to_dict(),
    )
