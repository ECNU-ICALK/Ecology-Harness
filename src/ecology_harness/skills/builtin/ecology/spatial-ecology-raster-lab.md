---
name: spatial-ecology-raster-lab
description: Plan raster and remote-sensing workflows for ecology using GIS MCP, Mapbox geospatial guidance, and Earth-observation sources.
slug: spatial-ecology-raster-lab
triggers: [/spatial-ecology-raster-lab]
allowed-tools: [ListMcpServersTool, ListMcpToolsTool, Skill, SkillRead, WebSearch, WebFetch, Read]
context: inline
---
Design a spatial-ecology workflow before downloading or processing data.

Use the following source mapping:
- `stac` for catalog, collection, and item discovery before you commit to downloads
- `gis-mcp` for `download_climate_data`, `download_worldcover`, `compute_s2_ndvi`, and `download_satellite_imagery`
- `mapbox-geospatial-operations` to choose the correct geometry or routing logic
- `nasa` when imagery or Earth-observation product discovery matters
- `weather-open-meteo` when weather, air-quality, flood, or climate context is part of the raster question
- `eosc-data-commons` when open dataset discovery is the real bottleneck

For each workflow, define:
- study area
- resolution and temporal window
- likely raster products
- derived indices or layers
- validation or ground-truth needs
- file and compute risks

If the user asks for a finished analysis but the MCP transport is only cataloged, first return the most plausible dataset stack and processing plan.
$ARGUMENTS
