---
name: ecology-dataset-hunt
description: Discover and rank agriculture, environment, and ecology datasets across the installed ecology MCP catalog and official web sources.
slug: ecology-dataset-hunt
triggers: [/ecology-dataset-hunt]
allowed-tools: [ListMcpServersTool, ListMcpToolsTool, SkillRead, WebSearch, WebFetch, Read, Bash]
context: inline
---
Find the best-available datasets for the user's agriculture, environment, or ecology question.

Workflow:
1. List the installed MCP servers and focus on `eosc-data-commons`, `nasa`, `weather-open-meteo`, `mapbox`, `baidu-maps`, and `semantic-scholar`.
2. Check whether the needed source is only cataloged or also locally runnable. Be explicit when a server is installed as metadata only in this build.
3. Use official MCP-backed sources first when they fit the request:
   - EOSC Data Commons for open-access dataset discovery
   - NASA for Earth observation, wildfire, hazards, and climate/POWER data
   - Open-Meteo weather for forecast, historical weather, and air quality
   - Mapbox or Baidu Maps for geospatial context and routing
4. If the needed MCP path is not runnable yet, fall back to official dataset portals with WebSearch/WebFetch and keep the same source preference order.
5. Rank candidates by topical fit, spatial coverage, temporal coverage, license/access friction, and reproducibility.

Output format:
- One short summary paragraph
- A dataset table with: source, dataset/product, variables, spatial scale, temporal scale, access method, and caveats
- A final "recommended next pull" section with the top 1-3 sources

For ecology work, always capture biome/ecosystem relevance.
For agriculture work, always capture crop/system relevance.
$ARGUMENTS
