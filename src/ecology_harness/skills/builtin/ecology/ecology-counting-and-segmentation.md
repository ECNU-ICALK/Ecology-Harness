---
name: ecology-counting-and-segmentation
description: Choose counting, detection, and segmentation tools for plants, tree crowns, wildlife imagery, and coverage estimation.
slug: ecology-counting-and-segmentation
triggers: [/ecology-counting-and-segmentation]
allowed-tools: [ListEcologyToolkits, ListEcologyFunctions, Read]
context: inline
---
Use this when the user needs counts, delineations, or object masks rather than just names.

Preferred mapping:
1. `PlantCV` for plant counting and phenotyping scenes.
2. `DeepForest` for airborne tree or bird detection.
3. `detectree2` when crown delineation matters.
4. `TreeCountSegHeight` for large-scale tree counting, crown segmentation, and height prediction.
5. `PyTorch-Wildlife` for wildlife image detection and classification.

Return:
- object type being counted
- likely best toolkit
- expected input modality
- likely output type
- compute or annotation constraints
$ARGUMENTS
