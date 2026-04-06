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


if __name__ == "__main__":
    unittest.main()
