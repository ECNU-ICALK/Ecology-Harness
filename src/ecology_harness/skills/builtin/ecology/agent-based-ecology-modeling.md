---
name: agent-based-ecology-modeling
description: Plan agent-based and individual-based ecology workflows using NetLogo, Mesa, and GAMA Platform.
slug: agent-based-ecology-modeling
triggers: [/agent-based-ecology-modeling]
allowed-tools: [ListEcologyToolkits, Read]
context: inline
---
Use this for individual behavior, rule-based movement, local interaction, spatial ABM, or social-ecological system questions.

Preferred mapping:
1. `NetLogo` for rapid ecological prototypes, teaching models, BehaviorSpace experiments, and headless batch runs.
2. `Mesa` for Python-native ABM that should sit close to notebooks, data pipelines, or custom scientific code.
3. `GAMA Platform` for GIS-heavy, multi-agent, and more spatially explicit workflows with richer scenario setup.
4. If the question depends heavily on spatial layers, chain to `mapbox-geospatial-operations`, `species-occurrence-workbench`, or `remote-sensing-catalog-hunt` first.

Report:
- agent types and rules
- spatial representation
- best ABM platform
- likely calibration data
- scenario outputs to compare
$ARGUMENTS
