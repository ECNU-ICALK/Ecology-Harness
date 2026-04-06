---
name: terrestrial-biosphere-and-vegetation-modeling
description: Organize terrestrial carbon, water, nitrogen, LAI, vegetation-dynamics, and long-term biosphere workflows using LPJ-GUESS, ED2, Biome-BGC, and CENTURY or DayCent.
slug: terrestrial-biosphere-and-vegetation-modeling
triggers: [/terrestrial-biosphere-and-vegetation-modeling]
allowed-tools: [ListEcologyToolkits, Read]
context: inline
---
Use this for dynamic vegetation, LAI, NPP, soil carbon, terrestrial carbon-water-nitrogen coupling, or long-term ecosystem response questions.

Preferred mapping:
1. `LPJ-GUESS` for dynamic global vegetation and climate-response studies.
2. `ED2` for ecosystem demography and vegetation-structure questions.
3. `Biome-BGC` for carbon, water, nitrogen, LAI, and ecophysiological process studies.
4. `CENTURY / DayCent` for plant-soil nutrient cycling and soil-carbon-oriented scenarios.
5. Pair with `global-change-ecology-brief` and `weather-open-meteo` or `nasa` when climate forcing is central.

Report:
- terrestrial process question
- best-fit model
- forcing data and timescale
- key pools or fluxes
- likely validation targets
$ARGUMENTS
