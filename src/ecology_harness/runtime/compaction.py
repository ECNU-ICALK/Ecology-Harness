from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Callable, Optional

from ecology_harness.runtime.messages import ChatMessage


COMPACT_CONTINUATION_PREAMBLE = (
    "This conversation is being continued from an earlier context window. "
    "The summary below covers the compacted portion of the session."
)
COMPACT_RECENT_MESSAGES_NOTE = "Recent messages are preserved verbatim."
COMPACT_DIRECT_RESUME_INSTRUCTION = (
    "Continue directly from the preserved context. Do not acknowledge the summary or ask the "
    "user to repeat prior details."
)
CriticalFactExtractor = Callable[[list[ChatMessage], int], Optional[list[str]]]


@dataclass(frozen=True)
class SummaryCompressionBudget:
    max_chars: int = 1_200
    max_lines: int = 24
    max_line_chars: int = 160


@dataclass(frozen=True)
class SummaryCompressionResult:
    summary: str
    original_chars: int
    compressed_chars: int
    original_lines: int
    compressed_lines: int
    removed_duplicate_lines: int
    omitted_lines: int
    truncated: bool


@dataclass(frozen=True)
class CompactionConfig:
    preserve_recent_messages: int = 8
    min_recent_messages: int = 4
    max_estimated_tokens: int = 10_000
    target_estimated_tokens: int = 8_000
    summary_budget: SummaryCompressionBudget = SummaryCompressionBudget()


@dataclass
class CompactionResult:
    messages: list[ChatMessage]
    compacted: bool = False
    summary: str = ""
    formatted_summary: str = ""
    compressed_summary: str = ""
    removed_message_count: int = 0
    token_estimate_before: int = 0
    token_estimate_after: int = 0

    def to_dict(self) -> dict[str, int | str | bool]:
        return {
            "compacted": self.compacted,
            "summary": self.summary,
            "formatted_summary": self.formatted_summary,
            "compressed_summary": self.compressed_summary,
            "removed_message_count": self.removed_message_count,
            "token_estimate_before": self.token_estimate_before,
            "token_estimate_after": self.token_estimate_after,
        }


def estimate_tokens(messages: list[ChatMessage]) -> int:
    total_chars = 0
    for message in messages:
        total_chars += len(message.content_text() or "")
        total_chars += len(message.name or "")
        for tool_call in message.tool_calls:
            total_chars += len(tool_call.name)
            total_chars += len(str(tool_call.arguments))
    return int(total_chars / 3.5)


def snip_old_tool_results(
    messages: list[ChatMessage],
    max_chars: int = 2_000,
    preserve_last_n_turns: int = 6,
) -> list[ChatMessage]:
    cutoff = max(0, len(messages) - max(4, preserve_last_n_turns * 2))
    for index in range(cutoff):
        message = messages[index]
        if message.role != "tool":
            continue
        if len(message.content_text() or "") <= max_chars:
            continue
        content = message.content
        first_half = content[: max_chars // 2]
        last_quarter = content[-(max_chars // 4) :]
        snipped = len(content) - len(first_half) - len(last_quarter)
        message.content = "%s\n[... %s chars snipped ...]\n%s" % (
            first_half,
            snipped,
            last_quarter,
        )
    return messages


def maybe_compact_messages(
    messages: list[ChatMessage],
    max_context_tokens: int,
    preserve_last_n_turns: int,
    critical_fact_extractor: CriticalFactExtractor | None = None,
) -> CompactionResult:
    threshold = int(max_context_tokens * 0.7)
    target_after = min(
        threshold,
        max(int(max_context_tokens * 0.55), min(512, threshold)),
    )
    token_estimate_before = estimate_tokens(messages)
    if token_estimate_before <= threshold:
        return CompactionResult(
            messages=messages,
            token_estimate_before=token_estimate_before,
            token_estimate_after=token_estimate_before,
        )

    snipped_messages = snip_old_tool_results(
        list(messages),
        preserve_last_n_turns=preserve_last_n_turns,
    )
    token_estimate_after_snip = estimate_tokens(snipped_messages)
    if token_estimate_after_snip <= threshold:
        return CompactionResult(
            messages=snipped_messages,
            token_estimate_before=token_estimate_before,
            token_estimate_after=token_estimate_after_snip,
        )

    config = CompactionConfig(
        preserve_recent_messages=max(6, preserve_last_n_turns * 2),
        min_recent_messages=max(4, preserve_last_n_turns),
        max_estimated_tokens=threshold,
        target_estimated_tokens=target_after,
    )
    return compact_messages(
        snipped_messages,
        config=config,
        token_estimate_before=token_estimate_before,
        critical_fact_extractor=critical_fact_extractor,
    )


def compact_messages(
    messages: list[ChatMessage],
    config: CompactionConfig | None = None,
    token_estimate_before: int | None = None,
    critical_fact_extractor: CriticalFactExtractor | None = None,
) -> CompactionResult:
    active_config = config or CompactionConfig()
    start = _compaction_start_index(messages)
    compactable = messages[start:]
    if len(compactable) <= active_config.preserve_recent_messages:
        current_tokens = estimate_tokens(messages)
        return CompactionResult(
            messages=messages,
            token_estimate_before=token_estimate_before or current_tokens,
            token_estimate_after=current_tokens,
        )

    preferred_preserve = min(max(active_config.preserve_recent_messages, 1), len(compactable))
    soft_min_preserve = min(
        preferred_preserve,
        max(2, min(active_config.min_recent_messages, len(compactable))),
    )
    hard_min_preserve = 1 if preferred_preserve else 0

    best_result: CompactionResult | None = None
    for preserve_count in range(preferred_preserve, hard_min_preserve - 1, -1):
        result = _build_compaction_candidate(
            messages,
            start=start,
            preserve_count=preserve_count,
            active_config=active_config,
            token_estimate_before=token_estimate_before,
            critical_fact_extractor=critical_fact_extractor,
        )
        if result is None:
            continue
        if best_result is None or result.token_estimate_after < best_result.token_estimate_after:
            best_result = result
        if result.token_estimate_after <= active_config.target_estimated_tokens:
            return result
        if (
            preserve_count <= soft_min_preserve
            and result.token_estimate_after <= active_config.max_estimated_tokens
        ):
            return result

    if best_result is not None:
        return best_result

    current_tokens = estimate_tokens(messages)
    return CompactionResult(
        messages=messages,
        token_estimate_before=token_estimate_before or current_tokens,
        token_estimate_after=current_tokens,
    )


def _build_compaction_candidate(
    messages: list[ChatMessage],
    *,
    start: int,
    preserve_count: int,
    active_config: CompactionConfig,
    token_estimate_before: int | None,
    critical_fact_extractor: CriticalFactExtractor | None,
) -> CompactionResult | None:
    keep_from = max(start, len(messages) - max(preserve_count, 0))
    removed = messages[start:keep_from]
    preserved = messages[keep_from:]
    if not removed:
        return None

    existing_summary = _extract_existing_summary(messages)
    new_summary = summarize_messages(
        removed,
        critical_fact_extractor=critical_fact_extractor,
    )
    merged_summary = merge_compact_summaries(existing_summary, new_summary)
    formatted_summary = format_compact_summary(merged_summary)
    compressed_summary = compress_summary_text(
        formatted_summary,
        budget=active_config.summary_budget,
    )
    continuation = get_compact_continuation_message(
        compressed_summary,
        suppress_follow_up_questions=True,
        recent_messages_preserved=bool(preserved),
    )

    compacted_messages = list(messages[:1]) if messages and messages[0].role == "system" else []
    compacted_messages.append(ChatMessage(role="system", content=continuation))
    compacted_messages.extend(preserved)
    token_after = estimate_tokens(compacted_messages)
    if token_after > active_config.max_estimated_tokens and preserved:
        budgeted_preserved = _snip_verbose_messages(
            preserved,
            max_chars=max(240, min(900, int(active_config.target_estimated_tokens or 0))),
            preserve_tail=1,
        )
        compacted_messages = list(messages[:1]) if messages and messages[0].role == "system" else []
        compacted_messages.append(ChatMessage(role="system", content=continuation))
        compacted_messages.extend(budgeted_preserved)
        token_after = estimate_tokens(compacted_messages)
    if token_after > active_config.max_estimated_tokens:
        tighter_budget = SummaryCompressionBudget(
            max_chars=max(400, active_config.summary_budget.max_chars // 2),
            max_lines=max(12, active_config.summary_budget.max_lines // 2),
            max_line_chars=max(100, active_config.summary_budget.max_line_chars - 40),
        )
        compressed_summary = compress_summary_text(formatted_summary, budget=tighter_budget)
        continuation = get_compact_continuation_message(
            compressed_summary,
            suppress_follow_up_questions=True,
            recent_messages_preserved=bool(preserved),
        )
        compacted_messages = list(messages[:1]) if messages and messages[0].role == "system" else []
        compacted_messages.append(ChatMessage(role="system", content=continuation))
        compacted_messages.extend(
            _snip_verbose_messages(
                preserved,
                max_chars=max(180, min(600, int(active_config.target_estimated_tokens * 0.75))),
                preserve_tail=1,
            )
        )
        token_after = estimate_tokens(compacted_messages)
    if token_after > active_config.max_estimated_tokens and preserved:
        compacted_messages = list(messages[:1]) if messages and messages[0].role == "system" else []
        compacted_messages.append(ChatMessage(role="system", content=continuation))
        compacted_messages.extend(
            _snip_verbose_messages(
                preserved,
                max_chars=max(160, min(420, int(active_config.target_estimated_tokens * 0.6))),
                preserve_tail=0,
            )
        )
        token_after = estimate_tokens(compacted_messages)
    return CompactionResult(
        messages=compacted_messages,
        compacted=True,
        summary=merged_summary,
        formatted_summary=formatted_summary,
        compressed_summary=compressed_summary,
        removed_message_count=len(removed),
        token_estimate_before=token_estimate_before or estimate_tokens(messages),
        token_estimate_after=token_after,
    )


def summarize_messages(
    messages: list[ChatMessage],
    critical_fact_extractor: CriticalFactExtractor | None = None,
) -> str:
    user_messages = [item for item in messages if item.role == "user"]
    assistant_messages = [item for item in messages if item.role == "assistant"]
    tool_messages = [item for item in messages if item.role == "tool"]

    lines = [
        "Conversation summary:",
        "- Scope: %s earlier messages compacted (user=%s, assistant=%s, tool=%s)."
        % (len(messages), len(user_messages), len(assistant_messages), len(tool_messages)),
    ]

    tool_names = sorted(
        {
            name
            for name in _tool_names(messages)
            if name
        }
    )
    if tool_names:
        lines.append("- Tools mentioned: %s." % ", ".join(tool_names))

    recent_user_requests = _collect_recent_role_summaries(messages, role="user", limit=3)
    if recent_user_requests:
        lines.append("- Recent user requests:")
        lines.extend("  - %s" % item for item in recent_user_requests)

    pending_work = _infer_pending_work(messages)
    if pending_work:
        lines.append("- Pending work:")
        lines.extend("  - %s" % item for item in pending_work[:4])

    critical_facts = _extract_critical_facts(
        messages,
        extractor=critical_fact_extractor,
    )
    if critical_facts:
        lines.append("- Critical facts to preserve:")
        lines.extend("  - %s" % item for item in critical_facts[:5])

    key_files = _collect_key_files(messages)
    if key_files:
        lines.append("- Key files referenced: %s." % ", ".join(key_files[:8]))

    current_work = _infer_current_work(messages)
    if current_work:
        lines.append("- Current work: %s" % current_work)

    lines.append("- Key timeline:")
    for message in messages[-16:]:
        lines.append("  - %s: %s" % (message.role, _summarize_message(message)))

    return "\n".join(lines)


def merge_compact_summaries(existing_summary: str | None, new_summary: str) -> str:
    if not existing_summary:
        return new_summary

    previous_lines = _extract_summary_lines(existing_summary)
    new_lines = _extract_summary_lines(new_summary)
    merged = ["Conversation summary:"]
    if previous_lines:
        merged.append("- Previously compacted context:")
        merged.extend("  %s" % line for line in previous_lines[:10])
    if new_lines:
        merged.append("- Newly compacted context:")
        merged.extend("  %s" % line for line in new_lines[:12])
    return "\n".join(merged)


def format_compact_summary(summary: str) -> str:
    lines = []
    seen = set()
    for raw_line in summary.splitlines():
        collapsed = _collapse_inline_whitespace(raw_line)
        if not collapsed:
            continue
        dedupe_key = collapsed.lower()
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        lines.append(collapsed)
    return "\n".join(lines)


def get_compact_continuation_message(
    summary: str,
    suppress_follow_up_questions: bool = True,
    recent_messages_preserved: bool = True,
) -> str:
    parts = [COMPACT_CONTINUATION_PREAMBLE, "", summary.strip()]
    if recent_messages_preserved:
        parts.extend(["", COMPACT_RECENT_MESSAGES_NOTE])
    if suppress_follow_up_questions:
        parts.extend(["", COMPACT_DIRECT_RESUME_INSTRUCTION])
    return "\n".join(item for item in parts if item is not None).strip()


def compress_summary(
    summary: str,
    budget: SummaryCompressionBudget | None = None,
) -> SummaryCompressionResult:
    active_budget = budget or SummaryCompressionBudget()
    original_chars = len(summary)
    original_lines = len(summary.splitlines())
    normalized, removed_duplicate_lines = _normalize_lines(summary, active_budget.max_line_chars)
    if not normalized or active_budget.max_chars <= 0 or active_budget.max_lines <= 0:
        return SummaryCompressionResult(
            summary="",
            original_chars=original_chars,
            compressed_chars=0,
            original_lines=original_lines,
            compressed_lines=0,
            removed_duplicate_lines=removed_duplicate_lines,
            omitted_lines=len(normalized),
            truncated=bool(summary.strip()),
        )

    selected_indexes = _select_line_indexes(normalized, active_budget)
    compressed_lines = [normalized[index] for index in selected_indexes]
    omitted_lines = max(0, len(normalized) - len(compressed_lines))
    if omitted_lines:
        _push_line_with_budget(
            compressed_lines,
            "- ... %s additional line(s) omitted." % omitted_lines,
            active_budget,
        )
    compressed_summary = "\n".join(compressed_lines)
    return SummaryCompressionResult(
        summary=compressed_summary,
        original_chars=original_chars,
        compressed_chars=len(compressed_summary),
        original_lines=original_lines,
        compressed_lines=len(compressed_lines),
        removed_duplicate_lines=removed_duplicate_lines,
        omitted_lines=omitted_lines,
        truncated=compressed_summary != summary.strip(),
    )


def compress_summary_text(
    summary: str,
    budget: SummaryCompressionBudget | None = None,
) -> str:
    return compress_summary(summary, budget=budget).summary


def _compaction_start_index(messages: list[ChatMessage]) -> int:
    start = 0
    if messages and messages[0].role == "system":
        start = 1
    if len(messages) > start and _is_compacted_summary_message(messages[start]):
        start += 1
    return start


def _extract_existing_summary(messages: list[ChatMessage]) -> str | None:
    start = 1 if messages and messages[0].role == "system" else 0
    if len(messages) <= start:
        return None
    candidate = messages[start]
    if not _is_compacted_summary_message(candidate):
        return None
    content = candidate.content_text()
    content = content.replace(COMPACT_CONTINUATION_PREAMBLE, "", 1).strip()
    content = content.replace(COMPACT_RECENT_MESSAGES_NOTE, "").strip()
    content = content.replace(COMPACT_DIRECT_RESUME_INSTRUCTION, "").strip()
    return content or None


def _is_compacted_summary_message(message: ChatMessage) -> bool:
    return message.role == "system" and COMPACT_CONTINUATION_PREAMBLE in (message.content_text() or "")


def _collect_recent_role_summaries(
    messages: list[ChatMessage],
    role: str,
    limit: int,
) -> list[str]:
    summaries = []
    for message in reversed(messages):
        if message.role != role:
            continue
        summaries.append(_summarize_message(message))
        if len(summaries) >= limit:
            break
    summaries.reverse()
    return summaries


def _snip_verbose_messages(
    messages: list[ChatMessage],
    *,
    max_chars: int,
    preserve_tail: int = 1,
) -> list[ChatMessage]:
    if max_chars <= 0 or not messages:
        return list(messages)
    cutoff = max(0, len(messages) - max(preserve_tail, 0))
    snipped: list[ChatMessage] = []
    for index, message in enumerate(messages):
        cloned = ChatMessage(
            role=message.role,
            content=message.content,
            name=message.name,
            tool_call_id=message.tool_call_id,
            tool_calls=list(message.tool_calls),
            content_parts=list(message.content_parts),
        )
        if index < cutoff and len(cloned.content_text() or "") > max_chars:
            content = cloned.content_text()
            first_half = content[: max_chars // 2]
            last_quarter = content[-(max_chars // 4) :] if max_chars >= 4 else ""
            snipped_chars = len(content) - len(first_half) - len(last_quarter)
            cloned.content = "%s\n[... %s chars snipped ...]\n%s" % (
                first_half,
                max(snipped_chars, 0),
                last_quarter,
            )
        snipped.append(cloned)
    return snipped


def _infer_pending_work(messages: list[ChatMessage]) -> list[str]:
    pending = []
    keywords = ("todo", "next", "remaining", "follow up", "need to", "should", "plan")
    for message in reversed(messages[-12:]):
        content = _collapse_inline_whitespace(message.summary_text())
        lowered = content.lower()
        if not content:
            continue
        if any(keyword in lowered for keyword in keywords):
            pending.append(_truncate_line(content, 140))
        if len(pending) >= 4:
            break
    pending.reverse()
    deduped = []
    seen = set()
    for item in pending:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _collect_key_files(messages: list[ChatMessage]) -> list[str]:
    pattern = re.compile(r"[\w./-]+\.(?:py|md|json|yaml|yml|txt|csv|ipynb|rs|ts|js|tsx|jsx|toml)")
    found = []
    seen = set()
    for message in messages:
        for match in pattern.findall(message.summary_text()):
            if match in seen:
                continue
            seen.add(match)
            found.append(match)
    return found


def _infer_current_work(messages: list[ChatMessage]) -> str:
    for message in reversed(messages):
        text = _summarize_message(message)
        if text:
            return text
    return ""


def _extract_critical_facts(
    messages: list[ChatMessage],
    limit: int = 5,
    extractor: CriticalFactExtractor | None = None,
) -> list[str]:
    semantic_facts = _extract_semantic_critical_facts(
        messages,
        limit=limit,
        extractor=extractor,
    )
    if semantic_facts:
        return semantic_facts
    return _extract_pattern_critical_facts(messages, limit=limit)


def _extract_semantic_critical_facts(
    messages: list[ChatMessage],
    *,
    limit: int,
    extractor: CriticalFactExtractor | None,
) -> list[str]:
    if extractor is None:
        return []
    try:
        extracted = extractor(messages, limit)
    except Exception:
        return []
    return _normalize_critical_fact_items(extracted, limit=limit)


def _extract_pattern_critical_facts(messages: list[ChatMessage], limit: int = 5) -> list[str]:
    patterns = (
        re.compile(r"\bMUST\s*:\s*(.+)", re.IGNORECASE),
        re.compile(r"\bCRITICAL\s*:\s*(.+)", re.IGNORECASE),
        re.compile(r"\bIMPORTANT\s*:\s*(.+)", re.IGNORECASE),
        re.compile(r"\bDO NOT\s*:\s*(.+)", re.IGNORECASE),
        re.compile(r"\bNEXT(?:\s+STEP)?\s*:\s*(.+)", re.IGNORECASE),
    )
    facts: list[str] = []
    seen = set()
    for message in messages:
        text = message.summary_text(max_document_chars=900)
        if not text:
            continue
        in_critical_section = False
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                in_critical_section = False
                continue
            lowered = line.lower()
            if "critical facts" in lowered:
                in_critical_section = True
                continue
            normalized = line.lstrip("-* ").strip()
            matched = None
            for pattern in patterns:
                capture = pattern.search(normalized)
                if capture:
                    matched = capture.group(0).strip()
                    break
            if matched is None and in_critical_section and normalized:
                matched = normalized
            if matched is None:
                continue
            truncated = _truncate_line(_collapse_inline_whitespace(matched), 180)
            key = truncated.lower()
            if key in seen:
                continue
            seen.add(key)
            facts.append(truncated)
            if len(facts) >= limit:
                return facts
    return facts


def _normalize_critical_fact_items(items: list[str] | None, *, limit: int) -> list[str]:
    if not items:
        return []
    facts: list[str] = []
    seen = set()
    for raw_item in items:
        text = _truncate_line(_collapse_inline_whitespace(str(raw_item or "").strip()), 180)
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        facts.append(text)
        if len(facts) >= limit:
            break
    return facts


def _summarize_message(message: ChatMessage) -> str:
    parts = []
    content = _collapse_inline_whitespace(message.summary_text())
    if content:
        parts.append(_truncate_line(content, 180))
    if message.tool_calls:
        parts.append(
            "tool_calls=%s"
            % ", ".join(_truncate_line(item.name, 32) for item in message.tool_calls if item.name)
        )
    if message.role == "tool" and message.name:
        parts.insert(0, "tool=%s" % message.name)
    if not parts:
        return "<empty>"
    return " | ".join(parts)


def _tool_names(messages: list[ChatMessage]) -> list[str]:
    names = []
    for message in messages:
        if message.role == "tool" and message.name:
            names.append(message.name)
        for tool_call in message.tool_calls:
            if tool_call.name:
                names.append(tool_call.name)
    return names


def _extract_summary_lines(summary: str) -> list[str]:
    lines = []
    for line in format_compact_summary(summary).splitlines():
        if line == "Conversation summary:":
            continue
        lines.append(line)
    return lines


def _normalize_lines(summary: str, max_line_chars: int) -> tuple[list[str], int]:
    lines = []
    seen = set()
    removed_duplicate_lines = 0
    for raw_line in summary.splitlines():
        normalized = _collapse_inline_whitespace(raw_line)
        if not normalized:
            continue
        truncated = _truncate_line(normalized, max_line_chars)
        key = truncated.lower()
        if key in seen:
            removed_duplicate_lines += 1
            continue
        seen.add(key)
        lines.append(truncated)
    return lines, removed_duplicate_lines


def _select_line_indexes(lines: list[str], budget: SummaryCompressionBudget) -> list[int]:
    selected: list[int] = []
    selected_set = set()
    for priority in range(4):
        for index, line in enumerate(lines):
            if index in selected_set or _line_priority(line) != priority:
                continue
            candidate = [lines[item] for item in selected] + [line]
            if len(candidate) > budget.max_lines:
                continue
            if _joined_char_count(candidate) > budget.max_chars:
                continue
            selected.append(index)
            selected_set.add(index)
    return selected


def _push_line_with_budget(lines: list[str], line: str, budget: SummaryCompressionBudget) -> None:
    candidate = list(lines) + [line]
    if len(candidate) <= budget.max_lines and _joined_char_count(candidate) <= budget.max_chars:
        lines.append(line)


def _line_priority(line: str) -> int:
    if (
        line in {"Summary:", "Conversation summary:"}
        or _is_core_detail(line)
        or _contains_preserve_signal(line)
    ):
        return 0
    if line.endswith(":"):
        return 1
    if line.startswith("- ") or line.startswith("  - "):
        return 2
    return 3


def _is_core_detail(line: str) -> bool:
    return any(
        line.startswith(prefix)
        for prefix in (
            "- Scope:",
            "- Current work:",
            "- Pending work:",
            "- Critical facts to preserve:",
            "- Key files referenced:",
            "- Tools mentioned:",
            "- Recent user requests:",
            "- Previously compacted context:",
            "- Newly compacted context:",
        )
    )


def _contains_preserve_signal(line: str) -> bool:
    upper = line.upper()
    return any(
        marker in upper
        for marker in (
            "MUST:",
            "CRITICAL:",
            "IMPORTANT:",
            "DO NOT:",
            "NEXT:",
            "NEXT STEP:",
        )
    )


def _joined_char_count(lines: list[str]) -> int:
    return sum(len(item) for item in lines) + max(0, len(lines) - 1)


def _collapse_inline_whitespace(line: str) -> str:
    return " ".join(line.split())


def _truncate_line(line: str, max_chars: int) -> str:
    if max_chars <= 0 or len(line) <= max_chars:
        return line
    if max_chars == 1:
        return "…"
    return line[: max_chars - 1] + "…"
