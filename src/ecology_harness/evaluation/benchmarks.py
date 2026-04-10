from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json

from ecology_harness.evaluation.trajectory_export import TrajectoryRecord, TrajectoryStore


@dataclass
class TrajectoryScore:
    trajectory_id: str
    session_id: str
    task_slice: str
    score: float
    success: bool
    error_count: int
    tool_call_count: int
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "session_id": self.session_id,
            "task_slice": self.task_slice,
            "score": round(self.score, 4),
            "success": self.success,
            "error_count": self.error_count,
            "tool_call_count": self.tool_call_count,
            "tags": list(self.tags),
        }


@dataclass
class BenchmarkSliceSummary:
    name: str
    trajectory_count: int
    average_score: float

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "trajectory_count": self.trajectory_count,
            "average_score": round(self.average_score, 4),
        }


@dataclass
class BenchmarkSummary:
    trajectory_count: int
    average_steps: float
    average_tool_calls: float
    compaction_rate: float
    attachment_rate: float
    success_rate: float
    error_rate: float
    average_replay_score: float
    slices: list[BenchmarkSliceSummary] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_count": self.trajectory_count,
            "average_steps": round(self.average_steps, 3),
            "average_tool_calls": round(self.average_tool_calls, 3),
            "compaction_rate": round(self.compaction_rate, 3),
            "attachment_rate": round(self.attachment_rate, 3),
            "success_rate": round(self.success_rate, 3),
            "error_rate": round(self.error_rate, 3),
            "average_replay_score": round(self.average_replay_score, 3),
            "slices": [item.to_dict() for item in self.slices],
        }


class BenchmarkRunner:
    def __init__(self, store: TrajectoryStore, output_dir: Path) -> None:
        self.store = store
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def replay(self, limit: int | None = None, task_slice: str = "") -> list[TrajectoryScore]:
        records = self.store.list_records()
        if task_slice:
            records = [item for item in records if item.task_slice == task_slice]
        if limit is not None:
            records = records[: max(int(limit), 0)]
        return [self.score_record(item) for item in records]

    def score_record(self, record: TrajectoryRecord) -> TrajectoryScore:
        success = bool(record.final_text.strip()) and "Agent reached max_agent_loops" not in record.final_text
        error_count = 0
        for invocation in record.tool_invocations:
            output = str(invocation.get("output", ""))
            if "Tool error" in output or "Permission denied" in output:
                error_count += 1

        score = 0.0
        if record.final_text.strip():
            score += 0.35
        if success:
            score += 0.2
        if record.tool_invocations:
            score += 0.15
        if record.compactions:
            score += 0.05
        if record.attachments:
            score += 0.05
        if "tool-error" not in record.quality_tags and "permission-denied" not in record.quality_tags:
            score += 0.1
        score -= min(error_count, 3) * 0.1
        score = max(0.0, min(1.0, score))

        return TrajectoryScore(
            trajectory_id=record.trajectory_id,
            session_id=record.session_id,
            task_slice=record.task_slice,
            score=score,
            success=success,
            error_count=error_count,
            tool_call_count=len(record.tool_invocations),
            tags=list(record.quality_tags),
        )

    def summarize(self) -> BenchmarkSummary:
        records = self.store.list_records()
        if not records:
            return BenchmarkSummary(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, [])

        total_steps = 0
        total_tool_calls = 0
        compaction_count = 0
        attachment_count = 0
        scores = [self.score_record(item) for item in records]
        success_count = 0
        error_count = 0
        slices: dict[str, list[float]] = {}
        for item, score in zip(records, scores):
            total_steps += _step_count(item)
            total_tool_calls += len(item.tool_invocations)
            if item.compactions:
                compaction_count += 1
            if item.attachments:
                attachment_count += 1
            if score.success:
                success_count += 1
            if score.error_count:
                error_count += 1
            slices.setdefault(item.task_slice or "general", []).append(score.score)

        slice_rows = [
            BenchmarkSliceSummary(
                name=name,
                trajectory_count=len(values),
                average_score=(sum(values) / len(values)) if values else 0.0,
            )
            for name, values in sorted(slices.items())
        ]

        return BenchmarkSummary(
            trajectory_count=len(records),
            average_steps=total_steps / len(records),
            average_tool_calls=total_tool_calls / len(records),
            compaction_rate=compaction_count / len(records),
            attachment_rate=attachment_count / len(records),
            success_rate=success_count / len(records),
            error_rate=error_count / len(records),
            average_replay_score=sum(item.score for item in scores) / len(scores),
            slices=slice_rows,
        )

    def write_summary(self, name: str = "latest-benchmark") -> Path:
        summary = self.summarize()
        scores = self.replay()
        path = self.output_dir / ("%s.json" % name)
        path.write_text(
            json.dumps(
                {
                    "summary": summary.to_dict(),
                    "scores": [item.to_dict() for item in scores],
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return path


def _step_count(record: TrajectoryRecord) -> int:
    if record.metadata.get("steps"):
        try:
            return int(record.metadata["steps"])
        except Exception:
            pass
    return max(1, len(record.tool_invocations) + 1)
