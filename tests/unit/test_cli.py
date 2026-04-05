import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from ecology_harness.cli import main


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
            self.assertIn("scientific-papers", output)
            self.assertIn("unpaywall", output)
            self.assertIn("dataverse", output)
            self.assertIn("cataloged", output)

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


if __name__ == "__main__":
    unittest.main()
