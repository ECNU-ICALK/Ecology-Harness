import tempfile
import unittest
from pathlib import Path

from ecology_harness.config import HarnessSettings
from ecology_harness.tools import ToolDefinition, ToolError, ToolRegistry, ToolResult


class ToolRegistryTests(unittest.TestCase):
    def test_registry_registers_and_executes_tool(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ToolRegistry()
            settings = HarnessSettings.from_workspace(Path(tmpdir))
            settings.user_state_dir = Path(tmpdir) / ".user_state"
            settings.ensure_directories()

            registry.register(
                ToolDefinition(
                    name="Echo",
                    description="Echo a value.",
                    input_schema={
                        "type": "object",
                        "properties": {"value": {"type": "string"}},
                        "required": ["value"],
                    },
                    handler=lambda params, _: ToolResult(content=params["value"]),
                )
            )

            result = registry.execute("Echo", {"value": "hello"}, settings)

            self.assertEqual(result.content, "hello")

    def test_registry_validates_required_params(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ToolRegistry()
            settings = HarnessSettings.from_workspace(Path(tmpdir))
            settings.user_state_dir = Path(tmpdir) / ".user_state"
            settings.ensure_directories()

            registry.register(
                ToolDefinition(
                    name="Echo",
                    description="Echo a value.",
                    input_schema={
                        "type": "object",
                        "properties": {"value": {"type": "string"}},
                        "required": ["value"],
                    },
                    handler=lambda params, _: ToolResult(content=params["value"]),
                )
            )

            with self.assertRaises(ToolError):
                registry.execute("Echo", {}, settings)

    def test_registry_rejects_duplicate_tool_names(self) -> None:
        registry = ToolRegistry()
        tool = ToolDefinition(
            name="Echo",
            description="Echo a value.",
            input_schema={"type": "object", "properties": {}},
            handler=lambda _params, _ctx: ToolResult(content="ok"),
        )

        registry.register(tool)

        with self.assertRaises(ValueError) as exc:
            registry.register(tool)

        self.assertIn("already registered", str(exc.exception))


if __name__ == "__main__":
    unittest.main()
