# Aquatic Microcosm and Plankton Pack

This document records the freshwater microcosm, plankton, biofilm, fluorescence,
and assay-oriented skills and toolkit catalog additions for Ecology Harness.

## Installed Skills

- `aquatic-microcosm-foodweb-design`
  - purpose: enclosed freshwater food-web design across zooplankton, phytoplankton, benthic algae, and decomposers
- `zooplankton-grazing-and-plankton-dynamics`
  - purpose: grazing pressure, top-down control, prey selectivity, and community-shift interpretation
- `benthic-biofilm-and-periphyton-monitoring`
  - purpose: bottom-photo, attached algae, diatom, and biofilm-thickness workflows
- `water-quality-and-nutrient-panel`
  - purpose: continuous sensor and day-scale assay panel design for freshwater systems
- `plankton-microscopy-and-auto-classification`
  - purpose: microscope-camera pipelines, segmentation, classification, and review workflows
- `fluorescence-spectra-and-molecular-assays`
  - purpose: chlorophyll and phycocyanin fluorescence, multispectral signals, total carbon, PCR, and sequencing follow-up

## Related MCP Layers

These workflows primarily route through MCPs already added in the repository:

- `jupyter-mcp`
  - notebook-native analysis, visualization, and feature engineering
- `influxdb3`
  - sensor telemetry and time-series queries
- `labarchives`
  - experiment logging, provenance capture, and notebook integration
- `unit-converter`
  - harmonizing mixed units across sensors, assays, and literature

## Added External Toolkit Catalog Entries

- `Fiji / ImageJ`
- `PyImageJ`
- `CellProfiler`
- `napari`
- `ilastik`
- `scikit-image`
- `EcoTaxa Python Client`
- `PlanktoScope`
- `QIIME 2 / Rachis Framework`
- `DADA2`

## Why These Were Selected

- They map directly onto the user’s requested workflow families:
  - community composition from microscope-camera imagery
  - zooplankton, phytoplankton, and benthic-biofilm monitoring
  - fluorescence and spectral interpretation
  - water-quality telemetry and nutrient chemistry
  - PCR or amplicon-style microbial follow-up
- They are widely used or maintained in the scientific ecosystem and fit the project’s “catalog now, integrate deeper later” pattern.

## Notes

- This pass prioritized toolkit catalogs and workflow skills over adding weak third-party MCP wrappers for microscopy or plankton classification.
- The strongest immediately usable MCPs for this domain are still the notebook, telemetry, lab-record, and unit-conversion layers.
