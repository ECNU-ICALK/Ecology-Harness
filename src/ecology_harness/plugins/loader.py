from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import subprocess
from typing import Any

from ecology_harness.utils import slugify


PLUGIN_MANIFEST_DIRS = (".claude-plugin", ".ecology-plugin")


@dataclass
class PluginManifest:
    slug: str
    name: str
    version: str
    description: str
    source: str
    root: Path
    manifest_path: Path
    default_enabled: bool
    hooks: dict[str, list[str]] = field(default_factory=dict)
    tools: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    mcp_servers: list[str] = field(default_factory=list)

    def to_index_dict(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "source": self.source,
            "default_enabled": self.default_enabled,
            "hooks": self.hooks,
            "tools": self.tools,
            "skills": self.skills,
            "mcp_servers": self.mcp_servers,
            "root": str(self.root),
            "manifest_path": str(self.manifest_path),
        }


@dataclass
class PluginRuntimeState:
    slug: str
    enabled: bool
    status: str = "healthy"
    last_error: str = ""

    def to_dict(self) -> dict[str, str | bool]:
        return {
            "slug": self.slug,
            "enabled": self.enabled,
            "status": self.status,
            "last_error": self.last_error,
        }


class PluginManager:
    def __init__(self, builtin_dir: Path, user_dir: Path, project_dir: Path) -> None:
        self.builtin_dir = builtin_dir
        self.user_dir = user_dir
        self.project_dir = project_dir
        self.user_dir.mkdir(parents=True, exist_ok=True)
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self._runtime_state: dict[str, PluginRuntimeState] = {}

    def list_plugins(self) -> list[PluginManifest]:
        seen: dict[str, PluginManifest] = {}
        for source, root in (
            ("builtin", self.builtin_dir),
            ("user", self.user_dir),
            ("project", self.project_dir),
        ):
            if not root.exists():
                continue
            for manifest_path in self._find_manifests(root):
                plugin = self._load_manifest(manifest_path, source)
                seen[plugin.slug] = plugin
                self._runtime_state.setdefault(
                    plugin.slug,
                    PluginRuntimeState(slug=plugin.slug, enabled=plugin.default_enabled),
                )
        return sorted(seen.values(), key=lambda item: item.name.lower())

    def get(self, slug_or_name: str) -> PluginManifest | None:
        normalized = slugify(slug_or_name)
        for item in self.list_plugins():
            if item.slug == normalized or item.name == slug_or_name:
                return item
        return None

    def list_enabled_plugins(self) -> list[PluginManifest]:
        enabled = []
        for plugin in self.list_plugins():
            state = self._runtime_state.get(plugin.slug)
            if state is None:
                state = PluginRuntimeState(slug=plugin.slug, enabled=plugin.default_enabled)
                self._runtime_state[plugin.slug] = state
            if state.enabled:
                enabled.append(plugin)
        return enabled

    def list_runtime_states(self) -> list[PluginRuntimeState]:
        for item in self.list_plugins():
            self._runtime_state.setdefault(
                item.slug,
                PluginRuntimeState(slug=item.slug, enabled=item.default_enabled),
            )
        return sorted(self._runtime_state.values(), key=lambda item: item.slug)

    def collect_hooks(self, event_name: str) -> list[tuple[PluginManifest, Path]]:
        hooks: list[tuple[PluginManifest, Path]] = []
        for plugin in self.list_enabled_plugins():
            for relative in plugin.hooks.get(event_name, []):
                script = (plugin.root / relative).resolve()
                if script.exists():
                    hooks.append((plugin, script))
        return hooks

    def run_hooks(
        self,
        event_name: str,
        payload: dict[str, Any],
        workspace_root: Path,
        timeout_sec: int,
    ) -> list[dict[str, Any]]:
        results = []
        for plugin, script in self.collect_hooks(event_name):
            env = {
                "EH_PLUGIN_NAME": plugin.name,
                "EH_HOOK_EVENT": event_name,
                "EH_WORKSPACE_ROOT": str(workspace_root),
                "EH_PAYLOAD_JSON": json.dumps(payload, ensure_ascii=False),
                "EH_TOOL_NAME": str(payload.get("tool", "")),
                "EH_TOOL_ARGS_JSON": json.dumps(payload.get("arguments", {}), ensure_ascii=False),
                "EH_TOOL_OUTPUT": str(payload.get("output", "")),
            }
            command = [str(script)]
            if script.suffix in {".sh", ".bash"}:
                command = ["/bin/bash", str(script)]
            try:
                completed = subprocess.run(
                    command,
                    cwd=str(workspace_root),
                    env={**os.environ, **env},
                    capture_output=True,
                    text=True,
                    timeout=timeout_sec,
                )
                status = "healthy" if completed.returncode == 0 else "degraded"
                error = ""
                if completed.returncode != 0:
                    error = (completed.stderr or completed.stdout).strip()
                self._runtime_state[plugin.slug] = PluginRuntimeState(
                    slug=plugin.slug,
                    enabled=True,
                    status=status,
                    last_error=error,
                )
                results.append(
                    {
                        "plugin": plugin.slug,
                        "script": str(script),
                        "returncode": completed.returncode,
                        "stdout": (completed.stdout or "").strip(),
                        "stderr": (completed.stderr or "").strip(),
                    }
                )
            except Exception as exc:
                self._runtime_state[plugin.slug] = PluginRuntimeState(
                    slug=plugin.slug,
                    enabled=True,
                    status="failed",
                    last_error=str(exc),
                )
                results.append(
                    {
                        "plugin": plugin.slug,
                        "script": str(script),
                        "returncode": -1,
                        "stdout": "",
                        "stderr": str(exc),
                    }
                )
        return results

    def _find_manifests(self, root: Path) -> list[Path]:
        manifests = []
        for path in root.rglob("plugin.json"):
            parts = set(path.parts)
            if any(marker in parts for marker in PLUGIN_MANIFEST_DIRS) or path.parent == root:
                manifests.append(path)
        return sorted(dict.fromkeys(manifests))

    def _load_manifest(self, manifest_path: Path, source: str) -> PluginManifest:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        name = raw.get("name", manifest_path.parent.parent.name or manifest_path.parent.name)
        slug = slugify(raw.get("slug", name))
        default_enabled = raw.get("defaultEnabled")
        if default_enabled is None:
            default_enabled = raw.get("default_enabled")
        if default_enabled is None:
            default_enabled = source != "builtin"
        root = manifest_path.parent.parent if manifest_path.parent.name in PLUGIN_MANIFEST_DIRS else manifest_path.parent
        return PluginManifest(
            slug=slug,
            name=name,
            version=str(raw.get("version", "0.1.0")),
            description=str(raw.get("description", "")),
            source=source,
            root=root,
            manifest_path=manifest_path,
            default_enabled=bool(default_enabled),
            hooks={key: list(value or []) for key, value in dict(raw.get("hooks", {})).items()},
            tools=[str(item) for item in raw.get("tools", []) or []],
            skills=[str(item) for item in raw.get("skills", []) or []],
            mcp_servers=[str(item) for item in raw.get("mcpServers", raw.get("mcp_servers", [])) or []],
        )
