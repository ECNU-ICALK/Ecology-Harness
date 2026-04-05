from __future__ import annotations

from pathlib import Path

from ecology_harness.claw_compat import list_claw_tools
from ecology_harness.tools.base import ToolContext, ToolDefinition, ToolError, ToolResult
from ecology_harness.tools.registry import ToolRegistry


def register_claw_compat_tools(registry: ToolRegistry) -> None:
    registry.register(
        ToolDefinition(
            name="ClawToolCatalog",
            description="List the curated claw-code compatibility tool surface installed in this harness.",
            input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
            handler=_claw_catalog,
            read_only=True,
            concurrent_safe=True,
            source="claw-compat",
        )
    )
    registry.register(
        ToolDefinition(
            name="AskUserQuestionTool",
            description="Return a user-facing clarification request when more input is needed.",
            input_schema={
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "header": {"type": "string"},
                },
                "required": ["question"],
            },
            handler=_ask_user_question,
            read_only=True,
            concurrent_safe=True,
            source="claw-compat",
        )
    )
    registry.register(
        ToolDefinition(
            name="BriefTool",
            description="Compose a compact implementation brief from structured fields.",
            input_schema={
                "type": "object",
                "properties": {
                    "objective": {"type": "string"},
                    "context": {"type": "string"},
                    "constraints": {"type": "array"},
                    "files": {"type": "array"},
                },
                "required": ["objective"],
            },
            handler=_brief,
            read_only=True,
            concurrent_safe=True,
            source="claw-compat",
        )
    )
    registry.register(
        ToolDefinition(
            name="ConfigTool",
            description="Inspect or update selected runtime configuration keys.",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {"type": "string"},
                    "key": {"type": "string"},
                    "value": {"type": "string"},
                },
            },
            handler=_config_tool,
            read_only=False,
            concurrent_safe=False,
            source="claw-compat",
        )
    )
    registry.register(
        ToolDefinition(
            name="EnterPlanModeTool",
            description="Enable plan mode guidance for the current harness session.",
            input_schema={"type": "object", "properties": {}},
            handler=_enter_plan_mode,
            read_only=False,
            concurrent_safe=False,
            source="claw-compat",
        )
    )
    registry.register(
        ToolDefinition(
            name="ExitPlanModeV2Tool",
            description="Disable plan mode guidance for the current harness session.",
            input_schema={"type": "object", "properties": {}},
            handler=_exit_plan_mode,
            read_only=False,
            concurrent_safe=False,
            source="claw-compat",
        )
    )
    registry.register(
        ToolDefinition(
            name="ListDirectoryTool",
            description="List directory entries inside the workspace with optional recursion.",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "recursive": {"type": "boolean"},
                },
            },
            handler=_list_directory,
            read_only=True,
            concurrent_safe=True,
            source="claw-compat",
        )
    )
    registry.register(
        ToolDefinition(
            name="TodoWriteTool",
            description="Create or update tracked tasks from a compact todo array.",
            input_schema={
                "type": "object",
                "properties": {
                    "items": {"type": "array"},
                },
                "required": ["items"],
            },
            handler=_todo_write,
            read_only=False,
            concurrent_safe=False,
            source="claw-compat",
        )
    )
    _register_alias(
        registry,
        "AgentTool",
        _agent_tool,
        {
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "task": {"type": "string"},
                "objective": {"type": "string"},
                "agent_type": {"type": "string"},
                "subagent_type": {"type": "string"},
                "wait": {"type": "boolean"},
                "model": {"type": "string"},
            },
        },
    )
    _register_alias(
        registry,
        "BashTool",
        _bash_tool,
        {
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "cmd": {"type": "string"},
                "cwd": {"type": "string"},
            },
            "required": [],
        },
    )
    _register_alias(
        registry,
        "FileReadTool",
        _file_read_tool,
        {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "file_path": {"type": "string"},
                "offset": {"type": "integer"},
                "limit": {"type": "integer"},
                "start_line": {"type": "integer"},
                "end_line": {"type": "integer"},
            },
        },
    )
    _register_alias(
        registry,
        "FileEditTool",
        _file_edit_tool,
        {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "file_path": {"type": "string"},
                "old_text": {"type": "string"},
                "new_text": {"type": "string"},
                "find": {"type": "string"},
                "replace": {"type": "string"},
                "replace_all": {"type": "boolean"},
            },
        },
    )
    _register_alias(
        registry,
        "GlobTool",
        _glob_tool,
        {
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "glob": {"type": "string"},
            },
        },
    )
    _register_alias(
        registry,
        "GrepTool",
        _grep_tool,
        {
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "query": {"type": "string"},
                "include": {"type": "string"},
                "path": {"type": "string"},
                "case_sensitive": {"type": "boolean"},
                "max_results": {"type": "integer"},
            },
        },
    )
    _register_alias(
        registry,
        "MemoryReadTool",
        _memory_read_tool,
        {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "memory": {"type": "string"},
                "slug": {"type": "string"},
                "scope": {"type": "string"},
            },
        },
    )
    _register_alias(
        registry,
        "MemoryWriteTool",
        _memory_write_tool,
        {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "summary": {"type": "string"},
                "content": {"type": "string"},
                "memory": {"type": "string"},
                "type": {"type": "string"},
                "scope": {"type": "string"},
            },
        },
    )
    _register_alias(
        registry,
        "SkillTool",
        _skill_tool,
        {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "skill": {"type": "string"},
                "args": {"type": "string"},
            },
        },
    )
    _register_alias(
        registry,
        "WebFetchTool",
        _web_fetch_tool,
        {
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
        },
    )
    _register_alias(
        registry,
        "WebSearchTool",
        _web_search_tool,
        {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    )


def _register_alias(registry: ToolRegistry, name: str, handler, input_schema: dict) -> None:
    registry.register(
        ToolDefinition(
            name=name,
            description=next(item.description for item in list_claw_tools() if item.name == name),
            input_schema=input_schema,
            handler=handler,
            read_only=False,
            concurrent_safe=False,
            source="claw-compat",
        )
    )


def _app(context: ToolContext):
    app = context.services.get("app")
    if app is None:
        raise ToolError("app service is unavailable.")
    return app


def _execute_alias(context: ToolContext, tool_name: str, params: dict) -> ToolResult:
    app = _app(context)
    return app.registry.execute(
        tool_name,
        params,
        context.settings,
        services=context.services,
    )


def _claw_catalog(params: dict, context: ToolContext) -> ToolResult:
    query = str(params.get("query", "")).strip().lower()
    rows = []
    for item in list_claw_tools():
        if query and query not in item.name.lower() and query not in item.source_hint.lower():
            continue
        rows.append(item.to_dict())
    lines = [
        "%(name)s\t%(availability)s\t%(mapped_tool)s\t%(source_hint)s" % item
        for item in rows
    ] or ["No claw-code compatibility tools matched."]
    return ToolResult(content="\n".join(lines), data={"tools": rows, "query": query})


def _ask_user_question(params: dict, context: ToolContext) -> ToolResult:
    del context
    header = params.get("header", "Need user input")
    question = params["question"]
    return ToolResult(
        content="%s\n%s" % (header, question),
        data={"header": header, "question": question, "interactive": False},
    )


def _brief(params: dict, context: ToolContext) -> ToolResult:
    del context
    lines = [
        "# Brief",
        "",
        "Objective: %s" % params["objective"],
    ]
    if params.get("context"):
        lines.append("Context: %s" % params["context"])
    constraints = params.get("constraints", []) or []
    files = params.get("files", []) or []
    if constraints:
        lines.append("Constraints:")
        lines.extend("- %s" % item for item in constraints)
    if files:
        lines.append("Files:")
        lines.extend("- %s" % item for item in files)
    return ToolResult(content="\n".join(lines), data={"brief": "\n".join(lines)})


def _config_tool(params: dict, context: ToolContext) -> ToolResult:
    app = _app(context)
    settings = app.settings
    action = (params.get("action", "get") or "get").strip().lower()
    allowed = {
        "provider": "provider",
        "model": "model",
        "permission_mode": "permission_mode",
        "sandbox_mode": "sandbox_mode",
        "runtime_mode": "runtime_mode",
    }
    if action == "list":
        payload = {key: getattr(app, attr) if key == "runtime_mode" else getattr(settings, attr) for key, attr in allowed.items()}
        lines = ["%s: %s" % (key, value) for key, value in payload.items()]
        return ToolResult(content="\n".join(lines), data=payload)
    key = params.get("key", "")
    if key not in allowed:
        raise ToolError("ConfigTool supports keys: %s" % ", ".join(sorted(allowed)))
    attr = allowed[key]
    if action == "get":
        value = getattr(app, attr) if key == "runtime_mode" else getattr(settings, attr)
        return ToolResult(content="%s=%s" % (key, value), data={"key": key, "value": value})
    if action == "set":
        value = params.get("value", "")
        if key == "runtime_mode":
            app.runtime_mode = value or "default"
        else:
            setattr(settings, attr, value)
        current = getattr(app, attr) if key == "runtime_mode" else getattr(settings, attr)
        return ToolResult(content="Set %s=%s" % (key, current), data={"key": key, "value": current})
    raise ToolError("Unsupported ConfigTool action: %s" % action)


def _enter_plan_mode(params: dict, context: ToolContext) -> ToolResult:
    del params
    app = _app(context)
    app.runtime_mode = "plan"
    return ToolResult(content="runtime_mode=plan", data={"runtime_mode": app.runtime_mode})


def _exit_plan_mode(params: dict, context: ToolContext) -> ToolResult:
    del params
    app = _app(context)
    app.runtime_mode = "default"
    return ToolResult(content="runtime_mode=default", data={"runtime_mode": app.runtime_mode})


def _list_directory(params: dict, context: ToolContext) -> ToolResult:
    raw_path = params.get("path", ".")
    sandbox = context.services.get("sandbox")
    if sandbox is not None:
        path = sandbox.resolve_path(raw_path, access="read")
    else:
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            path = context.settings.workspace_root / path
        path = path.resolve()
    if not path.exists():
        raise ToolError("Directory does not exist: %s" % raw_path)
    if not path.is_dir():
        raise ToolError("Path is not a directory: %s" % raw_path)
    recursive = bool(params.get("recursive", False))
    entries = []
    iterator = path.rglob("*") if recursive else path.iterdir()
    for item in iterator:
        rel = item.relative_to(context.settings.workspace_root) if item.is_relative_to(context.settings.workspace_root) else item
        suffix = "/" if item.is_dir() else ""
        entries.append("%s%s" % (rel.as_posix(), suffix))
        if len(entries) >= context.settings.max_glob_results:
            break
    return ToolResult(content="\n".join(entries) or "(empty directory)", data={"entries": entries, "recursive": recursive})


def _todo_write(params: dict, context: ToolContext) -> ToolResult:
    store = context.services.get("task_store")
    if store is None:
        raise ToolError("task_store service is unavailable.")
    items = params["items"]
    if not isinstance(items, list):
        raise ToolError("TodoWriteTool requires `items` to be an array.")
    touched = []
    for item in items:
        if not isinstance(item, dict):
            continue
        task_id = item.get("id")
        subject = item.get("subject") or item.get("content") or item.get("title")
        if not subject:
            continue
        if task_id:
            task, _updated_fields = store.update(
                task_id=task_id,
                subject=subject,
                description=item.get("description"),
                status=item.get("status"),
                active_form=item.get("active_form") or item.get("activeForm"),
                owner=item.get("owner"),
                metadata=item.get("metadata"),
            )
            if task is not None:
                touched.append(task.to_dict())
                continue
        task = store.create(
            subject=subject,
            description=item.get("description", ""),
            active_form=item.get("active_form") or item.get("activeForm") or "",
            metadata=item.get("metadata"),
        )
        if item.get("status"):
            store.update(task_id=task.id, status=item["status"])
            task = store.get(task.id) or task
        touched.append(task.to_dict())
    lines = ["#%s [%s] %s" % (item["id"], item["status"], item["subject"]) for item in touched]
    return ToolResult(content="\n".join(lines) or "No todos were applied.", data={"tasks": touched})


def _agent_tool(params: dict, context: ToolContext) -> ToolResult:
    mapped = {
        "prompt": params.get("prompt") or params.get("task") or params.get("objective"),
        "provider": params.get("provider", ""),
        "subagent_type": params.get("subagent_type") or params.get("agent_type") or params.get("type", ""),
        "name": params.get("name", ""),
        "model": params.get("model", ""),
        "wait": params.get("wait", True),
        "isolation": params.get("isolation", ""),
        "depends_on": params.get("depends_on", []),
        "expected_output": params.get("expected_output", ""),
        "ownership": params.get("ownership", ""),
        "coordination_context": params.get("coordination_context", ""),
    }
    if not mapped["prompt"]:
        raise ToolError("AgentTool requires `prompt`, `task`, or `objective`.")
    return _execute_alias(context, "Agent", mapped)


def _bash_tool(params: dict, context: ToolContext) -> ToolResult:
    command = params.get("command") or params.get("cmd")
    if not command:
        raise ToolError("BashTool requires `command` or `cmd`.")
    mapped = {
        "command": command,
        "cwd": params.get("cwd", ""),
    }
    return _execute_alias(context, "Bash", mapped)


def _file_read_tool(params: dict, context: ToolContext) -> ToolResult:
    path = params.get("path") or params.get("file_path")
    if not path:
        raise ToolError("FileReadTool requires `path` or `file_path`.")
    start_line = params.get("start_line")
    end_line = params.get("end_line")
    offset = params.get("offset")
    limit = params.get("limit")
    if start_line is None and isinstance(offset, int):
        start_line = max(1, offset + 1)
    if end_line is None and isinstance(start_line, int) and isinstance(limit, int) and limit > 0:
        end_line = start_line + limit - 1
    mapped = {"path": path}
    if isinstance(start_line, int):
        mapped["start_line"] = start_line
    if isinstance(end_line, int):
        mapped["end_line"] = end_line
    return _execute_alias(context, "Read", mapped)


def _file_edit_tool(params: dict, context: ToolContext) -> ToolResult:
    path = params.get("path") or params.get("file_path")
    old_text = params.get("old_text") or params.get("find")
    new_text = params.get("new_text") or params.get("replace")
    if not path or old_text is None or new_text is None:
        raise ToolError("FileEditTool requires path/file_path and old_text/new_text.")
    return _execute_alias(
        context,
        "Edit",
        {
            "path": path,
            "old_text": old_text,
            "new_text": new_text,
            "replace_all": params.get("replace_all", False),
        },
    )


def _glob_tool(params: dict, context: ToolContext) -> ToolResult:
    pattern = params.get("pattern") or params.get("glob")
    if not pattern:
        raise ToolError("GlobTool requires `pattern`.")
    return _execute_alias(context, "Glob", {"pattern": pattern})


def _grep_tool(params: dict, context: ToolContext) -> ToolResult:
    pattern = params.get("pattern") or params.get("query")
    if not pattern:
        raise ToolError("GrepTool requires `pattern` or `query`.")
    mapped = {
        "pattern": pattern,
        "include": params.get("include", params.get("path", "**/*")),
        "case_sensitive": params.get("case_sensitive", False),
    }
    if "max_results" in params:
        mapped["max_results"] = params["max_results"]
    return _execute_alias(context, "Grep", mapped)


def _memory_read_tool(params: dict, context: ToolContext) -> ToolResult:
    name = params.get("name") or params.get("memory") or params.get("slug")
    if not name:
        raise ToolError("MemoryReadTool requires `name`.")
    return _execute_alias(context, "MemoryRead", {"name": name, "scope": params.get("scope", "all")})


def _memory_write_tool(params: dict, context: ToolContext) -> ToolResult:
    name = params.get("name") or params.get("title")
    description = params.get("description") or params.get("summary") or name
    content = params.get("content") or params.get("memory")
    if not name or content is None:
        raise ToolError("MemoryWriteTool requires `name` and `content`.")
    return _execute_alias(
        context,
        "MemorySave",
        {
            "name": name,
            "description": description,
            "content": content,
            "type": params.get("type", "project"),
            "scope": params.get("scope", context.settings.memory_default_scope),
        },
    )


def _skill_tool(params: dict, context: ToolContext) -> ToolResult:
    name = params.get("name") or params.get("skill")
    if not name:
        raise ToolError("SkillTool requires `name` or `skill`.")
    return _execute_alias(context, "Skill", {"name": name, "args": params.get("args", "")})


def _web_fetch_tool(params: dict, context: ToolContext) -> ToolResult:
    url = params.get("url")
    if not url:
        raise ToolError("WebFetchTool requires `url`.")
    return _execute_alias(context, "WebFetch", {"url": url})


def _web_search_tool(params: dict, context: ToolContext) -> ToolResult:
    query = params.get("query")
    if not query:
        raise ToolError("WebSearchTool requires `query`.")
    return _execute_alias(context, "WebSearch", {"query": query})
