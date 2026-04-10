from __future__ import annotations

from dataclasses import replace
from datetime import datetime
import json
from pathlib import Path

from ecology_harness.agents import SubAgentManager
from ecology_harness.config import HarnessSettings
from ecology_harness.evaluation import BenchmarkRunner, TrajectoryStore
from ecology_harness.evolution import ReviewManager
from ecology_harness.evolution.review import REVIEW_SYSTEM_PROMPT
from ecology_harness.memory import MemoryManager
from ecology_harness.memory.providers import (
    BuiltinMemoryProvider,
    MarkdownProfileProvider,
    MemoryProviderManager,
)
from ecology_harness.mcp import McpServerRegistry
from ecology_harness.permissions import PermissionPolicy
from ecology_harness.plugins import PluginManager
from ecology_harness.runtime import AgentLoop
from ecology_harness.runtime import ChatMessage
from ecology_harness.runtime.checkpoints import CheckpointManager
from ecology_harness.runtime.prompt_builder import PromptBuilder
from ecology_harness.runtime.providers import ProviderError, create_provider
from ecology_harness.runtime.provider_router import resolve_slot_settings
from ecology_harness.runtime.session_index import SessionIndex
from ecology_harness.runtime.session_search import SessionSearchEngine
from ecology_harness.runtime.session_store import SessionForkRecord, SessionStore
from ecology_harness.sandbox import SandboxPolicy
from ecology_harness.skills import SkillLoader, execute_skill
from ecology_harness.tasks import TaskStore
from ecology_harness.tools import ToolRegistry
from ecology_harness.tools.builtin import register_builtin_tools
from ecology_harness.profiles import ProfileManager
from ecology_harness.automation import AutomationManager


class EcologyHarnessApp:
    """Application wiring for the harness runtime."""

    def __init__(self, settings: HarnessSettings) -> None:
        self.settings = settings
        self.registry = ToolRegistry()
        self.memory_manager: MemoryManager | None = None
        self.memory_provider_manager: MemoryProviderManager | None = None
        self.skill_loader: SkillLoader | None = None
        self.plugin_manager: PluginManager | None = None
        self.task_store: TaskStore | None = None
        self.permission_policy = PermissionPolicy()
        self.prompt_builder = PromptBuilder()
        self.subagent_manager: SubAgentManager | None = None
        self.mcp_registry: McpServerRegistry | None = None
        self.sandbox: SandboxPolicy | None = None
        self.session_store: SessionStore | None = None
        self.session_index: SessionIndex | None = None
        self.session_search_engine: SessionSearchEngine | None = None
        self.review_manager: ReviewManager | None = None
        self.trajectory_store: TrajectoryStore | None = None
        self.benchmark_runner: BenchmarkRunner | None = None
        self.checkpoint_manager: CheckpointManager | None = None
        self.profile_manager: ProfileManager | None = None
        self.automation_manager: AutomationManager | None = None
        self._active_session_id = ""
        self._active_session_created_at = ""
        self._active_fork: SessionForkRecord | None = None
        self.runtime_mode = "default"
        self._initialized = False

    def initialize(self) -> None:
        if self._initialized:
            return
        self.settings.ensure_directories()
        self.settings.user_memory_dir.mkdir(parents=True, exist_ok=True)
        self.settings.user_skill_dir.mkdir(parents=True, exist_ok=True)
        self.settings.user_plugin_dir.mkdir(parents=True, exist_ok=True)
        self.settings.user_mcp_dir.mkdir(parents=True, exist_ok=True)
        self.settings.user_agent_dir.mkdir(parents=True, exist_ok=True)
        self.memory_manager = MemoryManager(
            user_root=self.settings.user_memory_dir,
            project_root=self.settings.memory_dir,
            max_index_lines=self.settings.memory_index_max_lines,
            max_index_bytes=self.settings.memory_index_max_bytes,
        )
        builtin_skill_dir = Path(__file__).resolve().parent / "skills" / "builtin"
        self.skill_loader = SkillLoader(
            builtin_dir=builtin_skill_dir,
            user_dir=self.settings.user_skill_dir,
            project_dir=self.settings.skill_dir,
            history_turns=self.settings.skill_retrieval_history_turns,
        )
        builtin_plugin_dir = Path(__file__).resolve().parent / "plugins" / "builtin"
        self.plugin_manager = PluginManager(
            builtin_dir=builtin_plugin_dir,
            user_dir=self.settings.user_plugin_dir,
            project_dir=self.settings.plugin_dir,
        )
        builtin_mcp_dir = Path(__file__).resolve().parent / "mcp" / "builtin"
        self.mcp_registry = McpServerRegistry(
            self,
            builtin_dir=builtin_mcp_dir,
            user_dir=self.settings.user_mcp_dir,
            project_dir=self.settings.mcp_dir,
            history_turns=self.settings.mcp_retrieval_history_turns,
        )
        self.task_store = TaskStore(self.settings.task_file)
        self.subagent_manager = SubAgentManager(self)
        self.sandbox = SandboxPolicy(self.settings)
        self.session_store = SessionStore(self.settings.session_dir)
        self.session_index = SessionIndex(self.settings.session_index_path)
        self.session_search_engine = SessionSearchEngine(
            self.session_store,
            history_turns=self.settings.session_retrieval_history_turns,
            max_messages=self.settings.session_search_max_messages,
            session_index=self.session_index,
        )
        self._rehydrate_session_index()
        self.review_manager = ReviewManager(
            review_dir=self.settings.review_dir,
            candidate_dir=self.settings.review_candidate_dir,
        )
        self.trajectory_store = TrajectoryStore(self.settings.trajectory_dir)
        self.benchmark_runner = BenchmarkRunner(
            self.trajectory_store,
            output_dir=self.settings.benchmark_dir,
        )
        self.checkpoint_manager = CheckpointManager(self.settings.checkpoint_dir)
        self.profile_manager = ProfileManager(self.settings.profile_dir, active_profile=self.settings.active_profile)
        self.settings.active_profile = self.profile_manager.get_active().name
        self.automation_manager = AutomationManager(self.settings.automation_dir)
        project_profile = MarkdownProfileProvider(
            name="project-profile",
            path=self.settings.profile_dir / "project-profile.md",
            title="Project Profile",
            description="Stable background about the active ecological project, study system, or workspace.",
        )
        research_profile = MarkdownProfileProvider(
            name="research-profile",
            path=self.settings.user_state_dir / "profiles" / "research-profile.md",
            title="Research Profile",
            description="Long-lived user research preferences, modeling habits, and favored data sources.",
        )
        self.memory_provider_manager = MemoryProviderManager(
            providers=[
                BuiltinMemoryProvider(self.memory_manager),
                project_profile,
                research_profile,
            ],
            history_turns=self.settings.skill_retrieval_history_turns,
        )
        register_builtin_tools(self.registry)
        self.mcp_registry.register_dynamic_tools(self.registry)
        self._initialized = True
        self.start_new_session()

    def build_system_prompt(
        self,
        settings: HarnessSettings | None = None,
        prompt_text: str = "",
        conversation: list[ChatMessage] | None = None,
    ) -> str:
        self._ensure_initialized()
        active_settings = settings or self.settings
        skill_report = self.skill_loader.select_for_prompt(  # type: ignore[union-attr]
            query=prompt_text,
            conversation=conversation,
            limit=active_settings.skill_prompt_top_k,
        )
        skill_index = [item.skill.to_index_dict() for item in skill_report.hits]
        agent_index = [
            item.to_index_dict() for item in self.subagent_manager.list_agent_definitions()  # type: ignore[union-attr]
        ]
        plugin_index = [
            item.to_index_dict() for item in self.plugin_manager.list_enabled_plugins()  # type: ignore[union-attr]
        ]
        mcp_report = self.mcp_registry.select_for_prompt(  # type: ignore[union-attr]
            query=prompt_text,
            conversation=conversation,
            limit=active_settings.mcp_prompt_top_k,
        )
        mcp_index = self.mcp_registry.prompt_index_from_hits(mcp_report.hits)  # type: ignore[union-attr]
        memory_context = self.memory_manager.get_memory_context(  # type: ignore[union-attr]
            query=prompt_text,
            conversation=conversation,
            include_guidance=True,
        )
        self.memory_provider_manager.queue_prefetch(  # type: ignore[union-attr]
            query=prompt_text,
            conversation=conversation,
        )
        provider_context = self.memory_provider_manager.build_context(  # type: ignore[union-attr]
            query=prompt_text,
            conversation=conversation,
            limit=active_settings.memory_provider_prompt_top_k,
        )
        profile_context = self.profile_manager.build_context() if self.profile_manager is not None else ""
        if profile_context:
            provider_context = (
                "%s\n\n%s" % (provider_context, profile_context)
                if provider_context
                else profile_context
            )
        session_report = self.session_search_engine.select_for_prompt(  # type: ignore[union-attr]
            query=prompt_text,
            conversation=conversation,
            limit=active_settings.session_prompt_top_k,
            exclude_session_id=self._active_session_id,
        )
        return self.prompt_builder.build(
            active_settings,
            memory_context=memory_context,
            provider_context=provider_context,
            skill_index=skill_index,
            skill_retrieval=skill_report.to_prompt_dict(),
            agent_index=agent_index,
            plugin_index=plugin_index,
            mcp_index=mcp_index,
            mcp_retrieval=mcp_report.to_prompt_dict(),
            session_index=[item.to_index_dict() for item in session_report.hits],
            session_retrieval=session_report.to_prompt_dict(),
            active_profile=(self.profile_manager.get_active().to_dict() if self.profile_manager is not None else None),
            context_pressure={
                "warn_ratio": active_settings.context_pressure_warn_ratio,
                "critical_ratio": active_settings.context_pressure_critical_ratio,
            },
            runtime_mode=self.runtime_mode,
        )

    def select_available_tools(
        self,
        prompt_text: str,
        conversation: list[ChatMessage] | None = None,
        allowed_tools: set[str] | None = None,
        settings: HarnessSettings | None = None,
    ):
        self._ensure_initialized()
        active_settings = settings or self.settings
        tools = self.registry.list_tools()
        if allowed_tools:
            tools = [item for item in tools if item.name in allowed_tools]

        relevant_dynamic_mcp = self.mcp_registry.relevant_dynamic_tool_names(  # type: ignore[union-attr]
            query=prompt_text,
            conversation=conversation,
            limit=active_settings.mcp_prompt_top_k,
        )
        selected = []
        normalized_prompt = (prompt_text or "").lower()
        for tool in tools:
            if not tool.name.startswith("mcp__"):
                selected.append(tool)
                continue
            if allowed_tools and tool.name in allowed_tools:
                selected.append(tool)
                continue
            if tool.name in relevant_dynamic_mcp or tool.name.lower() in normalized_prompt:
                selected.append(tool)
        return selected

    def create_agent_loop(
        self,
        provider_name: str = "",
        allowed_tools: set[str] | None = None,
        settings: HarnessSettings | None = None,
    ) -> AgentLoop:
        self._ensure_initialized()
        active_settings = settings or self.settings
        provider = create_provider(provider_name or active_settings.provider, settings=active_settings)
        return AgentLoop(self, provider, allowed_tools=allowed_tools)

    def run_prompt(
        self,
        prompt: str,
        provider_name: str = "",
        allowed_tools: set[str] | None = None,
        settings: HarnessSettings | None = None,
        event_handler=None,
        conversation: list[ChatMessage] | None = None,
        attachment_paths: list[str] | None = None,
    ):
        self._ensure_initialized()
        active_settings = settings or self.settings
        self.run_plugin_hooks(
            "PreRun",
            {
                "prompt": prompt,
                "provider": provider_name or active_settings.provider,
                "session_id": self._active_session_id,
                "attachment_paths": list(attachment_paths or []),
                "runtime_mode": self.runtime_mode,
            },
            settings=active_settings,
        )
        try:
            skill = self.skill_loader.find_by_trigger(prompt)  # type: ignore[union-attr]
            if skill is not None:
                trigger = prompt.strip().split(" ", 1)[0]
                args = prompt.strip()[len(trigger) :].strip()
                self.skill_loader.record_usage(  # type: ignore[union-attr]
                    skill,
                    query=prompt,
                    mode="trigger",
                    session_id=self._active_session_id,
                )
                result = execute_skill(
                    self,
                    skill,
                    args,
                    depth=0,
                    event_handler=event_handler,
                    conversation=conversation,
                    attachment_paths=attachment_paths,
                )
                if getattr(result, "messages", None):
                    compactions = getattr(result, "compactions", [])
                    self.save_session(
                        result.messages,
                        compaction=compactions[-1] if compactions else None,
                    )
                    self._post_run_artifacts(
                        prompt=prompt,
                        result=result,
                        attachment_paths=attachment_paths,
                    )
                self.run_plugin_hooks(
                    "PostRun",
                    {
                        "prompt": prompt,
                        "final_text": getattr(result, "final_text", ""),
                        "steps": getattr(result, "steps", 0),
                        "tool_count": len(getattr(result, "tool_invocations", [])),
                        "session_id": self._active_session_id,
                    },
                    settings=active_settings,
                )
                return result
            runner = self.create_agent_loop(
                provider_name,
                allowed_tools=allowed_tools,
                settings=active_settings,
            )
            result = runner.run(
                prompt=prompt,
                settings=active_settings,
                system_prompt=self.build_system_prompt(
                    settings=active_settings,
                    prompt_text=prompt,
                    conversation=conversation,
                ),
                conversation=conversation,
                attachment_paths=attachment_paths,
                event_handler=event_handler,
            )
            self.save_session(
                result.messages,
                compaction=result.compactions[-1] if result.compactions else None,
            )
            self._post_run_artifacts(
                prompt=prompt,
                result=result,
                attachment_paths=attachment_paths,
            )
            self.run_plugin_hooks(
                "PostRun",
                {
                    "prompt": prompt,
                    "final_text": result.final_text,
                    "steps": result.steps,
                    "tool_count": len(result.tool_invocations),
                    "session_id": self._active_session_id,
                },
                settings=active_settings,
            )
            return result
        except Exception as exc:
            self.run_plugin_hooks(
                "OnError",
                {
                    "stage": "run_prompt",
                    "prompt": prompt,
                    "session_id": self._active_session_id,
                    "error": str(exc),
                },
                settings=active_settings,
            )
            raise

    def get_services(self, **extra):
        self._ensure_initialized()
        services = {
            "app": self,
            "memory_manager": self.memory_manager,
            "memory_provider_manager": self.memory_provider_manager,
            "skill_loader": self.skill_loader,
            "plugin_manager": self.plugin_manager,
            "task_store": self.task_store,
            "subagent_manager": self.subagent_manager,
            "mcp_registry": self.mcp_registry,
            "sandbox": self.sandbox,
            "tool_registry": self.registry,
            "session_store": self.session_store,
            "session_search_engine": self.session_search_engine,
            "session_index": self.session_index,
            "review_manager": self.review_manager,
            "trajectory_store": self.trajectory_store,
            "benchmark_runner": self.benchmark_runner,
            "checkpoint_manager": self.checkpoint_manager,
            "profile_manager": self.profile_manager,
            "automation_manager": self.automation_manager,
        }
        services.update(extra)
        return services

    def audit(self, kind: str, payload: dict) -> None:
        entry = {
            "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "kind": kind,
            "payload": payload,
        }
        with self.settings.audit_log_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def save_session(self, messages, compaction: dict | None = None) -> None:
        self._ensure_initialized()
        if not self._active_session_id or not self._active_session_created_at:
            self.start_new_session()
        title = self._derive_session_title(messages)
        recap = self._derive_session_recap(messages, compaction=compaction)
        managed = self.session_store.save(  # type: ignore[union-attr]
            session_id=self._active_session_id,
            created_at=self._active_session_created_at,
            messages=messages,
            title=title,
            recap=recap,
            compaction=compaction,
            fork=self._active_fork.to_dict() if self._active_fork is not None else None,
        )
        if self.session_index is not None:
            self.session_index.index_session(managed)

    def load_session(self, name: str = "latest") -> list[ChatMessage]:
        self._ensure_initialized()
        managed = self.session_store.load(name)  # type: ignore[union-attr]
        self._active_session_id = managed.session_id
        self._active_session_created_at = managed.created_at
        self._active_fork = managed.fork
        self.run_plugin_hooks(
            "SessionResume",
            {
                "session_id": managed.session_id,
                "created_at": managed.created_at,
                "title": managed.title,
                "message_count": len(managed.messages),
            },
        )
        return managed.messages

    def latest_session_path(self) -> Path:
        self._ensure_initialized()
        return self.session_store.latest_path()  # type: ignore[union-attr]

    def list_sessions(self):
        self._ensure_initialized()
        return self.session_store.list_sessions()  # type: ignore[union-attr]

    def session_stats(self) -> dict[str, object]:
        self._ensure_initialized()
        store_stats = self.session_store.stats()  # type: ignore[union-attr]
        if self.session_index is not None:
            store_stats["index"] = self.session_index.stats()
        return store_stats

    def search_sessions(
        self,
        query: str,
        conversation: list[ChatMessage] | None = None,
        limit: int | None = None,
    ):
        self._ensure_initialized()
        effective_limit = limit if limit is not None else self.settings.session_search_default_k
        return self.session_search_engine.search(  # type: ignore[union-attr]
            query=query,
            conversation=conversation,
            limit=effective_limit,
            exclude_session_id=self._active_session_id,
        )

    def list_reviews(self):
        self._ensure_initialized()
        return self.review_manager.list_reports()  # type: ignore[union-attr]

    def start_new_session(
        self,
        fork_from_session_id: str = "",
        branch_name: str = "",
    ) -> None:
        if self.session_store is None:
            raise RuntimeError("EcologyHarnessApp must be initialized before starting a session.")
        fork = None
        if fork_from_session_id:
            fork = SessionForkRecord(
                parent_session_id=fork_from_session_id,
                branch_name=branch_name,
            )
        managed = self.session_store.create_empty(fork=fork)
        self._active_session_id = managed.session_id
        self._active_session_created_at = managed.created_at
        self._active_fork = fork
        self.run_plugin_hooks(
            "SessionStart",
            {
                "session_id": managed.session_id,
                "created_at": managed.created_at,
                "fork": fork.to_dict() if fork is not None else None,
            },
        )

    def run_plugin_hooks(
        self,
        event_name: str,
        payload: dict,
        settings: HarnessSettings | None = None,
    ) -> list[dict]:
        if self.plugin_manager is None:
            return []
        active_settings = settings or self.settings
        return self.plugin_manager.run_hooks(
            event_name,
            payload,
            workspace_root=active_settings.workspace_root,
            timeout_sec=active_settings.command_timeout_sec,
        )

    def _ensure_initialized(self) -> None:
        if not self._initialized:
            raise RuntimeError("EcologyHarnessApp must be initialized before use.")

    def _rehydrate_session_index(self) -> None:
        if self.session_store is None or self.session_index is None:
            return
        for summary in self.session_store.list_sessions():
            try:
                managed = self.session_store.load(summary.session_id)
            except Exception:
                continue
            changed = False
            if not managed.title:
                managed.title = self._derive_session_title(managed.messages)
                changed = True
            if not managed.recap:
                compaction = managed.compaction.to_dict() if managed.compaction is not None else None
                managed.recap = self._derive_session_recap(managed.messages, compaction=compaction)
                changed = True
            if changed:
                payload = json.dumps(managed.to_dict(), indent=2, ensure_ascii=False)
                self.session_store.session_path(managed.session_id).write_text(payload, encoding="utf-8")
                if self.session_store.latest_path().exists():
                    try:
                        latest = self.session_store.load("latest")
                    except Exception:
                        latest = None
                    if latest is not None and latest.session_id == managed.session_id:
                        self.session_store.latest_path().write_text(payload, encoding="utf-8")
            self.session_index.index_session(managed)

    def _post_run_artifacts(
        self,
        prompt: str,
        result,
        attachment_paths: list[str] | None = None,
    ) -> None:
        self._ensure_initialized()
        if self.settings.trajectory_export_enabled and self.trajectory_store is not None:
            self.trajectory_store.save(
                session_id=self._active_session_id,
                prompt=prompt,
                final_text=getattr(result, "final_text", ""),
                messages=list(getattr(result, "messages", [])),
                tool_invocations=list(getattr(result, "tool_invocations", [])),
                events=list(getattr(result, "events", [])),
                compactions=list(getattr(result, "compactions", [])),
                attachments=list(attachment_paths or []),
                metadata={"steps": getattr(result, "steps", 0)},
            )

        if (
            not self.settings.evolution_enabled
            or self.review_manager is None
            or self.settings.evolution_review_mode == "off"
        ):
            if self.memory_provider_manager is not None:
                self.memory_provider_manager.sync_turn(list(getattr(result, "messages", [])))
            return

        def _run_review() -> None:
            report = self.review_manager.review_run(
                session_id=self._active_session_id,
                prompt=prompt,
                messages=list(getattr(result, "messages", [])),
                tool_invocations=list(getattr(result, "tool_invocations", [])),
                final_text=getattr(result, "final_text", ""),
                min_tool_calls=self.settings.evolution_review_min_tool_calls,
                reviewer=self._create_review_reviewer(),
            )
            if report is None:
                return

            if self.settings.evolution_auto_memory_apply:
                for candidate in report.candidates:
                    if candidate.candidate_type != "memory":
                        continue
                    try:
                        self.review_manager.apply_memory_candidate(
                            candidate.candidate_id,
                            self.memory_manager,
                        )
                    except Exception:
                        pass

            if self.settings.evolution_auto_skill_apply:
                for candidate in report.candidates:
                    if candidate.candidate_type != "skill":
                        continue
                    try:
                        self.review_manager.apply_skill_candidate(
                            candidate.candidate_id,
                            self.skill_loader,
                            self.settings.skill_dir,
                        )
                    except Exception:
                        pass

            if self.memory_provider_manager is not None:
                self.memory_provider_manager.sync_turn(list(getattr(result, "messages", [])))

        if self.settings.evolution_review_mode == "async":
            import threading

            thread = threading.Thread(
                target=_run_review,
                name="ecology-harness-review",
                daemon=True,
            )
            thread.start()
            return

        _run_review()

    def _create_review_reviewer(self):
        if not self.settings.evolution_enabled:
            return None
        configured_provider = (self.settings.evolution_review_provider or "").strip()
        configured_model = (self.settings.evolution_review_model or "").strip()
        if configured_provider == "off":
            return None

        review_settings = replace(self.settings)
        if configured_provider:
            review_settings.provider = configured_provider
        if configured_model:
            review_settings.model = configured_model

        def _review(payload: dict) -> dict | str | None:
            slot_settings = resolve_slot_settings(review_settings, "review")
            try:
                provider = create_provider(slot_settings.provider, settings=slot_settings)
            except (ProviderError, Exception):
                return None
            system_message = ChatMessage(
                role="system",
                content=REVIEW_SYSTEM_PROMPT,
            )
            user_message = ChatMessage(
                role="user",
                content=json.dumps(payload, ensure_ascii=False, indent=2),
            )
            try:
                response = provider.complete([system_message, user_message], [], slot_settings)
            except Exception:
                return None
            return response.content

        return _review

    def _derive_session_title(self, messages: list[ChatMessage]) -> str:
        for message in messages:
            if message.role != "user":
                continue
            text = message.summary_text(max_document_chars=180).strip().replace("\n", " ")
            if not text:
                continue
            if len(text) > 72:
                return text[:69].rstrip() + "..."
            return text
        return "Untitled session"

    def _derive_session_recap(self, messages: list[ChatMessage], compaction: dict | None = None) -> str:
        assistant = ""
        user = ""
        for message in reversed(messages):
            text = message.summary_text(max_document_chars=220).strip().replace("\n", " ")
            if not text:
                continue
            if not assistant and message.role == "assistant":
                assistant = text
            elif not user and message.role == "user":
                user = text
            if assistant and user:
                break
        parts = []
        if user:
            parts.append("Latest ask: %s" % user)
        if assistant:
            parts.append("Latest outcome: %s" % assistant)
        if compaction and compaction.get("compressed_summary"):
            parts.append("Continuation: %s" % str(compaction["compressed_summary"]).strip()[:180])
        recap = " | ".join(parts).strip()
        if len(recap) > 320:
            recap = recap[:317].rstrip() + "..."
        return recap
