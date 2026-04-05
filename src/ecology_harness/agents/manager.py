from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field, replace
from datetime import datetime
import os
from pathlib import Path
import queue
import subprocess
import tempfile
import time
from typing import Any
import uuid

from ecology_harness.runtime.agent_loop import AgentRunResult
from ecology_harness.runtime.compaction import compress_summary_text, summarize_messages
from ecology_harness.runtime.messages import ChatMessage
from ecology_harness.tasks import TaskStore
from ecology_harness.utils import parse_frontmatter, slugify


def _utc_now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


@dataclass
class AgentDefinition:
    name: str
    description: str = ""
    system_prompt: str = ""
    model: str = ""
    tools: list[str] = field(default_factory=list)
    source: str = "builtin"

    def to_index_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "description": self.description,
            "source": self.source,
            "model": self.model,
            "tools": ", ".join(self.tools),
        }


@dataclass
class SubAgentTask:
    id: str
    prompt: str
    status: str = "pending"
    result: str = ""
    depth: int = 0
    name: str = ""
    agent_type: str = ""
    worktree_path: str = ""
    worktree_branch: str = ""
    provider: str = ""
    model: str = ""
    expected_output: str = ""
    ownership: str = ""
    shared_context_summary: str = ""
    parent_task_id: str = ""
    dependency_ids: list[str] = field(default_factory=list)
    child_task_ids: list[str] = field(default_factory=list)
    task_record_id: str = ""
    handoff_history: list[str] = field(default_factory=list)
    coordination_notes: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_utc_now)
    updated_at: str = field(default_factory=_utc_now)
    steps: int = 0
    tool_calls: int = 0
    conversation_messages: int = 0
    last_tool_invocations: list[dict[str, Any]] = field(default_factory=list)
    _cancel_flag: bool = False
    _future: Future | None = field(default=None, repr=False)
    _inbox: queue.Queue = field(default_factory=queue.Queue, repr=False)

    def touch(self) -> None:
        self.updated_at = _utc_now()

    def note(self, text: str) -> None:
        if not text:
            return
        self.coordination_notes.append(text)
        self.touch()


BUILTIN_AGENTS = {
    "general-purpose": AgentDefinition(
        name="general-purpose",
        description="General-purpose agent for research and multi-step tasks.",
        source="builtin",
    ),
    "coder": AgentDefinition(
        name="coder",
        description="Specialized coding agent for reading and modifying code.",
        system_prompt=(
            "You are a specialized coding subagent. Read before changing files, make minimal edits, "
            "and prefer concrete implementation over discussion."
        ),
        source="builtin",
    ),
    "reviewer": AgentDefinition(
        name="reviewer",
        description="Review agent for correctness, security, and regressions.",
        system_prompt=(
            "You are a review subagent. Prioritize bugs, regressions, and missing tests."
        ),
        tools=["Read", "Glob", "Grep", "MemorySearch", "TaskList"],
        source="builtin",
    ),
    "researcher": AgentDefinition(
        name="researcher",
        description="Research agent for codebase or web investigation.",
        system_prompt=(
            "You are a research subagent. Gather evidence and answer precisely."
        ),
        tools=["Read", "Glob", "Grep", "WebFetch", "MemorySearch"],
        source="builtin",
    ),
    "tester": AgentDefinition(
        name="tester",
        description="Testing agent for writing and running tests.",
        system_prompt=(
            "You are a testing subagent. Focus on targeted, reproducible verification."
        ),
        source="builtin",
    ),
    "planner": AgentDefinition(
        name="planner",
        description="Planning agent for decomposition, sequencing, and dependency mapping.",
        system_prompt=(
            "You are a planning subagent. Break work into clear steps, dependencies, and checkpoints."
        ),
        tools=["TaskCreate", "TaskList", "TaskUpdate", "MemorySearch", "Read", "Glob", "Grep"],
        source="builtin",
    ),
    "coordinator": AgentDefinition(
        name="coordinator",
        description="Coordination agent for delegating work, tracking dependencies, and merging findings.",
        system_prompt=(
            "You are a coordination subagent. Keep shared context crisp, maintain dependencies, and "
            "return integration-ready outputs."
        ),
        tools=["TaskList", "TaskUpdate", "MemorySearch", "ListAgentTasks", "CheckAgentResult"],
        source="builtin",
    ),
}


def _parse_agent_file(path: Path, source: str) -> AgentDefinition | None:
    try:
        raw = path.read_text(encoding="utf-8")
    except Exception:
        return None
    metadata, body = parse_frontmatter(raw)
    name = metadata.get("name", path.stem).strip()
    if not name:
        return None
    tools_raw = metadata.get("tools", metadata.get("allowed-tools", ""))
    tools = []
    if tools_raw:
        cleaned = tools_raw.strip()
        if cleaned.startswith("[") and cleaned.endswith("]"):
            cleaned = cleaned[1:-1]
        tools = [item.strip().strip('"').strip("'") for item in cleaned.split(",") if item.strip()]
    return AgentDefinition(
        name=slugify(name),
        description=metadata.get("description", ""),
        system_prompt=body.strip(),
        model=metadata.get("model", ""),
        tools=tools,
        source=source,
    )


class SubAgentManager:
    def __init__(self, app) -> None:
        self.app = app
        self.tasks: dict[str, SubAgentTask] = {}
        self._by_name: dict[str, str] = {}
        self._pool = ThreadPoolExecutor(max_workers=app.settings.subagent_max_concurrent)
        self._task_store = TaskStore(app.settings.state_dir / "agent_tasks.json")

    def load_agent_definitions(self) -> dict[str, AgentDefinition]:
        definitions = dict(BUILTIN_AGENTS)
        for source, root in (
            ("user", self.app.settings.user_agent_dir),
            ("project", self.app.settings.agent_dir),
        ):
            if not root.exists():
                continue
            for path in sorted(root.glob("*.md")):
                parsed = _parse_agent_file(path, source)
                if parsed is not None:
                    definitions[parsed.name] = parsed
        return definitions

    def get_agent_definition(self, name: str) -> AgentDefinition | None:
        return self.load_agent_definitions().get(name)

    def list_agent_definitions(self) -> list[AgentDefinition]:
        return sorted(self.load_agent_definitions().values(), key=lambda item: item.name)

    def run(
        self,
        prompt: str,
        provider_name: str = "",
        depth: int = 0,
        agent_type: str = "",
        name: str = "",
        wait: bool = True,
        model_override: str = "",
        allowed_tools: set[str] | None = None,
        extra_system_prompt: str = "",
        isolation: str = "",
        event_handler=None,
        expected_output: str = "",
        ownership: str = "",
        depends_on: list[str] | None = None,
        parent_conversation: list[ChatMessage] | None = None,
        parent_task_id: str = "",
        coordination_context: str = "",
    ) -> AgentRunResult | SubAgentTask:
        task = self.spawn(
            prompt=prompt,
            provider_name=provider_name,
            depth=depth,
            agent_type=agent_type,
            name=name,
            model_override=model_override,
            allowed_tools=allowed_tools,
            extra_system_prompt=extra_system_prompt,
            isolation=isolation,
            event_handler=event_handler,
            expected_output=expected_output,
            ownership=ownership,
            depends_on=depends_on,
            parent_conversation=parent_conversation,
            parent_task_id=parent_task_id,
            coordination_context=coordination_context,
        )
        if not wait:
            return task
        self.wait(task.id, timeout=None)
        return AgentRunResult(
            final_text=task.result or "",
            steps=task.steps,
            tool_invocations=task.last_tool_invocations,
        )

    def spawn(
        self,
        prompt: str,
        provider_name: str = "",
        depth: int = 0,
        agent_type: str = "",
        name: str = "",
        model_override: str = "",
        allowed_tools: set[str] | None = None,
        extra_system_prompt: str = "",
        isolation: str = "",
        event_handler=None,
        expected_output: str = "",
        ownership: str = "",
        depends_on: list[str] | None = None,
        parent_conversation: list[ChatMessage] | None = None,
        parent_task_id: str = "",
        coordination_context: str = "",
    ) -> SubAgentTask:
        task_id = uuid.uuid4().hex[:12]
        task = SubAgentTask(
            id=task_id,
            prompt=prompt,
            depth=depth,
            name=name or task_id[:8],
            agent_type=agent_type,
            provider=provider_name or self.app.settings.provider,
            expected_output=expected_output,
            ownership=ownership,
            parent_task_id=parent_task_id,
            dependency_ids=[str(item) for item in depends_on or []],
        )
        self.tasks[task.id] = task
        if name:
            self._by_name[name] = task.id
        if parent_task_id:
            parent = self.get_task(parent_task_id)
            if parent is not None and task.id not in parent.child_task_ids:
                parent.child_task_ids.append(task.id)
                parent.touch()

        task.shared_context_summary = self._build_shared_context_summary(
            task=task,
            parent_conversation=parent_conversation,
            coordination_context=coordination_context,
        )
        task.task_record_id = self._create_task_record(task)

        if depth >= self.app.settings.subagent_max_depth:
            task.status = "failed"
            task.result = "Max depth (%s) exceeded" % self.app.settings.subagent_max_depth
            task.note(task.result)
            self._sync_task_record(task)
            return task

        agent_def = self.get_agent_definition(agent_type) if agent_type else None
        if agent_type and agent_def is None:
            task.status = "failed"
            task.result = "Unknown agent type: %s" % agent_type
            task.note(task.result)
            self._sync_task_record(task)
            return task

        worktree_path = ""
        worktree_branch = ""
        if isolation == "worktree":
            git_root = self._git_root(str(self.app.settings.workspace_root))
            if not git_root:
                task.status = "failed"
                task.result = "isolation='worktree' requires a git repository"
                task.note(task.result)
                self._sync_task_record(task)
                return task
            try:
                worktree_path, worktree_branch = self._create_worktree(git_root)
                task.worktree_path = worktree_path
                task.worktree_branch = worktree_branch
            except Exception as exc:
                task.status = "failed"
                task.result = "Failed to create worktree: %s" % exc
                task.note(task.result)
                self._sync_task_record(task)
                return task

        def _run() -> None:
            local_settings = replace(self.app.settings)
            task.status = "running"
            task.touch()
            self._sync_task_record(task)

            if worktree_path:
                root = Path(worktree_path)
                local_settings.workspace_root = root
                local_settings.state_dir = root / ".ecology_harness"
                local_settings.memory_dir = local_settings.state_dir / "memory"
                local_settings.skill_dir = local_settings.state_dir / "skills"
                local_settings.agent_dir = local_settings.state_dir / "agents"
                local_settings.session_dir = local_settings.state_dir / "sessions"
                local_settings.task_file = local_settings.state_dir / "tasks.json"
                local_settings.audit_log_file = local_settings.state_dir / "audit.log"
                local_settings.ensure_directories()

            if model_override:
                local_settings.model = model_override
            elif agent_def and agent_def.model:
                local_settings.model = agent_def.model
            task.model = local_settings.model

            if provider_name:
                local_settings.provider = provider_name
            task.provider = local_settings.provider

            effective_tools = set(allowed_tools or [])
            if agent_def and agent_def.tools:
                effective_tools = (
                    set(agent_def.tools)
                    if not effective_tools
                    else effective_tools & set(agent_def.tools)
                )
            if not effective_tools:
                effective_tools = None

            if not self._wait_for_dependencies(task):
                self._sync_task_record(task)
                return

            system_prompt = self.app.build_system_prompt(
                settings=local_settings,
                prompt_text=prompt,
                conversation=parent_conversation,
            )
            if agent_def and agent_def.system_prompt:
                system_prompt = agent_def.system_prompt.rstrip() + "\n\n" + system_prompt
            if extra_system_prompt:
                system_prompt = extra_system_prompt.rstrip() + "\n\n" + system_prompt

            if task.shared_context_summary:
                system_prompt = (
                    "# Delegation brief\n%s\n\n%s" % (task.shared_context_summary, system_prompt)
                )

            conversation = None
            current_prompt = self._compose_initial_prompt(task)
            try:
                while True:
                    if task._cancel_flag:
                        task.status = "cancelled"
                        task.note("Cancelled before completion.")
                        break

                    loop = self.app.create_agent_loop(
                        provider_name=local_settings.provider,
                        allowed_tools=effective_tools,
                        settings=local_settings,
                    )
                    result = loop.run(
                        prompt=current_prompt,
                        settings=local_settings,
                        system_prompt=system_prompt,
                        conversation=conversation,
                        depth=depth + 1,
                        event_handler=event_handler,
                    )
                    conversation = result.messages
                    task.result = result.final_text
                    task.steps += result.steps
                    task.tool_calls += len(result.tool_invocations)
                    task.last_tool_invocations = result.tool_invocations
                    task.conversation_messages = len(result.messages)
                    task.status = "completed"
                    task.touch()
                    self._sync_task_record(task)

                    if task._inbox.empty():
                        break
                    current_prompt = task._inbox.get()
                    task.handoff_history.append(current_prompt)
                    task.status = "running"
                    task.touch()
                    self._sync_task_record(task)
            except Exception as exc:
                task.status = "failed"
                task.result = "Error: %s" % exc
                task.note(task.result)
            finally:
                task.touch()
                self._sync_task_record(task)
                if worktree_path:
                    self._remove_worktree(
                        worktree_path,
                        worktree_branch,
                        str(self.app.settings.workspace_root),
                    )

        task._future = self._pool.submit(_run)
        return task

    def wait(self, task_id: str, timeout: float | None = None) -> SubAgentTask | None:
        task = self.tasks.get(task_id)
        if task is None:
            return None
        if task._future is not None:
            try:
                task._future.result(timeout=timeout)
            except Exception:
                pass
        return task

    def send_message(self, task_id_or_name: str, message: str) -> bool:
        task_id = self._by_name.get(task_id_or_name, task_id_or_name)
        task = self.tasks.get(task_id)
        if task is None:
            return False
        if task.status not in {"running", "pending", "blocked"}:
            return False
        task._inbox.put(message)
        task.handoff_history.append(message)
        task.touch()
        self._sync_task_record(task)
        return True

    def get_task(self, task_id_or_name: str) -> SubAgentTask | None:
        task_id = self._by_name.get(task_id_or_name, task_id_or_name)
        return self.tasks.get(task_id)

    def list_tasks(self) -> list[SubAgentTask]:
        return list(self.tasks.values())

    def _create_task_record(self, task: SubAgentTask) -> str:
        record = self._task_store.create(
            subject="Subagent %s [%s]" % (task.name, task.agent_type or "general-purpose"),
            description=_truncate(task.prompt, 240),
            metadata={
                "subagent_id": task.id,
                "agent_type": task.agent_type or "general-purpose",
                "provider": task.provider,
                "expected_output": task.expected_output,
                "ownership": task.ownership,
                "dependencies": task.dependency_ids,
            },
        )
        self._task_store.update(
            record.id,
            owner=task.name,
            status=task.status,
        )
        return record.id

    def _sync_task_record(self, task: SubAgentTask) -> None:
        if not task.task_record_id:
            return
        self._task_store.update(
            task.task_record_id,
            status=task.status,
            owner=task.name,
            metadata={
                "subagent_id": task.id,
                "agent_type": task.agent_type or "general-purpose",
                "provider": task.provider,
                "model": task.model,
                "expected_output": task.expected_output,
                "ownership": task.ownership,
                "dependencies": task.dependency_ids,
                "children": task.child_task_ids,
                "steps": task.steps,
                "tool_calls": task.tool_calls,
                "conversation_messages": task.conversation_messages,
                "shared_context_summary": _truncate(task.shared_context_summary, 600),
                "result_excerpt": _truncate(task.result, 400),
                "handoff_count": len(task.handoff_history),
                "updated_at": task.updated_at,
            },
        )

    def _wait_for_dependencies(self, task: SubAgentTask) -> bool:
        if not task.dependency_ids:
            return True
        task.status = "blocked"
        task.note("Waiting for dependencies: %s" % ", ".join(task.dependency_ids))
        self._sync_task_record(task)
        terminal_success = {"completed"}
        terminal_failure = {"failed", "cancelled"}
        while True:
            unresolved = []
            for dependency_id in task.dependency_ids:
                dependency = self.get_task(dependency_id)
                if dependency is None:
                    continue
                if dependency.status in terminal_failure:
                    task.status = "failed"
                    task.result = (
                        "Dependency %s finished with status %s."
                        % (dependency_id, dependency.status)
                    )
                    task.note(task.result)
                    return False
                if dependency.status not in terminal_success:
                    unresolved.append(dependency_id)
            if not unresolved:
                task.status = "running"
                task.note("Dependencies satisfied.")
                return True
            time.sleep(0.05)

    def _build_shared_context_summary(
        self,
        task: SubAgentTask,
        parent_conversation: list[ChatMessage] | None,
        coordination_context: str,
    ) -> str:
        lines = [
            "- Assigned work: %s" % _truncate(task.prompt, 220),
            "- Agent role: %s" % (task.agent_type or "general-purpose"),
        ]
        if task.ownership:
            lines.append("- Ownership: %s" % task.ownership)
        if task.expected_output:
            lines.append("- Expected output: %s" % _truncate(task.expected_output, 220))
        if task.parent_task_id:
            lines.append("- Parent subagent: %s" % task.parent_task_id)
        if task.dependency_ids:
            lines.append("- Depends on: %s" % ", ".join(task.dependency_ids))
        if coordination_context:
            lines.append("- Coordinator notes: %s" % _truncate(coordination_context, 240))
        if parent_conversation:
            subset = list(parent_conversation[-10:])
            if subset and subset[0].role == "system":
                subset = subset[1:]
            if subset:
                conversation_summary = compress_summary_text(
                    summarize_messages(subset),
                )
                lines.append("- Parent conversation summary:")
                lines.extend("  %s" % line for line in conversation_summary.splitlines()[:12])
        return "\n".join(lines)

    def _compose_initial_prompt(self, task: SubAgentTask) -> str:
        parts = []
        if task.shared_context_summary:
            parts.append("[Shared context]\n%s" % task.shared_context_summary)
        parts.append(task.prompt)
        if task.expected_output:
            parts.append("[Expected output]\n%s" % task.expected_output)
        return "\n\n".join(part for part in parts if part)

    def _git_root(self, cwd: str) -> str | None:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except Exception:
            return None

    def _create_worktree(self, base_dir: str) -> tuple[str, str]:
        branch = "ecology-agent-%s" % uuid.uuid4().hex[:8]
        path = tempfile.mkdtemp(prefix="ecology-agent-wt-")
        os.rmdir(path)
        subprocess.run(
            ["git", "worktree", "add", "-b", branch, path],
            cwd=base_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        return path, branch

    def _remove_worktree(self, worktree_path: str, branch: str, base_dir: str) -> None:
        try:
            subprocess.run(
                ["git", "worktree", "remove", "--force", worktree_path],
                cwd=base_dir,
                capture_output=True,
                text=True,
            )
        except Exception:
            pass
        if branch:
            try:
                subprocess.run(
                    ["git", "branch", "-D", branch],
                    cwd=base_dir,
                    capture_output=True,
                    text=True,
                )
            except Exception:
                pass


def _truncate(text: str, limit: int) -> str:
    cleaned = " ".join((text or "").split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3] + "..."
