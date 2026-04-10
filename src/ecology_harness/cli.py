from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime
import difflib
import json
import shlex
from typing import Sequence

from ecology_harness.app import EcologyHarnessApp
from ecology_harness.config import HarnessSettings
from ecology_harness.runtime.attachments import inspect_attachment
from ecology_harness.runtime.messages import ChatMessage
from ecology_harness.runtime.providers import ProviderError, list_provider_specs
from ecology_harness.server import run_api_server
from ecology_harness.tools import ToolError
from ecology_harness.ui import ConsoleRenderer, create_repl_reader


SESSION_COMMAND_LINES = [
    "/help       show session commands",
    "/status     show session status",
    "/config     show active runtime configuration",
    "/permissions show or change permission mode",
    "/model      show or change the active model",
    "/session    show current and saved session details",
    "/cost       show current session activity summary",
    "/tools      list built-in tools",
    "/skills     list available skills",
    "/skill-hub [query] browse installed skill packs and matching skills",
    "/skill-view NAME [PATH] inspect a skill or a single file in its bundle",
    "/plugins    list installed plugins",
    "/mcp        list configured MCP servers",
    "/profiles   list available work-style profiles",
    "/heartbeat  show workspace heartbeat status or run `/heartbeat run`",
    "/automations list recurring automation jobs",
    "/checkpoints list recent run checkpoints",
    "/memories   list saved memories",
    "/tasks      list tracked tasks",
    "/providers  list configured provider backends",
    "/sandbox    show sandbox state",
    "/attach PATH add an image or document to the next turn",
    "/image PATH  add an image attachment to the next turn",
    "/doc PATH    add a document attachment to the next turn",
    "/audio PATH  add an audio attachment to the next turn",
    "/video PATH  add a video attachment to the next turn",
    "/attachments show pending attachments",
    "/clear-attachments remove pending attachments",
    "/trace on   enable intermediate step trace",
    "/trace off  disable intermediate step trace",
    "/new        start a fresh conversation",
    "/reset      clear the in-memory conversation",
    "/clear      clear the terminal and redraw the header",
    "/quit       exit the REPL",
    "",
    "Interactive tip: in the REPL, typing / opens command suggestions while you type.",
    "Aliases: use \\help, \\status, \\reset, \\quit, and other session commands with a leading backslash.",
    "Quick tip: enter / or \\ to open this command list instantly.",
    "With the mock provider, use: /tool NAME {json}",
]

SESSION_COMMANDS = {
    "/help",
    "/status",
    "/config",
    "/permissions",
    "/model",
    "/session",
    "/cost",
    "/tools",
    "/skills",
    "/skill-hub",
    "/skill-view",
    "/plugins",
    "/mcp",
    "/profiles",
    "/heartbeat",
    "/automations",
    "/checkpoints",
    "/memories",
    "/tasks",
    "/providers",
    "/sandbox",
    "/attach",
    "/image",
    "/doc",
    "/audio",
    "/video",
    "/attachments",
    "/clear-attachments",
    "/trace",
    "/new",
    "/reset",
    "/clear",
    "/quit",
    "/exit",
}

MODEL_ALIASES = {
    "opus": "claude-opus-4-6",
    "sonnet": "claude-sonnet-4-6",
    "haiku": "claude-haiku-4-5-20251213",
}

PERMISSION_MODE_ALIASES = {
    "danger-full-access": "allow-all",
}

POSITIONAL_ACTIONS = {
    "prompt",
    "repl",
    "status",
    "config",
    "model",
    "permissions",
    "cost",
    "tools",
    "skills",
    "plugins",
    "mcp",
    "profiles",
    "heartbeat",
    "automations",
    "checkpoints",
    "memories",
    "tasks",
    "providers",
    "sandbox",
    "session",
    "tool",
    "skill-hub",
    "skill-view",
    "serve",
}


@dataclass
class ReplState:
    conversation: list[ChatMessage] | None = None
    turn_count: int = 0
    trace_enabled: bool = True
    total_tool_calls: int = 0
    total_steps: int = 0
    last_prompt: str = ""
    pending_attachment_paths: list[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="eh",
        description="Self-evolving Ecology Harness CLI with a natural REPL and command flow.",
        epilog=(
            "Examples:\n"
            "  eh repl\n"
            "  eh status\n"
            "  eh prompt \"summarize this repository\"\n"
            "  eh --attach docs/paper.pdf \"summarize this paper\"\n"
            "  eh --attach imgs/specimen.jpg \"identify this species\"\n"
            "  eh --provider openrouter --model openai/gpt-4.1-mini \"inspect this workspace\"\n"
            "  eh \"review src/ecology_harness/cli.py\"\n"
            "  eh tool Read '{\"path\":\"README.md\"}'\n"
            "  eh --resume latest repl"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--workspace",
        default=".",
        help="Workspace root used by tools. Defaults to the current directory.",
    )
    parser.add_argument(
        "--provider",
        default="auto",
        help="Provider backend. Supported: auto, mock, anthropic, openai, openrouter, gemini, kimi, qwen, zhipu, deepseek, ollama, lmstudio, custom.",
    )
    parser.add_argument(
        "--model",
        default="mock-agent",
        help="Model name used by the provider.",
    )
    parser.add_argument(
        "--base-url",
        default="",
        help="Override the provider base URL.",
    )
    parser.add_argument(
        "--api-key",
        default="",
        help="API key passed directly to the provider.",
    )
    parser.add_argument(
        "--api-key-env",
        default="",
        help="Override the provider API key environment variable.",
    )
    parser.add_argument(
        "--resume",
        default="",
        help="Resume a saved session, for example --resume latest.",
    )
    parser.add_argument(
        "--permission-mode",
        default="workspace-write",
        help="Permission mode: workspace-write, read-only, allow-all, or danger-full-access.",
    )
    parser.add_argument(
        "--sandbox-mode",
        default="workspace-write",
        help="Sandbox mode: workspace-write or read-only.",
    )
    parser.add_argument(
        "--sandbox-backend",
        default="internal",
        help="Sandbox backend: internal, auto, sandbox-exec, disabled.",
    )
    parser.add_argument(
        "--no-sandbox",
        action="store_true",
        help="Disable sandbox policy enforcement.",
    )
    parser.add_argument(
        "--no-network",
        action="store_true",
        help="Disable WebFetch/WebSearch network access in sandbox policy.",
    )
    parser.add_argument(
        "--sandbox-fail-closed",
        action="store_true",
        help="Fail when a requested sandbox backend is unavailable.",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=0,
        help="Maximum tool-use iterations per agent run. Use 0 to disable the limit.",
    )
    parser.add_argument(
        "--provider-timeout",
        type=int,
        default=0,
        help="Maximum seconds to wait for a model provider response. Use 0 to disable the timeout.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host for `eh serve`.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port for `eh serve`.",
    )
    parser.add_argument(
        "-p",
        "--prompt",
        default="",
        help="Run one prompt and exit.",
    )
    parser.add_argument(
        "--attach",
        action="append",
        default=[],
        help="Attach a local image or document to the prompt. Can be repeated.",
    )
    parser.add_argument(
        "--list-tools",
        action="store_true",
        help="List registered tools.",
    )
    parser.add_argument(
        "--list-providers",
        action="store_true",
        help="List supported model providers and example model names.",
    )
    parser.add_argument(
        "--describe-tool",
        metavar="NAME",
        help="Show metadata for a registered tool.",
    )
    parser.add_argument(
        "--exec-tool",
        metavar="NAME",
        help="Execute a registered tool.",
    )
    parser.add_argument(
        "--params",
        default="{}",
        help="JSON object passed to --exec-tool.",
    )
    parser.add_argument(
        "--list-skills",
        action="store_true",
        help="List available skills.",
    )
    parser.add_argument(
        "--skill-hub",
        nargs="?",
        const="",
        default=None,
        metavar="QUERY",
        help="Browse installed skill packs and optionally search them with a query.",
    )
    parser.add_argument(
        "--view-skill",
        default="",
        metavar="NAME",
        help="Inspect a skill and list bundle files.",
    )
    parser.add_argument(
        "--skill-file",
        default="",
        metavar="PATH",
        help="Optional relative file inside the selected skill bundle.",
    )
    parser.add_argument(
        "--list-plugins",
        action="store_true",
        help="List installed plugins.",
    )
    parser.add_argument(
        "--list-mcp-servers",
        action="store_true",
        help="List configured MCP servers.",
    )
    parser.add_argument(
        "--list-memories",
        action="store_true",
        help="List saved memories.",
    )
    parser.add_argument(
        "--list-tasks",
        action="store_true",
        help="List tracked tasks.",
    )
    parser.add_argument(
        "--sandbox-status",
        action="store_true",
        help="Show current sandbox configuration and active backend.",
    )
    parser.add_argument(
        "--repl",
        action="store_true",
        help="Start an interactive REPL.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON output for tool metadata or execution results.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress intermediate trace output for prompt and REPL runs.",
    )
    parser.add_argument(
        "command_args",
        nargs="*",
        help=argparse.SUPPRESS,
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    renderer = ConsoleRenderer()

    settings = HarnessSettings.from_workspace(args.workspace)
    settings.provider = args.provider
    settings.model = _resolve_model_alias(args.model)
    settings.base_url = args.base_url
    settings.api_key = args.api_key
    settings.api_key_env = args.api_key_env
    settings.permission_mode = _resolve_permission_mode(args.permission_mode)
    settings.sandbox_mode = args.sandbox_mode
    settings.sandbox_backend = args.sandbox_backend
    settings.sandbox_enabled = not args.no_sandbox
    settings.sandbox_allow_network = not args.no_network
    settings.sandbox_fail_closed = args.sandbox_fail_closed
    settings.max_agent_loops = args.max_steps
    settings.provider_timeout_sec = args.provider_timeout

    app = EcologyHarnessApp(settings)
    app.initialize()
    resumed_conversation, resume_error = _load_resume(app, renderer, args.resume)
    if resume_error:
        return 1

    if args.list_tools:
        return _list_tools(app, renderer, args.json)
    if args.list_providers:
        return _list_providers(renderer, args.json)
    if args.describe_tool:
        return _describe_tool(app, parser, renderer, args.describe_tool, args.json)
    if args.exec_tool:
        return _exec_tool(app, parser, renderer, args.exec_tool, args.params, args.json)
    if args.list_skills:
        return _list_skills(app, renderer, args.json)
    if args.skill_hub is not None:
        return _skill_hub(app, renderer, args.json, args.skill_hub)
    if args.view_skill:
        return _skill_view(app, renderer, args.json, args.view_skill, args.skill_file)
    if args.list_plugins:
        return _list_plugins(app, renderer, args.json)
    if args.list_mcp_servers:
        return _list_mcp_servers(app, renderer, args.json)
    if args.list_memories:
        return _list_memories(app, renderer, args.json)
    if args.list_tasks:
        return _list_tasks(app, renderer, args.json)
    if args.sandbox_status:
        return _sandbox_status(app, renderer, args.json)
    if args.prompt:
        return _run_prompt(
            app,
            renderer,
            args.prompt,
            args.provider,
            args.json,
            args.quiet,
            conversation=resumed_conversation,
            attachment_paths=args.attach,
        )
    positional_result = _handle_positional_command(
        app,
        parser,
        renderer,
        args.command_args,
        host=args.host,
        port=args.port,
        json_output=args.json,
        quiet=args.quiet,
        conversation=resumed_conversation,
        attachment_paths=args.attach,
    )
    if positional_result is not None:
        return positional_result

    return run_repl(
        app,
        renderer=renderer,
        json_output=args.json,
        show_trace=not args.json and not args.quiet,
        initial_conversation=resumed_conversation,
        initial_attachment_paths=args.attach,
    )


def run_repl(
    app: EcologyHarnessApp,
    renderer: ConsoleRenderer | None = None,
    json_output: bool = False,
    show_trace: bool = True,
    initial_conversation: list[ChatMessage] | None = None,
    initial_attachment_paths: list[str] | None = None,
) -> int:
    console = renderer or ConsoleRenderer()
    state = ReplState(
        conversation=initial_conversation,
        trace_enabled=show_trace,
        pending_attachment_paths=_resolve_attachment_paths(app, initial_attachment_paths or []),
    )
    if initial_conversation:
        state.turn_count = _conversation_turn_count(initial_conversation)
    read_line = create_repl_reader(app, console, state_getter=lambda: state)

    console.banner(app, mode="repl", turn_count=state.turn_count)
    console.print_repl_welcome()
    if initial_conversation:
        console.print_notice(
            "Resumed %s conversation messages from %s."
            % (len(initial_conversation), app.latest_session_path())
        )
    else:
        console.print_notice("Type / for commands, or ask directly in natural language.")
    if state.pending_attachment_paths:
        console.print_notice(
            "Loaded %s pending attachment(s): %s"
            % (
                len(state.pending_attachment_paths),
                ", ".join(_attachment_labels(app, state.pending_attachment_paths)),
            )
        )

    while True:
        try:
            line = read_line(console.prompt_label(app, state.turn_count + 1)).strip()
        except EOFError:
            console.print()
            return 0
        except KeyboardInterrupt:
            console.print()
            return 130

        if not line:
            continue

        command_result = _handle_repl_command(
            app,
            console,
            line,
            json_output=json_output,
            state=state,
        )
        if command_result is not None:
            action = command_result["action"]
            if action == "exit":
                return command_result["code"]
            if action == "continue":
                continue

        try:
            result = app.run_prompt(
                line,
                provider_name=app.settings.provider,
                event_handler=console.build_trace_printer() if state.trace_enabled and not json_output else None,
                conversation=state.conversation,
                attachment_paths=state.pending_attachment_paths,
            )
        except (ToolError, ProviderError) as exc:
            console.print_notice(str(exc), level="error")
            continue

        if result.messages:
            state.conversation = result.messages
        state.turn_count += 1
        state.total_steps += result.steps
        state.total_tool_calls += len(result.tool_invocations)
        state.last_prompt = line
        state.pending_attachment_paths = []

        if json_output:
            print(
                json.dumps(
                    {
                        "final_text": result.final_text,
                        "steps": result.steps,
                        "tool_invocations": result.tool_invocations,
                        "events": [item.to_dict() for item in result.events],
                    },
                    indent=2,
                    ensure_ascii=False,
                )
            )
        else:
            console.print_final_block(
                result.final_text,
                steps=result.steps,
                tool_calls=len(result.tool_invocations),
                tools_used=_tool_names_from_invocations(result.tool_invocations),
            )


def _list_tools(app: EcologyHarnessApp, renderer: ConsoleRenderer, json_output: bool) -> int:
    tools = app.registry.list_tools()
    if json_output:
        print(json.dumps([tool.to_dict() for tool in tools], indent=2, ensure_ascii=False))
        return 0
    rows = [[tool.name, tool.source, tool.description] for tool in tools]
    renderer.print_table("Tools", ["name", "source", "description"], rows)
    return 0


def _list_providers(renderer: ConsoleRenderer, json_output: bool) -> int:
    providers = [item.to_dict() for item in list_provider_specs()]
    if json_output:
        print(json.dumps(providers, indent=2, ensure_ascii=False))
        return 0
    rows = []
    for item in providers:
        location = "local" if item["local"] else "remote"
        examples = ", ".join(item["model_examples"]) or "-"
        rows.append([item["name"], item["protocol"], location, examples])
    renderer.print_table("Providers", ["name", "protocol", "scope", "examples"], rows)
    return 0


def _describe_tool(
    app: EcologyHarnessApp,
    parser: argparse.ArgumentParser,
    renderer: ConsoleRenderer,
    tool_name: str,
    json_output: bool,
) -> int:
    tool = app.registry.get(tool_name)
    if tool is None:
        parser.error("Unknown tool: %s" % tool_name)
    if json_output:
        print(json.dumps(tool.to_dict(), indent=2, ensure_ascii=False))
    else:
        renderer.print_tool_description(tool)
    return 0


def _exec_tool(
    app: EcologyHarnessApp,
    parser: argparse.ArgumentParser,
    renderer: ConsoleRenderer,
    tool_name: str,
    raw_params: str,
    json_output: bool,
) -> int:
    try:
        params = json.loads(raw_params)
    except json.JSONDecodeError as exc:
        parser.error("Invalid --params JSON: %s" % exc)
    try:
        result = app.registry.execute(
            tool_name,
            params,
            app.settings,
            services=app.get_services(),
        )
    except ToolError as exc:
        renderer.print_notice(str(exc), level="error")
        return 1
    if json_output:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    else:
        renderer.section("Tool Result", result.content.splitlines() or ["<empty>"])
    return 0


def _list_skills(app: EcologyHarnessApp, renderer: ConsoleRenderer, json_output: bool) -> int:
    skills = [item.to_index_dict() for item in app.skill_loader.list_skills()]
    if json_output:
        print(json.dumps(skills, indent=2, ensure_ascii=False))
        return 0
    rows = [
        [
            item["slug"],
            item["status"],
            item["readiness"],
            item["usage_count"],
            item["source"],
            item["description"],
        ]
        for item in skills
    ]
    renderer.print_table("Skills", ["slug", "status", "ready", "used", "source", "description"], rows)
    return 0


def _skill_hub(
    app: EcologyHarnessApp,
    renderer: ConsoleRenderer,
    json_output: bool,
    query: str = "",
) -> int:
    result = app.skill_loader.skill_hub(query=query)
    if json_output:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    if result["packs"]:
        rows = [
            [
                item["slug"],
                item["trust_level"],
                item["audit_status"],
                str(item["skill_count"]),
                item["description"],
            ]
            for item in result["packs"]
        ]
        renderer.print_table(
            "Skill Hub Packs",
            ["pack", "trust", "audit", "skills", "description"],
            rows,
        )
    if result["skills"]:
        rows = [
            [
                item["slug"],
                item["hub_pack"],
                item["status"],
                item["readiness"],
                item.get("score", ""),
                item["description"],
            ]
            for item in result["skills"]
        ]
        renderer.print_table(
            "Skill Hub Matches",
            ["skill", "pack", "status", "ready", "score", "description"],
            rows,
        )
    return 0


def _skill_view(
    app: EcologyHarnessApp,
    renderer: ConsoleRenderer,
    json_output: bool,
    name: str,
    file_path: str = "",
) -> int:
    try:
        result = app.skill_loader.view(name, file_path=file_path)
    except ValueError as exc:
        renderer.print_notice(str(exc), level="error")
        return 1
    if json_output:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    skill = result["skill"]
    selected = result["selected_file"]
    renderer.section(
        "Skill View",
        [
            "skill: %s" % skill["slug"],
            "pack: %s" % skill["hub_pack"],
            "trust: %s" % skill["trust_level"],
            "status: %s" % skill["status"],
            "readiness: %s" % skill["readiness"],
            "file: %s" % selected["relative_path"],
        ],
    )
    if result["available_files"]:
        renderer.print_table(
            "Bundle Files",
            ["relative_path", "kind"],
            [[item["relative_path"], item["kind"]] for item in result["available_files"][:20]],
        )
    renderer.section("Content", result["content"].splitlines() or ["<empty>"])
    return 0


def _list_plugins(app: EcologyHarnessApp, renderer: ConsoleRenderer, json_output: bool) -> int:
    result = app.registry.execute(
        "PluginList",
        {},
        app.settings,
        services=app.get_services(),
    )
    if json_output:
        print(json.dumps(result.data["plugins"], indent=2, ensure_ascii=False))
        return 0
    rows = []
    for item in result.data["plugins"]:
        rows.append(
            [
                item["slug"],
                item["source"],
                item["status"],
                "yes" if item["enabled"] else "no",
                item["description"],
            ]
        )
    renderer.print_table("Plugins", ["slug", "source", "status", "enabled", "description"], rows)
    return 0


def _list_mcp_servers(app: EcologyHarnessApp, renderer: ConsoleRenderer, json_output: bool) -> int:
    result = app.registry.execute(
        "ListMcpServersTool",
        {},
        app.settings,
        services=app.get_services(),
    )
    if json_output:
        print(json.dumps(result.data["servers"], indent=2, ensure_ascii=False))
        return 0
    rows = []
    for item in result.data["servers"]:
        rows.append(
            [
                item["server_name"],
                item["transport"],
                item["status"],
                "yes" if item["enabled"] else "no",
                str(item["tool_count"]),
                str(item["resource_count"]),
            ]
        )
    renderer.print_table(
        "MCP Servers",
        ["server", "transport", "status", "enabled", "tools", "resources"],
        rows,
    )
    return 0


def _list_profiles(app: EcologyHarnessApp, renderer: ConsoleRenderer, json_output: bool) -> int:
    result = app.registry.execute(
        "ProfileList",
        {},
        app.settings,
        services=app.get_services(),
    )
    if json_output:
        print(json.dumps(result.data, indent=2, ensure_ascii=False))
        return 0
    rows = [
        [item["name"], "yes" if item["name"] == result.data["active_profile"] else "no", item["description"]]
        for item in result.data["profiles"]
    ]
    renderer.print_table("Profiles", ["name", "active", "description"], rows)
    return 0


def _heartbeat_status(
    app: EcologyHarnessApp,
    renderer: ConsoleRenderer,
    json_output: bool,
    run: bool = False,
    force: bool = False,
) -> int:
    tool_name = "HeartbeatRun" if run else "HeartbeatStatus"
    params = {"force": force} if run else {}
    result = app.registry.execute(
        tool_name,
        params,
        app.settings,
        services=app.get_services(),
    )
    if json_output:
        print(json.dumps(result.data, indent=2, ensure_ascii=False))
        return 0
    if run:
        renderer.section(
            "Heartbeat",
            [
                result.content,
                "next_run_at: %s" % result.data.get("next_run_at", ""),
                "path: %s" % result.data.get("path", ""),
            ],
        )
        return 0
    renderer.section(
        "Heartbeat",
        [
            "enabled: %s" % result.data.get("enabled", False),
            "due: %s" % result.data.get("due", False),
            "last_run_at: %s" % result.data.get("last_run_at", ""),
            "next_run_at: %s" % result.data.get("next_run_at", ""),
            "path: %s" % result.data.get("path", ""),
        ],
    )
    return 0


def _list_automations(app: EcologyHarnessApp, renderer: ConsoleRenderer, json_output: bool) -> int:
    result = app.registry.execute(
        "AutomationList",
        {},
        app.settings,
        services=app.get_services(),
    )
    if json_output:
        print(json.dumps(result.data, indent=2, ensure_ascii=False))
        return 0
    rows = [
        [item["job_id"], item["name"], item["schedule"], item["next_run_at"]]
        for item in result.data["jobs"]
    ]
    renderer.print_table("Automations", ["id", "name", "schedule", "next_run_at"], rows)
    return 0


def _list_checkpoints(app: EcologyHarnessApp, renderer: ConsoleRenderer, json_output: bool) -> int:
    result = app.registry.execute(
        "CheckpointList",
        {},
        app.settings,
        services=app.get_services(),
    )
    if json_output:
        print(json.dumps(result.data, indent=2, ensure_ascii=False))
        return 0
    rows = [
        [item["checkpoint_id"], item["session_id"], item["stage"], item["summary"]]
        for item in result.data["checkpoints"]
    ]
    renderer.print_table("Checkpoints", ["id", "session", "stage", "summary"], rows)
    return 0


def _list_memories(app: EcologyHarnessApp, renderer: ConsoleRenderer, json_output: bool) -> int:
    items = [item.to_index_dict() for item in app.memory_manager.list_items()]
    if json_output:
        print(json.dumps(items, indent=2, ensure_ascii=False))
        return 0
    rows = [[item["slug"], item["description"]] for item in items]
    renderer.print_table("Memories", ["slug", "description"], rows)
    return 0


def _list_tasks(app: EcologyHarnessApp, renderer: ConsoleRenderer, json_output: bool) -> int:
    task_objects = app.task_store.list_tasks()
    tasks = [item.to_dict() for item in task_objects]
    if json_output:
        print(json.dumps(tasks, indent=2, ensure_ascii=False))
        return 0
    if not tasks:
        renderer.section("Tasks", ["No tasks found."])
        return 0
    resolved = {item.id for item in task_objects if item.status == "completed"}
    rows = [[str(item.id), item.status, item.one_line(resolved_ids=resolved)] for item in task_objects]
    renderer.print_table("Tasks", ["id", "status", "summary"], rows)
    return 0


def _sandbox_status(app: EcologyHarnessApp, renderer: ConsoleRenderer, json_output: bool) -> int:
    result = app.registry.execute(
        "SandboxStatus",
        {},
        app.settings,
        services=app.get_services(),
    )
    if json_output:
        print(json.dumps(result.data, indent=2, ensure_ascii=False))
    else:
        renderer.print_sandbox_status(result)
    return 0


def _run_prompt(
    app: EcologyHarnessApp,
    renderer: ConsoleRenderer,
    prompt: str,
    provider_name: str,
    json_output: bool,
    quiet: bool,
    conversation: list[ChatMessage] | None = None,
    attachment_paths: list[str] | None = None,
) -> int:
    normalized_attachments = _resolve_attachment_paths(app, attachment_paths or [])
    event_handler = None
    if not json_output and not quiet:
        renderer.banner(app, mode="prompt")
        renderer.print_prompt_block(
            prompt,
            attachments=_attachment_labels(app, normalized_attachments),
        )
        event_handler = renderer.build_trace_printer()
    try:
        result = app.run_prompt(
            prompt,
            provider_name=provider_name,
            event_handler=event_handler,
            conversation=conversation,
            attachment_paths=normalized_attachments,
        )
    except (ToolError, ProviderError) as exc:
        renderer.print_notice(str(exc), level="error")
        return 1

    if json_output:
        print(
            json.dumps(
                {
                    "final_text": result.final_text,
                    "steps": result.steps,
                    "tool_invocations": result.tool_invocations,
                    "events": [item.to_dict() for item in result.events],
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        renderer.print_final_block(
            result.final_text,
            steps=result.steps,
            tool_calls=len(result.tool_invocations),
            tools_used=_tool_names_from_invocations(result.tool_invocations),
        )
    return 0


def _handle_positional_command(
    app: EcologyHarnessApp,
    parser: argparse.ArgumentParser,
    renderer: ConsoleRenderer,
    command_args: list[str],
    host: str,
    port: int,
    json_output: bool,
    quiet: bool,
    conversation: list[ChatMessage] | None,
    attachment_paths: list[str] | None,
) -> int | None:
    if not command_args:
        return None
    head = command_args[0]
    tail = command_args[1:]

    if head == "repl":
        return run_repl(
            app,
            renderer=renderer,
            json_output=json_output,
            show_trace=not json_output and not quiet,
            initial_conversation=conversation,
            initial_attachment_paths=attachment_paths,
        )
    if head == "prompt":
        if not tail:
            parser.error("`eh prompt` requires text after the command.")
        return _run_prompt(
            app,
            renderer,
            " ".join(tail),
            app.settings.provider,
            json_output,
            quiet,
            conversation=conversation,
            attachment_paths=attachment_paths,
        )
    if head == "status":
        renderer.print_status_panel(
            app,
            turn_count=_conversation_turn_count(conversation),
            conversation_messages=len(conversation or []),
            trace_enabled=not quiet,
        )
        return 0
    if head == "config":
        renderer.print_config_panel(app)
        return 0
    if head == "model":
        if tail:
            app.settings.model = _resolve_model_alias(" ".join(tail))
        renderer.section(
            "Model",
            [
                "active_model: %s" % app.settings.model,
                "provider: %s" % renderer.provider_text(app.settings),
                "aliases: opus, sonnet, haiku",
            ],
        )
        return 0
    if head == "permissions":
        if tail:
            app.settings.permission_mode = _resolve_permission_mode(tail[0].lower())
        renderer.print_permissions_panel(app)
        return 0
    if head == "cost":
        renderer.print_cost_panel(
            total_tool_calls=0,
            total_steps=0,
            turn_count=_conversation_turn_count(conversation),
        )
        return 0
    if head == "tools":
        return _list_tools(app, renderer, json_output)
    if head == "skills":
        return _list_skills(app, renderer, json_output)
    if head == "skill-hub":
        return _skill_hub(app, renderer, json_output, " ".join(tail))
    if head == "skill-view":
        if not tail:
            parser.error("`eh skill-view` requires a skill name.")
        name = tail[0]
        file_path = " ".join(tail[1:]) if len(tail) > 1 else ""
        return _skill_view(app, renderer, json_output, name, file_path)
    if head == "plugins":
        return _list_plugins(app, renderer, json_output)
    if head == "mcp":
        return _list_mcp_servers(app, renderer, json_output)
    if head == "profiles":
        return _list_profiles(app, renderer, json_output)
    if head == "heartbeat":
        run = bool(tail and tail[0] == "run")
        force = bool(run and len(tail) > 1 and tail[1] == "--force")
        return _heartbeat_status(app, renderer, json_output, run=run, force=force)
    if head == "automations":
        return _list_automations(app, renderer, json_output)
    if head == "checkpoints":
        return _list_checkpoints(app, renderer, json_output)
    if head == "memories":
        return _list_memories(app, renderer, json_output)
    if head == "tasks":
        return _list_tasks(app, renderer, json_output)
    if head == "providers":
        return _list_providers(renderer, json_output)
    if head == "sandbox":
        return _sandbox_status(app, renderer, json_output)
    if head == "session":
        if json_output:
            stats = app.session_stats()
            payload = {
                "turn_count": _conversation_turn_count(conversation),
                "conversation_messages": len(conversation or []),
                "latest_session": str(app.latest_session_path()),
                "exists": app.latest_session_path().exists(),
                "stats": stats,
            }
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            return 0
        renderer.print_session_panel(
            app,
            conversation_messages=len(conversation or []),
            turn_count=_conversation_turn_count(conversation),
        )
        return 0
    if head == "tool":
        if not tail:
            parser.error("`eh tool` requires a tool name.")
        tool_name = tail[0]
        raw_params = " ".join(tail[1:]) if len(tail) > 1 else "{}"
        return _exec_tool(app, parser, renderer, tool_name, raw_params, json_output)
    if head == "serve":
        renderer.print_notice("Starting API server on %s:%s" % (host, port))
        run_api_server(app, host=host, port=port)
        return 0

    if head in POSITIONAL_ACTIONS:
        parser.error("Unsupported positional command: %s" % head)

    return _run_prompt(
        app,
        renderer,
        " ".join(command_args),
        app.settings.provider,
        json_output,
        quiet,
        conversation=conversation,
        attachment_paths=attachment_paths,
    )


def _handle_repl_command(
    app: EcologyHarnessApp,
    renderer: ConsoleRenderer,
    line: str,
    json_output: bool,
    state: ReplState,
):
    del json_output
    normalized, treat_as_session_command = _normalize_repl_command(line)

    if normalized in {"/", "/?"}:
        renderer.section("Commands", SESSION_COMMAND_LINES)
        return {"action": "continue"}

    if treat_as_session_command and not _matches_session_command(normalized):
        suggestion = _suggest_session_command(normalized)
        message = "Unknown session command: %s" % line
        if suggestion:
            message += ". Did you mean %s?" % suggestion
        else:
            message += ". Type / or \\ for the command list."
        renderer.print_notice(message, level="warn")
        return {"action": "continue"}

    if normalized in {"/quit", "/exit"}:
        return {"action": "exit", "code": 0}
    if normalized == "/help":
        renderer.section("Commands", SESSION_COMMAND_LINES)
        return {"action": "continue"}
    if normalized == "/status":
        renderer.print_status_panel(
            app,
            turn_count=state.turn_count,
            conversation_messages=len(state.conversation or []),
            trace_enabled=state.trace_enabled,
            total_tool_calls=state.total_tool_calls,
            total_steps=state.total_steps,
        )
        return {"action": "continue"}
    if normalized == "/config":
        renderer.print_config_panel(app)
        return {"action": "continue"}
    if normalized.startswith("/permissions"):
        parts = normalized.split()
        if len(parts) > 1:
            app.settings.permission_mode = _resolve_permission_mode(parts[1].lower())
            renderer.print_notice("permission_mode=%s" % app.settings.permission_mode)
        renderer.print_permissions_panel(app)
        return {"action": "continue"}
    if normalized.startswith("/model"):
        parts = normalized.split(None, 1)
        if len(parts) > 1:
            app.settings.model = _resolve_model_alias(parts[1].strip())
            renderer.print_notice("model=%s" % app.settings.model)
        renderer.section(
            "Model",
            [
                "active_model: %s" % app.settings.model,
                "provider: %s" % renderer.provider_text(app.settings),
                "aliases: opus, sonnet, haiku",
            ],
        )
        return {"action": "continue"}
    if normalized == "/session":
        renderer.print_session_panel(
            app,
            conversation_messages=len(state.conversation or []),
            turn_count=state.turn_count,
        )
        return {"action": "continue"}
    if normalized == "/cost":
        renderer.print_cost_panel(
            total_tool_calls=state.total_tool_calls,
            total_steps=state.total_steps,
            turn_count=state.turn_count,
        )
        return {"action": "continue"}
    if normalized == "/tools":
        _list_tools(app, renderer, False)
        return {"action": "continue"}
    if normalized == "/skills":
        _list_skills(app, renderer, False)
        return {"action": "continue"}
    if normalized.startswith("/skill-hub"):
        query = normalized.split(None, 1)[1] if " " in normalized else ""
        _skill_hub(app, renderer, False, query)
        return {"action": "continue"}
    if normalized.startswith("/skill-view"):
        parts = normalized.split(None, 2)
        if len(parts) < 2:
            renderer.print_notice("Usage: /skill-view <name> [file_path]", level="warn")
            return {"action": "continue"}
        name = parts[1]
        file_path = parts[2] if len(parts) > 2 else ""
        _skill_view(app, renderer, False, name, file_path)
        return {"action": "continue"}
    if normalized == "/plugins":
        _list_plugins(app, renderer, False)
        return {"action": "continue"}
    if normalized == "/mcp":
        _list_mcp_servers(app, renderer, False)
        return {"action": "continue"}
    if normalized == "/profiles":
        _list_profiles(app, renderer, False)
        return {"action": "continue"}
    if normalized.startswith("/heartbeat"):
        parts = normalized.split()
        run = len(parts) > 1 and parts[1] == "run"
        force = len(parts) > 2 and parts[2] == "--force"
        _heartbeat_status(app, renderer, False, run=run, force=force)
        return {"action": "continue"}
    if normalized == "/automations":
        _list_automations(app, renderer, False)
        return {"action": "continue"}
    if normalized == "/checkpoints":
        _list_checkpoints(app, renderer, False)
        return {"action": "continue"}
    if normalized == "/memories":
        _list_memories(app, renderer, False)
        return {"action": "continue"}
    if normalized == "/tasks":
        _list_tasks(app, renderer, False)
        return {"action": "continue"}
    if normalized == "/providers":
        _list_providers(renderer, False)
        return {"action": "continue"}
    if normalized == "/sandbox":
        _sandbox_status(app, renderer, False)
        return {"action": "continue"}
    if normalized == "/attachments":
        if not state.pending_attachment_paths:
            renderer.print_notice("No pending attachments.")
            return {"action": "continue"}
        renderer.section(
            "Pending Attachments",
            [
                "- %s" % item
                for item in _attachment_labels(app, state.pending_attachment_paths)
            ],
        )
        return {"action": "continue"}
    if normalized == "/clear-attachments":
        state.pending_attachment_paths = []
        renderer.print_notice("Pending attachments cleared.")
        return {"action": "continue"}
    if (
        normalized.startswith("/attach")
        or normalized.startswith("/image")
        or normalized.startswith("/doc")
        or normalized.startswith("/audio")
        or normalized.startswith("/video")
    ):
        parts = normalized.split(None, 1)
        if len(parts) == 1:
            renderer.print_notice("Usage: %s <path>" % parts[0], level="warn")
            return {"action": "continue"}
        try:
            raw_paths = shlex.split(parts[1])
        except ValueError as exc:
            renderer.print_notice("Invalid attachment path: %s" % exc, level="error")
            return {"action": "continue"}
        try:
            resolved = _resolve_attachment_paths(app, raw_paths)
        except ToolError as exc:
            renderer.print_notice(str(exc), level="error")
            return {"action": "continue"}
        state.pending_attachment_paths.extend(
            item for item in resolved if item not in state.pending_attachment_paths
        )
        renderer.print_notice(
            "Pending attachments: %s"
            % ", ".join(_attachment_labels(app, state.pending_attachment_paths))
        )
        return {"action": "continue"}
    if normalized.startswith("/trace"):
        parts = normalized.split()
        if len(parts) == 1:
            renderer.print_notice("trace=%s" % ("on" if state.trace_enabled else "off"))
            next_trace = state.trace_enabled
        else:
            next_trace = parts[1].lower() not in {"off", "false", "0"}
            renderer.print_notice("trace=%s" % ("on" if next_trace else "off"))
        state.trace_enabled = next_trace
        return {"action": "continue"}
    if normalized in {"/new", "/reset"}:
        renderer.print_notice("Conversation context cleared.")
        app.start_new_session()
        state.conversation = None
        state.turn_count = 0
        state.total_tool_calls = 0
        state.total_steps = 0
        state.last_prompt = ""
        return {"action": "continue"}
    if normalized == "/clear":
        renderer.clear_screen()
        renderer.banner(app, mode="repl", turn_count=state.turn_count)
        renderer.print_repl_welcome()
        return {"action": "continue"}
    return None


def _conversation_turn_count(conversation: list[ChatMessage] | None) -> int:
    if not conversation:
        return 0
    return len([item for item in conversation if item.role == "user"])


def _load_resume(
    app: EcologyHarnessApp,
    renderer: ConsoleRenderer,
    resume_name: str,
) -> tuple[list[ChatMessage] | None, bool]:
    if not resume_name:
        return None, False
    try:
        return app.load_session(resume_name), False
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        renderer.print_notice(str(exc), level="error")
        return None, True


def _resolve_model_alias(model: str) -> str:
    normalized = (model or "").strip()
    if not normalized:
        return normalized
    return MODEL_ALIASES.get(normalized.lower(), normalized)


def _resolve_permission_mode(mode: str) -> str:
    normalized = (mode or "").strip().lower()
    if not normalized:
        return normalized
    return PERMISSION_MODE_ALIASES.get(normalized, normalized)


def _tool_names_from_invocations(tool_invocations: list[dict]) -> list[str]:
    names = []
    for item in tool_invocations:
        name = str(item.get("tool", ""))
        if name and name not in names:
            names.append(name)
    return names


def _normalize_repl_command(line: str) -> tuple[str, bool]:
    stripped = line.strip()
    if not stripped:
        return stripped, False
    if stripped in {"/", "/?", "\\", "\\?"}:
        return "/", True
    if stripped.startswith("\\"):
        return "/" + stripped[1:], True
    return stripped, False


def _matches_session_command(command: str) -> bool:
    base = command.split(" ", 1)[0]
    return base in SESSION_COMMANDS


def _suggest_session_command(command: str) -> str:
    base = command.split(" ", 1)[0]
    matches = difflib.get_close_matches(base, sorted(SESSION_COMMANDS), n=1, cutoff=0.55)
    if not matches:
        return ""
    suggestion = matches[0]
    remainder = command.split(" ", 1)[1] if " " in command else ""
    if remainder:
        return "%s %s" % (suggestion, remainder)
    return suggestion


def _resolve_attachment_paths(app: EcologyHarnessApp, raw_paths: list[str]) -> list[str]:
    resolved = []
    for raw_path in raw_paths:
        if not raw_path:
            continue
        info = inspect_attachment(
            raw_path,
            app.settings,
            sandbox=getattr(app, "sandbox", None),
        )
        candidate = str(info.resolved_path)
        if candidate not in resolved:
            resolved.append(candidate)
    return resolved


def _attachment_labels(app: EcologyHarnessApp, attachment_paths: list[str]) -> list[str]:
    labels = []
    for raw_path in attachment_paths:
        try:
            info = inspect_attachment(
                raw_path,
                app.settings,
                sandbox=getattr(app, "sandbox", None),
            )
        except ToolError:
            labels.append(raw_path)
            continue
        labels.append("%s: %s" % (info.kind, info.display_path))
    return labels


if __name__ == "__main__":
    raise SystemExit(main())
