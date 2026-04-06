---
name: audio-video-analysis
description: Analyze attached audio, video, and multi-frame visual material using the multimodal runtime and media tools.
slug: audio-video-analysis
triggers: [/audio-video-analysis]
allowed-tools: [AudioInspect, VideoInspect, VideoSampleFrames, DocumentInspect, DocumentExtract, Read, Glob]
context: inline
---
Analyze the requested audio or video carefully.

Checklist:
- if the current turn includes audio or video attachments, reason over them directly
- for workspace media files, use `AudioInspect` or `VideoInspect` first to understand duration, sample rate, fps, and resolution
- use `VideoSampleFrames` when you need explicit sampled frames for downstream review
- distinguish observed visual/audio evidence from inference
- when the user asks for event timing, mention uncertainty if timestamps are approximate

User context: $ARGUMENTS
