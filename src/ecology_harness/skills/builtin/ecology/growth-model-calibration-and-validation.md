---
name: growth-model-calibration-and-validation
description: Plan calibration, sensitivity, uncertainty, and validation workflows for plant, crop, algae, or microbial growth models.
slug: growth-model-calibration-and-validation
triggers: [/growth-model-calibration-and-validation]
allowed-tools: [ListEcologyToolkits, Read]
context: inline
---
Use this when a growth model exists but needs parameter fitting, sensitivity checks, uncertainty analysis, or validation design.

Preferred mapping:
1. Use `pyPESTO` for parameter estimation, profile likelihoods, sensitivity, and uncertainty workflows.
2. Use `jupyter-mcp` for notebook-based preprocessing, calibration loops, residual analysis, and plotting.
3. Use `labarchives` to preserve calibration runs, assumptions, and provenance.
4. Use `unit-converter` before fitting whenever inputs mix units, reporting conventions, or scales.
5. Validate against held-out seasons, treatments, or independent time-series whenever possible.

Report:
- model to calibrate
- parameters and priors
- observed variables
- fitting and validation split
- uncertainty or sensitivity outputs
$ARGUMENTS
