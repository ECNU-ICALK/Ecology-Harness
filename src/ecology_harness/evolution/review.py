from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path
import re
from typing import Any, Callable
import uuid

from ecology_harness.runtime.messages import ChatMessage
from ecology_harness.utils import atomic_write_text, dump_frontmatter, parse_frontmatter, slugify


REVIEW_SYSTEM_PROMPT = """You are the Ecology Harness review agent.

Your job is to inspect a completed run and decide what durable knowledge should be kept.

Rules:
1. Prefer durable, reusable knowledge rather than one-off details.
2. Create memory candidates only when the run reveals stable project context, a reliable workflow, or a durable interpretation worth reusing.
3. Create skill candidates only when the run demonstrates a repeatable multi-step workflow.
4. Do not invent tools, files, results, or facts not present in the run context.
5. Keep output compact and machine-readable.
6. If nothing is worth saving, return empty candidate lists.

Return strict JSON with this shape:
{
  "summary": "short run summary",
  "memory_candidates": [
    {
      "title": "durable memory title",
      "description": "why this memory matters",
      "content": "durable memory content",
      "scope": "project"
    }
  ],
  "skill_candidates": [
    {
      "title": "reusable workflow title",
      "description": "when to use it",
      "when_to_use": "clear trigger condition",
      "steps": ["step 1", "step 2"],
      "allowed_tools": ["Read", "Grep"],
      "trigger": "/workflow-trigger",
      "expected_outcome": "what success looks like"
    }
  ]
}
"""


ReviewLLMCallback = Callable[[dict[str, Any]], Any]


@dataclass
class ReviewCandidate:
    candidate_id: str
    candidate_type: str
    title: str
    description: str
    content: str
    source_session_id: str
    status: str = "candidate"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "candidate_type": self.candidate_type,
            "title": self.title,
            "description": self.description,
            "content": self.content,
            "source_session_id": self.source_session_id,
            "status": self.status,
            "metadata": self.metadata,
        }


@dataclass
class ReviewReport:
    review_id: str
    created_at: str
    session_id: str
    prompt: str
    summary: str
    candidates: list[ReviewCandidate] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "review_id": self.review_id,
            "created_at": self.created_at,
            "session_id": self.session_id,
            "prompt": self.prompt,
            "summary": self.summary,
            "candidates": [item.to_dict() for item in self.candidates],
            "metadata": self.metadata,
        }


class ReviewManager:
    def __init__(self, review_dir: Path, candidate_dir: Path) -> None:
        self.review_dir = review_dir
        self.candidate_dir = candidate_dir
        self.review_dir.mkdir(parents=True, exist_ok=True)
        self.candidate_dir.mkdir(parents=True, exist_ok=True)

    def review_run(
        self,
        session_id: str,
        prompt: str,
        messages: list[ChatMessage],
        tool_invocations: list[dict[str, Any]],
        final_text: str,
        min_tool_calls: int = 3,
        reviewer: ReviewLLMCallback | None = None,
        max_review_messages: int = 12,
    ) -> ReviewReport | None:
        normalized_prompt = _normalize_prompt(prompt)
        fallback_summary = _build_run_summary(messages, tool_invocations, final_text)
        summary = fallback_summary
        candidates: list[ReviewCandidate] = []
        review_mode = "heuristic"

        review_payload = _build_review_payload(
            session_id=session_id,
            prompt=normalized_prompt,
            messages=messages,
            tool_invocations=tool_invocations,
            final_text=final_text,
            max_review_messages=max_review_messages,
        )
        parsed_review = _run_model_review(reviewer, review_payload) if reviewer is not None else None
        if parsed_review:
            review_mode = "model"
            parsed_summary = str(parsed_review.get("summary", "")).strip()
            if parsed_summary:
                summary = parsed_summary
            candidates.extend(
                _build_candidates_from_model(
                    parsed_review,
                    session_id=session_id,
                    prompt=normalized_prompt,
                    tool_invocations=tool_invocations,
                    final_text=final_text,
                )
            )

        if not candidates:
            candidates.extend(
                _build_heuristic_candidates(
                    session_id=session_id,
                    prompt=normalized_prompt,
                    messages=messages,
                    tool_invocations=tool_invocations,
                    final_text=final_text,
                    min_tool_calls=min_tool_calls,
                )
            )

        if not candidates:
            return None

        report = ReviewReport(
            review_id=uuid.uuid4().hex[:16],
            created_at=_utcnow(),
            session_id=session_id,
            prompt=normalized_prompt,
            summary=summary,
            candidates=candidates,
            metadata={
                "tool_call_count": len(tool_invocations),
                "message_count": len(messages),
                "review_mode": review_mode,
                "review_input": review_payload,
            },
        )
        self._save_report(report)
        return report

    def list_reports(self) -> list[ReviewReport]:
        reports: list[ReviewReport] = []
        for path in sorted(self.review_dir.glob("review-*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            reports.append(_report_from_dict(payload))
        reports.sort(key=lambda item: item.created_at, reverse=True)
        return reports

    def get_candidate(self, candidate_id: str) -> ReviewCandidate | None:
        path = self.candidate_dir / ("%s.json" % candidate_id)
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        return _candidate_from_dict(payload)

    def apply_memory_candidate(self, candidate_id: str, memory_manager, scope: str = "project") -> dict[str, Any]:
        candidate = self.get_candidate(candidate_id)
        if candidate is None or candidate.candidate_type != "memory":
            raise ValueError("Memory candidate not found: %s" % candidate_id)
        saved = memory_manager.save(
            name=candidate.title,
            description=candidate.description,
            content=candidate.content,
            memory_type="review",
            scope=scope,
        )
        candidate.status = "applied"
        self._save_candidate(candidate)
        return {"candidate": candidate.to_dict(), "memory": saved.to_index_dict()}

    def apply_skill_candidate(self, candidate_id: str, skill_loader, skill_dir: Path) -> dict[str, Any]:
        candidate = self.get_candidate(candidate_id)
        if candidate is None or candidate.candidate_type != "skill":
            raise ValueError("Skill candidate not found: %s" % candidate_id)
        validated = _validate_skill_candidate(candidate)
        merge_result = skill_loader.merge_candidate(
            title=validated.title,
            content=validated.content,
            preferred_slug=str(validated.metadata.get("slug", "") or ""),
        )
        if merge_result["action"] == "merged":
            candidate.status = "merged"
            candidate.metadata["path"] = str(merge_result["target_path"])
            candidate.metadata["merged_into"] = str(merge_result["target_slug"])
            candidate.metadata["merge_similarity"] = merge_result["similarity"]
            self._save_candidate(candidate)
            return {"candidate": candidate.to_dict(), "path": str(merge_result["target_path"]), "action": "merged"}

        slug = slugify(candidate.metadata.get("slug", "") or merge_result.get("slug", "") or candidate.title)
        target_dir = (skill_dir / "auto").resolve()
        target_dir.mkdir(parents=True, exist_ok=True)
        target = (target_dir / ("%s.md" % slug)).resolve()
        if target.parent != target_dir:
            raise ValueError("Skill candidate resolved outside the auto skill directory.")
        atomic_write_text(target, validated.content, encoding="utf-8")
        candidate.status = "applied"
        candidate.metadata["path"] = str(target)
        self._save_candidate(candidate)
        return {"candidate": candidate.to_dict(), "path": str(target), "action": "created"}

    def _save_report(self, report: ReviewReport) -> None:
        payload = json.dumps(report.to_dict(), indent=2, ensure_ascii=False)
        atomic_write_text(
            self.review_dir / ("review-%s.json" % report.review_id),
            payload,
            encoding="utf-8",
        )
        for candidate in report.candidates:
            self._save_candidate(candidate)

    def _save_candidate(self, candidate: ReviewCandidate) -> None:
        payload = json.dumps(candidate.to_dict(), indent=2, ensure_ascii=False)
        atomic_write_text(
            self.candidate_dir / ("%s.json" % candidate.candidate_id),
            payload,
            encoding="utf-8",
        )


def _normalize_prompt(prompt: str) -> str:
    text = (prompt or "").strip()
    if text.startswith("/tool "):
        return text
    return re.sub(r"\s+", " ", text)


def _candidate_id() -> str:
    return uuid.uuid4().hex[:16]


def _utcnow() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _build_run_summary(
    messages: list[ChatMessage],
    tool_invocations: list[dict[str, Any]],
    final_text: str,
) -> str:
    last_user = ""
    for message in reversed(messages):
        if message.role == "user":
            last_user = message.summary_text(max_document_chars=120)
            break
    tool_sequence = [item.get("tool", "") for item in tool_invocations if item.get("tool")]
    parts = []
    if last_user:
        parts.append("Request: %s" % last_user)
    if tool_sequence:
        parts.append("Tools: %s" % " -> ".join(tool_sequence[:8]))
    if final_text.strip():
        excerpt = final_text.strip()
        if len(excerpt) > 240:
            excerpt = excerpt[:237].rstrip() + "..."
        parts.append("Outcome: %s" % excerpt)
    return "\n".join(parts)


def _build_review_payload(
    session_id: str,
    prompt: str,
    messages: list[ChatMessage],
    tool_invocations: list[dict[str, Any]],
    final_text: str,
    max_review_messages: int = 12,
) -> dict[str, Any]:
    recent_messages = []
    for index, message in enumerate(messages[-max_review_messages:]):
        recent_messages.append(
            {
                "index": max(len(messages) - max_review_messages, 0) + index,
                "role": message.role,
                "summary": message.summary_text(max_document_chars=180),
            }
        )
    return {
        "session_id": session_id,
        "prompt": prompt,
        "recent_messages": recent_messages,
        "tool_invocations": list(tool_invocations[-12:]),
        "final_text": final_text.strip()[:2_400],
    }


def _run_model_review(
    reviewer: ReviewLLMCallback | None,
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    if reviewer is None:
        return None
    try:
        raw = reviewer(payload)
    except Exception:
        return None
    return _coerce_review_output(raw)


def _coerce_review_output(raw: dict[str, Any] | str | None) -> dict[str, Any] | None:
    if raw is None:
        return None
    if isinstance(raw, dict):
        return raw
    text = str(raw).strip()
    if not text:
        return None
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def _build_candidates_from_model(
    payload: dict[str, Any],
    session_id: str,
    prompt: str,
    tool_invocations: list[dict[str, Any]],
    final_text: str,
) -> list[ReviewCandidate]:
    candidates: list[ReviewCandidate] = []

    for item in payload.get("memory_candidates", []) or []:
        title = str(item.get("title", "")).strip()
        content = str(item.get("content", "")).strip()
        if not title or not content:
            continue
        description = str(item.get("description", "")).strip() or "Project memory candidate from model review."
        scope = str(item.get("scope", "project")).strip() or "project"
        candidates.append(
            ReviewCandidate(
                candidate_id=_candidate_id(),
                candidate_type="memory",
                title=title,
                description=description,
                content=content,
                source_session_id=session_id,
                metadata={"scope": scope, "source": "model-review"},
            )
        )

    for item in payload.get("skill_candidates", []) or []:
        title = str(item.get("title", "")).strip()
        if not title:
            continue
        description = str(item.get("description", "")).strip() or "Reusable workflow candidate from model review."
        allowed_tools = _coerce_string_list(item.get("allowed_tools"))
        steps = _coerce_string_list(item.get("steps"))
        when_to_use = str(item.get("when_to_use", "")).strip()
        trigger = str(item.get("trigger", "")).strip()
        expected_outcome = str(item.get("expected_outcome", "")).strip() or final_text.strip()
        content = _build_skill_markdown_from_plan(
            title=title,
            description=description,
            prompt=prompt,
            tool_invocations=tool_invocations,
            allowed_tools=allowed_tools,
            steps=steps,
            when_to_use=when_to_use,
            trigger=trigger,
            expected_outcome=expected_outcome,
        )
        candidates.append(
            ReviewCandidate(
                candidate_id=_candidate_id(),
                candidate_type="skill",
                title=title,
                description=description,
                content=content,
                source_session_id=session_id,
                metadata={
                    "slug": slugify(title),
                    "allowed_tools": allowed_tools,
                    "steps": steps,
                    "source": "model-review",
                },
            )
        )

    return candidates


def _build_heuristic_candidates(
    session_id: str,
    prompt: str,
    messages: list[ChatMessage],
    tool_invocations: list[dict[str, Any]],
    final_text: str,
    min_tool_calls: int,
) -> list[ReviewCandidate]:
    candidates: list[ReviewCandidate] = []
    if len(tool_invocations) >= min_tool_calls and final_text.strip():
        candidates.append(
            ReviewCandidate(
                candidate_id=_candidate_id(),
                candidate_type="skill",
                title=_skill_title(prompt),
                description="Auto-generated reusable workflow candidate from a successful run.",
                content=_build_skill_markdown(
                    prompt=prompt,
                    tool_invocations=tool_invocations,
                    final_text=final_text,
                ),
                source_session_id=session_id,
                metadata={
                    "tool_sequence": [item.get("tool", "") for item in tool_invocations],
                    "source": "heuristic-review",
                },
            )
        )

    memory_candidate = _build_memory_candidate(
        session_id=session_id,
        prompt=prompt,
        messages=messages,
        tool_invocations=tool_invocations,
        final_text=final_text,
    )
    if memory_candidate is not None:
        candidates.append(memory_candidate)
    return candidates


def _coerce_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        if not value.strip():
            return []
        if "\n" in value:
            return [item.strip("- ").strip() for item in value.splitlines() if item.strip()]
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def _skill_title(prompt: str) -> str:
    cleaned = prompt.strip().strip("/").replace("{", " ").replace("}", " ")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned[:72].strip() or "auto-review-skill"


def _build_skill_markdown(
    prompt: str,
    tool_invocations: list[dict[str, Any]],
    final_text: str,
) -> str:
    tool_names = [str(item.get("tool", "")).strip() for item in tool_invocations if item.get("tool")]
    deduped_tools = list(dict.fromkeys(tool_names))
    steps = []
    for index, item in enumerate(tool_invocations, start=1):
        tool = str(item.get("tool", "tool")).strip()
        arguments = item.get("arguments", {})
        steps.append("%s. Use `%s` with arguments `%s`." % (index, tool, json.dumps(arguments, ensure_ascii=False)))
    if not steps:
        steps.append("1. Review the task and execute the necessary tools.")
    return _render_skill_markdown(
        title=_skill_title(prompt),
        description="Auto-generated reusable workflow from post-run review.",
        original_task=prompt,
        when_to_use="Use this skill when a similar task appears and you want to replay a proven workflow.",
        steps=steps,
        allowed_tools=deduped_tools,
        trigger="",
        expected_outcome=final_text.strip() or "Complete the task and summarize the result.",
    )


def _build_skill_markdown_from_plan(
    title: str,
    description: str,
    prompt: str,
    tool_invocations: list[dict[str, Any]],
    allowed_tools: list[str],
    steps: list[str],
    when_to_use: str,
    trigger: str,
    expected_outcome: str,
) -> str:
    effective_tools = list(dict.fromkeys(allowed_tools or [
        str(item.get("tool", "")).strip()
        for item in tool_invocations
        if item.get("tool")
    ]))
    effective_steps = steps or [
        "Review the request and reuse the workflow shown in the original run.",
        "Use the required tools in the same order when appropriate.",
        "Summarize the outcome and note assumptions."
    ]
    numbered_steps = ["%s. %s" % (index, item) for index, item in enumerate(effective_steps, start=1)]
    return _render_skill_markdown(
        title=title,
        description=description,
        original_task=prompt,
        when_to_use=when_to_use or description,
        steps=numbered_steps,
        allowed_tools=effective_tools,
        trigger=trigger,
        expected_outcome=expected_outcome or "Complete the task and summarize the result.",
    )


def _render_skill_markdown(
    title: str,
    description: str,
    original_task: str,
    when_to_use: str,
    steps: list[str],
    allowed_tools: list[str],
    trigger: str,
    expected_outcome: str,
) -> str:
    slug = slugify(title)
    trigger_value = trigger or ("/%s" % slug)
    metadata = {
        "name": slug,
        "description": description,
        "slug": slug,
        "triggers": "[%s]" % trigger_value,
        "allowed-tools": "[%s]" % ", ".join(item for item in allowed_tools if item),
        "context": "inline",
        "user-invocable": "true",
    }
    body = [
        "# Auto Review Skill",
        "",
        "## When to use",
        when_to_use or "Use this skill when the same class of task appears again.",
        "",
        "## Original task",
        original_task,
        "",
        "## Recommended steps",
        *steps,
        "",
        "## Expected outcome",
        expected_outcome,
    ]
    return dump_frontmatter(metadata, "\n".join(body))


def _build_memory_candidate(
    session_id: str,
    prompt: str,
    messages: list[ChatMessage],
    tool_invocations: list[dict[str, Any]],
    final_text: str,
) -> ReviewCandidate | None:
    if not final_text.strip():
        return None
    if len(tool_invocations) < 2:
        return None
    key_tools = [item.get("tool", "") for item in tool_invocations if item.get("tool")]
    user_messages = [
        message.summary_text(max_document_chars=120)
        for message in messages
        if message.role == "user"
    ]
    content = "\n".join(
        [
            "Task: %s" % prompt,
            "User context: %s" % " | ".join(user_messages[-2:]),
            "Tool sequence: %s" % " -> ".join(key_tools[:10]),
            "Outcome: %s" % final_text.strip(),
        ]
    )
    return ReviewCandidate(
        candidate_id=_candidate_id(),
        candidate_type="memory",
        title="Run memory: %s" % _skill_title(prompt),
        description="Project memory candidate distilled from a successful run.",
        content=content,
        source_session_id=session_id,
        metadata={"scope": "project", "source": "heuristic-review"},
    )


def _validate_skill_candidate(candidate: ReviewCandidate) -> ReviewCandidate:
    content = candidate.content
    if not content.strip():
        raise ValueError("Skill candidate content is empty.")
    if "\x00" in content:
        raise ValueError("Skill candidate contains invalid null bytes.")
    if len(content.encode("utf-8")) > 64_000:
        raise ValueError("Skill candidate content is too large.")
    metadata, body = parse_frontmatter(content)
    if not metadata:
        raise ValueError("Skill candidate must include frontmatter metadata.")
    if not body.strip():
        raise ValueError("Skill candidate body is empty.")
    name = str(metadata.get("name", "")).strip()
    if not name:
        raise ValueError("Skill candidate metadata is missing name.")
    if name != slugify(name):
        raise ValueError("Skill candidate name must be slug-safe.")
    return candidate


def _candidate_from_dict(payload: dict[str, Any]) -> ReviewCandidate:
    return ReviewCandidate(
        candidate_id=str(payload.get("candidate_id", "")),
        candidate_type=str(payload.get("candidate_type", "")),
        title=str(payload.get("title", "")),
        description=str(payload.get("description", "")),
        content=str(payload.get("content", "")),
        source_session_id=str(payload.get("source_session_id", "")),
        status=str(payload.get("status", "candidate")),
        metadata=dict(payload.get("metadata", {}) or {}),
    )


def _report_from_dict(payload: dict[str, Any]) -> ReviewReport:
    return ReviewReport(
        review_id=str(payload.get("review_id", "")),
        created_at=str(payload.get("created_at", "")),
        session_id=str(payload.get("session_id", "")),
        prompt=str(payload.get("prompt", "")),
        summary=str(payload.get("summary", "")),
        candidates=[
            _candidate_from_dict(item)
            for item in payload.get("candidates", [])
            if isinstance(item, dict)
        ],
        metadata=dict(payload.get("metadata", {}) or {}),
    )
