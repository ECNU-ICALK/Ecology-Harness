# Ecology Harness

[English](README.md) | [简体中文](README.zh-CN.md)

Ecology Harness 是一个面向生态、环境与农业生态研究工作流的 Python Agent Harness。当前项目已经内置了一批不断增长的生态能力包，包括面向不同子方向的 skills、可发现的 MCP 目录，以及用于文献检索、空间分析、水体微宇宙、光生物反应器、生物多样性观测、显微图像和多模态分析的实用 tools。

项目希望在保持通用 Harness 内核稳定的同时，把生态领域的扩展面做得越来越丰富，让新的 skills、MCP servers 和 tools 能持续叠加而不把核心运行时搞乱。也非常欢迎大家一起参与补充和完善，共同把这个生态领域的能力栈做得更完整。

当前发布版本是 `0.2.0 beta`（包版本为 `0.2.0b0`）。
变更说明见 [CHANGELOG.md](CHANGELOG.md)，参与方式见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## News

- `2026-04-06`：发布 `0.2.0 beta`，这是 Ecology Harness 第一个可正式分发的 beta 版本。
- `2026-04-09`：从 `K-Dense-AI/claude-scientific-skills` 引入了一批经过筛选的科研技能包，补充了文献综述、论文检索、地理空间分析、统计分析、科学可视化、生物信息、实验记录与 protocol 自动化等能力。
- `2026-04-09`：继续补充了三类内置技能包：来自 `obra/superpowers` 的 workflow 工程技能、来自 `blader/humanizer` 的写作去 AI 腔技能，以及来自 `Orchestra-Research/AI-Research-SKILLs` 的大规模 AI 研究技能树。

## 启动界面

![Ecology Harness 启动截图](imgs/start_img.png)

## 目录结构

```text
EcologyHarness/
├── .github/workflows/        # CI 测试与打包 smoke check
├── docs/                     # 专题说明、架构文档与领域参考
├── imgs/                     # README 和启动截图
├── scripts/                  # 本地安装辅助脚本
├── src/ecology_harness/
│   ├── agents/               # 多智能体协同与任务状态
│   ├── config/               # 设置与运行时配置
│   ├── ecology/              # 生态领域 catalog 与扩展入口
│   ├── mcp/                  # MCP 注册、目录和桥接逻辑
│   ├── memory/               # 持久记忆管理
│   ├── permissions/          # 权限策略与安全检查
│   ├── plugins/              # 内置 plugin manifest 与加载器
│   ├── runtime/              # Agent loop、provider、session、压缩
│   ├── sandbox/              # 文件、shell、网络 sandbox 辅助层
│   ├── skills/               # 内置 skills，包括 ecology、scientific、workflow、writing 与 AI research packs
│   ├── tasks/                # 用户任务与 agent 任务追踪
│   ├── tools/                # 内置 CLI / runtime 工具
│   ├── ui/                   # 终端界面与 REPL 展示层
│   ├── app.py                # 应用组装入口
│   └── cli.py                # `eh` 命令入口
├── tests/unit/               # 标准库单元测试
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
└── pyproject.toml
```

## 项目包含的能力

- 模块化包结构，便于后续持续扩展
- CLI + REPL 双入口，支持自然语言与 slash command 混合使用
- 事件驱动的终端交互界面
- Agent loop 与工具调用闭环
- 统一的模型 provider 抽象层，兼容本地与远端后端
- 内置支持 `mock`、`anthropic`、`openai`、`openrouter`、`gemini`、`kimi`、`qwen`、`zhipu`、`deepseek`、`ollama`、`lmstudio`、`custom`
- 会话持久化、恢复与上下文压缩
- 可配置 Sandbox、权限策略与审计
- 工具注册系统与内置通用工具
- 支持本地图片、音频、文档与视频抽帧附件的多模态输入
- 内置文档分析工具，可处理 `pdf`、`docx`、`md`、`csv`、`json`、`html`、`ipynb`
- 双 scope 记忆系统与自动 `MEMORY.md`
- 多智能体与子智能体协同机制
- Markdown skill 系统
- MCP 与 plugin 扩展骨架
- 来自高质量上游仓库的生态技能包
- 来自高质量上游仓库的科研通用技能包，覆盖文献、统计、地理空间、可视化、omics 与实验工作流
- 来自 `obra/superpowers` 的 workflow 工程技能包
- 来自 `blader/humanizer` 的写作清理与去 AI 腔技能
- 来自 `Orchestra-Research/AI-Research-SKILLs` 的 AI 研究技能树，覆盖训练、评测、推理、MLOps、多模态与论文写作
- 面向农业、环境、生态场景的 MCP 目录
- 封闭藻类系统 / 光生物反应器 skills 与实验分析型 MCP 目录
- 标准库 `unittest` 测试集

## 已安装 Skill Packs

- `ecology`：项目内置的生态、环境与农业生态工作流技能，以及 Mapbox、Open-Meteo、Semantic Scholar 等上游 domain bundles。
- `scientific`：来自 `K-Dense-AI/claude-scientific-skills` 的科研通用技能包，包括 `literature-review`、`paper-lookup`、`geopandas`、`statistical-analysis`、`scientific-visualization`、`biopython`、`scikit-bio` 等。
- `superpowers`：来自 `obra/superpowers` 的 workflow 与工程实践技能，包括 `systematic-debugging`、`test-driven-development`、`verification-before-completion`、`writing-plans`、`using-git-worktrees` 等。
- `writing`：写作清理类技能，目前包含来自 `blader/humanizer` 的 `humanizer`。
- `ai-research`：来自 `Orchestra-Research/AI-Research-SKILLs` 的大型 AI 研究技能树，覆盖 `autoresearch`、模型架构、微调、评测、推理服务、MLOps、多模态、ML 论文写作和研究 ideation。

## Ecology Pack

当前仓库已经内置了一组经过筛选的生态能力包，包括在线 skill bundle 和可发现的 MCP server 配置。

目前最适合用“子方向地图”的方式来看这批能力：

下面可点击的名称都尽量指向原始上游来源。没有明确单一上游仓库的
项目内 skill 或组合型 workflow，则保留为普通文本，不再误导性地链回
本项目仓库。

| 子方向 | 典型研究任务 | 已有 Skill | 已有 MCP / Tool |
|---|---|---|---|
| 文献检索与证据综合 | 综述、引文扩展、证据简报、综述识别、研究版图扫描 | `ecology-evidence-synthesis`<br>`literature-multi-source-search`<br>`open-access-paper-harvest`<br>[expand-references](https://github.com/zongmin-yu/semantic-scholar-skills)<br>[trace-citations](https://github.com/zongmin-yu/semantic-scholar-skills)<br>[paper-triage](https://github.com/zongmin-yu/semantic-scholar-skills) | [semantic-scholar](https://github.com/zongmin-yu/semantic-scholar-skills)<br>[openalex-research](https://github.com/oksure/openalex-research-mcp)<br>[scientific-papers](https://github.com/benedict2310/Scientific-Papers-MCP)<br>[simple-pubmed](https://github.com/andybrandt/mcp-simple-pubmed)<br>[crossref](https://github.com/BotanicaStudios/crossref-mcp)<br>[unpaywall](https://github.com/ElliotPadfield/unpaywall-mcp) |
| 个体、种群与群落生态 | 胁迫响应、种群扩张、入侵扩散、共存机制、扰动响应 | `organismal-stress-screen`<br>`population-invasion-screen`<br>`community-assembly-review` | [openalex-research](https://github.com/oksure/openalex-research-mcp)<br>[gbif](https://github.com/tyson-swetnam/gbif-mcp)<br>[simple-pubmed](https://github.com/andybrandt/mcp-simple-pubmed)<br>[scientific-papers](https://github.com/benedict2310/Scientific-Papers-MCP) |
| 生物多样性与物种分布 | 物种信息、occurrence、采样偏差、栖息地预筛查 | `biodiversity-data-triage`<br>`species-occurrence-workbench` | [gbif](https://github.com/tyson-swetnam/gbif-mcp)<br>[gis-mcp](https://github.com/mahdin75/gis-mcp)<br>[stac](https://github.com/BnJam/stac-mcp) |
| 物种识别与野外观测 | 从照片识别植物、规范 taxon、查看观测背景 | `species-photo-identification` | [PlantNetIdentify](https://github.com/plantnet/my.plantnet)<br>[INaturalistSearchTaxa](https://github.com/pyinat/pyinaturalist)<br>[INaturalistSearchObservations](https://github.com/pyinat/pyinaturalist)<br>[pyinaturalist](https://github.com/pyinat/pyinaturalist)<br>[Pl@ntNet API](https://github.com/plantnet/my.plantnet)<br>[pybioclip](https://github.com/Imageomics/pybioclip) |
| 空间生态与遥感 | NDVI、土地覆盖、影像筛查、栅格规划、目录选择、连通性 | `spatial-ecology-raster-lab`<br>`remote-sensing-catalog-hunt`<br>`landscape-connectivity-screen`<br>[mapbox-geospatial-operations](https://github.com/mapbox/mapbox-agent-skills) | [stac](https://github.com/BnJam/stac-mcp)<br>[gis-mcp](https://github.com/mahdin75/gis-mcp)<br>[nasa](https://github.com/ProgramComputer/NASA-MCP-server)<br>[mapbox](https://github.com/mapbox/mcp-server) |
| 气候、天气与空气质量 | 干旱、热浪、降水、空气质量、气候信号、季节预测 | `agri-climate-screen`<br>`global-change-ecology-brief`<br>[open-meteo](https://github.com/cmer81/open-meteo-mcp)<br>[open-meteo-advanced](https://github.com/cmer81/open-meteo-mcp) | [weather-open-meteo](https://github.com/cmer81/open-meteo-mcp)<br>[nasa](https://github.com/ProgramComputer/NASA-MCP-server)<br>[gis-mcp](https://github.com/mahdin75/gis-mcp) |
| 水文与淡水环境 | 水位、流量、洪水背景、流域预筛查 | `hydrology-and-flood-screen`<br>`environmental-site-screen` | [weather-open-meteo](https://github.com/cmer81/open-meteo-mcp)<br>[swiss-environment](https://github.com/malkreide/swiss-environment-mcp)<br>[noaa-tides-currents](https://github.com/RyanCardin15/NOAA-Tides-And-Currents-MCP) |
| 海岸、河口、湿地与蓝碳 | 潮位、海平面、沿海洪水、湿地选址预筛查 | `coastal-ecology-screen` | [noaa-tides-currents](https://github.com/RyanCardin15/NOAA-Tides-And-Currents-MCP)<br>[nasa](https://github.com/ProgramComputer/NASA-MCP-server)<br>[weather-open-meteo](https://github.com/cmer81/open-meteo-mcp) |
| 农业生态与农业环境 | 作物系统筛查、气候胁迫、景观背景 | `agri-climate-screen` | [weather-open-meteo](https://github.com/cmer81/open-meteo-mcp)<br>[nasa](https://github.com/ProgramComputer/NASA-MCP-server)<br>[mapbox](https://github.com/mapbox/mcp-server)<br>[gis-mcp](https://github.com/mahdin75/gis-mcp) |
| 植物、作物与微生物成长模拟 | 作物生长、灌溉、木本植被、根-茎结构、植物-土壤耦合、微生物增长、生物膜、参数拟合 | `plant-growth-model-selection`<br>`crop-growth-simulation-workflow`<br>`crop-water-and-irrigation-simulation`<br>`functional-structural-plant-modeling`<br>`root-and-rhizosphere-architecture-modeling`<br>`woody-plant-and-forest-simulation`<br>`microbial-growth-and-community-simulation`<br>`microbial-community-metabolism-simulation`<br>`microbial-biofilm-and-reactor-simulation`<br>`microbiome-timeseries-and-benchmark-simulation`<br>`plant-soil-microbe-coupled-simulation`<br>`growth-model-calibration-and-validation` | [jupyter-mcp](https://github.com/datalayer/jupyter-mcp-server)<br>[labarchives](https://github.com/SamuelBrudner/lab_archives_mcp)<br>[unit-converter](https://github.com/zazencodes/unit-converter-mcp)<br>[weather-open-meteo](https://github.com/cmer81/open-meteo-mcp)<br>[nasa](https://github.com/ProgramComputer/NASA-MCP-server)<br>[APSIM Next Generation](https://github.com/APSIMInitiative/ApsimX)<br>[PCSE / WOFOST](https://github.com/ajwdewit/pcse)<br>[AquaCrop-OSPy](https://github.com/aquacropos/aquacrop)<br>[BioCro](https://github.com/biocro/biocro)<br>[pyfao56](https://github.com/kthorp/pyfao56)<br>[CPlantBox](https://github.com/Plant-Root-Soil-Interactions-Modelling/CPlantBox)<br>[OpenAlea L-Py](https://github.com/openalea/lpy)<br>[OpenSimRoot](https://rootsystemml.github.io/ISMCROOT/opensimroot/)<br>[r3PG](https://github.com/trotsiuk/r3PG)<br>[medfate](https://github.com/emf-creaf/medfate)<br>[pyrealm](https://github.com/ImperialCollegeLondon/pyrealm)<br>[FATES](https://github.com/NGEET/fates)<br>[COBRApy](https://github.com/opencobra/cobrapy)<br>[MICOM](https://github.com/micom-dev/micom)<br>[COMETS](https://github.com/segrelab/comets)<br>[BacArena](https://github.com/euba/BacArena)<br>[Community Simulator](https://github.com/Emergent-Behaviors-in-Biology/community-simulator)<br>[NUFEB](https://github.com/nufeb/NUFEB)<br>[miaSim](https://github.com/microbiome/miaSim)<br>[CarveMe](https://github.com/cdanielmachado/carveme)<br>[PyCoMo](https://github.com/univieCUBE/PyCoMo) |
| 传统生态过程模型与主体模型 | 主体生态、流域模拟、食物网情景、森林干扰、陆地生态过程、多模型比较 | `process-model-selection`<br>`agent-based-ecology-modeling`<br>`watershed-and-ecohydrology-modeling`<br>`food-web-and-trophic-simulation`<br>`forest-landscape-disturbance-modeling`<br>`terrestrial-biosphere-and-vegetation-modeling`<br>`model-calibration-and-sensitivity`<br>`cross-model-scenario-comparison` | [NetLogo](https://github.com/NetLogo/NetLogo)<br>[Mesa](https://github.com/projectmesa/mesa)<br>[GAMA Platform](https://github.com/gama-platform/gama)<br>[DSSAT Cropping System Model](https://github.com/DSSAT/dssat-csm-os)<br>[SWAT+](https://swatplus.gitbook.io/docs/)<br>[Ecopath with Ecosim](https://ecopath.org/)<br>[LPJ-GUESS](https://web.nateko.lu.se/lpj-guess/index.html)<br>[FATES](https://github.com/NGEET/fates)<br>[ED2](https://github.com/EDmodel/ED2)<br>[Biome-BGC](https://carbonmodel.org/biome_bgc/)<br>[CENTURY / DayCent](https://www.nrel.colostate.edu/projects/century/)<br>[RHESSys](https://github.com/RHESSys/RHESSys)<br>[LANDIS-II](https://www.landis-ii.org/home)<br>[Madingley Model](https://madingley.github.io/)<br>[RangeShifter 2.0](https://rangeshifter.github.io/software/rangeshifter2.0/) |
| 湖库与水体生态过程模拟 | 分层、溶氧、藻华、营养盐情景、水质和水体生物地球化学 | `aquatic-ecodynamics-and-water-quality-modeling` | [GLM](https://github.com/AquaticEcoDynamics/GLM)<br>[glm-py](https://github.com/AquaticEcoDynamics/glm-py)<br>[FABM](https://github.com/fabm-model/fabm) |
| 淡水微宇宙、浮游群落与生物膜 | 摄食微宇宙、浮游变化、底栖生物膜、水质、荧光、显微分类 | `aquatic-microcosm-foodweb-design`<br>`zooplankton-grazing-and-plankton-dynamics`<br>`benthic-biofilm-and-periphyton-monitoring`<br>`water-quality-and-nutrient-panel`<br>`plankton-microscopy-and-auto-classification`<br>`fluorescence-spectra-and-molecular-assays` | [jupyter-mcp](https://github.com/datalayer/jupyter-mcp-server)<br>[influxdb3](https://github.com/influxdata/influxdb3_mcp_server)<br>[labarchives](https://github.com/SamuelBrudner/lab_archives_mcp)<br>[unit-converter](https://github.com/zazencodes/unit-converter-mcp)<br>[scientific-papers](https://github.com/benedict2310/Scientific-Papers-MCP)<br>[openalex-research](https://github.com/oksure/openalex-research-mcp)<br>[simple-pubmed](https://github.com/andybrandt/mcp-simple-pubmed)<br>[pubchem](https://github.com/Augmented-Nature/PubChem-MCP-Server)<br>[MorphoCut](https://github.com/morphocut/morphocut)<br>[GLM](https://github.com/AquaticEcoDynamics/GLM)<br>[glm-py](https://github.com/AquaticEcoDynamics/glm-py)<br>[FABM](https://github.com/fabm-model/fabm) |
| 封闭藻类系统与光生物反应器 | 封闭反应器设计、光径、pH / CO2 控制、污染排查、生长曲线、物质平衡 | [closed-algae-system-design](https://github.com/K-Dense-AI/claude-scientific-skills)<br>[photobioreactor-environment-control](https://github.com/K-Dense-AI/claude-scientific-skills)<br>[microalgae-strain-and-inoculation](https://github.com/K-Dense-AI/claude-scientific-skills)<br>[algal-monitoring-plan](https://github.com/K-Dense-AI/claude-scientific-skills)<br>[photobioreactor-troubleshooting](https://github.com/K-Dense-AI/claude-scientific-skills)<br>[algal-timeseries-and-mass-balance](https://github.com/K-Dense-AI/claude-scientific-skills) | [jupyter-mcp](https://github.com/datalayer/jupyter-mcp-server)<br>[influxdb3](https://github.com/influxdata/influxdb3_mcp_server)<br>[labarchives](https://github.com/SamuelBrudner/lab_archives_mcp)<br>[unit-converter](https://github.com/zazencodes/unit-converter-mcp)<br>[scientific-papers](https://github.com/benedict2310/Scientific-Papers-MCP)<br>[openalex-research](https://github.com/oksure/openalex-research-mcp)<br>[pubchem](https://github.com/Augmented-Nature/PubChem-MCP-Server) |
| 植物表型与性状提取 | 叶片性状、形态测量、腊叶标本测量、器官检测 | `plant-phenotyping-and-traits`<br>`root-phenotyping-and-rhizosphere-imaging` | [PlantCV](https://github.com/danforthcenter/plantcv)<br>[LeafMachine2](https://github.com/Gene-Weaver/LeafMachine2)<br>[RhizoVision Explorer](https://github.com/noble-research-group/RhizoVisionExplorer)<br>[RootPainter](https://github.com/Abe404/root_painter)<br>[OpenSimRoot](https://rootsystemml.github.io/ISMCROOT/opensimroot/) |
| 生态计数与分割 | 植株计数、树木计数、动物检测、树冠分割 | `ecology-counting-and-segmentation` | [DeepForest](https://github.com/weecology/DeepForest)<br>[detectree2](https://github.com/PatBall1/detectree2)<br>[TreeCountSegHeight](https://github.com/sizhuoli/TreeCountSegHeight)<br>[PyTorch-Wildlife](https://github.com/microsoft/CameraTraps) |
| 行为生态与姿态跟踪 | 运动、觅食、求偶、互动视频分析、多动物跟踪 | `animal-behavior-and-pose-tracking` | [DeepLabCut](https://github.com/DeepLabCut/DeepLabCut)<br>[SLEAP](https://github.com/talmolab/sleap)<br>[PyTorch-Wildlife](https://github.com/microsoft/CameraTraps) |
| 生态系统生物地球化学与土壤系统 | 碳、甲烷、养分循环、土壤健康、修复背景 | `ecosystem-biogeochemistry-workup`<br>`soil-health-and-nutrient-screen` | [weather-open-meteo](https://github.com/cmer81/open-meteo-mcp)<br>[nasa](https://github.com/ProgramComputer/NASA-MCP-server)<br>[eosc-data-commons](https://github.com/EOSC-Data-Commons/data-commons-mcp)<br>[dataverse](https://github.com/gdcc/mcp-dataverse)<br>[wsl-envidat](https://github.com/malkreide/wsl-envidat-mcp) |
| 环境化学与暴露 | 污染物、PFAS、微塑料、农药归趋、毒理交叉文献 | `environmental-chemistry-risk-scan`<br>`literature-multi-source-search` | [pubchem](https://github.com/Augmented-Nature/PubChem-MCP-Server)<br>[simple-pubmed](https://github.com/andybrandt/mcp-simple-pubmed)<br>[scientific-papers](https://github.com/benedict2310/Scientific-Papers-MCP)<br>[weather-open-meteo](https://github.com/cmer81/open-meteo-mcp)<br>[swiss-environment](https://github.com/malkreide/swiss-environment-mcp) |
| 微生物生态与保育遗传 | 分类、marker、组装、直系同源、BLAST 工作流 | `microbial-ecology-sequence-workflow`<br>`amplicon-and-metabolic-reconstruction-workflow` | [ncbi-datasets](https://github.com/Augmented-Nature/NCBI-Datasets-MCP-Server)<br>[bio-blast](https://github.com/bio-mcp/bio-mcp-blast)<br>[simple-pubmed](https://github.com/andybrandt/mcp-simple-pubmed)<br>[mothur](https://github.com/mothur/mothur)<br>[VSEARCH](https://github.com/torognes/vsearch)<br>[CarveMe](https://github.com/cdanielmachado/carveme)<br>[PyCoMo](https://github.com/univieCUBE/PyCoMo) |
| 生态声学 | 鸟声识别、被动声学筛查、批量音频回顾 | `ecoacoustics-screen` | [BirdNET-Analyzer](https://github.com/birdnet-team/BirdNET-Analyzer) |
| 保护与恢复 | 恢复预筛查、生态压力、场地背景 | `environmental-site-screen`<br>`ecology-evidence-synthesis` | [mapbox](https://github.com/mapbox/mcp-server)<br>[gis-mcp](https://github.com/mahdin75/gis-mcp)<br>[nasa](https://github.com/ProgramComputer/NASA-MCP-server) |
| 开放数据与科研仓储 | 数据集发现、DOI 级数据记录、复现材料 | `research-data-repository-hunt`<br>`ecology-dataset-hunt` | [dataverse](https://github.com/gdcc/mcp-dataverse)<br>[eosc-data-commons](https://github.com/EOSC-Data-Commons/data-commons-mcp)<br>[wsl-envidat](https://github.com/malkreide/wsl-envidat-mcp) |
| 区域公共环境数据 | 区域环境监测和公开研究数据 | `swiss-environment-brief` | [swiss-environment](https://github.com/malkreide/swiss-environment-mcp)<br>[wsl-envidat](https://github.com/malkreide/wsl-envidat-mcp) |
| 制图与地图表达 | 地图设计、视觉层级、报告制图 | [mapbox-cartography](https://github.com/mapbox/mapbox-agent-skills)<br>[mapbox-data-visualization-patterns](https://github.com/mapbox/mapbox-agent-skills) | [mapbox](https://github.com/mapbox/mcp-server) |

可以直接查看：

```bash
eh skills
eh mcp
```

当前版本里的 MCP 状态含义：

- `connected`：当前就是可直接工作的 in-process server
- `configured`：已经启用，但依赖远端 transport
- `cataloged`：元数据已经装进仓库，后续 transport 接上即可启用

上游来源说明见 [docs/ecology-pack.zh-CN.md](docs/ecology-pack.zh-CN.md)。

封闭藻类系统与光生物反应器相关能力说明见 [docs/algae-photobioreactor-pack.zh-CN.md](docs/algae-photobioreactor-pack.zh-CN.md)。

淡水微宇宙、浮游群落和生物膜相关能力说明见 [docs/aquatic-microcosm-pack.zh-CN.md](docs/aquatic-microcosm-pack.zh-CN.md)。

植物、作物与微生物成长模拟相关说明见 [docs/plant-growth-simulation-pack.zh-CN.md](docs/plant-growth-simulation-pack.zh-CN.md)。

这一包现在也覆盖了按植物类型拆分的建模入口，比如一年生作物、
灌溉/水分平衡、木本和森林、根际结构，以及微生物群落和生物膜模拟。

传统生态过程模型与主体模型相关说明见 [docs/ecology-process-modeling-pack.zh-CN.md](docs/ecology-process-modeling-pack.zh-CN.md)。

可以直接这样试：

```bash
eh prompt '/closed-algae-system-design flat-panel Chlorella reactor for wastewater polishing'
eh prompt '/photobioreactor-environment-control CO2 and pH control for sealed Spirulina cultivation'
eh prompt '/algal-timeseries-and-mass-balance interpret pH, dissolved oxygen, and nitrate drawdown in a batch reactor'
eh prompt '/aquatic-microcosm-foodweb-design Daphnia Chlorella Microcystis Navicula freshwater microcosm'
eh prompt '/plankton-microscopy-and-auto-classification microscope camera workflow for Daphnia rotifers and algal colonies'
eh prompt '/plant-growth-model-selection 玉米干旱加灌溉处理的成长模拟'
eh prompt '/crop-growth-simulation-workflow 水稻在高温和晚播情景下的产量变化'
eh prompt '/woody-plant-and-forest-simulation 松树林分生长和干旱胁迫'
eh prompt '/microbial-community-metabolism-simulation 根际合成菌群中的交叉喂养'
eh prompt '/microbial-growth-and-community-simulation 根际菌群在碳脉冲条件下的互作模拟'
eh prompt '/process-model-selection 流域水文、火干扰和恢复耦合问题'
eh prompt '/agent-based-ecology-modeling 破碎化农田中的传粉者移动'
eh prompt '/watershed-and-ecohydrology-modeling 施肥变化下的流域氮输出'
```

这一轮还进一步补齐了更细粒度的研究方向：

- 个体胁迫与生理生态
- 种群、入侵与元种群筛查
- 群落组装与扰动响应
- 生态系统碳、甲烷与养分循环
- 景观连通性与遥感目录选择
- 全球变化生态与气候风险
- 微生物生态、eDNA 邻近工作流与保育遗传
- 环境化学、污染物归趋与毒性筛查

## Ecology 基础工具层

当前仓库还新增了一层“生态观测与视觉基础工具”：

- 轻量原生工具：taxon / observation 查询
- 原生植物识别：通过 Pl@ntNet API
- 外部重型工具目录：表型、计数、分割、相机陷阱、生态声学

完整功能树见 [docs/ecology-basic-tools.zh-CN.md](docs/ecology-basic-tools.zh-CN.md)。

当前这个工具目录也已经纳入实验室和生物过程分析相关项，例如
`Jupyter MCP Server`、`InfluxDB 3 MCP Server`、`LabArchives MCP Server`、
`unit-converter-mcp`、`PyLabRobot` 和 `Opentrons`。

现在也纳入了植物和微生物成长模拟框架，例如
`APSIM Next Generation`、`PCSE / WOFOST`、`AquaCrop-OSPy`、`CPlantBox`、
`OpenAlea L-Py`、`pyrealm`、`COBRApy`、`MICOM`、`Tellurium`、`COPASI`、
`PySCeS`、`MDSINE2` 和 `pyPESTO`。

现在也纳入了传统生态模拟器和主体模型系统，例如
`NetLogo`、`Mesa`、`GAMA Platform`、`DSSAT Cropping System Model`、`SWAT+`、
`Ecopath with Ecosim`、`LPJ-GUESS`、`ED2`、`Biome-BGC`、`CENTURY / DayCent`、
`RHESSys`、`LANDIS-II`、`Madingley Model` 和 `RangeShifter 2.0`。

现在也纳入了显微图像、浮游生物和分子分析相关工具，例如
`Fiji / ImageJ`、`PyImageJ`、`CellProfiler`、`napari`、`ilastik`、
`EcoTaxa Python Client`、`PlanktoScope`、`QIIME 2 / Rachis Framework` 和 `DADA2`。

可以直接查看：

```bash
eh tool ListEcologyFunctions '{}'
eh tool ListEcologyToolkits '{}'
eh tool DescribeEcologyToolkit '{"name":"plantcv"}'
eh tool INaturalistSearchTaxa '{"query":"Quercus alba"}'
eh tool INaturalistSearchObservations '{"taxon_name":"Quercus alba","per_page":3}'
```

如果你有 Pl@ntNet API key：

```bash
export PLANTNET_API_KEY=your_key_here
eh tool PlantNetIdentify '{"image_paths":["leaf.jpg"],"organs":["leaf"]}'
```

## 多模态与文档分析

当前运行时已经支持把本地图片、音频、文档与视频带进主对话链路：

- 图片附件会按支持视觉输入的 provider 发送为真正的多模态内容块
- 音频附件在 OpenAI provider 上会按原生音频输入发送，其它 provider 暂时退化为带元数据的上下文
- 文档附件会先做规范化提取，在支持原生文件输入的 provider 上走更合适的格式，其余 provider 退化为纯文本分析
- 视频附件会在本地先抽取多帧图像，再进入分析链路
- REPL 的附件交互参考了 `claw-code`，支持 `/attach`、`/image`、`/audio`、`/video`、`/doc`、`/attachments`

可以直接这样使用：

```bash
# 附带本地图片
eh --provider openai --model gpt-4o --attach imgs/specimen.jpg \
  "识别这个物种，并说明你判断时看到的关键特征"

# 附带本地报告或论文
eh --attach docs/wetland_report.pdf \
  "总结这个报告的方法、主要发现，以及对湿地修复的启示"

# 附带本地音频
eh --provider openai --model gpt-4o-audio-preview --attach audio/birdsong.wav \
  "识别可能的鸟种，并描述鸣叫节律"

# 附带本地视频；框架会先抽取多帧图像供分析
eh --attach video/camera_trap.mp4 \
  "基于采样帧描述这个相机陷阱视频中的动物活动"

# 不走模型，直接做文档检查/提取
eh tool DocumentInspect '{"path":"docs/wetland_report.pdf"}'
eh tool DocumentExtract '{"path":"notes/field_log.docx","max_chars":12000}'
eh tool AudioInspect '{"path":"audio/birdsong.wav"}'
eh tool VideoInspect '{"path":"video/camera_trap.mp4"}'
eh tool VideoSampleFrames '{"path":"video/camera_trap.mp4","frame_count":6}'
```

在 REPL 中：

```text
/attach docs/wetland_report.pdf
/image imgs/specimen.jpg
/audio audio/birdsong.wav
/video video/camera_trap.mp4
/attachments
总结这些附件里的关键信息
```

## 快速开始

### 一键安装

```bash
bash scripts/install.sh
```

带开发依赖：

```bash
bash scripts/install.sh --with-dev
```

如果你更习惯 `uv`：

```bash
bash scripts/install.sh --uv
```

### 从源码安装

```bash
git clone <your-repo-url>
cd EcologyHarness

python3 -m venv .venv
source .venv/bin/activate

python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install -e .

# 可选：安装开发依赖
python3 -m pip install -e '.[dev]'
```

也可以使用 `uv`：

```bash
uv sync
uv run eh --help
```

安装完成后，推荐直接使用：

```bash
eh --help
```

`eh` 是推荐入口；`ecology-harness` 与 `python3 -m ecology_harness` 仍然可用。

如果暂时不想安装，也可以直接源码运行：

```bash
PYTHONPATH=src python3 -m ecology_harness --help
```

## 运行示例

```bash
# 查看状态
eh status

# 查看内置工具
eh tools

# 查看插件与 MCP
eh plugins
eh mcp

# 查看支持的模型来源
eh providers

# 直接使用 OpenRouter
export OPENROUTER_API_KEY="sk-or-..."
eh --provider openrouter --model openai/gpt-4.1-mini \
  "summarize this repository in 5 bullets"

# 查看生态技能
eh skills

# 直接进入 REPL
eh repl

# 单轮 prompt
eh "summarize this repository in 5 bullets"

# 显式 prompt 命令
eh prompt '/tool Read {"path":"README.md"}'

# 带本地附件的多模态 prompt
eh --attach docs/wetland_report.pdf prompt "summarize this report"

# 恢复最近一次会话
eh --resume latest repl
```

默认情况下，`--prompt` 和 `--repl` 会显示中间 trace，包括步骤、工具调用和结果摘要。可以用 `--quiet` 关闭，也可以用 `--json` 获取结构化输出。

REPL 是有状态的，新的输入会继续沿用当前会话，直到你执行 `/reset` 或 `/new`。

## REPL 常用命令

```text
/help
/status
/config
/permissions
/model sonnet
/session
/plugins
/mcp
/attach docs/wetland_report.pdf
/image imgs/specimen.jpg
/audio audio/birdsong.wav
/video video/camera_trap.mp4
/doc notes/field_log.docx
/attachments
/ecology-dataset-hunt estuary methane flux datasets 2018-2024
/ecology-evidence-synthesis blue carbon mangroves
/literature-multi-source-search wetland methane ebullition
/open-access-paper-harvest 10.1038/nclimate2616
/research-data-repository-hunt peatland carbon flux tower data
/biodiversity-data-triage alpine pollinator decline
/species-occurrence-workbench Panthera leo occurrences in Kenya
/species-photo-identification oak leaf with lobed margins
/plant-phenotyping-and-traits herbarium leaf length width area extraction
/ecology-counting-and-segmentation count trees in UAV imagery
/ecoacoustics-screen batch bird-call screening workflow
/remote-sensing-catalog-hunt 华南红树林冠层扰动
/global-change-ecology-brief alpine pollinator climate-driven range shift
/microbial-ecology-sequence-workflow drought-responsive soil microbiome markers
/environmental-chemistry-risk-scan PFAS wetland food web exposure
/tool Read {"path":"README.md"}
/tool TaskCreate {"title":"Inspect project"}
/trace off
/new
```

常用命令列表：

- `/help`
- `/status`
- `/config`
- `/permissions`
- `/model`
- `/session`
- `/cost`
- `/tools`
- `/skills`
- `/plugins`
- `/mcp`
- `/memories`
- `/tasks`
- `/providers`
- `/sandbox`
- `/attach`
- `/image`
- `/doc`
- `/audio`
- `/video`
- `/attachments`
- `/clear-attachments`
- `/trace on`
- `/trace off`
- `/new`
- `/reset`
- `/clear`
- `/quit`

## 记忆、会话与压缩

当前运行时已经具备比较完整的长任务支撑能力：

- 项目记忆和用户记忆会按当前 prompt 做相关性排序后再注入
- 会话会以结构化快照形式持久化，包含 `session_id`、时间戳、消息历史与压缩元信息
- 上下文过长时会自动生成 continuation summary，而不是简单截断
- 压缩摘要会尽量保留最近请求、工具使用、待办、关键文件与时间线

这部分实现参考了 `claw-code` 的 session 与 compaction 思路，并结合本项目的轻量 Python 架构做了适配。

## 多智能体与协同

子智能体层已经不只是简单并发调用，而是有明确的协作结构：

- 内置 agent type 包括 `planner`、`coordinator`、`coder`、`reviewer`、`researcher`、`tester`
- 委派时会附带 ownership、预期产出、依赖关系与上游上下文摘要
- 后台子智能体会跟踪 handoff、dependency 与 coordination notes
- 内部 agent 协调任务与用户任务分开持久化，避免污染主任务编号

查看内置 agent 类型：

```bash
eh prompt '/tool ListAgentTypes {}'
```

## 模型来源

当前支持的模型来源包括：

- `anthropic`
- `openai`
- `openrouter`
- `gemini`
- `kimi`
- `qwen`
- `zhipu`
- `deepseek`
- `ollama`
- `lmstudio`
- `custom`
- `mock`

可以直接查看：

```bash
eh providers
```

示例：

```bash
export ANTHROPIC_API_KEY=your_key
eh --provider anthropic --model claude-sonnet-4-6 prompt "Summarize this repository."
```

```bash
export OPENROUTER_API_KEY="sk-or-..."

# 可选，但推荐用于 OpenRouter 的应用标识
export OPENROUTER_HTTP_REFERER="https://github.com/ECNU-ICALK/Ecology-Harness"
export OPENROUTER_TITLE="Ecology Harness"

eh --provider openrouter --model openai/gpt-4.1-mini prompt "Inspect the workspace."
eh --provider openrouter --model anthropic/claude-3.7-sonnet prompt "Summarize this repository."
```

```bash
export OPENAI_API_KEY=your_key
eh --provider openai --model gpt-4o-mini --base-url https://api.openai.com/v1 prompt "Inspect the workspace."
```

```bash
eh --provider ollama --model ollama/qwen2.5-coder prompt "Inspect the workspace."
```

## 内置工具

### 文件与搜索

- `Read`
- `Write`
- `Edit`
- `Glob`
- `Grep`

### Runtime 与 Web

- `Bash`
- `WebFetch`
- `WebSearch`
- `GetDiagnostics`
- `NotebookEdit`
- `SandboxStatus`
- `Agent`
- `SendMessage`
- `CheckAgentResult`
- `ListAgentTasks`
- `ListAgentTypes`
- `PluginList`
- `PluginRead`
- `ListMcpServersTool`
- `ListMcpToolsTool`
- `MCPTool`
- `ListMcpResourcesTool`
- `ReadMcpResourceTool`
- `McpAuthTool`

### 记忆与技能

- `MemorySave`
- `MemoryList`
- `MemoryRead`
- `MemoryDelete`
- `MemorySearch`
- `Skill`
- `SkillList`
- `SkillRead`

### 任务

- `TaskCreate`
- `TaskList`
- `TaskGet`
- `TaskUpdate`

## 测试

```bash
PYTHONPATH=src python3 -m unittest discover -s tests/unit -v
```

如果已经安装了开发依赖，也可以直接运行：

```bash
python3 -m unittest discover -s tests/unit -v
```

## 项目结构

```text
src/ecology_harness/
  app.py                 # 依赖装配
  cli.py                 # CLI + REPL
  runtime/               # agent loop, providers, prompt 组装
  tools/                 # 工具协议、注册与内置工具
  memory/                # 持久记忆
  skills/                # Markdown skill 系统
  tasks/                 # 任务持久化
  permissions/           # 权限与执行策略
  agents/                # 子智能体管理
```

## 下一步方向

下一层会逐步补充生态领域能力：

- 面向数据集、表格分析、遥感、GIS 的生态工具
- 生态领域 memory schema 与 skill pack
- 面向生态推理任务的 benchmark 与 evaluation harness
