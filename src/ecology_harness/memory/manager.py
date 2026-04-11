from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
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
        slug = slugify(name)
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
        needle = query.lower()
        results = []
        header_index = {header.file_path: header for header in self.scan_all(scope)}
        for item in self.list_items(scope=scope):
            haystack = "\n".join(
                [item.name, item.description, item.memory_type, item.content]
            ).lower()
            if needle not in haystack:
                continue
            header = header_index.get(item.file_path)
            result = item.to_index_dict()
            result["content"] = item.content
            result["freshness_text"] = (
                memory_freshness_text(header.mtime_s) if header is not None else ""
            )
            results.append(result)
        return results[:max_results]

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
        query_terms = [
            term
            for term in re.findall(r"[A-Za-z0-9_./-]{3,}", query_text.lower())
            if term not in {"tool", "read", "write", "with", "from", "that", "this"}
        ]
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
