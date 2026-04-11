import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ecology_harness.app import EcologyHarnessApp
from ecology_harness.config import HarnessSettings


class BuiltinToolTests(unittest.TestCase):
    def test_read_tool_returns_numbered_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "notes.txt").write_text("alpha\nbeta\ngamma\n", encoding="utf-8")

            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            result = app.registry.execute(
                "Read",
                {"path": "notes.txt", "start_line": 2},
                app.settings,
            )

            self.assertIn("2: beta", result.content)
            self.assertIn("3: gamma", result.content)

    def test_glob_tool_lists_matching_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "a.py").write_text("print('a')\n", encoding="utf-8")
            (root / "b.txt").write_text("hello\n", encoding="utf-8")

            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            result = app.registry.execute("Glob", {"pattern": "*.py"}, app.settings)

            self.assertEqual(result.data["matches"], ["a.py"])

    def test_grep_tool_finds_text_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "main.py").write_text("def calc():\n    return 42\n", encoding="utf-8")
            (root / "other.txt").write_text("no hit here\n", encoding="utf-8")

            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            result = app.registry.execute(
                "Grep",
                {"pattern": "return", "include": "*.py"},
                app.settings,
            )

            self.assertIn("main.py:2:     return 42", result.content)

    def test_write_and_edit_tools_modify_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            written = app.registry.execute(
                "Write",
                {"path": "draft.txt", "content": "alpha beta"},
                app.settings,
                services=app.get_services(),
            )
            self.assertIn("Wrote draft.txt", written.content)

            edited = app.registry.execute(
                "Edit",
                {"path": "draft.txt", "old_text": "beta", "new_text": "gamma"},
                app.settings,
                services=app.get_services(),
            )
            self.assertIn("Edited draft.txt", edited.content)
            self.assertEqual((root / "draft.txt").read_text(encoding="utf-8"), "alpha gamma")

    def test_bash_tool_runs_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            result = app.registry.execute(
                "Bash",
                {"command": "printf 'ok'"},
                app.settings,
                services=app.get_services(),
            )
            self.assertEqual(result.content, "ok")

    def test_bash_tool_prefers_current_runtime_python_environment(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            with patch("ecology_harness.tools.builtin.system_tools.subprocess.run") as run_mock:
                run_mock.return_value.stdout = "3.11.0\n"
                run_mock.return_value.stderr = ""
                run_mock.return_value.returncode = 0
                result = app.registry.execute(
                    "Bash",
                    {"command": "python3 --version"},
                    app.settings,
                    services=app.get_services(),
                )

            self.assertEqual(result.data["returncode"], 0)
            _, kwargs = run_mock.call_args
            env = kwargs["env"]
            runtime_python = env["ECOLOGY_HARNESS_RUNTIME_PYTHON"]
            runtime_bin = str(Path(runtime_python).parent)
            self.assertTrue(env["PATH"].split(":")[0] == runtime_bin)
            self.assertIn("python_executable", result.data)


if __name__ == "__main__":
    unittest.main()
