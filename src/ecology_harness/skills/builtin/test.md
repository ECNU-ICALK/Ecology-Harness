---
name: test
description: Run or add targeted tests for the current change.
slug: test
triggers: [/test]
allowed-tools: [Bash, Read, Glob, Grep, GetDiagnostics]
context: inline
---
Validate the change with focused testing.

Checklist:
- find the most relevant existing tests
- run the smallest credible test command first
- if no tests exist, add targeted tests where appropriate
- summarize failures before proposing broader changes

User context: $ARGUMENTS
