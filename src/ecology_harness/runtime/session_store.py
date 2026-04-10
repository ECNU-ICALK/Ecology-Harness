from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import uuid

from ecology_harness.runtime.messages import ChatMessage


SESSION_VERSION = 1
LATEST_SESSION_REFERENCE = "latest"


@dataclass
class SessionCompactionRecord:
    count: int = 0
    removed_message_count: int = 0
    summary: str = ""
    compressed_summary: str = ""
    token_estimate_before: int = 0
    token_estimate_after: int = 0
    updated_at: str = ""

    def to_dict(self) -> dict:
        return {
            "count": self.count,
            "removed_message_count": self.removed_message_count,
            "summary": self.summary,
            "compressed_summary": self.compressed_summary,
            "token_estimate_before": self.token_estimate_before,
            "token_estimate_after": self.token_estimate_after,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "SessionCompactionRecord":
        return cls(
            count=int(payload.get("count", 0)),
            removed_message_count=int(payload.get("removed_message_count", 0)),
            summary=str(payload.get("summary", "")),
            compressed_summary=str(payload.get("compressed_summary", "")),
            token_estimate_before=int(payload.get("token_estimate_before", 0)),
            token_estimate_after=int(payload.get("token_estimate_after", 0)),
            updated_at=str(payload.get("updated_at", "")),
        )


@dataclass
class SessionForkRecord:
    parent_session_id: str = ""
    branch_name: str = ""

    def to_dict(self) -> dict:
        return {
            "parent_session_id": self.parent_session_id,
            "branch_name": self.branch_name,
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "SessionForkRecord":
        return cls(
            parent_session_id=str(payload.get("parent_session_id", "")),
            branch_name=str(payload.get("branch_name", "")),
        )


@dataclass
class ManagedSession:
    session_id: str
    created_at: str
    updated_at: str
    messages: list[ChatMessage]
    title: str = ""
    recap: str = ""
    compaction: SessionCompactionRecord | None = None
    fork: SessionForkRecord | None = None
    version: int = SESSION_VERSION

    def to_dict(self) -> dict:
        payload = {
            "version": self.version,
            "session_id": self.session_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "title": self.title,
            "recap": self.recap,
            "message_count": len(self.messages),
            "messages": [item.to_dict() for item in self.messages],
        }
        if self.compaction is not None:
            payload["compaction"] = self.compaction.to_dict()
        if self.fork is not None:
            payload["fork"] = self.fork.to_dict()
        return payload

    @classmethod
    def from_dict(cls, payload: dict) -> "ManagedSession":
        messages = [ChatMessage.from_dict(item) for item in payload.get("messages", [])]
        compaction_payload = payload.get("compaction")
        fork_payload = payload.get("fork")
        return cls(
            version=int(payload.get("version", SESSION_VERSION)),
            session_id=str(payload.get("session_id", create_session_id())),
            created_at=str(payload.get("created_at", current_timestamp())),
            updated_at=str(payload.get("updated_at", current_timestamp())),
            title=str(payload.get("title", "")),
            recap=str(payload.get("recap", "")),
            messages=messages,
            compaction=(
                SessionCompactionRecord.from_dict(compaction_payload)
                if isinstance(compaction_payload, dict)
                else None
            ),
            fork=SessionForkRecord.from_dict(fork_payload) if isinstance(fork_payload, dict) else None,
        )


@dataclass
class ManagedSessionSummary:
    session_id: str
    path: Path
    updated_at: str
    message_count: int
    title: str = ""
    recap: str = ""
    parent_session_id: str = ""


class SessionStore:
    def __init__(self, session_dir: Path) -> None:
        self.session_dir = session_dir
        self.session_dir.mkdir(parents=True, exist_ok=True)

    def latest_path(self) -> Path:
        return self.session_dir / "latest.json"

    def session_path(self, session_id: str) -> Path:
        return self.session_dir / ("session-%s.json" % session_id)

    def create_empty(self, fork: SessionForkRecord | None = None) -> ManagedSession:
        session_id = create_session_id()
        now = current_timestamp()
        return ManagedSession(
            session_id=session_id,
            created_at=now,
            updated_at=now,
            messages=[],
            title="",
            recap="",
            fork=fork,
        )

    def save(
        self,
        session_id: str,
        created_at: str,
        messages: list[ChatMessage],
        title: str = "",
        recap: str = "",
        compaction: dict | None = None,
        fork: dict | None = None,
    ) -> ManagedSession:
        managed = ManagedSession(
            session_id=session_id,
            created_at=created_at or current_timestamp(),
            updated_at=current_timestamp(),
            messages=list(messages),
            title=title,
            recap=recap,
            compaction=(
                SessionCompactionRecord.from_dict(compaction) if isinstance(compaction, dict) else None
            ),
            fork=SessionForkRecord.from_dict(fork) if isinstance(fork, dict) else None,
        )
        payload = json.dumps(managed.to_dict(), indent=2, ensure_ascii=False)
        self.latest_path().write_text(payload, encoding="utf-8")
        self.session_path(session_id).write_text(payload, encoding="utf-8")
        return managed

    def load(self, reference: str = LATEST_SESSION_REFERENCE) -> ManagedSession:
        path = self._resolve_path(reference)
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, list):
            now = current_timestamp()
            return ManagedSession(
                session_id=create_session_id(),
                created_at=now,
                updated_at=now,
                messages=[ChatMessage.from_dict(item) for item in raw],
            )
        if not isinstance(raw, dict):
            raise ValueError("Invalid session payload in %s" % path)
        return ManagedSession.from_dict(raw)

    def list_sessions(self) -> list[ManagedSessionSummary]:
        sessions = []
        for path in sorted(self.session_dir.glob("session-*.json")):
            try:
                managed = self.load(str(path))
            except Exception:
                continue
            sessions.append(
                ManagedSessionSummary(
                    session_id=managed.session_id,
                    path=path,
                    updated_at=managed.updated_at,
                    message_count=len(managed.messages),
                    title=managed.title,
                    recap=managed.recap,
                    parent_session_id=managed.fork.parent_session_id if managed.fork else "",
                )
            )
        if not sessions and self.latest_path().exists():
            try:
                managed = self.load(LATEST_SESSION_REFERENCE)
                sessions.append(
                    ManagedSessionSummary(
                        session_id=managed.session_id,
                        path=self.latest_path(),
                        updated_at=managed.updated_at,
                        message_count=len(managed.messages),
                        title=managed.title,
                        recap=managed.recap,
                        parent_session_id=managed.fork.parent_session_id if managed.fork else "",
                    )
                )
            except Exception:
                pass
        sessions.sort(key=lambda item: (item.updated_at, item.session_id), reverse=True)
        return sessions

    def stats(self) -> dict[str, object]:
        sessions = self.list_sessions()
        total_messages = 0
        lineage_counts: dict[str, int] = {}
        newest = sessions[0] if sessions else None
        for summary in sessions:
            total_messages += int(summary.message_count)
            lineage_id = summary.parent_session_id or summary.session_id
            lineage_counts[lineage_id] = lineage_counts.get(lineage_id, 0) + 1
        hottest_lineage = ""
        if lineage_counts:
            hottest_lineage = sorted(lineage_counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
        return {
            "session_count": len(sessions),
            "message_count": total_messages,
            "newest_session_id": newest.session_id if newest else "",
            "newest_title": newest.title if newest else "",
            "hottest_lineage": hottest_lineage,
        }

    def _resolve_path(self, reference: str) -> Path:
        normalized = (reference or LATEST_SESSION_REFERENCE).strip()
        if normalized in {"", LATEST_SESSION_REFERENCE, "last", "recent"}:
            return self.latest_path()
        direct = Path(normalized).expanduser()
        if direct.exists():
            return direct
        candidate = self.session_path(normalized)
        if candidate.exists():
            return candidate
        if not normalized.endswith(".json"):
            alt = self.session_dir / normalized
            if alt.exists():
                return alt
        raise FileNotFoundError("Session not found: %s" % normalized)


def create_session_id() -> str:
    return uuid.uuid4().hex[:16]


def current_timestamp() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"
