from __future__ import annotations

from importlib.util import find_spec
from pathlib import Path
import platform
import shutil
from typing import Any

from ecology_harness.workspace import WorkspaceBootstrapManager


class HarnessDoctor:
    def __init__(self, app) -> None:
        self.app = app

    def run(self, probe_mcp: bool = False, timeout_sec: int = 3) -> dict[str, Any]:
        settings = self.app.settings
        bootstrap = WorkspaceBootstrapManager(settings.workspace_root)
        bootstrap_status = bootstrap.status()
        skills = self.app.skill_loader.list_skills(include_archived=True)
        skill_status_counts: dict[str, int] = {}
        for item in skills:
            skill_status_counts[item.readiness] = skill_status_counts.get(item.readiness, 0) + 1
        mcp_states = self.app.mcp_registry.list_server_states(
            probe_remote=probe_mcp,
            timeout_sec=timeout_sec,
        )
        mcp_catalog_issues = self.app.mcp_registry.list_config_issues()
        integrations = self.app.integration_manager.status_summary() if self.app.integration_manager is not None else {
            "total": 0,
            "enabled": 0,
            "kinds": {},
            "status_counts": {},
            "items": [],
        }
        mcp_status_counts: dict[str, int] = {}
        for item in mcp_states:
            status = str(getattr(item, "status", "unknown") or "unknown")
            mcp_status_counts[status] = mcp_status_counts.get(status, 0) + 1
        optional_dependencies = {
            "prompt_toolkit": self._module_status("prompt_toolkit"),
            "playwright": self._module_status("playwright"),
            "ffmpeg": self._command_status("ffmpeg"),
            "ffprobe": self._command_status("ffprobe"),
        }
        issues: list[str] = []
        if bootstrap_status["present_count"] == 0:
            issues.append("No workspace bootstrap files are present.")
        if skill_status_counts.get("setup-needed", 0):
            issues.append(
                "%s skills still require setup."
                % skill_status_counts.get("setup-needed", 0)
            )
        if mcp_status_counts.get("missing-command", 0):
            issues.append(
                "%s MCP server(s) reference a missing stdio command."
                % mcp_status_counts.get("missing-command", 0)
            )
        if probe_mcp and mcp_status_counts.get("unreachable", 0):
            issues.append(
                "%s MCP server(s) were unreachable during probing."
                % mcp_status_counts.get("unreachable", 0)
            )
        if mcp_catalog_issues:
            issues.append(
                "%s MCP catalog config file(s) could not be loaded."
                % len(mcp_catalog_issues)
            )
        if integrations["status_counts"].get("invalid-config", 0):
            issues.append(
                "%s integration(s) have invalid configuration."
                % integrations["status_counts"].get("invalid-config", 0)
            )
        suggestions = self._build_suggestions(
            bootstrap_status=bootstrap_status,
            skill_status_counts=skill_status_counts,
            mcp_states=mcp_states,
            mcp_catalog_issues=mcp_catalog_issues,
            integrations=integrations,
            optional_dependencies=optional_dependencies,
            probe_mcp=probe_mcp,
        )
        return {
            "workspace": {
                "root": str(settings.workspace_root),
                "state_dir": str(settings.state_dir),
                "user_state_dir": str(settings.user_state_dir),
                "audit_log_file": str(settings.audit_log_file),
            },
            "runtime": {
                "provider": settings.provider,
                "model": settings.model,
                "permission_mode": settings.permission_mode,
                "sandbox_enabled": settings.sandbox_enabled,
                "sandbox_backend": settings.sandbox_backend,
                "profile": settings.active_profile,
                "fallbacks": list(settings.provider_fallbacks),
            },
            "bootstrap": bootstrap_status,
            "skills": {
                "total": len(skills),
                "readiness": skill_status_counts,
            },
            "mcp": {
                "total": len(mcp_states),
                "status_counts": mcp_status_counts,
                "probed": probe_mcp,
                "catalog_issues": mcp_catalog_issues,
            },
            "integrations": integrations,
            "dependencies": optional_dependencies,
            "issues": issues,
            "suggestions": suggestions,
        }

    def _module_status(self, name: str) -> dict[str, object]:
        return {
            "name": name,
            "available": find_spec(name) is not None,
        }

    def _command_status(self, name: str) -> dict[str, object]:
        resolved = shutil.which(name)
        return {
            "name": name,
            "available": bool(resolved),
            "path": resolved or "",
        }

    def _build_suggestions(
        self,
        *,
        bootstrap_status: dict[str, Any],
        skill_status_counts: dict[str, int],
        mcp_states: list[Any],
        mcp_catalog_issues: list[dict[str, str]],
        integrations: dict[str, Any],
        optional_dependencies: dict[str, dict[str, object]],
        probe_mcp: bool,
    ) -> list[dict[str, str]]:
        suggestions: list[dict[str, str]] = []
        if int(bootstrap_status.get("present_count", 0)) == 0:
            suggestions.append(
                {
                    "severity": "high",
                    "title": "Initialize workspace bootstrap files",
                    "command": "eh setup",
                    "reason": "Workspace guidance files such as AGENTS.md and STANDING_ORDERS.md are missing.",
                }
            )
        elif int(bootstrap_status.get("missing_count", 0)) > 0:
            suggestions.append(
                {
                    "severity": "medium",
                    "title": "Complete missing workspace bootstrap files",
                    "command": "eh setup",
                    "reason": "Some recommended workspace guidance files are still missing.",
                }
            )
        if skill_status_counts.get("setup-needed", 0):
            suggestions.append(
                {
                    "severity": "medium",
                    "title": "Review skills that still need setup",
                    "command": "eh tool SkillGovernanceReport '{}'",
                    "reason": "%s installed skills are not ready yet."
                    % skill_status_counts.get("setup-needed", 0),
                }
            )
        if not bool(optional_dependencies.get("prompt_toolkit", {}).get("available", False)):
            suggestions.append(
                {
                    "severity": "medium",
                    "title": "Install prompt_toolkit for better REPL UX",
                    "command": "python3 -m pip install prompt_toolkit",
                    "reason": "Command completion and interactive menus fall back to the basic REPL without it.",
                }
            )
        if not bool(optional_dependencies.get("playwright", {}).get("available", False)):
            suggestions.append(
                {
                    "severity": "low",
                    "title": "Install Playwright for browser automation",
                    "command": "python3 -m pip install playwright && playwright install",
                    "reason": "BrowserAction remains setup-needed until Playwright is installed.",
                }
            )
        if not bool(optional_dependencies.get("ffmpeg", {}).get("available", False)):
            suggestions.append(
                {
                    "severity": "low",
                    "title": "Install ffmpeg for video inspection and frame sampling",
                    "command": self._ffmpeg_install_command(),
                    "reason": "Video tools need ffmpeg and ffprobe to inspect media and sample frames.",
                }
            )
        missing_command_states = [item for item in mcp_states if getattr(item, "status", "") == "missing-command"]
        if missing_command_states:
            suggestions.append(
                {
                    "severity": "high",
                    "title": "Install or disable MCP servers with missing stdio commands",
                    "command": "eh mcp",
                    "reason": "%s MCP server(s) reference commands that are not installed on this machine."
                    % len(missing_command_states),
                }
            )
        auth_required_states = [item for item in mcp_states if getattr(item, "status", "") == "auth-required"]
        if auth_required_states:
            suggestions.append(
                {
                    "severity": "medium",
                    "title": "Configure credentials for authenticated MCP servers",
                    "command": "eh doctor --probe",
                    "reason": "%s MCP server(s) responded but still require credentials or headers."
                    % len(auth_required_states),
                }
            )
        unreachable_states = [item for item in mcp_states if getattr(item, "status", "") == "unreachable"]
        if probe_mcp and unreachable_states:
            suggestions.append(
                {
                    "severity": "medium",
                    "title": "Inspect unreachable MCP endpoints",
                    "command": "eh mcp",
                    "reason": "%s probed MCP server(s) were unreachable; verify URLs, network access, or service health."
                    % len(unreachable_states),
                }
            )
        if mcp_catalog_issues:
            suggestions.append(
                {
                    "severity": "medium",
                    "title": "Repair malformed MCP catalog files",
                    "command": "eh doctor --json",
                    "reason": "%s MCP catalog file(s) were skipped while loading; inspect `mcp.catalog_issues` for paths and parser errors."
                    % len(mcp_catalog_issues),
                }
            )
        if integrations.get("status_counts", {}).get("invalid-config", 0):
            suggestions.append(
                {
                    "severity": "medium",
                    "title": "Repair invalid integration configuration",
                    "command": "eh integrations",
                    "reason": "%s configured integration(s) need valid webhook or channel settings."
                    % integrations["status_counts"].get("invalid-config", 0),
                }
            )
        return suggestions

    def _ffmpeg_install_command(self) -> str:
        system = platform.system().lower()
        if system == "darwin":
            return "brew install ffmpeg"
        if system == "linux":
            return "sudo apt-get install ffmpeg"
        if system == "windows":
            return "winget install Gyan.FFmpeg"
        return "Install ffmpeg with your system package manager"
