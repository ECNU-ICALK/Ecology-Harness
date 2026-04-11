---
name: crop-growth-simulation-workflow
description: Organize crop growth, irrigation, weather, soil, and management simulation questions using mature crop and agro-ecosystem models.
slug: crop-growth-simulation-workflow
triggers: [/crop-growth-simulation-workflow]
allowed-tools: [ListEcologyToolkits, DescribeEcologyToolkit, Bash, Read]
context: inline
---
Use this for crop growth, phenology, biomass, irrigation, drought, management, or yield-scenario questions.

Preferred mapping:
1. `AquaCrop-OSPy` for water-limited growth, irrigation scheduling, drought stress, and water productivity.
2. `pyfao56` for FAO-56 evapotranspiration, irrigation accounting, and lighter soil-water balance workflows.
3. `PCSE / WOFOST` for crop phenology, biomass, and yield when weather, soil, and management forcing are available.
4. `BioCro` when explicit canopy physiology, photosynthesis, and mechanistic crop growth are more important than standard management files.
5. `APSIM Next Generation` or `DSSAT Cropping System Model` for broader agro-ecosystem, rotation, and management-system scenarios.
6. Pair with `agri-climate-screen`, `weather-open-meteo`, or `nasa` when climate and forcing data are central.
7. Use `jupyter-mcp` for scenario notebooks and preprocessing; use `unit-converter` before comparing forcing datasets from different sources.

Execution guidance:
- If the user explicitly wants the simulation to run, use `DescribeEcologyToolkit` to inspect install guidance for the selected Python-first toolkit.
- If the package is missing and the install guidance is lightweight, use `Bash` to install it into the current harness Python environment, then verify the import and version before running any scenario code.
- Prefer `AquaCrop-OSPy`, `pyfao56`, `PCSE / WOFOST`, or `BioCro` for first-pass local execution because they are more automation-friendly than heavier desktop runtimes.

Report:
- crop and management question
- recommended simulator
- forcing data required
- calibration or validation need
- outputs to compare across scenarios
$ARGUMENTS
