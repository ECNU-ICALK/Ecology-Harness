import tempfile
import unittest
from pathlib import Path

from ecology_harness.app import EcologyHarnessApp
from ecology_harness.config import HarnessSettings


class TaskTests(unittest.TestCase):
    def test_task_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()
            services = app.get_services()

            created = app.registry.execute(
                "TaskCreate",
                {"title": "Bootstrap harness", "description": "Create the generic runtime"},
                app.settings,
                services=services,
            )
            self.assertEqual(created.data["id"], "1")

            listed = app.registry.execute("TaskList", {}, app.settings, services=services)
            self.assertIn("Bootstrap harness", listed.content)

            fetched = app.registry.execute(
                "TaskGet",
                {"id": "1"},
                app.settings,
                services=services,
            )
            self.assertIn("Create the generic runtime", fetched.content)

            updated = app.registry.execute(
                "TaskUpdate",
                {"id": "1", "status": "completed"},
                app.settings,
                services=services,
            )
            self.assertEqual(updated.data["status"], "completed")


if __name__ == "__main__":
    unittest.main()
