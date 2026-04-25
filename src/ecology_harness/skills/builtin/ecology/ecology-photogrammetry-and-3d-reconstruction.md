---
name: ecology-photogrammetry-and-3d-reconstruction
description: Plan drone, close-range, and plot-scale photogrammetry workflows for ecological 3D reconstruction, textured meshes, orthomosaics, and surface models.
slug: ecology-photogrammetry-and-3d-reconstruction
triggers: [/ecology-photogrammetry-and-3d-reconstruction]
allowed-tools: [ListEcologyToolkits, ListMcpServersTool, DescribeEcologyToolkit, Read]
context: inline
---
Use this for UAV photogrammetry, plot-scale 3D reconstruction, habitat meshes, coral or vegetation structure models, or repeatable drone-to-surface-model workflows.

Preferred mapping:
1. `OpenDroneMap` or `WebODM` for georeferenced orthomosaics, DEMs, textured meshes, and drone-image processing at ecology project scale.
2. `Meshroom` for close-range photogrammetry, object or quadrat reconstruction, and node-based 3D processing when georeferencing is secondary.
3. `Blender` plus `blender-mcp` when mesh cleanup, scene annotation, habitat mockups, or presentation-quality renders are required.
4. `QGIS MCP` when reconstructed products must be checked against rasters, vectors, terrain, or project CRS inside a geospatial workflow.

Report:
- acquisition context
- recommended reconstruction stack
- expected outputs
- georeferencing or scaling method
- quality-control checkpoints
$ARGUMENTS
