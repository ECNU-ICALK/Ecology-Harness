from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ecology_harness.utils import parse_frontmatter, slugify


@dataclass
class Skill:
    slug: str
    name: str
    description: str
    source: str
    content: str
    triggers: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    when_to_use: str = ""
    argument_hint: str = ""
    arguments: list[str] = field(default_factory=list)
    model: str = ""
    context: str = "inline"
    user_invocable: bool = True

    def to_index_dict(self) -> dict[str, str]:
        return {
            "slug": self.slug,
            "name": self.name,
            "description": self.description,
            "source": self.source,
            "context": self.context,
            "triggers": ", ".join(self.triggers),
        }


def _parse_list(value: str) -> list[str]:
    raw = value.strip()
    if not raw:
        return []
    if raw.startswith("[") and raw.endswith("]"):
        raw = raw[1:-1]
    return [item.strip().strip('"').strip("'") for item in raw.split(",") if item.strip()]


class SkillLoader:
    def __init__(self, builtin_dir: Path, user_dir: Path, project_dir: Path) -> None:
        self.builtin_dir = builtin_dir
        self.user_dir = user_dir
        self.project_dir = project_dir
        self.user_dir.mkdir(parents=True, exist_ok=True)
        self.project_dir.mkdir(parents=True, exist_ok=True)

    def list_skills(self) -> list[Skill]:
        seen: dict[str, Skill] = {}
        for source, root in (
            ("builtin", self.builtin_dir),
            ("user", self.user_dir),
            ("project", self.project_dir),
        ):
            if not root.exists():
                continue
            for path in sorted(root.rglob("*.md")):
                skill = self._load_path(path, source)
                seen[skill.slug] = skill
        return sorted(seen.values(), key=lambda item: item.name.lower())

    def get(self, slug_or_name: str) -> Skill | None:
        normalized = slugify(slug_or_name)
        for skill in self.list_skills():
            if skill.slug == normalized or skill.name == slug_or_name:
                return skill
        return None

    def find_by_trigger(self, query: str) -> Skill | None:
        first = query.strip().split(" ", 1)[0] if query.strip() else ""
        if not first:
            return None
        for skill in self.list_skills():
            for trigger in skill.triggers:
                if trigger == first:
                    return skill
        return None

    def render(self, skill: Skill, args: str) -> str:
        rendered = skill.content.replace("$ARGUMENTS", args)
        values = args.split()
        for idx, name in enumerate(skill.arguments):
            rendered = rendered.replace(
                "$%s" % name.upper(),
                values[idx] if idx < len(values) else "",
            )
        return rendered

    def _load_path(self, path: Path, source: str) -> Skill:
        raw = path.read_text(encoding="utf-8")
        metadata, body = parse_frontmatter(raw)
        name = metadata.get("name", path.stem)
        slug = metadata.get("slug", slugify(name))
        description = metadata.get("description", "")
        triggers = _parse_list(metadata.get("triggers", "")) or ["/%s" % slug]
        tools = _parse_list(metadata.get("allowed-tools", metadata.get("tools", "")))
        arguments = _parse_list(metadata.get("arguments", ""))
        context = metadata.get("context", "inline").strip().lower() or "inline"
        if context not in {"inline", "fork"}:
            context = "inline"
        user_invocable = metadata.get("user-invocable", "true").lower() not in {
            "false",
            "0",
            "no",
        }
        return Skill(
            slug=slug,
            name=name,
            description=description,
            source=source,
            content=body.strip(),
            triggers=triggers,
            tools=tools,
            when_to_use=metadata.get("when_to_use", ""),
            argument_hint=metadata.get("argument-hint", ""),
            arguments=arguments,
            model=metadata.get("model", ""),
            context=context,
            user_invocable=user_invocable,
        )
