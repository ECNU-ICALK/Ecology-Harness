import tempfile
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
