from __future__ import annotations

from ecology_harness.runtime.messages import ChatMessage


def derive_session_title(messages: list[ChatMessage]) -> str:
    for message in messages:
        if message.role != "user":
            continue
        text = message.summary_text(max_document_chars=180).strip().replace("\n", " ")
        if not text:
            continue
        if len(text) > 72:
            return text[:69].rstrip() + "..."
        return text
    return "Untitled session"


def derive_session_recap(
    messages: list[ChatMessage],
    compaction: dict | None = None,
) -> str:
    assistant = ""
    user = ""
    for message in reversed(messages):
        text = message.summary_text(max_document_chars=220).strip().replace("\n", " ")
        if not text:
            continue
        if not assistant and message.role == "assistant":
            assistant = text
        elif not user and message.role == "user":
            user = text
        if assistant and user:
            break
    parts = []
    if user:
        parts.append("Latest ask: %s" % user)
    if assistant:
        parts.append("Latest outcome: %s" % assistant)
    if compaction and compaction.get("compressed_summary"):
        parts.append("Continuation: %s" % str(compaction["compressed_summary"]).strip()[:180])
    recap = " | ".join(parts).strip()
    if len(recap) > 320:
        recap = recap[:317].rstrip() + "..."
    return recap
