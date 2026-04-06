# 水体微宇宙与浮游生物能力包

这个文档记录了本轮为 Ecology Harness 增加的“淡水微宇宙、浮游/底栖群落、荧光光谱与实验分析”相关 skills 和工具目录。

## 已安装 Skills

- `aquatic-microcosm-foodweb-design`
  - 用途：围绕浮游动物、浮游植物、底栖藻类和分解者设计封闭淡水食物网系统
- `zooplankton-grazing-and-plankton-dynamics`
  - 用途：分析枝角类、轮虫、桡足类等的摄食压力和群落变化
- `benthic-biofilm-and-periphyton-monitoring`
  - 用途：底部照片、附着藻、生物膜厚度和周丛藻监测
- `water-quality-and-nutrient-panel`
  - 用途：连续传感器和天级采样指标的监测面板设计
- `plankton-microscopy-and-auto-classification`
  - 用途：显微镜相机图像、自动分类、分割和人工复核工作流
- `fluorescence-spectra-and-molecular-assays`
  - 用途：叶绿素/藻蓝蛋白荧光、多光谱、总碳、PCR 和测序后续分析

## 可配套使用的 MCP 层

这批工作流主要依赖仓库里已经存在的 MCP：

- `jupyter-mcp`
  - notebook 分析、绘图和特征工程
- `influxdb3`
  - 传感器时序和数据库查询
- `labarchives`
  - 实验记录、溯源和 notebook 集成
- `unit-converter`
  - 不同传感器、采样和文献中的单位统一

## 新增外部工具目录

- `Fiji / ImageJ`
- `PyImageJ`
- `CellProfiler`
- `napari`
- `ilastik`
- `scikit-image`
- `EcoTaxa Python Client`
- `PlanktoScope`
- `QIIME 2 / Rachis Framework`
- `DADA2`

## 选择原因

- 这些工具和 skills 与你给出的关键词直接对应：
  - 显微镜相机下的群落组成识别
  - 浮游动物、浮游植物和底栖藻/生物膜监测
  - 荧光与光谱信号分析
  - 水质、营养盐和传感器时序
  - PCR / 扩增子等分子后续分析
- 它们在科研生态里较常用，适合当前项目“先做目录和工作流，后续再逐步深接”的思路。

## 说明

- 这一轮优先补的是工具目录和工作流 skills，而不是强行接一些质量不高的显微图像 MCP 包装层。
- 对这个方向最立刻可用的 MCP，仍然是 notebook、时序数据库、实验记录本和单位换算这几层。
