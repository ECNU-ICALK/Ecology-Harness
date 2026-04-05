---
name: open-access-paper-harvest
description: Recover open-access full text and DOI metadata for ecology research papers using Unpaywall, Crossref, and related literature sources.
slug: open-access-paper-harvest
triggers: [/open-access-paper-harvest]
allowed-tools: [ListMcpServersTool, ListMcpToolsTool, Skill, SkillRead, WebSearch, WebFetch, Read]
context: inline
---
Use this when the research bottleneck is not "finding papers" but "getting usable open-access full text".

Preferred sequence:
1. Identify the paper by DOI, exact title, or a short candidate set from `literature-multi-source-search`.
2. Use `crossref` to normalize DOI metadata when the title or DOI is messy.
3. Use `openalex-research` to check whether an open-access version or PDF link is already available.
4. Use `unpaywall` to:
   - resolve OA status
   - fetch the best OA landing page
   - fetch and extract OA PDF text when available
5. If neither source yields OA full text, report that clearly and fall back to abstract-only synthesis instead of pretending the full text was found.

Required output:
- paper identifier
- DOI status
- OA availability
- best OA URL
- whether full text was actually obtained
- what evidence remains abstract-only

For ecology research, highlight if the retrieved paper is:
- field study
- modeling study
- review or synthesis
- methods paper
$ARGUMENTS
