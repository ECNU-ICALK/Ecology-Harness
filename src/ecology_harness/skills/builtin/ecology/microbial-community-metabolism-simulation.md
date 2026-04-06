---
name: microbial-community-metabolism-simulation
description: Choose between metabolic, resource-competition, and community-assembly simulators for microbial ecology questions.
slug: microbial-community-metabolism-simulation
triggers: [/microbial-community-metabolism-simulation]
allowed-tools: [ListEcologyToolkits, Read]
context: inline
---
Use this when the question is about microbial consortia, cross-feeding, resource competition, or community assembly.

Preferred mapping:
1. `MICOM` for abundance-aware community metabolism and microbiome-style cross-feeding.
2. `COMETS` for metabolite diffusion, spatial cross-feeding, and dynamic community metabolism.
3. `BacArena` when microbial individuals and metabolic exchange both need to stay explicit.
4. `Community Simulator` when consumer-resource dynamics and ecological assembly matter more than genome-scale fluxes.
5. `COBRApy` for single-strain or component metabolic models that will feed into a larger community workflow.

Report:
- community type
- simulation family
- recommended toolkit
- inputs and priors
- expected outputs
$ARGUMENTS
