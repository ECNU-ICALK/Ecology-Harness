import json
import os
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


class EcologyToolTests(unittest.TestCase):
    def _make_app(self, root: Path) -> EcologyHarnessApp:
        settings = HarnessSettings.from_workspace(root)
        settings.user_state_dir = root / ".user_state"
        app = EcologyHarnessApp(settings)
        app.initialize()
        return app

    def test_list_ecology_functions_returns_categories(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._make_app(Path(tmpdir))

            result = app.registry.execute(
                "ListEcologyFunctions",
                {},
                app.settings,
                services=app.get_services(),
            )

            self.assertIn("Field observation and species identification", result.content)
            self.assertIn("Plant phenotyping and trait extraction", result.content)
            self.assertIn("Closed algal systems and photobioreactors", result.content)
            self.assertIn("Aquatic microcosms, plankton, and biofilm monitoring", result.content)

    def test_list_ecology_toolkits_filters_by_modality(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._make_app(Path(tmpdir))

            result = app.registry.execute(
                "ListEcologyToolkits",
                {"modality": "audio-identification"},
                app.settings,
                services=app.get_services(),
            )

            self.assertIn("birdnet-analyzer", result.content)
            self.assertEqual(len(result.data["toolkits"]), 1)

    def test_list_ecology_toolkits_can_filter_lab_automation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._make_app(Path(tmpdir))

            result = app.registry.execute(
                "ListEcologyToolkits",
                {"modality": "lab-automation"},
                app.settings,
                services=app.get_services(),
            )

            self.assertIn("pylabrobot", result.content)
            self.assertIn("opentrons", result.content)
            self.assertEqual(len(result.data["toolkits"]), 2)

    def test_list_ecology_toolkits_can_find_plankton_classification_stack(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._make_app(Path(tmpdir))

            result = app.registry.execute(
                "ListEcologyToolkits",
                {"query": "plankton"},
                app.settings,
                services=app.get_services(),
            )

            self.assertIn("planktoscope", result.content)
            self.assertIn("ecotaxa-py-client", result.content)

    def test_inaturalist_search_taxa_parses_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._make_app(Path(tmpdir))
            payload = {
                "results": [
                    {
                        "id": 47126,
                        "name": "Quercus alba",
                        "preferred_common_name": "White Oak",
                        "rank": "species",
                        "observations_count": 12034,
                    }
                ]
            }
            with patch(
                "ecology_harness.tools.builtin.ecology_tools.request.urlopen",
                return_value=_FakeResponse(json.dumps(payload)),
            ):
                result = app.registry.execute(
                    "INaturalistSearchTaxa",
                    {"query": "Quercus alba"},
                    app.settings,
                    services=app.get_services(),
                )

            self.assertIn("White Oak", result.content)
            self.assertEqual(result.data["results"][0]["id"], 47126)

    def test_plantnet_identify_parses_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            image_path = root / "leaf.jpg"
            image_path.write_bytes(b"fake-image")
            app = self._make_app(root)
            payload = {
                "results": [
                    {
                        "score": 0.91,
                        "species": {
                            "scientificNameWithoutAuthor": "Quercus alba",
                            "commonNames": ["White Oak"],
                            "family": {"scientificNameWithoutAuthor": "Fagaceae"},
                            "genus": {"scientificNameWithoutAuthor": "Quercus"},
                        },
                    }
                ]
            }
            with patch.dict(os.environ, {"PLANTNET_API_KEY": "demo-key"}, clear=False):
                with patch(
                    "ecology_harness.tools.builtin.ecology_tools.request.urlopen",
                    return_value=_FakeResponse(json.dumps(payload)),
                ):
                    result = app.registry.execute(
                        "PlantNetIdentify",
                        {"image_paths": ["leaf.jpg"], "organs": ["leaf"]},
                        app.settings,
                        services=app.get_services(),
                    )

            self.assertIn("Quercus alba", result.content)
            self.assertEqual(result.data["results"][0]["family"], "Fagaceae")


if __name__ == "__main__":
    unittest.main()
