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

## 说明

- 当前 Ecology Harness 版本已经能把这些远端 MCP server 作为生态目录项发现出来，但真正的远端 transport 执行能力还没有完全接通。
- 先把目录和配置装进仓库是有意义的，因为后续 transport 层补上之后，可以直接沿用这批生态配置，不需要再重做一遍。
- 这一轮优先接入的是“维护状态较好、科研工作流价值明确”的来源，没有为了数量去默认收录明显偏弱或偏陈旧的实现。
