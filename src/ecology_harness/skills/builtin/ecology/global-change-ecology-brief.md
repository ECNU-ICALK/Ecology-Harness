---
name: global-change-ecology-brief
description: Brief global-change ecology questions around warming, extreme events, phenology, range shifts, thresholds, and climate vulnerability.
slug: global-change-ecology-brief
triggers: [/global-change-ecology-brief]
allowed-tools: [Skill, SkillRead, ListMcpServersTool, ListMcpToolsTool, WebSearch, WebFetch, Read]
context: inline
---
Use this for climate change ecology, extreme-event impact, phenology, distribution shifts, vulnerability, adaptation, or NbS framing questions.

Preferred workflow:
1. Identify the ecological response, geography, and time horizon.
2. Use `open-meteo-advanced` or `weather-open-meteo` for forecast, historical, seasonal, or climate-projection context.
3. Use `nasa`, `stac`, and `gis-mcp` when Earth-observation context matters.
4. Use `openalex-research` and `literature-multi-source-search` for review articles, seminal papers, and trend mapping.
5. If the question intersects agriculture or restoration, chain to `agri-climate-screen` or `environmental-site-screen`.

Report:
- change driver
- ecological response pathway
- best climate or EO sources
- likely thresholds or confounders
- next synthesis or retrieval step
$ARGUMENTS
