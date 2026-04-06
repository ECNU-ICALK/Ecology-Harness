# 封闭藻类系统与光生物反应器能力包

这个文档记录了本轮为 Ecology Harness 增加的“封闭藻类系统 / 光生物反应器”相关 skills、MCP 目录项和外部工具来源。

## 已安装 Skills

- `closed-algae-system-design`
  - 用途：反应器边界、几何、材质、无菌、采样与封闭性设计
- `photobioreactor-environment-control`
  - 用途：光照、温度、pH、CO2、气体交换、营养盐与控制回路设计
- `microalgae-strain-and-inoculation`
  - 用途：藻种选择、接种密度、启动策略与无菌操作
- `algal-monitoring-plan`
  - 用途：生物、化学、物理指标的监测设计与记录频率规划
- `photobioreactor-troubleshooting`
  - 用途：污染、沉淀、分层、过热、增长异常等问题诊断
- `algal-timeseries-and-mass-balance`
  - 用途：生长曲线、传感器时序与物质平衡分析

## 已安装 MCP 目录项

- `jupyter-mcp`
  - 仓库：https://github.com/datalayer/jupyter-mcp-server
  - 原因：最适合交互计算、绘图和可复现实验 notebook 的分析层

- `influxdb3`
  - 仓库：https://github.com/influxdata/influxdb3_mcp_server
  - 原因：很适合 pH、溶氧、温度、光照、浊度、加料等时序数据管理

- `labarchives`
  - 仓库：https://github.com/SamuelBrudner/lab_archives_mcp
  - 原因：很适合电子实验记录、SOP、纠偏记录和分析结果上传

- `unit-converter`
  - 仓库：https://github.com/zazencodes/unit-converter-mcp
  - 原因：对实验中的混合单位、传感器单位和文献单位统一非常实用

## 相关外部工具

- `PyLabRobot`
  - 仓库：https://github.com/PyLabRobot/pylabrobot
  - 原因：跨设备实验室自动化，适合加液、培养基配置和模拟

- `Opentrons`
  - 仓库：https://github.com/Opentrons/opentrons
  - 原因：官方 OT-2 / Flex 协议栈，适合稳定的液体处理自动化流程

## 本轮参考的上游来源

- `claude-scientific-skills`
  - 仓库：https://github.com/K-Dense-AI/claude-scientific-skills
  - 重点参考：
    - `protocolsio-integration`
    - `labarchive-integration`
    - `pylabrobot`
    - `opentrons-integration`
    - `statistical-analysis`
    - `scientific-visualization`
  - 原因：高质量科研工作流模式，对本轮新增的藻类与实验室技能设计帮助很大

## 说明

- 这一轮重点是封闭培养系统，不是开放池塘或大尺度遥感生态。
- 当前版本里远端 MCP transport 仍然以目录发现为主，真正连通后才能直接执行。
- 即便 MCP 还没接通，这批 skills 也仍然有价值，因为它们能把问题正确路由到文献、化学、notebook 和时序分析层。
