---
name: plant-phenotyping-and-traits
description: Plan plant trait extraction, phenotyping, and herbarium measurement workflows using PlantCV, LeafMachine2, and related toolkits.
slug: plant-phenotyping-and-traits
triggers: [/plant-phenotyping-and-traits]
allowed-tools: [ListEcologyToolkits, ListEcologyFunctions, Read]
context: inline
---
Use this for leaf traits, morphology, phenotyping, herbarium measurements, or growth-stage questions.

Preferred mapping:
1. Use `PlantCV` for flexible plant phenotyping pipelines, segmentation, counting, and morphology.
2. Use `LeafMachine2` for herbarium-heavy workflows, archival components, and detailed leaf measurements.
3. If the user starts with only a field photo and needs the species first, chain to `species-photo-identification`.

Report:
- target trait or phenotype
- best toolkit
- likely input image requirements
- whether the task is lightweight screening or a full phenotyping pipeline
$ARGUMENTS
