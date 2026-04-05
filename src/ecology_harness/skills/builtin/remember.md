---
name: remember
description: Capture durable user or project facts in memory when they will matter later.
slug: remember
triggers: [/remember]
allowed-tools: [MemorySave, MemorySearch, MemoryRead]
context: inline
---
Review the current request and only save information that is durable and likely to help in future sessions.

When memory is warranted:
- save concise facts, preferences, stable project constraints, or repeated workflow conventions
- avoid saving transient execution state or anything that can be re-derived from the repository

Use `MemorySave` with a short descriptive name, a one-line description, and compact content.

If nothing is durable enough to save, explain that briefly instead of writing memory.

User context:
$ARGUMENTS
