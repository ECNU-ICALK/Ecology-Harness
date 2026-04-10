---
name: ralph
description: Execute an approved plan iteratively, verifying progress and surfacing blockers instead of silently drifting.
slug: ralph
triggers:
  - /ralph
  - $ralph
tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
  - SkillSearch
  - McpSearchTool
  - CheckpointList
  - CheckpointRestore
---
Use this skill when the task is ready for execution.

Workflow:
- restate the approved goal and the immediate next step
- implement in small increments, verifying after each meaningful change
- prefer built-in tools, existing skills, and existing project structure over inventing parallel flows
- if a blocker appears, stop, explain it clearly, and propose the narrowest next decision
- when useful, mention checkpoints, tests, or validation evidence explicitly

Output structure:
- **Current Objective**
- **What Changed**
- **Verification**
- **Open Risks**
- **Next Step**

Do not pretend the task is complete unless verification supports it.
