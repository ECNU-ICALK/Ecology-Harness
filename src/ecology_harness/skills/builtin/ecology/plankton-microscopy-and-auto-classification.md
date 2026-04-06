---
name: plankton-microscopy-and-auto-classification
description: Plan microscope-camera workflows for community composition, automated species grouping, and object-level review across plankton and biofilm imagery.
slug: plankton-microscopy-and-auto-classification
triggers: [/plankton-microscopy-and-auto-classification]
allowed-tools: [Skill, SkillRead, ListEcologyToolkits, DescribeEcologyToolkit, ListMcpServersTool, ListMcpToolsTool, WebSearch, WebFetch, Read]
context: inline
---
Use this for microscope-image pipelines where community composition, automated species grouping, or object-level segmentation is needed.

Preferred workflow:
1. Clarify the imaging mode: brightfield, phase contrast, fluorescence, or multispectral microscopy.
2. Define the targets: zooplankton, phytoplankton colonies, benthic diatoms, filamentous algae, bacteria, or mixed objects.
3. Use `DescribeEcologyToolkit` for:
   - `cellprofiler`, `scikit-image`, or `pyimagej` for scripted batch pipelines
   - `napari` for manual review and annotation
   - `ilastik` for interactive pixel or object classification
   - `ecotaxa-py-client` and `planktoscope` for plankton-oriented imaging and classification workflows
4. Use `jupyter-mcp` when image-derived features need to be merged with telemetry or assay tables.
5. Use `labarchives` when microscopy runs, annotations, and classifier decisions should be archived.

Return:
- imaging mode and target objects
- recommended segmentation or classification path
- best toolkit by workflow style
- where human review is still required
- strongest next annotation or validation step

$ARGUMENTS
