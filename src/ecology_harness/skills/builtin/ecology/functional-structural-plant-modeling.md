---
name: functional-structural-plant-modeling
description: Plan root-shoot architecture, organ development, and plant-form simulation workflows using functional-structural plant models.
slug: functional-structural-plant-modeling
triggers: [/functional-structural-plant-modeling]
allowed-tools: [ListEcologyToolkits, Read]
context: inline
---
Use this for canopy architecture, root-system structure, branching rules, rhizosphere geometry, or organ-level plant growth questions.

Preferred mapping:
1. `CPlantBox` for root architecture, plant-soil interaction, and 3D root-shoot geometry.
2. `OpenAlea L-Py` for L-system-based plant form, organogenesis, branching, and visualization.
3. `BioCro` or `pyrealm` when structure needs to connect to canopy physiology, productivity, or environmental response.
4. `PlantCV` when image-derived structure or phenotype measurements are needed to parameterize the model.

Report:
- structure or process of interest
- recommended framework
- key geometric or trait inputs
- spatial or temporal scale
- validation strategy
$ARGUMENTS
