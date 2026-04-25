---
name: lidar-survey-design-and-simulation
description: Plan LiDAR survey design, virtual scanning, and acquisition benchmarking for ecological and forestry campaigns.
slug: lidar-survey-design-and-simulation
triggers: [/lidar-survey-design-and-simulation]
allowed-tools: [ListEcologyToolkits, ListMcpServersTool, DescribeEcologyToolkit, Read]
context: inline
---
Use this for designing TLS, ALS, or UAV-LiDAR campaigns before field acquisition, comparing scan layouts, or benchmarking point density and canopy observability under different survey settings.

Preferred mapping:
1. `HELIOS++` for virtual LiDAR acquisition, scanner-layout comparison, and pre-field survey simulation.
2. `PDAL` for downstream normalization, filtering, reprojection, and batch preprocessing once simulated or real point clouds exist.
3. `CloudCompare` for interactive inspection of simulated-versus-observed scan geometry and manual QA.
4. `lidR` when simulated or acquired forest LiDAR must be translated into canopy metrics, CHMs, or tree-level summaries.

Report:
- LiDAR platform and survey objective
- simulated versus real acquisition plan
- recommended software stack
- output products and benchmarking criteria
- field-validation or calibration plan
$ARGUMENTS
