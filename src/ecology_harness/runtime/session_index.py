from __future__ import annotations

from dataclasses import dataclass, field
import sqlite3
from pathlib import Path
import threading
from typing import Any

from ecology_harness.runtime.messages import ChatMessage
from ecology_harness.runtime.session_store import ManagedSession
from ecology_harness.skills.retrieval import tokenize_text


@dataclass
class IndexedSessionMessageMatch:
    message_index: int
    role: str
    score: float
    excerpt: str
    matched_terms: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "message_index": self.message_index,
            "role": self.role,
            "score": round(self.score, 4),
            "excerpt": self.excerpt,
            "matched_terms": list(self.matched_terms),
        }


@dataclass
class IndexedSessionHit:
    session_id: str
    score: float
    title: str
    recap: str
    updated_at: str
    created_at: str
    message_count: int
    parent_session_id: str = ""
    matches: list[IndexedSessionMessageMatch] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "score": round(self.score, 4),
            "title": self.title,
            "recap": self.recap,
            "updated_at": self.updated_at,
            "created_at": self.created_at,
            "message_count": self.message_count,
            "parent_session_id": self.parent_session_id,
            "matches": [item.to_dict() for item in self.matches],
        }


class SessionIndex:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._fts_enabled = True
        self._initialize()

    def _initialize(self) -> None:
        with self._lock:
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    title TEXT NOT NULL,
                    recap TEXT NOT NULL,
                    parent_session_id TEXT NOT NULL,
                    message_count INTEGER NOT NULL
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    session_id TEXT NOT NULL,
                    message_index INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    excerpt TEXT NOT NULL,
                    content TEXT NOT NULL,
                    PRIMARY KEY (session_id, message_index)
                )
                """
            )
            try:
                self._conn.execute(
                    """
                    CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts
                    USING fts5(session_id UNINDEXED, message_index UNINDEXED, role, excerpt, content)
                    """
                )
            except sqlite3.OperationalError:
                self._fts_enabled = False
            self._conn.commit()

    def index_session(self, session: ManagedSession) -> None:
        parent_session_id = session.fork.parent_session_id if session.fork else ""
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO sessions (session_id, created_at, updated_at, title, recap, parent_session_id, message_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    created_at=excluded.created_at,
                    updated_at=excluded.updated_at,
                    title=excluded.title,
                    recap=excluded.recap,
                    parent_session_id=excluded.parent_session_id,
                    message_count=excluded.message_count
                """,
                (
                    session.session_id,
                    session.created_at,
                    session.updated_at,
                    session.title,
                    session.recap,
                    parent_session_id,
                    len(session.messages),
                ),
            )
            self._conn.execute("DELETE FROM messages WHERE session_id = ?", (session.session_id,))
            if self._fts_enabled:
                self._conn.execute("DELETE FROM messages_fts WHERE session_id = ?", (session.session_id,))
            for index, message in enumerate(session.messages):
                if message.role == "system":
                    continue
                excerpt = _excerpt(message)
                content = message.summary_text(max_document_chars=4000).strip()
                self._conn.execute(
                    """
                    INSERT INTO messages (session_id, message_index, role, excerpt, content)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (session.session_id, index, message.role, excerpt, content),
                )
                if self._fts_enabled:
                    self._conn.execute(
                        """
                        INSERT INTO messages_fts (session_id, message_index, role, excerpt, content)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (session.session_id, index, message.role, excerpt, content),
                    )
            self._conn.commit()

    def stats(self) -> dict[str, Any]:
        with self._lock:
            session_count = int(self._conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0])
            message_count = int(self._conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0])
            newest = self._conn.execute(
                "SELECT session_id, title, updated_at FROM sessions ORDER BY updated_at DESC LIMIT 1"
            ).fetchone()
        return {
            "session_count": session_count,
            "indexed_message_count": message_count,
            "newest_session_id": str(newest["session_id"]) if newest else "",
            "newest_title": str(newest["title"]) if newest else "",
            "fts_enabled": self._fts_enabled,
        }

    def search(self, query: str, limit: int = 5, exclude_session_id: str = "") -> list[IndexedSessionHit]:
        normalized = query.strip()
        if not normalized:
            return []
        with self._lock:
            if self._fts_enabled:
                try:
                    hits = self._search_fts(normalized, limit=limit, exclude_session_id=exclude_session_id)
                except sqlite3.OperationalError:
                    hits = []
                if hits:
                    return hits
            return self._search_like(normalized, limit=limit, exclude_session_id=exclude_session_id)

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def _search_fts(self, query: str, limit: int, exclude_session_id: str) -> list[IndexedSessionHit]:
        normalized_query = _normalize_fts_query(query)
        if not normalized_query:
            return []
        rows = self._conn.execute(
            """
            SELECT
                s.session_id,
                s.title,
                s.recap,
                s.updated_at,
                s.created_at,
                s.message_count,
                s.parent_session_id,
                m.message_index,
                m.role,
                m.excerpt,
                bm25(messages_fts) AS score
            FROM messages_fts
            JOIN sessions s ON s.session_id = messages_fts.session_id
            JOIN messages m
              ON m.session_id = messages_fts.session_id
             AND m.message_index = messages_fts.message_index
            WHERE messages_fts MATCH ?
              AND (? = '' OR s.session_id != ?)
            ORDER BY score ASC
            LIMIT ?
            """,
            (normalized_query, exclude_session_id, exclude_session_id, max(limit * 8, limit)),
        ).fetchall()
        return self._coalesce_hits(rows, score_transform=lambda value: 1.0 / (1.0 + max(value, 0.0)), limit=limit, query=query)

    def _search_like(self, query: str, limit: int, exclude_session_id: str) -> list[IndexedSessionHit]:
        tokens = list(dict.fromkeys(tokenize_text(query)))
        search_terms = tokens or [query]
        clauses: list[str] = []
        parameters: list[Any] = []
        for term in search_terms[:16]:
            pattern = "%%%s%%" % term
            clauses.append("(m.content LIKE ? OR m.excerpt LIKE ? OR s.title LIKE ? OR s.recap LIKE ?)")
            parameters.extend([pattern, pattern, pattern, pattern])
        where_clause = " OR ".join(clauses) if clauses else "1 = 0"
        rows = self._conn.execute(
            f"""
            SELECT
                s.session_id,
                s.title,
                s.recap,
                s.updated_at,
                s.created_at,
                s.message_count,
                s.parent_session_id,
                m.message_index,
                m.role,
                m.excerpt
            FROM messages m
            JOIN sessions s ON s.session_id = m.session_id
            WHERE ({where_clause})
              AND (? = '' OR s.session_id != ?)
            ORDER BY s.updated_at DESC, m.message_index DESC
            LIMIT ?
            """,
            tuple(parameters + [exclude_session_id, exclude_session_id, max(limit * 8, limit)]),
        ).fetchall()
        return self._coalesce_hits(rows, score_transform=lambda value: 1.0, limit=limit, query=query)

    def _coalesce_hits(self, rows: list[sqlite3.Row], score_transform, limit: int, query: str) -> list[IndexedSessionHit]:
        hits: dict[str, IndexedSessionHit] = {}
        query_terms = tokenize_text(query)
        for row in rows:
            session_id = str(row["session_id"])
            if session_id not in hits:
                hits[session_id] = IndexedSessionHit(
                    session_id=session_id,
                    score=0.0,
                    title=str(row["title"] or ""),
                    recap=str(row["recap"] or ""),
                    updated_at=str(row["updated_at"] or ""),
                    created_at=str(row["created_at"] or ""),
                    message_count=int(row["message_count"] or 0),
                    parent_session_id=str(row["parent_session_id"] or ""),
                    matches=[],
                )
            hit = hits[session_id]
            raw_score = float(row["score"]) if "score" in row.keys() and row["score"] is not None else 0.0
            hit.score += float(score_transform(raw_score))
            excerpt = str(row["excerpt"] or "")
            matched_terms = [term for term in query_terms if term in excerpt.lower()]
            hit.matches.append(
                IndexedSessionMessageMatch(
                    message_index=int(row["message_index"] or 0),
                    role=str(row["role"] or ""),
                    score=float(score_transform(raw_score)),
                    excerpt=excerpt,
                    matched_terms=list(dict.fromkeys(matched_terms))[:8],
                )
            )
        values = list(hits.values())
        for hit in values:
            hit.matches.sort(key=lambda item: (-item.score, item.message_index))
            hit.matches = hit.matches[:3]
        values.sort(key=lambda item: (-item.score, item.updated_at, item.session_id))
        return values[:limit]


def _excerpt(message: ChatMessage, limit: int = 220) -> str:
    text = message.summary_text(max_document_chars=180).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _normalize_fts_query(query: str, limit: int = 24) -> str:
    tokens = list(dict.fromkeys(tokenize_text(query)))
    if not tokens:
        fallback = query.replace('"', " ").replace(":", " ").strip()
        return fallback
    sanitized: list[str] = []
    for token in tokens[:limit]:
        cleaned = token.replace('"', " ").replace(":", " ").strip()
        if not cleaned:
            continue
        sanitized.append('"%s"' % cleaned)
    return " OR ".join(sanitized)
