import unittest

from ecology_harness.ui.console import ConsoleRenderer


class _BrokenPipeStream:
    def isatty(self):
        return False

    def write(self, _text):
        raise BrokenPipeError()

    def flush(self):
        raise BrokenPipeError()

    def close(self):
        return None


class ConsoleRendererTests(unittest.TestCase):
    def test_print_exits_cleanly_on_broken_pipe(self) -> None:
        renderer = ConsoleRenderer(stream=_BrokenPipeStream())

        with self.assertRaises(SystemExit) as ctx:
            renderer.print("hello")

        self.assertEqual(ctx.exception.code, 0)

    def test_format_trace_event_renders_richer_tool_result(self) -> None:
        renderer = ConsoleRenderer(stream=_BrokenPipeStream())

        rendered = renderer.format_trace_event(
            "tool_result",
            {
                "tool": "WebSearch",
                "allowed": True,
                "output": "Top result: Wetland monitoring handbook",
                "duration_ms": 842,
                "data_keys": ["results", "query"],
            },
        )

        self.assertIsInstance(rendered, list)
        lines = rendered if isinstance(rendered, list) else [rendered]
        self.assertTrue(any("WebSearch" in line for line in lines))
        self.assertTrue(any("842ms" in line for line in lines))
        self.assertTrue(any("Wetland monitoring handbook" in line for line in lines))

    def test_format_trace_event_renders_step_started(self) -> None:
        renderer = ConsoleRenderer(stream=_BrokenPipeStream())

        rendered = renderer.format_trace_event(
            "step_started",
            {"step": 2, "available_tool_count": 14},
        )

        self.assertIsInstance(rendered, str)
        self.assertIn("step 2", rendered)
        self.assertIn("14", rendered)


if __name__ == "__main__":
    unittest.main()
