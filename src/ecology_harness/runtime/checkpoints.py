from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import uuid

from ecology_harness.runtime.messages import ChatMessage
from ecology_harness.utils import atomic_write_text


def _utcnow() -> str:
    return datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass
class CheckpointRecord:
    checkpoint_id: str
    session_id: str
    created_at: str
    stage: str
    summary: str
    metadata: dict
    messages: list[ChatMessage]

    def to_dict(self) -> dict:
        return {
            "checkpoint_id": self.checkpoint_id,
            "session_id": self.session_id,
            "created_at": self.created_at,
            "stage": self.stage,
            "summary": self.summary,
            "metadata": self.metadata,
            "messages": [item.to_dict() for item in self.messages],
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "CheckpointRecord":
        return cls(
            checkpoint_id=str(payload.get("checkpoint_id", "")),
            session_id=str(payload.get("session_id", "")),
            created_at=str(payload.get("created_at", "")),
            stage=str(payload.get("stage", "")),
            summary=str(payload.get("summary", "")),
            metadata=dict(payload.get("metadata", {}) or {}),
            messages=[ChatMessage.from_dict(item) for item in payload.get("messages", [])],
        )


class CheckpointManager:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def create(
        self,
        *,
        session_id: str,
        stage: str,
        messages: list[ChatMessage],
        metadata: dict | None = None,
        summary: str = "",
    ) -> CheckpointRecord:
        checkpoint = CheckpointRecord(
            checkpoint_id="ckpt_%s" % uuid.uuid4().hex[:12],
            session_id=session_id,
            created_at=_utcnow(),
            stage=stage,
            summary=summary.strip() or stage,
            metadata=dict(metadata or {}),
            messages=list(messages),
        )
        atomic_write_text(
            self.path_for(checkpoint.checkpoint_id),
            json.dumps(checkpoint.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return checkpoint

    def get(self, checkpoint_id: str) -> CheckpointRecord | None:
        path = self.path_for(checkpoint_id)
        if not path.exists():
            return None
        return CheckpointRecord.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def list(self, session_id: str = "", limit: int = 50) -> list[CheckpointRecord]:
        items: list[CheckpointRecord] = []
        for path in sorted(self.directory.glob("checkpoint-*.json"), reverse=True):
            try:
                record = CheckpointRecord.from_dict(json.loads(path.read_text(encoding="utf-8")))
            except Exception:
                continue
            if session_id and record.session_id != session_id:
                continue
            items.append(record)
            if len(items) >= limit:
                break
        items.sort(key=lambda item: (item.created_at, item.checkpoint_id), reverse=True)
        return items

    def restore(self, checkpoint_id: str) -> list[ChatMessage]:
        record = self.get(checkpoint_id)
        if record is None:
            raise ValueError("Checkpoint not found: %s" % checkpoint_id)
        return list(record.messages)

    def path_for(self, checkpoint_id: str) -> Path:
        return self.directory / ("checkpoint-%s.json" % checkpoint_id)
