from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import math
from pathlib import Path
import re

from ecology_harness.memory.scan import (
    MemoryHeader,
    format_memory_manifest,
    memory_freshness_text,
    scan_memory_dir,
)
from ecology_harness.memory.types import MEMORY_SYSTEM_PROMPT
from ecology_harness.utils import atomic_write_text, dump_frontmatter, parse_frontmatter, slugify


INDEX_FILENAME = "MEMORY.md"
_MEMORY_STOPWORDS = {
    "and",
    "are",
    "for",
    "from",
    "into",
    "read",
    "that",
    "the",
    "this",
    "tool",
    "with",
}
_UNSAFE_MEMORY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("prompt-injection", re.compile(r"ignore.{0,80}\binstructions\b", re.I)),
    ("prompt-injection", re.compile(r"(system|developer)\s+prompt", re.I)),
    ("credential-risk", re.compile(r"\b(api[_ -]?key|password|secret|token|ssh\s+key)\b", re.I)),
    ("destructive-command", re.compile(r"\b(rm\s+-rf|git\s+reset\s+--hard|mkfs|dd\s+if=)\b", re.I)),
    ("exfiltration-risk", re.compile(r"\b(curl|wget)\b.{0,80}\|\s*(sh|bash)", re.I)),
)


@dataclass
class MemoryItem:
    slug: str
    name: str
    description: str
    memory_type: str
    scope: str
    created_at: str
    updated_at: str
    content: str
    file_path: str = ""

    def to_index_dict(self) -> dict[str, str]:
        return {
            "slug": self.slug,
            "name": self.name,
            "description": self.description,
            "type": self.memory_type,
            "category": self.memory_type,
            "scope": self.scope,
            "updated_at": self.updated_at,
            "file_path": self.file_path,
        }


class MemoryManager:
    def __init__(
        self,
        user_root: Path,
        project_root: Path,
        max_index_lines: int = 200,
        max_index_bytes: int = 25_000,
        context_max_chars: int = 5_500,
        context_max_relevant_items: int = 4,
        context_excerpt_chars: int = 220,
        inventory_max_items: int = 4,
    ) -> None:
        self.user_root = user_root
        self.project_root = project_root
        self.max_index_lines = max_index_lines
        self.max_index_bytes = max_index_bytes
        self.context_max_chars = max(800, context_max_chars)
        self.context_max_relevant_items = max(1, context_max_relevant_items)
        self.context_excerpt_chars = max(80, context_excerpt_chars)
        self.inventory_max_items = max(1, inventory_max_items)
        self.user_root.mkdir(parents=True, exist_ok=True)
        self.project_root.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        name: str,
        description: str,
        content: str,
        memory_type: str = "project",
        scope: str = "project",
    ) -> MemoryItem:
        slug = _memory_slug(name)
        now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        existing = self.get(slug, scope=scope)
        created_at = existing.created_at if existing else now
        item = MemoryItem(
            slug=slug,
            name=name,
            description=description,
            memory_type=memory_type,
            scope=scope,
            created_at=created_at,
            updated_at=now,
            content=content,
        )
        metadata = {
            "slug": item.slug,
            "name": item.name,
            "description": item.description,
            "type": item.memory_type,
            "scope": item.scope,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }
        path = self._path_for(slug, scope)
        atomic_write_text(path, dump_frontmatter(metadata, content), encoding="utf-8")
        item.file_path = str(path)
        self._rewrite_index(scope)
        return item

    def delete(self, slug_or_name: str, scope: str = "project") -> bool:
        item = self.get(slug_or_name, scope=scope)
        if item is None:
            return False
        self._path_for(item.slug, item.scope).unlink(missing_ok=True)
        self._rewrite_index(item.scope)
        return True

    def get(self, slug_or_name: str, scope: str = "all") -> MemoryItem | None:
        normalized = slugify(slug_or_name)
        for item in self.list_items(scope=scope):
            if item.slug == normalized or item.name == slug_or_name:
                return item
        return None

    def list_items(self, scope: str = "all") -> list[MemoryItem]:
        scopes = self._resolve_scopes(scope)
        items = []
        for one_scope in scopes:
            root = self._root_for_scope(one_scope)
            for path in sorted(root.glob("*.md")):
                if path.name == INDEX_FILENAME:
                    continue
                item = self._read_path(path, one_scope)
                if item is not None:
                    items.append(item)
        items.sort(
            key=lambda item: (
                1 if item.scope == "project" else 0,
                self._timestamp_value(item.updated_at),
                item.name.lower(),
            ),
            reverse=True,
        )
        return items

    def search(self, query: str, scope: str = "all", max_results: int = 5) -> list[dict]:
        needle = query.strip().lower()
        query_terms = _memory_terms(query)
        if not needle and not query_terms:
            return []
        items = self.list_items(scope=scope)
        if not items:
            return []
        document_terms = [
            set(
                _memory_terms("\n".join([item.name, item.description, item.memory_type, item.content]))
            )
            for item in items
        ]
        document_frequency: dict[str, int] = {}
        for term in query_terms:
            document_frequency[term] = sum(
                1 for terms in document_terms if term in terms
            )
        scored_results: list[tuple[float, float, dict]] = []
        header_index = {header.file_path: header for header in self.scan_all(scope)}
        for item in items:
            score, matched_terms = self._search_score(
                item=item,
                query=needle,
                terms=query_terms,
                document_frequency=document_frequency,
                document_count=len(items),
            )
            if score <= 0:
                continue
            header = header_index.get(item.file_path)
            result = item.to_index_dict()
            result["content"] = item.content
            result["score"] = round(score, 4)
            result["matched_terms"] = matched_terms
            result["freshness_text"] = (
                memory_freshness_text(header.mtime_s) if header is not None else ""
            )
            scored_results.append((score, self._timestamp_value(item.updated_at), result))
        scored_results.sort(key=lambda row: (row[0], row[1]), reverse=True)
        return [item for _, _, item in scored_results[:max_results]]

    def health_report(
        self,
        scope: str = "all",
        stale_days: int = 90,
        large_chars: int = 4_000,
        max_overlap_pairs: int = 8,
    ) -> dict[str, object]:
        items = self.list_items(scope=scope)
        scope_counts = {"user": 0, "project": 0}
        issues: list[dict[str, object]] = []
        now_ts = datetime.utcnow().timestamp()
        for item in items:
            scope_counts[item.scope] = scope_counts.get(item.scope, 0) + 1
            age_days = self._age_days(item.updated_at, now_ts)
            if stale_days > 0 and age_days is not None and age_days > stale_days:
                issues.append(
                    _health_issue(
                        issue_type="stale",
                        severity="low",
                        slug=item.slug,
                        scope=item.scope,
                        description="`%s` has not been updated for %s days." % (item.name, int(age_days)),
                        suggestion="Review whether this memory is still accurate or archive it.",
                        metadata={"age_days": int(age_days)},
                    )
                )
            if large_chars > 0 and len(item.content) > large_chars:
                issues.append(
                    _health_issue(
                        issue_type="large",
                        severity="medium",
                        slug=item.slug,
                        scope=item.scope,
                        description="`%s` is %s characters long." % (item.name, len(item.content)),
                        suggestion="Compress this item into durable facts and move raw detail to a document.",
                        metadata={"content_chars": len(item.content)},
                    )
                )
            risk_flags = _memory_risk_flags("\n".join([item.name, item.description, item.content]))
            if risk_flags:
                issues.append(
                    _health_issue(
                        issue_type="instruction-risk",
                        severity="high",
                        slug=item.slug,
                        scope=item.scope,
                        description="`%s` contains risky instruction-like or credential-like text." % item.name,
                        suggestion="Rewrite as neutral facts; do not store secrets or executable instructions in memory.",
                        metadata={"risk_flags": risk_flags},
                    )
                )
        issues.extend(self._overlap_issues(items, max_overlap_pairs=max_overlap_pairs))
        recommendations = _memory_recommendations(issues)
        return {
            "scope": scope,
            "item_count": len(items),
            "scope_counts": scope_counts,
            "issue_count": len(issues),
            "issues": issues,
            "recommendations": recommendations,
        }

    def scan_all(self, scope: str = "all") -> list[MemoryHeader]:
        headers = []
        for one_scope in self._resolve_scopes(scope):
            headers.extend(
                scan_memory_dir(
                    self._root_for_scope(one_scope),
                    one_scope,
                    index_filename=INDEX_FILENAME,
                )
            )
        headers.sort(key=lambda item: item.mtime_s, reverse=True)
        return headers

    def format_manifest(self, scope: str = "all") -> str:
        headers = self.scan_all(scope=scope)
        if not headers:
            return ""
        return format_memory_manifest(headers)

    def get_index_content(self, scope: str = "project") -> str:
        path = self._root_for_scope(scope) / INDEX_FILENAME
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8").strip()

    def truncate_index_content(self, raw: str) -> str:
        trimmed = raw.strip()
        if not trimmed:
            return ""
        lines = trimmed.splitlines()
        byte_count = len(trimmed.encode("utf-8"))
        line_truncated = len(lines) > self.max_index_lines
        byte_truncated = byte_count > self.max_index_bytes
        if not line_truncated and not byte_truncated:
            return trimmed

        truncated = "\n".join(lines[: self.max_index_lines]) if line_truncated else trimmed
        while len(truncated.encode("utf-8")) > self.max_index_bytes:
            pos = truncated.rfind("\n")
            if pos <= 0:
                truncated = truncated.encode("utf-8")[: self.max_index_bytes].decode(
                    "utf-8", errors="replace"
                )
                break
            truncated = truncated[:pos]

        warning = (
            "\n\n> WARNING: %s exceeded prompt limits and was truncated." % INDEX_FILENAME
        )
        return truncated + warning

    def get_memory_context(
        self,
        query: str = "",
        conversation: list | None = None,
        include_guidance: bool = False,
    ) -> str:
        parts = []
        relevant = self._select_relevant_items(
            query=query,
            conversation=conversation,
            max_items=self.context_max_relevant_items,
        )
        if relevant:
            relevant_lines = ["## Relevant memories"]
            freshness_index = {header.file_path: header for header in self.scan_all("all")}
            for item in relevant:
                freshness = ""
                header = freshness_index.get(item.file_path)
                if header is not None:
                    freshness = memory_freshness_text(header.mtime_s)
                line = "- %s [%s/%s] %s" % (
                    item.name,
                    item.memory_type,
                    item.scope,
                    item.description or _excerpt(item.content, min(120, self.context_excerpt_chars)),
                )
                if freshness:
                    line += " (%s)" % freshness
                relevant_lines.append(line)
                excerpt = _excerpt(item.content, self.context_excerpt_chars)
                if excerpt and excerpt.lower() != (item.description or "").strip().lower():
                    relevant_lines.append("  detail: %s" % excerpt)
            parts.append("\n".join(relevant_lines))
        inventory_summary = self._build_inventory_summary()
        if inventory_summary:
            parts.append(inventory_summary)
        if not parts:
            return ""
        body_budget = self.context_max_chars
        if include_guidance:
            body_budget = max(
                400,
                self.context_max_chars - len(MEMORY_SYSTEM_PROMPT) - len("\n\n## MEMORY.md\n"),
            )
        body = _fit_blocks_to_budget(parts, body_budget)
        if include_guidance:
            return "%s\n\n## MEMORY.md\n%s" % (MEMORY_SYSTEM_PROMPT, body)
        return body

    def _build_inventory_summary(self) -> str:
        sections = ["## Memory inventory"]
        for scope in ("user", "project"):
            items = self.list_items(scope=scope)
            if not items:
                continue
            labels = []
            for item in items[: self.inventory_max_items]:
                summary = item.description or _excerpt(
                    item.content,
                    min(80, max(40, self.context_excerpt_chars // 2)),
                )
                labels.append("%s (%s)" % (item.name, summary))
            sections.append(
                "- %s memories: %s item(s). Recent: %s"
                % (
                    scope.capitalize(),
                    len(items),
                    "; ".join(labels),
                )
            )
        return "\n".join(sections) if len(sections) > 1 else ""

    def _root_for_scope(self, scope: str) -> Path:
        if scope == "user":
            return self.user_root
        return self.project_root

    def _resolve_scopes(self, scope: str) -> list[str]:
        if scope == "all":
            return ["user", "project"]
        if scope not in {"user", "project"}:
            raise ValueError("Unknown memory scope: %s" % scope)
        return [scope]

    def _path_for(self, slug: str, scope: str) -> Path:
        return self._root_for_scope(scope) / ("%s.md" % slug)

    def _select_relevant_items(
        self,
        query: str,
        conversation: list | None,
        max_items: int = 6,
    ) -> list[MemoryItem]:
        items = self.list_items(scope="all")
        if not items:
            return []
        query_text = self._build_query_text(query, conversation)
        if not query_text:
            return items[:max_items]
        query_terms = _memory_terms(query_text)
        if not query_terms:
            return items[:max_items]
        scored = []
        for item in items:
            scored.append((self._relevance_score(item, query_terms), item))
        scored.sort(
            key=lambda pair: (
                pair[0],
                self._timestamp_value(pair[1].updated_at),
                pair[1].scope == "project",
            ),
            reverse=True,
        )
        selected = [item for score, item in scored if score > 0][:max_items]
        return selected or items[:max_items]

    def _rewrite_index(self, scope: str) -> None:
        entries = self.list_items(scope=scope)
        index_path = self._root_for_scope(scope) / INDEX_FILENAME
        lines = [
            "- [%s](%s.md) - [%s/%s] %s"
            % (item.name, item.slug, item.memory_type, item.scope, item.description)
            for item in entries
        ]
        atomic_write_text(
            index_path,
            ("\n".join(lines) + ("\n" if lines else "")),
            encoding="utf-8",
        )

    def _read_path(self, path: Path, scope: str) -> MemoryItem | None:
        raw = path.read_text(encoding="utf-8", errors="replace")
        metadata, body = parse_frontmatter(raw)
        if not metadata:
            return None
        return MemoryItem(
            slug=metadata.get("slug", path.stem),
            name=metadata.get("name", path.stem),
            description=metadata.get("description", ""),
            memory_type=metadata.get("type", metadata.get("category", "project")),
            scope=metadata.get("scope", scope),
            created_at=metadata.get("created_at", ""),
            updated_at=metadata.get("updated_at", ""),
            content=body.strip(),
            file_path=str(path),
        )

    def _build_query_text(self, query: str, conversation: list | None) -> str:
        parts = [query.strip()]
        for item in (conversation or [])[-8:]:
            role = getattr(item, "role", "")
            if role not in {"user", "assistant"}:
                continue
            parts.append(str(getattr(item, "content", "")).strip())
        return "\n".join(part for part in parts if part)

    def _relevance_score(self, item: MemoryItem, terms: list[str]) -> float:
        haystacks = {
            "name": item.name.lower(),
            "description": item.description.lower(),
            "content": item.content.lower(),
            "type": item.memory_type.lower(),
        }
        score = 0.0
        for term in terms:
            if term in haystacks["name"]:
                score += 5.0
            elif term in haystacks["description"]:
                score += 3.0
            elif term in haystacks["content"]:
                score += 1.5
            elif term in haystacks["type"]:
                score += 1.0
        if item.scope == "project":
            score += 0.5
        age_value = self._timestamp_value(item.updated_at)
        if age_value:
            score += min(2.0, age_value / 10_000_000_000.0)
        return score

    def _search_score(
        self,
        item: MemoryItem,
        query: str,
        terms: list[str],
        document_frequency: dict[str, int],
        document_count: int,
    ) -> tuple[float, list[str]]:
        haystacks = {
            "name": item.name.lower(),
            "description": item.description.lower(),
            "content": item.content.lower(),
            "type": item.memory_type.lower(),
        }
        score = 0.0
        matched: list[str] = []
        if query:
            if query in haystacks["name"]:
                score += 8.0
            elif query in haystacks["description"]:
                score += 5.0
            elif query in haystacks["content"]:
                score += 2.0
        for term in terms:
            term_score = 0.0
            idf = 1.0 + math.log((document_count + 1) / (1 + document_frequency.get(term, 0)))
            if term in haystacks["name"]:
                term_score += 5.0 * idf
            if term in haystacks["description"]:
                term_score += 3.0 * idf
            if term in haystacks["content"]:
                term_score += 1.5 * idf
            if term in haystacks["type"]:
                term_score += 1.0 * idf
            if term_score > 0:
                matched.append(term)
                score += term_score
        if score > 0 and item.scope == "project":
            score += 0.4
        return score, list(dict.fromkeys(matched))

    def _age_days(self, value: str, now_ts: float) -> float | None:
        timestamp = self._timestamp_value(value)
        if not timestamp:
            return None
        return max(0.0, (now_ts - timestamp) / 86_400)

    def _overlap_issues(self, items: list[MemoryItem], max_overlap_pairs: int) -> list[dict[str, object]]:
        if max_overlap_pairs <= 0 or len(items) < 2:
            return []
        term_index = {
            (item.scope, item.slug): set(_memory_terms("\n".join([item.name, item.description, item.content])))
            for item in items
        }
        scored: list[tuple[float, MemoryItem, MemoryItem]] = []
        for left_index, left in enumerate(items):
            left_terms = term_index.get((left.scope, left.slug), set())
            if len(left_terms) < 4:
                continue
            for right in items[left_index + 1 :]:
                right_terms = term_index.get((right.scope, right.slug), set())
                if len(right_terms) < 4:
                    continue
                overlap = len(left_terms & right_terms) / max(1, min(len(left_terms), len(right_terms)))
                if overlap >= 0.82:
                    scored.append((overlap, left, right))
        scored.sort(key=lambda row: row[0], reverse=True)
        issues = []
        for overlap, left, right in scored[:max_overlap_pairs]:
            issues.append(
                _health_issue(
                    issue_type="overlap",
                    severity="medium",
                    slug=left.slug,
                    scope=left.scope,
                    description="`%s` and `%s` appear to cover nearly the same memory." % (left.name, right.name),
                    suggestion="Merge these memories or archive the less useful one.",
                    metadata={
                        "other_slug": right.slug,
                        "other_scope": right.scope,
                        "similarity": round(overlap, 4),
                    },
                )
            )
        return issues

    def _timestamp_value(self, value: str) -> float:
        normalized = (value or "").strip()
        if not normalized:
            return 0.0
        try:
            return datetime.fromisoformat(normalized.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return 0.0


def _excerpt(text: str, limit: int) -> str:
    cleaned = " ".join((text or "").split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3] + "..."


def _memory_terms(text: str) -> list[str]:
    lowered = (text or "").lower()
    raw_terms = re.findall(r"[a-z0-9_./-]{2,}|[\u4e00-\u9fff]{2,}", lowered)
    terms = []
    for term in raw_terms:
        normalized = term.strip("-_./")
        if len(normalized) < 2 or normalized in _MEMORY_STOPWORDS:
            continue
        terms.append(normalized)
        if re.fullmatch(r"[\u4e00-\u9fff]+", normalized) and len(normalized) > 2:
            terms.extend(normalized[index : index + 2] for index in range(len(normalized) - 1))
    return list(dict.fromkeys(terms))


def _memory_slug(name: str) -> str:
    slug = slugify(name)
    if slug != "item" or not (name or "").strip():
        return slug
    digest = hashlib.sha1(name.strip().encode("utf-8")).hexdigest()[:10]
    return "memory-%s" % digest


def _memory_risk_flags(text: str) -> list[str]:
    flags = []
    for name, pattern in _UNSAFE_MEMORY_PATTERNS:
        if pattern.search(text or ""):
            flags.append(name)
    return list(dict.fromkeys(flags))


def _health_issue(
    issue_type: str,
    severity: str,
    slug: str,
    scope: str,
    description: str,
    suggestion: str,
    metadata: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "type": issue_type,
        "severity": severity,
        "slug": slug,
        "scope": scope,
        "description": description,
        "suggestion": suggestion,
        "metadata": metadata or {},
    }


def _memory_recommendations(issues: list[dict[str, object]]) -> list[str]:
    if not issues:
        return ["Memory inventory is clean; keep using focused, durable memories."]
    issue_types = {str(item.get("type", "")) for item in issues}
    recommendations = []
    if "instruction-risk" in issue_types:
        recommendations.append("Review high-risk memories before injecting them into prompts.")
    if "overlap" in issue_types:
        recommendations.append("Consolidate overlapping memories so retrieval stays precise as the project grows.")
    if "large" in issue_types:
        recommendations.append("Compress large memories into short durable facts and link to raw artifacts.")
    if "stale" in issue_types:
        recommendations.append("Refresh or archive stale memories during the next project maintenance pass.")
    return recommendations


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
        shortened = normalized[: max(0, remaining - 3)].rstrip() + "..."
        selected.append(shortened)
        break
    return "\n\n".join(selected).strip()
