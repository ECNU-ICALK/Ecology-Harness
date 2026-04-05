from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass
class HarnessSettings:
    workspace_root: Path
    state_dir: Path
    user_state_dir: Path
    memory_dir: Path
    skill_dir: Path
    plugin_dir: Path
    mcp_dir: Path
    agent_dir: Path
    session_dir: Path
    task_file: Path
    audit_log_file: Path
    provider: str = "auto"
    model: str = "mock-agent"
    base_url: str = ""
    api_key: str = ""
    api_key_env: str = ""
    permission_mode: str = "workspace-write"
    max_read_bytes: int = 200_000
    max_write_bytes: int = 300_000
    max_grep_results: int = 100
    max_glob_results: int = 200
    max_web_bytes: int = 300_000
    max_command_output: int = 12_000
    command_timeout_sec: int = 20
    provider_timeout_sec: int = 0
    max_agent_loops: int = 0
    max_context_tokens: int = 128_000
    preserve_last_n_turns: int = 6
    subagent_max_depth: int = 2
    subagent_max_concurrent: int = 4
    memory_index_max_lines: int = 200
    memory_index_max_bytes: int = 25_000
    memory_default_scope: str = "project"
    sandbox_enabled: bool = True
    sandbox_mode: str = "workspace-write"
    sandbox_backend: str = "internal"
    sandbox_allow_network: bool = True
    sandbox_fail_closed: bool = False
    sandbox_extra_read_roots: tuple[str, ...] = ()
    sandbox_extra_write_roots: tuple[str, ...] = ()
    denied_bash_patterns: tuple[str, ...] = (
        "rm -rf /",
        "shutdown",
        "reboot",
        ":(){ :|:& };:",
        "mkfs",
        "dd if=",
        "chmod -R 777 /",
    )

    @classmethod
    def from_workspace(cls, workspace: str | Path) -> "HarnessSettings":
        workspace_root = Path(workspace).expanduser().resolve()
        state_dir = workspace_root / ".ecology_harness"
        user_state_dir = Path.home() / ".ecology_harness"
        return cls(
            workspace_root=workspace_root,
            state_dir=state_dir,
            user_state_dir=user_state_dir,
            memory_dir=state_dir / "memory",
            skill_dir=state_dir / "skills",
            plugin_dir=state_dir / "plugins",
            mcp_dir=state_dir / "mcp",
            agent_dir=state_dir / "agents",
            session_dir=state_dir / "sessions",
            task_file=state_dir / "tasks.json",
            audit_log_file=state_dir / "audit.log",
        )

    def ensure_directories(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.user_state_dir.mkdir(parents=True, exist_ok=True)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.skill_dir.mkdir(parents=True, exist_ok=True)
        self.plugin_dir.mkdir(parents=True, exist_ok=True)
        self.mcp_dir.mkdir(parents=True, exist_ok=True)
        self.agent_dir.mkdir(parents=True, exist_ok=True)
        self.session_dir.mkdir(parents=True, exist_ok=True)

    def resolve_api_key(self) -> str:
        if self.api_key:
            return self.api_key
        return os.environ.get(self.api_key_env, "")

    @property
    def user_memory_dir(self) -> Path:
        return self.user_state_dir / "memory"

    @property
    def user_skill_dir(self) -> Path:
        return self.user_state_dir / "skills"

    @property
    def user_plugin_dir(self) -> Path:
        return self.user_state_dir / "plugins"

    @property
    def user_mcp_dir(self) -> Path:
        return self.user_state_dir / "mcp"

    @property
    def user_agent_dir(self) -> Path:
        return self.user_state_dir / "agents"

    def resolved_sandbox_read_roots(self) -> list[Path]:
        roots = [
            self.workspace_root,
            self.state_dir,
            self.user_state_dir,
        ]
        roots.extend(Path(item).expanduser().resolve() for item in self.sandbox_extra_read_roots)
        return roots

    def resolved_sandbox_write_roots(self) -> list[Path]:
        roots = [
            self.workspace_root,
            self.state_dir,
            self.user_state_dir,
        ]
        roots.extend(Path(item).expanduser().resolve() for item in self.sandbox_extra_write_roots)
        return roots
