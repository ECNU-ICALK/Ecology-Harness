---
name: plant-growth-model-selection
description: Choose between crop models, functional-structural plant models, microbial-growth frameworks, and calibration stacks for plant and microbe growth simulation.
slug: plant-growth-model-selection
triggers: [/plant-growth-model-selection]
allowed-tools: [ListEcologyToolkits, ListEcologyFunctions, Read]
context: inline
---
Use this when the user needs the right growth-simulation family before committing to one toolchain.

Preferred mapping:
1. `PCSE / WOFOST`, `AquaCrop-OSPy`, `pyfao56`, `BioCro`, and `APSIM Next Generation` for annual crops, irrigation, canopy physiology, and yield scenarios.
2. `CPlantBox` and `OpenAlea L-Py` for root-shoot structure, branching, organ development, and functional-structural plant modeling.
3. `r3PG`, `medfate`, `LPJ-GUESS`, and `ED2` for woody plants, forests, shrublands, hydraulic stress, and stand dynamics.
4. `pyrealm` for productivity, ecophysiology, carbon, water, and environmental-response calculations.
5. `COBRApy`, `MICOM`, `COMETS`, `BacArena`, and `Community Simulator` for microbial metabolism, community assembly, cross-feeding, and spatial community dynamics.
6. `NUFEB`, `Tellurium`, `COPASI`, `PySCeS`, and `Vivarium Core` for biofilms, reactor-style growth, ODE systems, and composable process models.
7. `MDSINE2` and `miaSim` when longitudinal microbial time-series, perturbation studies, or benchmarking matter.
8. `pyPESTO` when parameter estimation, uncertainty, or sensitivity analysis is central.
9. Use `jupyter-mcp`, `labarchives`, and `unit-converter` when execution, provenance, and unit harmonization are part of the workflow.

Report:
- target system or organism
- recommended model family
- best-fit toolkit
- minimum required inputs
- likely outputs
- biggest assumptions or constraints
$ARGUMENTS
