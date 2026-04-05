---
name: coastal-ecology-screen
description: Screen coasts, estuaries, wetlands, and marine-adjacent sites using NOAA, NASA, weather, and geospatial sources.
slug: coastal-ecology-screen
triggers: [/coastal-ecology-screen]
allowed-tools: [ListMcpServersTool, ListMcpToolsTool, Skill, SkillRead, WebSearch, WebFetch, Read]
context: inline
---
Screen a coastal or wetland question with the right mix of hydrology, atmosphere, and spatial context.

Source priority:
1. `noaa-tides-currents` for water level, tide, current, meteorology, sea-level trends, and flooding projections.
2. `weather-open-meteo` for weather and air quality.
3. `nasa` for imagery, wildfire, hazards, and Earth observation.
4. `gis-mcp` or `mapbox-geospatial-operations` for buffering, land-cover, NDVI, and site geometry.

Use cases:
- estuary exposure screening
- marsh or mangrove site context
- flood-risk pre-screening
- coastal restoration planning support

Report:
- site and scale
- coastal drivers and stressors
- likely ecological receptors
- best observation sources
- highest-uncertainty assumptions
$ARGUMENTS
