---
name: deep-interview
description: Clarify a request before planning or implementation by surfacing goals, constraints, unknowns, and success criteria.
slug: deep-interview
triggers:
  - /deep-interview
  - /clarify
  - $deep-interview
tools:
  - Read
  - Glob
  - Grep
  - WebFetch
  - WebSearch
  - SkillSearch
---
Use this skill when a request is ambiguous, underspecified, or likely to benefit from a sharper task definition before planning or coding.

Workflow:
- restate the goal in plain language
- identify the target outcome, constraints, and non-goals
- surface the minimum unanswered questions that would change the approach
- if local files or docs are relevant, inspect only what is needed to sharpen the problem
- make reasonable assumptions when safe, but label them explicitly

Output structure:
- **Goal**
- **What We Already Know**
- **Open Questions**
- **Working Assumptions**
- **Success Criteria**
- **Ready For Planning**

Do not jump into implementation. The purpose of this skill is to produce a clean, decision-ready problem definition.
