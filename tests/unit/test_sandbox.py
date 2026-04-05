import tempfile
import unittest
from pathlib import Path

from ecology_harness.app import EcologyHarnessApp
from ecology_harness.config import HarnessSettings
from ecology_harness.tools import ToolError


class SandboxTests(unittest.TestCase):
    def test_sandbox_status_reports_internal_backend(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            result = app.registry.execute(
                "SandboxStatus",
                {},
                app.settings,
                services=app.get_services(),
            )

            self.assertEqual(result.data["backend"], "internal")
            self.assertTrue(result.data["active"])

    def test_sandbox_blocks_reads_outside_allowed_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            outside = Path(tmpdir).parent / "outside.txt"
            outside.write_text("secret\n", encoding="utf-8")
            try:
                with self.assertRaises(ToolError):
                    app.registry.execute(
                        "Read",
                        {"path": str(outside)},
                        app.settings,
                        services=app.get_services(),
                    )
            finally:
                outside.unlink(missing_ok=True)

    def test_network_disabled_blocks_webfetch(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            settings.sandbox_allow_network = False
            app = EcologyHarnessApp(settings)
            app.initialize()

            with self.assertRaises(ToolError):
                app.registry.execute(
                    "WebFetch",
                    {"url": "https://example.com"},
                    app.settings,
                    services=app.get_services(),
                )


if __name__ == "__main__":
    unittest.main()
