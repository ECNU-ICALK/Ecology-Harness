---
name: process-model-selection
description: Choose between traditional process models, ABM platforms, watershed simulators, forest-disturbance models, and food-web systems for ecology research.
slug: process-model-selection
triggers: [/process-model-selection]
allowed-tools: [ListEcologyToolkits, ListEcologyFunctions, Read]
context: inline
---
Use this when the user needs a traditional ecological model family rather than only a literature or data-analysis workflow.

Preferred mapping:
1. `NetLogo`, `Mesa`, and `GAMA Platform` for agent-based and individual-based ecology.
2. `DSSAT Cropping System Model`, `APSIM Next Generation`, `PCSE / WOFOST`, and `AquaCrop-OSPy` for crop and agro-ecosystem simulation.
3. `SWAT+` and `RHESSys` for watershed, routing, ecohydrology, and land-use-change scenarios.
4. `Ecopath with Ecosim` for trophic balance, biomass flow, fisheries, and food-web scenarios.
5. `LPJ-GUESS`, `ED2`, `Biome-BGC`, and `CENTURY / DayCent` for terrestrial carbon-water-nitrogen, LAI, vegetation, and long-term biosphere dynamics.
6. `LANDIS-II` for forest landscapes, succession, fire, harvest, and disturbance-regime studies.
7. `Madingley Model` for general ecosystem simulation and `RangeShifter 2.0` for dispersal, range shifts, and spatial eco-evolution.
8. Use `jupyter-mcp`, `labarchives`, and `unit-converter` as the execution and provenance spine around heavy external models.

Report:
- target ecological process
- recommended model family
- best-fit system
- minimum input data
- expected outputs
- biggest assumptions and limitations
$ARGUMENTS
