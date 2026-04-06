---
name: watershed-and-ecohydrology-modeling
description: Organize watershed, hydrology, routing, and ecohydrology workflows using SWAT+, RHESSys, and the existing climate-data stack.
slug: watershed-and-ecohydrology-modeling
triggers: [/watershed-and-ecohydrology-modeling]
allowed-tools: [ListEcologyToolkits, Read]
context: inline
---
Use this for catchments, streamflow, nutrient export, routing, ecohydrology, basin-scale land-use change, or management-scenario questions.

Preferred mapping:
1. `SWAT+` for watershed hydrology, routing, nutrients, and agricultural management scenarios.
2. `RHESSys` for ecohydrological coupling where hydrology and ecosystem response need to stay tightly linked.
3. Use `weather-open-meteo` and `nasa` for forcing-data discovery and climate-scenario context.
4. Use `jupyter-mcp` for post-processing, calibration notebooks, and scenario comparison.

Report:
- basin or watershed question
- recommended simulator
- forcing and spatial inputs needed
- calibration targets
- outputs for management comparison
$ARGUMENTS
