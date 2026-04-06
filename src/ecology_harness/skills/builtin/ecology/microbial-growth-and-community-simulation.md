---
name: microbial-growth-and-community-simulation
description: Organize microbial growth, metabolic modeling, reactor dynamics, and community interaction workflows using strong open-source simulation stacks.
slug: microbial-growth-and-community-simulation
triggers: [/microbial-growth-and-community-simulation]
allowed-tools: [ListEcologyToolkits, Read]
context: inline
---
Use this for microbial growth curves, substrate uptake, community dynamics, cross-feeding, or reactor-style microbial simulation questions.

Preferred mapping:
1. `COBRApy` for single-strain metabolic growth, flux balance analysis, and dynamic constraints.
2. `MICOM` for abundance-aware microbial-community metabolism and cross-feeding.
3. `COMETS` or `BacArena` when community metabolism must stay explicit in space, diffusion fields, or agent-like environments.
4. `Community Simulator` when the emphasis is on resource competition, assembly, and community ecology rather than genome-scale metabolic detail.
5. `Tellurium`, `COPASI`, `PySCeS`, or `Vivarium Core` for kinetic, mechanistic, custom process, batch-growth, inhibition, or reactor dynamics.
6. `NUFEB` when biofilm structure, particle interactions, or 3D spatial gradients matter.
7. `MDSINE2` or `miaSim` when longitudinal microbial time-series, perturbation studies, or benchmark generation are core to the study.
8. If sequencing, markers, or taxonomic follow-up drive the work, chain to `microbial-ecology-sequence-workflow`.

Report:
- organism or community type
- simulation style
- best-fit toolkit
- measurements or priors needed
- expected outputs and limitations
$ARGUMENTS
