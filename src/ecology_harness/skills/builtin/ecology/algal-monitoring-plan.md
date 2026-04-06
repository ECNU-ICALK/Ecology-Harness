---
name: algal-monitoring-plan
description: Build a monitoring plan for closed algal systems across biomass, cell density, water chemistry, dissolved gases, light, and thermal state.
slug: algal-monitoring-plan
triggers: [/algal-monitoring-plan]
allowed-tools: [Skill, SkillRead, ListMcpServersTool, ListMcpToolsTool, ListEcologyToolkits, DescribeEcologyToolkit, WebSearch, WebFetch, Read]
context: inline
---
Use this when designing what to measure, how often to measure it, and which records matter for closed algal culture performance and troubleshooting.

Preferred workflow:
1. Split indicators into biological, chemical, and physical groups.
2. Identify whether the system is manual, sensorized, or fully logged.
3. Use `influxdb3` when the goal is real-time telemetry, sensor history, anomaly flags, or threshold dashboards.
4. Use `jupyter-mcp` when the plan needs a notebook template for data logging, QC flags, growth curves, or derived metrics.
5. Use `labarchives` when the monitoring plan should live alongside SOPs, findings, and experiment-day notes.
6. Inspect `ListEcologyToolkits` and `DescribeEcologyToolkit` when image-based counting or phenotyping should augment manual cell counts or spectrophotometry.

Return:
- minimum monitoring set
- higher-resolution optional measurements
- logging cadence and event triggers
- biological, chemical, and physical QC checks
- when to sample manually vs stream automatically
- what should be archived in notebooks for reproducibility

$ARGUMENTS
