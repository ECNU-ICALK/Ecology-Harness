from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ecology_harness.runtime.messages import ChatMessage
from ecology_harness.skills.retrieval import SkillQueryRewrite


@dataclass
class MemoryProviderHit:
    provider: str
    title: str
    description: str
    content: str
    score: float
    source: str = ""
    matched_terms: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "title": self.title,
            "description": self.description,
            "content": self.content,
            "score": round(self.score, 4),
            "source": self.source,
            "matched_terms": self.matched_terms,
        }


@dataclass
class MemoryProviderSearchReport:
    rewrite: SkillQueryRewrite
    hits: list[MemoryProviderHit]
    provider_count: int

    def to_prompt_dict(self) -> dict[str, object]:
        return {
            "original_query": self.rewrite.original_query,
            "rewritten_query": self.rewrite.rewritten_query,
            "expanded_terms": self.rewrite.expanded_terms,
            "provider_count": self.provider_count,
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "query": self.rewrite.to_dict(),
            "provider_count": self.provider_count,
            "hits": [item.to_dict() for item in self.hits],
        }


class BaseMemoryProvider:
    name = "memory-provider"

    def queue_prefetch(
        self,
        query: str,
        conversation: list[ChatMessage] | None = None,
    ) -> None:
        del query, conversation

    def prefetch(
        self,
        query: str,
        conversation: list[ChatMessage] | None = None,
    ) -> None:
        del query, conversation

    def sync_turn(self, messages: list[ChatMessage]) -> None:
        del messages

    def on_pre_compact(self, messages: list[ChatMessage]) -> None:
        del messages

    def build_context(
        self,
        query: str,
        conversation: list[ChatMessage] | None = None,
    ) -> str:
        del query, conversation
        return ""

    def search(
        self,
        query: str,
        conversation: list[ChatMessage] | None = None,
        limit: int = 5,
    ) -> list[MemoryProviderHit]:
        del query, conversation, limit
        return []

    def describe(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "supports_prefetch": self.__class__.queue_prefetch is not BaseMemoryProvider.queue_prefetch,
            "supports_sync_turn": self.__class__.sync_turn is not BaseMemoryProvider.sync_turn,
        }
