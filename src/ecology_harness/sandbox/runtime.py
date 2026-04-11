from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile

from ecology_harness.config import HarnessSettings


class SandboxViolation(RuntimeError):
    """Raised when an operation violates sandbox policy."""


@dataclass(frozen=True)
class SandboxAvailability:
    enabled: bool
    active: bool
    backend: str
    reason: str = ""


class SandboxPolicy:
    def __init__(self, settings: HarnessSettings) -> None:
        self.settings = settings

    def get_availability(self) -> SandboxAvailability:
        if not self.settings.sandbox_enabled:
            return SandboxAvailability(
                enabled=False,
                active=False,
                backend="disabled",
                reason="sandbox is disabled",
            )
        backend = (self.settings.sandbox_backend or "internal").strip().lower()
        if backend == "disabled":
            return SandboxAvailability(
                enabled=True,
                active=False,
                backend="disabled",
                reason="sandbox backend disabled by configuration",
            )
        if backend in {"auto", "sandbox-exec"}:
            sandbox_exec = shutil.which("sandbox-exec")
            if sandbox_exec:
                return SandboxAvailability(
                    enabled=True,
                    active=True,
                    backend="sandbox-exec",
                    reason="",
                )
            if backend == "sandbox-exec" and self.settings.sandbox_fail_closed:
                raise SandboxViolation("sandbox-exec backend requested but unavailable")
        return SandboxAvailability(
            enabled=True,
            active=True,
            backend="internal",
            reason="using internal path and command policy",
        )

    def resolve_path(self, raw_path: str, access: str = "read") -> Path:
        candidate = Path(raw_path).expanduser()
        if not candidate.is_absolute():
            candidate = self.settings.workspace_root / candidate
        candidate = candidate.resolve()

        allowed_roots = (
            self.settings.resolved_sandbox_read_roots()
            if access == "read"
            else self.settings.resolved_sandbox_write_roots()
        )
        if self._is_under_allowed_root(candidate, allowed_roots):
            return candidate
        raise SandboxViolation("Path is outside sandbox %s roots: %s" % (access, raw_path))

    def resolve_directory(self, raw_path: str | Path | None = None) -> Path:
        candidate = Path(raw_path).expanduser().resolve() if raw_path else self.settings.workspace_root
        if self._is_under_allowed_root(candidate, self.settings.resolved_sandbox_read_roots()):
            return candidate
        raise SandboxViolation("Directory is outside sandbox roots: %s" % candidate)

    def validate_command(self, command: str) -> None:
        normalized = command.strip().lower()
        if not normalized:
            raise SandboxViolation("Empty command is not allowed")
        for pattern in self.settings.denied_bash_patterns:
            if pattern.lower() in normalized:
                raise SandboxViolation("command matched denied pattern `%s`" % pattern)

    def run_shell(
        self,
        command: str,
        *,
        cwd: str | Path | None = None,
        timeout_sec: int | None = None,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess:
        self.validate_command(command)
        resolved_cwd = self.resolve_directory(cwd)
        availability = self.get_availability()
        timeout = timeout_sec or self.settings.command_timeout_sec

        if availability.backend == "sandbox-exec":
            argv, profile_path = self._build_macos_sandbox_command(command, resolved_cwd)
            try:
                completed = subprocess.run(
                    argv,
                    cwd=str(resolved_cwd),
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    env=env,
                )
            finally:
                if profile_path is not None:
                    Path(profile_path).unlink(missing_ok=True)
            return completed

        return subprocess.run(
            command,
            cwd=str(resolved_cwd),
            shell=True,
            executable="/bin/bash",
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )

    def describe(self) -> dict[str, object]:
        availability = self.get_availability()
        return {
            "enabled": availability.enabled,
            "active": availability.active,
            "backend": availability.backend,
            "reason": availability.reason,
            "mode": self.settings.sandbox_mode,
            "allow_network": self.settings.sandbox_allow_network,
            "read_roots": [str(item) for item in self.settings.resolved_sandbox_read_roots()],
            "write_roots": [str(item) for item in self.settings.resolved_sandbox_write_roots()],
        }

    def _build_macos_sandbox_command(self, command: str, cwd: Path) -> tuple[list[str], str]:
        profile = self._build_macos_profile()
        tmp = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix="ecology-harness-sandbox-",
            suffix=".sb",
            delete=False,
        )
        try:
            tmp.write(profile)
            tmp.write("\n")
        finally:
            tmp.close()
        sandbox_exec = shutil.which("sandbox-exec") or "sandbox-exec"
        argv = [
            sandbox_exec,
            "-f",
            tmp.name,
            "/bin/bash",
            "-lc",
            command,
        ]
        return argv, tmp.name

    def _build_macos_profile(self) -> str:
        read_roots = self.settings.resolved_sandbox_read_roots()
        write_roots = self.settings.resolved_sandbox_write_roots()
        lines = [
            "(version 1)",
            '(deny default)',
            '(import "system.sb")',
            '(allow process*)',
            '(allow file-read-metadata)',
        ]
        if self.settings.sandbox_allow_network:
            lines.append("(allow network*)")
        for root in read_roots:
            lines.append('(allow file-read* (subpath "%s"))' % _escape_sb_path(root))
        if self.settings.sandbox_mode != "read-only":
            for root in write_roots:
                lines.append('(allow file-write* (subpath "%s"))' % _escape_sb_path(root))
        return "\n".join(lines)

    def _is_under_allowed_root(self, candidate: Path, roots: list[Path]) -> bool:
        for root in roots:
            try:
                candidate.relative_to(root.resolve())
                return True
            except ValueError:
                continue
        return False


def _escape_sb_path(path: Path) -> str:
    return str(path).replace("\\", "\\\\").replace('"', '\\"')
