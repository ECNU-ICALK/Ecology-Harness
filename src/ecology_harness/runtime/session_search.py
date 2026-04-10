from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
import math
from typing import Any

from ecology_harness.runtime.compaction import summarize_messages
from ecology_harness.runtime.messages import ChatMessage
from ecology_harness.runtime.session_store import ManagedSession, SessionStore
from ecology_harness.skills.retrieval import SkillQueryRewrite, SkillQueryRewriter, tokenize_text


def _message_excerpt(message: ChatMessage, max_chars: int = 220) -> str:
    text = message.summary_text(max_document_chars=180).strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def _session_preview(messages: list[ChatMessage], max_messages: int = 18) -> str:
    if not messages:
        return ""
    sample = messages[-max_messages:]
    lines: list[str] = []
    for message in sample:
        if message.role == "system":
            continue
        excerpt = _message_excerpt(message)
        if not excerpt:
            continue
        lines.append("%s: %s" % (message.role, excerpt))
    return "\n".join(lines)


def _build_session_document_text(session: ManagedSession) -> str:
    parts: list[str] = [
        session.session_id,
        session.created_at,
        session.updated_at,
    ]
    if session.fork and session.fork.parent_session_id:
        parts.extend([session.fork.parent_session_id] * 2)
        if session.fork.branch_name:
            parts.extend([session.fork.branch_name] * 2)
    if session.compaction:
        parts.extend(
            [
                session.compaction.summary,
                session.compaction.compressed_summary,
            ]
        )
    if session.messages:
        parts.extend(
            [
                _message_excerpt(session.messages[0]),
                _message_excerpt(session.messages[-1]),
            ]
        )
    return "\n".join(item for item in parts if item)


def _message_document_text(message: ChatMessage) -> str:
    excerpt = _message_excerpt(message, max_chars=280)
    if not excerpt:
        return message.role
    # Repeat the role and first excerpt to slightly boost message-type matches.
    return "\n".join([message.role, excerpt, excerpt])


def _trim_lines(lines: list[str], max_lines: int = 4, max_chars: int = 420) -> str:
    selected: list[str] = []
    total_chars = 0
    for line in lines:
        normalized = line.strip()
        if not normalized:
            continue
        if total_chars + len(normalized) > max_chars and selected:
            break
        selected.append(normalized)
        total_chars += len(normalized)
        if len(selected) >= max_lines:
            break
    return "\n".join(selected)


def _lineage_key(session: ManagedSession) -> str:
    if session.fork and session.fork.parent_session_id:
        return session.fork.parent_session_id
    return session.session_id


@dataclass
class SessionMessageMatch:
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
class SessionSearchHit:
    session_id: str
    score: float
    created_at: str
    updated_at: str
    message_count: int
    excerpt: str
    matched_terms: list[str] = field(default_factory=list)
    exact_match: bool = False
    parent_session_id: str = ""
    lineage_id: str = ""
    message_matches: list[SessionMessageMatch] = field(default_factory=list)

    def to_index_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "score": round(self.score, 4),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "message_count": self.message_count,
            "excerpt": self.excerpt,
            "matched_terms": self.matched_terms,
            "exact_match": self.exact_match,
            "parent_session_id": self.parent_session_id,
            "lineage_id": self.lineage_id,
            "message_matches": [item.to_dict() for item in self.message_matches],
        }


@dataclass
class SessionSearchReport:
    rewrite: SkillQueryRewrite
    hits: list[SessionSearchHit]
    total_sessions: int
    fallback_used: bool = False

    def to_prompt_dict(self) -> dict[str, Any]:
        return {
            "original_query": self.rewrite.original_query,
            "rewritten_query": self.rewrite.rewritten_query,
            "expanded_terms": self.rewrite.expanded_terms,
            "context_snippets": self.rewrite.context_snippets,
            "total_sessions": self.total_sessions,
            "fallback_used": self.fallback_used,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.rewrite.to_dict(),
            "total_sessions": self.total_sessions,
            "fallback_used": self.fallback_used,
            "hits": [item.to_index_dict() for item in self.hits],
        }


class SessionSearchEngine:
    def __init__(
        self,
        store: SessionStore,
        history_turns: int = 4,
        max_messages: int = 18,
    ) -> None:
        self.store = store
        self.history_turns = history_turns
        self.max_messages = max_messages

    def search(
        self,
        query: str,
        conversation: list[ChatMessage] | None = None,
        limit: int = 5,
        exclude_session_id: str = "",
    ) -> SessionSearchReport:
        rewriter = SkillQueryRewriter(history_turns=self.history_turns)
        rewrite = rewriter.rewrite(query, conversation=conversation)
        sessions = self._load_sessions(exclude_session_id=exclude_session_id)
        if not sessions:
            return SessionSearchReport(rewrite=rewrite, hits=[], total_sessions=0)
        hits = _SessionRecallRetriever(
            sessions,
            max_messages=self.max_messages,
        ).search(rewrite, limit=max(int(limit), 1))
        return SessionSearchReport(
            rewrite=rewrite,
            hits=hits,
            total_sessions=len(sessions),
            fallback_used=False,
        )

    def select_for_prompt(
        self,
        query: str,
        conversation: list[ChatMessage] | None = None,
        limit: int = 3,
        exclude_session_id: str = "",
    ) -> SessionSearchReport:
        report = self.search(
            query=query,
            conversation=conversation,
            limit=limit,
            exclude_session_id=exclude_session_id,
        )
        if report.hits or not limit:
            return report
        sessions = self._load_sessions(exclude_session_id=exclude_session_id)
        fallback_sessions = sessions[:limit]
        fallback_hits = []
        for session in fallback_sessions:
            fallback_hits.append(
                SessionSearchHit(
                    session_id=session.session_id,
                    score=0.0,
                    created_at=session.created_at,
                    updated_at=session.updated_at,
                    message_count=len(session.messages),
                    excerpt=_session_preview(session.messages, max_messages=self.max_messages),
                    matched_terms=[],
                    exact_match=False,
                    parent_session_id=session.fork.parent_session_id if session.fork else "",
                    lineage_id=_lineage_key(session),
                    message_matches=[],
                )
            )
        report.hits = fallback_hits
        report.fallback_used = bool(fallback_hits)
        return report

    def _load_sessions(self, exclude_session_id: str = "") -> list[ManagedSession]:
        sessions: list[ManagedSession] = []
        for summary in self.store.list_sessions():
            if exclude_session_id and summary.session_id == exclude_session_id:
                continue
            path = summary.path
            try:
                session = self.store.load(str(path))
            except Exception:
                continue
            if exclude_session_id and session.session_id == exclude_session_id:
                continue
            sessions.append(session)
        sessions.sort(key=lambda item: item.updated_at, reverse=True)
        return sessions


@dataclass
class _MessageDocument:
    session_index: int
    message_index: int
    role: str
    excerpt: str
    tokens: list[str]


class _BM25Index:
    def __init__(self, documents: list[list[str]]) -> None:
        self.documents = documents
        self.doc_lengths = [len(tokens) for tokens in documents]
        self.avgdl = sum(self.doc_lengths) / len(self.doc_lengths) if self.doc_lengths else 0.0
        self.term_freqs = [Counter(tokens) for tokens in documents]
        self.doc_freqs: Counter[str] = Counter()
        for tokens in documents:
            self.doc_freqs.update(set(tokens))

    def score_document(
        self,
        doc_index: int,
        query_tokens: list[str],
        k1: float = 1.5,
        b: float = 0.75,
    ) -> float:
        score = 0.0
        freqs = self.term_freqs[doc_index]
        doc_len = self.doc_lengths[doc_index] or 1
        avgdl = self.avgdl or 1.0
        total_docs = len(self.documents) or 1
        for term in query_tokens:
            term_freq = freqs.get(term, 0)
            if not term_freq:
                continue
            doc_freq = self.doc_freqs.get(term, 0)
            idf = math.log(1.0 + ((total_docs - doc_freq + 0.5) / (doc_freq + 0.5)))
            denom = term_freq + k1 * (1.0 - b + b * (doc_len / avgdl))
            score += idf * ((term_freq * (k1 + 1.0)) / denom)
        return score


class _SessionRecallRetriever:
    def __init__(self, sessions: list[ManagedSession], max_messages: int = 18) -> None:
        self.sessions = sessions
        self.max_messages = max_messages
        self.session_texts = [_build_session_document_text(item) for item in sessions]
        self.session_tokens = [tokenize_text(document) for document in self.session_texts]
        self.session_index = _BM25Index(self.session_tokens)

        self.message_docs: list[_MessageDocument] = []
        message_tokens: list[list[str]] = []
        for session_index, session in enumerate(self.sessions):
            for message_index, message in enumerate(session.messages):
                if message.role == "system":
                    continue
                excerpt = _message_excerpt(message, max_chars=220)
                if not excerpt:
                    continue
                doc_tokens = tokenize_text(_message_document_text(message))
                if not doc_tokens:
                    continue
                self.message_docs.append(
                    _MessageDocument(
                        session_index=session_index,
                        message_index=message_index,
                        role=message.role,
                        excerpt=excerpt,
                        tokens=doc_tokens,
                    )
                )
                message_tokens.append(doc_tokens)
        self.message_index = _BM25Index(message_tokens)

    def search(self, rewrite: SkillQueryRewrite, limit: int = 5) -> list[SessionSearchHit]:
        if not self.sessions:
            return []
        query_tokens = rewrite.query_tokens
        if not query_tokens:
            return []

        matches_by_session: dict[int, list[SessionMessageMatch]] = defaultdict(list)
        session_scores: dict[int, float] = defaultdict(float)
        session_terms: dict[int, list[str]] = defaultdict(list)
        session_exact: dict[int, bool] = defaultdict(bool)

        query_text = rewrite.rewritten_query.lower()
        for session_index, session in enumerate(self.sessions):
            session_score = self.session_index.score_document(session_index, query_tokens)
            if session.session_id.lower() in query_text:
                session_score += 4.0
                session_exact[session_index] = True
            matched_terms = [term for term in query_tokens if term in self.session_tokens[session_index]]
            if matched_terms:
                session_score += min(len(set(matched_terms)), 6) * 0.1
                session_terms[session_index].extend(matched_terms)
            if session_score > 0:
                session_scores[session_index] += session_score

        for doc_index, message_doc in enumerate(self.message_docs):
            score = self.message_index.score_document(doc_index, query_tokens)
            if score <= 0:
                continue
            matched_terms = [term for term in query_tokens if term in message_doc.tokens]
            if matched_terms:
                score += min(len(set(matched_terms)), 6) * 0.08
                session_terms[message_doc.session_index].extend(matched_terms)
            matches_by_session[message_doc.session_index].append(
                SessionMessageMatch(
                    message_index=message_doc.message_index,
                    role=message_doc.role,
                    score=score,
                    excerpt=message_doc.excerpt,
                    matched_terms=list(dict.fromkeys(matched_terms))[:8],
                )
            )
            session_scores[message_doc.session_index] += score

        raw_hits: list[SessionSearchHit] = []
        for session_index, session in enumerate(self.sessions):
            score = session_scores.get(session_index, 0.0)
            message_matches = sorted(
                matches_by_session.get(session_index, []),
                key=lambda item: (-item.score, item.message_index),
            )[:3]
            if score <= 0 and not message_matches:
                continue
            exact_match = bool(session_exact.get(session_index))
            summary = _build_focused_summary(session, message_matches)
            raw_hits.append(
                SessionSearchHit(
                    session_id=session.session_id,
                    score=score,
                    created_at=session.created_at,
                    updated_at=session.updated_at,
                    message_count=len(session.messages),
                    excerpt=summary,
                    matched_terms=list(dict.fromkeys(session_terms.get(session_index, [])))[:10],
                    exact_match=exact_match,
                    parent_session_id=session.fork.parent_session_id if session.fork else "",
                    lineage_id=_lineage_key(session),
                    message_matches=message_matches,
                )
            )

        deduped: dict[str, SessionSearchHit] = {}
        for hit in raw_hits:
            lineage_id = hit.lineage_id or hit.session_id
            current = deduped.get(lineage_id)
            if current is None:
                deduped[lineage_id] = hit
                continue
            if (hit.score, hit.updated_at, hit.session_id) > (
                current.score,
                current.updated_at,
                current.session_id,
            ):
                deduped[lineage_id] = hit

        hits = list(deduped.values())
        hits.sort(
            key=lambda item: (
                -item.score,
                0 if item.exact_match else 1,
                item.updated_at,
            ),
            reverse=False,
        )
        return hits[:limit]


def _build_focused_summary(
    session: ManagedSession,
    matches: list[SessionMessageMatch],
) -> str:
    if not matches:
        return _session_preview(session.messages, max_messages=6)

    lines: list[str] = []
    if session.compaction and session.compaction.compressed_summary.strip():
        summary_excerpt = session.compaction.compressed_summary.strip()
        if len(summary_excerpt) > 180:
            summary_excerpt = summary_excerpt[:177].rstrip() + "..."
        lines.append("Earlier compacted context: %s" % summary_excerpt)

    selected_messages: list[ChatMessage] = []
    seen_indexes: set[int] = set()
    for match in matches:
        start = max(match.message_index - 1, 0)
        end = min(match.message_index + 2, len(session.messages))
        for index in range(start, end):
            if index in seen_indexes:
                continue
            candidate = session.messages[index]
            if candidate.role == "system":
                continue
            seen_indexes.add(index)
            selected_messages.append(candidate)

    if selected_messages:
        summary = summarize_messages(selected_messages)
        compact_lines = []
        for raw_line in summary.splitlines():
            normalized = raw_line.strip()
            if not normalized or normalized.lower().startswith("conversation summary"):
                continue
            compact_lines.append(normalized)
        trimmed = _trim_lines(compact_lines, max_lines=3, max_chars=240)
        if trimmed:
            lines.append(trimmed)

    message_lines = []
    for match in matches:
        message_lines.append("%s: %s" % (match.role, match.excerpt))
    trimmed_matches = _trim_lines(message_lines, max_lines=3, max_chars=280)
    if trimmed_matches:
        lines.append("Matched messages:\n%s" % trimmed_matches)

    return "\n".join(line for line in lines if line).strip()


def session_hits_to_prompt_lines(hits: list[SessionSearchHit], limit: int = 3) -> list[str]:
    lines: list[str] = []
    for item in hits[:limit]:
        line = "- %(session_id)s (%(updated_at)s, %(message_count)s msgs): %(excerpt)s" % item.to_index_dict()
        lines.append(line)
    return lines
