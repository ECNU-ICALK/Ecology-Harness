---
name: batch
description: Group discovery work into compact batches before making changes.
slug: batch
triggers: [/batch]
allowed-tools: [Read, Glob, Grep, ListDirectoryTool, SkillRead]
context: inline
---
Group read-only discovery into a small number of focused batches.

Principles:
- prefer a few high-signal reads over many tiny calls
- capture patterns and differences across files
- conclude with the minimal action plan that follows from the evidence

Discovery target:
$ARGUMENTS
