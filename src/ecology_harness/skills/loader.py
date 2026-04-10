from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import difflib
import json
import os
from pathlib import Path
import platform
import subprocess
import shutil
import tempfile
from typing import Any

from ecology_harness.runtime.messages import ChatMessage
from ecology_harness.skills.catalog import (
    SKILL_HUB_ORDER,
    SKILL_HUB_PACKS,
    SkillCatalog,
)
from ecology_harness.skills.retrieval import (
    SkillBM25Retriever,
    SkillQueryRewriter,
    SkillSearchHit,
    SkillSearchReport,
    tokenize_text,
)
from ecology_harness.skills.state_store import SkillStateStore
from ecology_harness.utils import atomic_write_text, parse_frontmatter, slugify


_SKILL_STATUS_VALUES = {"active", "deprecated", "archived"}

@dataclass
class Skill:
    slug: str
    name: str
    description: str
    source: str
    content: str
    path: Path
    triggers: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    when_to_use: str = ""
    argument_hint: str = ""
    arguments: list[str] = field(default_factory=list)
    model: str = ""
    context: str = "inline"
    user_invocable: bool = True
    category: str = ""
    requirements: list[str] = field(default_factory=list)
    platforms: list[str] = field(default_factory=list)
    setup: str = ""
    setup_required: bool = False
    readiness: str = "ready"
    missing_requirements: list[str] = field(default_factory=list)
    bundle_root: str = ""
    status: str = "active"
    usage_count: int = 0
    last_used_at: str = ""
    last_used_query: str = ""
    retrieval_count: int = 0
    last_retrieved_at: str = ""
    deprecated_at: str = ""
    deprecation_reason: str = ""
    archived_at: str = ""
    archive_reason: str = ""
    superseded_by: str = ""
    author: str = ""
    license: str = ""
    compatibility: list[str] = field(default_factory=list)
    hub_pack: str = "core"
    trust_level: str = "official"
    upstream_url: str = ""
    audit_status: str = "reviewed"

    def to_index_dict(self) -> dict[str, str]:
        return {
            "slug": self.slug,
            "name": self.name,
            "description": self.description,
            "source": self.source,
            "context": self.context,
            "triggers": ", ".join(self.triggers),
            "path": str(self.path),
            "readiness": self.readiness,
            "category": self.category,
            "requirements": ", ".join(self.requirements),
            "platforms": ", ".join(self.platforms),
            "setup": self.setup,
            "status": self.status,
            "usage_count": str(self.usage_count),
            "last_used_at": self.last_used_at,
            "last_used_query": self.last_used_query,
            "retrieval_count": str(self.retrieval_count),
            "last_retrieved_at": self.last_retrieved_at,
            "deprecated_at": self.deprecated_at,
            "deprecation_reason": self.deprecation_reason,
            "archived_at": self.archived_at,
            "archive_reason": self.archive_reason,
            "superseded_by": self.superseded_by,
            "author": self.author,
            "license": self.license,
            "compatibility": ", ".join(self.compatibility),
            "hub_pack": self.hub_pack,
            "trust_level": self.trust_level,
            "upstream_url": self.upstream_url,
            "audit_status": self.audit_status,
        }


@dataclass
class SkillOverlap:
    primary_slug: str
    secondary_slug: str
    primary_source: str
    secondary_source: str
    score: float
    shared_terms: list[str] = field(default_factory=list)
    recommendation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "primary_slug": self.primary_slug,
            "secondary_slug": self.secondary_slug,
            "primary_source": self.primary_source,
            "secondary_source": self.secondary_source,
            "score": round(self.score, 4),
            "shared_terms": self.shared_terms,
            "recommendation": self.recommendation,
        }


def _parse_list(value: str) -> list[str]:
    raw = value.strip()
    if not raw:
        return []
    if raw.startswith("[") and raw.endswith("]"):
        raw = raw[1:-1]
    return [item.strip().strip('"').strip("'") for item in raw.split(",") if item.strip()]


def _stringify_list(values: list[str]) -> str:
    return "[%s]" % ", ".join(_unique_text(values))


def _platform_aliases() -> set[str]:
    current = platform.system().strip().lower()
    aliases = {current}
    if current == "darwin":
        aliases.update({"mac", "macos", "osx"})
    elif current == "windows":
        aliases.add("win32")
    elif current == "linux":
        aliases.add("gnu/linux")
    return aliases


def _evaluate_requirements(requirements: list[str]) -> list[str]:
    missing: list[str] = []
    for requirement in requirements:
        token = requirement.strip()
        if not token:
            continue
        lowered = token.lower()
        if lowered.startswith("env:"):
            env_name = token.split(":", 1)[1].strip()
            if env_name and not os.environ.get(env_name):
                missing.append("env:%s" % env_name)
            continue
        if lowered.startswith("command:") or lowered.startswith("binary:"):
            command = token.split(":", 1)[1].strip()
            if command and shutil.which(command) is None:
                missing.append("command:%s" % command)
            continue
        if lowered.startswith("python:"):
            module_name = token.split(":", 1)[1].strip()
            if not module_name:
                continue
            try:
                __import__(module_name)
            except Exception:
                missing.append("python:%s" % module_name)
            continue
        if token.isupper() and "_" in token:
            if not os.environ.get(token):
                missing.append("env:%s" % token)
            continue
        if shutil.which(token) is None:
            missing.append("command:%s" % token)
    return missing


def _evaluate_readiness(
    platforms: list[str],
    requirements: list[str],
    setup_required: bool,
) -> tuple[str, list[str]]:
    normalized_platforms = {item.strip().lower() for item in platforms if item.strip()}
    if normalized_platforms and not (_platform_aliases() & normalized_platforms):
        return "unsupported", []
    missing = _evaluate_requirements(requirements)
    if missing or setup_required:
        return "setup-needed", missing
    return "ready", []


def _utcnow() -> str:
    return datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse_timestamp(value: str) -> datetime | None:
    text = (value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


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


def _merge_text(existing: str, incoming: str) -> str:
    left = (existing or "").strip()
    right = (incoming or "").strip()
    if not left:
        return right
    if not right:
        return left
    if left == right:
        return left
    if right.lower() in left.lower():
        return left
    if left.lower() in right.lower():
        return right
    return "%s %s" % (left, right)


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


def _skill_source_priority(skill: Skill) -> tuple[int, int, float, str]:
    source_rank = {"builtin": 3, "project": 2, "user": 1}.get(skill.source, 0)
    last_used = _parse_timestamp(skill.last_used_at)
    last_used_epoch = last_used.timestamp() if last_used is not None else 0.0
    return (source_rank, skill.usage_count, last_used_epoch, skill.slug)


class SkillLoader:
    @classmethod
    def from_settings(cls, settings: Any) -> "SkillLoader":
        builtin_dir = Path(__file__).resolve().parent / "builtin"
        return cls(
            builtin_dir=builtin_dir,
            user_dir=settings.user_skill_dir,
            project_dir=settings.skill_dir,
            history_turns=getattr(settings, "skill_retrieval_history_turns", 4),
        )

    def __init__(
        self,
        builtin_dir: Path,
        user_dir: Path,
        project_dir: Path,
        history_turns: int = 4,
    ) -> None:
        self.builtin_dir = builtin_dir
        self.user_dir = user_dir
        self.project_dir = project_dir
        self.history_turns = history_turns
        self.user_dir.mkdir(parents=True, exist_ok=True)
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.state_store = SkillStateStore(self.project_dir)
        self.catalog = SkillCatalog(self.builtin_dir, self.user_dir, self.project_dir)
        self._cached_signature = ""
        self._cached_skills: list[Skill] = []
        self._cached_runtime_signature = ""

    def list_skills(self, include_archived: bool = False) -> list[Skill]:
        directory_signature, file_entries = self._directory_signature()
        governance = self._load_governance()
        governance_signature = self._governance_signature(governance)
        combined_signature = "%s\n##governance##\n%s" % (directory_signature, governance_signature)
        if combined_signature == self._cached_signature and self._cached_skills:
            runtime_signature = self._runtime_signature(self._cached_skills)
            if runtime_signature != self._cached_runtime_signature:
                self._cached_skills = [
                    self._refresh_skill_state(item, governance) for item in self._cached_skills
                ]
                self._cached_runtime_signature = runtime_signature
            return self._filtered_skills(self._cached_skills, include_archived=include_archived)

        snapshot = self._load_snapshot()
        if snapshot and snapshot.get("signature") == directory_signature:
            loaded = self._skills_from_snapshot(snapshot)
            if loaded:
                self._cached_signature = combined_signature
                self._cached_skills = [
                    self._refresh_skill_state(item, governance) for item in loaded
                ]
                self._cached_runtime_signature = self._runtime_signature(self._cached_skills)
                return self._filtered_skills(self._cached_skills, include_archived=include_archived)

        seen: dict[str, Skill] = {}
        for source, path in file_entries:
            skill = self._load_path(path, source)
            if skill is None:
                continue
            seen[skill.slug] = skill
        skills = sorted(seen.values(), key=lambda item: item.name.lower())
        self._cached_signature = combined_signature
        self._cached_skills = [self._refresh_skill_state(item, governance) for item in skills]
        self._cached_runtime_signature = self._runtime_signature(self._cached_skills)
        self._write_snapshot(directory_signature, skills)
        return self._filtered_skills(self._cached_skills, include_archived=include_archived)

    def get(self, slug_or_name: str, include_archived: bool = False) -> Skill | None:
        normalized = slugify(slug_or_name)
        for skill in self.list_skills(include_archived=include_archived):
            if skill.slug == normalized or skill.name == slug_or_name:
                return skill
        return None

    def skill_hub(
        self,
        query: str = "",
        limit: int = 12,
        scope: str = "all",
    ) -> dict[str, Any]:
        normalized_scope = (scope or "all").strip().lower()
        if normalized_scope not in {"all", "packs", "skills"}:
            normalized_scope = "all"
        skills = self.list_skills(include_archived=True)
        packs = self.catalog.build_hub_entries(skills, query=query, limit=limit)
        result: dict[str, Any] = {
            "query": query,
            "scope": normalized_scope,
            "packs": [],
            "skills": [],
        }
        if normalized_scope in {"all", "packs"}:
            result["packs"] = [item.to_dict() for item in packs[:limit]]
        if normalized_scope in {"all", "skills"}:
            if query.strip():
                search_report = self.search(
                    query=query,
                    limit=max(limit, 1),
                    user_invocable_only=False,
                )
                skill_rows = []
                for hit in search_report.hits[:limit]:
                    payload = hit.skill.to_index_dict()
                    payload["score"] = round(hit.score, 4)
                    payload["matched_terms"] = ", ".join(hit.matched_terms)
                    skill_rows.append(payload)
                result["skills"] = skill_rows
                result["rewrite"] = search_report.rewrite.to_dict()
            else:
                ordered = sorted(
                    skills,
                    key=lambda item: (
                        SKILL_HUB_ORDER.get(item.hub_pack, 100),
                        item.hub_pack,
                        item.name.lower(),
                    ),
                )
                result["skills"] = [item.to_index_dict() for item in ordered[:limit]]
        return result

    def view(
        self,
        slug_or_name: str,
        file_path: str = "",
        max_chars: int = 6000,
    ) -> dict[str, Any]:
        skill = self.get(slug_or_name, include_archived=True)
        if skill is None:
            raise ValueError("Skill not found: %s" % slug_or_name)
        return self.catalog.build_view(skill, file_path=file_path, max_chars=max_chars)

    def search(
        self,
        query: str,
        conversation: list[ChatMessage] | None = None,
        limit: int = 8,
        user_invocable_only: bool = True,
    ) -> SkillSearchReport:
        skills = self.list_skills()
        if user_invocable_only:
            skills = [item for item in skills if item.user_invocable]
        rewriter = SkillQueryRewriter(history_turns=self.history_turns)
        rewrite = rewriter.rewrite(query, conversation=conversation)
        retriever = SkillBM25Retriever(skills)
        hits = retriever.search(rewrite, limit=limit)
        return SkillSearchReport(
            rewrite=rewrite,
            hits=hits,
            total_skills=len(skills),
            fallback_used=False,
        )

    def select_for_prompt(
        self,
        query: str,
        conversation: list[ChatMessage] | None = None,
        limit: int = 8,
    ) -> SkillSearchReport:
        report = self.search(
            query=query,
            conversation=conversation,
            limit=limit,
            user_invocable_only=True,
        )
        self.record_retrievals(report.hits)
        if report.hits or not limit:
            return report

        fallback = [
            item for item in self.list_skills() if item.user_invocable
        ][:limit]
        report.hits = [
            SkillSearchHit(
                skill=item,
                score=0.0,
                matched_terms=[],
                exact_match=False,
            )
            for item in fallback
        ]
        report.fallback_used = True
        return report

    def find_by_trigger(self, query: str) -> Skill | None:
        first = query.strip().split(" ", 1)[0] if query.strip() else ""
        if not first:
            return None
        for skill in self.list_skills():
            if skill.status == "archived":
                continue
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
        if skill.path.name == "SKILL.md":
            rendered = (
                "Skill bundle root: %s\n"
                "Resolve any relative files from that directory. If the workflow mentions scripts or references, run shell commands with that directory as the working directory.\n\n%s"
                % (skill.path.parent, rendered)
            )
        if skill.status == "deprecated":
            note = "Skill status: deprecated"
            if skill.superseded_by:
                note += " (prefer `%s`)" % skill.superseded_by
            if skill.deprecation_reason:
                note += " - %s" % skill.deprecation_reason
            rendered = "%s\n\n%s" % (note, rendered)
        if skill.readiness == "setup-needed":
            readiness_note = "Skill readiness: setup-needed"
            if skill.missing_requirements:
                readiness_note += " (%s)" % ", ".join(skill.missing_requirements)
            rendered = "%s\n%s\n\n%s" % (readiness_note, "Follow any setup notes before use.", rendered)
        elif skill.readiness == "unsupported":
            rendered = "Skill readiness: unsupported on this platform.\n\n%s" % rendered
        return rendered

    def record_usage(
        self,
        skill_or_slug: Skill | str,
        query: str = "",
        mode: str = "execute",
        session_id: str = "",
    ) -> dict[str, Any]:
        skill = skill_or_slug if isinstance(skill_or_slug, Skill) else self.get(str(skill_or_slug), include_archived=True)
        if skill is None:
            raise ValueError("Skill not found: %s" % skill_or_slug)
        governance = self._load_governance()
        record = governance.setdefault("skills", {}).setdefault(skill.slug, {})
        record["source"] = skill.source
        record["path"] = str(skill.path)
        record["usage_count"] = int(record.get("usage_count", 0) or 0) + 1
        record["last_used_at"] = _utcnow()
        if query:
            record["last_used_query"] = query.strip()[:400]
        if mode:
            record["last_used_mode"] = mode
        if session_id:
            record["last_session_id"] = session_id
        if record.get("status") not in _SKILL_STATUS_VALUES:
            record["status"] = "active"
        self._write_governance(governance)
        self._mark_cache_dirty()
        return dict(record)

    def record_retrievals(self, hits: list[SkillSearchHit]) -> None:
        if not hits:
            return
        governance = self._load_governance()
        changed = False
        for hit in hits:
            skill = hit.skill
            record = governance.setdefault("skills", {}).setdefault(skill.slug, {})
            record["source"] = skill.source
            record["path"] = str(skill.path)
            record["retrieval_count"] = int(record.get("retrieval_count", 0) or 0) + 1
            record["last_retrieved_at"] = _utcnow()
            changed = True
        if changed:
            self._write_governance(governance)
            self._mark_cache_dirty()

    def governance_report(
        self,
        limit: int = 12,
        stale_days: int = 90,
        overlap_threshold: float = 0.62,
    ) -> dict[str, Any]:
        governance = self._load_governance()
        skills = self.list_skills(include_archived=True)
        active_skills = [item for item in skills if item.status != "archived"]
        overlaps = self.detect_overlaps(
            skills=active_skills,
            threshold=overlap_threshold,
            limit=limit,
        )
        stale_candidates: list[dict[str, Any]] = []
        setup_needed: list[dict[str, Any]] = []
        deprecated: list[dict[str, Any]] = []
        archived: list[dict[str, Any]] = []
        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        loaded_slugs = {item.slug for item in skills}
        for skill in skills:
            if skill.readiness == "setup-needed":
                setup_needed.append(
                    {
                        "slug": skill.slug,
                        "source": skill.source,
                        "requirements": skill.missing_requirements,
                    }
                )
            if skill.status == "deprecated":
                deprecated.append(skill.to_index_dict())
            if skill.status == "archived":
                archived.append(skill.to_index_dict())
                continue
            if skill.source == "builtin":
                continue
            age_days = 0
            if skill.last_used_at:
                timestamp = _parse_timestamp(skill.last_used_at)
                if timestamp is not None:
                    age_days = max(int((now - timestamp).total_seconds() // 86400), 0)
            else:
                try:
                    age_days = max(int((now.timestamp() - skill.path.stat().st_mtime) // 86400), 0)
                except FileNotFoundError:
                    age_days = stale_days
            if skill.usage_count == 0 and age_days >= stale_days:
                stale_candidates.append(
                    {
                        "slug": skill.slug,
                        "source": skill.source,
                        "usage_count": skill.usage_count,
                        "days_since_last_used": age_days,
                        "reason": "unused for %s days" % age_days,
                    }
                )
            elif skill.last_used_at and age_days >= stale_days:
                stale_candidates.append(
                    {
                        "slug": skill.slug,
                        "source": skill.source,
                        "usage_count": skill.usage_count,
                        "days_since_last_used": age_days,
                        "reason": "inactive for %s days" % age_days,
                    }
                )

        for slug, record in governance.get("skills", {}).items():
            if slug in loaded_slugs:
                continue
            status = str(record.get("status", "") or "").strip().lower()
            if status != "archived":
                continue
            archived.append(
                {
                    "slug": slug,
                    "source": str(record.get("source", "project") or "project"),
                    "status": "archived",
                    "archived_at": str(record.get("archived_at", "") or ""),
                    "archive_reason": str(record.get("archive_reason", "") or ""),
                    "path": str(record.get("archived_path", record.get("original_path", "")) or ""),
                    "readiness": "",
                    "usage_count": str(record.get("usage_count", 0) or 0),
                }
            )

        stale_candidates.sort(
            key=lambda item: (-item["days_since_last_used"], item["usage_count"], item["slug"])
        )
        setup_needed.sort(key=lambda item: item["slug"])
        deprecated.sort(key=lambda item: item["slug"])
        archived.sort(key=lambda item: item["slug"])

        status_counts = {"active": 0, "deprecated": 0, "archived": 0}
        readiness_counts = {"ready": 0, "setup-needed": 0, "unsupported": 0}
        source_counts: dict[str, int] = {}
        for skill in skills:
            status_counts[skill.status] = status_counts.get(skill.status, 0) + 1
            readiness_counts[skill.readiness] = readiness_counts.get(skill.readiness, 0) + 1
            source_counts[skill.source] = source_counts.get(skill.source, 0) + 1
        for item in archived:
            if item["slug"] in loaded_slugs:
                continue
            status_counts["archived"] = status_counts.get("archived", 0) + 1
            source_counts[item["source"]] = source_counts.get(item["source"], 0) + 1

        return {
            "summary": {
                "skill_count": len(skills),
                "status_counts": status_counts,
                "readiness_counts": readiness_counts,
                "source_counts": source_counts,
            },
            "stale_candidates": stale_candidates[:limit],
            "setup_needed": setup_needed[:limit],
            "overlaps": [item.to_dict() for item in overlaps],
            "deprecated": deprecated[:limit],
            "archived": archived[:limit],
        }

    def detect_overlaps(
        self,
        skills: list[Skill] | None = None,
        threshold: float = 0.62,
        limit: int = 20,
    ) -> list[SkillOverlap]:
        active_skills = [
            item
            for item in (skills or self.list_skills(include_archived=True))
            if item.status != "archived"
        ]
        overlaps: list[SkillOverlap] = []
        docs = {item.slug: _overlap_document(item) for item in active_skills}
        token_sets = {item.slug: set(tokenize_text(docs[item.slug])) for item in active_skills}
        governance_targets = [item for item in active_skills if item.source != "builtin"]
        if not governance_targets:
            return []
        seen_pairs: set[tuple[str, str]] = set()
        for left in governance_targets:
            for right in active_skills:
                if left.slug == right.slug:
                    continue
                pair = tuple(sorted((left.slug, right.slug)))
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                left_tokens = token_sets[left.slug]
                right_tokens = token_sets[right.slug]
                if not left_tokens or not right_tokens:
                    continue
                shared = sorted(left_tokens & right_tokens)
                if len(shared) < 3 and not (set(left.triggers) & set(right.triggers)):
                    continue
                union = left_tokens | right_tokens
                jaccard = (len(shared) / len(union)) if union else 0.0
                sequence = difflib.SequenceMatcher(None, docs[left.slug][:4000], docs[right.slug][:4000]).ratio()
                trigger_bonus = 0.08 if set(left.triggers) & set(right.triggers) else 0.0
                title_bonus = 0.05 if left.slug in right.slug or right.slug in left.slug else 0.0
                score = min(1.0, 0.6 * jaccard + 0.35 * sequence + trigger_bonus + title_bonus)
                if score < threshold:
                    continue
                primary, secondary = (
                    (left, right)
                    if _skill_source_priority(left) >= _skill_source_priority(right)
                    else (right, left)
                )
                recommendation = "Consider merging `%s` into `%s`." % (secondary.slug, primary.slug)
                if secondary.usage_count == 0 and secondary.source != "builtin":
                    recommendation = "Consider deprecating or archiving `%s` in favor of `%s`." % (
                        secondary.slug,
                        primary.slug,
                    )
                overlaps.append(
                    SkillOverlap(
                        primary_slug=primary.slug,
                        secondary_slug=secondary.slug,
                        primary_source=primary.source,
                        secondary_source=secondary.source,
                        score=score,
                        shared_terms=shared[:8],
                        recommendation=recommendation,
                    )
                )
        overlaps.sort(key=lambda item: (-item.score, item.secondary_slug, item.primary_slug))
        return overlaps[:limit]

    def deprecate_skill(
        self,
        slug_or_name: str,
        reason: str,
        superseded_by: str = "",
    ) -> dict[str, Any]:
        skill = self.get(slug_or_name, include_archived=True)
        if skill is None:
            raise ValueError("Skill not found: %s" % slug_or_name)
        governance = self._load_governance()
        record = governance.setdefault("skills", {}).setdefault(skill.slug, {})
        record["source"] = skill.source
        record["path"] = str(skill.path)
        record["status"] = "deprecated"
        record["deprecated_at"] = _utcnow()
        record["deprecation_reason"] = reason.strip()
        if superseded_by:
            record["superseded_by"] = slugify(superseded_by)
        self._write_governance(governance)
        self._mark_cache_dirty()
        updated = self.get(skill.slug, include_archived=True)
        return updated.to_index_dict() if updated is not None else {"slug": skill.slug, **record}

    def archive_skill(self, slug_or_name: str, reason: str) -> dict[str, Any]:
        skill = self.get(slug_or_name, include_archived=True)
        if skill is None:
            raise ValueError("Skill not found: %s" % slug_or_name)
        governance = self._load_governance()
        record = governance.setdefault("skills", {}).setdefault(skill.slug, {})
        record["source"] = skill.source
        record["path"] = str(skill.path)
        if skill.source in {"project", "user"} and skill.path.exists():
            archive_root = self._archive_root_for_source(skill.source)
            archive_root.mkdir(parents=True, exist_ok=True)
            target = archive_root / ("%s-%s.md" % (skill.slug, _utcnow().replace(":", "").replace("-", "")))
            suffix = 1
            while target.exists():
                target = archive_root / ("%s-%s-%s.md" % (skill.slug, _utcnow().replace(":", "").replace("-", ""), suffix))
                suffix += 1
            skill.path.rename(target)
            record["archived_path"] = str(target)
            record["original_path"] = str(skill.path)
        record["status"] = "archived"
        record["archived_at"] = _utcnow()
        record["archive_reason"] = reason.strip()
        self._write_governance(governance)
        self._mark_cache_dirty()
        archived = self.get(skill.slug, include_archived=True)
        if archived is not None:
            return archived.to_index_dict()
        return {
            "slug": skill.slug,
            "status": "archived",
            "archived_at": record["archived_at"],
            "archive_reason": record["archive_reason"],
            "source": skill.source,
        }

    def quarantine_skill(self, slug_or_name: str, reason: str) -> dict[str, Any]:
        skill = self.get(slug_or_name, include_archived=True)
        if skill is None:
            raise ValueError("Skill not found: %s" % slug_or_name)
        if skill.source not in {"project", "user"}:
            raise ValueError("Only project or user skills can be quarantined.")
        governance = self._load_governance()
        record = governance.setdefault("skills", {}).setdefault(skill.slug, {})
        original_path = skill.path
        source_root = self.catalog.bundle_root(skill) if skill.path.name == "SKILL.md" else skill.path
        quarantine_root = self._quarantine_root_for_source(skill.source)
        quarantine_root.mkdir(parents=True, exist_ok=True)
        stamp = _utcnow().replace(":", "").replace("-", "")
        target = quarantine_root / ("%s-%s" % (skill.slug, stamp))
        if source_root.is_file():
            target = target.with_suffix(source_root.suffix or ".md")
        shutil.move(str(source_root), str(target))
        record["source"] = skill.source
        record["path"] = str(original_path)
        record["original_path"] = str(source_root)
        record["quarantined"] = True
        record["quarantined_at"] = _utcnow()
        record["quarantine_reason"] = reason.strip()
        record["quarantined_path"] = str(target)
        record["audit_status"] = "quarantined"
        self._write_governance(governance)
        self._mark_cache_dirty()
        return {
            "slug": skill.slug,
            "source": skill.source,
            "quarantined_at": record["quarantined_at"],
            "quarantine_reason": record["quarantine_reason"],
            "quarantined_path": record["quarantined_path"],
        }

    def approve_quarantined_skill(self, slug: str) -> dict[str, Any]:
        governance = self._load_governance()
        record = governance.setdefault("skills", {}).get(slugify(slug))
        if not record or not record.get("quarantined"):
            raise ValueError("Quarantined skill not found: %s" % slug)
        quarantined_path = Path(str(record.get("quarantined_path", "") or ""))
        original_path = Path(str(record.get("original_path", "") or ""))
        if not quarantined_path.exists():
            raise ValueError("Quarantined path no longer exists for skill: %s" % slug)
        original_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(quarantined_path), str(original_path))
        record["quarantined"] = False
        record["approved_at"] = _utcnow()
        record["audit_status"] = "approved"
        self._write_governance(governance)
        self._mark_cache_dirty()
        approved = self.get(slug, include_archived=True)
        return approved.to_index_dict() if approved is not None else {"slug": slug, "approved_at": record["approved_at"]}

    def audit_skill_hub(
        self,
        slug_or_pack: str = "",
        limit: int = 20,
    ) -> dict[str, Any]:
        target = (slug_or_pack or "").strip()
        skills = self.list_skills(include_archived=True)
        selected = skills
        if target:
            normalized = slugify(target)
            selected = [
                item for item in skills if item.slug == normalized or item.hub_pack == normalized or item.name == target
            ]
        issues: list[dict[str, Any]] = []
        for skill in selected:
            if not skill.description.strip():
                issues.append({"slug": skill.slug, "level": "warn", "issue": "missing description"})
            if skill.readiness == "unsupported":
                issues.append({"slug": skill.slug, "level": "warn", "issue": "unsupported on current platform"})
            if skill.readiness == "setup-needed":
                issues.append(
                    {
                        "slug": skill.slug,
                        "level": "info",
                        "issue": "setup needed: %s" % ", ".join(skill.missing_requirements),
                    }
                )
            if skill.trust_level in {"community", "trusted"} and not skill.upstream_url:
                issues.append({"slug": skill.slug, "level": "warn", "issue": "missing upstream_url"})
            if len(skill.content.strip()) < 120:
                issues.append({"slug": skill.slug, "level": "info", "issue": "very short skill content"})
        issues.sort(key=lambda item: (item["level"], item["slug"], item["issue"]))
        return {
            "target": target,
            "skill_count": len(selected),
            "issues": issues[:limit],
        }

    def install_repo_skills(
        self,
        repo_url: str,
        scope: str = "user",
        subdir: str = "",
    ) -> dict[str, Any]:
        normalized_scope = (scope or "user").strip().lower()
        if normalized_scope not in {"user", "project"}:
            raise ValueError("scope must be user or project")
        destination_root = self.user_dir if normalized_scope == "user" else self.project_dir
        repo_slug = slugify(repo_url.rstrip("/").split("/")[-1].replace(".git", "")) or "imported-skills"
        imported: list[dict[str, str]] = []
        with tempfile.TemporaryDirectory() as tmpdir:
            clone_root = Path(tmpdir) / "repo"
            subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, str(clone_root)],
                capture_output=True,
                text=True,
                check=True,
            )
            scan_root = clone_root / subdir if subdir else clone_root
            if not scan_root.exists():
                raise ValueError("subdir does not exist in repo: %s" % subdir)
            for skill_md in scan_root.rglob("SKILL.md"):
                source_root = skill_md.parent
                target_root = destination_root / ("%s-%s" % (repo_slug, slugify(source_root.name)))
                if target_root.exists():
                    shutil.rmtree(target_root)
                shutil.copytree(source_root, target_root)
                imported.append({"name": source_root.name, "path": str(target_root)})
        governance = self._load_governance()
        for item in imported:
            slug = slugify(item["name"])
            record = governance.setdefault("skills", {}).setdefault(slug, {})
            record["source"] = normalized_scope
            record["path"] = str(Path(item["path"]) / "SKILL.md")
            record["upstream_url"] = repo_url
            record["audit_status"] = "imported"
        self._write_governance(governance)
        self._mark_cache_dirty()
        return {
            "repo_url": repo_url,
            "scope": normalized_scope,
            "imported": imported,
        }

    def merge_candidate(
        self,
        title: str,
        content: str,
        preferred_slug: str = "",
        threshold: float = 0.72,
    ) -> dict[str, Any]:
        candidate_slug = slugify(preferred_slug or title)
        target = self.get(candidate_slug)
        similarity = 1.0 if target is not None else 0.0
        if target is None or target.source == "builtin":
            target, similarity = self._best_merge_target(candidate_slug, content)
        if target is None or target.source == "builtin" or similarity < threshold:
            return {
                "action": "create",
                "slug": candidate_slug,
                "similarity": round(similarity, 4),
            }
        existing_raw = target.path.read_text(encoding="utf-8")
        existing_meta, existing_body = parse_frontmatter(existing_raw)
        candidate_meta, candidate_body = parse_frontmatter(content)
        merged_meta = self._merge_skill_metadata(existing_meta, candidate_meta, target.slug)
        merged_body = self._merge_skill_body(existing_body, candidate_body)
        from ecology_harness.utils import dump_frontmatter

        atomic_write_text(
            target.path,
            dump_frontmatter(merged_meta, merged_body),
            encoding="utf-8",
        )
        governance = self._load_governance()
        record = governance.setdefault("skills", {}).setdefault(target.slug, {})
        record["source"] = target.source
        record["path"] = str(target.path)
        record["last_merged_at"] = _utcnow()
        record["last_merge_source"] = "review-candidate"
        self._write_governance(governance)
        self._mark_cache_dirty()
        return {
            "action": "merged",
            "target_slug": target.slug,
            "target_path": str(target.path),
            "similarity": round(similarity, 4),
        }

    def _directory_signature(self) -> tuple[str, list[tuple[str, Path]]]:
        file_entries: list[tuple[str, Path]] = []
        signature_parts: list[str] = []
        archive_roots = {
            ("user", self.user_dir / ".archive"),
            ("project", self.project_dir / ".archive"),
        }
        quarantine_roots = {
            ("user", self.user_dir / ".skill-quarantine"),
            ("project", self.project_dir / ".skill-quarantine"),
        }
        for source, root in (
            ("builtin", self.builtin_dir),
            ("user", self.user_dir),
            ("project", self.project_dir),
        ):
            if not root.exists():
                continue
            excluded_root = dict(archive_roots).get(source)
            quarantine_root = dict(quarantine_roots).get(source)
            for path in sorted(root.rglob("*.md")):
                if excluded_root is not None and self._is_relative_to(path, excluded_root):
                    continue
                if quarantine_root is not None and self._is_relative_to(path, quarantine_root):
                    continue
                try:
                    stat = path.stat()
                except FileNotFoundError:
                    continue
                file_entries.append((source, path))
                signature_parts.append(
                    "%s|%s|%s|%s" % (
                        source,
                        path,
                        int(stat.st_mtime_ns),
                        int(stat.st_size),
                    )
                )
        return "\n".join(signature_parts), file_entries

    def _snapshot_path(self) -> Path:
        return self.state_store.snapshot_path

    def _governance_path(self) -> Path:
        return self.state_store.governance_path

    def _load_snapshot(self) -> dict[str, Any] | None:
        return self.state_store.load_snapshot()

    def _write_snapshot(self, signature: str, skills: list[Skill]) -> None:
        payload = {
            "signature": signature,
            "skills": [self._skill_to_dict(item) for item in skills],
        }
        self.state_store.write_snapshot(payload)

    def _load_governance(self) -> dict[str, Any]:
        return self.state_store.load_governance()

    def _write_governance(self, payload: dict[str, Any]) -> None:
        self.state_store.write_governance(payload)

    def _governance_signature(self, governance: dict[str, Any]) -> str:
        return json.dumps(governance, ensure_ascii=False, sort_keys=True)

    def _skills_from_snapshot(self, snapshot: dict[str, Any]) -> list[Skill]:
        loaded: list[Skill] = []
        for item in snapshot.get("skills", []):
            if not isinstance(item, dict):
                continue
            try:
                loaded.append(self._skill_from_dict(item))
            except Exception:
                continue
        return sorted(loaded, key=lambda skill: skill.name.lower())

    def _skill_to_dict(self, skill: Skill) -> dict[str, Any]:
        payload = dict(skill.__dict__)
        payload["path"] = str(skill.path)
        return payload

    def _skill_from_dict(self, payload: dict[str, Any]) -> Skill:
        payload = dict(payload)
        payload["path"] = Path(str(payload.get("path", "")))
        source = str(payload.get("source", "") or "")
        inferred_pack = self._infer_hub_pack(str(payload.get("source", "") or ""), payload["path"])
        pack_meta = SKILL_HUB_PACKS.get(inferred_pack, SKILL_HUB_PACKS["core"])
        fallback_from_disk = None
        needs_disk_refresh = (
            "author" not in payload
            or "license" not in payload
            or "compatibility" not in payload
            or "upstream_url" not in payload
            or "audit_status" not in payload
        )
        if needs_disk_refresh and payload["path"].exists():
            try:
                fallback_from_disk = self._load_path(payload["path"], source)
            except Exception:
                fallback_from_disk = None
        payload.setdefault("triggers", [])
        payload.setdefault("tools", [])
        payload.setdefault("arguments", [])
        payload.setdefault("requirements", [])
        payload.setdefault("platforms", [])
        payload.setdefault("missing_requirements", [])
        payload.setdefault("category", "")
        payload.setdefault("setup", "")
        payload.setdefault("setup_required", False)
        payload.setdefault("bundle_root", "")
        payload.setdefault("status", "active")
        payload.setdefault("usage_count", 0)
        payload.setdefault("last_used_at", "")
        payload.setdefault("last_used_query", "")
        payload.setdefault("retrieval_count", 0)
        payload.setdefault("last_retrieved_at", "")
        payload.setdefault("deprecated_at", "")
        payload.setdefault("deprecation_reason", "")
        payload.setdefault("archived_at", "")
        payload.setdefault("archive_reason", "")
        payload.setdefault("superseded_by", "")
        payload.setdefault("author", getattr(fallback_from_disk, "author", ""))
        payload.setdefault("license", getattr(fallback_from_disk, "license", ""))
        payload.setdefault("compatibility", list(getattr(fallback_from_disk, "compatibility", [])))
        payload.setdefault("hub_pack", inferred_pack)
        payload.setdefault("trust_level", pack_meta["trust_level"])
        payload.setdefault("upstream_url", getattr(fallback_from_disk, "upstream_url", pack_meta["source_url"]))
        payload.setdefault("audit_status", getattr(fallback_from_disk, "audit_status", pack_meta["audit_status"]))
        payload.setdefault("bundle_root", getattr(fallback_from_disk, "bundle_root", ""))
        readiness, missing_requirements = _evaluate_readiness(
            platforms=list(payload.get("platforms", []) or []),
            requirements=list(payload.get("requirements", []) or []),
            setup_required=bool(payload.get("setup_required", False)),
        )
        payload["readiness"] = readiness
        payload["missing_requirements"] = missing_requirements
        return Skill(**payload)

    def _load_path(self, path: Path, source: str) -> Skill | None:
        raw = path.read_text(encoding="utf-8")
        metadata, body = parse_frontmatter(raw)
        if not metadata and path.name != "SKILL.md":
            return None
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
        requirements = _parse_list(metadata.get("requirements", ""))
        platforms = _parse_list(metadata.get("platforms", ""))
        compatibility = _parse_list(metadata.get("compatibility", ""))
        setup = metadata.get("setup", "").strip()
        setup_required = metadata.get("setup-required", "").strip().lower() in {"true", "1", "yes"}
        hub_pack = self._infer_hub_pack(source, path)
        pack_meta = SKILL_HUB_PACKS.get(hub_pack, SKILL_HUB_PACKS["core"])
        readiness, missing_requirements = _evaluate_readiness(
            platforms=platforms,
            requirements=requirements,
            setup_required=setup_required,
        )
        return Skill(
            slug=slug,
            name=name,
            description=description,
            source=source,
            content=body.strip(),
            path=path,
            triggers=triggers,
            tools=tools,
            when_to_use=metadata.get("when_to_use", ""),
            argument_hint=metadata.get("argument-hint", ""),
            arguments=arguments,
            model=metadata.get("model", ""),
            context=context,
            user_invocable=user_invocable,
            category=metadata.get("category", ""),
            requirements=requirements,
            platforms=platforms,
            setup=setup,
            setup_required=setup_required,
            readiness=readiness,
            missing_requirements=missing_requirements,
            bundle_root=str(path.parent) if path.name == "SKILL.md" else "",
            author=metadata.get("author", metadata.get("metadata.skill-author", "")).strip(),
            license=metadata.get("license", "").strip(),
            compatibility=compatibility,
            hub_pack=hub_pack,
            trust_level=pack_meta["trust_level"],
            upstream_url=pack_meta["source_url"],
            audit_status=pack_meta["audit_status"],
        )

    def _filtered_skills(self, skills: list[Skill], include_archived: bool) -> list[Skill]:
        if include_archived:
            return list(skills)
        return [item for item in skills if item.status != "archived"]

    def _refresh_skill_state(self, skill: Skill, governance: dict[str, Any]) -> Skill:
        readiness, missing_requirements = _evaluate_readiness(
            platforms=skill.platforms,
            requirements=skill.requirements,
            setup_required=skill.setup_required,
        )
        skill.readiness = readiness
        skill.missing_requirements = missing_requirements
        record = governance.get("skills", {}).get(skill.slug, {})
        status = str(record.get("status", "active") or "active").strip().lower()
        skill.status = status if status in _SKILL_STATUS_VALUES else "active"
        skill.usage_count = int(record.get("usage_count", 0) or 0)
        skill.last_used_at = str(record.get("last_used_at", "") or "")
        skill.last_used_query = str(record.get("last_used_query", "") or "")
        skill.retrieval_count = int(record.get("retrieval_count", 0) or 0)
        skill.last_retrieved_at = str(record.get("last_retrieved_at", "") or "")
        skill.deprecated_at = str(record.get("deprecated_at", "") or "")
        skill.deprecation_reason = str(record.get("deprecation_reason", "") or "")
        skill.archived_at = str(record.get("archived_at", "") or "")
        skill.archive_reason = str(record.get("archive_reason", "") or "")
        skill.superseded_by = str(record.get("superseded_by", "") or "")
        if record.get("upstream_url"):
            skill.upstream_url = str(record.get("upstream_url", "") or "")
        if record.get("audit_status"):
            skill.audit_status = str(record.get("audit_status", "") or "")
        return skill

    def _runtime_signature(self, skills: list[Skill]) -> str:
        parts = sorted(_platform_aliases())
        for skill in skills:
            parts.append("status:%s=%s" % (skill.slug, skill.status))
            parts.append("usage:%s=%s" % (skill.slug, skill.usage_count))
            parts.append("retrieval:%s=%s" % (skill.slug, skill.retrieval_count))
            for requirement in skill.requirements:
                token = requirement.strip()
                if not token:
                    continue
                lowered = token.lower()
                if lowered.startswith("env:"):
                    env_name = token.split(":", 1)[1].strip()
                    parts.append("env:%s=%s" % (env_name, "1" if os.environ.get(env_name) else "0"))
                elif lowered.startswith("command:") or lowered.startswith("binary:"):
                    command = token.split(":", 1)[1].strip()
                    parts.append("cmd:%s=%s" % (command, "1" if shutil.which(command) else "0"))
                elif lowered.startswith("python:"):
                    module_name = token.split(":", 1)[1].strip()
                    try:
                        __import__(module_name)
                        available = "1"
                    except Exception:
                        available = "0"
                    parts.append("py:%s=%s" % (module_name, available))
                elif token.isupper() and "_" in token:
                    parts.append("env:%s=%s" % (token, "1" if os.environ.get(token) else "0"))
        return "|".join(parts)

    def _mark_cache_dirty(self) -> None:
        self._cached_signature = ""
        self._cached_runtime_signature = ""
        self._cached_skills = []

    def _infer_hub_pack(self, source: str, path: Path) -> str:
        if source == "user":
            return "user"
        if source == "project":
            return "project"
        if source != "builtin":
            return "core"
        try:
            relative = path.relative_to(self.builtin_dir)
        except ValueError:
            return "core"
        if not relative.parts:
            return "core"
        top_level = relative.parts[0]
        if top_level in SKILL_HUB_PACKS:
            return top_level
        return "core"

    def _archive_root_for_source(self, source: str) -> Path:
        if source == "user":
            return self.user_dir / ".archive"
        return self.project_dir / ".archive"

    def _quarantine_root_for_source(self, source: str) -> Path:
        if source == "user":
            return self.user_dir / ".skill-quarantine"
        return self.project_dir / ".skill-quarantine"

    def _best_merge_target(self, candidate_slug: str, candidate_content: str) -> tuple[Skill | None, float]:
        candidate_skill = Skill(
            slug=candidate_slug,
            name=candidate_slug,
            description="review candidate",
            source="candidate",
            content=candidate_content,
            path=Path(candidate_slug + ".md"),
        )
        best_skill = None
        best_score = 0.0
        candidate_doc = _overlap_document(candidate_skill)
        candidate_tokens = set(tokenize_text(candidate_doc))
        for skill in self.list_skills():
            if skill.source == "builtin":
                continue
            doc = _overlap_document(skill)
            tokens = set(tokenize_text(doc))
            if not tokens or not candidate_tokens:
                continue
            shared = candidate_tokens & tokens
            if len(shared) < 3 and candidate_slug not in skill.slug:
                continue
            union = candidate_tokens | tokens
            jaccard = len(shared) / len(union) if union else 0.0
            sequence = difflib.SequenceMatcher(None, candidate_doc[:4000], doc[:4000]).ratio()
            score = min(1.0, 0.6 * jaccard + 0.4 * sequence)
            if score > best_score:
                best_skill = skill
                best_score = score
        return best_skill, best_score

    def _merge_skill_metadata(
        self,
        existing_meta: dict[str, str],
        candidate_meta: dict[str, str],
        target_slug: str,
    ) -> dict[str, str]:
        merged = dict(existing_meta)
        merged["name"] = existing_meta.get("name", target_slug)
        merged["slug"] = existing_meta.get("slug", target_slug)
        merged["description"] = _merge_text(
            existing_meta.get("description", ""),
            candidate_meta.get("description", ""),
        )
        merged["triggers"] = _stringify_list(
            _parse_list(existing_meta.get("triggers", "")) + _parse_list(candidate_meta.get("triggers", ""))
        )
        merged["allowed-tools"] = _stringify_list(
            _parse_list(existing_meta.get("allowed-tools", existing_meta.get("tools", "")))
            + _parse_list(candidate_meta.get("allowed-tools", candidate_meta.get("tools", "")))
        )
        merged["context"] = existing_meta.get("context", candidate_meta.get("context", "inline")) or "inline"
        merged["user-invocable"] = existing_meta.get("user-invocable", candidate_meta.get("user-invocable", "true")) or "true"
        merged["category"] = existing_meta.get("category", candidate_meta.get("category", ""))
        merged["requirements"] = _stringify_list(
            _parse_list(existing_meta.get("requirements", "")) + _parse_list(candidate_meta.get("requirements", ""))
        )
        merged["platforms"] = _stringify_list(
            _parse_list(existing_meta.get("platforms", "")) + _parse_list(candidate_meta.get("platforms", ""))
        )
        merged["setup"] = _merge_text(existing_meta.get("setup", ""), candidate_meta.get("setup", ""))
        setup_required = existing_meta.get("setup-required", "").strip().lower() in {"true", "1", "yes"} or candidate_meta.get("setup-required", "").strip().lower() in {"true", "1", "yes"}
        if setup_required:
            merged["setup-required"] = "true"
        elif "setup-required" in merged:
            merged.pop("setup-required", None)
        if candidate_meta.get("model") and not merged.get("model"):
            merged["model"] = candidate_meta.get("model", "")
        return merged

    def _merge_skill_body(self, existing_body: str, candidate_body: str) -> str:
        left = (existing_body or "").strip()
        right = (candidate_body or "").strip()
        if not left:
            return right
        if not right:
            return left
        similarity = difflib.SequenceMatcher(None, left[:4000], right[:4000]).ratio()
        if similarity >= 0.9 or right.lower() in left.lower():
            return left
        section = right
        if section.startswith("#"):
            lines = section.splitlines()
            section = "\n".join(lines[1:]).strip()
        return (
            left.rstrip()
            + "\n\n## Additional guidance from review\n"
            + (section or right).strip()
        )

    @staticmethod
    def _is_relative_to(path: Path, root: Path) -> bool:
        try:
            path.resolve().relative_to(root.resolve())
            return True
        except Exception:
            return False
