import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from ecology_harness.app import EcologyHarnessApp
from ecology_harness.config import HarnessSettings


class PermissionTests(unittest.TestCase):
    def test_read_only_mode_blocks_write_tools(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            settings = HarnessSettings.from_workspace(Path(tmpdir))
            settings.user_state_dir = Path(tmpdir) / ".user_state"
            settings.permission_mode = "read-only"
            app = EcologyHarnessApp(settings)
            app.initialize()

            result = app.run_prompt('/tool Write {"path":"note.txt","content":"hello"}')

            self.assertIn("Permission denied", result.final_text)
            self.assertFalse((Path(tmpdir) / "note.txt").exists())

    def test_workspace_mode_blocks_dangerous_bash(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            settings = HarnessSettings.from_workspace(Path(tmpdir))
            settings.user_state_dir = Path(tmpdir) / ".user_state"
            settings.permission_mode = "workspace-write"
            app = EcologyHarnessApp(settings)
            app.initialize()

            result = app.run_prompt('/tool Bash {"command":"rm -rf /tmp/not-real"}')

            self.assertIn("Permission denied", result.final_text)

    def test_ask_mode_prompts_and_can_allow_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            settings.permission_mode = "ask"
            app = EcologyHarnessApp(settings)
            app.initialize()
            app.set_permission_request_handler(lambda payload: "allow-once")

            result = app.run_prompt('/tool Write {"path":"note.txt","content":"hello"}')

            self.assertIn("Tool execution complete", result.final_text)
            self.assertTrue((root / "note.txt").exists())

    def test_ask_mode_can_grant_tool_for_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            settings.permission_mode = "ask"
            app = EcologyHarnessApp(settings)
            app.initialize()
            handler = Mock(return_value="allow-session")
            app.set_permission_request_handler(handler)

            first = app.run_prompt('/tool Write {"path":"one.txt","content":"hello"}')
            second = app.run_prompt('/tool Write {"path":"two.txt","content":"world"}')

            self.assertIn("Tool execution complete", first.final_text)
            self.assertIn("Tool execution complete", second.final_text)
            self.assertEqual(handler.call_count, 1)
            self.assertTrue((root / "one.txt").exists())
            self.assertTrue((root / "two.txt").exists())

    def test_ask_mode_does_not_prompt_for_hard_blocked_bash(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            settings = HarnessSettings.from_workspace(Path(tmpdir))
            settings.user_state_dir = Path(tmpdir) / ".user_state"
            settings.permission_mode = "ask"
            app = EcologyHarnessApp(settings)
            app.initialize()
            handler = Mock(return_value="allow-once")
            app.set_permission_request_handler(handler)

            result = app.run_prompt('/tool Bash {"command":"rm -rf /tmp/not-real"}')

            self.assertIn("Permission denied", result.final_text)
            self.assertEqual(handler.call_count, 0)

    def test_new_session_clears_permission_session_grants(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            settings.permission_mode = "ask"
            app = EcologyHarnessApp(settings)
            app.initialize()
            handler = Mock(return_value="allow-session")
            app.set_permission_request_handler(handler)

            app.run_prompt('/tool Write {"path":"one.txt","content":"hello"}')
            app.start_new_session()
            app.run_prompt('/tool Write {"path":"two.txt","content":"world"}')

            self.assertEqual(handler.call_count, 2)


if __name__ == "__main__":
    unittest.main()
