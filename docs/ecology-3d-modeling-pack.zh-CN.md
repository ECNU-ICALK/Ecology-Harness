# Ecology 3D 建模工具包

这个工具包把生态三维能力补进了 Ecology Harness，重点不是泛用 CG，而是面向生态研究的三维重建、点云处理、冠层与地形分析，以及生境场景可视化。

## 新增 Skills

- `ecology-photogrammetry-and-3d-reconstruction`
  - 用途：规划无人机或近景摄影测量工作流，生成正射影像、DEM、纹理网格与生境重建结果
- `lidar-point-cloud-and-canopy-analysis`
  - 用途：组织 LAS/LAZ、LiDAR、冠层高度和树木结构分析流程
- `habitat-scene-3d-visualization`
  - 用途：规划生境、地形、点云和生态网格的三维可视化与表达工作流

## 新增 Toolkits

- `OpenDroneMap`
  - 来源：[OpenDroneMap/ODM](https://github.com/OpenDroneMap/ODM)
  - 适合：正射影像、DEM、点云、纹理模型等开源航测流程
- `WebODM`
  - 来源：[OpenDroneMap/WebODM](https://github.com/OpenDroneMap/WebODM)
  - 适合：团队协作式、界面友好的无人机影像处理
- `Meshroom`
  - 来源：[alicevision/Meshroom](https://github.com/alicevision/Meshroom)
  - 适合：近景与小尺度对象的三维重建
- `PDAL`
  - 来源：[PDAL/PDAL](https://github.com/PDAL/PDAL)
  - 适合：可复现的点云流水线、过滤、投影、切片与标准化
- `CloudCompare`
  - 来源：[CloudCompare/CloudCompare](https://github.com/CloudCompare/CloudCompare)
  - 适合：大规模点云与网格的交互式质检和比较
- `Open3D`
  - 来源：[isl-org/Open3D](https://github.com/isl-org/Open3D)
  - 适合：Python 原生点云、网格、配准与体素分析
- `PyVista`
  - 来源：[pyvista/pyvista](https://github.com/pyvista/pyvista)
  - 适合：三维生态图件与网格可视化
- `Potree`
  - 来源：[potree/potree](https://github.com/potree/potree)
  - 适合：超大点云的浏览器共享与交互查看
- `lidR`
  - 来源：[r-lidar/lidR](https://github.com/r-lidar/lidR)
  - 适合：R 里的航空 LiDAR 和森林生态分析
- `ForestTools`
  - 来源：[andrew-plowright/ForestTools](https://github.com/andrew-plowright/ForestTools)
  - 适合：冠层高度模型与树木分割
- `Blender`
  - 来源：[blender/blender](https://github.com/blender/blender)
  - 适合：生境场景整理、标注和高质量渲染

## 新增 MCP Servers

- `blender-mcp`
  - 来源：[ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp)
  - 适合：提示驱动的 Blender 场景查看、脚本和编辑
- `qgis-mcp`
  - 来源：[jjsantos01/qgis_mcp](https://github.com/jjsantos01/qgis_mcp)
  - 适合：围绕三维生态成果做地理配准、栅格/矢量检查和处理

## 示例 Prompt

```bash
eh prompt '/ecology-photogrammetry-and-3d-reconstruction 用 UAV 影像重建盐沼监测样地'
eh prompt '/lidar-point-cloud-and-canopy-analysis 设计温带森林 ALS 冠层高度和单木分析流程'
eh prompt '/habitat-scene-3d-visualization 为珊瑚礁网格和点云设计网页加图件输出流程'
```

## 推荐组合

- `OpenDroneMap` + `QGIS MCP`
  - 适合：需要把航测结果和 CRS、边界、底图一起核对
- `PDAL` + `CloudCompare`
  - 适合：脚本化点云处理后再做人工质检
- `Open3D` + `PyVista`
  - 适合：分析和最终可视化都保持在 Python 里
- `Blender` + `blender-mcp`
  - 适合：对生态网格做标注、整理和展示级渲染
