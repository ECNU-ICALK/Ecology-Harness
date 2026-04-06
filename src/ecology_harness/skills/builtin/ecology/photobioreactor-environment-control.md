---
name: photobioreactor-environment-control
description: Plan and audit light, temperature, pH, CO2, gas exchange, mixing, and nutrient-control strategy for closed algal systems.
slug: photobioreactor-environment-control
triggers: [/photobioreactor-environment-control]
allowed-tools: [Skill, SkillRead, ListMcpServersTool, ListMcpToolsTool, ListEcologyToolkits, DescribeEcologyToolkit, WebSearch, WebFetch, Read]
context: inline
---
Use this for environmental control design in algal growth systems, especially when light, heat, pH drift, carbonate chemistry, nutrient dosing, or gas exchange are central constraints.

Preferred workflow:
1. Identify the organism, target productivity or physiology endpoint, and operational mode: batch, semi-batch, chemostat, or recirculating closed loop.
2. Separate control variables into light, temperature, pH, dissolved gases, mixing, and nutrient regime.
3. Use `literature-multi-source-search` to find strain-specific setpoints and known failure modes.
4. Use `unit-converter` for irradiance, area-normalized power, gas-flow, temperature, pressure, density, and concentration unit harmonization.
5. Use `pubchem` when micronutrients, chelators, contaminants, or chemical compatibility questions matter.
6. Use `jupyter-mcp` when you need control tables, dosing schedules, or setpoint envelopes in a notebook.
7. Use `influxdb3` when the system is instrumented and the question is about sensor layout, streaming variables, or threshold-based monitoring.

Return:
- control variables and recommended monitoring frequency
- likely setpoint ranges or decision bounds
- interactions among light, heat, pH, and CO2
- nutrient and trace-element control concerns
- which variables need active control vs passive observation
- highest-risk instability or drift mechanisms

$ARGUMENTS
