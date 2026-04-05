---
name: fix
description: Diagnose and fix a bug with minimal, verifiable changes.
slug: fix
triggers: [/fix]
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep, GetDiagnostics, TaskCreate, TaskUpdate]
context: inline
---
Fix the issue systematically.

Checklist:
- reproduce or locate the failure boundary
- inspect the relevant code path before editing
- apply the smallest plausible fix
- verify with diagnostics or tests

User context: $ARGUMENTS
