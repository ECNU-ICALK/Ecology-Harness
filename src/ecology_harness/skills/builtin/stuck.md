---
name: stuck
description: Recover from blockers by shrinking the problem and gathering the next missing fact.
slug: stuck
triggers: [/stuck]
allowed-tools: [Read, Glob, Grep, GetDiagnostics, Bash, TaskList, TaskUpdate]
context: inline
---
You are in blocker-recovery mode.

Do this:
1. restate the concrete blocker in one sentence
2. identify the smallest missing fact that would unblock progress
3. gather that fact using the minimal tool call
4. propose or execute the smallest next step

If a tracked task exists, update it so the blocker and next action are visible.

Current blocker:
$ARGUMENTS
