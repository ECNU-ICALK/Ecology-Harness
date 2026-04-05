---
name: research-data-repository-hunt
description: Find ecology-relevant datasets in Dataverse and related research-data repositories, then map the next retrieval step.
slug: research-data-repository-hunt
triggers: [/research-data-repository-hunt]
allowed-tools: [ListMcpServersTool, ListMcpToolsTool, SkillRead, WebSearch, WebFetch, Read]
context: inline
---
Use this when the user needs actual research datasets, not just papers.

Source order:
1. `dataverse` for hosted research-data repositories and DOI-level dataset records
2. `eosc-data-commons` for broader open-access dataset discovery
3. `wsl-envidat` or `swiss-environment` when the geography is Switzerland
4. `gis-mcp`, `nasa`, and `weather-open-meteo` when the best path is product-oriented rather than repository-oriented

Workflow:
1. Clarify whether the user needs raw measurements, processed gridded products, or reproducibility artifacts.
2. Search repository-style sources first.
3. If a dataset DOI is found, prefer richer repository metadata such as Croissant records.
4. Return the best 3-5 datasets with access notes and reuse risks.

Output:
- dataset objective
- repository or source
- DOI or persistent identifier
- data type
- access friction
- likely reuse caveats
- top next retrieval step
$ARGUMENTS
