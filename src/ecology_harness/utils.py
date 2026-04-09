from __future__ import annotations

import re


def slugify(value: str) -> str:
    normalized = value.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = normalized.strip("-")
    return normalized or "item"


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text

    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        return {}, text

    header, body = parts
    metadata: dict[str, str] = {}
    lines = header.splitlines()[1:]
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip() or line.startswith(" ") or ":" not in line:
            index += 1
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()

        if value in {"|", ">"}:
            index += 1
            block_lines: list[str] = []
            while index < len(lines):
                current = lines[index]
                if current.startswith(" ") or current.startswith("\t"):
                    block_lines.append(current.lstrip())
                    index += 1
                    continue
                break
            metadata[key] = (
                "\n".join(block_lines).strip()
                if value == "|"
                else " ".join(item.strip() for item in block_lines).strip()
            )
            continue

        if value == "":
            probe = index + 1
            list_items: list[str] = []
            while probe < len(lines):
                current = lines[probe]
                stripped = current.strip()
                if current.startswith(" ") or current.startswith("\t"):
                    if stripped.startswith("- "):
                        list_items.append(stripped[2:].strip())
                    probe += 1
                    continue
                break
            if list_items:
                metadata[key] = "[%s]" % ", ".join(list_items)
                index = probe
                continue

        metadata[key] = value
        index += 1
    return metadata, body


def dump_frontmatter(metadata: dict[str, str], body: str) -> str:
    lines = ["---"]
    for key, value in metadata.items():
        lines.append("%s: %s" % (key, value))
    lines.append("---")
    lines.append(body)
    return "\n".join(lines)
