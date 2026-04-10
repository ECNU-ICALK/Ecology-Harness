from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ecology_harness.memory.providers.base import MemoryProviderHit
from ecology_harness.runtime.messages import ChatMessage
from ecology_harness.skills.retrieval import tokenize_text
from ecology_harness.utils import atomic_write_text, dump_frontmatter, parse_frontmatter


@dataclass
class MarkdownProfileProvider:
    name: str
    path: Path
    title: str
    description: str
    _last_query: str = field(default="", init=False, repr=False)
    _last_hits: list[MemoryProviderHit] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.write("", self.description)

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
        self._last_hits = self.search(query, conversation=conversation, limit=3)

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
        del conversation
        hit = self.search(query, limit=1)
        if hit:
            item = hit[0]
            content = item.content.strip()
            if content:
                return "## %s\n%s" % (self.title, content)
        return ""

    def search(
        self,
        query: str,
        conversation: list[ChatMessage] | None = None,
        limit: int = 5,
    ) -> list[MemoryProviderHit]:
        del conversation
        if self._last_hits and self._last_query == query:
            return self._last_hits[:limit]
        metadata, content = self.read()
        haystack = " ".join(
            [
                self.title,
                self.description,
                str(metadata.get("description", "")),
                content,
            ]
        ).lower()
        query_tokens = tokenize_text(query)
        if not query_tokens:
            return []
        matched_terms = [term for term in query_tokens if term in haystack]
        if not matched_terms:
            return []
        hits = [
            MemoryProviderHit(
                provider=self.name,
                title=self.title,
                description=self.description,
                content=content.strip(),
                score=1.0 + (0.15 * len(set(matched_terms))),
                source=str(self.path),
                matched_terms=list(dict.fromkeys(matched_terms)),
            )
        ]
        self._last_query = query
        self._last_hits = hits
        return hits[:limit]

    def read(self) -> tuple[dict[str, str], str]:
        raw = self.path.read_text(encoding="utf-8")
        metadata, body = parse_frontmatter(raw)
        return metadata, body.strip()

    def write(self, content: str, description: str | None = None) -> None:
        metadata = {
            "name": self.title,
            "description": description or self.description,
            "provider": self.name,
        }
        atomic_write_text(
            self.path,
            dump_frontmatter(metadata, content.strip()),
            encoding="utf-8",
        )
