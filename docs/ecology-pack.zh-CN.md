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

## 已安装的 MCP 目录项

- `mapbox`
  - 仓库：https://github.com/mapbox/mcp-server

- `baidu-maps`
  - 仓库：https://github.com/baidu-maps/mcp

- `weather-open-meteo`
  - 仓库：https://github.com/isdaniel/mcp_weather_server

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

## 候选扩展

下面这些来源也很值得后续继续接入，但这次没有默认装成目录项：

- `paperclip`
  - 仓库：https://github.com/matsjfunke/paperclip
  - 原因：
    - 覆盖 EarthArXiv、EcoEvoRxiv、MarXiv、AgriXiv 等生态相关预印本源
    - 当前更推荐自建 remote endpoint，默认接入摩擦更高

- `gbif-mcp`
  - 仓库：https://github.com/tyson-swetnam/gbif-mcp
  - 原因：
    - 生物多样性观测和 GBIF literature 场景非常契合
    - 目前分发和安装链路不如本次已装入的目录项顺手

- `alex-mcp`
  - 仓库：https://github.com/drAbreu/alex-mcp
  - 原因：
    - 很适合做 OpenAlex 作者消歧和作者侧检索
    - 相比当前已装的多源文献服务，更偏窄一点

## 说明

- 当前 Ecology Harness 版本已经能把这些远端 MCP server 作为生态目录项发现出来，但真正的远端 transport 执行能力还没有完全接通。
- 先把目录和配置装进仓库是有意义的，因为后续 transport 层补上之后，可以直接沿用这批生态配置，不需要再重做一遍。
