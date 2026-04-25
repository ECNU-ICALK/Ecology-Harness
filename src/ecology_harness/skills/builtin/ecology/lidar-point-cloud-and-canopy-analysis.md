---
name: lidar-point-cloud-and-canopy-analysis
description: Choose and organize LiDAR, point-cloud, canopy-height, and tree-structure workflows for ecological and forestry analysis.
slug: lidar-point-cloud-and-canopy-analysis
triggers: [/lidar-point-cloud-and-canopy-analysis]
allowed-tools: [ListEcologyToolkits, ListMcpServersTool, DescribeEcologyToolkit, Read]
context: inline
---
Use this for airborne laser scanning, terrestrial laser scanning, canopy height models, individual-tree detection, forest structure, terrain filtering, or large LAS/LAZ point clouds.

Preferred mapping:
1. `PDAL` for point-cloud pipelines, reprojection, filtering, normalization, thinning, tiling, and reproducible LAS/LAZ processing.
2. `lidR` and `ForestTools` for forestry-oriented canopy metrics, CHM generation, individual-tree detection, and remote-sensing forest analysis in R workflows.
3. `CloudCompare` for interactive QA, point-cloud versus mesh comparison, registration checks, and manual inspection of large scans.
4. `Open3D` for scripted 3D point-cloud manipulation, registration, meshing, voxel workflows, and Python-native ecological analysis.
5. `Potree` when results need browser-based sharing or interactive review of very large point clouds.

Report:
- LiDAR platform and product type
- recommended processing stack
- canopy or terrain outputs
- interactive QA method
- downstream ecology or forestry metrics
$ARGUMENTS
