from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path

from ecology_harness.agents import SubAgentManager
from ecology_harness.config import HarnessSettings
from ecology_harness.memory import MemoryManager
from ecology_harness.mcp import McpServerRegistry
from ecology_harness.permissions import PermissionPolicy
from ecology_harness.plugins import PluginManager
from ecology_harness.runtime import AgentLoop
from ecology_harness.runtime import ChatMessage
from ecology_harness.runtime.prompt_builder import PromptBuilder
from ecology_harness.runtime.providers import create_provider
from ecology_harness.runtime.session_store import SessionForkRecord, SessionStore
from ecology_harness.sandbox import SandboxPolicy
from ecology_harness.skills import SkillLoader, execute_skill
from ecology_harness.tasks import TaskStore
from ecology_harness.tools import ToolRegistry
from ecology_harness.tools.builtin import register_builtin_tools


class EcologyHarnessApp:
    """Application wiring for the harness runtime."""

    def __init__(self, settings: HarnessSettings) -> None:
        self.settings = settings
        self.registry = ToolRegistry()
        self.memory_manager: MemoryManager | None = None
        self.skill_loader: SkillLoader | None = None
        self.plugin_manager: PluginManager | None = None
        self.task_store: TaskStore | None = None
        self.permission_policy = PermissionPolicy()
        self.prompt_builder = PromptBuilder()
        self.subagent_manager: SubAgentManager | None = None
        self.mcp_registry: McpServerRegistry | None = None
        self.sandbox: SandboxPolicy | None = None
        self.session_store: SessionStore | None = None
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
        )
        self.task_store = TaskStore(self.settings.task_file)
        self.subagent_manager = SubAgentManager(self)
        self.sandbox = SandboxPolicy(self.settings)
        self.session_store = SessionStore(self.settings.session_dir)
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
        skill_index = [
            item.to_index_dict() for item in self.skill_loader.list_skills()  # type: ignore[union-attr]
        ]
        agent_index = [
            item.to_index_dict() for item in self.subagent_manager.list_agent_definitions()  # type: ignore[union-attr]
        ]
        plugin_index = [
            item.to_index_dict() for item in self.plugin_manager.list_enabled_plugins()  # type: ignore[union-attr]
        ]
        mcp_index = [
            item.to_dict() for item in self.mcp_registry.list_server_states()  # type: ignore[union-attr]
        ]
        memory_context = self.memory_manager.get_memory_context(  # type: ignore[union-attr]
            query=prompt_text,
            conversation=conversation,
            include_guidance=True,
        )
        return self.prompt_builder.build(
            active_settings,
            memory_context=memory_context,
            skill_index=skill_index,
            agent_index=agent_index,
            plugin_index=plugin_index,
            mcp_index=mcp_index,
            runtime_mode=self.runtime_mode,
        )

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
        skill = self.skill_loader.find_by_trigger(prompt)  # type: ignore[union-attr]
        if skill is not None:
            trigger = prompt.strip().split(" ", 1)[0]
            args = prompt.strip()[len(trigger) :].strip()
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
        return result

    def get_services(self, **extra):
        self._ensure_initialized()
        services = {
            "app": self,
            "memory_manager": self.memory_manager,
            "skill_loader": self.skill_loader,
            "plugin_manager": self.plugin_manager,
            "task_store": self.task_store,
            "subagent_manager": self.subagent_manager,
            "mcp_registry": self.mcp_registry,
            "sandbox": self.sandbox,
            "tool_registry": self.registry,
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
        self.session_store.save(  # type: ignore[union-attr]
            session_id=self._active_session_id,
            created_at=self._active_session_created_at,
            messages=messages,
            compaction=compaction,
            fork=self._active_fork.to_dict() if self._active_fork is not None else None,
        )

    def load_session(self, name: str = "latest") -> list[ChatMessage]:
        self._ensure_initialized()
        managed = self.session_store.load(name)  # type: ignore[union-attr]
        self._active_session_id = managed.session_id
        self._active_session_created_at = managed.created_at
        self._active_fork = managed.fork
        return managed.messages

    def latest_session_path(self) -> Path:
        self._ensure_initialized()
        return self.session_store.latest_path()  # type: ignore[union-attr]

    def list_sessions(self):
        self._ensure_initialized()
        return self.session_store.list_sessions()  # type: ignore[union-attr]

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

    def _ensure_initialized(self) -> None:
        if not self._initialized:
            raise RuntimeError("EcologyHarnessApp must be initialized before use.")
