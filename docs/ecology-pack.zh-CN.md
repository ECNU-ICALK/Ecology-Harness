# Ecology Pack 来源说明

这个文档记录了当前这批农业、环境与生态能力包所采用的上游来源。

## 已安装的 Skill Bundle

- `semantic-scholar-skills`
  - 仓库：https://github.com/zongmin-yu/semantic-scholar-skills
  - 已安装：
    - `expand-references`
    - `trace-citations`
    - `paper-triage`
  - 选择原因：
    - skill bundle 自包含
    - 很适合生态、环境、农业领域的文献梳理
    - 同仓库还提供可配套的 MCP server

- `mapbox-agent-skills`
  - 仓库：https://github.com/mapbox/mapbox-agent-skills
  - 已安装：
    - `mapbox-geospatial-operations`
    - `mapbox-cartography`
    - `mapbox-data-visualization-patterns`
  - 选择原因：
    - 官方维护
    - 对空间分析、制图和可视化有直接帮助
    - Markdown + references 结构很适合当前 Harness

- `open-meteo-mcp`
  - 仓库：https://github.com/cmer81/open-meteo-mcp
  - 已安装：
    - `open-meteo`
    - `open-meteo-advanced`
  - 选择原因：
    - 维护活跃、覆盖完整
    - 自带可直接复用的 weather/climate skill
    - 对生态、农业、空气质量、洪水和气候风险问题都很有帮助

## 已安装的场景化 Skills

- 封闭藻类系统与光生物反应器 skills
  - 本地 skill 集：
    - `closed-algae-system-design`
    - `photobioreactor-environment-control`
    - `microalgae-strain-and-inoculation`
    - `algal-monitoring-plan`
    - `photobioreactor-troubleshooting`
    - `algal-timeseries-and-mass-balance`
  - 参考来源：
    - https://github.com/K-Dense-AI/claude-scientific-skills
  - 选择原因：
    - 直接对应封闭藻类培养和台式光生物反应器工作流
    - 能把文献、化学、时序、notebook 和实验记录串起来
    - 给当前 Harness 补上一层真正面向实验系统的问题处理能力

- 淡水微宇宙与浮游监测 skills
  - 本地 skill 集：
    - `aquatic-microcosm-foodweb-design`
    - `zooplankton-grazing-and-plankton-dynamics`
    - `benthic-biofilm-and-periphyton-monitoring`
    - `water-quality-and-nutrient-panel`
    - `plankton-microscopy-and-auto-classification`
    - `fluorescence-spectra-and-molecular-assays`
  - 选择原因：
    - 直接对应浮游动物-浮游植物-底栖藻类-细菌的微宇宙研究
    - 能把水质时序、显微分类、荧光信号和采样分析串在一起
    - 给当前 Harness 补上一层更贴近水生态监测的问题处理能力

- 植物、作物与微生物成长模拟 skills
  - 本地 skill 集：
    - `plant-growth-model-selection`
    - `crop-growth-simulation-workflow`
    - `crop-water-and-irrigation-simulation`
    - `functional-structural-plant-modeling`
    - `root-and-rhizosphere-architecture-modeling`
    - `woody-plant-and-forest-simulation`
    - `microbial-growth-and-community-simulation`
    - `microbial-community-metabolism-simulation`
    - `microbial-biofilm-and-reactor-simulation`
    - `microbiome-timeseries-and-benchmark-simulation`
    - `plant-soil-microbe-coupled-simulation`
    - `growth-model-calibration-and-validation`
  - 选择原因：
    - 补上了从生态观测到机理模拟之间最常见的一段空白
    - 能把一年生作物、灌溉、水分平衡、木本植被、植物结构模型、微生物动力学和参数拟合放进统一入口
    - 与现有 `jupyter-mcp`、`labarchives`、`unit-converter` 组合很自然

## 植物类型与微生物模拟补充工具层

- 按植物类型补充的工具
  - `BioCro`
  - `pyfao56`
  - `r3PG`
  - `medfate`
  - 选择原因：
    - 补上了一年生作物冠层生理、灌溉核算、森林和木本植被这些常见空缺
    - 和 `APSIM`、`WOFOST`、`AquaCrop`、`CPlantBox`、`pyrealm` 形成互补

- 微生物生态补充工具
  - `COMETS`
  - `BacArena`
  - `Community Simulator`
  - `NUFEB`
  - `Vivarium Core`
  - `miaSim`
  - 选择原因：
    - 覆盖群落代谢、资源竞争、生物膜、空间扩散和纵向微生物组 benchmark
    - 把原先的 `COBRApy`、`MICOM`、`Tellurium`、`MDSINE2` 进一步扩成更像“微生物生态模拟栈”

- 传统生态过程模型与主体模型 skills
  - 本地 skill 集：
    - `process-model-selection`
    - `agent-based-ecology-modeling`
    - `watershed-and-ecohydrology-modeling`
    - `food-web-and-trophic-simulation`
    - `forest-landscape-disturbance-modeling`
    - `terrestrial-biosphere-and-vegetation-modeling`
    - `model-calibration-and-sensitivity`
    - `cross-model-scenario-comparison`
  - 选择原因：
    - 让当前 Harness 不只做文献和数据梳理，也能进入传统生态模拟系统选型
    - 为后续 `RunNetLogoModel`、`RunSWATPlusProject` 这类 runner tools 留出清晰入口
    - 把重型编译模型放在 toolkit 层，先做到可发现、可组织、可比较

## 已安装的 MCP 目录项

- `mapbox`
  - 仓库：https://github.com/mapbox/mcp-server

- `baidu-maps`
  - 仓库：https://github.com/baidu-maps/mcp

- `weather-open-meteo`
  - 仓库：https://github.com/cmer81/open-meteo-mcp

- `nasa`
  - 仓库：https://github.com/ProgramComputer/NASA-MCP-server

- `eosc-data-commons`
  - 仓库：https://github.com/EOSC-Data-Commons/data-commons-mcp

- `semantic-scholar`
  - 仓库：https://github.com/zongmin-yu/semantic-scholar-skills

- `gis-mcp`
  - 仓库：https://github.com/mahdin75/gis-mcp

- `scientific-papers`
  - 仓库：https://github.com/benedict2310/Scientific-Papers-MCP

- `simple-pubmed`
  - 仓库：https://github.com/andybrandt/mcp-simple-pubmed

- `crossref`
  - 仓库：https://github.com/BotanicaStudios/crossref-mcp

- `unpaywall`
  - 仓库：https://github.com/ElliotPadfield/unpaywall-mcp

- `dataverse`
  - 仓库：https://github.com/gdcc/mcp-dataverse

- `noaa-tides-currents`
  - 仓库：https://github.com/RyanCardin15/NOAA-Tides-And-Currents-MCP

- `swiss-environment`
  - 仓库：https://github.com/malkreide/swiss-environment-mcp

- `wsl-envidat`
  - 仓库：https://github.com/malkreide/wsl-envidat-mcp

- `gbif`
  - 仓库：https://github.com/tyson-swetnam/gbif-mcp

- `stac`
  - 仓库：https://github.com/BnJam/stac-mcp

- `openalex-research`
  - 仓库：https://github.com/oksure/openalex-research-mcp

- `ncbi-datasets`
  - 仓库：https://github.com/Augmented-Nature/NCBI-Datasets-MCP-Server

- `bio-blast`
  - 仓库：https://github.com/bio-mcp/bio-mcp-blast

- `pubchem`
  - 仓库：https://github.com/Augmented-Nature/PubChem-MCP-Server

- `jupyter-mcp`
  - 仓库：https://github.com/datalayer/jupyter-mcp-server

- `influxdb3`
  - 仓库：https://github.com/influxdata/influxdb3_mcp_server

- `labarchives`
  - 仓库：https://github.com/SamuelBrudner/lab_archives_mcp

- `unit-converter`
  - 仓库：https://github.com/zazencodes/unit-converter-mcp

## 候选扩展

下面这些来源也很值得后续继续接入，但这次没有默认装成目录项：

- `paperclip`
  - 仓库：https://github.com/matsjfunke/paperclip
  - 原因：
    - 覆盖 EarthArXiv、EcoEvoRxiv、MarXiv、AgriXiv 等生态相关预印本源
    - 该仓库在 2025 年 12 月 16 日显示为 archived，同时当前仍更偏向自建 remote endpoint，所以不再适合作为默认高质量安装项

- FAOSTAT、USDA/NASS 这类农业公共数据 MCP
  - 原因：
    - 这一轮没有找到同等清晰、活跃、安装链路稳定的高质量 MCP 实现
    - 后续更适合优先做成我们自己的 first-party tool 或适配层

- 植物成长模拟专用 MCP
  - 原因：
    - 这一轮没有找到同等成熟、又明显适合作为默认安装项的 crop / plant-growth MCP server
    - 当前更稳的路径是把模拟框架本身编进 catalog，再通过 `jupyter-mcp` 和实验记录工具去执行

- 传统生态模拟系统专用 MCP
  - 原因：
    - 这一轮没有找到足够成熟、可直接作为默认安装项的 NetLogo、DSSAT、SWAT+、EwE、LANDIS-II、LPJ-GUESS 等 MCP server
    - 当前更稳的路径是先把官方模拟系统编进 toolkit catalog，再逐步补 runner 或 container adapter

## 说明

- 当前 Ecology Harness 版本已经能把这些远端 MCP server 作为生态目录项发现出来，但真正的远端 transport 执行能力还没有完全接通。
- 先把目录和配置装进仓库是有意义的，因为后续 transport 层补上之后，可以直接沿用这批生态配置，不需要再重做一遍。
- 这一轮优先接入的是“维护状态较好、科研工作流价值明确”的来源，没有为了数量去默认收录明显偏弱或偏陈旧的实现。
