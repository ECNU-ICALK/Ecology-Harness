---
name: biodiversity-data-triage
description: Triage biodiversity questions into taxonomy, occurrence, habitat, and observation workflows using the installed ecology MCP catalog.
slug: biodiversity-data-triage
triggers: [/biodiversity-data-triage]
allowed-tools: [ListMcpServersTool, ListMcpToolsTool, WebSearch, WebFetch, Read]
context: inline
---
Break biodiversity work into the right data path before analysis.

Use this decision tree:
1. If the user needs taxon background, prefer `gis-mcp` with `get_species_info`.
2. If the user needs occurrences or observations, prefer `gis-mcp` with `download_species_occurrences`.
3. If the user needs habitat or vegetation context, combine `download_worldcover`, `compute_s2_ndvi`, and `download_satellite_imagery`.
4. If the user needs literature around species, habitats, or conservation interventions, hand off to `literature-multi-source-search`.
5. If the server needed is only cataloged in this build, fall back to official sources and make the gap explicit.

Output:
- biological entity or system
- likely data type needed
- best MCP server or fallback source
- quality risks such as taxonomic ambiguity, spatial bias, or sampling bias
- next recommended retrieval step
$ARGUMENTS
