---
name: habitat-scene-3d-visualization
description: Plan 3D habitat, terrain, and mesh visualization workflows for ecological interpretation, communication, and review.
slug: habitat-scene-3d-visualization
triggers: [/habitat-scene-3d-visualization]
allowed-tools: [ListEcologyToolkits, ListMcpServersTool, DescribeEcologyToolkit, Read]
context: inline
---
Use this for 3D habitat scenes, terrain-aware ecological storytelling, interactive mesh or point-cloud review, and publication or outreach visuals built from ecology data.

Preferred mapping:
1. `PyVista` for Python-native mesh visualization, slicing, scalar overlays, and rapid 3D figure production from ecological surfaces or volumes.
2. `Potree` for web-based review of large point clouds and survey outputs that need lightweight browser sharing.
3. `Blender` plus `blender-mcp` for final habitat scenes, annotation, camera setup, animation, and high-quality ecological render output.
4. `QGIS MCP` when 3D scenes must stay aligned with terrain rasters, land-cover layers, site boundaries, or map products.

Report:
- scene or habitat type
- recommended visualization stack
- input geometry and attributes
- target output medium
- reproducibility and export plan
$ARGUMENTS
