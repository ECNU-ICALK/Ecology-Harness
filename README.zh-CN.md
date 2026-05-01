# Ecology Harness

[English](README.md) | [简体中文](README.zh-CN.md)

Ecology Harness 是一个面向生态、环境与农业生态研究工作流的 Python Agent Harness。它把生态领域专用的能力面和稳定的通用运行时结合在一起：一方面内置了持续扩展的 skills、MCP catalogs、scientific toolkits、多模态与文档分析能力，另一方面又能支撑文献综述、空间推理、生物多样性观测、水体微宇宙、光生物反应器、显微分析、生态系统建模等具体研究任务。

除了传统的 CLI Agent 形态，这个项目还提供了 query-aware 的 skill/MCP 检索、长期记忆与历史 session 召回、有界上下文压缩、profile 驱动的工作模式，以及任务结束后沉淀可复用记忆与技能候选的自进化闭环。在这层核心能力之外，还补上了 `eh setup`、`eh doctor`、heartbeat、analytics、checkpoint、automation、渐进式 skill inspection，以及面向团队通知的飞书 / Lark、钉钉、企业微信 webhook 轻量集成，让生态能力栈可以持续增长，同时不把核心运行时拖得难以维护。也非常欢迎大家一起参与补充和完善，共同把这个生态领域的能力栈做得更完整。

当前发布版本是 `0.5.5 beta`（包版本为 `0.5.5b0`）。
变更说明见 [CHANGELOG.md](CHANGELOG.md)，参与方式见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 阅读导航

- [News](#news)
- [启动界面](#启动界面)
- [目录结构](#目录结构)
- [项目包含的能力](#项目包含的能力)
- [已安装 Skill Packs](#已安装-skill-packs)
- [Ecology Pack](#ecology-pack)
- [Ecology 基础工具层](#ecology-基础工具层)
- [多模态与文档分析](#多模态与文档分析)
- [快速开始](#快速开始)
- [运行示例](#运行示例)
- [REPL 常用命令](#repl-常用命令)
- [记忆、会话与压缩](#记忆会话与压缩)
- [多智能体与协同](#多智能体与协同)
- [模型来源](#模型来源)
- [内置工具](#内置工具)
- [测试](#测试)
- [项目结构](#项目结构)
- [下一步方向](#下一步方向)

## News

- `2026-05-01`：发布 `0.5.5 beta`，进一步明确 MCP runtime 边界，给 `ExecuteCode` 增加超时护栏，并把 provider tool schema 规范化逻辑拆成更小的运行时模块，方便后续维护。
- `2026-05-01`：发布 `0.5.4 beta`，增强 OpenAI-compatible provider 响应解析、旧 session / message 恢复，以及 BrowserAction 清理逻辑，让长任务和自定义模型网关在遇到异常上游响应时更不容易崩溃。
- `2026-04-25`：发布 `0.5.3 beta`，继续扩展生态三维能力，新增近景测量级摄影测量、LiDAR 采样设计与模拟、单木 QSM、浏览器与地理三维发布工作流，并补入 COLMAP、MicMac、HELIOS++、TreeQSM、SimpleForest、ParaView、CesiumJS。
- `2026-04-25`：发布 `0.5.2 beta`，新增面向生态三维重建、点云和生境场景可视化的一组能力，包括 OpenDroneMap、PDAL、Blender、QGIS 等相关 tools / MCP / skills。
- `2026-04-25`：发布 `0.5.1 beta`，新增 `clawhub-research`、`clawhub-ecology`、`bioskills-ecology` 三组技能包，并修复了 SkillHub / loader 会把 bundle 辅助 markdown 误识别成独立 skill 的问题。
- `2026-04-25`：新增两个生态相关的 community skill pack：`clawhub-ecology` 用于承接来自 ClawHub 的生态/碳分析外部服务型技能，`bioskills-ecology` 用于承接来自 GPTomics/bioSkills 的生态基因组学、宏基因组、系统发育与群体遗传工作流。
- `2026-04-17`：扩展轻量 integrations 层，在飞书 / Lark 之外新增钉钉与企业微信 webhook 支持，加入通用 `IntegrationNotify` 消息发送和 `eh integrations` 运维命令。
- `2026-04-25`：扫描 ClawHub 上的学术类 skill，并筛选接入一小批高价值工作流：`academic-search`、`paper-compare`、`research-paper-kb`、`virtual-reading-group`。
- `2026-04-11`：对 `0.5.0 beta` 做了一轮交付级 hardening，收紧了 workspace operator 上下文边界，让 `HEARTBEAT.md` 只在 heartbeat 运行时注入，同时把浏览器工具限制为只接受 `http(s)` URL，并完成了新一轮回归、构建与打包校验。
- `2026-04-11`：发布 `0.5.0 beta`，加入 `eh doctor`、`eh setup`、只读 `eh explore`、`eh runtime`、`eh analytics`，以及更清晰的 clarify → plan → execute 工作流别名；这些能力参考了 oh-my-codex，但仍保持现有 Ecology Harness 运行时的轻量结构。
- `2026-04-10`：发布 `0.4.1 beta`，加入了更像 OpenClaw 的 workspace bootstrap context files、轻量 heartbeat、更多 plugin 生命周期 hooks，以及对外部浏览器内容“默认不可信”的安全处理。
- `2026-04-10`：发布 `0.4.0 beta`，新增 provider 路由与 fallback、session 标题和 SQLite 索引、checkpoint、profile、automation、最小 API server、browser/code execution 工具，以及更完整的 skill 治理能力。
- `2026-04-10`：发布 `0.3.1 beta`，新增 `SkillHub` 与 `SkillView(file_path)` 渐进式 bundle 查看能力，修补旧 skill snapshot 的兼容问题，并完成一轮交付级审计，包括单元测试、wheel/sdist 打包校验和安装后 smoke test。
- `2026-04-10`：发布 `0.3.0 beta`，把 query-aware 检索、自进化闭环、profile 化记忆、trajectory 导出和 skill 治理控制整合成了一个更完整的研究型版本。
- `2026-04-06`：发布 `0.2.0 beta`，这是 Ecology Harness 第一个可正式分发的 beta 版本。

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
│   ├── automation/           # 轻量定时任务与重复工作流元数据
│   ├── config/               # 设置与运行时配置
│   ├── ecology/              # 生态领域 catalog 与扩展入口
│   ├── evaluation/           # Trajectory 导出、压缩与 benchmark 汇总
│   ├── evolution/            # 任务后复盘与自进化 candidate 生成
│   ├── integrations/         # 轻量外部集成，例如飞书 / Lark、钉钉、企业微信 webhook
│   ├── mcp/                  # MCP 注册、目录和桥接逻辑
│   ├── memory/               # 持久记忆管理
│   ├── permissions/          # 权限策略与安全检查
│   ├── plugins/              # 内置 plugin manifest 与加载器
│   ├── profiles/             # 工作模式 profile 与 profile 上下文
│   ├── runtime/              # Agent loop、provider、session、压缩
│   ├── sandbox/              # 文件、shell、网络 sandbox 辅助层
│   ├── server/               # 最小 OpenAI 兼容 API 服务层
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
- 基于 query rewrite 和 BM25 的历史 session 检索与召回
- 可配置 Sandbox、权限策略与审计
- 支持自动读取 `STANDING_ORDERS.md`、`AGENTS.md`、`BOOTSTRAP.md` 等 workspace bootstrap 上下文文件，`HEARTBEAT.md` 仅在 heartbeat 运行时注入
- `eh setup` 可为工作区脚手架生成 `AGENTS.md`、`STANDING_ORDERS.md`、`BOOTSTRAP.md`、`HEARTBEAT.md`
- `eh doctor` 可做工作区、依赖、skills 与 MCP readiness 的健康检查
- `eh runtime` 可查看实时运行快照，包括上下文压力、active profile、任务计数和子智能体状态
- `eh analytics` 可汇总近期 session、query history、trajectory 切片、skill 使用情况、automation 与 MCP 状态
- 基于工作区 `HEARTBEAT.md` 的轻量 heartbeat 查看与执行能力
- `eh explore` 提供只读探索模式，适合安全地浏览仓库和整理上下文
- 支持轻量飞书 / Lark、钉钉、企业微信 webhook 集成，可用于通知和自动化输出
- 工具注册系统与内置通用工具
- 支持本地图片、音频、文档与视频抽帧附件的多模态输入
- 内置文档分析工具，可处理 `pdf`、`docx`、`md`、`csv`、`json`、`html`、`ipynb`
- 双 scope 记忆系统与自动 `MEMORY.md`
- provider 化的记忆分层，可组合 builtin memory、project profile 和 research profile
- 多智能体与子智能体协同机制
- 任务结束后的 post-run review，可提炼 memory candidate 和 skill candidate
- 带 readiness/setup 元数据和 snapshot cache 的 Markdown skill 系统
- 带 usage 统计、生命周期状态（`active` / `deprecated` / `archived`）、重叠检测与候选合并控制的 skill 治理层
- 带 trust/audit 元数据的 skill hub 浏览能力，以及 `SkillView(file_path)` 风格的 bundle 渐进查看
- trajectory 导出、面向训练资产的压缩、replay scoring 与 benchmark 汇总能力
- MCP 与 plugin 扩展骨架
- 来自高质量上游仓库的生态技能包
- 来自高质量上游仓库的科研通用技能包，覆盖文献、统计、地理空间、可视化、omics 与实验工作流
- 来自 `obra/superpowers` 的 workflow 工程技能包
- 来自 `blader/humanizer` 的写作清理与去 AI 腔技能
- 来自 `Orchestra-Research/AI-Research-SKILLs` 的 AI 研究技能树，覆盖训练、评测、推理、MLOps、多模态与论文写作
- 面向农业、环境、生态场景的 MCP 目录
- 封闭藻类系统 / 光生物反应器 skills 与实验分析型 MCP 目录
- 覆盖 session、run、compaction 和 error 阶段的更完整 plugin lifecycle hooks
- 对 browser/web 抓取内容默认按“不可信外部输入”处理，并把浏览器工具限制为只接受 `http(s)` URL
- 标准库 `unittest` 测试集

## 已安装 Skill Packs

- `ecology`：项目内置的生态、环境与农业生态工作流技能，以及 Mapbox、Open-Meteo、Semantic Scholar 等上游 domain bundles。
- `scientific`：来自 `K-Dense-AI/claude-scientific-skills` 的科研通用技能包，包括 `literature-review`、`paper-lookup`、`geopandas`、`statistical-analysis`、`scientific-visualization`、`biopython`、`scikit-bio` 等。
- `superpowers`：来自 `obra/superpowers` 的 workflow 与工程实践技能，包括 `systematic-debugging`、`test-driven-development`、`verification-before-completion`、`writing-plans`、`using-git-worktrees` 等。
- `writing`：写作清理类技能，目前包含来自 `blader/humanizer` 的 `humanizer`。
- `ai-research`：来自 `Orchestra-Research/AI-Research-SKILLs` 的大型 AI 研究技能树，覆盖 `autoresearch`、模型架构、微调、评测、推理服务、MLOps、多模态、ML 论文写作和研究 ideation。
- `clawhub-research`：从 [ClawHub](https://clawhub.ai/) 筛选并 vendoring 进来的学术工作流技能，目前包括 `academic-search`、`paper-compare`、`research-paper-kb`、`virtual-reading-group`。
- `clawhub-ecology`：从 [ClawHub](https://clawhub.ai/) vendoring 进来的生态与碳分析外部服务型 skill，目前包括 `hiq-cortex`、`agent-earth`、`biodiversity-corridor-calculator`。这批属于 community skill，部分依赖外部 API 或在线服务。
- `bioskills-ecology`：从 [GPTomics/bioSkills](https://github.com/GPTomics/bioSkills) vendoring 进来的生态相关 genomics workflow，包括 ecological genomics、metagenomics、phylogenetics 和 population genetics 四大类。

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
| 生态三维重建与点云 | 无人机摄影测量、近景测量级摄影测量、LiDAR 预处理与模拟、单木 QSM、生境网格、浏览器与地理三维发布 | `ecology-photogrammetry-and-3d-reconstruction`<br>`close-range-ecology-photogrammetry`<br>`lidar-point-cloud-and-canopy-analysis`<br>`lidar-survey-design-and-simulation`<br>`tree-qsm-and-forest-structure-modeling`<br>`habitat-scene-3d-visualization`<br>`web-geospatial-3d-publishing` | [blender-mcp](https://github.com/ahujasid/blender-mcp)<br>[qgis-mcp](https://github.com/jjsantos01/qgis_mcp)<br>[OpenDroneMap](https://github.com/OpenDroneMap/ODM)<br>[WebODM](https://github.com/OpenDroneMap/WebODM)<br>[Meshroom](https://github.com/alicevision/Meshroom)<br>[COLMAP](https://github.com/colmap/colmap)<br>[MicMac](https://github.com/micmacIGN/micmac)<br>[PDAL](https://github.com/PDAL/PDAL)<br>[HELIOS++](https://github.com/3dgeo-heidelberg/helios)<br>[CloudCompare](https://github.com/CloudCompare/CloudCompare)<br>[Open3D](https://github.com/isl-org/Open3D)<br>[TreeQSM](https://github.com/InverseTampere/TreeQSM)<br>[SimpleForest GitLab](https://gitlab.com/SimpleForest)<br>[PyVista](https://github.com/pyvista/pyvista)<br>[ParaView](https://github.com/Kitware/ParaView)<br>[Potree](https://github.com/potree/potree)<br>[CesiumJS](https://github.com/CesiumGS/cesium)<br>[lidR](https://github.com/r-lidar/lidR)<br>[ForestTools](https://github.com/andrew-plowright/ForestTools)<br>[Blender](https://github.com/blender/blender) |
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
eh skill-hub "literature review"
eh skill-view literature-review
eh skill-view literature-review scripts/search_databases.py
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

生态三维重建、点云和生境场景说明见 [docs/ecology-3d-modeling-pack.zh-CN.md](docs/ecology-3d-modeling-pack.zh-CN.md)。

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

默认情况下，安装脚本会自动创建或复用一个专用的
`eh_py` conda 环境，并在其中安装主包；同时它还会顺手 bootstrap
一批当前常用的 MCP 基础运行时，包括 `uv/uvx`、核心 Python helper 模块，
以及放在 `~/.ecology_harness/mcp_runtimes` 下的本地 runtime checkout/build。
像 `baidu-maps/labarchives` 这类可选增强，以及 `gis-mcp` 这类更重的 GIS
依赖默认不会一起装上；如果是在交互终端里执行安装脚本，基础安装完成后会再询问你是否继续补装。

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

如果你想强制指定某个 conda 环境：

```bash
bash scripts/install.sh --conda-env eh_py
```

如果你只想安装主包，不希望同时 bootstrap MCP 运行时：

```bash
bash scripts/install.sh --skip-mcp-runtimes
```

如果你希望安装时顺手把 `uvx` 类 MCP 的缓存也预热：

```bash
bash scripts/install.sh --warm-mcp-caches
```

如果你还想安装 `baidu-maps` 和 `labarchives` 这组可选增强：

```bash
bash scripts/install.sh --with-python311-mcps
```

如果你还想安装更重的可选 GIS MCP 依赖：

```bash
bash scripts/install.sh --with-gis-mcp
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

如果你已经有自己的 conda 环境，推荐这样安装：

```bash
source activate eh_py
python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install -e .
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

# 查看实时运行快照
eh runtime

# 查看近期使用与查询历史摘要
eh analytics

# 查看工作区健康状态
eh doctor

# 初始化 bootstrap 文件
eh setup

# 只读探索仓库
eh explore "梳理这个仓库的结构和潜在风险"

# 查看内置工具
eh tools

# 查看插件与 MCP
eh plugins
eh mcp

# 配置飞书 / Lark webhook 集成
eh integrations add feishu-webhook --name default \
  --webhook-url https://open.feishu.cn/open-apis/bot/v2/hook/...

# 配置钉钉 webhook 集成
eh integrations add dingtalk-webhook --name ops \
  --webhook-url https://oapi.dingtalk.com/robot/send?access_token=... \
  --secret your-dingtalk-secret

# 配置企业微信 webhook 集成
eh integrations add wecom-webhook --name team \
  --webhook-url https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=...

# 发送一条测试消息
eh integrations test default "Ecology Harness integration test"

# 查看支持的模型来源
eh providers

# 直接使用 OpenRouter
export OPENROUTER_API_KEY="sk-or-..."
eh --provider openrouter --model openai/gpt-4.1-mini \
  "summarize this repository in 5 bullets"

# 使用新的工作流别名
eh clarify "帮我先把一个生态数据分析任务的边界理清楚"
eh ralplan "为湿地甲烷分析工作流设计执行计划"
eh ralph "执行已经批准的计划并汇报验证结果"

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
/integrations
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
- `BrowserFetch`
- `BrowserAction`
- `ExecuteCode`
- `GetDiagnostics`
- `NotebookEdit`
- `SandboxStatus`
- `SessionStats`
- `CheckpointList`
- `CheckpointRestore`
- `ProfileList`
- `ProfileSelect`
- `AutomationList`
- `AutomationCreate`
- `AutomationRunDue`
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
  automation/            # 定时任务与重复作业
  profiles/              # 工作模式 profile
  runtime/               # agent loop、provider routing、checkpoint、session、prompt 组装
  server/                # API server 入口
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
