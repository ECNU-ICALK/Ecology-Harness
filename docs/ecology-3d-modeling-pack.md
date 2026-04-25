# Ecology 3D Modeling Pack

This pack adds a lightweight but high-value 3D ecology layer to Ecology
Harness. It is aimed at reconstruction, point-cloud processing, canopy and
terrain review, and habitat-scene visualization rather than generic computer
graphics.

## Added Skills

- `ecology-photogrammetry-and-3d-reconstruction`
  - purpose: choose and structure drone or close-range photogrammetry workflows
    for orthomosaics, DEMs, textured meshes, and habitat reconstruction
- `close-range-ecology-photogrammetry`
  - purpose: choose measurement-oriented close-range photogrammetry workflows
    for quadrats, corals, roots, branches, and specimen-scale 3D reconstruction
- `lidar-point-cloud-and-canopy-analysis`
  - purpose: organize LAS/LAZ, LiDAR, canopy-height, and tree-structure
    workflows for ecology and forestry questions
- `lidar-survey-design-and-simulation`
  - purpose: design and benchmark TLS, ALS, and UAV-LiDAR acquisition layouts
    before field campaigns
- `tree-qsm-and-forest-structure-modeling`
  - purpose: fit single-tree and plot-scale quantitative structure models from
    terrestrial point clouds
- `habitat-scene-3d-visualization`
  - purpose: plan reproducible 3D visualization and communication workflows for
    habitats, terrain, point clouds, and ecological meshes
- `web-geospatial-3d-publishing`
  - purpose: publish ecology meshes, terrains, and point clouds to browsers or
    scientific 3D viewers with geospatial context

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
- `COLMAP`
  - source: [colmap/colmap](https://github.com/colmap/colmap)
  - fit: research-grade structure-from-motion and dense reconstruction for
    specimen, coral, branch, and quadrat-scale ecology scenes
- `MicMac`
  - source: [micmacIGN/micmac](https://github.com/micmacIGN/micmac)
  - fit: more measurement-oriented and control-point-aware photogrammetry when
    survey rigor matters
- `PDAL`
  - source: [PDAL/PDAL](https://github.com/PDAL/PDAL)
  - fit: reproducible point-cloud pipelines, reprojection, filtering, tiling,
    and normalization
- `HELIOS++`
  - source: [3dgeo-heidelberg/helios](https://github.com/3dgeo-heidelberg/helios)
  - fit: LiDAR survey design, virtual scanning, and acquisition benchmarking
- `CloudCompare`
  - source: [CloudCompare/CloudCompare](https://github.com/CloudCompare/CloudCompare)
  - fit: interactive QA of large point clouds and mesh-versus-cloud comparison
- `Open3D`
  - source: [isl-org/Open3D](https://github.com/isl-org/Open3D)
  - fit: Python-native point-cloud, mesh, registration, and voxel analysis
- `TreeQSM`
  - source: [InverseTampere/TreeQSM](https://github.com/InverseTampere/TreeQSM)
  - fit: single-tree quantitative structure models from TLS point clouds
- `SimpleForest`
  - source: [SimpleForest GitLab](https://gitlab.com/SimpleForest)
  - fit: forest-plot and tree-structure workflows in Computree-style TLS
    environments
- `PyVista`
  - source: [pyvista/pyvista](https://github.com/pyvista/pyvista)
  - fit: reproducible 3D ecological figures and mesh visualization
- `ParaView`
  - source: [Kitware/ParaView](https://github.com/Kitware/ParaView)
  - fit: heavy scientific visualization for large ecological 3D datasets and
    gridded fields
- `Potree`
  - source: [potree/potree](https://github.com/potree/potree)
  - fit: browser-based sharing and inspection of large point clouds
- `CesiumJS`
  - source: [CesiumGS/cesium](https://github.com/CesiumGS/cesium)
  - fit: geospatial 3D publishing with terrain, imagery, and browser delivery
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
eh prompt '/close-range-ecology-photogrammetry reconstruct a coral colony from close-range photos with scale bars'
eh prompt '/lidar-point-cloud-and-canopy-analysis ALS canopy height and individual-tree workflow for a temperate forest'
eh prompt '/lidar-survey-design-and-simulation compare TLS scanner layouts for a dense forest plot'
eh prompt '/tree-qsm-and-forest-structure-modeling extract branch and woody structure metrics from TLS tree clouds'
eh prompt '/habitat-scene-3d-visualization prepare a web and figure workflow for a coral reef mesh plus point cloud'
eh prompt '/web-geospatial-3d-publishing publish a dune and marsh 3D scene with terrain-aware browser review'
```

## Suggested Pairings

- `OpenDroneMap` + `QGIS MCP`
  - best when georeferenced drone products must be checked against rasters,
    boundaries, and CRS-aware map layers
- `COLMAP` + `MicMac`
  - best when specimen or quadrat reconstruction needs a research-grade stack
    with stronger control over geometry and survey rigor
- `HELIOS++` + `PDAL`
  - best when LiDAR acquisition design must feed directly into a reproducible
    processing workflow
- `TreeQSM` + `SimpleForest`
  - best when single-tree QSM fitting and plot-scale TLS interpretation both
    matter in the same forest-structure study
- `PDAL` + `CloudCompare`
  - best when scripted point-cloud processing must be paired with interactive QA
- `Open3D` + `PyVista`
  - best when analysis and final 3D figures both need to stay in Python
- `ParaView` + `CesiumJS`
  - best when large scientific 3D outputs must be published or reviewed in
    browser and map-aware contexts
- `Blender` + `blender-mcp`
  - best when ecological meshes need annotation, staging, or presentation-ready
    rendering
