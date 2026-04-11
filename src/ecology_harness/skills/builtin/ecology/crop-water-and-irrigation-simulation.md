---
name: crop-water-and-irrigation-simulation
description: Select and organize crop water-balance, evapotranspiration, irrigation, and drought-response simulation workflows.
slug: crop-water-and-irrigation-simulation
triggers: [/crop-water-and-irrigation-simulation]
allowed-tools: [ListEcologyToolkits, DescribeEcologyToolkit, Bash, Read]
context: inline
---
Use this when the main question is irrigation, evapotranspiration, deficit stress, or crop-water accounting rather than broad ecosystem simulation.

Preferred mapping:
1. `pyfao56` for FAO-56 evapotranspiration, irrigation scheduling, and field water-balance accounting.
2. `AquaCrop-OSPy` for water-limited growth, water productivity, and seasonal irrigation scenarios.
3. `PCSE / WOFOST` when water stress must be connected to phenology, biomass, and yield in a Python-first workflow.
4. `DSSAT Cropping System Model` or `APSIM Next Generation` when irrigation is only one part of a broader crop-management scenario.

Execution guidance:
- If the user wants a runnable simulation instead of only a model recommendation, inspect `DescribeEcologyToolkit` for the preferred Python toolkit first.
- When the chosen toolkit has a straightforward `pip install ...` command and is missing, install it in the current harness Python environment via `Bash`, then verify the import before proceeding.
- Prefer lightweight Python-first stacks such as `pyfao56`, `AquaCrop-OSPy`, or `PCSE / WOFOST` before escalating to heavier desktop-style runtimes.

Report:
- crop and stressor
- recommended simulator
- forcing data needed
- irrigation or soil data assumptions
- outputs to compare
$ARGUMENTS
