from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ecology_harness.utils import atomic_write_text


class SkillStateStore:
    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir

    @property
    def snapshot_path(self) -> Path:
        return self.project_dir / ".skill-snapshot.json"

    @property
    def governance_path(self) -> Path:
        return self.project_dir / ".skill-governance.json"

    def load_snapshot(self) -> dict[str, Any] | None:
        path = self.snapshot_path
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
        return payload if isinstance(payload, dict) else None

    def write_snapshot(self, payload: dict[str, Any]) -> None:
        atomic_write_text(
            self.snapshot_path,
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def load_governance(self) -> dict[str, Any]:
        path = self.governance_path
        default = {"version": 1, "skills": {}}
        if not path.exists():
            return dict(default)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return dict(default)
        if not isinstance(payload, dict):
            return dict(default)
        payload.setdefault("version", 1)
        payload.setdefault("skills", {})
        return payload

    def write_governance(self, payload: dict[str, Any]) -> None:
        payload.setdefault("version", 1)
        payload.setdefault("skills", {})
        atomic_write_text(
            self.governance_path,
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
