---
name: crop-water-and-irrigation-simulation
description: Select and organize crop water-balance, evapotranspiration, irrigation, and drought-response simulation workflows.
slug: crop-water-and-irrigation-simulation
triggers: [/crop-water-and-irrigation-simulation]
allowed-tools: [ListEcologyToolkits, Read]
context: inline
---
Use this when the main question is irrigation, evapotranspiration, deficit stress, or crop-water accounting rather than broad ecosystem simulation.

Preferred mapping:
1. `pyfao56` for FAO-56 evapotranspiration, irrigation scheduling, and field water-balance accounting.
2. `AquaCrop-OSPy` for water-limited growth, water productivity, and seasonal irrigation scenarios.
3. `PCSE / WOFOST` when water stress must be connected to phenology, biomass, and yield in a Python-first workflow.
4. `DSSAT Cropping System Model` or `APSIM Next Generation` when irrigation is only one part of a broader crop-management scenario.

Report:
- crop and stressor
- recommended simulator
- forcing data needed
- irrigation or soil data assumptions
- outputs to compare
$ARGUMENTS
