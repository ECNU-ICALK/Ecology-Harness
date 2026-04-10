from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from dataclasses import replace
import os
import time
from typing import Callable

from ecology_harness.config import HarnessSettings
from ecology_harness.runtime.messages import ChatMessage, ModelResponse
from ecology_harness.tools import ToolDefinition


_POOL_CURSOR: dict[str, int] = defaultdict(int)


@dataclass(frozen=True)
class ProviderRouteAttempt:
    provider: str
    model: str
    attempt: int
    key_slot: int
    error: str = ""
    success: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "model": self.model,
            "attempt": self.attempt,
            "key_slot": self.key_slot,
            "error": self.error,
            "success": self.success,
        }


def parse_provider_fallbacks(settings: HarnessSettings) -> list[str]:
    values: list[str] = []
    for item in getattr(settings, "provider_fallbacks", ()) or ():
        normalized = str(item).strip().lower()
        if normalized and normalized not in values:
            values.append(normalized)
    return values


def resolve_slot_settings(settings: HarnessSettings, slot: str) -> HarnessSettings:
    normalized = (slot or "main").strip().lower()
    if normalized == "main":
        return settings
    cloned = replace(settings)
    provider_override = getattr(settings, "%s_provider" % normalized, "") or ""
    model_override = getattr(settings, "%s_model" % normalized, "") or ""
    if provider_override:
        cloned.provider = provider_override
    if model_override:
        cloned.model = model_override
    return cloned


class RoutedProvider:
    def __init__(
        self,
        settings: HarnessSettings,
        factory: Callable[[str, HarnessSettings], object],
        *,
        explicit: str = "",
    ) -> None:
        self.settings = settings
        self.factory = factory
        self.explicit = explicit
        self.name = "router"
        self.last_attempts: list[ProviderRouteAttempt] = []

    def complete(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDefinition],
        settings: HarnessSettings,
    ) -> ModelResponse:
        candidates = self._candidate_settings(settings)
        attempts: list[ProviderRouteAttempt] = []
        last_error: Exception | None = None
        for index, candidate in enumerate(candidates):
            key_pool = _resolve_key_pool(candidate)
            if not key_pool:
                key_pool = [candidate.api_key]
            ordered_keys = _ordered_keys(candidate.provider, key_pool, candidate.provider_pool_strategy)
            max_attempts = max(int(candidate.provider_retry_attempts or 1), 1)
            for attempt_number in range(max_attempts):
                for key_index, api_key in enumerate(ordered_keys):
                    local_settings = replace(candidate, api_key=api_key)
                    provider = self.factory(local_settings.provider, local_settings)
                    try:
                        response = provider.complete(messages, tools, local_settings)
                        mark_key_use(local_settings.provider, key_index)
                        attempts.append(
                            ProviderRouteAttempt(
                                provider=local_settings.provider,
                                model=local_settings.model,
                                attempt=attempt_number + 1,
                                key_slot=key_index,
                                success=True,
                            )
                        )
                        if isinstance(response.raw, dict):
                            response.raw.setdefault("_router", {})
                            response.raw["_router"]["attempts"] = [item.to_dict() for item in attempts]
                        self.last_attempts = attempts
                        return response
                    except Exception as exc:  # pragma: no cover - error shape varies by provider
                        last_error = exc
                        attempts.append(
                            ProviderRouteAttempt(
                                provider=local_settings.provider,
                                model=local_settings.model,
                                attempt=attempt_number + 1,
                                key_slot=key_index,
                                error=str(exc),
                                success=False,
                            )
                        )
                        if not _is_retryable_provider_error(str(exc)):
                            break
                        backoff_ms = int(candidate.provider_retry_backoff_ms or 0)
                        if backoff_ms > 0:
                            time.sleep(backoff_ms / 1000.0)
                if attempts and attempts[-1].provider == candidate.provider and not _is_retryable_provider_error(attempts[-1].error):
                    break
            if index < len(candidates) - 1 and attempts:
                continue
        self.last_attempts = attempts
        if last_error is not None:
            raise last_error
        raise RuntimeError("Provider router failed before attempting a provider.")

    def _candidate_settings(self, settings: HarnessSettings) -> list[HarnessSettings]:
        candidates: list[HarnessSettings] = []
        seen: set[str] = set()
        primary = replace(settings)
        primary.provider = (self.explicit or settings.provider or "auto").strip().lower() or "auto"
        for provider_name in [primary.provider, *parse_provider_fallbacks(settings)]:
            normalized = provider_name.strip().lower()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            candidate = replace(primary)
            candidate.provider = normalized
            candidates.append(candidate)
        return candidates or [primary]


def _resolve_key_pool(settings: HarnessSettings) -> list[str]:
    if settings.api_key and "," in settings.api_key:
        return [item.strip() for item in settings.api_key.split(",") if item.strip()]
    env_name = (settings.api_key_env or "").strip()
    if not env_name:
        return [settings.api_key] if settings.api_key else []
    pool_env_names = [
        env_name,
        env_name + "S" if not env_name.endswith("S") else env_name,
        env_name.replace("_KEY", "_KEYS") if env_name.endswith("_KEY") else env_name,
    ]
    for pool_env in pool_env_names:
        raw = os.environ.get(pool_env, "")
        if not raw:
            continue
        if "," in raw or "\n" in raw:
            return [item.strip() for item in raw.replace("\n", ",").split(",") if item.strip()]
        return [raw.strip()]
    return [settings.api_key] if settings.api_key else []


def _ordered_keys(provider_name: str, keys: list[str], strategy: str) -> list[str]:
    if not keys:
        return []
    normalized = (strategy or "fill-first").strip().lower()
    if normalized == "least-used":
        indexed = sorted(range(len(keys)), key=lambda idx: (_POOL_CURSOR["%s:%s" % (provider_name, idx)], idx))
        return [keys[idx] for idx in indexed]
    if normalized == "round-robin":
        cursor_key = "rr:%s" % provider_name
        start = _POOL_CURSOR[cursor_key] % len(keys)
        _POOL_CURSOR[cursor_key] = start + 1
        return [keys[(start + offset) % len(keys)] for offset in range(len(keys))]
    return keys


def mark_key_use(provider_name: str, key_slot: int) -> None:
    _POOL_CURSOR["%s:%s" % (provider_name, key_slot)] += 1


def _is_retryable_provider_error(message: str) -> bool:
    normalized = (message or "").lower()
    return any(
        token in normalized
        for token in (
            "429",
            "timeout",
            "timed out",
            "connection reset",
            "temporarily unavailable",
            "502",
            "503",
            "504",
            "rate limit",
            "rate-limited",
        )
    )
