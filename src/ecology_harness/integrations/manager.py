from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
from threading import RLock
from typing import Any
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request

from ecology_harness.utils import atomic_write_text


def _utc_now_text() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


@dataclass
class IntegrationRecord:
    name: str
    kind: str
    enabled: bool
    config: dict[str, Any]
    created_at: str
    updated_at: str
    notes: str = ""

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "IntegrationRecord":
        return cls(
            name=str(payload.get("name", "") or "").strip(),
            kind=str(payload.get("kind", "") or "").strip(),
            enabled=bool(payload.get("enabled", True)),
            config=dict(payload.get("config", {}) or {}),
            created_at=str(payload.get("created_at", "") or ""),
            updated_at=str(payload.get("updated_at", "") or ""),
            notes=str(payload.get("notes", "") or ""),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "enabled": self.enabled,
            "config": dict(self.config),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "notes": self.notes,
        }


class IntegrationManager:
    def __init__(self, directory: Path) -> None:
        self.directory = Path(directory)
        self.path = self.directory / "integrations.json"
        self._lock = RLock()
        self.directory.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write_records([])

    def list_integrations(self) -> list[dict[str, Any]]:
        with self._lock:
            records = self._read_records()
        return [self._public_view(item) for item in records]

    def status_summary(self) -> dict[str, Any]:
        items = self.list_integrations()
        kinds: dict[str, int] = {}
        status_counts: dict[str, int] = {}
        for item in items:
            kind = str(item.get("kind", "") or "unknown")
            status = str(item.get("status", "") or "unknown")
            kinds[kind] = kinds.get(kind, 0) + 1
            status_counts[status] = status_counts.get(status, 0) + 1
        return {
            "total": len(items),
            "enabled": sum(1 for item in items if item.get("enabled")),
            "kinds": kinds,
            "status_counts": status_counts,
            "items": items,
        }

    def configure_feishu_webhook(
        self,
        *,
        name: str,
        webhook_url: str,
        secret: str = "",
        enabled: bool = True,
        notes: str = "",
    ) -> dict[str, Any]:
        normalized_name = self._normalize_name(name)
        normalized_url = self._normalize_feishu_webhook_url(webhook_url)
        now = _utc_now_text()
        with self._lock:
            records = self._read_records()
            existing = self._find_record(records, normalized_name)
            if existing is None:
                record = IntegrationRecord(
                    name=normalized_name,
                    kind="feishu-webhook",
                    enabled=enabled,
                    config={
                        "webhook_url": normalized_url,
                        "secret": secret.strip(),
                    },
                    created_at=now,
                    updated_at=now,
                    notes=notes.strip(),
                )
                records.append(record)
            else:
                existing.kind = "feishu-webhook"
                existing.enabled = enabled
                existing.config = {
                    "webhook_url": normalized_url,
                    "secret": secret.strip(),
                }
                existing.updated_at = now
                existing.notes = notes.strip()
                record = existing
            self._write_records(records)
        return self._public_view(record)

    def send_feishu_message(
        self,
        *,
        name: str,
        text: str,
        title: str = "",
    ) -> dict[str, Any]:
        message = str(text or "").strip()
        if not message:
            raise ValueError("Feishu message text cannot be empty.")
        with self._lock:
            record = self._find_record(self._read_records(), self._normalize_name(name))
        if record is None:
            raise ValueError("Unknown integration: %s" % name)
        if record.kind != "feishu-webhook":
            raise ValueError("Integration `%s` is not a feishu-webhook integration." % name)
        if not record.enabled:
            raise ValueError("Integration `%s` is disabled." % name)
        webhook_url = str(record.config.get("webhook_url", "") or "").strip()
        secret = str(record.config.get("secret", "") or "").strip()
        if not webhook_url:
            raise ValueError("Integration `%s` has no webhook URL configured." % name)
        payload = self._build_feishu_payload(text=message, title=title)
        if secret:
            timestamp = str(int(datetime.utcnow().timestamp()))
            payload["timestamp"] = timestamp
            payload["sign"] = self._compute_feishu_signature(timestamp=timestamp, secret=secret)
        raw_payload = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib_request.Request(
            webhook_url,
            data=raw_payload,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        try:
            with urllib_request.urlopen(request, timeout=10) as response:
                status_code = int(getattr(response, "status", 200) or 200)
                raw_response = response.read().decode("utf-8", errors="replace")
        except urllib_error.HTTPError as exc:
            raw_response = exc.read().decode("utf-8", errors="replace")
            raise ValueError(
                "Feishu webhook request failed with HTTP %s: %s"
                % (exc.code, raw_response.strip() or exc.reason)
            ) from exc
        except urllib_error.URLError as exc:
            raise ValueError("Feishu webhook request failed: %s" % exc.reason) from exc
        try:
            response_payload = json.loads(raw_response) if raw_response.strip() else {}
        except json.JSONDecodeError:
            response_payload = {"raw": raw_response}
        if status_code >= 400:
            raise ValueError("Feishu webhook request failed with HTTP %s." % status_code)
        if isinstance(response_payload, dict):
            status = response_payload.get("StatusCode")
            code = response_payload.get("code")
            if status not in (None, 0) or code not in (None, 0):
                message_text = (
                    response_payload.get("StatusMessage")
                    or response_payload.get("msg")
                    or response_payload.get("message")
                    or "unknown error"
                )
                raise ValueError("Feishu webhook rejected the message: %s" % message_text)
        return {
            "integration": self._public_view(record),
            "status_code": status_code,
            "response": response_payload,
            "sent_at": _utc_now_text(),
            "title": str(title or "").strip(),
            "text": message,
        }

    def _read_records(self) -> list[IntegrationRecord]:
        if not self.path.exists():
            return []
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
        items = payload.get("integrations", [])
        records: list[IntegrationRecord] = []
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    record = IntegrationRecord.from_dict(item)
                    if record.name:
                        records.append(record)
        return records

    def _write_records(self, records: list[IntegrationRecord]) -> None:
        payload = {
            "integrations": [item.to_dict() for item in sorted(records, key=lambda entry: entry.name.lower())],
        }
        atomic_write_text(
            self.path,
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass

    def _find_record(
        self,
        records: list[IntegrationRecord],
        name: str,
    ) -> IntegrationRecord | None:
        normalized = self._normalize_name(name)
        for item in records:
            if self._normalize_name(item.name) == normalized:
                return item
        return None

    def _public_view(self, record: IntegrationRecord) -> dict[str, Any]:
        return {
            "name": record.name,
            "kind": record.kind,
            "enabled": record.enabled,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
            "notes": record.notes,
            "status": self._status_for_record(record),
            "config": self._masked_config(record),
        }

    def _masked_config(self, record: IntegrationRecord) -> dict[str, Any]:
        config = dict(record.config)
        webhook_url = str(config.get("webhook_url", "") or "")
        if webhook_url:
            config["webhook_url"] = self._mask_webhook_url(webhook_url)
        if "secret" in config:
            secret = str(config.get("secret", "") or "")
            config["secret"] = "***" if secret else ""
        return config

    def _status_for_record(self, record: IntegrationRecord) -> str:
        if not record.enabled:
            return "disabled"
        if record.kind != "feishu-webhook":
            return "unsupported"
        try:
            self._normalize_feishu_webhook_url(str(record.config.get("webhook_url", "") or ""))
        except ValueError:
            return "invalid-config"
        return "ready"

    def _normalize_name(self, name: str) -> str:
        normalized = str(name or "").strip()
        if not normalized:
            raise ValueError("Integration name cannot be empty.")
        return normalized

    def _normalize_feishu_webhook_url(self, webhook_url: str) -> str:
        value = str(webhook_url or "").strip()
        if not value:
            raise ValueError("Feishu webhook URL cannot be empty.")
        parsed = urllib_parse.urlparse(value)
        if parsed.scheme != "https":
            raise ValueError("Feishu webhook URL must use https.")
        host = (parsed.netloc or "").lower()
        if not host:
            raise ValueError("Feishu webhook URL must include a hostname.")
        if "feishu" not in host and "larksuite" not in host:
            raise ValueError("Feishu webhook URL must point to a Feishu or Lark host.")
        if not parsed.path:
            raise ValueError("Feishu webhook URL is missing a path.")
        return value

    def _mask_webhook_url(self, webhook_url: str) -> str:
        parsed = urllib_parse.urlparse(webhook_url)
        host = parsed.netloc
        suffix = parsed.path.split("/")[-1] if parsed.path else ""
        if len(suffix) > 8:
            suffix = suffix[-8:]
        masked = ".../%s" % suffix if suffix else "..."
        return "%s://%s%s" % (parsed.scheme or "https", host, masked)

    def _build_feishu_payload(self, *, text: str, title: str = "") -> dict[str, Any]:
        trimmed_title = str(title or "").strip()
        if not trimmed_title:
            return {
                "msg_type": "text",
                "content": {"text": text},
            }
        return {
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": trimmed_title,
                        "content": [[{"tag": "text", "text": text}]],
                    }
                }
            },
        }

    def _compute_feishu_signature(self, *, timestamp: str, secret: str) -> str:
        string_to_sign = "%s\n%s" % (timestamp, secret)
        digest = hmac.new(
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        return base64.b64encode(digest).decode("utf-8")
