---
name: zooplankton-grazing-and-plankton-dynamics
description: Analyze grazing pressure, top-down control, and community shifts involving cladocerans, rotifers, copepods, and phytoplankton.
slug: zooplankton-grazing-and-plankton-dynamics
triggers: [/zooplankton-grazing-and-plankton-dynamics]
allowed-tools: [Skill, SkillRead, ListMcpServersTool, ListMcpToolsTool, WebSearch, WebFetch, Read]
context: inline
---
Use this for Daphnia, rotifers, copepods, and other grazer-driven questions about phytoplankton suppression, cyanobacterial release, trophic shifts, and community restructuring.

Preferred workflow:
1. Define the grazers, the prey community, and the response variables: chlorophyll, cyanobacteria share, cell density, grazing rate, or community composition.
2. Clarify whether the question is about direct consumption, selective feeding, predator-mediated shifts, or indirect nutrient effects.
3. Use `literature-multi-source-search`, `openalex-research`, `scientific-papers`, `simple-pubmed`, and `semantic-scholar` for feeding preferences, size selectivity, and microcosm precedents.
4. Use `jupyter-mcp` for growth-curve, lag, and interaction analysis when time-series are available.
5. Use `influxdb3` when dissolved oxygen, pH, turbidity, or fluorescence logs must be paired with grazer or algal observations.

Return:
- likely grazer-prey mechanisms
- variables that separate selective grazing from nutrient-side effects
- expected response signatures by grazer group
- top interpretation risks
- strongest next experiment or data split to run

$ARGUMENTS
