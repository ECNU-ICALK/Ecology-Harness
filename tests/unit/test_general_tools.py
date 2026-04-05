import json
import tempfile
import unittest
from pathlib import Path
from typing import Optional
from unittest.mock import patch

from ecology_harness.app import EcologyHarnessApp
from ecology_harness.config import HarnessSettings


class _FakeResponse:
    def __init__(self, payload: str) -> None:
        self.payload = payload.encode("utf-8")

    def read(self, _limit: Optional[int] = None):
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        del exc_type, exc, tb
        return False


class GeneralToolTests(unittest.TestCase):
    def _make_app(self, root: Path) -> EcologyHarnessApp:
        settings = HarnessSettings.from_workspace(root)
        settings.user_state_dir = root / ".user_state"
        app = EcologyHarnessApp(settings)
        app.initialize()
        return app

    def test_get_diagnostics_reports_python_syntax_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "broken.py").write_text("def bad(:\n    pass\n", encoding="utf-8")
            app = self._make_app(root)

            result = app.registry.execute(
                "GetDiagnostics",
                {"path": "broken.py"},
                app.settings,
                services=app.get_services(),
            )

            self.assertIn("SyntaxError", result.content)

    def test_notebook_edit_replaces_cell_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            notebook = {
                "cells": [
                    {"cell_type": "code", "metadata": {}, "source": ["print('a')\n"], "outputs": [], "execution_count": None},
                    {"cell_type": "markdown", "metadata": {}, "source": ["hello\n"]},
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
            (root / "demo.ipynb").write_text(json.dumps(notebook), encoding="utf-8")
            app = self._make_app(root)

            result = app.registry.execute(
                "NotebookEdit",
                {
                    "notebook_path": "demo.ipynb",
                    "action": "replace",
                    "cell_id": "cell-0",
                    "new_source": "print('b')\n",
                },
                app.settings,
                services=app.get_services(),
            )

            updated = json.loads((root / "demo.ipynb").read_text(encoding="utf-8"))
            self.assertIn("Notebook updated", result.content)
            self.assertEqual(updated["cells"][0]["source"], ["print('b')\n"])

    def test_websearch_parses_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            app = self._make_app(root)
            html = """
            <html><body>
              <a class="result__a" href="https://example.com/one">Result One</a>
              <a class="result__a" href="https://example.com/two">Result Two</a>
            </body></html>
            """
            with patch("ecology_harness.tools.builtin.web_tools.request.urlopen", return_value=_FakeResponse(html)):
                result = app.registry.execute(
                    "WebSearch",
                    {"query": "example"},
                    app.settings,
                    services=app.get_services(),
                )

            self.assertIn("Result One", result.content)
            self.assertEqual(len(result.data["results"]), 2)


if __name__ == "__main__":
    unittest.main()
