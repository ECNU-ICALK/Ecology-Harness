---
name: environmental-chemistry-risk-scan
description: Screen pollutants, pesticides, PFAS, microplastics, and environmental-chemistry questions with PubChem and literature sources.
slug: environmental-chemistry-risk-scan
triggers: [/environmental-chemistry-risk-scan]
allowed-tools: [Skill, SkillRead, ListMcpServersTool, ListMcpToolsTool, WebSearch, WebFetch, Read]
context: inline
---
Use this for pollutant identity, environmental fate, toxicity, regulatory context, or chemistry-to-ecology bridging questions.

Preferred workflow:
1. Normalize the chemical identity, synonym set, or CAS number.
2. Use `pubchem` for compound properties, similarity, toxicity, regulatory context, and environmental fate signals.
3. Use `simple-pubmed`, `scientific-papers`, or `openalex-research` for ecotoxicology and environmental-health literature.
4. Use `crossref` and `unpaywall` when you need DOI cleanup or full text.

Report:
- compound identity and synonym risks
- key properties and fate indicators
- likely ecological or health endpoints
- best supporting literature sources
- next retrieval or review step
$ARGUMENTS
