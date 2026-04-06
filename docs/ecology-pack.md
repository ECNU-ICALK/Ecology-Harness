# Ecology Pack Sources

This document records the upstream repositories used to build the first
agriculture, environment, and ecology pack for Ecology Harness.

## Installed Skill Bundles

- `semantic-scholar-skills`
  - repo: https://github.com/zongmin-yu/semantic-scholar-skills
  - installed bundles:
    - `expand-references`
    - `trace-citations`
    - `paper-triage`
  - why selected:
    - self-contained skill bundles
    - literature workflows that fit environment and ecology review work
    - optional MCP server from the same codebase

- `mapbox-agent-skills`
  - repo: https://github.com/mapbox/mapbox-agent-skills
  - installed bundles:
    - `mapbox-geospatial-operations`
    - `mapbox-cartography`
    - `mapbox-data-visualization-patterns`
  - why selected:
    - official Mapbox repository
    - practical geospatial reasoning patterns for screening and mapping workflows
    - lightweight markdown-first bundles with reference files

- `open-meteo-mcp`
  - repo: https://github.com/cmer81/open-meteo-mcp
  - installed bundles:
    - `open-meteo`
    - `open-meteo-advanced`
  - why selected:
    - actively maintained and comprehensive Open-Meteo server
    - includes ready-made skills for everyday weather and advanced climate/model workflows
    - strong fit for ecology, agriculture, air-quality, flood, and climate-risk questions

## Installed Domain-Focused Skills

- closed algae and photobioreactor skills
  - local skill set:
    - `closed-algae-system-design`
    - `photobioreactor-environment-control`
    - `microalgae-strain-and-inoculation`
    - `algal-monitoring-plan`
    - `photobioreactor-troubleshooting`
    - `algal-timeseries-and-mass-balance`
  - informed by:
    - https://github.com/K-Dense-AI/claude-scientific-skills
  - why selected:
    - directly matches sealed algal cultivation and benchtop photobioreactor workflows
    - bridges literature, chemistry, telemetry, notebook analysis, and lab records
    - gives the harness a practical experimental-systems layer instead of only field or geospatial ecology

- freshwater microcosm and plankton-monitoring skills
  - local skill set:
    - `aquatic-microcosm-foodweb-design`
    - `zooplankton-grazing-and-plankton-dynamics`
    - `benthic-biofilm-and-periphyton-monitoring`
    - `water-quality-and-nutrient-panel`
    - `plankton-microscopy-and-auto-classification`
    - `fluorescence-spectra-and-molecular-assays`
  - why selected:
    - directly matches plankton-biofilm-bacteria freshwater microcosm studies
    - connects water-quality telemetry with microscopy, fluorescence, and assay follow-up
    - gives the harness stronger support for community-composition and monitoring workflows

- plant, crop, and microbial growth-simulation skills
  - local skill set:
    - `plant-growth-model-selection`
    - `crop-growth-simulation-workflow`
    - `crop-water-and-irrigation-simulation`
    - `functional-structural-plant-modeling`
    - `root-and-rhizosphere-architecture-modeling`
    - `woody-plant-and-forest-simulation`
    - `microbial-growth-and-community-simulation`
    - `microbial-community-metabolism-simulation`
    - `microbial-biofilm-and-reactor-simulation`
    - `microbiome-timeseries-and-benchmark-simulation`
    - `plant-soil-microbe-coupled-simulation`
    - `growth-model-calibration-and-validation`
  - why selected:
    - fills a common gap between ecology observation workflows and mechanistic simulation work
    - gives the harness a clean entry point for annual crops, irrigation, woody plants, plant architecture, microbial dynamics, and calibration workflows
    - pairs naturally with the existing Jupyter, LabArchives, and unit-conversion MCP stack

## Additional Toolkit Layer For Plant Types And Microbes

- plant-type-specific additions
  - `BioCro`
  - `pyfao56`
  - `r3PG`
  - `medfate`
  - why selected:
    - improves coverage for annual crops, canopy physiology, irrigation accounting, forests, and woody plants
    - complements rather than replaces `APSIM`, `WOFOST`, `AquaCrop`, `CPlantBox`, and `pyrealm`

- microbial ecology additions
  - `COMETS`
  - `BacArena`
  - `Community Simulator`
  - `NUFEB`
  - `Vivarium Core`
  - `miaSim`
  - why selected:
    - covers community metabolism, resource competition, biofilms, spatial diffusion, and longitudinal microbiome benchmarks
    - extends the earlier `COBRApy`, `MICOM`, `Tellurium`, and `MDSINE2` layer into richer microbial-ecology workflows

- traditional ecological process-model and ABM skills
  - local skill set:
    - `process-model-selection`
    - `agent-based-ecology-modeling`
    - `watershed-and-ecohydrology-modeling`
    - `food-web-and-trophic-simulation`
    - `forest-landscape-disturbance-modeling`
    - `terrestrial-biosphere-and-vegetation-modeling`
    - `model-calibration-and-sensitivity`
    - `cross-model-scenario-comparison`
  - why selected:
    - moves the harness beyond literature and data review into model-family selection for traditional ecological simulators
    - creates a clean surface for future runner tools such as `RunNetLogoModel` or `RunSWATPlusProject`
    - keeps heavy compiled systems in the toolkit layer while still making them discoverable now

## Installed MCP Catalog Entries

- `mapbox`
  - repo: https://github.com/mapbox/mcp-server
  - rationale: official hosted and npm-backed geospatial MCP server

- `baidu-maps`
  - repo: https://github.com/baidu-maps/mcp
  - rationale: official China-focused mapping MCP server with strong local relevance

- `weather-open-meteo`
  - repo: https://github.com/cmer81/open-meteo-mcp
  - rationale: broader Open-Meteo coverage including archive, air quality, marine, flood, ensemble, seasonal, and climate-projection endpoints

- `nasa`
  - repo: https://github.com/ProgramComputer/NASA-MCP-server
  - rationale: useful Earth-observation, hazard, wildfire, and POWER endpoints

- `eosc-data-commons`
  - repo: https://github.com/EOSC-Data-Commons/data-commons-mcp
  - rationale: dataset discovery for open-access research assets

- `semantic-scholar`
  - repo: https://github.com/zongmin-yu/semantic-scholar-skills
  - rationale: literature MCP entry paired with the installed research skills

- `gis-mcp`
  - repo: https://github.com/mahdin75/gis-mcp
  - rationale: broad geospatial analysis server with climate, biodiversity, land-cover, and raster workflows

- `scientific-papers`
  - repo: https://github.com/benedict2310/Scientific-Papers-MCP
  - rationale: broad literature coverage across arXiv, OpenAlex, PMC, Europe PMC, bioRxiv, and CORE

- `simple-pubmed`
  - repo: https://github.com/andybrandt/mcp-simple-pubmed
  - rationale: well-scoped PubMed/PMC search and full-text retrieval server for life-science evidence workflows

- `crossref`
  - repo: https://github.com/BotanicaStudios/crossref-mcp
  - rationale: lightweight DOI metadata lookup for literature cleanup and citation normalization

- `unpaywall`
  - repo: https://github.com/ElliotPadfield/unpaywall-mcp
  - rationale: open-access fulltext discovery and PDF-text extraction for paper follow-up

- `dataverse`
  - repo: https://github.com/gdcc/mcp-dataverse
  - rationale: research-data repository search and DOI-to-Croissant conversion

- `noaa-tides-currents`
  - repo: https://github.com/RyanCardin15/NOAA-Tides-And-Currents-MCP
  - rationale: strong coastal and marine-adjacent coverage for tides, currents, sea level, and flooding

- `swiss-environment`
  - repo: https://github.com/malkreide/swiss-environment-mcp
  - rationale: high-quality public environmental data server with air, hydrology, hazards, and wildfire tools

- `wsl-envidat`
  - repo: https://github.com/malkreide/wsl-envidat-mcp
  - rationale: strong Swiss research-data source for forest, biodiversity, avalanche, and natural-hazard datasets

- `gbif`
  - repo: https://github.com/tyson-swetnam/gbif-mcp
  - rationale: excellent fit for biodiversity occurrences, taxonomy, dataset discovery, and literature citing GBIF-mediated datasets

- `stac`
  - repo: https://github.com/BnJam/stac-mcp
  - rationale: high-value Earth-observation catalog discovery layer for remote sensing, land cover, and item or asset selection

- `openalex-research`
  - repo: https://github.com/oksure/openalex-research-mcp
  - rationale: strong literature-review and scholarly-landscape server with citation, expert, venue, and trend tools

- `ncbi-datasets`
  - repo: https://github.com/Augmented-Nature/NCBI-Datasets-MCP-Server
  - rationale: useful for microbial ecology, taxonomy, conservation genetics, and genome-aware ecology workflows

- `bio-blast`
  - repo: https://github.com/bio-mcp/bio-mcp-blast
  - rationale: practical bridge for sequence-similarity workflows in microbial ecology, marker validation, and genetics-adjacent tasks

- `pubchem`
  - repo: https://github.com/Augmented-Nature/PubChem-MCP-Server
  - rationale: useful for pollutant identity, chemical fate, toxicity, and environmental-chemistry workflows

- `jupyter-mcp`
  - repo: https://github.com/datalayer/jupyter-mcp-server
  - rationale: notebook-native analysis for telemetry review, calculations, plots, and experiment notebooks

- `influxdb3`
  - repo: https://github.com/influxdata/influxdb3_mcp_server
  - rationale: strong time-series database bridge for instrumented culture systems and reactor monitoring

- `labarchives`
  - repo: https://github.com/SamuelBrudner/lab_archives_mcp
  - rationale: practical ELN and provenance layer for recording experiments, SOPs, and corrective actions

- `unit-converter`
  - repo: https://github.com/zazencodes/unit-converter-mcp
  - rationale: compact but highly useful scientific conversion layer for temperature, pressure, density, power, and reactor-unit reconciliation

## Candidate Backlog

These looked promising during the expanded search but were not installed as
default catalog entries yet:

- `paperclip`
  - repo: https://github.com/matsjfunke/paperclip
  - why not default yet:
    - strong ecology-adjacent literature coverage through EarthArXiv, EcoEvoRxiv, MarXiv, and AgriXiv
    - the repository shows as archived on December 16, 2025, and the recommended path is still self-hosting a remote endpoint, so it is no longer a strong default install target

- agriculture-specific public-data MCPs such as FAOSTAT or USDA/NASS wrappers
  - why not default yet:
    - I did not find equally clear, maintained, install-ready MCP servers in this pass
    - these may be better added later as first-party native tools or adapters rather than copied from weaker third-party wrappers

- plant-growth-specific MCP servers
  - why not default yet:
    - I did not find equally mature, broadly reusable MCP servers for crop or plant-growth simulation that clearly beat direct use of existing model frameworks
    - the stronger current pattern is to catalog the simulation frameworks themselves and execute them through `jupyter-mcp` plus notebook or lab-record tooling

- model-specific MCP servers for traditional ecological simulators
  - why not default yet:
    - I did not find broadly reused MCP servers for NetLogo, DSSAT, SWAT+, EwE, LANDIS-II, or LPJ-GUESS that were mature enough to treat as high-quality defaults
    - the better near-term path is to add model runners or container adapters around the official systems while keeping the MCP spine focused on notebooks, provenance, and data handling

## Notes

- In the current Ecology Harness build, remote MCP transports are cataloged and
  discoverable, but only in-process MCP servers execute end-to-end.
- The catalog is still worth installing now because it lets the harness expose a
  stable ecology source inventory and keeps later transport support
  configuration-compatible.
- This pass intentionally prioritized sources that are either actively maintained
  or clearly useful to research workflows. I avoided turning weak or stale
  wrappers into default installs just to increase counts.
