---
name: environmental-site-screen
description: Screen a site, corridor, or region for environmental and ecological context using the installed geospatial skills and ecology MCP catalog.
slug: environmental-site-screen
triggers: [/environmental-site-screen]
allowed-tools: [Skill, SkillRead, ListMcpServersTool, ListMcpToolsTool, WebSearch, WebFetch, Read]
context: inline
---
Screen a place before deeper analysis or field work.

Process:
1. Use `mapbox-geospatial-operations` to choose the right geospatial method:
   - straight-line geometry for buffers, containment, and area
   - routing or travel-time methods only when access/logistics matter
2. Use `mapbox-cartography` or `mapbox-data-visualization-patterns` when the user asks for map outputs or visual design guidance.
3. Inspect installed ecology MCP sources and match them to the task:
   - weather and air quality from `weather-open-meteo`
   - wildfire, hazards, and Earth observation from `nasa`
   - open dataset discovery from `eosc-data-commons`
   - local China-focused mapping context from `baidu-maps`
4. If a needed MCP source is only cataloged, say so and fall back to official web documentation or portals.

Output sections:
- location and analysis scope
- geospatial method choice
- likely environmental stressors
- likely ecological receptors or habitats
- data sources to query next
- decisions that should wait for better data

Always distinguish confirmed facts from screening hypotheses.
$ARGUMENTS
