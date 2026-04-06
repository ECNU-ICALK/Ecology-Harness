from __future__ import annotations

import base64
import html
import json
import mimetypes
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
import re
import uuid
import wave
import zipfile
from xml.etree import ElementTree

from ecology_harness.config import HarnessSettings
from ecology_harness.runtime.messages import ChatMessage, MessagePart
from ecology_harness.tools.base import ToolError


IMAGE_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
    ".svg",
}
AUDIO_SUFFIXES = {
    ".wav",
    ".mp3",
    ".m4a",
    ".aac",
    ".flac",
    ".ogg",
    ".opus",
    ".webm",
}
VIDEO_SUFFIXES = {
    ".mp4",
    ".mov",
    ".m4v",
    ".avi",
    ".mkv",
    ".webm",
    ".mpeg",
    ".mpg",
}
TEXT_SUFFIXES = {
    ".txt",
    ".md",
    ".markdown",
    ".rst",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".csv",
    ".tsv",
    ".html",
    ".htm",
    ".xml",
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".rs",
    ".go",
    ".sh",
    ".sql",
    ".log",
    ".ini",
    ".cfg",
}
DOCUMENT_SUFFIXES = TEXT_SUFFIXES | {".pdf", ".docx", ".ipynb"}


@dataclass(frozen=True)
class AttachmentInfo:
    raw_path: str
    resolved_path: Path
    display_path: str
    kind: str
    mime_type: str
    size_bytes: int


@dataclass(frozen=True)
class DocumentExtraction:
    path: Path
    display_path: str
    mime_type: str
    text: str
    size_bytes: int
    truncated: bool = False
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class MediaInspection:
    path: Path
    display_path: str
    mime_type: str
    size_bytes: int
    metadata: dict[str, object] = field(default_factory=dict)


def build_user_message(
    prompt: str,
    attachment_paths: list[str] | None,
    settings: HarnessSettings,
    sandbox=None,
) -> ChatMessage:
    normalized = list(attachment_paths or [])
    if not normalized:
        return ChatMessage(role="user", content=prompt)

    parts: list[MessagePart] = []
    if prompt or not normalized:
        parts.append(MessagePart.text_part(prompt))

    for raw_path in normalized:
        info = inspect_attachment(raw_path, settings, sandbox=sandbox)
        if info.kind == "image":
            parts.append(
                MessagePart.image_part(
                    path=str(info.resolved_path),
                    mime_type=info.mime_type,
                    name=Path(info.display_path).name,
                    size_bytes=info.size_bytes,
                    metadata={"display_path": info.display_path},
                )
            )
            continue
        if info.kind == "audio":
            inspection = inspect_audio(
                str(info.resolved_path),
                settings=settings,
                sandbox=sandbox,
            )
            metadata = dict(inspection.metadata)
            metadata["display_path"] = inspection.display_path
            parts.append(
                MessagePart.audio_part(
                    path=str(info.resolved_path),
                    mime_type=inspection.mime_type,
                    name=Path(inspection.display_path).name,
                    size_bytes=inspection.size_bytes,
                    metadata=metadata,
                )
            )
            continue
        if info.kind == "video":
            inspection = inspect_video(
                str(info.resolved_path),
                settings=settings,
                sandbox=sandbox,
            )
            frame_paths = sample_video_frames(
                str(info.resolved_path),
                settings=settings,
                sandbox=sandbox,
                frame_count=settings.video_frame_sample_count,
            )
            metadata = dict(inspection.metadata)
            metadata["display_path"] = inspection.display_path
            metadata["sampled_frames"] = len(frame_paths)
            parts.append(
                MessagePart.video_part(
                    path=str(info.resolved_path),
                    mime_type=inspection.mime_type,
                    name=Path(inspection.display_path).name,
                    size_bytes=inspection.size_bytes,
                    metadata=metadata,
                )
            )
            for frame_path in frame_paths:
                parts.append(
                    MessagePart.image_part(
                        path=str(frame_path),
                        mime_type=guess_mime_type(frame_path, kind="image"),
                        name=frame_path.name,
                        size_bytes=frame_path.stat().st_size,
                        metadata={
                            "generated_from_video": inspection.display_path,
                        },
                    )
                )
            continue
        extracted = extract_document(
            str(info.resolved_path),
            settings=settings,
            sandbox=sandbox,
            max_chars=settings.max_document_chars,
        )
        metadata = dict(extracted.metadata)
        metadata["display_path"] = extracted.display_path
        parts.append(
            MessagePart.document_part(
                path=str(info.resolved_path),
                mime_type=extracted.mime_type,
                text=extracted.text,
                name=Path(extracted.display_path).name,
                size_bytes=extracted.size_bytes,
                metadata=metadata,
            )
        )

    return ChatMessage(role="user", content=prompt, content_parts=parts)


def inspect_attachment(
    raw_path: str,
    settings: HarnessSettings,
    sandbox=None,
) -> AttachmentInfo:
    path = resolve_readable_path(raw_path, settings, sandbox=sandbox)
    if not path.exists():
        raise ToolError("Attachment does not exist: %s" % raw_path)
    if not path.is_file():
        raise ToolError("Attachment is not a file: %s" % raw_path)
    size_bytes = path.stat().st_size
    if settings.max_attachment_bytes > 0 and size_bytes > settings.max_attachment_bytes:
        raise ToolError(
            "Attachment exceeds max_attachment_bytes=%s: %s"
            % (settings.max_attachment_bytes, raw_path)
        )
    suffix = path.suffix.lower()
    if suffix in IMAGE_SUFFIXES:
        kind = "image"
    elif suffix in AUDIO_SUFFIXES:
        kind = "audio"
    elif suffix in VIDEO_SUFFIXES:
        kind = "video"
    elif suffix in DOCUMENT_SUFFIXES:
        kind = "document"
    else:
        raise ToolError(
            "Unsupported attachment type for %s. Supported image/audio/video/document extensions only."
            % raw_path
        )
    mime_type = guess_mime_type(path, kind=kind)
    return AttachmentInfo(
        raw_path=raw_path,
        resolved_path=path,
        display_path=display_path(path, settings),
        kind=kind,
        mime_type=mime_type,
        size_bytes=size_bytes,
    )


def extract_document(
    raw_path: str,
    settings: HarnessSettings,
    sandbox=None,
    max_chars: int | None = None,
) -> DocumentExtraction:
    path = resolve_readable_path(raw_path, settings, sandbox=sandbox)
    if not path.exists() or not path.is_file():
        raise ToolError("Document does not exist: %s" % raw_path)
    size_bytes = path.stat().st_size
    max_chars = settings.max_document_chars if max_chars is None else max_chars
    suffix = path.suffix.lower()
    mime_type = guess_mime_type(path, kind="document")

    if suffix == ".pdf":
        text, metadata = _read_pdf_text(path, max_chars=max_chars)
    elif suffix == ".docx":
        text, metadata = _read_docx_text(path)
    elif suffix == ".ipynb":
        text, metadata = _read_ipynb_text(path)
    else:
        text, metadata = _read_text_like_document(path)

    normalized = _normalize_document_text(text)
    truncated = False
    if max_chars > 0 and len(normalized) > max_chars:
        normalized = normalized[:max_chars].rstrip() + "\n\n[Document text truncated]"
        truncated = True
    metadata = dict(metadata)
    metadata["suffix"] = suffix
    metadata["kind"] = "document"
    if truncated:
        metadata["truncated"] = True
    return DocumentExtraction(
        path=path,
        display_path=display_path(path, settings),
        mime_type=mime_type,
        text=normalized,
        size_bytes=size_bytes,
        truncated=truncated,
        metadata=metadata,
    )


def resolve_readable_path(raw_path: str, settings: HarnessSettings, sandbox=None) -> Path:
    if sandbox is not None:
        try:
            return sandbox.resolve_path(raw_path, access="read")
        except Exception as exc:  # pragma: no cover - delegated validation
            raise ToolError(str(exc)) from exc
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = settings.workspace_root / candidate
    return candidate.resolve()


def display_path(path: Path, settings: HarnessSettings) -> str:
    try:
        return path.relative_to(settings.workspace_root).as_posix()
    except ValueError:
        return str(path)


def guess_mime_type(path: Path, kind: str) -> str:
    guessed, _encoding = mimetypes.guess_type(path.name)
    if guessed:
        return guessed
    if kind == "image":
        return "image/png"
    if kind == "audio":
        return "audio/wav"
    if kind == "video":
        return "video/mp4"
    if path.suffix.lower() == ".pdf":
        return "application/pdf"
    if path.suffix.lower() == ".docx":
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return "text/plain"


def encode_file_base64(path: str | Path) -> str:
    candidate = Path(path)
    return base64.b64encode(candidate.read_bytes()).decode("ascii")


def audio_format_for_openai(path: str | Path) -> str:
    suffix = Path(path).suffix.lower()
    mapping = {
        ".wav": "wav",
        ".mp3": "mp3",
        ".m4a": "mp3",
    }
    return mapping.get(suffix, "wav")


def infer_document_headings(text: str, limit: int = 8) -> list[str]:
    headings = []
    seen = set()
    patterns = [
        re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*$"),
        re.compile(r"^\s*\d+(?:\.\d+)*\s+(.+?)\s*$"),
    ]
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        matched = ""
        for pattern in patterns:
            hit = pattern.match(line)
            if hit:
                matched = hit.group(1).strip()
                break
        if not matched and len(line) <= 80 and line == line.upper() and len(line.split()) <= 10:
            matched = line
        if not matched:
            continue
        lowered = matched.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        headings.append(matched)
        if len(headings) >= limit:
            break
    return headings


def inspect_audio(
    raw_path: str,
    settings: HarnessSettings,
    sandbox=None,
) -> MediaInspection:
    path = resolve_readable_path(raw_path, settings, sandbox=sandbox)
    if not path.exists() or not path.is_file():
        raise ToolError("Audio does not exist: %s" % raw_path)
    metadata: dict[str, object] = {}
    if path.suffix.lower() == ".wav":
        try:
            with wave.open(str(path), "rb") as handle:
                frame_rate = handle.getframerate()
                frame_count = handle.getnframes()
                channel_count = handle.getnchannels()
                duration = (frame_count / float(frame_rate)) if frame_rate else 0.0
                metadata.update(
                    {
                        "duration_seconds": round(duration, 3),
                        "sample_rate": frame_rate,
                        "channels": channel_count,
                        "frame_count": frame_count,
                    }
                )
        except wave.Error:
            metadata["warning"] = "Unable to parse WAV header."
    else:
        metadata.update(_ffprobe_media_info(path))
    return MediaInspection(
        path=path,
        display_path=display_path(path, settings),
        mime_type=guess_mime_type(path, kind="audio"),
        size_bytes=path.stat().st_size,
        metadata=metadata,
    )


def inspect_video(
    raw_path: str,
    settings: HarnessSettings,
    sandbox=None,
) -> MediaInspection:
    path = resolve_readable_path(raw_path, settings, sandbox=sandbox)
    if not path.exists() or not path.is_file():
        raise ToolError("Video does not exist: %s" % raw_path)
    metadata = _ffprobe_media_info(path)
    return MediaInspection(
        path=path,
        display_path=display_path(path, settings),
        mime_type=guess_mime_type(path, kind="video"),
        size_bytes=path.stat().st_size,
        metadata=metadata,
    )


def sample_video_frames(
    raw_path: str,
    settings: HarnessSettings,
    sandbox=None,
    frame_count: int = 6,
) -> list[Path]:
    path = resolve_readable_path(raw_path, settings, sandbox=sandbox)
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise ToolError(
            "Video frame sampling requires ffmpeg to be installed and available on PATH."
        )
    metadata = _ffprobe_media_info(path)
    duration = float(metadata.get("duration_seconds", 0) or 0)
    interval = max(duration / max(frame_count, 1), 0.5) if duration > 0 else 1.0
    output_dir = settings.state_dir / "media" / "video_frames" / uuid.uuid4().hex[:10]
    output_dir.mkdir(parents=True, exist_ok=True)
    pattern = output_dir / "frame-%03d.jpg"
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(path),
        "-vf",
        "fps=1/%s" % interval,
        "-frames:v",
        str(frame_count),
        str(pattern),
    ]
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise ToolError(
            "ffmpeg failed while sampling %s: %s"
            % (raw_path, (completed.stderr or completed.stdout).strip() or "unknown error")
        )
    frames = sorted(output_dir.glob("frame-*.jpg"))
    if not frames:
        raise ToolError("No video frames were produced for %s." % raw_path)
    return frames[:frame_count]


def _read_pdf_text(path: Path, max_chars: int) -> tuple[str, dict[str, object]]:
    try:
        from pypdf import PdfReader
    except Exception as exc:  # pragma: no cover - exercised when dependency is missing
        raise ToolError(
            "PDF extraction requires the optional pypdf dependency. Reinstall Ecology Harness after pulling the latest dependencies."
        ) from exc

    reader = PdfReader(str(path))
    parts = []
    for index, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            parts.append("[Page %s]\n%s" % (index, text))
        if max_chars > 0 and sum(len(item) for item in parts) >= max_chars:
            break
    return "\n\n".join(parts), {"page_count": len(reader.pages)}


def _read_docx_text(path: Path) -> tuple[str, dict[str, object]]:
    try:
        with zipfile.ZipFile(path) as archive:
            raw = archive.read("word/document.xml")
    except KeyError as exc:
        raise ToolError("DOCX file is missing word/document.xml: %s" % path) from exc
    root = ElementTree.fromstring(raw)
    paragraphs = []
    for paragraph in root.iter():
        if not paragraph.tag.endswith("}p"):
            continue
        texts = []
        for node in paragraph.iter():
            if node.tag.endswith("}t") and node.text:
                texts.append(node.text)
        if texts:
            paragraphs.append("".join(texts))
    return "\n\n".join(paragraphs), {"paragraph_count": len(paragraphs)}


def _read_ipynb_text(path: Path) -> tuple[str, dict[str, object]]:
    raw = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    cells = raw.get("cells", [])
    chunks = []
    for index, cell in enumerate(cells, start=1):
        cell_type = str(cell.get("cell_type", "unknown"))
        source = "".join(cell.get("source", []) or [])
        source = source.strip()
        if not source:
            continue
        chunks.append("[Cell %s | %s]\n%s" % (index, cell_type, source))
    return "\n\n".join(chunks), {"cell_count": len(cells)}


def _read_text_like_document(path: Path) -> tuple[str, dict[str, object]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    suffix = path.suffix.lower()
    if suffix in {".html", ".htm", ".xml"}:
        return _strip_markup(text), {"markup_stripped": True}
    return text, {"line_count": len(text.splitlines())}


def _strip_markup(text: str) -> str:
    stripped = re.sub(r"(?is)<(script|style)\b.*?>.*?</\1>", " ", text)
    stripped = re.sub(r"(?i)</(p|div|section|article|h\d|li|tr|br)>", "\n", stripped)
    stripped = re.sub(r"(?s)<[^>]+>", " ", stripped)
    return html.unescape(stripped)


def _normalize_document_text(text: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    collapsed = []
    previous_blank = False
    for line in lines:
        if not line:
            if not previous_blank:
                collapsed.append("")
            previous_blank = True
            continue
        collapsed.append(line)
        previous_blank = False
    return "\n".join(collapsed).strip()


def _ffprobe_media_info(path: Path) -> dict[str, object]:
    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:
        return {"warning": "ffprobe_not_available"}
    command = [
        ffprobe,
        "-v",
        "error",
        "-show_format",
        "-show_streams",
        "-of",
        "json",
        str(path),
    ]
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return {"warning": "ffprobe_failed"}
    try:
        payload = json.loads(completed.stdout or "{}")
    except json.JSONDecodeError:
        return {"warning": "ffprobe_invalid_json"}

    metadata: dict[str, object] = {}
    format_payload = payload.get("format", {}) or {}
    duration = format_payload.get("duration")
    if duration:
        try:
            metadata["duration_seconds"] = round(float(duration), 3)
        except (TypeError, ValueError):
            pass
    bit_rate = format_payload.get("bit_rate")
    if bit_rate:
        try:
            metadata["bit_rate"] = int(float(bit_rate))
        except (TypeError, ValueError):
            pass
    for stream in payload.get("streams", []) or []:
        codec_type = str(stream.get("codec_type", ""))
        if codec_type == "video":
            width = stream.get("width")
            height = stream.get("height")
            if width and height:
                metadata["resolution"] = "%sx%s" % (width, height)
            frame_rate = _parse_ffprobe_ratio(stream.get("r_frame_rate"))
            if frame_rate:
                metadata["fps"] = round(frame_rate, 3)
        if codec_type == "audio":
            sample_rate = stream.get("sample_rate")
            channels = stream.get("channels")
            if sample_rate:
                try:
                    metadata["sample_rate"] = int(sample_rate)
                except (TypeError, ValueError):
                    pass
            if channels:
                metadata["channels"] = channels
    return metadata


def _parse_ffprobe_ratio(value: object) -> float:
    if not value or not isinstance(value, str):
        return 0.0
    if "/" in value:
        left, right = value.split("/", 1)
        try:
            numerator = float(left)
            denominator = float(right)
        except (TypeError, ValueError):
            return 0.0
        if denominator == 0:
            return 0.0
        return numerator / denominator
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
