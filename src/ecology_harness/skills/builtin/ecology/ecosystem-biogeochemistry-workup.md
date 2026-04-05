---
name: ecosystem-biogeochemistry-workup
description: Plan ecosystem and biogeochemistry workflows around carbon, nitrogen, phosphorus, methane, productivity, and ecosystem metabolism.
slug: ecosystem-biogeochemistry-workup
triggers: [/ecosystem-biogeochemistry-workup]
allowed-tools: [Skill, SkillRead, ListMcpServersTool, ListMcpToolsTool, WebSearch, WebFetch, Read]
context: inline
---
Use this for ecosystem-level questions such as carbon sinks, methane flux, nitrogen cycling, decomposition, productivity, or nutrient-transfer pathways.

Preferred workflow:
1. Identify ecosystem type, focal flux or pool, and temporal scale.
2. Use `literature-multi-source-search` for process understanding and methods.
3. Use `weather-open-meteo` and `nasa` when climate forcing, drought, inundation, or energy balance matter.
4. Use `eosc-data-commons`, `dataverse`, or `wsl-envidat` when the bottleneck is finding open datasets.
5. Use `stac` or `gis-mcp` when land cover, moisture, productivity, or imagery context is required.

Return:
- ecosystem and process
- likely measurements or proxies
- best supporting datasets
- seasonal and disturbance drivers
- next paper or dataset stack
$ARGUMENTS
