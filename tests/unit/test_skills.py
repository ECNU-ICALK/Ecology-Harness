import tempfile
import unittest
from pathlib import Path

from ecology_harness.app import EcologyHarnessApp
from ecology_harness.config import HarnessSettings


class SkillTests(unittest.TestCase):
    def test_builtin_skills_are_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            skills = app.skill_loader.list_skills()
            self.assertTrue(any(item.slug == "plan" for item in skills))
            self.assertTrue(any(item.slug == "expand-references" for item in skills))
            self.assertTrue(any(item.slug == "mapbox-geospatial-operations" for item in skills))
            self.assertTrue(any(item.slug == "ecology-dataset-hunt" for item in skills))
            self.assertTrue(any(item.slug == "literature-multi-source-search" for item in skills))
            self.assertTrue(any(item.slug == "open-access-paper-harvest" for item in skills))
            self.assertTrue(any(item.slug == "open-meteo" for item in skills))
            self.assertTrue(any(item.slug == "species-occurrence-workbench" for item in skills))
            self.assertTrue(any(item.slug == "microbial-ecology-sequence-workflow" for item in skills))
            self.assertTrue(any(item.slug == "closed-algae-system-design" for item in skills))
            self.assertTrue(any(item.slug == "algal-timeseries-and-mass-balance" for item in skills))
            self.assertTrue(any(item.slug == "aquatic-microcosm-foodweb-design" for item in skills))
            self.assertTrue(any(item.slug == "plankton-microscopy-and-auto-classification" for item in skills))
            self.assertFalse(any(item.slug == "reference" for item in skills))
            self.assertFalse(any(item.slug == "performance-testing" for item in skills))

            result = app.registry.execute(
                "SkillRead",
                {"name": "review"},
                app.settings,
                services=app.get_services(),
            )
            self.assertIn("correctness bugs", result.content)

    def test_skill_tool_executes_inline_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            custom_skill = app.settings.skill_dir / "create-task.md"
            custom_skill.write_text(
                "---\n"
                "name: create-task\n"
                "description: Create a task from the provided argument.\n"
                "slug: create-task\n"
                "arguments: [subject]\n"
                "context: inline\n"
                "---\n"
                "/tool TaskCreate {\"subject\":\"$SUBJECT\"}\n",
                encoding="utf-8",
            )

            result = app.registry.execute(
                "Skill",
                {"name": "create-task", "args": "FromSkill"},
                app.settings,
                services=app.get_services(),
            )

            self.assertIn("Created task #1", result.content)

    def test_run_prompt_auto_triggers_builtin_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            result = app.run_prompt("/explain README")

            self.assertTrue(result.final_text)

    def test_bundle_skill_render_includes_bundle_root_hint(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            skill = app.skill_loader.get("expand-references")
            self.assertIsNotNone(skill)

            rendered = app.skill_loader.render(skill, "Attention Is All You Need")

            self.assertIn("Skill bundle root:", rendered)
            self.assertIn("scripts/run.py", rendered)


if __name__ == "__main__":
    unittest.main()
