# Ecology 3D Modeling Pack

This pack adds a lightweight but high-value 3D ecology layer to Ecology
Harness. It is aimed at reconstruction, point-cloud processing, canopy and
terrain review, and habitat-scene visualization rather than generic computer
graphics.

## Added Skills

- `ecology-photogrammetry-and-3d-reconstruction`
  - purpose: choose and structure drone or close-range photogrammetry workflows
    for orthomosaics, DEMs, textured meshes, and habitat reconstruction
- `lidar-point-cloud-and-canopy-analysis`
  - purpose: organize LAS/LAZ, LiDAR, canopy-height, and tree-structure
    workflows for ecology and forestry questions
- `habitat-scene-3d-visualization`
  - purpose: plan reproducible 3D visualization and communication workflows for
    habitats, terrain, point clouds, and ecological meshes

## Added Toolkits

- `OpenDroneMap`
  - source: [OpenDroneMap/ODM](https://github.com/OpenDroneMap/ODM)
  - fit: open aerial photogrammetry for orthomosaics, DEMs, point clouds, and
    textured models
- `WebODM`
  - source: [OpenDroneMap/WebODM](https://github.com/OpenDroneMap/WebODM)
  - fit: friendlier team-facing drone processing and repeatable survey tasks
- `Meshroom`
  - source: [alicevision/Meshroom](https://github.com/alicevision/Meshroom)
  - fit: close-range and object-scale 3D reconstruction when a node-based UI is
    more useful than pure scripting
- `PDAL`
  - source: [PDAL/PDAL](https://github.com/PDAL/PDAL)
  - fit: reproducible point-cloud pipelines, reprojection, filtering, tiling,
    and normalization
- `CloudCompare`
  - source: [CloudCompare/CloudCompare](https://github.com/CloudCompare/CloudCompare)
  - fit: interactive QA of large point clouds and mesh-versus-cloud comparison
- `Open3D`
  - source: [isl-org/Open3D](https://github.com/isl-org/Open3D)
  - fit: Python-native point-cloud, mesh, registration, and voxel analysis
- `PyVista`
  - source: [pyvista/pyvista](https://github.com/pyvista/pyvista)
  - fit: reproducible 3D ecological figures and mesh visualization
- `Potree`
  - source: [potree/potree](https://github.com/potree/potree)
  - fit: browser-based sharing and inspection of large point clouds
- `lidR`
  - source: [r-lidar/lidR](https://github.com/r-lidar/lidR)
  - fit: airborne LiDAR ecology and forestry workflows in R
- `ForestTools`
  - source: [andrew-plowright/ForestTools](https://github.com/andrew-plowright/ForestTools)
  - fit: canopy-height-model analysis and tree delineation from remote sensing
- `Blender`
  - source: [blender/blender](https://github.com/blender/blender)
  - fit: final habitat-scene cleanup, annotation, rendering, and communication

## Added MCP Servers

- `blender-mcp`
  - source: [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp)
  - fit: prompt-assisted Blender inspection, scripting, and scene editing
- `qgis-mcp`
  - source: [jjsantos01/qgis_mcp](https://github.com/jjsantos01/qgis_mcp)
  - fit: geospatial alignment, raster/vector review, and processing around 3D
    ecology outputs

## Example Prompts

```bash
eh prompt '/ecology-photogrammetry-and-3d-reconstruction reconstruct a saltmarsh monitoring plot from UAV imagery'
eh prompt '/lidar-point-cloud-and-canopy-analysis ALS canopy height and individual-tree workflow for a temperate forest'
eh prompt '/habitat-scene-3d-visualization prepare a web and figure workflow for a coral reef mesh plus point cloud'
```

## Suggested Pairings

- `OpenDroneMap` + `QGIS MCP`
  - best when georeferenced drone products must be checked against rasters,
    boundaries, and CRS-aware map layers
- `PDAL` + `CloudCompare`
  - best when scripted point-cloud processing must be paired with interactive QA
- `Open3D` + `PyVista`
  - best when analysis and final 3D figures both need to stay in Python
- `Blender` + `blender-mcp`
  - best when ecological meshes need annotation, staging, or presentation-ready
    rendering
