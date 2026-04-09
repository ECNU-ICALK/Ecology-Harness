import json
import tempfile
import unittest
from pathlib import Path

from ecology_harness.app import EcologyHarnessApp
from ecology_harness.config import HarnessSettings
from ecology_harness.runtime.messages import ChatMessage


class McpRetrievalTests(unittest.TestCase):
    def _make_app(self, root: Path) -> EcologyHarnessApp:
        settings = HarnessSettings.from_workspace(root)
        settings.user_state_dir = root / ".user_state"
        app = EcologyHarnessApp(settings)
        app.initialize()
        return app

    def _write_server(self, root: Path, payload: dict) -> None:
        mcp_dir = root / ".ecology_harness" / "mcp"
        mcp_dir.mkdir(parents=True, exist_ok=True)
        (mcp_dir / ("%s.json" % payload["name"])).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def test_mcp_search_rewrites_chinese_query_and_ranks_server(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_server(
                root,
                {
                    "name": "alpha-maps",
                    "transport": "inprocess",
                    "description": "Remote sensing and geospatial imagery server for satellite tiles, raster queries, and map analysis.",
                    "default_enabled": True,
                    "tools": [
                        {
                            "name": "search_tiles",
                            "description": "Search remote sensing imagery tiles and raster products.",
                            "handler": "list_claw_tools",
                        }
                    ],
                },
            )
            self._write_server(
                root,
                {
                    "name": "beta-literature",
                    "transport": "inprocess",
                    "description": "Literature search server for papers, citations, and article metadata.",
                    "default_enabled": True,
                    "tools": [
                        {
                            "name": "search_papers",
                            "description": "Search papers and references.",
                            "handler": "list_claw_tools",
                        }
                    ],
                },
            )
            app = self._make_app(root)

            report = app.mcp_registry.search("遥感 地理空间 影像", limit=2)

            self.assertEqual(report.hits[0].server.name, "alpha-maps")
            self.assertIn("remote sensing", report.rewrite.rewritten_query)
            self.assertIn("geospatial", report.rewrite.rewritten_query)

    def test_mcp_search_uses_conversation_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_server(
                root,
                {
                    "name": "benthic-monitor",
                    "transport": "inprocess",
                    "description": "Microscopy, fluorescence, and biofilm monitoring server for benthic algae and periphyton systems.",
                    "default_enabled": True,
                    "tools": [
                        {
                            "name": "analyze_biofilm",
                            "description": "Analyze biofilm thickness and benthic fluorescence signals.",
                            "handler": "list_claw_tools",
                        }
                    ],
                },
            )
            app = self._make_app(root)

            report = app.mcp_registry.search(
                "这个系统怎么监测",
                conversation=[
                    ChatMessage(
                        role="user",
                        content="我们现在在做底栖藻类、生物膜厚度和荧光信号的水体微宇宙实验。",
                    )
                ],
                limit=2,
            )

            self.assertEqual(report.hits[0].server.name, "benthic-monitor")
            self.assertTrue(report.rewrite.context_snippets)
            self.assertIn("biofilm", report.rewrite.rewritten_query)

    def test_build_system_prompt_injects_retrieved_mcp_servers(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            settings.mcp_prompt_top_k = 1
            self._write_server(
                root,
                {
                    "name": "alpha-maps",
                    "transport": "inprocess",
                    "description": "Remote sensing and geospatial imagery server for satellite tiles.",
                    "default_enabled": True,
                    "tools": [
                        {
                            "name": "search_tiles",
                            "description": "Search imagery tiles.",
                            "handler": "list_claw_tools",
                        }
                    ],
                },
            )
            app = EcologyHarnessApp(settings)
            app.initialize()

            prompt = app.build_system_prompt(prompt_text="遥感 地理空间 影像")

            self.assertIn("Relevant MCP servers for this request", prompt)
            self.assertIn("MCP retrieval query:", prompt)
            self.assertIn("alpha-maps", prompt)

    def test_select_available_tools_filters_dynamic_mcp_tools(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_server(
                root,
                {
                    "name": "alpha-maps",
                    "transport": "inprocess",
                    "description": "Remote sensing and geospatial imagery server for satellite analysis.",
                    "default_enabled": True,
                    "tools": [
                        {
                            "name": "search_tiles",
                            "description": "Search imagery tiles.",
                            "handler": "list_claw_tools",
                        }
                    ],
                },
            )
            self._write_server(
                root,
                {
                    "name": "beta-literature",
                    "transport": "inprocess",
                    "description": "Papers and citations server for literature review.",
                    "default_enabled": True,
                    "tools": [
                        {
                            "name": "search_papers",
                            "description": "Search papers and metadata.",
                            "handler": "list_claw_tools",
                        }
                    ],
                },
            )
            app = self._make_app(root)

            tools = app.select_available_tools("遥感 地理空间 影像")
            names = {item.name for item in tools}

            self.assertIn("MCPTool", names)
            self.assertIn("mcp__alpha-maps__search_tiles", names)
            self.assertNotIn("mcp__beta-literature__search_papers", names)

    def test_mcp_search_tool_returns_ranked_servers(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_server(
                root,
                {
                    "name": "alpha-maps",
                    "transport": "inprocess",
                    "description": "Remote sensing and geospatial imagery server for satellite analysis.",
                    "default_enabled": True,
                    "tools": [
                        {
                            "name": "search_tiles",
                            "description": "Search imagery tiles.",
                            "handler": "list_claw_tools",
                        }
                    ],
                },
            )
            app = self._make_app(root)

            result = app.registry.execute(
                "McpSearchTool",
                {"query": "遥感 地理空间 影像", "limit": 3},
                app.settings,
                services=app.get_services(),
            )

            self.assertIn("Rewritten query:", result.content)
            self.assertIn("alpha-maps", result.content)
            self.assertTrue(result.data["hits"])


if __name__ == "__main__":
    unittest.main()
