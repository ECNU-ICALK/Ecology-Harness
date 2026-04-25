---
name: web-geospatial-3d-publishing
description: Plan browser, scientific, and geospatial publishing workflows for ecology 3D scenes, meshes, terrain products, and point clouds.
slug: web-geospatial-3d-publishing
triggers: [/web-geospatial-3d-publishing]
allowed-tools: [ListEcologyToolkits, ListMcpServersTool, DescribeEcologyToolkit, Read]
context: inline
---
Use this for publishing ecological 3D products to browsers, sharing terrain-aware scenes, or preparing large habitat and point-cloud datasets for scientific visualization and interactive review.

Preferred mapping:
1. `Potree` for lightweight browser review of large point clouds.
2. `CesiumJS` for geospatial 3D scenes that must stay aligned with terrain, imagery, or globe-based context.
3. `ParaView` for scientific 3D visualization of large ecological meshes, scalar fields, or gridded model outputs.
4. `QGIS MCP` and `Blender` when publication assets need geospatial cross-checking, annotation, or presentation rendering before release.

Report:
- target audience and delivery channel
- input geometry and spatial reference
- recommended publishing stack
- asset packaging and hosting plan
- QA and reproducibility notes
$ARGUMENTS
