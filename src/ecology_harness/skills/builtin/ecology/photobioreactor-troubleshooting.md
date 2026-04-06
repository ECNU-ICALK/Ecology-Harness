---
name: photobioreactor-troubleshooting
description: Troubleshoot contamination, stratification, precipitation, pH drift, overheating, gas-exchange issues, and unstable growth in closed algal systems.
slug: photobioreactor-troubleshooting
triggers: [/photobioreactor-troubleshooting]
allowed-tools: [Skill, SkillRead, ListMcpServersTool, ListMcpToolsTool, ListEcologyToolkits, DescribeEcologyToolkit, WebSearch, WebFetch, Read]
context: inline
---
Use this for practical failure analysis when a closed algal reactor drifts away from expected performance.

Preferred workflow:
1. Anchor on the observed symptom first: contamination, sudden pH rise, oxygen overshoot, poor growth, wall fouling, settling, or thermal stress.
2. Separate likely causes into biology, chemistry, physics, and operations.
3. Use `literature-multi-source-search` for symptom-specific precedent and remediation patterns.
4. Use `pubchem` when precipitation chemistry, trace-metal availability, chelation, or contaminant identity matters.
5. Use `influxdb3` or `jupyter-mcp` when the diagnosis depends on time-series correlation among pH, temperature, light, dissolved oxygen, turbidity, or nutrient depletion.
6. Use `labarchives` when the troubleshooting process should be recorded as a corrective-action trail.

Return:
- observed symptom and most likely root causes
- quick checks to separate competing explanations
- immediate containment or safety actions
- likely process fix vs likely measurement artifact
- what should be logged before the next run

$ARGUMENTS
