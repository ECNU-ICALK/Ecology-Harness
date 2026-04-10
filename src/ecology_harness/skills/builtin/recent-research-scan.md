---
name: recent-research-scan
description: Build a recent, multi-source research scan with recency filters, grounded citations, and clear uncertainty notes.
slug: recent-research-scan
triggers: /recent-research-scan
tools: WebSearch, WebFetch, SkillSearch, McpSearchTool, MCPTool, Read
---
Use this skill when the user asks for the latest or most recent developments, papers, datasets, benchmarks, releases, incidents, or methods.

Workflow:
- restate the user's topic, domain, geography, and time window
- default to a recent window such as the last 30, 90, or 365 days if the user does not specify one
- search multiple source types instead of relying on a single web result
- prefer primary sources, official docs, papers, datasets, or project repos
- separate confirmed facts from inference
- include exact dates when discussing recency
- call out source gaps, conflicting evidence, and missing verification

Recommended source mix:
- scientific literature or metadata sources through available MCP servers
- official project or repository release notes
- trusted web search results for recent reporting and announcements
- local project notes or workspace files if they contain relevant context

Output structure:
- topic and time window
- key developments
- strongest sources
- open questions or unresolved conflicts
- suggested next searches or follow-up tools
