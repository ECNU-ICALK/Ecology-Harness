from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ecology_harness.runtime.compaction import estimate_tokens, summarize_messages
from ecology_harness.runtime.messages import ChatMessage


@dataclass
class TrajectoryCompressionResult:
    original_message_count: int
    compressed_message_count: int
    original_token_estimate: int
    compressed_token_estimate: int
    summary: str
    removed_count: int
    compressed_messages: list[dict[str, Any]]
    preserved_indices: list[int] = field(default_factory=list)
    preserved_highlights: list[str] = field(default_factory=list)
    quality_tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_message_count": self.original_message_count,
            "compressed_message_count": self.compressed_message_count,
            "original_token_estimate": self.original_token_estimate,
            "compressed_token_estimate": self.compressed_token_estimate,
            "summary": self.summary,
            "removed_count": self.removed_count,
            "compressed_messages": self.compressed_messages,
            "preserved_indices": self.preserved_indices,
            "preserved_highlights": self.preserved_highlights,
            "quality_tags": self.quality_tags,
        }


def compress_trajectory_messages(
    messages: list[ChatMessage],
    preserve_first_n: int = 2,
    preserve_last_n: int = 4,
) -> TrajectoryCompressionResult:
    if not messages:
        return TrajectoryCompressionResult(
            original_message_count=0,
            compressed_message_count=0,
            original_token_estimate=0,
            compressed_token_estimate=0,
            summary="",
            removed_count=0,
            compressed_messages=[],
        )

    preserved_indices = _select_preserved_indices(
        messages,
        preserve_first_n=preserve_first_n,
        preserve_last_n=preserve_last_n,
    )
    if len(preserved_indices) >= len(messages):
        serialized = [item.to_dict() for item in messages]
        tokens = estimate_tokens(messages)
        return TrajectoryCompressionResult(
            original_message_count=len(messages),
            compressed_message_count=len(messages),
            original_token_estimate=tokens,
            compressed_token_estimate=tokens,
            summary="",
            removed_count=0,
            compressed_messages=serialized,
            preserved_indices=preserved_indices,
            preserved_highlights=_highlights(messages, preserved_indices),
            quality_tags=_compression_tags(messages, preserved_indices, 0),
        )

    compressed: list[ChatMessage] = []
    removed_count = 0
    summary_segments: list[str] = []
    preserved_set = set(preserved_indices)
    index = 0
    while index < len(messages):
        if index in preserved_set:
            compressed.append(messages[index])
            index += 1
            continue
        gap_start = index
        while index < len(messages) and index not in preserved_set:
            index += 1
        removed = messages[gap_start:index]
        removed_count += len(removed)
        if removed:
            summary = summarize_messages(removed)
            summary_segments.append(summary)
            compressed.append(
                ChatMessage(
                    role="system",
                    content="Compressed trajectory segment:\n%s" % summary,
                )
            )

    merged_summary = "\n\n".join(item for item in summary_segments if item).strip()
    return TrajectoryCompressionResult(
        original_message_count=len(messages),
        compressed_message_count=len(compressed),
        original_token_estimate=estimate_tokens(messages),
        compressed_token_estimate=estimate_tokens(compressed),
        summary=merged_summary,
        removed_count=removed_count,
        compressed_messages=[item.to_dict() for item in compressed],
        preserved_indices=preserved_indices,
        preserved_highlights=_highlights(messages, preserved_indices),
        quality_tags=_compression_tags(messages, preserved_indices, removed_count),
    )


def _select_preserved_indices(
    messages: list[ChatMessage],
    preserve_first_n: int,
    preserve_last_n: int,
) -> list[int]:
    preserved: set[int] = set()
    for index in range(min(preserve_first_n, len(messages))):
        preserved.add(index)
    for index in range(max(0, len(messages) - preserve_last_n), len(messages)):
        preserved.add(index)

    for index, message in enumerate(messages):
        if message.role == "user":
            preserved.add(index)
            break
    for index, message in enumerate(messages):
        if message.role == "assistant" and message.tool_calls:
            preserved.add(index)
            break
    for index, message in enumerate(messages):
        if message.role == "tool":
            preserved.add(index)
            break

    for index, message in enumerate(messages):
        content = message.content_text()
        if message.content_parts:
            preserved.add(index)
        if "Tool error" in content or "Permission denied" in content:
            preserved.add(index)
        if "Agent reached max_agent_loops" in content:
            preserved.add(index)

    return sorted(preserved)


def _highlights(messages: list[ChatMessage], indices: list[int]) -> list[str]:
    highlights: list[str] = []
    for index in indices[:8]:
        message = messages[index]
        excerpt = message.summary_text(max_document_chars=100).strip()
        if not excerpt:
            continue
        highlights.append("%s[%s]: %s" % (message.role, index, excerpt))
    return highlights


def _compression_tags(messages: list[ChatMessage], indices: list[int], removed_count: int) -> list[str]:
    tags: list[str] = []
    if removed_count > 0:
        tags.append("compressed")
    if any(messages[index].content_parts for index in indices if index < len(messages)):
        tags.append("preserved-multimodal")
    if any(messages[index].role == "tool" for index in indices if index < len(messages)):
        tags.append("preserved-tool-signal")
    if any("Tool error" in messages[index].content_text() for index in indices if index < len(messages)):
        tags.append("preserved-failure")
    return tags
