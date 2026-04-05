---
name: hydrology-and-flood-screen
description: Screen freshwater, watershed, flow, flood, and riverine ecology questions using weather, hydrology, and coastal data sources.
slug: hydrology-and-flood-screen
triggers: [/hydrology-and-flood-screen]
allowed-tools: [Skill, SkillRead, ListMcpServersTool, ListMcpToolsTool, WebSearch, WebFetch, Read]
context: inline
---
Use this for streamflow, flood risk, river discharge, watershed context, or ecohydrology screening questions.

Preferred workflow:
1. Identify the basin, reach, site, or coastal-freshwater interface plus the time horizon.
2. Use `weather-open-meteo` for archive, forecast, flood, and climate context.
3. Use `swiss-environment` when hydrology observations or public environmental warnings are regionally relevant.
4. Use `noaa-tides-currents` for coastal flooding, water levels, and sea-level context.
5. Use `nasa` when Earth-observation or hazard context matters.

Return:
- focal site and hydrologic process
- likely best MCP source
- key forcing variables
- scale or uncertainty limits
- next data retrieval step
$ARGUMENTS
