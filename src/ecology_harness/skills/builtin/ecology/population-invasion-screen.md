---
name: population-invasion-screen
description: Screen population ecology, invasion, dispersal, and small-population questions with occurrence, literature, and landscape sources.
slug: population-invasion-screen
triggers: [/population-invasion-screen]
allowed-tools: [Skill, SkillRead, ListMcpServersTool, ListMcpToolsTool, WebSearch, WebFetch, Read]
context: inline
---
Use this for population growth, viability, metapopulation, spread, extinction risk, or invasive expansion questions.

Preferred workflow:
1. Define the species, region, time horizon, and population process of interest.
2. Use `gbif` for occurrence history and spatial spread signals.
3. Use `mapbox`, `gis-mcp`, or `stac` when barriers, corridors, or habitat change are central.
4. Use `literature-multi-source-search` for demographic parameters, prior models, and intervention evidence.
5. If the question becomes conservation-genetic, use `ncbi-datasets`.

Return:
- focal taxon and geography
- likely data sources for abundance, occurrence, or demographics
- likely model family
- major uncertainties
- strongest next retrieval step
$ARGUMENTS
