# Ecology 基础工具说明

这个文档把“生态观测与视觉基础工具”按功能簇整理出来，并标明当前仓库里哪些已经原生可用，哪些已经作为外部工具目录接入。

## 功能地图

| 功能簇 | 典型需求 | 已安装原生工具 | 已编目外部工具 |
|---|---|---|---|
| 野外观测与物种识别 | 从照片识别植物、规范学名、查看附近观测 | `INaturalistSearchTaxa`、`INaturalistSearchObservations`、`PlantNetIdentify`、`ListEcologyFunctions`、`ListEcologyToolkits` | `pyinaturalist`、`Pl@ntNet API`、`pybioclip`、`nature-id` |
| 植物表型与性状提取 | 叶片性状、形态测量、腊叶标本测量、器官检测 | `ListEcologyToolkits`、`DescribeEcologyToolkit` | `PlantCV`、`LeafMachine2` |
| 计数与密度估计 | 植株计数、树木计数、动物计数、密度估计 | `ListEcologyToolkits`、`DescribeEcologyToolkit` | `PlantCV`、`DeepForest`、`detectree2`、`TreeCountSegHeight`、`PyTorch-Wildlife` |
| 检测与分割 | 目标检测、实例分割、树冠分割、影像切片 | `ListEcologyToolkits`、`DescribeEcologyToolkit` | `DeepForest`、`detectree2`、`TreeCountSegHeight`、`PyTorch-Wildlife` |
| 相机陷阱工作流 | 空图过滤、动物检测、检测后分类 | `ListEcologyToolkits`、`DescribeEcologyToolkit` | `PyTorch-Wildlife` |
| 生态声学 | 鸟声识别、批量音频筛查 | `ListEcologyToolkits`、`DescribeEcologyToolkit` | `BirdNET-Analyzer` |
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

## 说明

- 这轮新增的原生工具优先选择“立刻可用、依赖轻”的在线接口。
- 更重的视觉/声学工具暂时先作为外部工具目录接入，因为它们往往依赖 GPU、CUDA、大模型权重或更复杂的环境。
- 这样的分层可以保证现在就有基础能力可用，同时后续还能继续往本地模型方向扩展。
