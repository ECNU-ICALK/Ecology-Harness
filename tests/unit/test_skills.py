import tempfile
import unittest
from pathlib import Path
import os
import json

from ecology_harness.app import EcologyHarnessApp
from ecology_harness.config import HarnessSettings, Settings
from ecology_harness.skills import SkillLoader
from ecology_harness.runtime.messages import ChatMessage


class SkillTests(unittest.TestCase):
    def test_public_settings_alias_and_skill_loader_factory_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = Settings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            loader = SkillLoader.from_settings(settings)

            self.assertIsInstance(settings, HarnessSettings)
            self.assertEqual(loader.project_dir, settings.skill_dir)
            self.assertEqual(loader.user_dir, settings.user_skill_dir)
            self.assertTrue((loader.builtin_dir / "plan.md").exists())

    def test_builtin_skills_are_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            skills = app.skill_loader.list_skills()
            self.assertTrue(any(item.slug == "plan" for item in skills))
            self.assertTrue(any(item.slug == "recent-research-scan" for item in skills))
            self.assertTrue(any(item.slug == "deep-interview" for item in skills))
            self.assertTrue(any(item.slug == "ralplan" for item in skills))
            self.assertTrue(any(item.slug == "ralph" for item in skills))
            self.assertTrue(any(item.slug == "expand-references" for item in skills))
            self.assertTrue(any(item.slug == "mapbox-geospatial-operations" for item in skills))
            self.assertTrue(any(item.slug == "ecology-dataset-hunt" for item in skills))
            self.assertTrue(any(item.slug == "literature-multi-source-search" for item in skills))
            self.assertTrue(any(item.slug == "open-access-paper-harvest" for item in skills))
            self.assertTrue(any(item.slug == "open-meteo" for item in skills))
            self.assertTrue(any(item.slug == "species-occurrence-workbench" for item in skills))
            self.assertTrue(any(item.slug == "microbial-ecology-sequence-workflow" for item in skills))
            self.assertTrue(any(item.slug == "closed-algae-system-design" for item in skills))
            self.assertTrue(any(item.slug == "algal-timeseries-and-mass-balance" for item in skills))
            self.assertTrue(any(item.slug == "aquatic-microcosm-foodweb-design" for item in skills))
            self.assertTrue(any(item.slug == "plankton-microscopy-and-auto-classification" for item in skills))
            self.assertTrue(any(item.slug == "plant-growth-model-selection" for item in skills))
            self.assertTrue(any(item.slug == "crop-growth-simulation-workflow" for item in skills))
            self.assertTrue(any(item.slug == "crop-water-and-irrigation-simulation" for item in skills))
            self.assertTrue(any(item.slug == "microbial-growth-and-community-simulation" for item in skills))
            self.assertTrue(any(item.slug == "root-and-rhizosphere-architecture-modeling" for item in skills))
            self.assertTrue(any(item.slug == "woody-plant-and-forest-simulation" for item in skills))
            self.assertTrue(any(item.slug == "microbial-community-metabolism-simulation" for item in skills))
            self.assertTrue(any(item.slug == "microbial-biofilm-and-reactor-simulation" for item in skills))
            self.assertTrue(any(item.slug == "microbiome-timeseries-and-benchmark-simulation" for item in skills))
            self.assertTrue(any(item.slug == "process-model-selection" for item in skills))
            self.assertTrue(any(item.slug == "agent-based-ecology-modeling" for item in skills))
            self.assertTrue(any(item.slug == "food-web-and-trophic-simulation" for item in skills))
            self.assertTrue(any(item.slug == "literature-review" for item in skills))
            self.assertTrue(any(item.slug == "paper-lookup" for item in skills))
            self.assertTrue(any(item.slug == "geopandas" for item in skills))
            self.assertTrue(any(item.slug == "statistical-analysis" for item in skills))
            self.assertTrue(any(item.slug == "scientific-visualization" for item in skills))
            self.assertTrue(any(item.slug == "biopython" for item in skills))
            self.assertTrue(any(item.slug == "scikit-bio" for item in skills))
            self.assertTrue(any(item.slug == "phylogenetics" for item in skills))
            self.assertTrue(any(item.slug == "open-notebook" for item in skills))
            self.assertTrue(any(item.slug == "systematic-debugging" for item in skills))
            self.assertTrue(any(item.slug == "test-driven-development" for item in skills))
            self.assertTrue(any(item.slug == "verification-before-completion" for item in skills))
            self.assertTrue(any(item.slug == "writing-plans" for item in skills))
            self.assertTrue(any(item.slug == "using-git-worktrees" for item in skills))
            self.assertTrue(any(item.slug == "humanizer" for item in skills))
            self.assertTrue(any(item.slug == "autoresearch" for item in skills))
            self.assertTrue(any(item.slug == "implementing-llms-litgpt" for item in skills))
            self.assertTrue(any(item.slug == "sentencepiece" for item in skills))
            self.assertTrue(any(item.slug == "peft-fine-tuning" for item in skills))
            self.assertTrue(any(item.slug == "evaluating-llms-harness" for item in skills))
            self.assertTrue(any(item.slug == "serving-llms-vllm" for item in skills))
            self.assertTrue(any(item.slug == "mlflow" for item in skills))
            self.assertTrue(any(item.slug == "whisper" for item in skills))
            self.assertTrue(any(item.slug == "academic-plotting" for item in skills))
            self.assertTrue(any(item.slug == "brainstorming-research-ideas" for item in skills))
            self.assertFalse(any(item.slug == "reference" for item in skills))
            self.assertFalse(any(item.slug == "performance-testing" for item in skills))

            result = app.registry.execute(
                "SkillRead",
                {"name": "review"},
                app.settings,
                services=app.get_services(),
            )
            self.assertIn("correctness bugs", result.content)

    def test_skill_tool_executes_inline_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            custom_skill = app.settings.skill_dir / "create-task.md"
            custom_skill.write_text(
                "---\n"
                "name: create-task\n"
                "description: Create a task from the provided argument.\n"
                "slug: create-task\n"
                "arguments: [subject]\n"
                "context: inline\n"
                "---\n"
                "/tool TaskCreate {\"subject\":\"$SUBJECT\"}\n",
                encoding="utf-8",
            )

            result = app.registry.execute(
                "Skill",
                {"name": "create-task", "args": "FromSkill"},
                app.settings,
                services=app.get_services(),
            )

            self.assertIn("Created task #1", result.content)

    def test_run_prompt_auto_triggers_builtin_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            result = app.run_prompt("/explain README")

            self.assertTrue(result.final_text)

    def test_workflow_skill_triggers_are_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            deep_interview = app.skill_loader.get("deep-interview")
            ralplan = app.skill_loader.get("ralplan")
            ralph = app.skill_loader.get("ralph")

            self.assertIsNotNone(deep_interview)
            self.assertIsNotNone(ralplan)
            self.assertIsNotNone(ralph)
            self.assertIn("/clarify", deep_interview.triggers)
            self.assertIn("/ralplan", ralplan.triggers)
            self.assertIn("/ralph", ralph.triggers)

    def test_bundle_skill_render_includes_bundle_root_hint(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            skill = app.skill_loader.get("expand-references")
            self.assertIsNotNone(skill)

            rendered = app.skill_loader.render(skill, "Attention Is All You Need")

            self.assertIn("Skill bundle root:", rendered)
            self.assertIn("scripts/run.py", rendered)

    def test_vendored_scientific_bundle_skill_render_preserves_bundle_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            skill = app.skill_loader.get("literature-review")
            self.assertIsNotNone(skill)

            rendered = app.skill_loader.render(skill, "wetland methane")

            self.assertIn("Skill bundle root:", rendered)
            self.assertIn("scripts/search_databases.py", rendered)
            self.assertIn("references/database_strategies.md", rendered)

    def test_vendored_superpowers_bundle_skill_render_preserves_bundle_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            skill = app.skill_loader.get("using-superpowers")
            self.assertIsNotNone(skill)

            rendered = app.skill_loader.render(skill, "")

            self.assertIn("Skill bundle root:", rendered)
            self.assertIn("references/codex-tools.md", rendered)

    def test_vendored_humanizer_skill_is_loadable_as_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            skill = app.skill_loader.get("humanizer")
            self.assertIsNotNone(skill)
            self.assertIn("Remove signs of AI-generated writing", skill.description)
            self.assertEqual(skill.tools[:4], ["Read", "Write", "Edit", "Grep"])

            rendered = app.skill_loader.render(skill, "Make this sound less robotic.")

            self.assertIn("Skill bundle root:", rendered)
            self.assertIn("Remove AI Writing Patterns", rendered)

    def test_vendored_ai_research_skill_is_loadable_as_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            skill = app.skill_loader.get("autoresearch")
            self.assertIsNotNone(skill)
            self.assertIn("autonomous AI research projects", skill.description)

            rendered = app.skill_loader.render(skill, "")

            self.assertIn("Skill bundle root:", rendered)
            self.assertIn("research-state.yaml", rendered)

    def test_skill_search_rewrites_chinese_growth_query(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            report = app.skill_loader.search("植物生长模拟 玉米 干旱 灌溉", limit=5)
            slugs = [item.skill.slug for item in report.hits]

            self.assertIn("plant-growth-model-selection", slugs)
            self.assertIn("crop-water-and-irrigation-simulation", slugs)
            self.assertIn("plant growth simulation", report.rewrite.rewritten_query)
            self.assertIn("maize", report.rewrite.rewritten_query)
            self.assertIn("drought", report.rewrite.rewritten_query)

    def test_skill_search_uses_conversation_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            custom_skill = app.settings.skill_dir / "benthic-biofilm-monitor.md"
            custom_skill.write_text(
                "---\n"
                "name: benthic-biofilm-monitor\n"
                "description: Monitor benthic algae, periphyton, and biofilm thickness in aquatic systems.\n"
                "slug: benthic-biofilm-monitor\n"
                "triggers: [/benthic-biofilm-monitor]\n"
                "context: inline\n"
                "---\n"
                "Focus on microscopy, fluorescence, and biofilm monitoring workflows.\n",
                encoding="utf-8",
            )

            conversation = [
                ChatMessage(
                    role="user",
                    content="我们在做底栖藻类、生物膜厚度和荧光监测的水体微宇宙实验。",
                )
            ]
            report = app.skill_loader.search("这个系统怎么监测？", conversation=conversation, limit=3)

            self.assertEqual(report.hits[0].skill.slug, "benthic-biofilm-monitor")
            self.assertTrue(report.rewrite.context_snippets)
            self.assertIn("biofilm", report.rewrite.rewritten_query)

    def test_build_system_prompt_injects_retrieved_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            settings.skill_prompt_top_k = 1
            app = EcologyHarnessApp(settings)
            app.initialize()

            custom_skill = app.settings.skill_dir / "lichen-succession-benchmark.md"
            custom_skill.write_text(
                "---\n"
                "name: lichen-succession-benchmark\n"
                "description: Compare monitoring and modeling workflows for lichen succession benchmark studies.\n"
                "slug: lichen-succession-benchmark\n"
                "triggers: [/lichen-succession-benchmark]\n"
                "context: inline\n"
                "---\n"
                "Use this for lichen succession benchmark analysis and monitoring.\n",
                encoding="utf-8",
            )

            prompt = app.build_system_prompt(prompt_text="lichen succession benchmark workflow")

            self.assertIn("Relevant skills for this request", prompt)
            self.assertIn("Skill retrieval query:", prompt)
            self.assertIn("lichen-succession-benchmark", prompt)

    def test_skill_search_tool_returns_ranked_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            result = app.registry.execute(
                "SkillSearch",
                {"query": "微生物群落代谢模拟 根际 共喂养", "limit": 3},
                app.settings,
                services=app.get_services(),
            )

            self.assertIn("Rewritten query:", result.content)
            self.assertIn("microbial-community-metabolism-simulation", result.content)
            self.assertTrue(result.data["hits"])

    def test_skill_hub_exposes_pack_metadata_and_upstream_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            result = app.registry.execute(
                "SkillHub",
                {"query": "systematic literature review citation workflow", "limit": 6},
                app.settings,
                services=app.get_services(),
            )

            scientific = next(item for item in result.data["packs"] if item["slug"] == "scientific")
            self.assertEqual(scientific["trust_level"], "trusted")
            self.assertIn("K-Dense-AI/claude-scientific-skills", scientific["source_url"])
            self.assertTrue(result.data["skills"])
            self.assertIn("literature-review", [item["slug"] for item in result.data["skills"]])

    def test_skill_view_lists_bundle_files_and_reads_specific_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            overview = app.registry.execute(
                "SkillView",
                {"name": "literature-review"},
                app.settings,
                services=app.get_services(),
            )
            available = [item["relative_path"] for item in overview.data["available_files"]]
            self.assertIn("scripts/search_databases.py", available)
            self.assertIn("references/database_strategies.md", available)

            detail = app.registry.execute(
                "SkillView",
                {"name": "literature-review", "file_path": "scripts/search_databases.py"},
                app.settings,
                services=app.get_services(),
            )
            self.assertEqual(
                detail.data["selected_file"]["relative_path"],
                "scripts/search_databases.py",
            )
            self.assertIn("search", detail.content.lower())

    def test_skill_view_blocks_path_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            with self.assertRaisesRegex(Exception, "inside the skill bundle"):
                app.registry.execute(
                    "SkillView",
                    {"name": "literature-review", "file_path": "../README.md"},
                    app.settings,
                    services=app.get_services(),
                )

    def test_old_skill_snapshot_is_rehydrated_for_hub_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            skill_path = app.skill_loader.builtin_dir / "scientific" / "literature-review" / "SKILL.md"
            snapshot_path = app.settings.skill_dir / ".skill-snapshot.json"
            snapshot_path.write_text(
                json.dumps(
                    {
                        "signature": app.skill_loader._directory_signature()[0],
                        "skills": [
                            {
                                "slug": "literature-review",
                                "name": "literature-review",
                                "description": "legacy snapshot entry",
                                "source": "builtin",
                                "content": "legacy body",
                                "path": str(skill_path),
                                "triggers": ["/literature-review"],
                                "tools": [],
                                "arguments": [],
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            app.skill_loader._mark_cache_dirty()

            skill = app.skill_loader.get("literature-review")
            self.assertIsNotNone(skill)
            self.assertEqual(skill.hub_pack, "scientific")
            self.assertEqual(skill.author, "K-Dense Inc.")
            self.assertIn("MIT", skill.license)

    def test_skill_readiness_and_cache_refresh_with_env_requirements(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            custom_skill = app.settings.skill_dir / "needs-env.md"
            custom_skill.write_text(
                "---\n"
                "name: needs-env\n"
                "description: Requires a token before use.\n"
                "slug: needs-env\n"
                "requirements: [env:ECOLOGY_HARNESS_TEST_TOKEN]\n"
                "setup-required: true\n"
                "context: inline\n"
                "---\n"
                "Use after setup is complete.\n",
                encoding="utf-8",
            )

            previous = os.environ.pop("ECOLOGY_HARNESS_TEST_TOKEN", None)
            try:
                skill = app.skill_loader.get("needs-env")
                self.assertIsNotNone(skill)
                self.assertEqual(skill.readiness, "setup-needed")
                self.assertIn("env:ECOLOGY_HARNESS_TEST_TOKEN", skill.missing_requirements)

                os.environ["ECOLOGY_HARNESS_TEST_TOKEN"] = "ready"
                custom_skill.write_text(
                    "---\n"
                    "name: needs-env\n"
                    "description: Requires a token before use.\n"
                    "slug: needs-env\n"
                    "requirements: [env:ECOLOGY_HARNESS_TEST_TOKEN]\n"
                    "context: inline\n"
                    "---\n"
                    "Use after setup is complete.\n",
                    encoding="utf-8",
                )
                refreshed = app.skill_loader.get("needs-env")
                self.assertIsNotNone(refreshed)
                self.assertEqual(refreshed.readiness, "ready")
            finally:
                if previous is None:
                    os.environ.pop("ECOLOGY_HARNESS_TEST_TOKEN", None)
                else:
                    os.environ["ECOLOGY_HARNESS_TEST_TOKEN"] = previous

    def test_skill_usage_governance_archive_and_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            duplicate_one = app.settings.skill_dir / "wetland-one.md"
            duplicate_one.write_text(
                "---\n"
                "name: wetland-one\n"
                "description: Analyze wetland methane and water-table coupling.\n"
                "slug: wetland-one\n"
                "triggers: [/wetland-one]\n"
                "context: inline\n"
                "---\n"
                "Use methane flux, water table, and hydrology observations to interpret wetland dynamics.\n",
                encoding="utf-8",
            )
            duplicate_two = app.settings.skill_dir / "wetland-two.md"
            duplicate_two.write_text(
                "---\n"
                "name: wetland-two\n"
                "description: Interpret wetland methane flux with water-table observations.\n"
                "slug: wetland-two\n"
                "triggers: [/wetland-two]\n"
                "context: inline\n"
                "---\n"
                "Use water-table, methane flux, and hydrology measurements to interpret wetland behavior.\n",
                encoding="utf-8",
            )

            app.registry.execute(
                "SkillDeprecate",
                {
                    "name": "wetland-two",
                    "reason": "Overlap with wetland-one",
                    "superseded_by": "wetland-one",
                },
                app.settings,
                services=app.get_services(),
            )
            deprecated = app.skill_loader.get("wetland-two")
            self.assertIsNotNone(deprecated)
            self.assertEqual(deprecated.status, "deprecated")

            app.registry.execute(
                "SkillArchive",
                {"name": "wetland-two", "reason": "Retire duplicate workflow"},
                app.settings,
                services=app.get_services(),
            )
            self.assertIsNone(app.skill_loader.get("wetland-two"))

            app.skill_loader.record_usage(
                "wetland-one",
                query="wetland methane water table",
                mode="test",
                session_id="sess-governance",
            )
            used = app.skill_loader.get("wetland-one")
            self.assertIsNotNone(used)
            self.assertGreaterEqual(used.usage_count, 1)

            governance = app.registry.execute(
                "SkillGovernanceReport",
                {"limit": 10, "stale_days": 0, "overlap_threshold": 0.45},
                app.settings,
                services=app.get_services(),
            )
            self.assertIn("archived", governance.content)
            self.assertTrue(governance.data["archived"])
            archived_slugs = [item["slug"] for item in governance.data["archived"]]
            self.assertIn("wetland-two", archived_slugs)

    def test_review_candidate_merges_into_existing_project_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            existing = app.settings.skill_dir / "wetland-methane-workflow.md"
            existing.write_text(
                "---\n"
                "name: wetland-methane-workflow\n"
                "description: Analyze wetland methane and water-table coupling.\n"
                "slug: wetland-methane-workflow\n"
                "triggers: [/wetland-methane-workflow]\n"
                "allowed-tools: [Read, Grep]\n"
                "context: inline\n"
                "---\n"
                "## When to use\n"
                "Use this skill for methane-water table interpretation tasks.\n",
                encoding="utf-8",
            )

            report = app.review_manager.review_run(
                session_id="sess-merge",
                prompt="分析湿地甲烷与水位关系",
                messages=[
                    ChatMessage(role="user", content="请分析湿地甲烷与水位关系"),
                    ChatMessage(role="assistant", content="已完成分析并形成可复用流程。"),
                ],
                tool_invocations=[{"tool": "Read", "arguments": {"path": "README.md"}}],
                final_text="甲烷通量与水位上升相关。",
                min_tool_calls=1,
                reviewer=lambda payload: {
                    "summary": "Found a reusable wetland workflow.",
                    "skill_candidates": [
                        {
                            "title": "Wetland methane workflow",
                            "description": "Use for methane-water table interpretation tasks.",
                            "when_to_use": "When comparing methane flux and water table observations.",
                            "steps": [
                                "Review methane and water table observations.",
                                "Summarize the coupling between them.",
                            ],
                            "allowed_tools": ["Read", "Grep"],
                            "trigger": "/wetland-methane-workflow",
                            "expected_outcome": "A concise interpretation of methane-water table coupling.",
                        }
                    ],
                },
            )
            self.assertIsNotNone(report)
            candidate = next(item for item in report.candidates if item.candidate_type == "skill")

            result = app.registry.execute(
                "ReviewApplySkill",
                {"candidate_id": candidate.candidate_id},
                app.settings,
                services=app.get_services(),
            )

            self.assertEqual(result.data["action"], "merged")
            merged_text = existing.read_text(encoding="utf-8")
            self.assertIn("Additional guidance from review", merged_text)


if __name__ == "__main__":
    unittest.main()
