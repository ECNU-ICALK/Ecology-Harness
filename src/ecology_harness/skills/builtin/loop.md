---
name: loop
description: Continue planned execution until the visible stop condition is satisfied.
slug: loop
triggers: [/loop]
allowed-tools: [TaskList, TaskUpdate, Skill, Bash, Read, Edit, Write, GetDiagnostics]
context: inline
---
Operate in persistent execution mode.

Keep moving through the work until one of these is true:
- the user-visible deliverable is complete
- you hit a real blocker that needs new user input
- further action would be destructive or speculative

At each turn:
- state the next concrete step briefly
- execute it
- update tasks if helpful
- stop only when the stop condition is met

Target:
$ARGUMENTS
