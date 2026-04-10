from __future__ import annotations

from dataclasses import dataclass, field
import difflib
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ecology_harness.skills.retrieval import tokenize_text

if TYPE_CHECKING:
    from ecology_harness.skills.loader import Skill


HUB_SOURCE_DEFAULT = "https://github.com/ECNU-ICALK/Ecology-Harness"
SKILL_HUB_PACKS: dict[str, dict[str, str]] = {
    "core": {
        "title": "Core Built-ins",
        "description": "Project-authored core workflow skills maintained inside Ecology Harness.",
        "trust_level": "official",
        "audit_status": "reviewed",
        "source_url": HUB_SOURCE_DEFAULT,
    },
    "ecology": {
        "title": "Ecology Pack",
        "description": "Ecology, environment, agriculture, simulation, and multimodal research workflows curated for Ecology Harness.",
        "trust_level": "official",
        "audit_status": "reviewed",
        "source_url": HUB_SOURCE_DEFAULT,
    },
    "scientific": {
        "title": "Scientific Skills",
        "description": "Vendored scientific research workflow skills curated from the K-Dense scientific-skills collection.",
        "trust_level": "trusted",
        "audit_status": "vendored",
        "source_url": "https://github.com/K-Dense-AI/claude-scientific-skills/tree/main/scientific-skills",
    },
    "superpowers": {
        "title": "Superpowers Skills",
        "description": "Workflow and engineering guidance vendored from obra/superpowers.",
        "trust_level": "community",
        "audit_status": "vendored",
        "source_url": "https://github.com/obra/superpowers/tree/main/skills",
    },
    "writing": {
        "title": "Writing Skills",
        "description": "Writing cleanup and style-focused helpers, including humanizer.",
        "trust_level": "community",
        "audit_status": "vendored",
        "source_url": "https://github.com/blader/humanizer",
    },
    "ai-research": {
        "title": "AI Research Skills",
        "description": "Large AI research workflow bundle vendored from Orchestra Research.",
        "trust_level": "community",
        "audit_status": "vendored",
        "source_url": "https://github.com/Orchestra-Research/AI-Research-SKILLs/tree/main",
    },
    "project": {
        "title": "Project Skills",
        "description": "Project-local skills defined inside the current workspace.",
        "trust_level": "local",
        "audit_status": "workspace",
        "source_url": "",
    },
    "user": {
        "title": "User Skills",
        "description": "User-local skills installed for this workstation profile.",
        "trust_level": "local",
        "audit_status": "workspace",
        "source_url": "",
    },
}
SKILL_HUB_ORDER = {
    "core": 0,
    "ecology": 1,
    "scientific": 2,
    "superpowers": 3,
    "writing": 4,
    "ai-research": 5,
    "project": 6,
    "user": 7,
}


@dataclass
class SkillHubEntry:
    slug: str
    title: str
    description: str
    trust_level: str
    audit_status: str
    source_url: str
    source: str
    root_path: str
    skill_count: int = 0
    active_count: int = 0
    ready_count: int = 0
    setup_needed_count: int = 0
    unsupported_count: int = 0
    top_skills: list[str] = field(default_factory=list)
    authors: list[str] = field(default_factory=list)
    licenses: list[str] = field(default_factory=list)
    score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "title": self.title,
            "description": self.description,
            "trust_level": self.trust_level,
            "audit_status": self.audit_status,
            "source_url": self.source_url,
            "source": self.source,
            "root_path": self.root_path,
            "skill_count": self.skill_count,
            "active_count": self.active_count,
            "ready_count": self.ready_count,
            "setup_needed_count": self.setup_needed_count,
            "unsupported_count": self.unsupported_count,
            "top_skills": self.top_skills,
            "authors": self.authors,
            "licenses": self.licenses,
            "score": round(self.score, 4),
        }


def _unique_text(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = (value or "").strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(normalized)
    return result


class SkillCatalog:
    def __init__(self, builtin_dir: Path, user_dir: Path, project_dir: Path) -> None:
        self.builtin_dir = builtin_dir
        self.user_dir = user_dir
        self.project_dir = project_dir

    def build_hub_entries(
        self,
        skills: list[Skill],
        query: str = "",
        limit: int = 12,
    ) -> list[SkillHubEntry]:
        grouped: dict[str, list[Skill]] = {}
        for skill in skills:
            grouped.setdefault(skill.hub_pack, []).append(skill)

        query_tokens = tokenize_text(query)
        entries: list[SkillHubEntry] = []
        for pack_slug, pack_skills in grouped.items():
            meta = SKILL_HUB_PACKS.get(pack_slug, SKILL_HUB_PACKS["core"])
            ready_count = len([item for item in pack_skills if item.readiness == "ready"])
            setup_needed_count = len([item for item in pack_skills if item.readiness == "setup-needed"])
            unsupported_count = len([item for item in pack_skills if item.readiness == "unsupported"])
            active_count = len([item for item in pack_skills if item.status == "active"])
            top_skills = [item.slug for item in sorted(pack_skills, key=lambda item: item.name.lower())[:8]]
            authors = _unique_text([item.author for item in pack_skills if item.author])[:6]
            licenses = _unique_text([item.license for item in pack_skills if item.license])[:6]
            entries.append(
                SkillHubEntry(
                    slug=pack_slug,
                    title=meta["title"],
                    description=meta["description"],
                    trust_level=meta["trust_level"],
                    audit_status=meta["audit_status"],
                    source_url=meta["source_url"],
                    source=pack_skills[0].source if pack_skills else pack_slug,
                    root_path=str(self.root_for_pack(pack_slug)),
                    skill_count=len(pack_skills),
                    active_count=active_count,
                    ready_count=ready_count,
                    setup_needed_count=setup_needed_count,
                    unsupported_count=unsupported_count,
                    top_skills=top_skills,
                    authors=authors,
                    licenses=licenses,
                    score=self._hub_pack_score(pack_slug, pack_skills, query_tokens),
                )
            )
        entries.sort(
            key=lambda item: (
                -item.score,
                SKILL_HUB_ORDER.get(item.slug, 100),
                item.title.lower(),
            )
        )
        return entries[: max(limit, 1) * 2]

    def build_view(
        self,
        skill: Skill,
        file_path: str = "",
        max_chars: int = 6000,
    ) -> dict[str, Any]:
        bundle_root = self.bundle_root(skill)
        available_files = self.list_skill_files(skill)
        if file_path.strip():
            resolved, relative_path = self.resolve_skill_file(skill, file_path)
            content = resolved.read_text(encoding="utf-8")
            truncated = len(content) > max_chars
            if truncated:
                content = content[:max_chars].rstrip() + "\n\n...[truncated]"
            return {
                "skill": skill.to_index_dict(),
                "bundle_root": str(bundle_root),
                "available_files": available_files,
                "selected_file": {
                    "relative_path": relative_path,
                    "absolute_path": str(resolved),
                    "kind": self.skill_file_kind(relative_path),
                },
                "content": content,
                "truncated": truncated,
            }

        preview = skill.content
        truncated = len(preview) > max_chars
        if truncated:
            preview = preview[:max_chars].rstrip() + "\n\n...[truncated]"
        return {
            "skill": skill.to_index_dict(),
            "bundle_root": str(bundle_root),
            "available_files": available_files,
            "selected_file": {
                "relative_path": skill.path.name,
                "absolute_path": str(skill.path),
                "kind": "main",
            },
            "content": preview,
            "truncated": truncated,
        }

    def bundle_root(self, skill: Skill) -> Path:
        return Path(skill.bundle_root) if skill.bundle_root else skill.path.parent

    def list_skill_files(self, skill: Skill, limit: int = 120) -> list[dict[str, str]]:
        bundle_root = self.bundle_root(skill)
        if skill.path.name != "SKILL.md":
            return [
                {
                    "relative_path": skill.path.name,
                    "absolute_path": str(skill.path),
                    "kind": "main",
                }
            ]
        files: list[dict[str, str]] = []
        for path in sorted(bundle_root.rglob("*")):
            if not path.is_file():
                continue
            if any(part.startswith(".") for part in path.relative_to(bundle_root).parts):
                continue
            relative_path = str(path.relative_to(bundle_root))
            files.append(
                {
                    "relative_path": relative_path,
                    "absolute_path": str(path),
                    "kind": self.skill_file_kind(relative_path),
                }
            )
            if len(files) >= limit:
                break
        return files

    def resolve_skill_file(self, skill: Skill, file_path: str) -> tuple[Path, str]:
        normalized = file_path.strip().replace("\\", "/")
        if not normalized:
            raise ValueError("file_path cannot be empty.")
        bundle_root = self.bundle_root(skill)
        available = [item["relative_path"] for item in self.list_skill_files(skill)]
        if skill.path.name != "SKILL.md":
            if normalized not in {skill.path.name, str(skill.path)}:
                raise ValueError("Non-bundle skill only supports `%s`." % skill.path.name)
            return skill.path, skill.path.name
        resolved = (bundle_root / normalized).resolve()
        try:
            resolved.relative_to(bundle_root.resolve())
        except ValueError as exc:
            raise ValueError("file_path must stay inside the skill bundle.") from exc
        if not resolved.exists() or not resolved.is_file():
            suggestion = difflib.get_close_matches(normalized, available, n=1, cutoff=0.45)
            if suggestion:
                raise ValueError("Skill file not found: %s. Did you mean `%s`?" % (normalized, suggestion[0]))
            raise ValueError("Skill file not found: %s" % normalized)
        return resolved, str(resolved.relative_to(bundle_root))

    @staticmethod
    def skill_file_kind(relative_path: str) -> str:
        normalized = relative_path.replace("\\", "/")
        if "/" not in normalized:
            return "main"
        return normalized.split("/", 1)[0]

    def root_for_pack(self, pack_slug: str) -> Path:
        if pack_slug == "user":
            return self.user_dir
        if pack_slug == "project":
            return self.project_dir
        if pack_slug == "core":
            return self.builtin_dir
        return self.builtin_dir / pack_slug

    def _hub_pack_score(self, pack_slug: str, skills: list[Skill], query_tokens: list[str]) -> float:
        if not query_tokens:
            return 1.0 - (SKILL_HUB_ORDER.get(pack_slug, 100) / 1000.0)
        meta = SKILL_HUB_PACKS.get(pack_slug, SKILL_HUB_PACKS["core"])
        haystack = " ".join(
            [
                pack_slug,
                meta["title"],
                meta["description"],
                " ".join(skill.slug for skill in skills[:20]),
                " ".join(skill.description for skill in skills[:8]),
            ]
        )
        tokens = set(tokenize_text(haystack))
        matched = sum(1 for token in query_tokens if token in tokens)
        exact_bonus = 0.4 if pack_slug in " ".join(query_tokens) else 0.0
        skill_bonus = min(
            0.4,
            len(
                [
                    item
                    for item in skills
                    if any(token in self._overlap_document(item).lower() for token in query_tokens)
                ]
            )
            * 0.03,
        )
        return matched / max(len(query_tokens), 1) + exact_bonus + skill_bonus

    @staticmethod
    def _overlap_document(skill: Skill) -> str:
        pieces = [
            skill.slug,
            skill.name,
            skill.description,
            " ".join(skill.triggers),
            skill.when_to_use,
            skill.content[:4000],
        ]
        return "\n".join(piece for piece in pieces if piece)
