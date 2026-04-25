---
name: close-range-ecology-photogrammetry
description: Plan close-range, plot-scale, and measurement-oriented ecological photogrammetry with COLMAP and MicMac for quadrats, corals, roots, branches, and specimen-scale reconstruction.
slug: close-range-ecology-photogrammetry
triggers: [/close-range-ecology-photogrammetry]
allowed-tools: [ListEcologyToolkits, ListMcpServersTool, DescribeEcologyToolkit, Read]
context: inline
---
Use this for specimen, quadrat, coral, root, branch, stem, or object-scale photogrammetry when image geometry, scaling, and reconstruction fidelity matter more than large-area drone mapping.

Preferred mapping:
1. `COLMAP` for research-grade structure-from-motion, camera-pose estimation, and scripted reconstruction workflows.
2. `MicMac` when survey rigor, control points, georeferencing discipline, or measurement-oriented photogrammetry matter more than interface simplicity.
3. `Meshroom` when a visual node workflow is preferable for exploratory or teaching-oriented reconstruction.
4. `Blender` plus `blender-mcp` when reconstructed meshes need cleanup, annotation, or downstream figure production.

Report:
- target organism or object scale
- recommended reconstruction stack
- scaling or control-point strategy
- expected dense outputs and QA checks
- downstream export plan
$ARGUMENTS
