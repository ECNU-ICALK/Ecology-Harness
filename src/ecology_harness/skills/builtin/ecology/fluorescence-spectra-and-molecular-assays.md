---
name: fluorescence-spectra-and-molecular-assays
description: Interpret chlorophyll or phycocyanin fluorescence, multispectral absorption, and day-scale assay outputs such as total carbon and PCR-based measurements.
slug: fluorescence-spectra-and-molecular-assays
triggers: [/fluorescence-spectra-and-molecular-assays]
allowed-tools: [Skill, SkillRead, ListEcologyToolkits, DescribeEcologyToolkit, ListMcpServersTool, ListMcpToolsTool, WebSearch, WebFetch, Read]
context: inline
---
Use this when fluorescence, spectral signals, and laboratory assays must be interpreted together in an aquatic ecological system.

Preferred workflow:
1. Separate the signal families: chlorophyll fluorescence, phycocyanin fluorescence, absorption or multispectral channels, bottom-image metrics, and sampled assays such as total carbon or PCR.
2. Clarify temporal resolution differences between high-frequency sensors and day-scale assay data.
3. Use `jupyter-mcp` and `influxdb3` when fluorescence or spectral logs must be aligned with environmental telemetry.
4. Use `DescribeEcologyToolkit` for `fiji-imagej`, `pyimagej`, `cellprofiler`, `napari`, or `scikit-image` when bottom-photo or multichannel image extraction is needed.
5. Use `qiime2-rachis`, `dada2`, `ncbi-datasets`, and `bio-blast` when PCR or sequencing follow-up enters the workflow.
6. Use `literature-multi-source-search` when fluorescence proxies or assay interpretation need method benchmarks.

Return:
- signal families and what each can and cannot infer
- alignment strategy across different time resolutions
- recommended image or spectral analysis toolkit
- strongest molecular follow-up route if PCR or sequencing is involved
- highest risk of over-interpreting proxy signals

$ARGUMENTS
