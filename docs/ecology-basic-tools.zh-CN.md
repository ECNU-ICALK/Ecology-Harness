# Ecology 基础工具说明

这个文档把“生态观测、实验室工作流与光生物反应器分析基础工具”按功能簇整理出来，并标明当前仓库里哪些已经原生可用，哪些已经作为外部工具目录接入。

## 功能地图

| 功能簇 | 典型需求 | 已安装原生工具 | 已编目外部工具 |
|---|---|---|---|
| 野外观测与物种识别 | 从照片识别植物、规范学名、查看附近观测 | `INaturalistSearchTaxa`、`INaturalistSearchObservations`、`PlantNetIdentify`、`ListEcologyFunctions`、`ListEcologyToolkits` | `pyinaturalist`、`Pl@ntNet API`、`pybioclip`、`nature-id` |
| 植物表型与性状提取 | 叶片性状、形态测量、腊叶标本测量、器官检测 | `ListEcologyToolkits`、`DescribeEcologyToolkit` | `PlantCV`、`LeafMachine2` |
| 计数与密度估计 | 植株计数、树木计数、动物计数、密度估计 | `ListEcologyToolkits`、`DescribeEcologyToolkit` | `PlantCV`、`DeepForest`、`detectree2`、`TreeCountSegHeight`、`PyTorch-Wildlife` |
| 检测与分割 | 目标检测、实例分割、树冠分割、影像切片 | `ListEcologyToolkits`、`DescribeEcologyToolkit` | `DeepForest`、`detectree2`、`TreeCountSegHeight`、`PyTorch-Wildlife` |
| 相机陷阱工作流 | 空图过滤、动物检测、检测后分类 | `ListEcologyToolkits`、`DescribeEcologyToolkit` | `PyTorch-Wildlife` |
| 生态声学 | 鸟声识别、批量音频筛查 | `ListEcologyToolkits`、`DescribeEcologyToolkit` | `BirdNET-Analyzer` |
| 封闭藻类系统与光生物反应器 | 封闭反应器设计、pH/CO2 控制、污染排查、生长曲线、物质平衡 | `ListEcologyFunctions`、`ListEcologyToolkits`、`DescribeEcologyToolkit` | `Jupyter MCP Server`、`InfluxDB 3 MCP Server`、`LabArchives MCP Server`、`unit-converter-mcp`、`PyLabRobot`、`Opentrons` |
| 实验协议、自动化与 notebook 工作流 | SOP 草拟、实验记录、时序 notebook、液体处理、单位统一 | `ListEcologyFunctions`、`ListEcologyToolkits`、`DescribeEcologyToolkit` | `Jupyter MCP Server`、`LabArchives MCP Server`、`unit-converter-mcp`、`PyLabRobot`、`Opentrons` |
| 水体微宇宙、浮游生物与生物膜 | 摄食微宇宙、附着生物膜、上下层分区、群落变化 | `ListEcologyFunctions`、`ListEcologyToolkits`、`DescribeEcologyToolkit` | `Jupyter MCP Server`、`InfluxDB 3 MCP Server`、`Fiji / ImageJ`、`CellProfiler`、`napari`、`ilastik`、`EcoTaxa Python Client`、`PlanktoScope` |
| 显微图像、自动分类与荧光工作流 | 显微镜相机分类、对象分割、荧光通道、多光谱图像复核 | `ListEcologyFunctions`、`ListEcologyToolkits`、`DescribeEcologyToolkit` | `Fiji / ImageJ`、`PyImageJ`、`CellProfiler`、`napari`、`ilastik`、`scikit-image`、`EcoTaxa Python Client` |
| 分子与采样后续分析 | PCR、扩增子、微生物群落后续分析、总碳等实验室指标 | `ListEcologyFunctions`、`ListEcologyToolkits`、`DescribeEcologyToolkit` | `QIIME 2 / Rachis Framework`、`DADA2`、`Jupyter MCP Server`、`LabArchives MCP Server` |
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
- `BirdNET-Analyzer`
  - 来源：[birdnet-team/BirdNET-Analyzer](https://github.com/birdnet-team/BirdNET-Analyzer)
  - 作用：鸟声识别和批量生态声学处理。
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
- `QIIME 2 / Rachis Framework`
  - 来源：[qiime2/qiime2](https://github.com/qiime2/qiime2)
  - 作用：PCR / 扩增子后的微生物群落分析与溯源。
- `DADA2`
  - 来源：[benjjneb/dada2](https://github.com/benjjneb/dada2)
  - 作用：高分辨率扩增子去噪和 ASV 推断。

## 说明

- 这轮新增的原生工具优先选择“立刻可用、依赖轻”的在线接口。
- 更重的视觉工具、实验室自动化工具和大多数 MCP 型实验分析服务暂时先作为目录接入，因为它们往往依赖 API 凭证、运行中的 notebook server、数据库、自动化硬件或更复杂环境。
- 这样的分层可以保证现在就有基础能力可用，同时后续还能继续往本地模型、实验室自动化和时序分析方向扩展。
