from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import time

from ecology_harness.utils import parse_frontmatter


@dataclass
class MemoryHeader:
    filename: str
    file_path: str
    mtime_s: float
    description: str
    memory_type: str
    scope: str


def memory_age_days(mtime_s: float) -> int:
    return max(0, math.floor((time.time() - mtime_s) / 86_400))


def memory_age_str(mtime_s: float) -> str:
    age = memory_age_days(mtime_s)
    if age == 0:
        return "today"
    if age == 1:
        return "yesterday"
    return "%s days ago" % age


def memory_freshness_text(mtime_s: float) -> str:
    age = memory_age_days(mtime_s)
    if age <= 1:
        return ""
    return (
        "This memory is %s days old. Verify code or workspace claims against current state."
        % age
    )


def scan_memory_dir(mem_dir: Path, scope: str, index_filename: str) -> list[MemoryHeader]:
    if not mem_dir.is_dir():
        return []
    headers = []
    for path in sorted(mem_dir.glob("*.md")):
        if path.name == index_filename:
            continue
        try:
            stat = path.stat()
            raw = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        metadata, _ = parse_frontmatter(raw)
        headers.append(
            MemoryHeader(
                filename=path.name,
                file_path=str(path),
                mtime_s=stat.st_mtime,
                description=metadata.get("description", ""),
                memory_type=metadata.get("type", metadata.get("category", "")),
                scope=scope,
            )
        )
    headers.sort(key=lambda item: item.mtime_s, reverse=True)
    return headers


def format_memory_manifest(headers: list[MemoryHeader]) -> str:
    lines = []
    for item in headers:
        tag = "[%s/%s]" % (item.memory_type or "general", item.scope)
        age = memory_age_str(item.mtime_s)
        if item.description:
            lines.append("- %s %s (%s): %s" % (tag, item.filename, age, item.description))
        else:
            lines.append("- %s %s (%s)" % (tag, item.filename, age))
    return "\n".join(lines)
