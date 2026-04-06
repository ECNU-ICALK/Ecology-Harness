# Ecology Basic Tools

This document maps foundational ecology observation, laboratory workflow, and
bioreactor-analysis functions to the toolkits that are now installed natively or
cataloged in the repository.

## Function Map

| Function Cluster | Typical Needs | Installed Native Tools | Cataloged External Toolkits |
|---|---|---|---|
| Field observation and species ID | identify a plant from a photo, normalize names, inspect nearby observations | `INaturalistSearchTaxa`, `INaturalistSearchObservations`, `PlantNetIdentify`, `ListEcologyFunctions`, `ListEcologyToolkits` | `pyinaturalist`, `Pl@ntNet API`, `pybioclip`, `nature-id` |
| Plant phenotyping and traits | leaf traits, morphology, herbarium measurements, organ detection | `ListEcologyToolkits`, `DescribeEcologyToolkit` | `PlantCV`, `LeafMachine2` |
| Counting and density | plant counting, tree counting, wildlife counts, density estimates | `ListEcologyToolkits`, `DescribeEcologyToolkit` | `PlantCV`, `DeepForest`, `detectree2`, `TreeCountSegHeight`, `PyTorch-Wildlife` |
| Detection and segmentation | object detection, masks, crown delineation, image tiling | `ListEcologyToolkits`, `DescribeEcologyToolkit` | `DeepForest`, `detectree2`, `TreeCountSegHeight`, `PyTorch-Wildlife` |
| Camera-trap wildlife workflows | empty-image filtering, animal detection, species classification | `ListEcologyToolkits`, `DescribeEcologyToolkit` | `PyTorch-Wildlife` |
| Ecoacoustics | bird sound recognition, batch acoustic review | `ListEcologyToolkits`, `DescribeEcologyToolkit` | `BirdNET-Analyzer` |
| Closed algal systems and photobioreactors | sealed reactor design, pH and CO2 control, contamination review, growth curves, mass balance | `ListEcologyFunctions`, `ListEcologyToolkits`, `DescribeEcologyToolkit` | `Jupyter MCP Server`, `InfluxDB 3 MCP Server`, `LabArchives MCP Server`, `unit-converter-mcp`, `PyLabRobot`, `Opentrons` |
| Lab protocols, automation, and notebook workflows | SOP drafting, notebook capture, telemetry notebooks, liquid handling, unit harmonization | `ListEcologyFunctions`, `ListEcologyToolkits`, `DescribeEcologyToolkit` | `Jupyter MCP Server`, `LabArchives MCP Server`, `unit-converter-mcp`, `PyLabRobot`, `Opentrons` |
| Aquatic microcosms, plankton, and biofilms | grazer-prey microcosms, biofilm monitoring, water-column vs benthic tracking, community shifts | `ListEcologyFunctions`, `ListEcologyToolkits`, `DescribeEcologyToolkit` | `Jupyter MCP Server`, `InfluxDB 3 MCP Server`, `Fiji / ImageJ`, `CellProfiler`, `napari`, `ilastik`, `EcoTaxa Python Client`, `PlanktoScope` |
| Microscopy, automated classification, and fluorescence workflows | microscope-camera classification, object segmentation, fluorescence channels, multispectral image review | `ListEcologyFunctions`, `ListEcologyToolkits`, `DescribeEcologyToolkit` | `Fiji / ImageJ`, `PyImageJ`, `CellProfiler`, `napari`, `ilastik`, `scikit-image`, `EcoTaxa Python Client` |
| Molecular and assay-linked follow-up | PCR, amplicon workflows, microbial-community follow-up, total-carbon-linked lab assays | `ListEcologyFunctions`, `ListEcologyToolkits`, `DescribeEcologyToolkit` | `QIIME 2 / Rachis Framework`, `DADA2`, `Jupyter MCP Server`, `LabArchives MCP Server` |
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
- `Jupyter MCP Server`
  - Source: [datalayer/jupyter-mcp-server](https://github.com/datalayer/jupyter-mcp-server)
  - Why included: the strongest notebook-native MCP option for interactive analysis, cell execution, and reproducible telemetry workflows.
- `InfluxDB 3 MCP Server`
  - Source: [influxdata/influxdb3_mcp_server](https://github.com/influxdata/influxdb3_mcp_server)
  - Why included: practical time-series query and write layer for pH, temperature, dissolved oxygen, light, and other sensor logs.
- `LabArchives MCP Server`
  - Source: [SamuelBrudner/lab_archives_mcp](https://github.com/SamuelBrudner/lab_archives_mcp)
  - Why included: valuable ELN and provenance bridge for experiment logs, SOPs, findings, and analysis uploads.
- `unit-converter-mcp`
  - Source: [zazencodes/unit-converter-mcp](https://github.com/zazencodes/unit-converter-mcp)
  - Why included: very practical scientific conversion server for pressure, density, energy, temperature, and reactor-unit harmonization.
- `PyLabRobot`
  - Source: [PyLabRobot/pylabrobot](https://github.com/PyLabRobot/pylabrobot)
  - Why included: strong vendor-agnostic lab automation framework for media prep, dosing, transfers, and simulation.
- `Opentrons`
  - Source: [Opentrons/opentrons](https://github.com/Opentrons/opentrons)
  - Why included: official liquid-handling automation stack for OT-2 and Flex workflows.
- `Fiji / ImageJ`
  - Source: [fiji/fiji](https://github.com/fiji/fiji)
  - Why included: the most recognizable scientific image-analysis workstation for microscopy, fluorescence, and measurement workflows.
- `PyImageJ`
  - Source: [imagej/pyimagej](https://github.com/imagej/pyimagej)
  - Why included: strong bridge from ImageJ into reproducible Python and notebook workflows.
- `CellProfiler`
  - Source: [CellProfiler/CellProfiler](https://github.com/CellProfiler/CellProfiler)
  - Why included: mature segmentation and feature-extraction pipeline builder for microscopy images.
- `napari`
  - Source: [napari/napari](https://github.com/napari/napari)
  - Why included: very strong for manual review, annotation, multichannel fluorescence, and human-in-the-loop QA.
- `ilastik`
  - Source: [ilastik/ilastik](https://github.com/ilastik/ilastik)
  - Why included: practical interactive classification and segmentation without a heavy bespoke ML stack.
- `scikit-image`
  - Source: [scikit-image/scikit-image](https://github.com/scikit-image/scikit-image)
  - Why included: dependable Python backbone for custom image-processing and feature-extraction pipelines.
- `EcoTaxa Python Client`
  - Source: [ecotaxa/ecotaxa_py_client](https://github.com/ecotaxa/ecotaxa_py_client)
  - Why included: relevant bridge to a plankton-classification ecosystem and object-oriented plankton workflows.
- `PlanktoScope`
  - Source: [PlanktoScope/PlanktoScope](https://github.com/PlanktoScope/PlanktoScope)
  - Why included: open plankton imaging platform that complements offline image analysis with acquisition workflows.
- `QIIME 2 / Rachis Framework`
  - Source: [qiime2/qiime2](https://github.com/qiime2/qiime2)
  - Why included: strong provenance-aware framework for amplicon and microbiome follow-up after PCR or sequencing.
- `DADA2`
  - Source: [benjjneb/dada2](https://github.com/benjjneb/dada2)
  - Why included: widely used denoising workflow for sequence-level microbial-community analysis.

## Notes

- The native tools added in this pass are intentionally lightweight and network-first.
- Heavier toolkits and most MCP-backed lab servers remain cataloged rather than bundled, because they often require API credentials, hardware context, running notebook servers, lab automation hardware, databases, or larger dependency stacks.
- This split gives the harness something immediately usable now while preserving a clean path to deeper local-model, laboratory, and telemetry integrations later.
