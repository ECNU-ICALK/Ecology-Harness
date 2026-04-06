---
name: microbiome-timeseries-and-benchmark-simulation
description: Plan longitudinal microbial-community inference, perturbation, and benchmark-data simulation workflows.
slug: microbiome-timeseries-and-benchmark-simulation
triggers: [/microbiome-timeseries-and-benchmark-simulation]
allowed-tools: [ListEcologyToolkits, Read]
context: inline
---
Use this for microbiome perturbation studies, repeated time-series, synthetic benchmarks, or method-testing workflows.

Preferred mapping:
1. `MDSINE2` for longitudinal microbial-dynamics inference with interaction structure.
2. `miaSim` for generating microbiome count tables, perturbation scenarios, and benchmark datasets.
3. `pyPESTO` when the simulated or inferred model still needs parameter estimation and uncertainty analysis.
4. Chain to `microbial-ecology-sequence-workflow` when sequence processing or taxonomic follow-up is part of the workflow.

Report:
- study design
- recommended simulator
- data type and temporal resolution
- benchmark or inference target
- validation checks
$ARGUMENTS
