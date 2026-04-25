import tempfile
import unittest
import json
from pathlib import Path

from ecology_harness.app import EcologyHarnessApp
from ecology_harness.config import HarnessSettings
from ecology_harness.runtime.messages import ChatMessage


class AgentLoopTests(unittest.TestCase):
    def test_mock_provider_executes_tool_through_agent_loop(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("hello harness\n", encoding="utf-8")

            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            result = app.run_prompt('/tool Read {"path":"README.md"}')

            self.assertIn("hello harness", result.final_text)
            self.assertEqual(result.steps, 2)
            session_path = root / ".ecology_harness" / "sessions" / "latest.json"
            self.assertTrue(session_path.exists())
            payload = json.loads(session_path.read_text(encoding="utf-8"))
            self.assertIn("session_id", payload)
            self.assertIn("messages", payload)

    def test_agent_loop_emits_trace_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("hello trace\n", encoding="utf-8")

            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            seen = []
            result = app.run_prompt(
                '/tool Read {"path":"README.md"}',
                event_handler=lambda event: seen.append(event.kind),
            )

            self.assertIn("hello trace", result.final_text)
            self.assertIn("run_started", seen)
            self.assertIn("step_started", seen)
            self.assertIn("assistant_message", seen)
            self.assertIn("tool_call", seen)
            self.assertIn("tool_result", seen)
            self.assertIn("run_completed", seen)
            self.assertTrue(result.events)
            tool_result = next(item for item in result.events if item.kind == "tool_result")
            self.assertIn("duration_ms", tool_result.payload)
            self.assertIn("output_chars", tool_result.payload)

    def test_agent_tool_runs_subagent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            result = app.run_prompt('/tool Agent {"prompt":"/tool TaskCreate {\\"title\\":\\"child task\\"}"}')

            self.assertIn("Created task #1", result.final_text)

    def test_run_prompt_supports_conversation_continuation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            first = app.run_prompt("hello there")
            second = app.run_prompt("follow up", conversation=first.messages)

            self.assertGreater(len(second.messages), len(first.messages))
            self.assertEqual(second.messages[-1].role, "assistant")

    def test_run_prompt_supports_unlimited_loop_setting(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("hello unlimited\n", encoding="utf-8")

            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            settings.max_agent_loops = 0
            app = EcologyHarnessApp(settings)
            app.initialize()

            result = app.run_prompt('/tool Read {"path":"README.md"}')

            self.assertIn("hello unlimited", result.final_text)
            self.assertEqual(result.steps, 2)

    def test_background_agent_can_receive_follow_up_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            spawn = app.registry.execute(
                "Agent",
                {
                    "prompt": '/tool Bash {"command":"sleep 0.2"}',
                    "name": "worker",
                    "wait": False,
                },
                app.settings,
                services=app.get_services(),
            )
            task_id = spawn.data["task_id"]

            queued = app.registry.execute(
                "SendMessage",
                {"to": "worker", "message": '/tool TaskCreate {"subject":"followup"}'},
                app.settings,
                services=app.get_services(),
            )
            self.assertIn("queued", queued.content.lower())

            app.subagent_manager.wait(task_id, timeout=2)
            checked = app.registry.execute(
                "CheckAgentResult",
                {"task_id": task_id},
                app.settings,
                services=app.get_services(),
            )
            self.assertIn("Created task #1", checked.content)

    def test_list_agent_types_includes_builtin_types(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            result = app.registry.execute(
                "ListAgentTypes",
                {},
                app.settings,
                services=app.get_services(),
            )

            self.assertIn("reviewer", result.content)
            self.assertIn("planner", result.content)
            self.assertIn("coordinator", result.content)

    def test_subagent_captures_shared_context_and_dependency_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            settings = HarnessSettings.from_workspace(root)
            settings.user_state_dir = root / ".user_state"
            app = EcologyHarnessApp(settings)
            app.initialize()

            dependency = app.subagent_manager.spawn(
                prompt='/tool Bash {"command":"sleep 0.2"}',
                name="dep",
            )
            child = app.subagent_manager.spawn(
                prompt='/tool TaskCreate {"title":"after dependency"}',
                name="child",
                depends_on=[dependency.id],
                coordination_context="Return only the outcome needed by the parent.",
                expected_output="A short completion update.",
                ownership="Own the dependency follow-up task only.",
                parent_conversation=[
                    ChatMessage(role="user", content="Plan the next ecological data pipeline step."),
                    ChatMessage(role="assistant", content="I will wait for the dependency and then create the follow-up task."),
                ],
            )

            self.assertIn("Depends on: %s" % dependency.id, child.shared_context_summary)
            self.assertIn("Coordinator notes", child.shared_context_summary)
            self.assertTrue(child.task_record_id)

            app.subagent_manager.wait(dependency.id, timeout=2)
            app.subagent_manager.wait(child.id, timeout=2)

            finished = app.subagent_manager.get_task(child.id)
            self.assertIsNotNone(finished)
            self.assertEqual(finished.status, "completed")
            self.assertIn("Created task #1", finished.result)


if __name__ == "__main__":
    unittest.main()
