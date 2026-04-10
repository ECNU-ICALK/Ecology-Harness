import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ecology_harness.app import EcologyHarnessApp
from ecology_harness.config import HarnessSettings
from ecology_harness.ui.repl_input import (
    _should_use_prompt_toolkit,
    _strip_control_sequences,
    build_toolbar_text,
    suggest_repl_commands,
)


class ReplInputTests(unittest.TestCase):
    def _app(self):
        tmpdir = tempfile.TemporaryDirectory()
        root = Path(tmpdir.name)
        settings = HarnessSettings.from_workspace(root)
        settings.user_state_dir = root / ".user_state"
        app = EcologyHarnessApp(settings)
        app.initialize()
        self.addCleanup(tmpdir.cleanup)
        return app

    def test_slash_suggestions_include_session_commands_and_skills(self) -> None:
        app = self._app()
        suggestions = suggest_repl_commands(app, "/")
        names = {item.text for item in suggestions}

        self.assertIn("/help", names)
        self.assertIn("/doctor", names)
        self.assertIn("/setup", names)
        self.assertIn("/explore", names)
        self.assertIn("/status", names)
        self.assertIn("/runtime", names)
        self.assertIn("/analytics", names)
        self.assertIn("/config", names)
        self.assertIn("/model", names)
        self.assertIn("/plugins", names)
        self.assertIn("/mcp", names)
        self.assertIn("/tool", names)
        self.assertIn("/explain", names)
        self.assertIn("/clarify", names)

    def test_tool_suggestions_expand_after_tool_prefix(self) -> None:
        app = self._app()
        suggestions = suggest_repl_commands(app, "/tool Re")
        names = {item.text for item in suggestions}

        self.assertIn("/tool Read", names)

    def test_backslash_suggestions_offer_session_aliases(self) -> None:
        app = self._app()
        suggestions = suggest_repl_commands(app, "\\")
        names = {item.text for item in suggestions}

        self.assertIn("\\help", names)
        self.assertIn("\\quit", names)
        self.assertNotIn("/tool", names)

    def test_toolbar_text_includes_provider_model_and_session_state(self) -> None:
        app = self._app()
        app.settings.provider = "auto"
        app.settings.model = "mock-agent"
        state = type(
            "State",
            (),
            {
                "turn_count": 2,
                "trace_enabled": False,
                "conversation": [object(), object(), object()],
                "total_tool_calls": 4,
            },
        )()

        toolbar = build_toolbar_text(app, state)

        self.assertIn("/ for commands", toolbar)
        self.assertIn("provider: auto", toolbar)
        self.assertIn("model: mock-agent", toolbar)
        self.assertIn("mode: default", toolbar)
        self.assertIn("profile: default", toolbar)
        self.assertIn("trace: off", toolbar)
        self.assertIn("turns: 2", toolbar)
        self.assertIn("ctx:", toolbar)
        self.assertIn("tools: 4", toolbar)

    def test_strip_control_sequences_removes_arrow_escape_codes(self) -> None:
        cleaned = _strip_control_sequences("hello\x1b[A\x1b[Bworld")
        self.assertEqual(cleaned, "helloworld")

    def test_prompt_toolkit_can_be_forced_off(self) -> None:
        with patch.dict("os.environ", {"EH_FORCE_BASIC_REPL": "1"}, clear=False):
            self.assertFalse(_should_use_prompt_toolkit())


if __name__ == "__main__":
    unittest.main()
