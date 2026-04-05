import tempfile
import unittest
from pathlib import Path

from ecology_harness.app import EcologyHarnessApp
from ecology_harness.config import HarnessSettings


class MemoryTests(unittest.TestCase):
    def test_memory_tools_cover_save_read_search_delete(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()
            services = app.get_services()

            saved = app.registry.execute(
                "MemorySave",
                {
                    "name": "Project Goal",
                    "description": "Current goal",
                    "content": "Build a reusable ecology harness.",
                },
                app.settings,
                services=services,
            )
            self.assertIn("Saved memory", saved.content)

            listed = app.registry.execute("MemoryList", {}, app.settings, services=services)
            self.assertIn("project-goal.md", listed.content)

            read = app.registry.execute(
                "MemoryRead",
                {"name": "project-goal"},
                app.settings,
                services=services,
            )
            self.assertIn("reusable ecology harness", read.content)

            searched = app.registry.execute(
                "MemorySearch",
                {"query": "ecology"},
                app.settings,
                services=services,
            )
            self.assertIn("Project Goal", searched.content)

            deleted = app.registry.execute(
                "MemoryDelete",
                {"name": "project-goal"},
                app.settings,
                services=services,
            )
            self.assertIn("Deleted memory", deleted.content)

    def test_memory_context_combines_user_and_project_scopes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            app.memory_manager.save(
                name="User Preference",
                description="How the user prefers outputs",
                content="Prefer concise summaries.",
                memory_type="user",
                scope="user",
            )
            app.memory_manager.save(
                name="Project Context",
                description="Current project focus",
                content="Build a nano-inspired harness core.",
                memory_type="project",
                scope="project",
            )

            memory_context = app.memory_manager.get_memory_context(include_guidance=True)

            self.assertIn("Memory system", memory_context)
            self.assertIn("User Preference", memory_context)
            self.assertIn("Project Context", memory_context)

    def test_memory_context_prioritizes_relevant_items_for_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            app.memory_manager.save(
                name="Remote Sensing Workflow",
                description="Preferred satellite processing notes",
                content="Use Landsat and Sentinel imagery for remote sensing comparisons.",
                memory_type="reference",
                scope="project",
            )
            app.memory_manager.save(
                name="Writing Preference",
                description="How to format general output",
                content="Keep answers concise and structured.",
                memory_type="user",
                scope="user",
            )

            memory_context = app.memory_manager.get_memory_context(
                query="remote sensing imagery",
                include_guidance=True,
            )

            self.assertIn("Relevant memories", memory_context)
            self.assertIn("Remote Sensing Workflow", memory_context)
            self.assertIn("Landsat", memory_context)


if __name__ == "__main__":
    unittest.main()
