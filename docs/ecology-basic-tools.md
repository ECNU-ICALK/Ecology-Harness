# Ecology Basic Tools

This document maps foundational ecology observation, laboratory workflow, and
bioreactor-analysis functions to the toolkits that are now installed natively or
cataloged in the repository.

## Function Map

| Function Cluster | Typical Needs | Installed Native Tools | Cataloged External Toolkits |
|---|---|---|---|
| Field observation and species ID | identify a plant from a photo, normalize names, inspect nearby observations | `INaturalistSearchTaxa`, `INaturalistSearchObservations`, `PlantNetIdentify`, `ListEcologyFunctions`, `ListEcologyToolkits` | `pyinaturalist`, `Pl@ntNet API`, `pybioclip`, `nature-id` |
| Plant phenotyping and traits | leaf traits, morphology, herbarium measurements, organ detection | `ListEcologyToolkits`, `DescribeEcologyToolkit` | `PlantCV`, `LeafMachine2`, `RhizoVision Explorer`, `RootPainter` |
| Root phenotyping and rhizosphere imaging | root crowns, washed roots, rhizoboxes, minirhizotron follow-up, root trait extraction | `ListEcologyFunctions`, `ListEcologyToolkits`, `DescribeEcologyToolkit` | `RhizoVision Explorer`, `RootPainter`, `OpenSimRoot` |
| Plant, crop, and growth simulation | crop phenology, irrigation, woody vegetation, root-shoot structure, microbial growth, biofilms, parameter estimation, scenario comparison | `ListEcologyFunctions`, `ListEcologyToolkits`, `DescribeEcologyToolkit` | `APSIM Next Generation`, `PCSE / WOFOST`, `AquaCrop-OSPy`, `BioCro`, `pyfao56`, `CPlantBox`, `OpenAlea L-Py`, `OpenSimRoot`, `r3PG`, `medfate`, `pyrealm`, `FATES`, `COBRApy`, `MICOM`, `COMETS`, `BacArena`, `Community Simulator`, `Tellurium`, `COPASI`, `PySCeS`, `NUFEB`, `Vivarium Core`, `MDSINE2`, `miaSim`, `pyPESTO`, `CarveMe`, `PyCoMo` |
| Traditional process models and ABM | agent-based ecology, watershed routing, trophic simulation, disturbance models, DGVM-style workflows | `ListEcologyFunctions`, `ListEcologyToolkits`, `DescribeEcologyToolkit` | `NetLogo`, `Mesa`, `GAMA Platform`, `DSSAT Cropping System Model`, `SWAT+`, `Ecopath with Ecosim`, `LPJ-GUESS`, `FATES`, `ED2`, `Biome-BGC`, `CENTURY / DayCent`, `RHESSys`, `LANDIS-II`, `Madingley Model`, `RangeShifter 2.0` |
| Lake, reservoir, and aquatic ecosystem modeling | stratification, oxygen, blooms, nutrient scenarios, water-quality and aquatic biogeochemistry | `ListEcologyFunctions`, `ListEcologyToolkits`, `DescribeEcologyToolkit` | `GLM`, `glm-py`, `FABM` |
| Counting and density | plant counting, tree counting, wildlife counts, density estimates | `ListEcologyToolkits`, `DescribeEcologyToolkit` | `PlantCV`, `DeepForest`, `detectree2`, `TreeCountSegHeight`, `PyTorch-Wildlife` |
| Detection and segmentation | object detection, masks, crown delineation, image tiling | `ListEcologyToolkits`, `DescribeEcologyToolkit` | `DeepForest`, `detectree2`, `TreeCountSegHeight`, `PyTorch-Wildlife` |
| Camera-trap wildlife workflows | empty-image filtering, animal detection, species classification | `ListEcologyToolkits`, `DescribeEcologyToolkit` | `PyTorch-Wildlife` |
| Animal behavior and pose tracking | movement trajectories, foraging, courtship, multi-animal interactions, markerless tracking | `ListEcologyFunctions`, `ListEcologyToolkits`, `DescribeEcologyToolkit` | `DeepLabCut`, `SLEAP`, `PyTorch-Wildlife` |
| Ecological 3D reconstruction and point clouds | drone photogrammetry, close-range survey photogrammetry, LiDAR preprocessing and simulation, tree QSM, habitat meshes, browser and geospatial 3D publishing | `ListEcologyFunctions`, `ListEcologyToolkits`, `DescribeEcologyToolkit`, `ListMcpServersTool` | `OpenDroneMap`, `WebODM`, `Meshroom`, `COLMAP`, `MicMac`, `PDAL`, `HELIOS++`, `CloudCompare`, `Open3D`, `TreeQSM`, `SimpleForest`, `PyVista`, `ParaView`, `Potree`, `CesiumJS`, `lidR`, `ForestTools`, `Blender`, `blender-mcp`, `qgis-mcp` |
| Ecoacoustics | bird sound recognition, batch acoustic review | `ListEcologyToolkits`, `DescribeEcologyToolkit` | `BirdNET-Analyzer` |
| Closed algal systems and photobioreactors | sealed reactor design, pH and CO2 control, contamination review, growth curves, mass balance | `ListEcologyFunctions`, `ListEcologyToolkits`, `DescribeEcologyToolkit` | `Jupyter MCP Server`, `InfluxDB 3 MCP Server`, `LabArchives MCP Server`, `unit-converter-mcp`, `PyLabRobot`, `Opentrons` |
| Lab protocols, automation, and notebook workflows | SOP drafting, notebook capture, telemetry notebooks, liquid handling, unit harmonization | `ListEcologyFunctions`, `ListEcologyToolkits`, `DescribeEcologyToolkit` | `Jupyter MCP Server`, `LabArchives MCP Server`, `unit-converter-mcp`, `PyLabRobot`, `Opentrons` |
| Aquatic microcosms, plankton, and biofilms | grazer-prey microcosms, biofilm monitoring, water-column vs benthic tracking, community shifts | `ListEcologyFunctions`, `ListEcologyToolkits`, `DescribeEcologyToolkit` | `Jupyter MCP Server`, `InfluxDB 3 MCP Server`, `Fiji / ImageJ`, `CellProfiler`, `napari`, `ilastik`, `EcoTaxa Python Client`, `PlanktoScope`, `MorphoCut`, `GLM`, `glm-py`, `FABM` |
| Microscopy, automated classification, and fluorescence workflows | microscope-camera classification, object segmentation, fluorescence channels, multispectral image review | `ListEcologyFunctions`, `ListEcologyToolkits`, `DescribeEcologyToolkit` | `Fiji / ImageJ`, `PyImageJ`, `CellProfiler`, `napari`, `ilastik`, `scikit-image`, `EcoTaxa Python Client`, `MorphoCut`, `RootPainter` |
| Molecular and assay-linked follow-up | PCR, amplicon workflows, microbial-community follow-up, total-carbon-linked lab assays | `ListEcologyFunctions`, `ListEcologyToolkits`, `DescribeEcologyToolkit` | `QIIME 2 / Rachis Framework`, `DADA2`, `mothur`, `VSEARCH`, `CarveMe`, `PyCoMo`, `Jupyter MCP Server`, `LabArchives MCP Server` |
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
- `RhizoVision Explorer`
  - Source: [noble-research-group/RhizoVisionExplorer](https://github.com/noble-research-group/RhizoVisionExplorer)
  - Why included: practical root-image analysis and belowground trait extraction toolkit.
- `RootPainter`
  - Source: [Abe404/root_painter](https://github.com/Abe404/root_painter)
  - Why included: useful corrective segmentation layer for difficult root and soil-background images.
- `APSIM Next Generation`
  - Source: [APSIMInitiative/ApsimX](https://github.com/APSIMInitiative/ApsimX)
  - Why included: strong agro-ecosystem framework for management, crop, and rotation scenarios.
- `PCSE / WOFOST`
  - Source: [ajwdewit/pcse](https://github.com/ajwdewit/pcse)
  - Why included: practical Python-first crop simulation environment for phenology, biomass, and yield studies.
- `AquaCrop-OSPy`
  - Source: [aquacropos/aquacrop](https://github.com/aquacropos/aquacrop)
  - Why included: strong fit for irrigation, drought, and water-limited crop growth.
- `BioCro`
  - Source: [biocro/biocro](https://github.com/biocro/biocro)
  - Why included: useful mechanistic crop-ecophysiology framework for canopy and photosynthesis-aware growth simulation.
- `pyfao56`
  - Source: [kthorp/pyfao56](https://github.com/kthorp/pyfao56)
  - Why included: practical ET and irrigation-accounting layer for crop water-balance workflows.
- `CPlantBox`
  - Source: [Plant-Root-Soil-Interactions-Modelling/CPlantBox](https://github.com/Plant-Root-Soil-Interactions-Modelling/CPlantBox)
  - Why included: high-value framework for 3D root-shoot architecture and plant-soil interactions.
- `OpenAlea L-Py`
  - Source: [openalea/lpy](https://github.com/openalea/lpy)
  - Why included: mature L-system plant-architecture environment for FSPM workflows.
- `OpenSimRoot`
  - Source: [OpenSimRoot project](https://rootsystemml.github.io/ISMCROOT/opensimroot/)
  - Why included: strong mechanistic root-system architecture simulator for belowground ecology and crop questions.
- `r3PG`
  - Source: [trotsiuk/r3PG](https://github.com/trotsiuk/r3PG)
  - Why included: practical forest and woody-plant productivity model for stands and plantations.
- `medfate`
  - Source: [emf-creaf/medfate](https://github.com/emf-creaf/medfate)
  - Why included: strong woody-vegetation package for drought, hydraulics, and stand water-balance questions.
- `pyrealm`
  - Source: [ImperialCollegeLondon/pyrealm](https://github.com/ImperialCollegeLondon/pyrealm)
  - Why included: useful bridge between environmental forcing, productivity, and ecophysiology.
- `FATES`
  - Source: [NGEET/fates](https://github.com/NGEET/fates)
  - Why included: useful vegetation-demography and disturbance layer between stand models and large-scale terrestrial biosphere models.
- `COBRApy`
  - Source: [opencobra/cobrapy](https://github.com/opencobra/cobrapy)
  - Why included: foundational metabolic-growth modeling framework for microbes.
- `MICOM`
  - Source: [micom-dev/micom](https://github.com/micom-dev/micom)
  - Why included: strong community-metabolism and cross-feeding layer for microbiome-style questions.
- `COMETS`
  - Source: [segrelab/comets](https://github.com/segrelab/comets)
  - Why included: valuable when microbial communities need spatial diffusion and metabolite exchange.
- `BacArena`
  - Source: [euba/BacArena](https://github.com/euba/BacArena)
  - Why included: combines microbial individuals and metabolic exchange in one community simulator.
- `Community Simulator`
  - Source: [Emergent-Behaviors-in-Biology/community-simulator](https://github.com/Emergent-Behaviors-in-Biology/community-simulator)
  - Why included: strong consumer-resource and assembly modeling layer for microbial ecology.
- `Tellurium`
  - Source: [sys-bio/tellurium](https://github.com/sys-bio/tellurium)
  - Why included: practical SBML and ODE environment for mechanistic growth dynamics.
- `COPASI`
  - Source: [copasi/COPASI](https://github.com/copasi/COPASI)
  - Why included: mature dynamic-systems platform with fitting and optimization support.
- `PySCeS`
  - Source: [PySCeS/pysces](https://github.com/PySCeS/pysces)
  - Why included: Python-native kinetic modeling option for mechanistic growth workflows.
- `NUFEB`
  - Source: [nufeb/NUFEB](https://github.com/nufeb/NUFEB)
  - Why included: strong individual-based microbial and biofilm simulator for reactor-style spatial systems.
- `Vivarium Core`
  - Source: [vivarium-collective/vivarium-core](https://github.com/vivarium-collective/vivarium-core)
  - Why included: flexible process-composition engine for custom microbial ecology workflows.
- `MDSINE2`
  - Source: [gerberlab/MDSINE2](https://github.com/gerberlab/MDSINE2)
  - Why included: useful when microbial-growth questions are driven by longitudinal time-series.
- `miaSim`
  - Source: [microbiome/miaSim](https://github.com/microbiome/miaSim)
  - Why included: useful benchmark and perturbation-simulation package for microbiome workflows.
- `pyPESTO`
  - Source: [ICB-DCM/pyPESTO](https://github.com/ICB-DCM/pyPESTO)
  - Why included: strong parameter-estimation and uncertainty layer for model calibration.
- `CarveMe`
  - Source: [cdanielmachado/carveme](https://github.com/cdanielmachado/carveme)
  - Why included: useful bridge from microbial genomic inputs into draft metabolic model reconstruction.
- `PyCoMo`
  - Source: [univieCUBE/PyCoMo](https://github.com/univieCUBE/PyCoMo)
  - Why included: good complement for community-scale metabolic modeling and cross-feeding analysis.
- `NetLogo`
  - Source: [NetLogo/NetLogo](https://github.com/NetLogo/NetLogo)
  - Why included: one of the most practical starting points for agent-based ecology and rule-based spatial simulations.
- `Mesa`
  - Source: [mesa/mesa](https://github.com/mesa/mesa)
  - Why included: Python-native ABM framework that integrates cleanly with notebooks and scientific Python workflows.
- `GAMA Platform`
  - Source: [gama-platform/gama](https://github.com/gama-platform/gama)
  - Why included: strong GIS-aware multi-agent platform for spatial ecology and social-ecological systems.
- `DSSAT Cropping System Model`
  - Source: [DSSAT/dssat-csm-os](https://github.com/DSSAT/dssat-csm-os)
  - Why included: classic crop-system model family with strong relevance for agricultural ecology and management scenarios.
- `SWAT+`
  - Source: [SWAT+ docs](https://swatplus.gitbook.io/docs/)
  - Why included: very practical watershed and water-quality model for land-use and management scenarios.
- `GLM`
  - Source: [AquaticEcoDynamics/GLM](https://github.com/AquaticEcoDynamics/GLM)
  - Why included: practical default entry point for lake and reservoir hydrodynamics and stratification modeling.
- `glm-py`
  - Source: [AquaticEcoDynamics/glm-py](https://github.com/AquaticEcoDynamics/glm-py)
  - Why included: Python-native orchestration layer for reproducible GLM workflows and notebook-driven scenario setup.
- `FABM`
  - Source: [fabm-model/fabm](https://github.com/fabm-model/fabm)
  - Why included: modular aquatic biogeochemistry framework for richer water-quality and ecosystem process coupling.
- `Ecopath with Ecosim`
  - Source: [Ecopath project](https://ecopath.org/)
  - Why included: mature default option for trophic and food-web simulation.
- `LPJ-GUESS`
  - Source: [LPJ-GUESS](https://web.nateko.lu.se/lpj-guess/index.html)
  - Why included: strong dynamic vegetation and terrestrial biosphere model for climate-response studies.
- `ED2`
  - Source: [EDmodel/ED2](https://github.com/EDmodel/ED2)
  - Why included: useful for ecosystem demography and vegetation-structure questions.
- `Biome-BGC`
  - Source: [Biome-BGC](https://carbonmodel.org/biome_bgc/)
  - Why included: classic process model for carbon-water-nitrogen and LAI-linked ecosystem response.
- `CENTURY / DayCent`
  - Source: [Colorado State Century project](https://www.nrel.colostate.edu/projects/century/)
  - Why included: classic plant-soil nutrient cycling model family with strong soil-carbon relevance.
- `RHESSys`
  - Source: [RHESSys/RHESSys](https://github.com/RHESSys/RHESSys)
  - Why included: strong ecohydrology option when hydrology and ecosystem response must stay coupled.
- `LANDIS-II`
  - Source: [LANDIS-II](https://www.landis-ii.org/home)
  - Why included: strong forest landscape and disturbance framework.
- `Madingley Model`
  - Source: [Madingley Model](https://madingley.github.io/)
  - Why included: useful general ecosystem model for multi-trophic and biodiversity-pattern questions.
- `RangeShifter 2.0`
  - Source: [RangeShifter 2.0](https://rangeshifter.github.io/software/rangeshifter2.0/)
  - Why included: strong fit for dispersal, range dynamics, and spatial eco-evolutionary scenarios.
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
- `DeepLabCut`
  - Source: [DeepLabCut/DeepLabCut](https://github.com/DeepLabCut/DeepLabCut)
  - Why included: strong markerless pose-estimation toolkit for behavior ecology and movement analysis.
- `SLEAP`
  - Source: [talmolab/sleap](https://github.com/talmolab/sleap)
  - Why included: valuable when multi-animal interactions and identity-aware pose tracking are central.
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
- `MorphoCut`
  - Source: [morphocut/morphocut](https://github.com/morphocut/morphocut)
  - Why included: practical Python pipeline layer for plankton and ecological image processing before classification.
- `QIIME 2 / Rachis Framework`
  - Source: [qiime2/qiime2](https://github.com/qiime2/qiime2)
  - Why included: strong provenance-aware framework for amplicon and microbiome follow-up after PCR or sequencing.
- `DADA2`
  - Source: [benjjneb/dada2](https://github.com/benjjneb/dada2)
  - Why included: widely used denoising workflow for sequence-level microbial-community analysis.
- `mothur`
  - Source: [mothur/mothur](https://github.com/mothur/mothur)
  - Why included: dependable amplicon-analysis platform for microbial ecology sequence processing and taxonomy workflows.
- `VSEARCH`
  - Source: [torognes/vsearch](https://github.com/torognes/vsearch)
  - Why included: transparent, open sequence-search and clustering tool widely used in metabarcoding pipelines.

## Notes

- The native tools added in this pass are intentionally lightweight and network-first.
- Heavier toolkits and most MCP-backed lab servers remain cataloged rather than bundled, because they often require API credentials, hardware context, running notebook servers, lab automation hardware, databases, or larger dependency stacks.
- This split gives the harness something immediately usable now while preserving a clean path to deeper local-model, laboratory, and telemetry integrations later.
