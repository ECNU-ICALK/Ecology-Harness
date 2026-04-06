# Ecology Process Modeling Pack

This document records the traditional process-model, ABM, watershed, and
ecosystem-simulation layer now cataloged in Ecology Harness.

## Installed Skills

- `process-model-selection`
  - purpose: choose the right process-model family before implementation
- `agent-based-ecology-modeling`
  - purpose: NetLogo, Mesa, and GAMA selection for individual-based and multi-agent ecology
- `watershed-and-ecohydrology-modeling`
  - purpose: SWAT+ and RHESSys workflows for basin and ecohydrology questions
- `food-web-and-trophic-simulation`
  - purpose: Ecopath with Ecosim and trophic-structure workflows
- `forest-landscape-disturbance-modeling`
  - purpose: LANDIS-II and disturbance-oriented forest landscape analysis
- `terrestrial-biosphere-and-vegetation-modeling`
  - purpose: LPJ-GUESS, ED2, Biome-BGC, and CENTURY or DayCent selection
- `model-calibration-and-sensitivity`
  - purpose: calibration, sensitivity, and uncertainty across traditional simulators
- `cross-model-scenario-comparison`
  - purpose: compare outputs from multiple ecological simulators without mixing assumptions carelessly

## Cataloged Model Systems

- first-priority process and simulation systems
  - `NetLogo`
  - `Mesa`
  - `GAMA Platform`
  - `DSSAT Cropping System Model`
  - `SWAT+`
  - `Ecopath with Ecosim`

- second-wave systems already cataloged for deeper expansion
  - `LPJ-GUESS`
  - `ED2`
  - `Biome-BGC`
  - `CENTURY / DayCent`
  - `RHESSys`
  - `LANDIS-II`
  - `Madingley Model`
  - `RangeShifter 2.0`

## Execution Spine

The current recommended execution pattern is:

- use heavy external models as cataloged toolkits
- use `jupyter-mcp` for pre-processing, launch wrappers, and post-processing
- use `labarchives` for provenance and run documentation
- use `unit-converter` before calibration and cross-model comparison
- add model-specific runners gradually once local installs are stable

## Planned Runner Surface

The next natural tool layer would include:

- `RunNetLogoModel`
- `RunMesaScenario`
- `RunGamaScenario`
- `RunDSSATScenario`
- `RunSWATPlusProject`
- `RunEcopathScenario`
- `ParseModelOutputs`
- `CompareScenarioRuns`
- `BuildForcingDataset`

## Example Prompts

```text
/process-model-selection restoration grazing fire and hydrology interactions in a catchment
/agent-based-ecology-modeling pollinator movement and flower visitation in fragmented farmland
/watershed-and-ecohydrology-modeling watershed nutrient export under changing fertilizer inputs
/food-web-and-trophic-simulation coastal food-web response to fishing pressure
/forest-landscape-disturbance-modeling wildfire and harvest scenarios in a temperate forest
/terrestrial-biosphere-and-vegetation-modeling long-term NPP and soil-carbon response to warming
/model-calibration-and-sensitivity calibrate a watershed model against streamflow and nitrate
/cross-model-scenario-comparison compare DSSAT and APSIM under heat and irrigation scenarios
```
