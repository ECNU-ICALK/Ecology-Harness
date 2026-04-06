---
name: root-and-rhizosphere-architecture-modeling
description: Plan root-system, rhizosphere, plant-soil geometry, and root-informed structural plant modeling workflows.
slug: root-and-rhizosphere-architecture-modeling
triggers: [/root-and-rhizosphere-architecture-modeling]
allowed-tools: [ListEcologyToolkits, Read]
context: inline
---
Use this for root architecture, rhizosphere geometry, soil-column experiments, branching, or trait-informed root-system simulations.

Preferred mapping:
1. `CPlantBox` for explicit root architecture, plant-soil geometry, and rhizosphere-aware simulation.
2. `OpenAlea L-Py` for generative branching rules, organ development, and structural plant representations.
3. `PlantCV` when root or organ measurements from images are needed for parameterization.
4. `pyrealm` when root- or plant-structure questions must connect back to productivity or environmental response.

Report:
- plant type
- recommended framework
- geometric or trait inputs
- soil or rhizosphere context
- validation plan
$ARGUMENTS
