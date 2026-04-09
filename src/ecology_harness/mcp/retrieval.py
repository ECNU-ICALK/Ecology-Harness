from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from ecology_harness.runtime.messages import ChatMessage
from ecology_harness.skills.retrieval import SkillQueryRewrite, SkillQueryRewriter, tokenize_text


class McpServerRecord(Protocol):
    name: str
    transport: str
    description: str
    source: str
    default_enabled: bool
    auth: str
    tools: list[Any]
    resources: list[Any]

    @property
    def tool_prefix(self) -> str: ...


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        normalized = item.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def _build_document_text(server: McpServerRecord) -> str:
    tokens: list[str] = []
    tokens.extend([server.name] * 5)
    tokens.extend([server.tool_prefix] * 2)
    if server.description:
        tokens.extend([server.description] * 3)
    tokens.extend([server.transport, server.auth, server.source])
    for tool in server.tools:
        tokens.extend([tool.name] * 3)
        if tool.description:
            tokens.append(tool.description)
    for resource in server.resources:
        tokens.append(resource.name)
        tokens.append(resource.uri)
        if resource.description:
            tokens.append(resource.description)
    return "\n".join(tokens)


@dataclass
class McpSearchHit:
    server: McpServerRecord
    score: float
    matched_terms: list[str] = field(default_factory=list)
    matched_tools: list[str] = field(default_factory=list)
    matched_resources: list[str] = field(default_factory=list)
    exact_match: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "server_name": self.server.name,
            "transport": self.server.transport,
            "description": self.server.description,
            "source": self.server.source,
            "enabled": self.server.default_enabled,
            "tool_prefix": self.server.tool_prefix,
            "tool_count": len(self.server.tools),
            "resource_count": len(self.server.resources),
            "auth": self.server.auth,
            "score": round(self.score, 4),
            "matched_terms": self.matched_terms,
            "matched_tools": self.matched_tools,
            "matched_resources": self.matched_resources,
            "exact_match": self.exact_match,
        }


@dataclass
class McpSearchReport:
    rewrite: SkillQueryRewrite
    hits: list[McpSearchHit]
    total_servers: int
    fallback_used: bool = False

    def to_prompt_dict(self) -> dict[str, Any]:
        return {
            "original_query": self.rewrite.original_query,
            "rewritten_query": self.rewrite.rewritten_query,
            "context_snippets": self.rewrite.context_snippets,
            "expanded_terms": self.rewrite.expanded_terms,
            "total_servers": self.total_servers,
            "fallback_used": self.fallback_used,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.rewrite.to_dict(),
            "total_servers": self.total_servers,
            "fallback_used": self.fallback_used,
            "hits": [item.to_dict() for item in self.hits],
        }


class McpBM25Retriever:
    def __init__(self, servers: list[McpServerRecord], history_turns: int = 4) -> None:
        from ecology_harness.skills.retrieval import SkillBM25Retriever

        self.servers = servers
        self.rewriter = SkillQueryRewriter(history_turns=history_turns)
        self._documents = [_build_document_text(server) for server in servers]
        self._bm25 = SkillBM25Retriever.__new__(SkillBM25Retriever)
        self._bm25.skills = servers
        self._bm25.documents = self._documents
        self._bm25.doc_tokens = [tokenize_text(document) for document in self._documents]
        self._bm25.doc_lengths = [len(tokens) for tokens in self._bm25.doc_tokens]
        self._bm25.avgdl = (
            sum(self._bm25.doc_lengths) / len(self._bm25.doc_lengths)
            if self._bm25.doc_lengths
            else 0.0
        )
        from collections import Counter

        self._bm25.term_freqs = [Counter(tokens) for tokens in self._bm25.doc_tokens]
        self._bm25.doc_freqs = Counter()
        for tokens in self._bm25.doc_tokens:
            self._bm25.doc_freqs.update(set(tokens))

    def search(
        self,
        query: str,
        conversation: list[ChatMessage] | None = None,
        limit: int = 6,
    ) -> McpSearchReport:
        rewrite = self.rewriter.rewrite(query, conversation=conversation)
        query_tokens = rewrite.query_tokens
        if not self.servers or not query_tokens:
            return McpSearchReport(rewrite=rewrite, hits=[], total_servers=len(self.servers))

        hits: list[McpSearchHit] = []
        query_text = rewrite.rewritten_query.lower()
        for idx, server in enumerate(self.servers):
            score = self._bm25._score_document(idx, query_tokens)  # type: ignore[attr-defined]
            matched_terms = [term for term in query_tokens if term in self._bm25.term_freqs[idx]]
            matched_tools = _unique(
                [
                    tool.name
                    for tool in server.tools
                    if any(term in tokenize_text("%s %s" % (tool.name, tool.description)) for term in query_tokens)
                ]
            )[:6]
            matched_resources = _unique(
                [
                    resource.name
                    for resource in server.resources
                    if any(
                        term in tokenize_text("%s %s %s" % (resource.name, resource.uri, resource.description))
                        for term in query_tokens
                    )
                ]
            )[:4]
            exact_match = False
            if server.name.lower() in query_text or server.tool_prefix.lower() in query_text:
                score += 6.0
                exact_match = True
            if matched_tools:
                score += min(len(matched_tools), 6) * 0.35
            if matched_resources:
                score += min(len(matched_resources), 4) * 0.2
            if matched_terms:
                score += min(len(matched_terms), 8) * 0.1
            if score <= 0:
                continue
            hits.append(
                McpSearchHit(
                    server=server,
                    score=score,
                    matched_terms=_unique(matched_terms)[:8],
                    matched_tools=matched_tools,
                    matched_resources=matched_resources,
                    exact_match=exact_match,
                )
            )
        hits.sort(
            key=lambda item: (
                -item.score,
                0 if item.server.default_enabled else 1,
                0 if item.exact_match else 1,
                item.server.name.lower(),
            )
        )
        return McpSearchReport(
            rewrite=rewrite,
            hits=hits[:limit],
            total_servers=len(self.servers),
            fallback_used=False,
        )
