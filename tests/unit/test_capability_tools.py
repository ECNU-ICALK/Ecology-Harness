from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest

from ecology_harness.app import EcologyHarnessApp
from ecology_harness.config import HarnessSettings
from ecology_harness.tools import ToolError


class CapabilityToolTests(unittest.TestCase):
    def _make_app(self, root: Path) -> EcologyHarnessApp:
        settings = HarnessSettings.from_workspace(root)
        settings.user_state_dir = root / ".user_state"
        app = EcologyHarnessApp(settings)
        app.initialize()
        return app

    def test_capability_readiness_report_ranks_ecology_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._make_app(Path(tmpdir))

            result = app.registry.execute(
                "CapabilityReadinessReport",
                {
                    "query": "玉米干旱加灌溉处理的成长模拟",
                    "skill_limit": 4,
                    "mcp_limit": 3,
                    "tool_limit": 4,
                },
                app.settings,
                services=app.get_services(),
            )

            skill_slugs = [item["slug"] for item in result.data["skills"]]
            self.assertIn("crop-water-and-irrigation-simulation", skill_slugs)
            self.assertGreaterEqual(result.data["summary"]["ready_skill_count"], 1)
            self.assertIn("Capability readiness for:", result.content)
            self.assertIn("Recommendations:", result.content)
            self.assertIn("mcp_servers", result.data)

    def test_capability_readiness_report_surfaces_setup_needed_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._make_app(Path(tmpdir))
            previous = os.environ.pop("ECOLOGY_HARNESS_CAPABILITY_TOKEN", None)
            try:
                custom_skill = app.settings.skill_dir / "needs-env.md"
                custom_skill.write_text(
                    "---\n"
                    "name: needs-env\n"
                    "description: Token setup workflow for capability readiness checks.\n"
                    "slug: needs-env\n"
                    "triggers: [needs env token, capability readiness token]\n"
                    "requirements: [env:ECOLOGY_HARNESS_CAPABILITY_TOKEN]\n"
                    "setup-required: true\n"
                    "context: inline\n"
                    "---\n"
                    "Use after setup is complete.\n",
                    encoding="utf-8",
                )

                result = app.registry.execute(
                    "CapabilityReadinessReport",
                    {
                        "query": "needs env token capability readiness",
                        "skill_limit": 3,
                        "mcp_limit": 1,
                        "tool_limit": 1,
                    },
                    app.settings,
                    services=app.get_services(),
                )

                setup_skills = [
                    item for item in result.data["skills"]
                    if item["slug"] == "needs-env"
                ]
                self.assertEqual(setup_skills[0]["readiness"], "setup-needed")
                self.assertIn(
                    "env:ECOLOGY_HARNESS_CAPABILITY_TOKEN",
                    setup_skills[0]["missing_requirements"],
                )
                self.assertGreaterEqual(result.data["summary"]["setup_needed_skill_count"], 1)
                self.assertTrue(
                    any("ECOLOGY_HARNESS_CAPABILITY_TOKEN" in item for item in result.data["recommendations"])
                )
            finally:
                if previous is None:
                    os.environ.pop("ECOLOGY_HARNESS_CAPABILITY_TOKEN", None)
                else:
                    os.environ["ECOLOGY_HARNESS_CAPABILITY_TOKEN"] = previous

    def test_capability_readiness_report_rejects_empty_query(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._make_app(Path(tmpdir))

            with self.assertRaises(ToolError):
                app.registry.execute(
                    "CapabilityReadinessReport",
                    {"query": "   "},
                    app.settings,
                    services=app.get_services(),
                )


if __name__ == "__main__":
    unittest.main()
