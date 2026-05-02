import io
import argparse
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from typing import Optional
from unittest.mock import patch

from ecology_harness.cli import _should_prompt_for_permission_choice, main


class _FakeFeishuResponse:
    status = 200

    def read(self) -> bytes:
        return b'{"StatusCode":0,"StatusMessage":"success"}'

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        del exc_type, exc, tb
        return False


class _FakeWebhookResponse:
    status = 200

    def __init__(self, payload: Optional[bytes] = None) -> None:
        self._payload = payload or b'{"errcode":0,"errmsg":"ok"}'

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        del exc_type, exc, tb
        return False


class CliTests(unittest.TestCase):
    def test_cli_lists_tools(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--workspace",
                        tmpdir,
                        "--list-tools",
                        "--api-key-env",
                        "UNUSED_KEY",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("Read", buffer.getvalue())

    def test_cli_executes_tool(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("hello\n", encoding="utf-8")

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--workspace",
                        tmpdir,
                        "--exec-tool",
                        "Read",
                        "--params",
                        '{"path":"README.md"}',
                        "--api-key-env",
                        "UNUSED_KEY",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("hello", buffer.getvalue())

    def test_cli_lists_providers(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--workspace",
                        tmpdir,
                        "--list-providers",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("anthropic", buffer.getvalue())
            self.assertIn("ollama", buffer.getvalue())

    def test_cli_runs_prompt_with_mock_provider(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("hello prompt\n", encoding="utf-8")

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--workspace",
                        tmpdir,
                        "--prompt",
                        '/tool Read {"path":"README.md"}',
                        "--api-key-env",
                        "UNUSED_KEY",
                    ]
                )

            self.assertEqual(exit_code, 0)
            output = buffer.getvalue()
            self.assertIn("Ecology Harness", output)
            self.assertIn("⏵ Read README.md", output)
            self.assertIn("⏺ Tool execution complete.", output)
            self.assertIn("hello prompt", output)

    def test_cli_doctor_reports_workspace_health(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--workspace",
                        tmpdir,
                        "doctor",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("Doctor", buffer.getvalue())
            self.assertIn("workspace:", buffer.getvalue())

    def test_cli_doctor_accepts_probe_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--workspace",
                        tmpdir,
                        "doctor",
                        "--probe",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("Doctor", buffer.getvalue())

    def test_cli_runtime_reports_live_runtime_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--workspace",
                        tmpdir,
                        "runtime",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("Runtime", buffer.getvalue())
            self.assertIn("context:", buffer.getvalue())

    def test_cli_analytics_reports_recent_usage_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("analytics cli\n", encoding="utf-8")

            with redirect_stdout(io.StringIO()):
                main(
                    [
                        "--workspace",
                        tmpdir,
                        '--prompt',
                        '/tool Read {"path":"README.md"}',
                    ]
                )

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--workspace",
                        tmpdir,
                        "analytics",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("Analytics", buffer.getvalue())
            self.assertIn("recent_queries", buffer.getvalue())

    def test_cli_setup_creates_bootstrap_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--workspace",
                        tmpdir,
                        "setup",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertTrue((root / "AGENTS.md").exists())
            self.assertTrue((root / "STANDING_ORDERS.md").exists())
            self.assertIn("created:", buffer.getvalue())

    def test_cli_setup_accepts_force_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "AGENTS.md").write_text("old\n", encoding="utf-8")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--workspace",
                        tmpdir,
                        "setup",
                        "--force",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("updated:", buffer.getvalue())

    def test_cli_lists_integrations(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--workspace",
                        tmpdir,
                        "integrations",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("Integrations", buffer.getvalue())

    def test_cli_can_add_feishu_integration(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--workspace",
                        tmpdir,
                        "integrations",
                        "add",
                        "feishu-webhook",
                        "--name",
                        "default",
                        "--webhook-url",
                        "https://open.feishu.cn/open-apis/bot/v2/hook/abc12345",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("Integration Added", buffer.getvalue())

    def test_cli_can_test_feishu_integration(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with redirect_stdout(io.StringIO()):
                main(
                    [
                        "--workspace",
                        tmpdir,
                        "integrations",
                        "add",
                        "feishu-webhook",
                        "--name",
                        "default",
                        "--webhook-url",
                        "https://open.feishu.cn/open-apis/bot/v2/hook/abc12345",
                    ]
                )

            buffer = io.StringIO()
            with patch("ecology_harness.integrations.manager.urllib_request.urlopen", return_value=_FakeFeishuResponse()):
                with redirect_stdout(buffer):
                    exit_code = main(
                        [
                            "--workspace",
                            tmpdir,
                            "integrations",
                            "test",
                            "default",
                            "hello",
                            "team",
                        ]
                    )

            self.assertEqual(exit_code, 0)
            self.assertIn("Integration Test", buffer.getvalue())

    def test_cli_can_add_dingtalk_integration(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--workspace",
                        tmpdir,
                        "integrations",
                        "add",
                        "dingtalk-webhook",
                        "--name",
                        "ops",
                        "--webhook-url",
                        "https://oapi.dingtalk.com/robot/send?access_token=abc12345",
                        "--secret",
                        "ding-secret",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("Integration Added", buffer.getvalue())

    def test_cli_can_add_wecom_integration(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--workspace",
                        tmpdir,
                        "integrations",
                        "add",
                        "wecom-webhook",
                        "--name",
                        "team",
                        "--webhook-url",
                        "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=abc12345",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("Integration Added", buffer.getvalue())

    def test_cli_can_test_dingtalk_integration(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with redirect_stdout(io.StringIO()):
                main(
                    [
                        "--workspace",
                        tmpdir,
                        "integrations",
                        "add",
                        "dingtalk-webhook",
                        "--name",
                        "ops",
                        "--webhook-url",
                        "https://oapi.dingtalk.com/robot/send?access_token=abc12345",
                        "--secret",
                        "ding-secret",
                    ]
                )

            buffer = io.StringIO()
            with patch("ecology_harness.integrations.manager.urllib_request.urlopen", return_value=_FakeWebhookResponse()):
                with redirect_stdout(buffer):
                    exit_code = main(
                        [
                            "--workspace",
                            tmpdir,
                            "integrations",
                            "test",
                            "ops",
                            "hello",
                            "ops",
                        ]
                    )

            self.assertEqual(exit_code, 0)
            self.assertIn("Integration Test", buffer.getvalue())

    def test_cli_explore_runs_in_read_only_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--workspace",
                        tmpdir,
                        "explore",
                        '/tool Write {"path":"note.txt","content":"hello"}',
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("Permission denied", buffer.getvalue())
            self.assertFalse((root / "note.txt").exists())

    def test_cli_short_prompt_flag_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("hello short flag\n", encoding="utf-8")

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--workspace",
                        tmpdir,
                        "-p",
                        '/tool Read {"path":"README.md"}',
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("hello short flag", buffer.getvalue())

    def test_cli_only_prompts_for_permission_choice_when_entering_interactive_repl(self) -> None:
        args = argparse.Namespace(
            prompt="",
            list_tools=False,
            list_providers=False,
            describe_tool="",
            exec_tool="",
            command_args=[],
        )
        with patch("sys.stdin.isatty", return_value=True), patch("sys.stdout.isatty", return_value=True):
            self.assertTrue(_should_prompt_for_permission_choice([], args))
            self.assertFalse(_should_prompt_for_permission_choice(["--permission-mode", "ask"], args))
        args.command_args = ["doctor"]
        with patch("sys.stdin.isatty", return_value=True), patch("sys.stdout.isatty", return_value=True):
            self.assertFalse(_should_prompt_for_permission_choice([], args))

    def test_cli_supports_positional_prompt_shorthand(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("hello positional prompt\n", encoding="utf-8")

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--workspace",
                        tmpdir,
                        '/tool Read {"path":"README.md"}',
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("hello positional prompt", buffer.getvalue())

    def test_cli_supports_prompt_subcommand(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("hello prompt subcommand\n", encoding="utf-8")

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--workspace",
                        tmpdir,
                        "prompt",
                        '/tool Read {"path":"README.md"}',
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("hello prompt subcommand", buffer.getvalue())

    def test_cli_lists_saved_sessions(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("hello sessions\n", encoding="utf-8")

            with redirect_stdout(io.StringIO()):
                main(
                    [
                        "--workspace",
                        tmpdir,
                        "--prompt",
                        '/tool Read {"path":"README.md"}',
                    ]
                )

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--workspace",
                        tmpdir,
                        "sessions",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("Sessions", buffer.getvalue())
            self.assertIn("msgs", buffer.getvalue().lower())

    def test_cli_searches_saved_sessions(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("wetland methane session\n", encoding="utf-8")

            with redirect_stdout(io.StringIO()):
                main(
                    [
                        "--workspace",
                        tmpdir,
                        "--prompt",
                        '/tool Read {"path":"README.md"}',
                    ]
                )

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--workspace",
                        tmpdir,
                        "sessions",
                        "search",
                        "wetland methane",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("Session Search", buffer.getvalue())
            self.assertIn("README.md", buffer.getvalue())

    def test_cli_resume_without_id_uses_interactive_selector(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("resume selector\n", encoding="utf-8")

            with redirect_stdout(io.StringIO()):
                main(
                    [
                        "--workspace",
                        tmpdir,
                        "--prompt",
                        '/tool Read {"path":"README.md"}',
                    ]
                )

            with patch("ecology_harness.cli.select_list_option", return_value="latest"), patch(
                "ecology_harness.cli.run_repl",
                return_value=0,
            ) as run_repl_mock:
                exit_code = main(
                    [
                        "--workspace",
                        tmpdir,
                        "resume",
                    ]
                )

            self.assertEqual(exit_code, 0)
            run_repl_mock.assert_called_once()

    def test_cli_accepts_provider_timeout_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("hello provider timeout\n", encoding="utf-8")

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--workspace",
                        tmpdir,
                        "--provider-timeout",
                        "240",
                        "-p",
                        '/tool Read {"path":"README.md"}',
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("hello provider timeout", buffer.getvalue())

    def test_cli_accepts_provider_router_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--workspace",
                        tmpdir,
                        "--provider-fallback",
                        "openai",
                        "--provider-fallback",
                        "gemini",
                        "--provider-retry-attempts",
                        "3",
                        "--provider-retry-backoff-ms",
                        "250",
                        "--provider-pool-strategy",
                        "round-robin",
                        "config",
                    ]
                )

            self.assertEqual(exit_code, 0)
            output = buffer.getvalue()
            self.assertIn("provider_fallbacks: openai, gemini", output)
            self.assertIn("provider_retry_attempts: 3", output)
            self.assertIn("provider_retry_backoff_ms: 250", output)
            self.assertIn("provider_pool_strategy: round-robin", output)

    def test_cli_max_steps_defaults_to_unlimited(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--workspace",
                        tmpdir,
                        "config",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("max_agent_loops: unlimited", buffer.getvalue())

    def test_cli_prompt_json_suppresses_trace_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("hello json\n", encoding="utf-8")

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--workspace",
                        tmpdir,
                        "--prompt",
                        '/tool Read {"path":"README.md"}',
                        "--json",
                    ]
                )

            self.assertEqual(exit_code, 0)
            output = buffer.getvalue()
            self.assertNotIn("⏵ Read README.md", output)
            self.assertIn('"events"', output)
            self.assertIn('"final_text"', output)

    def test_cli_lists_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--workspace",
                        tmpdir,
                        "--list-skills",
                        "--api-key-env",
                        "UNUSED_KEY",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("plan", buffer.getvalue())

    def test_cli_skill_hub_lists_installed_packs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--workspace",
                        tmpdir,
                        "skill-hub",
                        "literature review",
                    ]
                )

            self.assertEqual(exit_code, 0)
            output = buffer.getvalue()
            self.assertIn("Skill Hub Packs", output)
            self.assertIn("scientific", output)

    def test_cli_skill_view_reads_bundle_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--workspace",
                        tmpdir,
                        "skill-view",
                        "literature-review",
                        "scripts/search_databases.py",
                    ]
                )

            self.assertEqual(exit_code, 0)
            output = buffer.getvalue()
            self.assertIn("Skill View", output)
            self.assertIn("scripts/search_databases.py", output)

    def test_cli_capability_preflights_relevant_ecology_tools(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--workspace",
                        tmpdir,
                        "capability",
                        "玉米干旱加灌溉处理的成长模拟",
                    ]
                )

            self.assertEqual(exit_code, 0)
            output = buffer.getvalue()
            self.assertIn("Capability Readiness", output)
            self.assertIn("crop-water-and-irrigation-simulation", output)

    def test_cli_capability_supports_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--workspace",
                        tmpdir,
                        "--json",
                        "capability",
                        "microbial community metabolism simulation",
                    ]
                )

            self.assertEqual(exit_code, 0)
            payload = json.loads(buffer.getvalue())
            self.assertIn("skills", payload)
            self.assertIn("summary", payload)

    def test_cli_lists_plugins(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--workspace",
                        tmpdir,
                        "--list-plugins",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("claw-compat", buffer.getvalue())

    def test_cli_lists_mcp_servers(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--workspace",
                        tmpdir,
                        "--list-mcp-servers",
                    ]
                )

            self.assertEqual(exit_code, 0)
            output = buffer.getvalue()
            self.assertIn("claw-reference", output)
            self.assertIn("mapbox", output)
            self.assertIn("gis-mcp", output)
            self.assertIn("gbif", output)
            self.assertIn("stac", output)
            self.assertIn("scientific-papers", output)
            self.assertIn("openalex-research", output)
            self.assertIn("unpaywall", output)
            self.assertIn("dataverse", output)
            self.assertIn("pubchem", output)
            self.assertIn("cataloged", output)

    def test_cli_heartbeat_reports_workspace_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "HEARTBEAT.md").write_text("Check monitoring backlog.\n", encoding="utf-8")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--workspace",
                        tmpdir,
                        "heartbeat",
                    ]
                )

            self.assertEqual(exit_code, 0)
            output = buffer.getvalue()
            self.assertIn("Heartbeat", output)
            self.assertIn("enabled: True", output)

    def test_repl_supports_status_and_reset_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                with patch("builtins.input", side_effect=["/status", "/reset", "/quit"]):
                    exit_code = main(
                        [
                            "--workspace",
                            tmpdir,
                            "--repl",
                        ]
                    )

            self.assertEqual(exit_code, 0)
            output = buffer.getvalue()
            self.assertIn("Ecology Harness", output)
            self.assertIn("Conversation context cleared.", output)
            self.assertIn("conversation_messages: 0", output)
            self.assertIn("session_tool_calls: 0", output)

    def test_repl_supports_model_and_session_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                with patch("builtins.input", side_effect=["/model sonnet", "/session", "/quit"]):
                    exit_code = main(
                        [
                            "--workspace",
                            tmpdir,
                            "--repl",
                        ]
                    )

            self.assertEqual(exit_code, 0)
            output = buffer.getvalue()
            self.assertIn("active_model: claude-sonnet-4-6", output)
            self.assertIn("resume_hint: eh --resume latest", output)

    def test_cli_resume_latest_session_for_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("resume me\n", encoding="utf-8")

            first_buffer = io.StringIO()
            with redirect_stdout(first_buffer):
                first_exit = main(
                    [
                        "--workspace",
                        tmpdir,
                        "--prompt",
                        '/tool Read {"path":"README.md"}',
                    ]
                )
            self.assertEqual(first_exit, 0)

            second_buffer = io.StringIO()
            with redirect_stdout(second_buffer):
                second_exit = main(
                    [
                        "--workspace",
                        tmpdir,
                        "--resume",
                        "latest",
                        "session",
                    ]
                )

            self.assertEqual(second_exit, 0)
            self.assertIn("latest_session_exists: yes", second_buffer.getvalue())

    def test_repl_supports_backslash_command_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                with patch("builtins.input", side_effect=["\\", "\\quit"]):
                    exit_code = main(
                        [
                            "--workspace",
                            tmpdir,
                            "--repl",
                        ]
                    )

            self.assertEqual(exit_code, 0)
            output = buffer.getvalue()
            self.assertIn("Quick tip: enter / or \\", output)
            self.assertIn("Aliases: use \\help, \\status, \\reset, \\quit", output)

    def test_repl_suggests_unknown_backslash_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                with patch("builtins.input", side_effect=["\\statu", "\\quit"]):
                    exit_code = main(
                        [
                            "--workspace",
                            tmpdir,
                            "--repl",
                        ]
                    )

            self.assertEqual(exit_code, 0)
            output = buffer.getvalue()
            self.assertIn("Unknown session command: \\statu", output)
            self.assertIn("Did you mean /status?", output)

    def test_repl_does_not_reprint_submitted_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                with patch("builtins.input", side_effect=["hello leaf", "/quit"]):
                    exit_code = main(
                        [
                            "--workspace",
                            tmpdir,
                            "--repl",
                        ]
                    )

            self.assertEqual(exit_code, 0)
            output = buffer.getvalue()
            self.assertNotIn("> hello leaf", output)
            self.assertEqual(output.count("hello leaf"), 0)


if __name__ == "__main__":
    unittest.main()
