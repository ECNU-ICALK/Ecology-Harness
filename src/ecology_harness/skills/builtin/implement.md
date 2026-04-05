---
name: implement
description: Implement a feature incrementally with task tracking.
slug: implement
triggers: [/implement]
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep, TaskCreate, TaskUpdate, TaskList]
context: inline
---
Implement the requested change incrementally.

Checklist:
- clarify the target behavior
- break the work into small task units
- make changes in the existing style of the repository
- verify the result with the most relevant checks available

User context: $ARGUMENTS
