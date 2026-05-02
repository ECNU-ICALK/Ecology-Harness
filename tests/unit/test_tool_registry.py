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

    def test_registry_validates_nested_array_and_object_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ToolRegistry()
            settings = HarnessSettings.from_workspace(Path(tmpdir))
            settings.user_state_dir = Path(tmpdir) / ".user_state"
            settings.ensure_directories()

            registry.register(
                ToolDefinition(
                    name="Nested",
                    description="Validate nested inputs.",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "items": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "count": {"type": "integer"},
                                    },
                                    "required": ["name", "count"],
                                },
                            },
                            "mode": {"type": "string", "enum": ["fast", "safe"]},
                        },
                        "required": ["items", "mode"],
                    },
                    handler=lambda _params, _ctx: ToolResult(content="ok"),
                )
            )

            result = registry.execute(
                "Nested",
                {"items": [{"name": "a", "count": 1}], "mode": "safe"},
                settings,
            )
            self.assertEqual(result.content, "ok")

            with self.assertRaises(ToolError) as type_error:
                registry.execute(
                    "Nested",
                    {"items": [{"name": "a", "count": "1"}], "mode": "safe"},
                    settings,
                )
            self.assertIn("parameters.items[0].count", str(type_error.exception))

            with self.assertRaises(ToolError) as enum_error:
                registry.execute(
                    "Nested",
                    {"items": [{"name": "a", "count": 1}], "mode": "unsafe"},
                    settings,
                )
            self.assertIn("must be one of", str(enum_error.exception))

    def test_registry_allows_unknown_parameters_unless_schema_disallows_them(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ToolRegistry()
            settings = HarnessSettings.from_workspace(Path(tmpdir))
            settings.user_state_dir = Path(tmpdir) / ".user_state"
            settings.ensure_directories()

            registry.register(
                ToolDefinition(
                    name="Loose",
                    description="Allow unknown fields by default.",
                    input_schema={"type": "object", "properties": {"value": {"type": "string"}}},
                    handler=lambda _params, _ctx: ToolResult(content="ok"),
                )
            )
            registry.register(
                ToolDefinition(
                    name="Strict",
                    description="Reject unknown fields.",
                    input_schema={
                        "type": "object",
                        "properties": {"value": {"type": "string"}},
                        "additionalProperties": False,
                    },
                    handler=lambda _params, _ctx: ToolResult(content="ok"),
                )
            )

            self.assertEqual(
                registry.execute("Loose", {"value": "x", "extra": True}, settings).content,
                "ok",
            )
            with self.assertRaises(ToolError) as raised:
                registry.execute("Strict", {"value": "x", "extra": True}, settings)
            self.assertIn("Unknown parameter 'parameters.extra'", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
