---
name: literature-multi-source-search
description: Search ecology and environment literature across Semantic Scholar, PubMed, Crossref, and broader multi-source academic MCP servers.
slug: literature-multi-source-search
triggers: [/literature-multi-source-search]
allowed-tools: [ListMcpServersTool, ListMcpToolsTool, Skill, SkillRead, WebSearch, WebFetch, Read]
context: inline
---
Run a literature search across multiple scholarly sources instead of relying on a single index.

Preferred order:
1. Use `simple-pubmed` for biomedical, toxicology, exposure, environmental health, and life-science questions.
2. Use `semantic-scholar` for recommendation, citation, and related-work expansion.
3. Use `scientific-papers` for broader coverage across arXiv, OpenAlex, PMC, Europe PMC, bioRxiv, and CORE.
4. Use `crossref` to clean up DOI metadata or fill gaps in title and author lookup.
5. If the user starts vague, chain to `paper-triage`.
6. If the user already has seed papers, chain to `expand-references` and `trace-citations`.

Required output:
- search question
- sources queried
- top papers by source
- duplicates or conflicts across sources
- strongest next paper set to read
- what source should be queried next if evidence is still thin

When remote MCP execution is not available in this build, say which configured servers would have been used and fall back to official web search or the installed Semantic Scholar bundle.
$ARGUMENTS
