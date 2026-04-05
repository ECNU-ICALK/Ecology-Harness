---
name: species-occurrence-workbench
description: Workbench for species occurrence, taxonomy, distribution, and habitat-context retrieval using GBIF, STAC, and GIS-oriented sources.
slug: species-occurrence-workbench
triggers: [/species-occurrence-workbench]
allowed-tools: [Skill, SkillRead, ListMcpServersTool, ListMcpToolsTool, WebSearch, WebFetch, Read]
context: inline
---
Use this when the core task is to find a taxon, resolve names, inspect occurrence coverage, and connect records to habitat context.

Preferred workflow:
1. Resolve the scientific name with `gbif_species_match` when naming is uncertain.
2. Use `gbif_occurrence_count` before large retrievals, then `gbif_occurrence_search` for more detailed filtering.
3. Use `stac` or `gis-mcp` to add land-cover, NDVI, or imagery context around the occurrence footprint.
4. Use `literature-multi-source-search` when you need conservation or distribution-background papers.

Return:
- taxon resolution status
- likely occurrence source and filters
- habitat or imagery context source
- data-quality risks such as sampling bias, taxonomic ambiguity, or temporal gaps
- next recommended query
$ARGUMENTS
