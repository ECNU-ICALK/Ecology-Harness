from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class ProfileDefinition:
    name: str
    title: str
    description: str
    instructions: str

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "instructions": self.instructions,
        }


_BUILTIN_PROFILES: tuple[ProfileDefinition, ...] = (
    ProfileDefinition(
        name="default",
        title="Default",
        description="Balanced mode for mixed coding, research, and ecology analysis.",
        instructions="Prefer direct answers, keep retrieval lean, and only use specialized skills when they clearly help.",
    ),
    ProfileDefinition(
        name="ecology-research",
        title="Ecology Research",
        description="Best for ecological synthesis, study design, and evidence-grounded interpretation.",
        instructions="Emphasize study systems, scale, uncertainty, methods, and evidence quality before making conclusions.",
    ),
    ProfileDefinition(
        name="modeling",
        title="Modeling and Simulation",
        description="Best for process models, ABM, parameterization, and scenario comparison.",
        instructions="Prioritize explicit assumptions, input requirements, calibration, validation, and cross-model comparison.",
    ),
    ProfileDefinition(
        name="field-monitoring",
        title="Field Monitoring",
        description="Best for monitoring plans, sensors, camera traps, and recurring environmental observations.",
        instructions="Prefer operational clarity, instrumentation constraints, QC steps, and repeatable monitoring workflows.",
    ),
    ProfileDefinition(
        name="literature-review",
        title="Literature Review",
        description="Best for literature search, screening, citation tracing, and synthesis.",
        instructions="Bias toward source-backed claims, paper triage, and explicit evidence synthesis structure.",
    ),
)


class ProfileManager:
    def __init__(self, directory: Path, active_profile: str = "default") -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        self._state_path = self.directory / "active-profile.json"
        self._profiles = {item.name: item for item in _BUILTIN_PROFILES}
        self._active_name = active_profile if active_profile in self._profiles else "default"
        self._load_state()

    def list_profiles(self) -> list[ProfileDefinition]:
        return [self._profiles[key] for key in sorted(self._profiles.keys())]

    def get_active(self) -> ProfileDefinition:
        return self._profiles.get(self._active_name, self._profiles["default"])

    def set_active(self, name: str) -> ProfileDefinition:
        normalized = (name or "").strip().lower()
        if normalized not in self._profiles:
            raise ValueError("Unknown profile: %s" % name)
        self._active_name = normalized
        self._state_path.write_text(
            json.dumps({"active_profile": self._active_name}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return self.get_active()

    def build_context(self) -> str:
        active = self.get_active()
        return "Profile `%s`: %s\n%s" % (active.title, active.description, active.instructions)

    def _load_state(self) -> None:
        if not self._state_path.exists():
            return
        try:
            payload = json.loads(self._state_path.read_text(encoding="utf-8"))
        except Exception:
            return
        candidate = str(payload.get("active_profile", "") or "").strip().lower()
        if candidate in self._profiles:
            self._active_name = candidate
