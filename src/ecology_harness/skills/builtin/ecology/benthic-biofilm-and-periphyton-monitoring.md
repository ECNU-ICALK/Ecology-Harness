---
name: benthic-biofilm-and-periphyton-monitoring
description: Monitor diatoms, filamentous algae, attached biofilms, and benthic-pelagic coupling using bottom photos, microscopy, and thickness or cover metrics.
slug: benthic-biofilm-and-periphyton-monitoring
triggers: [/benthic-biofilm-and-periphyton-monitoring]
allowed-tools: [Skill, SkillRead, ListEcologyToolkits, DescribeEcologyToolkit, ListMcpServersTool, ListMcpToolsTool, WebSearch, WebFetch, Read]
context: inline
---
Use this for attached diatom and filamentous-algae systems, settling dynamics, periphyton development, wall growth, or bottom-surface biofilm monitoring.

Preferred workflow:
1. Define the attached compartment: reactor floor, slide, tile, wall, sediment surface, or removable coupon.
2. Separate measurements into cover, thickness, texture, species composition, fluorescence, and detachment events.
3. Use `DescribeEcologyToolkit` for `fiji-imagej`, `pyimagej`, `cellprofiler`, `napari`, `ilastik`, or `scikit-image` depending on whether the work is manual review, segmentation, or batch extraction.
4. Use `jupyter-mcp` when bottom-photo summaries, thickness time series, or image-derived metrics must be analyzed with environmental logs.
5. Use `labarchives` when annotated images, protocols, and sampling notes should be stored with provenance.

Return:
- attached surface and monitoring design
- recommended image and thickness metrics
- best toolkit choice for the image-analysis step
- likely failure modes such as detachment, shadowing, or uneven illumination
- strongest next QC or replication step

$ARGUMENTS
