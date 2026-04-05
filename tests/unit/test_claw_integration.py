import json
import tempfile
import unittest
from pathlib import Path

from ecology_harness.app import EcologyHarnessApp
from ecology_harness.config import HarnessSettings


class ClawIntegrationTests(unittest.TestCase):
    def _make_app(self, root: Path) -> EcologyHarnessApp:
        settings = HarnessSettings.from_workspace(root)
        settings.user_state_dir = root / ".user_state"
        app = EcologyHarnessApp(settings)
        app.initialize()
        return app

    def test_plugins_are_loaded_from_builtin_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._make_app(Path(tmpdir))

            plugins = app.plugin_manager.list_plugins()
            plugin_slugs = {item.slug for item in plugins}

            self.assertIn("claw-compat", plugin_slugs)
            self.assertIn("example-bundled", plugin_slugs)

            result = app.registry.execute(
                "PluginList",
                {},
                app.settings,
                services=app.get_services(),
            )

            self.assertIn("claw-compat", result.content)
            self.assertTrue(any(item["enabled"] for item in result.data["plugins"] if item["slug"] == "claw-compat"))

    def test_mcp_bridge_lists_tools_and_reads_resources(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._make_app(Path(tmpdir))

            self.assertIsNotNone(app.registry.get("mcp__claw-reference__list_tools"))

            server_result = app.registry.execute(
                "ListMcpServersTool",
                {},
                app.settings,
                services=app.get_services(),
            )
            self.assertIn("claw-reference", server_result.content)

            tool_result = app.registry.execute(
                "MCPTool",
                {"server": "claw-reference", "tool": "list_tools"},
                app.settings,
                services=app.get_services(),
            )
            self.assertIn("BashTool", tool_result.content)

            resource_result = app.registry.execute(
                "ReadMcpResourceTool",
                {"server": "claw-reference", "uri": "claw://skills"},
                app.settings,
                services=app.get_services(),
            )
            payload = json.loads(resource_result.content)
            self.assertTrue(any(item["slug"] == "remember" for item in payload))

    def test_claw_compat_tools_work_against_native_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("line one\nline two\nline three\n", encoding="utf-8")
            (root / "docs").mkdir()
            (root / "docs" / "guide.md").write_text("guide\n", encoding="utf-8")
            app = self._make_app(root)

            read_result = app.registry.execute(
                "FileReadTool",
                {"path": "README.md", "offset": 1, "limit": 1},
                app.settings,
                services=app.get_services(),
            )
            self.assertIn("line two", read_result.content)

            list_result = app.registry.execute(
                "ListDirectoryTool",
                {"path": ".", "recursive": False},
                app.settings,
                services=app.get_services(),
            )
            self.assertIn("docs/", list_result.content)

            config_result = app.registry.execute(
                "ConfigTool",
                {"action": "set", "key": "runtime_mode", "value": "plan"},
                app.settings,
                services=app.get_services(),
            )
            self.assertIn("runtime_mode=plan", config_result.content)

            todo_result = app.registry.execute(
                "TodoWriteTool",
                {
                    "items": [
                        {"content": "Review claw integration", "status": "in_progress"},
                        {"content": "Verify MCP resources", "status": "pending"},
                    ]
                },
                app.settings,
                services=app.get_services(),
            )
            self.assertIn("Review claw integration", todo_result.content)
            self.assertEqual(len(todo_result.data["tasks"]), 2)


if __name__ == "__main__":
    unittest.main()
