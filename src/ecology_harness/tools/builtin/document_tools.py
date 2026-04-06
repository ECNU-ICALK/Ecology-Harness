from __future__ import annotations

from ecology_harness.runtime.attachments import (
    extract_document,
    infer_document_headings,
    inspect_audio,
    inspect_video,
    sample_video_frames,
)
from ecology_harness.tools.base import ToolContext, ToolDefinition, ToolResult
from ecology_harness.tools.registry import ToolRegistry


def register_document_tools(registry: ToolRegistry) -> None:
    registry.register(
        ToolDefinition(
            name="DocumentExtract",
            description="Extract normalized text from a local document such as PDF, DOCX, Markdown, CSV, JSON, HTML, or notebook.",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "max_chars": {"type": "integer"},
                },
                "required": ["path"],
            },
            handler=_document_extract,
            read_only=True,
            concurrent_safe=True,
            tags=("document", "analysis", "multimodal"),
        )
    )
    registry.register(
        ToolDefinition(
            name="DocumentInspect",
            description="Inspect a local document and return format hints, heading candidates, and a short excerpt.",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "max_chars": {"type": "integer"},
                },
                "required": ["path"],
            },
            handler=_document_inspect,
            read_only=True,
            concurrent_safe=True,
            tags=("document", "analysis"),
        )
    )
    registry.register(
        ToolDefinition(
            name="AudioInspect",
            description="Inspect a local audio file and return format and timing metadata.",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                },
                "required": ["path"],
            },
            handler=_audio_inspect,
            read_only=True,
            concurrent_safe=True,
            tags=("audio", "multimodal"),
        )
    )
    registry.register(
        ToolDefinition(
            name="VideoInspect",
            description="Inspect a local video file and return duration, frame-rate, and resolution hints when available.",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                },
                "required": ["path"],
            },
            handler=_video_inspect,
            read_only=True,
            concurrent_safe=True,
            tags=("video", "multimodal"),
        )
    )
    registry.register(
        ToolDefinition(
            name="VideoSampleFrames",
            description="Sample a small number of frames from a local video for multimodal review. Requires ffmpeg.",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "frame_count": {"type": "integer"},
                },
                "required": ["path"],
            },
            handler=_video_sample_frames,
            read_only=True,
            concurrent_safe=False,
            tags=("video", "frames", "multimodal"),
        )
    )


def _document_extract(params: dict, context: ToolContext) -> ToolResult:
    extracted = extract_document(
        params["path"],
        settings=context.settings,
        sandbox=context.services.get("sandbox"),
        max_chars=params.get("max_chars"),
    )
    heading_lines = infer_document_headings(extracted.text, limit=6)
    lines = [
        "==> %s <==" % extracted.display_path,
        "mime_type: %s" % extracted.mime_type,
        "size_bytes: %s" % extracted.size_bytes,
    ]
    if extracted.metadata:
        for key in ("page_count", "paragraph_count", "cell_count", "line_count", "truncated"):
            value = extracted.metadata.get(key)
            if value not in {None, "", False}:
                lines.append("%s: %s" % (key, value))
    if heading_lines:
        lines.extend(["headings:"] + ["- %s" % item for item in heading_lines])
    lines.extend(["", extracted.text or "(document is empty)"])
    return ToolResult(
        content="\n".join(lines),
        data={
            "path": extracted.display_path,
            "mime_type": extracted.mime_type,
            "size_bytes": extracted.size_bytes,
            "truncated": extracted.truncated,
            "metadata": extracted.metadata,
            "headings": heading_lines,
            "text": extracted.text,
        },
    )


def _document_inspect(params: dict, context: ToolContext) -> ToolResult:
    extracted = extract_document(
        params["path"],
        settings=context.settings,
        sandbox=context.services.get("sandbox"),
        max_chars=params.get("max_chars") or min(context.settings.max_document_chars, 6000),
    )
    headings = infer_document_headings(extracted.text, limit=8)
    excerpt = extracted.text[:800].strip()
    if len(extracted.text) > 800:
        excerpt += "..."
    lines = [
        "path: %s" % extracted.display_path,
        "mime_type: %s" % extracted.mime_type,
        "size_bytes: %s" % extracted.size_bytes,
        "truncated: %s" % ("yes" if extracted.truncated else "no"),
    ]
    for key in ("page_count", "paragraph_count", "cell_count", "line_count"):
        value = extracted.metadata.get(key)
        if value not in {None, ""}:
            lines.append("%s: %s" % (key, value))
    if headings:
        lines.extend(["headings:"] + ["- %s" % item for item in headings])
    lines.extend(["excerpt:", excerpt or "(document is empty)"])
    return ToolResult(
        content="\n".join(lines),
        data={
            "path": extracted.display_path,
            "mime_type": extracted.mime_type,
            "size_bytes": extracted.size_bytes,
            "truncated": extracted.truncated,
            "metadata": extracted.metadata,
            "headings": headings,
            "excerpt": excerpt,
        },
    )


def _audio_inspect(params: dict, context: ToolContext) -> ToolResult:
    inspection = inspect_audio(
        params["path"],
        settings=context.settings,
        sandbox=context.services.get("sandbox"),
    )
    lines = [
        "path: %s" % inspection.display_path,
        "mime_type: %s" % inspection.mime_type,
        "size_bytes: %s" % inspection.size_bytes,
    ]
    for key in ("duration_seconds", "sample_rate", "channels", "frame_count", "bit_rate", "warning"):
        value = inspection.metadata.get(key)
        if value not in {None, ""}:
            lines.append("%s: %s" % (key, value))
    return ToolResult(
        content="\n".join(lines),
        data={
            "path": inspection.display_path,
            "mime_type": inspection.mime_type,
            "size_bytes": inspection.size_bytes,
            "metadata": inspection.metadata,
        },
    )


def _video_inspect(params: dict, context: ToolContext) -> ToolResult:
    inspection = inspect_video(
        params["path"],
        settings=context.settings,
        sandbox=context.services.get("sandbox"),
    )
    lines = [
        "path: %s" % inspection.display_path,
        "mime_type: %s" % inspection.mime_type,
        "size_bytes: %s" % inspection.size_bytes,
    ]
    for key in ("duration_seconds", "fps", "resolution", "sample_rate", "channels", "bit_rate", "warning"):
        value = inspection.metadata.get(key)
        if value not in {None, ""}:
            lines.append("%s: %s" % (key, value))
    return ToolResult(
        content="\n".join(lines),
        data={
            "path": inspection.display_path,
            "mime_type": inspection.mime_type,
            "size_bytes": inspection.size_bytes,
            "metadata": inspection.metadata,
        },
    )


def _video_sample_frames(params: dict, context: ToolContext) -> ToolResult:
    frame_count = params.get("frame_count") or context.settings.video_frame_sample_count
    frames = sample_video_frames(
        params["path"],
        settings=context.settings,
        sandbox=context.services.get("sandbox"),
        frame_count=frame_count,
    )
    lines = ["sampled_frames:"]
    for frame in frames:
        lines.append("- %s" % frame)
    return ToolResult(
        content="\n".join(lines),
        data={
            "frame_paths": [str(item) for item in frames],
            "frame_count": len(frames),
        },
    )
