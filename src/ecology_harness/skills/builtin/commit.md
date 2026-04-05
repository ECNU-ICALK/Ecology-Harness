---
name: commit
description: Review current changes and create a clean commit.
slug: commit
triggers: [/commit]
allowed-tools: [Bash, Read, Glob, Grep]
context: inline
---
Review the current git state and create a well-structured commit.

Checklist:
- inspect `git status` and staged or unstaged changes
- group related changes together
- avoid committing secrets, credentials, or unrelated files
- write a concise imperative commit message

User context: $ARGUMENTS
