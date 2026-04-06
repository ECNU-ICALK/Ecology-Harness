---
name: model-calibration-and-sensitivity
description: Plan calibration, sensitivity, uncertainty, and parameter-estimation workflows for traditional ecological process models and simulation systems.
slug: model-calibration-and-sensitivity
triggers: [/model-calibration-and-sensitivity]
allowed-tools: [ListEcologyToolkits, Read]
context: inline
---
Use this when a traditional ecological model exists but needs calibration, sensitivity analysis, or uncertainty framing.

Preferred mapping:
1. `pyPESTO` for parameter estimation, profile likelihoods, uncertainty, and sensitivity.
2. `jupyter-mcp` for preprocessing, residual analysis, plotting, and scenario notebooks.
3. `labarchives` for documenting assumptions, calibration decisions, and run provenance.
4. `unit-converter` before fitting whenever environmental forcing, field measurements, or model parameters mix units.
5. When possible, separate calibration, validation, and scenario-evaluation datasets.

Report:
- target model
- parameters to fit
- observed variables
- sensitivity or uncertainty method
- validation strategy
$ARGUMENTS
