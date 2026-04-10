from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import time
import uuid

from ecology_harness.utils import atomic_write_text


def _utcnow() -> datetime:
    return datetime.utcnow().replace(tzinfo=timezone.utc)


def _dt_to_text(value: datetime) -> str:
    return value.isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse_dt(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


@dataclass
class AutomationJob:
    job_id: str
    name: str
    prompt: str
    schedule: str
    created_at: str
    next_run_at: str
    last_run_at: str = ""
    enabled: bool = True
    notes: str = ""
    run_count: int = 0
    last_status: str = ""
    last_error: str = ""
    last_duration_ms: int = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "job_id": self.job_id,
            "name": self.name,
            "prompt": self.prompt,
            "schedule": self.schedule,
            "created_at": self.created_at,
            "next_run_at": self.next_run_at,
            "last_run_at": self.last_run_at,
            "enabled": self.enabled,
            "notes": self.notes,
            "run_count": self.run_count,
            "last_status": self.last_status,
            "last_error": self.last_error,
            "last_duration_ms": self.last_duration_ms,
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "AutomationJob":
        return cls(
            job_id=str(payload.get("job_id", "")),
            name=str(payload.get("name", "")),
            prompt=str(payload.get("prompt", "")),
            schedule=str(payload.get("schedule", "daily")),
            created_at=str(payload.get("created_at", _dt_to_text(_utcnow()))),
            next_run_at=str(payload.get("next_run_at", _dt_to_text(_utcnow()))),
            last_run_at=str(payload.get("last_run_at", "")),
            enabled=bool(payload.get("enabled", True)),
            notes=str(payload.get("notes", "")),
            run_count=int(payload.get("run_count", 0) or 0),
            last_status=str(payload.get("last_status", "")),
            last_error=str(payload.get("last_error", "")),
            last_duration_ms=int(payload.get("last_duration_ms", 0) or 0),
        )


class AutomationManager:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / "jobs.json"
        self.heartbeat_state_path = self.directory / "heartbeat.json"
        if not self.path.exists():
            self._write([])
        if not self.heartbeat_state_path.exists():
            self._write_heartbeat_state({})

    def list_jobs(self) -> list[AutomationJob]:
        return [AutomationJob.from_dict(item) for item in self._read()]

    def create_job(self, name: str, prompt: str, schedule: str = "daily", enabled: bool = True, notes: str = "") -> AutomationJob:
        now = _utcnow()
        job = AutomationJob(
            job_id="job_%s" % uuid.uuid4().hex[:10],
            name=name.strip(),
            prompt=prompt.strip(),
            schedule=schedule.strip().lower() or "daily",
            created_at=_dt_to_text(now),
            next_run_at=_dt_to_text(self._next_run(now, schedule)),
            enabled=enabled,
            notes=notes.strip(),
        )
        payload = self._read()
        payload.append(job.to_dict())
        self._write(payload)
        return job

    def run_due(self, runner) -> list[dict[str, object]]:
        now = _utcnow()
        payload = self._read()
        results: list[dict[str, object]] = []
        for item in payload:
            job = AutomationJob.from_dict(item)
            if not job.enabled:
                continue
            if _parse_dt(job.next_run_at) > now:
                continue
            started = time.monotonic()
            try:
                output = runner(job)
                error = ""
                status = "succeeded"
            except Exception as exc:
                output = None
                error = str(exc)
                status = "failed"
            duration_ms = int((time.monotonic() - started) * 1000)
            job.last_run_at = _dt_to_text(now)
            job.next_run_at = _dt_to_text(self._next_run(now, job.schedule))
            job.run_count += 1
            job.last_status = status
            job.last_error = error
            job.last_duration_ms = duration_ms
            item.update(job.to_dict())
            results.append(
                {
                    "job_id": job.job_id,
                    "name": job.name,
                    "ran_at": job.last_run_at,
                    "next_run_at": job.next_run_at,
                    "status": status,
                    "error": error,
                    "duration_ms": duration_ms,
                    "output": output,
                }
            )
        self._write(payload)
        return results

    def heartbeat_instruction_path(self, workspace_root: Path) -> Path | None:
        for name in ("HEARTBEAT.md", "heartbeat.md"):
            candidate = workspace_root / name
            if candidate.exists():
                return candidate
        return None

    def heartbeat_status(self, workspace_root: Path, interval_minutes: int = 60) -> dict[str, object]:
        now = _utcnow()
        state = self._read_heartbeat_state()
        path = self.heartbeat_instruction_path(workspace_root)
        prompt = ""
        if path is not None:
            try:
                prompt = path.read_text(encoding="utf-8")
            except Exception:
                prompt = ""
        last_run_at = str(state.get("last_run_at", "") or "")
        next_run_at = str(state.get("next_run_at", "") or "")
        if last_run_at and not next_run_at:
            next_run_at = _dt_to_text(self._next_heartbeat_run(_parse_dt(last_run_at), interval_minutes))
        due = False
        if path is not None and prompt.strip():
            if not next_run_at:
                due = True
            else:
                due = _parse_dt(next_run_at) <= now
        return {
            "enabled": bool(path is not None and prompt.strip()),
            "path": str(path) if path is not None else "",
            "prompt_chars": len(prompt.strip()),
            "last_run_at": last_run_at,
            "next_run_at": next_run_at,
            "due": due,
            "last_result": str(state.get("last_result", "") or ""),
            "noop": bool(state.get("noop", False)),
            "last_error": str(state.get("last_error", "") or ""),
            "last_status": str(state.get("last_status", "") or ""),
        }

    def run_heartbeat(
        self,
        workspace_root: Path,
        runner,
        interval_minutes: int = 60,
        force: bool = False,
    ) -> dict[str, object]:
        now = _utcnow()
        state = self._read_heartbeat_state()
        path = self.heartbeat_instruction_path(workspace_root)
        if path is None:
            return {"ran": False, "skipped": True, "reason": "no-heartbeat-file"}
        try:
            raw_prompt = path.read_text(encoding="utf-8").strip()
        except Exception:
            raw_prompt = ""
        if not raw_prompt:
            return {
                "ran": False,
                "skipped": True,
                "reason": "empty-heartbeat-file",
                "path": str(path),
            }
        status = self.heartbeat_status(workspace_root, interval_minutes=interval_minutes)
        if not force and not bool(status.get("due")):
            return {
                "ran": False,
                "skipped": True,
                "reason": "not-due",
                "path": str(path),
                "next_run_at": status.get("next_run_at", ""),
            }
        prompt = (
            "Heartbeat maintenance pass.\n"
            "Use the workspace heartbeat instructions below to decide whether any periodic maintenance, recall, "
            "or follow-up work is due. If there is nothing meaningful to do, reply with HEARTBEAT_OK only.\n\n"
            + raw_prompt
        )
        started = time.monotonic()
        try:
            output = runner(prompt)
            error = ""
            status = "succeeded"
        except Exception as exc:
            output = None
            error = str(exc)
            status = "failed"
        if isinstance(output, dict):
            final_text = str(output.get("final_text", "") or "")
        else:
            final_text = str(output or "")
        cleaned_text = final_text.replace("HEARTBEAT_OK", "").strip()
        noop = final_text.strip() == "HEARTBEAT_OK" or not cleaned_text
        next_run_at = _dt_to_text(self._next_heartbeat_run(now, interval_minutes))
        state.update(
            {
                "last_run_at": _dt_to_text(now),
                "next_run_at": next_run_at,
                "last_result": cleaned_text,
                "noop": noop,
                "path": str(path),
                "last_error": error,
                "last_status": status,
                "last_duration_ms": int((time.monotonic() - started) * 1000),
            }
        )
        self._write_heartbeat_state(state)
        return {
            "ran": status == "succeeded",
            "skipped": False,
            "path": str(path),
            "ran_at": state["last_run_at"],
            "next_run_at": next_run_at,
            "noop": noop,
            "final_text": cleaned_text,
            "status": status,
            "error": error,
            "duration_ms": state["last_duration_ms"],
        }

    def _next_run(self, current: datetime, schedule: str) -> datetime:
        normalized = (schedule or "daily").strip().lower()
        if normalized == "hourly":
            return current + timedelta(hours=1)
        if normalized == "weekly":
            return current + timedelta(days=7)
        return current + timedelta(days=1)

    def _next_heartbeat_run(self, current: datetime, interval_minutes: int) -> datetime:
        interval = max(int(interval_minutes or 0), 1)
        return current + timedelta(minutes=interval)

    def _read(self) -> list[dict]:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                return [item for item in payload if isinstance(item, dict)]
        except Exception:
            pass
        return []

    def _write(self, payload: list[dict]) -> None:
        atomic_write_text(
            self.path,
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _read_heartbeat_state(self) -> dict[str, object]:
        try:
            payload = json.loads(self.heartbeat_state_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                return payload
        except Exception:
            pass
        return {}

    def _write_heartbeat_state(self, payload: dict[str, object]) -> None:
        atomic_write_text(
            self.heartbeat_state_path,
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
