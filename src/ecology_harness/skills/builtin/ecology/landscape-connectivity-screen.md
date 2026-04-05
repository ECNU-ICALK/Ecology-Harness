---
name: landscape-connectivity-screen
description: Screen landscape-ecology questions around connectivity, fragmentation, corridors, edge effects, and ecological security patterns.
slug: landscape-connectivity-screen
triggers: [/landscape-connectivity-screen]
allowed-tools: [Skill, SkillRead, ListMcpServersTool, ListMcpToolsTool, WebSearch, WebFetch, Read]
context: inline
---
Use this for fragmentation, movement corridors, edge effects, habitat mosaics, or landscape-scale conservation planning.

Preferred workflow:
1. Define the species or ecological process plus the analysis scale.
2. Use `stac` to identify suitable imagery or land-cover collections.
3. Use `gis-mcp` and `mapbox-geospatial-operations` to reason about geometry, connectivity layers, and access patterns.
4. Use `gbif` when species occurrence or barrier-crossing records are needed.
5. Use `literature-multi-source-search` for corridor design and connectivity metrics.

Return:
- focal process and movement scale
- likely spatial layers
- likely connectivity or fragmentation metrics
- major uncertainties
- next geospatial workflow
$ARGUMENTS
