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
            self.assertIn("Crop, plant, and growth simulation", result.content)
            self.assertIn("Plant-type-specific growth and woody-vegetation simulation", result.content)
            self.assertIn("Agent-based and individual-based ecosystem modeling", result.content)
            self.assertIn("Microbial community, biofilm, and reactor simulation", result.content)
            self.assertIn("Closed algal systems and photobioreactors", result.content)
            self.assertIn("Aquatic microcosms, plankton, and biofilm monitoring", result.content)
            self.assertIn("Root phenotyping and rhizosphere imaging", result.content)
            self.assertIn("Lake, reservoir, and aquatic ecosystem modeling", result.content)
            self.assertIn("Microbial amplicon, taxonomy, and metabolic reconstruction", result.content)
            self.assertIn("Animal behavior and pose tracking", result.content)
            self.assertIn("Ecological 3D reconstruction, point clouds, and habitat visualization", result.content)
            self.assertIn("Species distribution, biodiversity, and occurrence-data modeling", result.content)
            self.assertIn("Movement ecology and telemetry analysis", result.content)
            self.assertIn("Open environmental data, hydrology, soil, and exposure APIs", result.content)
            self.assertIn("Earth-observation catalog and raster analytics", result.content)

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

    def test_list_ecology_toolkits_can_find_growth_simulation_stack(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._make_app(Path(tmpdir))

            result = app.registry.execute(
                "ListEcologyToolkits",
                {"query": "simulation"},
                app.settings,
                services=app.get_services(),
            )

            self.assertIn("pcse-wofost", result.content)
            self.assertIn("cobrapy", result.content)

    def test_describe_ecology_toolkit_reports_growth_model_details(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._make_app(Path(tmpdir))

            result = app.registry.execute(
                "DescribeEcologyToolkit",
                {"name": "aquacrop-ospy"},
                app.settings,
                services=app.get_services(),
            )

            self.assertIn("AquaCrop-OSPy", result.content)
            self.assertIn("water-limited crop growth", result.content)

    def test_list_ecology_toolkits_can_find_woody_plant_stack(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._make_app(Path(tmpdir))

            result = app.registry.execute(
                "ListEcologyToolkits",
                {"query": "woody"},
                app.settings,
                services=app.get_services(),
            )

            self.assertIn("medfate", result.content)
            self.assertIn("r3pg", result.content)

    def test_list_ecology_toolkits_can_find_microbial_community_stack(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._make_app(Path(tmpdir))

            result = app.registry.execute(
                "ListEcologyToolkits",
                {"query": "biofilm"},
                app.settings,
                services=app.get_services(),
            )

            self.assertIn("nufeb", result.content)

    def test_list_ecology_toolkits_can_find_process_model_stack(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._make_app(Path(tmpdir))

            result = app.registry.execute(
                "ListEcologyToolkits",
                {"query": "agent-based"},
                app.settings,
                services=app.get_services(),
            )

            self.assertIn("netlogo", result.content)
            self.assertIn("mesa", result.content)

    def test_list_ecology_toolkits_can_find_root_phenotyping_stack(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._make_app(Path(tmpdir))

            result = app.registry.execute(
                "ListEcologyToolkits",
                {"query": "root"},
                app.settings,
                services=app.get_services(),
            )

            self.assertIn("rhizovision-explorer", result.content)
            self.assertIn("opensimroot", result.content)

    def test_list_ecology_toolkits_can_find_aquatic_modeling_stack(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._make_app(Path(tmpdir))

            result = app.registry.execute(
                "ListEcologyToolkits",
                {"query": "lake"},
                app.settings,
                services=app.get_services(),
            )

            self.assertIn("glm", result.content)
            self.assertIn("glm-py", result.content)

    def test_list_ecology_toolkits_can_find_behavior_tracking_stack(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._make_app(Path(tmpdir))

            result = app.registry.execute(
                "ListEcologyToolkits",
                {"query": "pose"},
                app.settings,
                services=app.get_services(),
            )

            self.assertIn("deeplabcut", result.content)
            self.assertIn("sleap", result.content)

    def test_list_ecology_toolkits_can_find_species_distribution_stack(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._make_app(Path(tmpdir))

            result = app.registry.execute(
                "ListEcologyToolkits",
                {"query": "species distribution model"},
                app.settings,
                services=app.get_services(),
            )

            self.assertIn("biomod2", result.content)
            self.assertIn("enmeval", result.content)
            self.assertIn("maxnet", result.content)

    def test_list_ecology_toolkits_expands_chinese_environmental_query(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._make_app(Path(tmpdir))

            result = app.registry.execute(
                "ListEcologyToolkits",
                {"query": "玉米干旱灌溉模拟需要土壤和水文数据"},
                app.settings,
                services=app.get_services(),
            )

            self.assertIn("dataretrieval-python", result.content)
            self.assertIn("soilgrids-api", result.content)

    def test_list_ecology_toolkits_can_find_movement_stack(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._make_app(Path(tmpdir))

            result = app.registry.execute(
                "ListEcologyToolkits",
                {"query": "movement telemetry home range"},
                app.settings,
                services=app.get_services(),
            )

            self.assertIn("ctmm", result.content)
            self.assertIn("amt", result.content)
            self.assertIn("move2", result.content)

    def test_list_ecology_toolkits_can_find_point_cloud_stack(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._make_app(Path(tmpdir))

            result = app.registry.execute(
                "ListEcologyToolkits",
                {"query": "point cloud"},
                app.settings,
                services=app.get_services(),
            )

            self.assertIn("pdal", result.content)
            self.assertIn("cloudcompare", result.content)
            self.assertIn("potree", result.content)

    def test_list_ecology_toolkits_can_find_qsm_stack(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._make_app(Path(tmpdir))

            result = app.registry.execute(
                "ListEcologyToolkits",
                {"query": "qsm"},
                app.settings,
                services=app.get_services(),
            )

            self.assertIn("treeqsm", result.content)
            self.assertIn("simpleforest", result.content)

    def test_list_ecology_toolkits_can_find_scientific_3d_publishing_stack(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._make_app(Path(tmpdir))

            result = app.registry.execute(
                "ListEcologyToolkits",
                {"query": "scientific 3D publishing"},
                app.settings,
                services=app.get_services(),
            )

            self.assertIn("paraview", result.content)

    def test_list_ecology_toolkits_can_find_geospatial_3d_publishing_stack(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._make_app(Path(tmpdir))

            result = app.registry.execute(
                "ListEcologyToolkits",
                {"query": "geospatial 3D publishing"},
                app.settings,
                services=app.get_services(),
            )

            self.assertIn("cesiumjs", result.content)

    def test_describe_ecology_toolkit_reports_photogrammetry_details(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._make_app(Path(tmpdir))

            result = app.registry.execute(
                "DescribeEcologyToolkit",
                {"name": "opendronemap"},
                app.settings,
                services=app.get_services(),
            )

            self.assertIn("OpenDroneMap", result.content)
            self.assertIn("drone imagery", result.content)

    def test_describe_ecology_toolkit_reports_qsm_details(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._make_app(Path(tmpdir))

            result = app.registry.execute(
                "DescribeEcologyToolkit",
                {"name": "treeqsm"},
                app.settings,
                services=app.get_services(),
            )

            self.assertIn("TreeQSM", result.content)
            self.assertIn("single-tree", result.content)

    def test_describe_ecology_toolkit_reports_process_model_details(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._make_app(Path(tmpdir))

            result = app.registry.execute(
                "DescribeEcologyToolkit",
                {"name": "dssat-csm"},
                app.settings,
                services=app.get_services(),
            )

            self.assertIn("DSSAT Cropping System Model", result.content)
            self.assertIn("Long-running crop-system modeling framework", result.content)

    def test_describe_ecology_toolkit_reports_microbial_simulation_details(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._make_app(Path(tmpdir))

            result = app.registry.execute(
                "DescribeEcologyToolkit",
                {"name": "comets"},
                app.settings,
                services=app.get_services(),
            )

            self.assertIn("COMETS", result.content)
            self.assertIn("Community metabolism simulator", result.content)

    def test_describe_ecology_toolkit_reports_amplicon_tool_details(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._make_app(Path(tmpdir))

            result = app.registry.execute(
                "DescribeEcologyToolkit",
                {"name": "mothur"},
                app.settings,
                services=app.get_services(),
            )

            self.assertIn("mothur", result.content)
            self.assertIn("amplicon-analysis platform", result.content)

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
