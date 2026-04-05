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
1. If the user needs taxon background, prefer `gbif` for taxonomy and vernacular names, then fall back to `gis-mcp` for species context helpers.
2. If the user needs occurrences or observations, prefer `gbif_occurrence_search` or `gbif_occurrence_count`; use `gis-mcp` only when you need bundled raster or species-context workflows.
3. If the user needs habitat, land-cover, or imagery context, combine `stac`, `download_worldcover`, `compute_s2_ndvi`, and `download_satellite_imagery`.
4. If the user needs literature around species, habitats, or conservation interventions, hand off to `literature-multi-source-search`.
5. If the server needed is only cataloged in this build, fall back to official sources and make the gap explicit.

Output:
- biological entity or system
- likely data type needed
- best MCP server or fallback source
- quality risks such as taxonomic ambiguity, spatial bias, or sampling bias
- next recommended retrieval step
$ARGUMENTS
