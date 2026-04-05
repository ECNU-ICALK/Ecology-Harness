---
name: remote-sensing-catalog-hunt
description: Find the right imagery and raster catalog before download by combining STAC, NASA, GIS, and map-oriented context.
slug: remote-sensing-catalog-hunt
triggers: [/remote-sensing-catalog-hunt]
allowed-tools: [Skill, SkillRead, ListMcpServersTool, ListMcpToolsTool, WebSearch, WebFetch, Read]
context: inline
---
Use this when the user knows the phenomenon but not the best imagery, collection, asset type, or STAC catalog.

Preferred workflow:
1. Clarify study area, time window, spatial resolution, and target phenomenon.
2. Use `stac` first to locate candidate catalogs, collections, and item filters.
3. Use `nasa` when NASA Earth-observation collections or hazards are likely relevant.
4. Use `gis-mcp` for land-cover, NDVI, or raster-processing-oriented follow-up.
5. Use `mapbox-geospatial-operations` when geometry or route logic matters.

Output:
- candidate catalog or API
- likely collection names
- temporal and spatial filters
- asset or band expectations
- data-volume and compute risks
$ARGUMENTS
