from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path
from typing import Any
import uuid

from ecology_harness.runtime.messages import ChatMessage
from ecology_harness.utils import append_text_line, atomic_write_text


@dataclass
class TrajectoryRecord:
    trajectory_id: str
    created_at: str
    session_id: str
    prompt: str
    final_text: str
    messages: list[dict[str, Any]]
    tool_invocations: list[dict[str, Any]]
    events: list[dict[str, Any]]
    compactions: list[dict[str, Any]]
    attachments: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    quality_tags: list[str] = field(default_factory=list)
    task_slice: str = "general"

    def to_dict(self) -> dict[str, Any]:
        return {
            "trajectory_id": self.trajectory_id,
            "created_at": self.created_at,
            "session_id": self.session_id,
            "prompt": self.prompt,
            "final_text": self.final_text,
            "messages": self.messages,
            "tool_invocations": self.tool_invocations,
            "events": self.events,
            "compactions": self.compactions,
            "attachments": self.attachments,
            "metadata": self.metadata,
            "quality_tags": self.quality_tags,
            "task_slice": self.task_slice,
        }


class TrajectoryStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def index_path(self) -> Path:
        return self.root / "trajectories.jsonl"

    def record_path(self, trajectory_id: str) -> Path:
        return self.root / ("%s.json" % trajectory_id)

    def save(
        self,
        session_id: str,
        prompt: str,
        final_text: str,
        messages: list[ChatMessage],
        tool_invocations: list[dict[str, Any]],
        events: list[Any],
        compactions: list[dict[str, Any]],
        attachments: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TrajectoryRecord:
        quality_tags = infer_trajectory_quality_tags(
            prompt=prompt,
            final_text=final_text,
            tool_invocations=tool_invocations,
            attachments=list(attachments or []),
            compactions=compactions,
        )
        task_slice = infer_trajectory_slice(prompt, attachments=list(attachments or []))
        record = TrajectoryRecord(
            trajectory_id=uuid.uuid4().hex[:16],
            created_at=datetime.utcnow().isoformat(timespec="seconds") + "Z",
            session_id=session_id,
            prompt=prompt,
            final_text=final_text,
            messages=[item.to_dict() for item in messages],
            tool_invocations=list(tool_invocations),
            events=[getattr(item, "to_dict", lambda: item)() for item in events],
            compactions=list(compactions),
            attachments=list(attachments or []),
            metadata=dict(metadata or {}),
            quality_tags=quality_tags,
            task_slice=task_slice,
        )
        payload = json.dumps(record.to_dict(), ensure_ascii=False, indent=2)
        atomic_write_text(self.record_path(record.trajectory_id), payload, encoding="utf-8")
        append_text_line(
            self.index_path(),
            json.dumps(record.to_dict(), ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return record

    def list_records(self) -> list[TrajectoryRecord]:
        records: list[TrajectoryRecord] = []
        if not self.index_path().exists():
            return records
        for line in self.index_path().read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            records.append(self._record_from_payload(payload))
        records.sort(key=lambda item: item.created_at, reverse=True)
        return records

    def get(self, trajectory_id: str) -> TrajectoryRecord | None:
        path = self.record_path(trajectory_id)
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        return self._record_from_payload(payload)

    def _record_from_payload(self, payload: dict[str, Any]) -> TrajectoryRecord:
        normalized = dict(payload)
        normalized.setdefault("attachments", [])
        normalized.setdefault("metadata", {})
        normalized.setdefault("quality_tags", [])
        normalized.setdefault("task_slice", infer_trajectory_slice(str(normalized.get("prompt", "")), attachments=normalized.get("attachments", [])))
        return TrajectoryRecord(**normalized)


def infer_trajectory_slice(prompt: str, attachments: list[str] | None = None) -> str:
    text = (prompt or "").lower()
    if any(token in text for token in ("microbial", "微生物", "microbiome", "amplicon")):
        return "microbe"
    if any(token in text for token in ("遥感", "satellite", "geospatial", "gis", "地图")):
        return "geospatial"
    if any(token in text for token in ("simulate", "模拟", "scenario", "model", "模型", "dssat", "apsim")):
        return "simulation"
    if any(token in text for token in ("literature", "文献", "paper", "citation", "综述")):
        return "literature"
    attachments = list(attachments or [])
    if attachments:
        return "multimodal"
    return "general"


def infer_trajectory_quality_tags(
    prompt: str,
    final_text: str,
    tool_invocations: list[dict[str, Any]],
    attachments: list[str],
    compactions: list[dict[str, Any]],
) -> list[str]:
    tags: list[str] = []
    if final_text.strip():
        tags.append("has-final")
    if tool_invocations:
        tags.append("tool-use")
    if attachments:
        tags.append("multimodal")
    if compactions:
        tags.append("compacted")
    if any("Tool error" in str(item.get("output", "")) for item in tool_invocations):
        tags.append("tool-error")
    if any("Permission denied" in str(item.get("output", "")) for item in tool_invocations):
        tags.append("permission-denied")
    tags.append(infer_trajectory_slice(prompt, attachments=attachments))
    return list(dict.fromkeys(tags))
