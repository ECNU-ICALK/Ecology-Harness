---
name: ralplan
description: Turn a clarified request into an execution plan with milestones, risks, validation, and fallback paths.
slug: ralplan
triggers:
  - /ralplan
  - $ralplan
tools:
  - Read
  - Glob
  - Grep
  - SkillSearch
  - McpSearchTool
---
Use this skill after the task definition is clear enough to plan concrete work.

Workflow:
- summarize the problem and the execution target
- split work into the smallest meaningful milestones
- identify dependencies, data requirements, and validation steps
- call out the highest-risk decisions and how to de-risk them early
- recommend where to use existing skills, MCP servers, or tools instead of ad-hoc work

Output structure:
- **Plan Summary**
- **Milestones**
- **Dependencies**
- **Validation**
- **Risks and Fallbacks**
- **First Step**

Prefer an incremental plan over a one-shot rewrite. Keep plans actionable and reviewable.
