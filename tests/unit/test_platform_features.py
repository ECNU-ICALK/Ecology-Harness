import json
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from ecology_harness.app import EcologyHarnessApp
from ecology_harness.config import HarnessSettings
from ecology_harness.runtime.messages import ChatMessage, ModelResponse
from ecology_harness.runtime.provider_router import RoutedProvider
from ecology_harness.server.api import build_chat_completion_payload
from ecology_harness.tools import ToolDefinition, ToolError, ToolResult


class _FakeHtmlResponse:
    def __init__(self, html: str, mime: str = "text/html"):
        self.html = html.encode("utf-8")
        self.headers = {"Content-Type": mime}

    def read(self, *_args, **_kwargs):
        return self.html

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        del exc_type, exc, tb
        return False


class _FakeProvider:
    def __init__(self, provider_name: str, should_fail: bool) -> None:
        self.provider_name = provider_name
        self.should_fail = should_fail
        self.name = provider_name

    def complete(self, messages, tools, settings):
        del messages, tools, settings
        if self.should_fail:
            raise RuntimeError("429 rate limit from %s" % self.provider_name)
        return ModelResponse(content="ok from %s" % self.provider_name, raw={})


class PlatformFeatureTests(unittest.TestCase):
    def _make_app(self, root: Path) -> EcologyHarnessApp:
        settings = HarnessSettings.from_workspace(root)
        settings.user_state_dir = root / ".user_state"
        return EcologyHarnessApp(settings)

    def test_provider_router_falls_back_to_next_provider(self) -> None:
        settings = HarnessSettings.from_workspace(".")
        settings.provider = "openai"
        settings.provider_fallbacks = ("anthropic",)
        router = RoutedProvider(
            settings=settings,
            factory=lambda name, current: _FakeProvider(name, should_fail=(current.provider == "openai")),
        )
        response = router.complete([ChatMessage(role="user", content="hello")], [], settings)
        self.assertEqual(response.content, "ok from anthropic")
        self.assertEqual(router.last_attempts[-1].provider, "anthropic")

    def test_session_index_stats_and_recap_are_generated(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("hello session\n", encoding="utf-8")
            app = self._make_app(root)
            app.initialize()

            app.run_prompt('/tool Read {"path":"README.md"}')
            sessions = app.list_sessions()

            self.assertTrue(sessions)
            self.assertTrue(sessions[0].title)
            self.assertTrue(sessions[0].recap)
            stats = app.session_stats()
            self.assertEqual(stats["session_count"], 1)
            self.assertTrue(stats["index"]["fts_enabled"] in {True, False})

    def test_session_index_handles_rewritten_query_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            app = self._make_app(root)
            app.initialize()

            app.run_prompt("请总结一下湿地甲烷通量和水位变化之间的关系")
            app.start_new_session()
            app.run_prompt("请分析这个项目里的相机陷阱照片")

            report = app.search_sessions("intent: analyze target: 湿地甲烷通量 水位 关系")

            self.assertTrue(report.hits)
            self.assertIn("湿地甲烷通量", report.hits[0].excerpt)

    def test_existing_sessions_are_rehydrated_into_index_on_startup(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("historic session\n", encoding="utf-8")
            app = self._make_app(root)
            app.initialize()
            app.run_prompt('/tool Read {"path":"README.md"}')

            restarted = self._make_app(root)
            restarted.initialize()
            stats = restarted.session_stats()

            self.assertEqual(stats["session_count"], 1)
            self.assertEqual(stats["index"]["session_count"], 1)
            sessions = restarted.list_sessions()
            self.assertTrue(sessions[0].title)
            self.assertTrue(sessions[0].recap)

    def test_session_index_can_be_queried_from_another_thread(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            app = self._make_app(root)
            app.initialize()
            app.run_prompt("请总结这个湿地甲烷项目")

            errors: list[str] = []

            def _worker() -> None:
                try:
                    report = app.session_index.search("湿地 甲烷")
                    self.assertTrue(report)
                    stats = app.session_stats()
                    self.assertIn("index", stats)
                except Exception as exc:  # pragma: no cover - asserted below
                    errors.append(str(exc))

            thread = threading.Thread(target=_worker, daemon=True)
            thread.start()
            thread.join(timeout=5)

            self.assertFalse(errors, errors[0] if errors else "")

    def test_session_save_survives_indexing_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("index safety\n", encoding="utf-8")
            app = self._make_app(root)
            app.initialize()

            with patch.object(app.session_index, "index_session", side_effect=RuntimeError("index offline")):
                app.run_prompt('/tool Read {"path":"README.md"}')

            latest = app.latest_session_path()
            self.assertTrue(latest.exists())
            payload = json.loads(latest.read_text(encoding="utf-8"))
            self.assertTrue(payload["messages"])
            audit_lines = app.settings.audit_log_file.read_text(encoding="utf-8").strip().splitlines()
            self.assertTrue(any("session_index_error" in line for line in audit_lines))

    def test_audit_appends_jsonl_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            app = self._make_app(root)
            app.initialize()

            app.audit("first", {"value": 1})
            app.audit("second", {"value": 2})

            lines = app.settings.audit_log_file.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 2)
            first = json.loads(lines[0])
            second = json.loads(lines[1])
            self.assertEqual(first["kind"], "first")
            self.assertEqual(second["kind"], "second")

    def test_checkpoints_can_be_listed_and_restored(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("checkpoint me\n", encoding="utf-8")
            app = self._make_app(root)
            app.initialize()

            app.run_prompt('/tool Read {"path":"README.md"}')
            listed = app.registry.execute("CheckpointList", {}, app.settings, services=app.get_services())
            self.assertTrue(listed.data["checkpoints"])
            checkpoint_id = listed.data["checkpoints"][0]["checkpoint_id"]
            restored = app.registry.execute(
                "CheckpointRestore",
                {"checkpoint_id": checkpoint_id},
                app.settings,
                services=app.get_services(),
            )
            self.assertIn("Restored checkpoint", restored.content)

    def test_profile_selection_changes_prompt_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            app = self._make_app(root)
            app.initialize()
            app.registry.execute(
                "ProfileSelect",
                {"name": "modeling"},
                app.settings,
                services=app.get_services(),
            )
            prompt = app.build_system_prompt(prompt_text="比较 APSIM 和 AquaCrop")
            self.assertIn("<work-style-profile>", prompt)
            self.assertIn("Modeling and Simulation", prompt)

    def test_doctor_report_and_workspace_bootstrap_tools(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            app = self._make_app(root)
            app.initialize()

            status = app.registry.execute(
                "WorkspaceBootstrapStatus",
                {},
                app.settings,
                services=app.get_services(),
            )
            self.assertEqual(status.data["present_count"], 0)

            created = app.registry.execute(
                "WorkspaceBootstrapInit",
                {},
                app.settings,
                services=app.get_services(),
            )
            self.assertIn("AGENTS.md", created.data["created"])
            self.assertTrue((root / "AGENTS.md").exists())
            self.assertTrue((root / "HEARTBEAT.md").exists())

            report = app.registry.execute(
                "DoctorReport",
                {"probe_mcp": False},
                app.settings,
                services=app.get_services(),
            )
            self.assertEqual(report.data["bootstrap"]["present_count"], 4)
            self.assertIn("workspace", report.content)
            self.assertIn("suggestions", report.data)

    def test_doctor_report_includes_actionable_suggestions_when_workspace_is_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            app = self._make_app(root)
            app.initialize()

            report = app.registry.execute(
                "DoctorReport",
                {"probe_mcp": False},
                app.settings,
                services=app.get_services(),
            )

            suggestions = report.data["suggestions"]
            self.assertTrue(suggestions)
            self.assertTrue(any(item["command"] == "eh setup" for item in suggestions))

    def test_runtime_status_reports_context_pressure_and_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            app = self._make_app(root)
            app.initialize()
            app.task_store.create("Check inputs")

            result = app.registry.execute(
                "RuntimeStatus",
                {},
                app.settings,
                services=app.get_services(
                    conversation=[ChatMessage(role="user", content="hello world " * 30)]
                ),
            )

            self.assertIn("context:", result.content)
            self.assertEqual(result.data["tasks"]["total"], 1)
            self.assertIn("pressure_ratio", result.data["context_pressure"])

    def test_analytics_summary_reports_recent_queries_and_skill_usage(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("analytics read\n", encoding="utf-8")
            app = self._make_app(root)
            app.initialize()

            app.run_prompt('/tool Read {"path":"README.md"}')
            app.run_prompt("/recent-research-scan wetland methane monitoring")

            result = app.registry.execute(
                "AnalyticsSummary",
                {"limit": 3},
                app.settings,
                services=app.get_services(),
            )

            self.assertIn("recent_queries:", result.content)
            self.assertTrue(result.data["recent_queries"])
            self.assertIn("skills", result.data)

    def test_execute_code_can_call_existing_tools(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("hello from execute code\n", encoding="utf-8")
            app = self._make_app(root)
            app.initialize()

            result = app.registry.execute(
                "ExecuteCode",
                {
                    "code": 'payload = call_tool("Read", {"path": "README.md"})\nresult = payload["content"]',
                    "result_var": "result",
                },
                app.settings,
                services=app.get_services(),
            )
            payload = json.loads(result.content)
            self.assertEqual(payload["tool_calls"], 1)
            self.assertIn("hello from execute code", payload["result"])

    def test_automation_jobs_can_run_due(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("automation read\n", encoding="utf-8")
            app = self._make_app(root)
            app.initialize()

            created = app.registry.execute(
                "AutomationCreate",
                {"name": "Read job", "prompt": '/tool Read {"path":"README.md"}', "schedule": "daily"},
                app.settings,
                services=app.get_services(),
            )
            job_id = created.data["job_id"]
            payload = json.loads(app.automation_manager.path.read_text(encoding="utf-8"))
            payload[0]["next_run_at"] = "2000-01-01T00:00:00Z"
            app.automation_manager.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

            due = app.registry.execute("AutomationRunDue", {}, app.settings, services=app.get_services())
            self.assertIn(job_id, due.content)

    def test_automation_run_due_isolates_failures_and_records_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            app = self._make_app(root)
            app.initialize()
            first = app.automation_manager.create_job("Broken job", "bad", schedule="daily")
            second = app.automation_manager.create_job("Healthy job", "good", schedule="daily")

            payload = json.loads(app.automation_manager.path.read_text(encoding="utf-8"))
            for item in payload:
                item["next_run_at"] = "2000-01-01T00:00:00Z"
            app.automation_manager.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

            def _runner(job):
                if job.job_id == first.job_id:
                    raise RuntimeError("boom")
                return {"final_text": "ok"}

            results = app.automation_manager.run_due(_runner)

            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]["status"], "failed")
            self.assertEqual(results[1]["status"], "succeeded")
            stored = {item["job_id"]: item for item in json.loads(app.automation_manager.path.read_text(encoding="utf-8"))}
            self.assertEqual(stored[first.job_id]["last_status"], "failed")
            self.assertIn("boom", stored[first.job_id]["last_error"])
            self.assertEqual(stored[second.job_id]["last_status"], "succeeded")

    def test_heartbeat_status_and_run_use_workspace_heartbeat_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("heartbeat file\n", encoding="utf-8")
            (root / "HEARTBEAT.md").write_text('/tool Read {"path":"README.md"}\n', encoding="utf-8")
            app = self._make_app(root)
            app.initialize()

            status = app.registry.execute("HeartbeatStatus", {}, app.settings, services=app.get_services())
            self.assertTrue(status.data["enabled"])
            self.assertTrue(status.data["due"])

            result = app.registry.execute("HeartbeatRun", {}, app.settings, services=app.get_services())
            self.assertIn("Heartbeat ran", result.content)
            self.assertIn("heartbeat file", result.data["final_text"])
            self.assertFalse(result.data["noop"])

    def test_browser_fetch_extracts_title_and_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            app = self._make_app(root)
            app.initialize()
            html = "<html><head><title>Wetland Page</title></head><body><a href='https://example.com/a'>A</a><p>Hello wetland</p></body></html>"
            with patch("ecology_harness.tools.builtin.browser_tools.request.urlopen", return_value=_FakeHtmlResponse(html)):
                result = app.registry.execute(
                    "BrowserFetch",
                    {"url": "https://example.com"},
                    app.settings,
                    services=app.get_services(),
                )
            self.assertIn("Wetland Page", result.content)
            self.assertIn("https://example.com/a", result.content)
            self.assertEqual(result.data["trust_level"], "untrusted-external")

    def test_browser_tools_reject_non_http_urls(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            app = self._make_app(root)
            app.initialize()

            with self.assertRaises(ToolError):
                app.registry.execute(
                    "BrowserFetch",
                    {"url": "file:///etc/passwd"},
                    app.settings,
                    services=app.get_services(),
                )

    def test_remote_mcp_probe_reports_reachable_stdio_server(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            app = self._make_app(root)
            project_mcp_dir = app.settings.mcp_dir
            project_mcp_dir.mkdir(parents=True, exist_ok=True)
            (project_mcp_dir / "remote-probe.json").write_text(
                json.dumps(
                    {
                        "servers": [
                            {
                                "name": "probe-stdio",
                                "transport": "stdio",
                                "description": "Probe candidate",
                                "default_enabled": True,
                                "command": "python3",
                                "tools": [{"name": "ping", "description": "Ping", "input_schema": {"type": "object", "properties": {}}}],
                            }
                        ]
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            app.initialize()

            result = app.registry.execute(
                "ProbeMcpServerTool",
                {"server": "probe-stdio"},
                app.settings,
                services=app.get_services(),
            )

            self.assertEqual(result.data["status"], "reachable")
            listed = app.registry.execute(
                "ListMcpServersTool",
                {"probe": True},
                app.settings,
                services=app.get_services(),
            )
            rows = {item["server_name"]: item for item in listed.data["servers"]}
            self.assertEqual(rows["probe-stdio"]["status"], "reachable")
            self.assertFalse(rows["probe-stdio"]["runtime_invokable"])
            self.assertFalse(rows["probe-stdio"]["bridge_registered"])
            self.assertIsNone(app.registry.get("mcp__probe-stdio__ping"))

    def test_prompt_builder_excludes_heartbeat_in_normal_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "STANDING_ORDERS.md").write_text("Always record uncertainty and study scale.\n", encoding="utf-8")
            (root / "HEARTBEAT.md").write_text("Check recurring wetland monitoring tasks.\n", encoding="utf-8")
            app = self._make_app(root)
            app.initialize()

            prompt = app.build_system_prompt(prompt_text="湿地监测任务")

            self.assertIn("<workspace-bootstrap-context>", prompt)
            self.assertIn("STANDING_ORDERS.md", prompt)
            self.assertIn("Always record uncertainty", prompt)
            self.assertNotIn("HEARTBEAT.md", prompt)

            app.runtime_mode = "heartbeat"
            heartbeat_prompt = app.build_system_prompt(prompt_text="执行 heartbeat")
            self.assertIn("HEARTBEAT.md", heartbeat_prompt)

    def test_plugin_hooks_cover_session_and_run_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("hook me\n", encoding="utf-8")
            app = self._make_app(root)
            app.initialize()

            plugin_root = app.settings.plugin_dir / "hooked-plugin"
            hook_dir = plugin_root / "hooks"
            manifest_dir = plugin_root / ".ecology-plugin"
            hook_dir.mkdir(parents=True, exist_ok=True)
            manifest_dir.mkdir(parents=True, exist_ok=True)
            hook_script = hook_dir / "log.sh"
            hook_script.write_text(
                "#!/bin/bash\nprintf '%s\\n' \"$EH_HOOK_EVENT\" >> \"$EH_WORKSPACE_ROOT/hook-events.log\"\n",
                encoding="utf-8",
            )
            hook_script.chmod(0o755)
            (manifest_dir / "plugin.json").write_text(
                json.dumps(
                    {
                        "name": "Hooked Plugin",
                        "version": "0.1.0",
                        "hooks": {
                            "SessionStart": ["hooks/log.sh"],
                            "PreRun": ["hooks/log.sh"],
                            "PostRun": ["hooks/log.sh"],
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            app.start_new_session()
            app.run_prompt('/tool Read {"path":"README.md"}')

            events = (root / "hook-events.log").read_text(encoding="utf-8")
            self.assertIn("SessionStart", events)
            self.assertIn("PreRun", events)
            self.assertIn("PostRun", events)

    def test_skill_quarantine_and_approve_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            app = self._make_app(root)
            app.initialize()
            skill_path = app.settings.skill_dir / "local-test.md"
            skill_path.write_text(
                "---\nname: Local Test\ntriggers: [/local-test]\n---\nUse this local test skill.\n",
                encoding="utf-8",
            )
            self.assertIsNotNone(app.skill_loader.get("local-test"))
            quarantined = app.registry.execute(
                "SkillQuarantine",
                {"name": "local-test", "reason": "suspicious"},
                app.settings,
                services=app.get_services(),
            )
            self.assertIn("Quarantined skill", quarantined.content)
            self.assertIsNone(app.skill_loader.get("local-test"))
            approved = app.registry.execute(
                "SkillApprove",
                {"name": "local-test"},
                app.settings,
                services=app.get_services(),
            )
            self.assertIn("Approved skill", approved.content)
            self.assertIsNotNone(app.skill_loader.get("local-test"))

    def test_skill_install_repo_imports_local_skill_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            app = self._make_app(root)
            app.initialize()

            source_repo = root / "source-repo"
            (source_repo / "skills" / "demo-skill").mkdir(parents=True, exist_ok=True)
            (source_repo / "skills" / "demo-skill" / "SKILL.md").write_text(
                "---\nname: Demo Skill\ntriggers: [/demo-skill]\n---\nImported skill bundle.\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "init"], cwd=str(source_repo), check=True, capture_output=True, text=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(source_repo), check=True)
            subprocess.run(["git", "config", "user.name", "Tester"], cwd=str(source_repo), check=True)
            subprocess.run(["git", "add", "."], cwd=str(source_repo), check=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=str(source_repo), check=True, capture_output=True, text=True)

            result = app.registry.execute(
                "SkillInstallRepo",
                {"repo_url": str(source_repo), "scope": "user", "subdir": "skills"},
                app.settings,
                services=app.get_services(),
            )
            self.assertEqual(len(result.data["imported"]), 1)
            self.assertIsNotNone(app.skill_loader.get("demo-skill"))

    def test_api_server_payload_builder_returns_openai_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("server helper\n", encoding="utf-8")
            app = self._make_app(root)
            app.initialize()
            payload = build_chat_completion_payload(
                app,
                {"messages": [{"role": "user", "content": '/tool Read {"path":"README.md"}'}]},
            )
            self.assertEqual(payload["object"], "chat.completion")
            self.assertIn("server helper", payload["choices"][0]["message"]["content"])


if __name__ == "__main__":
    unittest.main()
