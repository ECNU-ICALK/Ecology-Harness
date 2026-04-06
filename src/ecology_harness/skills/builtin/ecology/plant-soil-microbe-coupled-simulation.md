---
name: plant-soil-microbe-coupled-simulation
description: Frame coupled plant, soil, nutrient, and microbial simulation workflows for ecology, agriculture, and biogeochemical studies.
slug: plant-soil-microbe-coupled-simulation
triggers: [/plant-soil-microbe-coupled-simulation]
allowed-tools: [ListEcologyToolkits, Read]
context: inline
---
Use this for coupled plant-soil-microbe, rhizosphere, nutrient-turnover, or multi-compartment growth simulation questions.

Preferred mapping:
1. `CPlantBox` for root geometry and plant-soil structure.
2. `pyrealm` for environmental response, productivity, and simplified carbon or water coupling.
3. `COBRApy` or `MICOM` for microbial metabolic submodels and nutrient-transformation logic.
4. `Tellurium`, `COPASI`, or `PySCeS` for explicit coupled ODE systems across plants, substrates, and microbes.
5. Use `jupyter-mcp`, `labarchives`, and `influxdb3` when telemetry, assay, or experiment logs need to sit beside the simulation.

Report:
- compartments to couple
- main driving variables
- candidate coupling strategy
- observables for calibration
- practical simplifications
$ARGUMENTS
