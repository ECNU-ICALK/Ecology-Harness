from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ecology_harness.memory.providers.base import (
    BaseMemoryProvider,
    MemoryProviderHit,
    MemoryProviderSearchReport,
)
from ecology_harness.skills.retrieval import SkillQueryRewriter


@dataclass
class MemoryProviderManager:
    providers: list[BaseMemoryProvider]
    history_turns: int = 4
    _last_query: str = ""
    _last_report: MemoryProviderSearchReport | None = None

    def list_providers(self) -> list[str]:
        return [provider.name for provider in self.providers]

    def describe_providers(self) -> list[dict[str, Any]]:
        rows = []
        for provider in self.providers:
            payload = provider.describe()
            payload.setdefault("name", provider.name)
            rows.append(payload)
        return rows

    def queue_prefetch(self, query: str, conversation=None) -> None:
        for provider in self.providers:
            provider.queue_prefetch(query, conversation=conversation)

    def prefetch(self, query: str, conversation=None) -> None:
        for provider in self.providers:
            provider.prefetch(query, conversation=conversation)

    def sync_turn(self, messages) -> None:
        for provider in self.providers:
            provider.sync_turn(messages)

    def on_pre_compact(self, messages) -> None:
        for provider in self.providers:
            provider.on_pre_compact(messages)

    def build_context(
        self,
        query: str,
        conversation=None,
        limit: int = 3,
        max_chars: int = 3_000,
        max_hit_chars: int = 700,
    ) -> str:
        parts: list[str] = []
        primary_hits = self.search(query, conversation=conversation, limit=limit)
        for hit in primary_hits.hits[:limit]:
            if hit.provider == "builtin-memory":
                continue
            if not hit.content.strip():
                continue
            section_lines = ["## %s [%s]" % (hit.title, hit.provider)]
            if hit.description.strip():
                section_lines.append("Summary: %s" % _shorten(hit.description.strip(), 180))
            if hit.matched_terms:
                section_lines.append("Matched terms: %s" % ", ".join(hit.matched_terms[:6]))
            section_lines.append(_shorten(hit.content.strip(), max_hit_chars))
            parts.append("\n".join(section_lines))
        return _fit_blocks_to_budget(parts, max_chars)

    def search(self, query: str, conversation=None, limit: int = 5) -> MemoryProviderSearchReport:
        rewriter = SkillQueryRewriter(history_turns=self.history_turns)
        rewrite = rewriter.rewrite(query, conversation=conversation)
        rewritten_query = rewrite.rewritten_query
        if self._last_report is not None and self._last_query == rewritten_query:
            return MemoryProviderSearchReport(
                rewrite=rewrite,
                hits=self._last_report.hits[:limit],
                provider_count=self._last_report.provider_count,
            )

        self.queue_prefetch(rewritten_query, conversation=conversation)
        self.prefetch(rewritten_query, conversation=conversation)
        hits: list[MemoryProviderHit] = []
        for provider in self.providers:
            hits.extend(provider.search(rewritten_query, conversation=conversation, limit=limit))
        hits.sort(key=lambda item: (-item.score, item.provider, item.title.lower()))
        report = MemoryProviderSearchReport(
            rewrite=rewrite,
            hits=hits[:limit],
            provider_count=len(self.providers),
        )
        self._last_query = rewritten_query
        self._last_report = report
        return report


from ecology_harness.memory.providers.builtin import BuiltinMemoryProvider
from ecology_harness.memory.providers.profiles import MarkdownProfileProvider

__all__ = [
    "BaseMemoryProvider",
    "BuiltinMemoryProvider",
    "MarkdownProfileProvider",
    "MemoryProviderHit",
    "MemoryProviderManager",
    "MemoryProviderSearchReport",
]


def _shorten(text: str, limit: int) -> str:
    stripped = text.strip()
    if len(stripped) <= limit:
        return stripped
    return stripped[: max(0, limit - 3)].rstrip() + "..."


def _fit_blocks_to_budget(blocks: list[str], max_chars: int) -> str:
    selected: list[str] = []
    used = 0
    for block in blocks:
        normalized = block.strip()
        if not normalized:
            continue
        separator = 2 if selected else 0
        if used + separator + len(normalized) <= max_chars:
            selected.append(normalized)
            used += separator + len(normalized)
            continue
        remaining = max_chars - used - separator
        if remaining <= 32:
            break
        selected.append(normalized[: max(0, remaining - 3)].rstrip() + "...")
        break
    return "\n\n".join(selected).strip()
