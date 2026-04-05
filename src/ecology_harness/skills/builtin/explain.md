---
name: explain
description: Explain code, architecture, or output clearly and concisely.
slug: explain
triggers: [/explain]
allowed-tools: [Read, Glob, Grep, MemorySearch]
context: inline
---
Explain the requested topic clearly.

Checklist:
- read the relevant source before answering
- lead with the main idea
- reference concrete files or functions when possible
- separate observed facts from inferences

User context: $ARGUMENTS
