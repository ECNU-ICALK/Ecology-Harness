---
name: agri-climate-screen
description: Screen agricultural systems for climate, weather, and landscape signals using the installed ecology tool and skill pack.
slug: agri-climate-screen
triggers: [/agri-climate-screen]
allowed-tools: [Skill, SkillRead, ListMcpServersTool, ListMcpToolsTool, WebSearch, WebFetch, Read]
context: inline
---
Assess an agricultural question through climate, weather, and landscape signals.

Use this structure:
1. Identify the crop, livestock system, or farming practice.
2. Identify the geography, season, and management horizon.
3. Check the installed ecology MCP catalog for:
   - `weather-open-meteo` for weather and air quality
   - `nasa` for POWER, FIRMS, GIBS, and broader Earth observation context
   - `eosc-data-commons` for open datasets
   - `mapbox` or `baidu-maps` for site and access context
4. If the user also needs evidence, call `ecology-evidence-synthesis`.

Report:
- likely climate or weather pressures
- likely environmental co-factors such as smoke, heat, drought, flood, or access constraints
- best next datasets or papers to inspect
- assumptions and missing variables

Never present this screening as a full agronomic recommendation.
$ARGUMENTS
