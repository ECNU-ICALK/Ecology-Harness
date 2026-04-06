# Plant Growth Simulation Pack

This note records the plant, crop, and microbial growth-simulation layer now
cataloged inside Ecology Harness.

## Installed Skills

- `plant-growth-model-selection`
  - purpose: choose the right modeling family before committing to implementation
- `crop-growth-simulation-workflow`
  - purpose: crop phenology, irrigation, yield, and agro-ecosystem scenario selection
- `crop-water-and-irrigation-simulation`
  - purpose: water balance, evapotranspiration, irrigation, and drought workflow selection
- `functional-structural-plant-modeling`
  - purpose: root-shoot architecture, branching, organ development, and FSPM workflows
- `root-and-rhizosphere-architecture-modeling`
  - purpose: explicit root-system geometry, rhizosphere context, and root-informed parameterization
- `woody-plant-and-forest-simulation`
  - purpose: forest, shrubland, plantation, and woody-plant drought-response workflow selection
- `microbial-growth-and-community-simulation`
  - purpose: microbial growth, community metabolism, and mechanistic reactor dynamics
- `microbial-community-metabolism-simulation`
  - purpose: choose between metabolic, assembly, and cross-feeding simulators for microbial consortia
- `microbial-biofilm-and-reactor-simulation`
  - purpose: biofilm, diffusion, reactor, and custom multi-process microbial simulation
- `microbiome-timeseries-and-benchmark-simulation`
  - purpose: longitudinal microbiome inference and benchmark-data generation
- `plant-soil-microbe-coupled-simulation`
  - purpose: coupled plant, soil, nutrient, and microbial simulation design
- `growth-model-calibration-and-validation`
  - purpose: parameter estimation, sensitivity, uncertainty, and validation planning

## Cataloged Toolkits

- `APSIM Next Generation`
  - repo: https://github.com/APSIMInitiative/ApsimX
  - rationale: strong agro-ecosystem framework for crop, management, and rotation scenarios
- `PCSE / WOFOST`
  - repo: https://github.com/ajwdewit/pcse
  - rationale: Python-first crop simulation environment with WOFOST-style workflows
- `AquaCrop-OSPy`
  - repo: https://github.com/aquacropos/aquacrop
  - rationale: very practical choice for irrigation, drought, and water-limited crop growth
- `BioCro`
  - repo: https://github.com/biocro/biocro
  - rationale: strong mechanistic crop-ecophysiology option for canopy photosynthesis and physiology-aware growth work
- `pyfao56`
  - repo: https://github.com/kthorp/pyfao56
  - rationale: lightweight FAO-56 water-balance and irrigation workflow for crop-water questions
- `CPlantBox`
  - repo: https://github.com/Plant-Root-Soil-Interactions-Modelling/CPlantBox
  - rationale: high-value framework for 3D root-shoot architecture and plant-soil interactions
- `OpenAlea L-Py`
  - repo: https://github.com/openalea/lpy
  - rationale: mature L-system environment for generative plant architecture and FSPM workflows
- `r3PG`
  - repo: https://github.com/trotsiuk/r3PG
  - rationale: strong forest and woody-plant productivity model for stand and plantation questions
- `medfate`
  - repo: https://github.com/emf-creaf/medfate
  - rationale: valuable woody-vegetation and forest-hydraulics package for drought and stand water-balance studies
- `pyrealm`
  - repo: https://github.com/ImperialCollegeLondon/pyrealm
  - rationale: good bridge between environmental forcing, productivity, and ecophysiology
- `COBRApy`
  - repo: https://github.com/opencobra/cobrapy
  - rationale: foundational metabolic-growth modeling framework for microbes
- `MICOM`
  - repo: https://github.com/micom-dev/micom
  - rationale: strong community-metabolism and cross-feeding layer for microbiome-style questions
- `COMETS`
  - repo: https://github.com/segrelab/comets
  - rationale: high-value community-metabolism framework when diffusion and spatial metabolite exchange matter
- `BacArena`
  - repo: https://github.com/euba/BacArena
  - rationale: useful when microbial individuals and metabolic exchange both need to stay explicit
- `Community Simulator`
  - repo: https://github.com/Emergent-Behaviors-in-Biology/community-simulator
  - rationale: strong consumer-resource and community-assembly framework for microbial ecology
- `Tellurium`
  - repo: https://github.com/sys-bio/tellurium
  - rationale: practical SBML and ODE environment for mechanistic growth dynamics
- `COPASI`
  - repo: https://github.com/copasi/COPASI
  - rationale: mature dynamic-systems platform with optimization and fitting support
- `PySCeS`
  - repo: https://github.com/PySCeS/pysces
  - rationale: Python-native kinetic modeling option for pathway and growth dynamics
- `NUFEB`
  - repo: https://github.com/nufeb/NUFEB
  - rationale: strong individual-based and biofilm-oriented microbial simulator for spatial reactor systems
- `Vivarium Core`
  - repo: https://github.com/vivarium-collective/vivarium-core
  - rationale: composable process-simulation engine for custom microbial physiology or hybrid ecosystem workflows
- `MDSINE2`
  - repo: https://github.com/gerberlab/MDSINE2
  - rationale: useful when microbial-growth questions are driven by longitudinal time-series
- `miaSim`
  - repo: https://github.com/microbiome/miaSim
  - rationale: useful for generating benchmark microbiome count data and perturbation scenarios
- `pyPESTO`
  - repo: https://github.com/ICB-DCM/pyPESTO
  - rationale: strong parameter-estimation and uncertainty layer for model calibration

## By Plant Type

- annual and row crops
  - best fit: `AquaCrop-OSPy`, `PCSE / WOFOST`, `BioCro`, `APSIM Next Generation`, `DSSAT Cropping System Model`
  - use when: phenology, yield, canopy physiology, irrigation, sowing-date, and management scenarios are central

- irrigation and water-balance focused workflows
  - best fit: `pyfao56`, `AquaCrop-OSPy`
  - use when: evapotranspiration, irrigation scheduling, deficit stress, and soil-water accounting are the main questions

- roots, rhizosphere, and structural plant models
  - best fit: `CPlantBox`, `OpenAlea L-Py`
  - use when: explicit root architecture, branching, 3D geometry, and rhizosphere structure matter

- woody plants, plantations, forests, and shrublands
  - best fit: `r3PG`, `medfate`, `ED2`, `LPJ-GUESS`, `LANDIS-II`
  - use when: tree growth, stand dynamics, woody drought stress, vegetation structure, or long-term forest response are the target

## Microbial Simulation Families

- community metabolism and cross-feeding
  - best fit: `MICOM`, `COMETS`, `BacArena`, `COBRApy`

- ecological assembly and resource competition
  - best fit: `Community Simulator`

- biofilms, reactors, and spatial gradients
  - best fit: `NUFEB`, `Tellurium`, `COPASI`, `PySCeS`, `Vivarium Core`

- longitudinal microbiome dynamics and benchmarking
  - best fit: `MDSINE2`, `miaSim`, `pyPESTO`

## MCP Strategy

I did not find equally strong, mature, plant-growth-specific MCP servers that
were clearly better than the frameworks above. For now, the recommended MCP
execution spine for growth simulation work is:

- `jupyter-mcp` for notebook execution and plotting
- `labarchives` for experiment logs, provenance, and notebook-linked records
- `unit-converter` for harmonizing units before model fitting or scenario comparison
- `weather-open-meteo` and `nasa` when forcing data or climate scenarios are needed

## Example Prompts

```text
/plant-growth-model-selection maize drought simulation with irrigation treatments
/crop-growth-simulation-workflow rice yield under heat stress and delayed sowing
/crop-water-and-irrigation-simulation deficit irrigation and ET accounting for maize
/functional-structural-plant-modeling root architecture under phosphorus limitation
/root-and-rhizosphere-architecture-modeling soil-column root branching under compaction
/woody-plant-and-forest-simulation plantation productivity and drought mortality risk
/microbial-growth-and-community-simulation rhizosphere consortium cross-feeding under carbon pulses
/microbial-community-metabolism-simulation diffusion-limited cross-feeding in a microbial consortium
/microbial-biofilm-and-reactor-simulation biofilm development under pulsed nutrient inflow
/microbiome-timeseries-and-benchmark-simulation perturbation benchmarks for longitudinal microbiome data
/plant-soil-microbe-coupled-simulation crop roots soil water and nitrifier coupling in pots
/growth-model-calibration-and-validation fit growth and yield parameters from multi-season field data
```
