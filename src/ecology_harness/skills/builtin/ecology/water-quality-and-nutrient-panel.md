---
name: water-quality-and-nutrient-panel
description: Build and interpret a sensor-and-assay panel for water temperature, light, DO, CO2, pH, conductivity, ORP, turbidity, water level, ammonia, and nitrate.
slug: water-quality-and-nutrient-panel
triggers: [/water-quality-and-nutrient-panel]
allowed-tools: [Skill, SkillRead, ListMcpServersTool, ListMcpToolsTool, ListEcologyToolkits, DescribeEcologyToolkit, WebSearch, WebFetch, Read]
context: inline
---
Use this when the main task is to design, audit, or interpret a water-quality monitoring panel in freshwater ecological systems.

Preferred workflow:
1. Group indicators into temperature and light, dissolved gases, acid-base and redox, particulates, hydraulics, and nutrients.
2. Mark which variables are continuous sensors and which are sampled assays.
3. Use `influxdb3` when the system is streaming telemetry and needs schema, query, or dashboard logic.
4. Use `unit-converter` to reconcile concentration, pressure, density, conductivity, and time units across sensors and assay reports.
5. Use `jupyter-mcp` for calibration review, drift checks, derived indicators, and time-series visualization.
6. Use `pubchem` when nutrient chemistry, trace contaminants, or physicochemical interpretation depends on compound properties.

Return:
- minimum sensor panel
- assay-based additions worth sampling daily or less frequently
- likely coupling among variables such as DO, pH, CO2, and fluorescence
- most important calibration and QC checks
- best next plot or threshold logic to implement

$ARGUMENTS
