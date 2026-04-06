---
name: algal-timeseries-and-mass-balance
description: Analyze growth curves, sensor logs, nutrient drawdown, carbon balance, and energy efficiency for closed algal systems.
slug: algal-timeseries-and-mass-balance
triggers: [/algal-timeseries-and-mass-balance]
allowed-tools: [Skill, SkillRead, ListMcpServersTool, ListMcpToolsTool, ListEcologyToolkits, DescribeEcologyToolkit, WebSearch, WebFetch, Read]
context: inline
---
Use this when the task is to interpret time-series measurements or balance inputs and outputs in a closed algal experiment.

Preferred workflow:
1. Identify the response variables first: optical density, cell density, biomass, chlorophyll, dissolved oxygen, pH, nutrient depletion, or gas flux.
2. Specify the system boundary and the accounting frame: reactor volume, headspace, gas loop, harvest events, evaporation correction, and any dosing events.
3. Use `jupyter-mcp` for notebook-based cleaning, visualization, regression, growth-rate estimation, and derived-metric calculation.
4. Use `influxdb3` when the primary source is a telemetry database or when multiple sensors need to be queried together.
5. Use `unit-converter` when reconciling concentrations, gas-flow units, irradiance, density, or energy metrics across papers and instruments.
6. Use `scientific-papers` or `openalex-research` if benchmark ranges, methods, or interpretation frameworks are missing.

Return:
- response variables and system boundary
- recommended preprocessing and QC steps
- derived metrics to compute next
- likely nonlinearities, lags, or confounders
- what would strengthen the mass-balance claim
- best next figure, notebook, or data table to produce

$ARGUMENTS
