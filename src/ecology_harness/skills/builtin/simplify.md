---
name: simplify
description: Refactor code to reduce complexity while preserving behavior.
slug: simplify
triggers: [/simplify]
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep, GetDiagnostics]
context: inline
---
Simplify the target code without changing behavior.

Checklist:
- identify duplication, over-branching, or confusing abstractions
- prefer smaller helpers and clearer naming
- keep public behavior stable unless asked otherwise
- validate after the refactor

User context: $ARGUMENTS
