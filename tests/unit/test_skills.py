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
            self.assertTrue(any(item.slug == "plant-growth-model-selection" for item in skills))
            self.assertTrue(any(item.slug == "crop-growth-simulation-workflow" for item in skills))
            self.assertTrue(any(item.slug == "crop-water-and-irrigation-simulation" for item in skills))
            self.assertTrue(any(item.slug == "microbial-growth-and-community-simulation" for item in skills))
            self.assertTrue(any(item.slug == "root-and-rhizosphere-architecture-modeling" for item in skills))
            self.assertTrue(any(item.slug == "woody-plant-and-forest-simulation" for item in skills))
            self.assertTrue(any(item.slug == "microbial-community-metabolism-simulation" for item in skills))
            self.assertTrue(any(item.slug == "microbial-biofilm-and-reactor-simulation" for item in skills))
            self.assertTrue(any(item.slug == "microbiome-timeseries-and-benchmark-simulation" for item in skills))
            self.assertTrue(any(item.slug == "process-model-selection" for item in skills))
            self.assertTrue(any(item.slug == "agent-based-ecology-modeling" for item in skills))
            self.assertTrue(any(item.slug == "food-web-and-trophic-simulation" for item in skills))
            self.assertTrue(any(item.slug == "literature-review" for item in skills))
            self.assertTrue(any(item.slug == "paper-lookup" for item in skills))
            self.assertTrue(any(item.slug == "geopandas" for item in skills))
            self.assertTrue(any(item.slug == "statistical-analysis" for item in skills))
            self.assertTrue(any(item.slug == "scientific-visualization" for item in skills))
            self.assertTrue(any(item.slug == "biopython" for item in skills))
            self.assertTrue(any(item.slug == "scikit-bio" for item in skills))
            self.assertTrue(any(item.slug == "phylogenetics" for item in skills))
            self.assertTrue(any(item.slug == "open-notebook" for item in skills))
            self.assertTrue(any(item.slug == "systematic-debugging" for item in skills))
            self.assertTrue(any(item.slug == "test-driven-development" for item in skills))
            self.assertTrue(any(item.slug == "verification-before-completion" for item in skills))
            self.assertTrue(any(item.slug == "writing-plans" for item in skills))
            self.assertTrue(any(item.slug == "using-git-worktrees" for item in skills))
            self.assertTrue(any(item.slug == "humanizer" for item in skills))
            self.assertTrue(any(item.slug == "autoresearch" for item in skills))
            self.assertTrue(any(item.slug == "implementing-llms-litgpt" for item in skills))
            self.assertTrue(any(item.slug == "sentencepiece" for item in skills))
            self.assertTrue(any(item.slug == "peft-fine-tuning" for item in skills))
            self.assertTrue(any(item.slug == "evaluating-llms-harness" for item in skills))
            self.assertTrue(any(item.slug == "serving-llms-vllm" for item in skills))
            self.assertTrue(any(item.slug == "mlflow" for item in skills))
            self.assertTrue(any(item.slug == "whisper" for item in skills))
            self.assertTrue(any(item.slug == "academic-plotting" for item in skills))
            self.assertTrue(any(item.slug == "brainstorming-research-ideas" for item in skills))
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

    def test_vendored_scientific_bundle_skill_render_preserves_bundle_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            skill = app.skill_loader.get("literature-review")
            self.assertIsNotNone(skill)

            rendered = app.skill_loader.render(skill, "wetland methane")

            self.assertIn("Skill bundle root:", rendered)
            self.assertIn("scripts/search_databases.py", rendered)
            self.assertIn("references/database_strategies.md", rendered)

    def test_vendored_superpowers_bundle_skill_render_preserves_bundle_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            skill = app.skill_loader.get("using-superpowers")
            self.assertIsNotNone(skill)

            rendered = app.skill_loader.render(skill, "")

            self.assertIn("Skill bundle root:", rendered)
            self.assertIn("references/codex-tools.md", rendered)

    def test_vendored_humanizer_skill_is_loadable_as_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            skill = app.skill_loader.get("humanizer")
            self.assertIsNotNone(skill)
            self.assertIn("Remove signs of AI-generated writing", skill.description)
            self.assertEqual(skill.tools[:4], ["Read", "Write", "Edit", "Grep"])

            rendered = app.skill_loader.render(skill, "Make this sound less robotic.")

            self.assertIn("Skill bundle root:", rendered)
            self.assertIn("Remove AI Writing Patterns", rendered)

    def test_vendored_ai_research_skill_is_loadable_as_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            skill = app.skill_loader.get("autoresearch")
            self.assertIsNotNone(skill)
            self.assertIn("autonomous AI research projects", skill.description)

            rendered = app.skill_loader.render(skill, "")

            self.assertIn("Skill bundle root:", rendered)
            self.assertIn("research-state.yaml", rendered)


if __name__ == "__main__":
    unittest.main()
