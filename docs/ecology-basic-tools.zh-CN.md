# Ecology 基础工具说明

这个文档把“生态观测、实验室工作流与光生物反应器分析基础工具”按功能簇整理出来，并标明当前仓库里哪些已经原生可用，哪些已经作为外部工具目录接入。

## 功能地图

| 功能簇 | 典型需求 | 已安装原生工具 | 已编目外部工具 |
|---|---|---|---|
| 野外观测与物种识别 | 从照片识别植物、规范学名、查看附近观测 | `INaturalistSearchTaxa`、`INaturalistSearchObservations`、`PlantNetIdentify`、`ListEcologyFunctions`、`ListEcologyToolkits` | `pyinaturalist`、`Pl@ntNet API`、`pybioclip`、`nature-id` |
| 植物表型与性状提取 | 叶片性状、形态测量、腊叶标本测量、器官检测 | `ListEcologyToolkits`、`DescribeEcologyToolkit` | `PlantCV`、`LeafMachine2`、`RhizoVision Explorer`、`RootPainter` |
| 根系表型与根际成像 | 根冠、洗根图像、rhizobox、minirhizotron、根系性状提取 | `ListEcologyFunctions`、`ListEcologyToolkits`、`DescribeEcologyToolkit` | `RhizoVision Explorer`、`RootPainter`、`OpenSimRoot` |
| 植物、作物与成长模拟 | 作物物候、灌溉、木本植被、根-茎结构、微生物增长、生物膜、参数估计、情景比较 | `ListEcologyFunctions`、`ListEcologyToolkits`、`DescribeEcologyToolkit` | `APSIM Next Generation`、`PCSE / WOFOST`、`AquaCrop-OSPy`、`BioCro`、`pyfao56`、`CPlantBox`、`OpenAlea L-Py`、`OpenSimRoot`、`r3PG`、`medfate`、`pyrealm`、`FATES`、`COBRApy`、`MICOM`、`COMETS`、`BacArena`、`Community Simulator`、`Tellurium`、`COPASI`、`PySCeS`、`NUFEB`、`Vivarium Core`、`MDSINE2`、`miaSim`、`pyPESTO`、`CarveMe`、`PyCoMo` |
| 传统生态过程模型与主体模型 | 主体生态、流域路由、食物网模拟、森林干扰、DGVM 风格工作流 | `ListEcologyFunctions`、`ListEcologyToolkits`、`DescribeEcologyToolkit` | `NetLogo`、`Mesa`、`GAMA Platform`、`DSSAT Cropping System Model`、`SWAT+`、`Ecopath with Ecosim`、`LPJ-GUESS`、`FATES`、`ED2`、`Biome-BGC`、`CENTURY / DayCent`、`RHESSys`、`LANDIS-II`、`Madingley Model`、`RangeShifter 2.0` |
| 湖库与水体生态过程模拟 | 分层、溶氧、藻华、营养盐情景、水质和水体生物地球化学 | `ListEcologyFunctions`、`ListEcologyToolkits`、`DescribeEcologyToolkit` | `GLM`、`glm-py`、`FABM` |
| 计数与密度估计 | 植株计数、树木计数、动物计数、密度估计 | `ListEcologyToolkits`、`DescribeEcologyToolkit` | `PlantCV`、`DeepForest`、`detectree2`、`TreeCountSegHeight`、`PyTorch-Wildlife` |
| 检测与分割 | 目标检测、实例分割、树冠分割、影像切片 | `ListEcologyToolkits`、`DescribeEcologyToolkit` | `DeepForest`、`detectree2`、`TreeCountSegHeight`、`PyTorch-Wildlife` |
| 相机陷阱工作流 | 空图过滤、动物检测、检测后分类 | `ListEcologyToolkits`、`DescribeEcologyToolkit` | `PyTorch-Wildlife` |
| 动物行为与姿态跟踪 | 运动轨迹、觅食、求偶、多动物互动、无标记跟踪 | `ListEcologyFunctions`、`ListEcologyToolkits`、`DescribeEcologyToolkit` | `DeepLabCut`、`SLEAP`、`PyTorch-Wildlife` |
| 生态三维重建与点云 | 无人机摄影测量、近景测量级摄影测量、LiDAR 预处理与模拟、单木 QSM、生境网格、浏览器与地理三维发布 | `ListEcologyFunctions`、`ListEcologyToolkits`、`DescribeEcologyToolkit`、`ListMcpServersTool` | `OpenDroneMap`、`WebODM`、`Meshroom`、`COLMAP`、`MicMac`、`PDAL`、`HELIOS++`、`CloudCompare`、`Open3D`、`TreeQSM`、`SimpleForest`、`PyVista`、`ParaView`、`Potree`、`CesiumJS`、`lidR`、`ForestTools`、`Blender`、`blender-mcp`、`qgis-mcp` |
| 生态声学 | 鸟声识别、批量音频筛查、eBird 背景验证 | `ListEcologyToolkits`、`DescribeEcologyToolkit` | `BirdNET-Analyzer`、`OpenSoundscape`、`eBird MCP Server` |
| 物种分布与生物多样性建模 | occurrence 质控、海洋和鸟类观测、SDM、Maxent 调参、时空分布模型 | `ListEcologyFunctions`、`ListEcologyToolkits`、`DescribeEcologyToolkit`、`McpSearchTool` | `pygbif`、`pyobis`、`eBird MCP Server`、`CoordinateCleaner`、`biomod2`、`ENMeval`、`maxnet`、`sdmTMB` |
| 运动生态与遥测 | Movebank 风格导入、轨迹清理、home range、step-selection、迁徙廊道 | `ListEcologyFunctions`、`ListEcologyToolkits`、`DescribeEcologyToolkit` | `move2`、`ctmm`、`amt` |
| 开放环境数据与 forcing | USGS 流量、水质、土壤、空气质量、STAC/GEE covariates、地形和分区统计 | `ListEcologyFunctions`、`ListEcologyToolkits`、`DescribeEcologyToolkit`、`McpSearchTool` | `dataretrieval-python`、`PyGeoHydro`、`soilDB`、`SoilGrids API`、`OpenAQ Python Client`、`pystac-client`、`stackstac`、`odc-stac`、`geemap`、`leafmap`、`WhiteboxTools`、`exactextract`、`OpenAPI MCP Server` |
| 封闭藻类系统与光生物反应器 | 封闭反应器设计、pH/CO2 控制、污染排查、生长曲线、物质平衡 | `ListEcologyFunctions`、`ListEcologyToolkits`、`DescribeEcologyToolkit` | `Jupyter MCP Server`、`InfluxDB 3 MCP Server`、`LabArchives MCP Server`、`unit-converter-mcp`、`PyLabRobot`、`Opentrons` |
| 实验协议、自动化与 notebook 工作流 | SOP 草拟、实验记录、时序 notebook、液体处理、单位统一 | `ListEcologyFunctions`、`ListEcologyToolkits`、`DescribeEcologyToolkit` | `Jupyter MCP Server`、`LabArchives MCP Server`、`unit-converter-mcp`、`PyLabRobot`、`Opentrons` |
| 水体微宇宙、浮游生物与生物膜 | 摄食微宇宙、附着生物膜、上下层分区、群落变化 | `ListEcologyFunctions`、`ListEcologyToolkits`、`DescribeEcologyToolkit` | `Jupyter MCP Server`、`InfluxDB 3 MCP Server`、`Fiji / ImageJ`、`CellProfiler`、`napari`、`ilastik`、`EcoTaxa Python Client`、`PlanktoScope`、`MorphoCut`、`GLM`、`glm-py`、`FABM` |
| 显微图像、自动分类与荧光工作流 | 显微镜相机分类、对象分割、荧光通道、多光谱图像复核 | `ListEcologyFunctions`、`ListEcologyToolkits`、`DescribeEcologyToolkit` | `Fiji / ImageJ`、`PyImageJ`、`CellProfiler`、`napari`、`ilastik`、`scikit-image`、`EcoTaxa Python Client`、`MorphoCut`、`RootPainter` |
| 分子与采样后续分析 | PCR、扩增子、微生物群落后续分析、总碳等实验室指标 | `ListEcologyFunctions`、`ListEcologyToolkits`、`DescribeEcologyToolkit` | `QIIME 2 / Rachis Framework`、`DADA2`、`mothur`、`VSEARCH`、`CarveMe`、`PyCoMo`、`Jupyter MCP Server`、`LabArchives MCP Server` |
| 工作流选择与质控 | 选型、能力比较、约束说明 | `ListEcologyFunctions`、`ListEcologyToolkits`、`DescribeEcologyToolkit` | 全部已编目工具 |

## 已安装原生工具

- `INaturalistSearchTaxa`
  - 按学名或俗名检索 taxon，并返回 rank 与观测规模信息。
- `INaturalistSearchObservations`
  - 按 taxon、地点、质量等级等条件检索 iNaturalist 观测。
- `PlantNetIdentify`
  - 用 Pl@ntNet 对本地植物图片做识别。
  - 需要设置 `PLANTNET_API_KEY`。
- `ListEcologyFunctions`
  - 列出生态基础工具所覆盖的功能树。
- `ListEcologyToolkits`
  - 按能力或模态查看当前已编目的外部工具。
- `DescribeEcologyToolkit`
  - 查看某个工具的仓库来源、安装方式和适用场景。

## 已编目的外部工具

- `pyinaturalist`
  - 来源：[pyinat/pyinaturalist](https://github.com/pyinat/pyinaturalist)
  - 作用：iNaturalist API Python 客户端，适合 taxa、observations、species counts。
- `Pl@ntNet API`
  - 来源：[plantnet/my.plantnet](https://github.com/plantnet/my.plantnet)
  - 作用：植物图片识别，支持本地图片上传和器官提示。
- `pybioclip`
  - 来源：[Imageomics/pybioclip](https://github.com/Imageomics/pybioclip)
  - 作用：基于 BioCLIP 的通用生物图像分类与 embedding。
- `nature-id`
  - 来源：[joergmlpts/nature-id](https://github.com/joergmlpts/nature-id)
  - 作用：植物、鸟类、昆虫的轻量图片识别，并支持高阶 taxon fallback。
- `PlantCV`
  - 来源：[danforthcenter/plantcv](https://github.com/danforthcenter/plantcv)
  - 作用：植物表型和性状分析的强工具箱。
- `LeafMachine2`
  - 来源：[Gene-Weaver/LeafMachine2](https://github.com/Gene-Weaver/LeafMachine2)
  - 作用：腊叶标本、叶片测量和档案组件识别。
- `RhizoVision Explorer`
  - 来源：[noble-research-group/RhizoVisionExplorer](https://github.com/noble-research-group/RhizoVisionExplorer)
  - 作用：很适合根图像分析、根系性状提取和地下表型工作流。
- `RootPainter`
  - 来源：[Abe404/root_painter](https://github.com/Abe404/root_painter)
  - 作用：适合根系与土壤背景分割困难场景下的交互式校正分割。
- `APSIM Next Generation`
  - 来源：[APSIMInitiative/ApsimX](https://github.com/APSIMInitiative/ApsimX)
  - 作用：很强的农业系统框架，适合管理、作物和轮作情景。
- `PCSE / WOFOST`
  - 来源：[ajwdewit/pcse](https://github.com/ajwdewit/pcse)
  - 作用：Python 优先、很适合作物物候、生物量和产量研究。
- `AquaCrop-OSPy`
  - 来源：[aquacropos/aquacrop](https://github.com/aquacropos/aquacrop)
  - 作用：特别适合灌溉、干旱和水分受限生长问题。
- `BioCro`
  - 来源：[biocro/biocro](https://github.com/biocro/biocro)
  - 作用：适合显式冠层光合和机理性作物生态生理问题。
- `pyfao56`
  - 来源：[kthorp/pyfao56](https://github.com/kthorp/pyfao56)
  - 作用：很适合 ET、灌溉核算和作物水分平衡工作流。
- `CPlantBox`
  - 来源：[Plant-Root-Soil-Interactions-Modelling/CPlantBox](https://github.com/Plant-Root-Soil-Interactions-Modelling/CPlantBox)
  - 作用：很适合 3D 根-茎结构与植物-土壤互作。
- `OpenAlea L-Py`
  - 来源：[openalea/lpy](https://github.com/openalea/lpy)
  - 作用：成熟的 L-system 植物结构建模环境。
- `OpenSimRoot`
  - 来源：[OpenSimRoot project](https://rootsystemml.github.io/ISMCROOT/opensimroot/)
  - 作用：很适合把根系成像测量进一步推进到机制性根系模拟。
- `r3PG`
  - 来源：[trotsiuk/r3PG](https://github.com/trotsiuk/r3PG)
  - 作用：适合林分、人工林和木本生产力问题。
- `medfate`
  - 来源：[emf-creaf/medfate](https://github.com/emf-creaf/medfate)
  - 作用：适合木本植被、干旱胁迫和植物水力过程。
- `pyrealm`
  - 来源：[ImperialCollegeLondon/pyrealm](https://github.com/ImperialCollegeLondon/pyrealm)
  - 作用：能把环境因子、生产力和生态生理过程连起来。
- `FATES`
  - 来源：[NGEET/fates](https://github.com/NGEET/fates)
  - 作用：适合植被种群统计、干扰和长期陆地生态过程研究。
- `COBRApy`
  - 来源：[opencobra/cobrapy](https://github.com/opencobra/cobrapy)
  - 作用：微生物代谢增长模拟的基础框架。
- `MICOM`
  - 来源：[micom-dev/micom](https://github.com/micom-dev/micom)
  - 作用：适合微生物群落代谢和 cross-feeding。
- `COMETS`
  - 来源：[segrelab/comets](https://github.com/segrelab/comets)
  - 作用：适合带空间扩散和代谢交换的群落模拟。
- `BacArena`
  - 来源：[euba/BacArena](https://github.com/euba/BacArena)
  - 作用：能把微生物个体和代谢交换同时显式表示出来。
- `Community Simulator`
  - 来源：[Emergent-Behaviors-in-Biology/community-simulator](https://github.com/Emergent-Behaviors-in-Biology/community-simulator)
  - 作用：适合资源竞争和群落组装导向的微生物生态问题。
- `Tellurium`
  - 来源：[sys-bio/tellurium](https://github.com/sys-bio/tellurium)
  - 作用：很适合 SBML / ODE 风格的机理增长模型。
- `COPASI`
  - 来源：[copasi/COPASI](https://github.com/copasi/COPASI)
  - 作用：成熟的动态系统和参数拟合平台。
- `PySCeS`
  - 来源：[PySCeS/pysces](https://github.com/PySCeS/pysces)
  - 作用：Python 原生的动力学建模方案。
- `NUFEB`
  - 来源：[nufeb/NUFEB](https://github.com/nufeb/NUFEB)
  - 作用：适合生物膜、个体基础微生物和反应器空间系统。
- `Vivarium Core`
  - 来源：[vivarium-collective/vivarium-core](https://github.com/vivarium-collective/vivarium-core)
  - 作用：适合自定义多过程微生物生态工作流。
- `MDSINE2`
  - 来源：[gerberlab/MDSINE2](https://github.com/gerberlab/MDSINE2)
  - 作用：适合带时间序列的微生物群落动态问题。
- `miaSim`
  - 来源：[microbiome/miaSim](https://github.com/microbiome/miaSim)
  - 作用：适合微生物组 benchmark 和扰动情景模拟。
- `pyPESTO`
  - 来源：[ICB-DCM/pyPESTO](https://github.com/ICB-DCM/pyPESTO)
  - 作用：很强的参数估计、不确定性和敏感性工具。
- `CarveMe`
  - 来源：[cdanielmachado/carveme](https://github.com/cdanielmachado/carveme)
  - 作用：适合把微生物基因组或分离株信息连接到代谢模型重建。
- `PyCoMo`
  - 来源：[univieCUBE/PyCoMo](https://github.com/univieCUBE/PyCoMo)
  - 作用：适合做群落尺度代谢建模和交叉喂养分析。
- `NetLogo`
  - 来源：[NetLogo/NetLogo](https://github.com/NetLogo/NetLogo)
  - 作用：很适合作为主体生态和规则驱动空间模拟的起点。
- `Mesa`
  - 来源：[mesa/mesa](https://github.com/mesa/mesa)
  - 作用：Python 原生主体模型框架，很适合 notebook 和科学计算工作流。
- `GAMA Platform`
  - 来源：[gama-platform/gama](https://github.com/gama-platform/gama)
  - 作用：很适合 GIS 感知的多主体空间生态模型。
- `DSSAT Cropping System Model`
  - 来源：[DSSAT/dssat-csm-os](https://github.com/DSSAT/dssat-csm-os)
  - 作用：经典作物系统模型，适合农业生态和管理情景分析。
- `SWAT+`
  - 来源：[SWAT+ 文档](https://swatplus.gitbook.io/docs/)
  - 作用：很适合流域水文、水质和土地利用管理情景。
- `GLM`
  - 来源：[AquaticEcoDynamics/GLM](https://github.com/AquaticEcoDynamics/GLM)
  - 作用：湖库分层、水动力和水柱模拟的实用入口。
- `glm-py`
  - 来源：[AquaticEcoDynamics/glm-py](https://github.com/AquaticEcoDynamics/glm-py)
  - 作用：适合用 Python 和 notebook 驱动可重复的 GLM 工作流。
- `FABM`
  - 来源：[fabm-model/fabm](https://github.com/fabm-model/fabm)
  - 作用：适合更进一步接入水体生物地球化学和生态过程模块。
- `Ecopath with Ecosim`
  - 来源：[Ecopath 项目](https://ecopath.org/)
  - 作用：成熟的食物网和营养级模拟系统。
- `LPJ-GUESS`
  - 来源：[LPJ-GUESS](https://web.nateko.lu.se/lpj-guess/index.html)
  - 作用：很适合动态植被和陆地生态过程问题。
- `ED2`
  - 来源：[EDmodel/ED2](https://github.com/EDmodel/ED2)
  - 作用：适合生态系统人口统计和植被结构问题。
- `Biome-BGC`
  - 来源：[Biome-BGC](https://carbonmodel.org/biome_bgc/)
  - 作用：适合碳-水-氮循环和 LAI 驱动的生态系统响应。
- `CENTURY / DayCent`
  - 来源：[Colorado State Century 项目](https://www.nrel.colostate.edu/projects/century/)
  - 作用：适合植物-土壤养分循环和土壤碳问题。
- `RHESSys`
  - 来源：[RHESSys/RHESSys](https://github.com/RHESSys/RHESSys)
  - 作用：很适合生态水文耦合问题。
- `LANDIS-II`
  - 来源：[LANDIS-II](https://www.landis-ii.org/home)
  - 作用：适合森林景观、干扰和经营模拟。
- `Madingley Model`
  - 来源：[Madingley Model](https://madingley.github.io/)
  - 作用：适合一般生态系统和多营养级问题。
- `RangeShifter 2.0`
  - 来源：[RangeShifter 2.0](https://rangeshifter.github.io/software/rangeshifter2.0/)
  - 作用：适合扩散、分布变化和空间 eco-evolution 情景。
- `DeepForest`
  - 来源：[weecology/DeepForest](https://github.com/weecology/DeepForest)
  - 作用：航空影像中的树冠和鸟类检测。
- `detectree2`
  - 来源：[PatBall1/detectree2](https://github.com/PatBall1/detectree2)
  - 作用：树冠分割和 delineation。
- `TreeCountSegHeight`
  - 来源：[sizhuoli/TreeCountSegHeight](https://github.com/sizhuoli/TreeCountSegHeight)
  - 作用：大尺度树木计数、树冠分割和高度预测。
- `PyTorch-Wildlife`
  - 来源：[microsoft/CameraTraps](https://github.com/microsoft/CameraTraps)
  - 作用：相机陷阱动物检测和分类。
- `DeepLabCut`
  - 来源：[DeepLabCut/DeepLabCut](https://github.com/DeepLabCut/DeepLabCut)
  - 作用：行为生态和运动分析里很强的无标记姿态估计工具。
- `SLEAP`
  - 来源：[talmolab/sleap](https://github.com/talmolab/sleap)
  - 作用：多动物互动和身份保持场景下很有价值。
- `BirdNET-Analyzer`
  - 来源：[birdnet-team/BirdNET-Analyzer](https://github.com/birdnet-team/BirdNET-Analyzer)
  - 作用：鸟声识别和批量生态声学处理。
- `OpenSoundscape`
  - 来源：[kitzeslab/opensoundscape](https://github.com/kitzeslab/opensoundscape)
  - 作用：补充 BirdNET，适合可训练的 Python 生态声学工作流。
- `eBird MCP Server`
  - 来源：[moonbirdai/ebird-mcp-server](https://github.com/moonbirdai/ebird-mcp-server)
  - 作用：提供鸟类 recent observations、hotspots、notable records 和 taxonomy 背景。
- `pygbif`
  - 来源：[gbif/pygbif](https://github.com/gbif/pygbif)
  - 作用：Python 原生 GBIF occurrence 和 taxonomy 工作流。
- `pyobis`
  - 来源：[iobis/pyobis](https://github.com/iobis/pyobis)
  - 作用：通过 OBIS 获取海洋生物多样性 occurrence。
- `CoordinateCleaner`
  - 来源：[ropensci/CoordinateCleaner](https://github.com/ropensci/CoordinateCleaner)
  - 作用：做 SDM 前的 occurrence 坐标质控。
- `biomod2`
  - 来源：[biomodhub/biomod2](https://github.com/biomodhub/biomod2)
  - 作用：成熟的 ensemble species distribution modeling 工作流。
- `ENMeval`
  - 来源：[jamiemkass/ENMeval](https://github.com/jamiemkass/ENMeval)
  - 作用：Maxent 风格生态位模型调参和评估。
- `maxnet`
  - 来源：[mrmaxent/maxnet](https://github.com/mrmaxent/maxnet)
  - 作用：轻量 Maxent 风格 R 建模。
- `sdmTMB`
  - 来源：[pbs-assess/sdmTMB](https://github.com/pbs-assess/sdmTMB)
  - 作用：适合丰度、生物量和分布的空间/时空模型。
- `dataretrieval-python`
  - 来源：[DOI-USGS/dataretrieval-python](https://github.com/DOI-USGS/dataretrieval-python)
  - 作用：USGS 和 Water Quality Portal 数据获取。
- `PyGeoHydro`
  - 来源：[hyriver/pygeohydro](https://github.com/hyriver/pygeohydro)
  - 作用：流域、水文和 hydrography web-service 访问。
- `soilDB`
  - 来源：[ncss-tech/soilDB](https://github.com/ncss-tech/soilDB)
  - 作用：土壤调查和剖面数据。
- `SoilGrids API`
  - 来源：[SoilGrids](https://soilgrids.org/)
  - 作用：全球土壤 covariates。
- `OpenAQ Python Client`
  - 来源：[openaq/openaq-python](https://github.com/openaq/openaq-python)
  - 作用：空气质量观测和暴露背景。
- `pystac-client`
  - 来源：[stac-utils/pystac-client](https://github.com/stac-utils/pystac-client)
  - 作用：Python STAC catalog 检索。
- `stackstac`
  - 来源：[gjoseph92/stackstac](https://github.com/gjoseph92/stackstac)
  - 作用：把 STAC item 加载成 xarray。
- `odc-stac`
  - 来源：[opendatacube/odc-stac](https://github.com/opendatacube/odc-stac)
  - 作用：Open Data Cube 风格的 STAC/xarray 工作流。
- `geemap`
  - 来源：[gee-community/geemap](https://github.com/gee-community/geemap)
  - 作用：Google Earth Engine Python 分析与可视化。
- `leafmap`
  - 来源：[opengeos/leafmap](https://github.com/opengeos/leafmap)
  - 作用：交互式地图、STAC 浏览和空间质控。
- `WhiteboxTools`
  - 来源：[jblindsay/whitebox-tools](https://github.com/jblindsay/whitebox-tools)
  - 作用：地形、水文和栅格特征工程。
- `exactextract`
  - 来源：[isciences/exactextract](https://github.com/isciences/exactextract)
  - 作用：快速分区统计，把栅格转成模型 covariates。
- `ctmm`
  - 来源：[ctmm-initiative/ctmm](https://github.com/ctmm-initiative/ctmm)
  - 作用：自相关感知的运动模型和 home range。
- `amt`
  - 来源：[jmsigner/amt](https://github.com/jmsigner/amt)
  - 作用：step-selection、轨迹预处理和 habitat-selection。
- `move2`
  - 来源：[BartK/move2](https://gitlab.com/bartk/move2)
  - 作用：运动数据处理和 Movebank 风格工作流。
- `BioMCP`
  - 来源：[yeyuan98/biomcp-ts](https://github.com/yeyuan98/biomcp-ts)
  - 作用：omics 后续分析中的基因、文献、疾病和 pathway 联合检索。
- `OpenAPI MCP Server`
  - 来源：[ivo-toby/mcp-openapi-server](https://github.com/ivo-toby/mcp-openapi-server)
  - 作用：把环境类 OpenAPI 服务暴露成 MCP 工具。
- `Jupyter MCP Server`
  - 来源：[datalayer/jupyter-mcp-server](https://github.com/datalayer/jupyter-mcp-server)
  - 作用：当前最强的一类 notebook 原生 MCP，可直接做交互分析、cell 执行和可复现实验记录。
- `InfluxDB 3 MCP Server`
  - 来源：[influxdata/influxdb3_mcp_server](https://github.com/influxdata/influxdb3_mcp_server)
  - 作用：适合 pH、温度、溶氧、光照等传感器时序数据查询与写入。
- `LabArchives MCP Server`
  - 来源：[SamuelBrudner/lab_archives_mcp](https://github.com/SamuelBrudner/lab_archives_mcp)
  - 作用：把电子实验记录本、实验发现、SOP 和分析结果关联起来。
- `unit-converter-mcp`
  - 来源：[zazencodes/unit-converter-mcp](https://github.com/zazencodes/unit-converter-mcp)
  - 作用：很适合温度、压力、密度、能量、体积等实验单位换算。
- `PyLabRobot`
  - 来源：[PyLabRobot/pylabrobot](https://github.com/PyLabRobot/pylabrobot)
  - 作用：跨设备实验室自动化框架，适合培养基配置、加液、采样和模拟。
- `Opentrons`
  - 来源：[Opentrons/opentrons](https://github.com/Opentrons/opentrons)
  - 作用：官方液体处理自动化栈，适合 OT-2 / Flex 的稳定协议执行。
- `Fiji / ImageJ`
  - 来源：[fiji/fiji](https://github.com/fiji/fiji)
  - 作用：最常见的一类科研图像工作站，适合显微、荧光和测量。
- `PyImageJ`
  - 来源：[imagej/pyimagej](https://github.com/imagej/pyimagej)
  - 作用：把 ImageJ 工作流拉进 Python 和 notebook。
- `CellProfiler`
  - 来源：[CellProfiler/CellProfiler](https://github.com/CellProfiler/CellProfiler)
  - 作用：成熟的显微图像分割和特征提取流水线工具。
- `napari`
  - 来源：[napari/napari](https://github.com/napari/napari)
  - 作用：适合人工复核、标注、多通道荧光图像查看。
- `ilastik`
  - 来源：[ilastik/ilastik](https://github.com/ilastik/ilastik)
  - 作用：很适合交互式像素分类和对象分类。
- `scikit-image`
  - 来源：[scikit-image/scikit-image](https://github.com/scikit-image/scikit-image)
  - 作用：Python 自定义图像分析和特征提取基础库。
- `EcoTaxa Python Client`
  - 来源：[ecotaxa/ecotaxa_py_client](https://github.com/ecotaxa/ecotaxa_py_client)
  - 作用：对接 plankton 分类生态中的 EcoTaxa 工作流。
- `PlanktoScope`
  - 来源：[PlanktoScope/PlanktoScope](https://github.com/PlanktoScope/PlanktoScope)
  - 作用：开源浮游生物成像平台，适合长期成像监测。
- `MorphoCut`
  - 来源：[morphocut/morphocut](https://github.com/morphocut/morphocut)
  - 作用：很适合把原始 plankton 图像处理成后续分类和测量可用的对象流水线。
- `QIIME 2 / Rachis Framework`
  - 来源：[qiime2/qiime2](https://github.com/qiime2/qiime2)
  - 作用：PCR / 扩增子后的微生物群落分析与溯源。
- `DADA2`
  - 来源：[benjjneb/dada2](https://github.com/benjjneb/dada2)
  - 作用：高分辨率扩增子去噪和 ASV 推断。
- `mothur`
  - 来源：[mothur/mothur](https://github.com/mothur/mothur)
  - 作用：稳定可靠的扩增子与分类工作流平台。
- `VSEARCH`
  - 来源：[torognes/vsearch](https://github.com/torognes/vsearch)
  - 作用：透明、开源、在 metabarcoding 中常见的序列搜索与聚类工具。

## 说明

- 这轮新增的原生工具优先选择“立刻可用、依赖轻”的在线接口。
- 更重的视觉工具、实验室自动化工具和大多数 MCP 型实验分析服务暂时先作为目录接入，因为它们往往依赖 API 凭证、运行中的 notebook server、数据库、自动化硬件或更复杂环境。
- 这样的分层可以保证现在就有基础能力可用，同时后续还能继续往本地模型、实验室自动化和时序分析方向扩展。
