from __future__ import annotations

from dataclasses import dataclass, field

from ecology_harness.memory.manager import MemoryManager
from ecology_harness.memory.providers.base import MemoryProviderHit
from ecology_harness.runtime.messages import ChatMessage
from ecology_harness.skills.retrieval import tokenize_text


@dataclass
class BuiltinMemoryProvider:
    manager: MemoryManager
    name: str = "builtin-memory"
    _last_query: str = field(default="", init=False, repr=False)
    _last_hits: list[MemoryProviderHit] = field(default_factory=list, init=False, repr=False)

    def queue_prefetch(
        self,
        query: str,
        conversation: list[ChatMessage] | None = None,
    ) -> None:
        del conversation
        self._last_query = query

    def prefetch(
        self,
        query: str,
        conversation: list[ChatMessage] | None = None,
    ) -> None:
        self._last_hits = self.search(query, conversation=conversation, limit=8)

    def sync_turn(self, messages: list[ChatMessage]) -> None:
        del messages
        self._last_query = ""
        self._last_hits = []

    def on_pre_compact(self, messages: list[ChatMessage]) -> None:
        del messages

    def describe(self) -> dict[str, object]:
        return {
            "name": self.name,
            "supports_prefetch": True,
            "supports_sync_turn": True,
        }

    def build_context(
        self,
        query: str,
        conversation: list[ChatMessage] | None = None,
    ) -> str:
        return self.manager.get_memory_context(
            query=query,
            conversation=conversation,
            include_guidance=False,
        )

    def search(
        self,
        query: str,
        conversation: list[ChatMessage] | None = None,
        limit: int = 5,
    ) -> list[MemoryProviderHit]:
        del conversation
        if self._last_hits and self._last_query == query:
            return self._last_hits[:limit]
        query_tokens = tokenize_text(query)
        if not query_tokens:
            return []
        hits: list[MemoryProviderHit] = []
        for item in self.manager.list_items(scope="all"):
            haystack = "\n".join(
                [item.name, item.description, item.memory_type, item.content]
            ).lower()
            matched_terms = [term for term in query_tokens if term in haystack]
            if not matched_terms:
                continue
            hits.append(
                MemoryProviderHit(
                    provider=self.name,
                    title=item.name,
                    description=item.description,
                    content=item.content,
                    score=1.0 + (0.15 * len(set(matched_terms))),
                    source=item.file_path,
                    matched_terms=list(dict.fromkeys(matched_terms))[:8],
                )
                )
        hits.sort(key=lambda item: (-item.score, item.title.lower()))
        self._last_query = query
        self._last_hits = hits
        return hits[:limit]
