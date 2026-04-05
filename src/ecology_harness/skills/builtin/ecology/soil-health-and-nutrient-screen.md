---
name: soil-health-and-nutrient-screen
description: Screen soil ecology, fertility, nutrient cycling, contamination, and remediation questions using literature, climate, chemistry, and dataset sources.
slug: soil-health-and-nutrient-screen
triggers: [/soil-health-and-nutrient-screen]
allowed-tools: [Skill, SkillRead, ListMcpServersTool, ListMcpToolsTool, WebSearch, WebFetch, Read]
context: inline
---
Use this for soil carbon, nutrient management, salinity, contamination, root-zone ecology, or remediation questions.

Preferred workflow:
1. Identify soil system, land use, management history, and target process or contaminant.
2. Use `literature-multi-source-search` for process evidence and methods.
3. Use `pubchem` when pesticide, PFAS, heavy-metal proxy chemistry, or contaminant-property reasoning is relevant.
4. Use `weather-open-meteo` and `nasa` when moisture, heat, drought, or climate forcing matters.
5. Use `eosc-data-commons`, `dataverse`, or `wsl-envidat` when the main need is open datasets.

Return:
- soil system and pressure
- likely data types or measurements
- supporting chemistry or climate context
- major interpretation risks
- best next dataset or literature step
$ARGUMENTS
