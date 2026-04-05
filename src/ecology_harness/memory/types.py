MEMORY_TYPES = ["user", "feedback", "project", "reference"]

MEMORY_TYPE_DESCRIPTIONS = {
    "user": (
        "Information about the user's role, goals, preferences, or knowledge."
    ),
    "feedback": (
        "Guidance from the user about how the harness should work going forward."
    ),
    "project": (
        "Ongoing project context, decisions, deadlines, or facts not derivable from code."
    ),
    "reference": (
        "Pointers to external systems, documents, dashboards, or data sources."
    ),
}

WHAT_NOT_TO_SAVE = """\
## What NOT to save in memory
- Code structure, architecture, or file paths already derivable from the repo.
- Git history or recent diffs.
- Temporary task progress that belongs in the task tracker.
- Anything already documented in CLAUDE.md or project docs.
"""

MEMORY_SYSTEM_PROMPT = """\
## Memory system

You have a persistent file-based memory system.

Use memory for context that should outlive the current conversation:
- user preferences or role context
- feedback on how to work
- non-obvious project facts or decisions
- external references worth keeping around

Before relying on a memory about code or file state, verify it against the current workspace.
Memories are durable context, not guaranteed live truth.
"""
