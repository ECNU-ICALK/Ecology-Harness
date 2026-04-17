from __future__ import annotations

import argparse
from dataclasses import replace
from dataclasses import dataclass, field
from datetime import datetime
import difflib
import json
import shlex
import sys
from typing import Sequence

from ecology_harness.app import EcologyHarnessApp
from ecology_harness.config import HarnessSettings
from ecology_harness.runtime.attachments import inspect_attachment
from ecology_harness.runtime.messages import ChatMessage
from ecology_harness.runtime.providers import ProviderError, list_provider_specs
from ecology_harness.server import run_api_server
from ecology_harness.tools import ToolError
from ecology_harness.ui import ConsoleRenderer, create_repl_reader, select_list_option


SESSION_COMMAND_LINES = [
    "/help       show session commands",
    "/doctor     run an environment and workspace health report",
    "/setup      scaffold workspace bootstrap files",
    "/explore    run a read-only exploration pass over the workspace",
    "/status     show session status",
    "/runtime    show a live runtime snapshot",
    "/analytics  summarize recent usage, sessions, and trajectories",
    "/config     show active runtime configuration",
    "/permissions show or change permission mode",
    "/model      show or change the active model",
    "/session    show current and saved session details",
    "/sessions   list or search saved sessions",
    "/resume [ID] load a saved session, or choose one interactively",
    "/cost       show current session activity summary",
    "/tools      list built-in tools",
    "/skills     list available skills",
    "/skill-hub [query] browse installed skill packs and matching skills",
    "/skill-view NAME [PATH] inspect a skill or a single file in its bundle",
    "/plugins    list installed plugins",
    "/integrations list configured external integrations",
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
    "/doctor",
    "/setup",
    "/explore",
    "/status",
    "/runtime",
    "/analytics",
    "/config",
    "/permissions",
    "/model",
    "/session",
    "/sessions",
    "/resume",
    "/cost",
    "/tools",
    "/skills",
    "/skill-hub",
    "/skill-view",
    "/plugins",
    "/integrations",
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
    "ask-before-write": "ask",
}

POSITIONAL_ACTIONS = {
    "prompt",
    "repl",
    "doctor",
    "setup",
    "explore",
    "clarify",
    "deep-interview",
    "ralplan",
    "ralph",
    "status",
    "runtime",
    "analytics",
    "config",
    "model",
    "permissions",
    "cost",
    "tools",
    "skills",
    "plugins",
    "integrations",
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
    "sessions",
    "resume",
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
            "  eh doctor --probe\n"
            "  eh setup\n"
            "  eh explore \"summarize the codebase without making changes\"\n"
            "  eh clarify \"help me define the right task boundaries\"\n"
            "  eh status\n"
            "  eh runtime\n"
            "  eh analytics\n"
            "  eh prompt \"summarize this repository\"\n"
            "  eh --attach docs/paper.pdf \"summarize this paper\"\n"
            "  eh --attach imgs/specimen.jpg \"identify this species\"\n"
            "  eh --provider openrouter --model openai/gpt-4.1-mini \"inspect this workspace\"\n"
            "  eh \"review src/ecology_harness/cli.py\"\n"
            "  eh tool Read '{\"path\":\"README.md\"}'\n"
            "  eh --resume latest repl\n"
            "  eh sessions\n"
            "  eh sessions search 湿地 甲烷\n"
            "  eh resume\n"
            "  eh resume latest\n"
            "  eh integrations\n"
            "  eh integrations add feishu-webhook --name default --webhook-url https://open.feishu.cn/open-apis/bot/v2/hook/..."
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
        help="Permission mode: workspace-write, ask, read-only, allow-all, or danger-full-access.",
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
        "--probe",
        action="store_true",
        help="When used with `eh doctor`, probe MCP server availability.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="When used with `eh setup`, overwrite existing bootstrap files.",
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
        "--provider-fallback",
        action="append",
        default=[],
        help="Fallback provider(s) to try after the primary provider, for example --provider-fallback openai.",
    )
    parser.add_argument(
        "--provider-retry-attempts",
        type=int,
        default=1,
        help="Retry attempts per provider before falling back. Defaults to 1.",
    )
    parser.add_argument(
        "--provider-retry-backoff-ms",
        type=int,
        default=150,
        help="Backoff in milliseconds between retry attempts. Defaults to 150.",
    )
    parser.add_argument(
        "--provider-pool-strategy",
        default="fill-first",
        help="API key pool strategy: fill-first, round-robin, or least-used.",
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
    raw_argv = list(argv) if argv is not None else list(sys.argv[1:])
    parser = build_parser()
    args, extras = parser.parse_known_args(raw_argv)
    if extras:
        if args.command_args:
            args.command_args.extend(extras)
        else:
            parser.error("unrecognized arguments: %s" % " ".join(extras))
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
    settings.provider_fallbacks = tuple(str(item).strip() for item in args.provider_fallback if str(item).strip())
    settings.provider_retry_attempts = max(int(args.provider_retry_attempts or 1), 1)
    settings.provider_retry_backoff_ms = max(int(args.provider_retry_backoff_ms or 0), 0)
    settings.provider_pool_strategy = str(args.provider_pool_strategy or "fill-first").strip().lower() or "fill-first"
    if _should_prompt_for_permission_choice(raw_argv, args):
        settings.permission_mode = _prompt_for_permission_mode(renderer, settings.permission_mode)

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
        probe=args.probe,
        force=args.force,
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
    previous_handler = app.get_permission_request_handler() if hasattr(app, "get_permission_request_handler") else None
    app.set_permission_request_handler(_build_permission_request_handler(console))
    if initial_conversation:
        state.turn_count = _conversation_turn_count(initial_conversation)
    try:
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
    finally:
        app.set_permission_request_handler(previous_handler)


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


def _list_integrations(app: EcologyHarnessApp, renderer: ConsoleRenderer, json_output: bool) -> int:
    result = app.registry.execute(
        "IntegrationList",
        {},
        app.settings,
        services=app.get_services(),
    )
    items = result.data.get("integrations", [])
    if json_output:
        print(json.dumps(items, indent=2, ensure_ascii=False))
        return 0
    if not items:
        renderer.section(
            "Integrations",
            [
                "No integrations configured.",
                "Tip: eh integrations add feishu-webhook --name default --webhook-url https://open.feishu.cn/open-apis/bot/v2/hook/...",
            ],
        )
        return 0
    rows = [
        [
            item["name"],
            item["kind"],
            item["status"],
            "yes" if item["enabled"] else "no",
            item.get("config", {}).get("webhook_url", "-"),
        ]
        for item in items
    ]
    renderer.print_table("Integrations", ["name", "kind", "status", "enabled", "endpoint"], rows)
    return 0


def _add_feishu_integration(
    app: EcologyHarnessApp,
    renderer: ConsoleRenderer,
    json_output: bool,
    *,
    name: str,
    webhook_url: str,
    secret: str = "",
    notes: str = "",
) -> int:
    manager = app.integration_manager
    if manager is None:
        renderer.print_notice("integration_manager service is unavailable.", level="error")
        return 1
    try:
        item = manager.configure_feishu_webhook(
            name=name,
            webhook_url=webhook_url,
            secret=secret,
            notes=notes,
        )
    except ValueError as exc:
        renderer.print_notice(str(exc), level="error")
        return 1
    if json_output:
        print(json.dumps(item, indent=2, ensure_ascii=False))
        return 0
    renderer.section(
        "Integration Added",
        [
            "name: %s" % item["name"],
            "kind: %s" % item["kind"],
            "status: %s" % item["status"],
            "endpoint: %s" % item.get("config", {}).get("webhook_url", ""),
        ],
    )
    return 0


def _test_integration(
    app: EcologyHarnessApp,
    renderer: ConsoleRenderer,
    json_output: bool,
    *,
    name: str,
    message: str,
    title: str = "",
) -> int:
    try:
        result = app.registry.execute(
            "FeishuNotify",
            {"name": name, "text": message, "title": title},
            app.settings,
            services=app.get_services(),
        )
    except ToolError as exc:
        renderer.print_notice(str(exc), level="error")
        return 1
    if json_output:
        print(json.dumps(result.data, indent=2, ensure_ascii=False))
        return 0
    renderer.section("Integration Test", result.content.splitlines() or ["<empty>"])
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


def _list_sessions(app: EcologyHarnessApp, renderer: ConsoleRenderer, json_output: bool) -> int:
    sessions = app.list_sessions()
    payload = [
        {
            "session_id": item.session_id,
            "updated_at": item.updated_at,
            "message_count": item.message_count,
            "title": item.title,
            "recap": item.recap,
            "parent_session_id": item.parent_session_id,
            "path": str(item.path),
        }
        for item in sessions
    ]
    if json_output:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0
    if not payload:
        renderer.section("Sessions", ["No saved sessions found."])
        return 0
    rows = [
        [
            item["session_id"],
            item["updated_at"],
            str(item["message_count"]),
            item["title"] or "-",
            _truncate_cli_text(item["recap"] or "-", 72),
        ]
        for item in payload[:20]
    ]
    renderer.print_table("Sessions", ["id", "updated_at", "msgs", "title", "recap"], rows)
    return 0


def _search_sessions(app: EcologyHarnessApp, renderer: ConsoleRenderer, json_output: bool, query: str) -> int:
    report = app.search_sessions(query)
    payload = report.to_dict()
    if json_output:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0
    if not report.hits:
        renderer.section("Session Search", ["query: %s" % query, "No matching sessions found."])
        return 0
    rows = [
        [
            item.session_id,
            item.updated_at,
            str(item.message_count),
            item.title or "-",
            _truncate_cli_text(
                (item.message_matches[0].excerpt if item.message_matches else item.excerpt) or "-",
                72,
            ),
        ]
        for item in report.hits
    ]
    renderer.print_table("Session Search", ["id", "updated_at", "msgs", "title", "excerpt"], rows)
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


def _doctor(app: EcologyHarnessApp, renderer: ConsoleRenderer, json_output: bool, probe: bool = False) -> int:
    result = app.registry.execute(
        "DoctorReport",
        {"probe_mcp": probe},
        app.settings,
        services=app.get_services(),
    )
    if json_output:
        print(json.dumps(result.data, indent=2, ensure_ascii=False))
        return 0
    report = result.data
    runtime = report.get("runtime", {})
    bootstrap = report.get("bootstrap", {})
    deps = report.get("dependencies", {})
    mcp = report.get("mcp", {})
    renderer.section(
        "Doctor",
        [
            "workspace: %s" % report.get("workspace", {}).get("root", ""),
            "provider: %s / %s" % (runtime.get("provider", ""), runtime.get("model", "")),
            "profile: %s" % runtime.get("profile", ""),
            "bootstrap_files: %s present, %s missing"
            % (bootstrap.get("present_count", 0), bootstrap.get("missing_count", 0)),
            "mcp: %s server(s), statuses=%s" % (mcp.get("total", 0), mcp.get("status_counts", {})),
            "integrations: %s, statuses=%s"
            % (
                report.get("integrations", {}).get("total", 0),
                report.get("integrations", {}).get("status_counts", {}),
            ),
            "deps: prompt_toolkit=%s playwright=%s ffmpeg=%s"
            % (
                deps.get("prompt_toolkit", {}).get("available", False),
                deps.get("playwright", {}).get("available", False),
                deps.get("ffmpeg", {}).get("available", False),
            ),
        ],
    )
    issues = report.get("issues", [])
    if issues:
        renderer.section("Doctor Issues", ["- %s" % item for item in issues])
    else:
        renderer.section("Doctor Issues", ["No blocking issues detected."])
    suggestions = report.get("suggestions", [])
    if suggestions:
        renderer.section(
            "Doctor Suggestions",
            [
                "- %(title)s :: %(reason)s"
                % item
                + (" [run: %s]" % item["command"] if item.get("command") else "")
                for item in suggestions
            ],
        )
    return 0


def _runtime_status(app: EcologyHarnessApp, renderer: ConsoleRenderer, json_output: bool, conversation=None) -> int:
    result = app.registry.execute(
        "RuntimeStatus",
        {},
        app.settings,
        services=app.get_services(conversation=conversation),
    )
    if json_output:
        print(json.dumps(result.data, indent=2, ensure_ascii=False))
        return 0
    renderer.section("Runtime", result.content.splitlines() or ["<empty>"])
    return 0


def _analytics_summary(app: EcologyHarnessApp, renderer: ConsoleRenderer, json_output: bool) -> int:
    result = app.registry.execute(
        "AnalyticsSummary",
        {},
        app.settings,
        services=app.get_services(),
    )
    if json_output:
        print(json.dumps(result.data, indent=2, ensure_ascii=False))
        return 0
    renderer.section("Analytics", result.content.splitlines() or ["<empty>"])
    return 0


def _setup_workspace(
    app: EcologyHarnessApp,
    renderer: ConsoleRenderer,
    json_output: bool,
    force: bool = False,
    files: list[str] | None = None,
) -> int:
    result = app.registry.execute(
        "WorkspaceBootstrapInit",
        {"force": force, "files": files or []},
        app.settings,
        services=app.get_services(),
    )
    if json_output:
        print(json.dumps(result.data, indent=2, ensure_ascii=False))
        return 0
    data = result.data
    renderer.section(
        "Workspace Setup",
        [
            "created: %s" % (", ".join(data.get("created", [])) or "-"),
            "updated: %s" % (", ".join(data.get("updated", [])) or "-"),
            "skipped: %s" % (", ".join(data.get("skipped", [])) or "-"),
            "invalid: %s" % (", ".join(data.get("invalid", [])) or "-"),
        ],
    )
    return 0


def _run_explore(
    app: EcologyHarnessApp,
    renderer: ConsoleRenderer,
    prompt: str,
    provider_name: str,
    json_output: bool,
    quiet: bool,
    conversation: list[ChatMessage] | None = None,
    attachment_paths: list[str] | None = None,
) -> int:
    read_only_settings = replace(
        app.settings,
        permission_mode="read-only",
        sandbox_mode="read-only",
    )
    allowed_tools = {item.name for item in app.registry.list_tools() if item.read_only}
    previous_mode = app.runtime_mode
    app.runtime_mode = "explore"
    try:
        return _run_prompt(
            app,
            renderer,
            prompt,
            provider_name,
            json_output,
            quiet,
            conversation=conversation,
            attachment_paths=attachment_paths,
            settings=read_only_settings,
            allowed_tools=allowed_tools,
            mode_label="explore",
        )
    finally:
        app.runtime_mode = previous_mode


def _resume_into_repl(
    app: EcologyHarnessApp,
    renderer: ConsoleRenderer,
    json_output: bool,
    quiet: bool,
    reference: str,
    attachment_paths: list[str] | None = None,
) -> int:
    selected_reference = reference.strip()
    if not selected_reference:
        selected_reference = _select_session_reference(app, renderer)
        if not selected_reference:
            renderer.print_notice("Resume cancelled.", level="warn")
            return 0
    try:
        conversation = app.load_session(selected_reference)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        renderer.print_notice(str(exc), level="error")
        return 1
    return run_repl(
        app,
        renderer=renderer,
        json_output=json_output,
        show_trace=not json_output and not quiet,
        initial_conversation=conversation,
        initial_attachment_paths=attachment_paths,
    )


def _select_session_reference(app: EcologyHarnessApp, renderer: ConsoleRenderer) -> str:
    sessions = app.list_sessions()
    if not sessions:
        renderer.print_notice("No saved sessions found.", level="warn")
        return ""
    options: list[tuple[str, str]] = []
    for item in sessions[:20]:
        label = "%s | %s msgs | %s | %s" % (
            item.updated_at,
            item.message_count,
            item.session_id,
            _truncate_cli_text(item.title or item.recap or "-", 72),
        )
        options.append((item.session_id, label))
    return select_list_option(
        title="Resume Session",
        text="Use ↑↓ to choose a saved session, then press Enter.",
        options=options,
        default=options[0][0],
    )


def _run_prompt(
    app: EcologyHarnessApp,
    renderer: ConsoleRenderer,
    prompt: str,
    provider_name: str,
    json_output: bool,
    quiet: bool,
    conversation: list[ChatMessage] | None = None,
    attachment_paths: list[str] | None = None,
    settings: HarnessSettings | None = None,
    allowed_tools: set[str] | None = None,
    mode_label: str = "prompt",
) -> int:
    normalized_attachments = _resolve_attachment_paths(app, attachment_paths or [])
    event_handler = None
    previous_handler = app.get_permission_request_handler() if hasattr(app, "get_permission_request_handler") else None
    permission_handler = _build_permission_request_handler(renderer)
    if not json_output and not quiet:
        renderer.banner(app, mode=mode_label)
        renderer.print_prompt_block(
            prompt,
            attachments=_attachment_labels(app, normalized_attachments),
        )
        event_handler = renderer.build_trace_printer()
    try:
        app.set_permission_request_handler(permission_handler)
        result = app.run_prompt(
            prompt,
            provider_name=provider_name,
            allowed_tools=allowed_tools,
            settings=settings,
            event_handler=event_handler,
            conversation=conversation,
            attachment_paths=normalized_attachments,
        )
    except (ToolError, ProviderError) as exc:
        renderer.print_notice(str(exc), level="error")
        return 1
    finally:
        app.set_permission_request_handler(previous_handler)

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
    probe: bool,
    force: bool,
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
    if head == "doctor":
        effective_probe = probe or bool(tail and tail[0] == "--probe")
        return _doctor(app, renderer, json_output, probe=effective_probe)
    if head == "setup":
        effective_force = force or "--force" in tail
        files = [item for item in tail if item != "--force"]
        return _setup_workspace(app, renderer, json_output, force=effective_force, files=files)
    if head == "explore":
        if not tail:
            parser.error("`eh explore` requires text after the command.")
        return _run_explore(
            app,
            renderer,
            " ".join(tail),
            app.settings.provider,
            json_output,
            quiet,
            conversation=conversation,
            attachment_paths=attachment_paths,
        )
    if head in {"clarify", "deep-interview"}:
        if not tail:
            parser.error("`eh %s` requires text after the command." % head)
        return _run_prompt(
            app,
            renderer,
            "/deep-interview %s" % " ".join(tail),
            app.settings.provider,
            json_output,
            quiet,
            conversation=conversation,
            attachment_paths=attachment_paths,
        )
    if head == "ralplan":
        if not tail:
            parser.error("`eh ralplan` requires text after the command.")
        return _run_prompt(
            app,
            renderer,
            "/ralplan %s" % " ".join(tail),
            app.settings.provider,
            json_output,
            quiet,
            conversation=conversation,
            attachment_paths=attachment_paths,
        )
    if head == "ralph":
        if not tail:
            parser.error("`eh ralph` requires text after the command.")
        return _run_prompt(
            app,
            renderer,
            "/ralph %s" % " ".join(tail),
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
    if head == "runtime":
        return _runtime_status(app, renderer, json_output, conversation=conversation)
    if head == "analytics":
        return _analytics_summary(app, renderer, json_output)
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
    if head == "integrations":
        parts = list(command_args)
        if len(parts) == 1:
            return _list_integrations(app, renderer, json_output)
        if parts[1] == "add":
            if len(parts) < 3 or parts[2] != "feishu-webhook":
                parser.error("`eh integrations add` currently supports `feishu-webhook`.")
            name = ""
            webhook_url = ""
            secret = ""
            notes = ""
            index = 3
            while index < len(parts):
                token = parts[index]
                next_value = parts[index + 1] if index + 1 < len(parts) else ""
                if token == "--name" and next_value:
                    name = next_value
                    index += 2
                    continue
                if token == "--webhook-url" and next_value:
                    webhook_url = next_value
                    index += 2
                    continue
                if token == "--secret" and next_value:
                    secret = next_value
                    index += 2
                    continue
                if token == "--notes" and next_value:
                    notes = next_value
                    index += 2
                    continue
                parser.error("Unknown or incomplete integrations add option: %s" % token)
            if not name or not webhook_url:
                parser.error("`eh integrations add feishu-webhook` requires --name and --webhook-url.")
            return _add_feishu_integration(
                app,
                renderer,
                json_output,
                name=name,
                webhook_url=webhook_url,
                secret=secret,
                notes=notes,
            )
        if parts[1] == "test":
            if len(parts) < 3:
                parser.error("`eh integrations test` requires an integration name.")
            name = parts[2]
            title = ""
            message_tokens: list[str] = []
            index = 3
            while index < len(parts):
                token = parts[index]
                next_value = parts[index + 1] if index + 1 < len(parts) else ""
                if token == "--title" and next_value:
                    title = next_value
                    index += 2
                    continue
                message_tokens.append(token)
                index += 1
            message = " ".join(message_tokens).strip() or "Ecology Harness integration test"
            return _test_integration(
                app,
                renderer,
                json_output,
                name=name,
                message=message,
                title=title,
            )
        parser.error("Unknown integrations subcommand: %s" % parts[1])
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
    if head == "sessions":
        if tail and tail[0] == "search":
            query = " ".join(tail[1:]).strip()
            if not query:
                parser.error("`eh sessions search` requires a query.")
            return _search_sessions(app, renderer, json_output, query)
        return _list_sessions(app, renderer, json_output)
    if head == "resume":
        reference = " ".join(tail).strip()
        return _resume_into_repl(
            app,
            renderer,
            json_output=json_output,
            quiet=quiet,
            reference=reference,
            attachment_paths=attachment_paths,
        )
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
    if normalized == "/doctor":
        _doctor(app, renderer, False)
        return {"action": "continue"}
    if normalized.startswith("/setup"):
        parts = normalized.split()
        force = "--force" in parts[1:]
        files = [item for item in parts[1:] if item != "--force"]
        _setup_workspace(app, renderer, False, force=force, files=files)
        return {"action": "continue"}
    if normalized.startswith("/explore"):
        parts = normalized.split(None, 1)
        if len(parts) < 2:
            renderer.print_notice("Usage: /explore <prompt>", level="warn")
            return {"action": "continue"}
        _run_explore(
            app,
            renderer,
            parts[1],
            app.settings.provider,
            False,
            not state.trace_enabled,
            conversation=state.conversation,
            attachment_paths=state.pending_attachment_paths,
        )
        state.pending_attachment_paths = []
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
    if normalized == "/runtime":
        _runtime_status(app, renderer, False, conversation=state.conversation)
        return {"action": "continue"}
    if normalized == "/analytics":
        _analytics_summary(app, renderer, False)
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
    if normalized == "/sessions":
        _list_sessions(app, renderer, False)
        return {"action": "continue"}
    if normalized.startswith("/sessions search"):
        parts = normalized.split(None, 2)
        if len(parts) < 3:
            renderer.print_notice("Usage: /sessions search <query>", level="warn")
            return {"action": "continue"}
        _search_sessions(app, renderer, False, parts[2])
        return {"action": "continue"}
    if normalized.startswith("/resume"):
        parts = normalized.split(None, 1)
        reference = parts[1].strip() if len(parts) > 1 else ""
        if not reference:
            reference = _select_session_reference(app, renderer)
            if not reference:
                renderer.print_notice("Resume cancelled.", level="warn")
                return {"action": "continue"}
        try:
            state.conversation = app.load_session(reference)
        except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
            renderer.print_notice(str(exc), level="error")
            return {"action": "continue"}
        state.turn_count = _conversation_turn_count(state.conversation)
        state.total_tool_calls = 0
        state.total_steps = 0
        state.last_prompt = ""
        state.pending_attachment_paths = []
        renderer.print_notice("Resumed session %s." % reference)
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
    if normalized == "/integrations":
        _list_integrations(app, renderer, False)
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


def _is_interactive_terminal() -> bool:
    return bool(getattr(sys.stdin, "isatty", lambda: False)()) and bool(
        getattr(sys.stdout, "isatty", lambda: False)()
    )


def _should_prompt_for_permission_choice(raw_argv: Sequence[str], args) -> bool:
    if not _is_interactive_terminal():
        return False
    if any(item == "--permission-mode" or item.startswith("--permission-mode=") for item in raw_argv):
        return False
    if args.prompt or args.list_tools or args.list_providers or args.describe_tool or args.exec_tool:
        return False
    if args.command_args and args.command_args[0] not in {"repl"}:
        return False
    return True


def _prompt_for_permission_mode(renderer: ConsoleRenderer, current_mode: str) -> str:
    renderer.section(
        "Permissions",
        [
            "Choose a starting permission mode for this session.",
            "1. workspace-write  :: allow normal workspace edits and commands",
            "2. ask              :: ask before write and execution tools run",
            "3. read-only        :: block write and execution tools",
            "4. allow-all        :: disable permission checks",
            "Press Enter to keep the default: %s" % current_mode,
        ],
    )
    choices = {
        "1": "workspace-write",
        "2": "ask",
        "3": "read-only",
        "4": "allow-all",
    }
    while True:
        try:
            selected = input("permission mode [1/2/3/4]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            renderer.print_notice("Keeping permission_mode=%s" % current_mode)
            return current_mode
        if not selected:
            renderer.print_notice("permission_mode=%s" % current_mode)
            return current_mode
        resolved = choices.get(selected, _resolve_permission_mode(selected))
        if resolved in {"workspace-write", "ask", "read-only", "allow-all"}:
            renderer.print_notice("permission_mode=%s" % resolved)
            return resolved
        renderer.print_notice("Unknown permission choice: %s" % selected, level="warn")


def _build_permission_request_handler(renderer: ConsoleRenderer):
    if not _is_interactive_terminal():
        return None

    def _request(payload: dict) -> str:
        tool = str(payload.get("tool", ""))
        reason = str(payload.get("reason", "permission required"))
        summary = str(payload.get("summary", tool))
        renderer.section(
            "Permission Request",
            [
                "tool: %s" % tool,
                "summary: %s" % summary,
                "reason: %s" % reason,
                "Choices: [o] allow once  [s] allow for this session  [n] deny",
            ],
        )
        while True:
            try:
                choice = input("permission [o/s/n]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                renderer.print_notice("Permission denied for %s." % tool, level="warn")
                return "deny"
            if choice in {"", "n", "no", "deny"}:
                renderer.print_notice("Permission denied for %s." % tool, level="warn")
                return "deny"
            if choice in {"o", "once", "y", "yes"}:
                renderer.print_notice("Permission granted once for %s." % tool)
                return "allow-once"
            if choice in {"s", "session"}:
                renderer.print_notice("Permission granted for this session: %s." % tool)
                return "allow-session"
            renderer.print_notice("Please enter o, s, or n.", level="warn")

    return _request


def _tool_names_from_invocations(tool_invocations: list[dict]) -> list[str]:
    names = []
    for item in tool_invocations:
        name = str(item.get("tool", ""))
        if name and name not in names:
            names.append(name)
    return names


def _truncate_cli_text(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    if limit <= 3:
        return text[:limit]
    return text[: limit - 3].rstrip() + "..."


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
