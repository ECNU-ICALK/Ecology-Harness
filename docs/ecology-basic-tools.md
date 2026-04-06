# Ecology Basic Tools

This document maps foundational ecology observation and vision functions to the
toolkits that are now installed natively or cataloged in the repository.

## Function Map

| Function Cluster | Typical Needs | Installed Native Tools | Cataloged External Toolkits |
|---|---|---|---|
| Field observation and species ID | identify a plant from a photo, normalize names, inspect nearby observations | `INaturalistSearchTaxa`, `INaturalistSearchObservations`, `PlantNetIdentify`, `ListEcologyFunctions`, `ListEcologyToolkits` | `pyinaturalist`, `Pl@ntNet API`, `pybioclip`, `nature-id` |
| Plant phenotyping and traits | leaf traits, morphology, herbarium measurements, organ detection | `ListEcologyToolkits`, `DescribeEcologyToolkit` | `PlantCV`, `LeafMachine2` |
| Counting and density | plant counting, tree counting, wildlife counts, density estimates | `ListEcologyToolkits`, `DescribeEcologyToolkit` | `PlantCV`, `DeepForest`, `detectree2`, `TreeCountSegHeight`, `PyTorch-Wildlife` |
| Detection and segmentation | object detection, masks, crown delineation, image tiling | `ListEcologyToolkits`, `DescribeEcologyToolkit` | `DeepForest`, `detectree2`, `TreeCountSegHeight`, `PyTorch-Wildlife` |
| Camera-trap wildlife workflows | empty-image filtering, animal detection, species classification | `ListEcologyToolkits`, `DescribeEcologyToolkit` | `PyTorch-Wildlife` |
| Ecoacoustics | bird sound recognition, batch acoustic review | `ListEcologyToolkits`, `DescribeEcologyToolkit` | `BirdNET-Analyzer` |
| Workflow planning and QA | choose the right toolkit, compare capabilities, review constraints | `ListEcologyFunctions`, `ListEcologyToolkits`, `DescribeEcologyToolkit` | all cataloged toolkits |

## Installed Native Tools

- `INaturalistSearchTaxa`
  - Search taxa by scientific or common name and get rank plus observation context.
- `INaturalistSearchObservations`
  - Search iNaturalist observations with simple filters such as taxon name, place, and quality grade.
- `PlantNetIdentify`
  - Identify plants from local images using Pl@ntNet.
  - Requires `PLANTNET_API_KEY`.
- `ListEcologyFunctions`
  - Show the function tree so the model can reason about which workflow family fits a task.
- `ListEcologyToolkits`
  - Show cataloged external toolkits by capability or modality.
- `DescribeEcologyToolkit`
  - Show install guidance, repo, and fit notes for one toolkit.

## Cataloged External Toolkits

- `pyinaturalist`
  - Source: [pyinat/pyinaturalist](https://github.com/pyinat/pyinaturalist)
  - Why included: actively maintained Python client for the iNaturalist API, useful for taxa, observations, and species counts.
- `Pl@ntNet API`
  - Source: [plantnet/my.plantnet](https://github.com/plantnet/my.plantnet)
  - Why included: practical plant identification API with local-image POST support and organ hints.
- `pybioclip`
  - Source: [Imageomics/pybioclip](https://github.com/Imageomics/pybioclip)
  - Why included: BioCLIP-family inference with a CLI and Python package.
- `nature-id`
  - Source: [joergmlpts/nature-id](https://github.com/joergmlpts/nature-id)
  - Why included: lightweight command-line species ID for plants, birds, and insects with higher-taxon fallback.
- `PlantCV`
  - Source: [danforthcenter/plantcv](https://github.com/danforthcenter/plantcv)
  - Why included: one of the strongest open-source plant phenotyping toolkits.
- `LeafMachine2`
  - Source: [Gene-Weaver/LeafMachine2](https://github.com/Gene-Weaver/LeafMachine2)
  - Why included: strong herbarium and leaf-measurement workflow.
- `DeepForest`
  - Source: [weecology/DeepForest](https://github.com/weecology/DeepForest)
  - Why included: practical ecological object detection in airborne imagery with tree crown and bird models.
- `detectree2`
  - Source: [PatBall1/detectree2](https://github.com/PatBall1/detectree2)
  - Why included: strong tree-crown delineation workflow.
- `TreeCountSegHeight`
  - Source: [sizhuoli/TreeCountSegHeight](https://github.com/sizhuoli/TreeCountSegHeight)
  - Why included: large-scale counting, segmentation, and height prediction.
- `PyTorch-Wildlife`
  - Source: [microsoft/CameraTraps](https://github.com/microsoft/CameraTraps)
  - Why included: strong camera-trap detection and classification platform around MegaDetector and related models.
- `BirdNET-Analyzer`
  - Source: [birdnet-team/BirdNET-Analyzer](https://github.com/birdnet-team/BirdNET-Analyzer)
  - Why included: strong ecoacoustic option for bird sound recognition.

## Notes

- The native tools added in this pass are intentionally lightweight and network-first.
- The heavier toolkits remain cataloged rather than bundled, because many require GPU, CUDA, large model weights, or specialized geospatial dependencies.
- This split gives the harness something immediately usable now while preserving a clean path to deeper local-model integrations later.
