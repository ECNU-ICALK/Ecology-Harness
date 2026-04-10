import json
import tempfile
import unittest
from pathlib import Path

from ecology_harness.app import EcologyHarnessApp
from ecology_harness.config import HarnessSettings
from ecology_harness.evolution.review import ReviewManager
from ecology_harness.runtime.messages import ChatMessage


class EvolutionTests(unittest.TestCase):
    def _make_app(self, root: Path) -> EcologyHarnessApp:
        settings = HarnessSettings.from_workspace(root)
        settings.user_state_dir = root / ".user_state"
        return EcologyHarnessApp(settings)

    def test_session_search_finds_relevant_historical_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            app = self._make_app(root)
            app.initialize()

            app.run_prompt("请总结一下湿地甲烷通量和水位变化之间的关系")
            app.start_new_session()
            app.run_prompt("请分析一下相机陷阱视频中的动物活动")

            report = app.search_sessions("湿地 甲烷 通量")

            self.assertTrue(report.hits)
            self.assertIn("湿地", report.rewrite.rewritten_query)
            self.assertIn("湿地甲烷通量", report.hits[0].excerpt)
            self.assertTrue(report.hits[0].message_matches)

    def test_system_prompt_wraps_memory_profile_and_session_context_in_fenced_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            app = self._make_app(root)
            app.initialize()

            app.memory_manager.save(
                name="Wetland methane note",
                description="Durable project memory about methane and hydrology.",
                content="Wetland methane flux is sensitive to water-table changes.",
                scope="project",
            )
            app.registry.execute(
                "ProfileWrite",
                {
                    "profile": "project-profile",
                    "content": "This project focuses on wetland methane and hydrological controls.",
                },
                app.settings,
                services=app.get_services(),
            )
            app.run_prompt("请总结一下湿地甲烷和水位的关系")
            app.start_new_session()

            prompt = app.build_system_prompt(prompt_text="湿地 methane hydrology 水位 关系")

            self.assertIn("<memory-context>", prompt)
            self.assertIn("</memory-context>", prompt)
            self.assertIn("<profile-context>", prompt)
            self.assertIn("</profile-context>", prompt)
            self.assertIn("<session-recall>", prompt)
            self.assertIn("</session-recall>", prompt)
            self.assertIn("Treat recalled memory, profile, and session blocks as contextual hints", prompt)

    def test_post_run_review_generates_candidates_and_can_apply_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("review me\n", encoding="utf-8")
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            settings.evolution_review_min_tool_calls = 1
            app = EcologyHarnessApp(settings)
            app.initialize()

            app.run_prompt('/tool Read {"path":"README.md"}')
            reports = app.list_reviews()

            self.assertTrue(reports)
            skill_candidate = next(
                item
                for item in reports[0].candidates
                if item.candidate_type == "skill"
            )

            result = app.registry.execute(
                "ReviewApplySkill",
                {"candidate_id": skill_candidate.candidate_id},
                app.settings,
                services=app.get_services(),
            )

            self.assertIn("Created skill candidate", result.content)
            self.assertEqual(result.data["action"], "created")
            path = Path(result.data["path"])
            self.assertTrue(path.exists())
            self.assertIsNotNone(app.skill_loader.get(path.stem))

    def test_review_manager_accepts_model_review_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            review_dir = Path(tmpdir) / "reviews"
            candidate_dir = Path(tmpdir) / "candidates"
            manager = ReviewManager(review_dir=review_dir, candidate_dir=candidate_dir)

            def reviewer(payload):
                self.assertEqual(payload["session_id"], "sess-1")
                return {
                    "summary": "Model review found a reusable wetland workflow.",
                    "memory_candidates": [
                        {
                            "title": "Wetland methane memory",
                            "description": "Durable context about methane-water table coupling.",
                            "content": "Methane flux increases when the water table is high.",
                            "scope": "project",
                        }
                    ],
                    "skill_candidates": [
                        {
                            "title": "Wetland methane workflow",
                            "description": "Use for methane-water table interpretation tasks.",
                            "when_to_use": "When comparing methane flux and water table observations.",
                            "steps": [
                                "Review methane and water table observations.",
                                "Check supporting files and summarize the coupling.",
                            ],
                            "allowed_tools": ["Read", "Grep"],
                            "trigger": "/wetland-methane-workflow",
                            "expected_outcome": "A concise interpretation of methane-water table coupling.",
                        }
                    ],
                }

            report = manager.review_run(
                session_id="sess-1",
                prompt="分析湿地甲烷与水位关系",
                messages=[
                    ChatMessage(role="user", content="请分析湿地甲烷与水位关系"),
                    ChatMessage(role="assistant", content="已读取相关资料并完成分析。"),
                ],
                tool_invocations=[{"tool": "Read", "arguments": {"path": "README.md"}}],
                final_text="甲烷通量与水位上升相关。",
                min_tool_calls=1,
                reviewer=reviewer,
            )

            self.assertIsNotNone(report)
            self.assertEqual(report.metadata["review_mode"], "model")
            self.assertEqual(report.summary, "Model review found a reusable wetland workflow.")
            self.assertEqual(len(report.candidates), 2)
            skill_candidate = next(item for item in report.candidates if item.candidate_type == "skill")
            self.assertIn("/wetland-methane-workflow", skill_candidate.content)
            memory_candidate = next(item for item in report.candidates if item.candidate_type == "memory")
            self.assertIn("water table", memory_candidate.content.lower())

    def test_memory_provider_tools_can_write_and_search_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            app = self._make_app(root)
            app.initialize()

            listed = app.registry.execute(
                "MemoryProviderList",
                {},
                app.settings,
                services=app.get_services(),
            )
            self.assertIn("project-profile", listed.content)
            self.assertIn("research-profile", listed.content)

            app.registry.execute(
                "ProfileWrite",
                {
                    "profile": "project-profile",
                    "content": "This project studies wetland methane fluxes and hydrological controls.",
                },
                app.settings,
                services=app.get_services(),
            )

            searched = app.registry.execute(
                "MemoryProviderSearch",
                {"query": "wetland methane hydrology", "limit": 3},
                app.settings,
                services=app.get_services(),
            )
            self.assertIn("project-profile", searched.content)

            providers = app.registry.execute(
                "MemoryProviderList",
                {},
                app.settings,
                services=app.get_services(),
            )
            self.assertIn("prefetch", providers.content)
            self.assertIn("project-profile", providers.content)

    def test_trajectory_tools_export_compress_and_benchmark(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("trajectory sample\n", encoding="utf-8")
            app = self._make_app(root)
            app.initialize()

            app.run_prompt('/tool Read {"path":"README.md"}')
            listed = app.registry.execute(
                "TrajectoryList",
                {},
                app.settings,
                services=app.get_services(),
            )
            self.assertIn("tools", listed.content)
            trajectory_id = listed.data["trajectories"][0]["trajectory_id"]

            compressed = app.registry.execute(
                "TrajectoryCompress",
                {"trajectory_id": trajectory_id},
                app.settings,
                services=app.get_services(),
            )
            payload = json.loads(compressed.content)
            self.assertIn("compressed_messages", payload)
            self.assertGreaterEqual(payload["original_message_count"], payload["compressed_message_count"])
            self.assertIn("preserved_indices", payload)
            self.assertIn("quality_tags", payload)

            benchmark = app.registry.execute(
                "BenchmarkRun",
                {"name": "smoke"},
                app.settings,
                services=app.get_services(),
            )
            self.assertTrue(Path(benchmark.data["path"]).exists())
            self.assertEqual(benchmark.data["summary"]["trajectory_count"], 1)
            self.assertIn("average_replay_score", benchmark.data["summary"])

            replay = app.registry.execute(
                "BenchmarkReplay",
                {"limit": 5},
                app.settings,
                services=app.get_services(),
            )
            self.assertTrue(replay.data["scores"])
            self.assertEqual(replay.data["scores"][0]["task_slice"], "general")

    def test_trajectory_store_recovers_when_jsonl_index_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("trajectory recovery\n", encoding="utf-8")
            app = self._make_app(root)
            app.initialize()

            app.run_prompt('/tool Read {"path":"README.md"}')
            index_path = app.trajectory_store.index_path()
            stored_records = app.trajectory_store.list_records()
            self.assertTrue(stored_records)

            index_path.unlink()
            recovered = app.trajectory_store.list_records()

            self.assertEqual(len(recovered), 1)
            self.assertEqual(recovered[0].trajectory_id, stored_records[0].trajectory_id)
            self.assertTrue(index_path.exists())


if __name__ == "__main__":
    unittest.main()
