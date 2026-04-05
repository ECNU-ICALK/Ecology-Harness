from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path
import threading
from typing import Any


VALID_STATUSES = {"pending", "blocked", "in_progress", "completed", "cancelled", "failed"}


@dataclass
class TaskRecord:
    id: str
    subject: str
    description: str
    status: str = "pending"
    active_form: str = ""
    owner: str = ""
    blocks: list[str] = field(default_factory=list)
    blocked_by: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat(timespec="seconds") + "Z")
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat(timespec="seconds") + "Z")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "subject": self.subject,
            "description": self.description,
            "status": self.status,
            "active_form": self.active_form,
            "owner": self.owner,
            "blocks": self.blocks,
            "blocked_by": self.blocked_by,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskRecord":
        return cls(
            id=str(data.get("id", "")),
            subject=data.get("subject", data.get("title", "")),
            description=data.get("description", ""),
            status=data.get("status", "pending"),
            active_form=data.get("active_form", ""),
            owner=data.get("owner", ""),
            blocks=[str(item) for item in data.get("blocks", [])],
            blocked_by=[str(item) for item in data.get("blocked_by", [])],
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", datetime.utcnow().isoformat(timespec="seconds") + "Z"),
            updated_at=data.get("updated_at", datetime.utcnow().isoformat(timespec="seconds") + "Z"),
        )

    def status_icon(self) -> str:
        return {
            "pending": "○",
            "blocked": "◌",
            "in_progress": "●",
            "completed": "✓",
            "cancelled": "✗",
            "failed": "!",
        }.get(self.status, "?")

    def one_line(self, resolved_ids: set[str] | None = None) -> str:
        owner = " (%s)" % self.owner if self.owner else ""
        pending_blockers = [
            item for item in self.blocked_by if resolved_ids is None or item not in resolved_ids
        ]
        blocked = (
            " [blocked by #%s]" % ", #".join(pending_blockers)
            if pending_blockers
            else ""
        )
        return "#%s [%s] %s %s%s%s" % (
            self.id,
            self.status,
            self.status_icon(),
            self.subject,
            owner,
            blocked,
        )


class TaskStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def list_tasks(self) -> list[TaskRecord]:
        with self._lock:
            return [TaskRecord.from_dict(item) for item in self._load()]

    def get(self, task_id: str) -> TaskRecord | None:
        task_id = str(task_id)
        for item in self.list_tasks():
            if item.id == task_id:
                return item
        return None

    def create(
        self,
        subject: str,
        description: str = "",
        active_form: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> TaskRecord:
        with self._lock:
            items = [TaskRecord.from_dict(item) for item in self._load()]
            next_id = str(max([int(item.id) for item in items if item.id.isdigit()] or [0]) + 1)
            task = TaskRecord(
                id=next_id,
                subject=subject,
                description=description,
                active_form=active_form,
                metadata=metadata or {},
            )
            items.append(task)
            self._save(items)
            return task

    def update(
        self,
        task_id: str,
        subject: str | None = None,
        description: str | None = None,
        status: str | None = None,
        active_form: str | None = None,
        owner: str | None = None,
        add_blocks: list[str] | None = None,
        add_blocked_by: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[TaskRecord | None, list[str]]:
        with self._lock:
            items = [TaskRecord.from_dict(item) for item in self._load()]
            index = {item.id: item for item in items}
            task = index.get(str(task_id))
            if task is None:
                return None, []

            updated = []
            if subject is not None and subject != task.subject:
                task.subject = subject
                updated.append("subject")
            if description is not None and description != task.description:
                task.description = description
                updated.append("description")
            if active_form is not None and active_form != task.active_form:
                task.active_form = active_form
                updated.append("active_form")
            if owner is not None and owner != task.owner:
                task.owner = owner
                updated.append("owner")
            if status is not None and status in VALID_STATUSES and status != task.status:
                task.status = status
                updated.append("status")
            if metadata is not None:
                for key, value in metadata.items():
                    if value is None:
                        task.metadata.pop(key, None)
                    else:
                        task.metadata[key] = value
                updated.append("metadata")
            if add_blocks:
                new_values = [str(item) for item in add_blocks if str(item) not in task.blocks]
                if new_values:
                    task.blocks.extend(new_values)
                    for item in new_values:
                        peer = index.get(item)
                        if peer and task.id not in peer.blocked_by:
                            peer.blocked_by.append(task.id)
                    updated.append("blocks")
            if add_blocked_by:
                new_values = [str(item) for item in add_blocked_by if str(item) not in task.blocked_by]
                if new_values:
                    task.blocked_by.extend(new_values)
                    for item in new_values:
                        peer = index.get(item)
                        if peer and task.id not in peer.blocks:
                            peer.blocks.append(task.id)
                    updated.append("blocked_by")

            if updated:
                task.updated_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"
                self._save(items)
            return task, updated

    def _load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            return raw.get("tasks", [])
        return raw

    def _save(self, items: list[TaskRecord]) -> None:
        payload = {"tasks": [item.to_dict() for item in items]}
        self.path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
