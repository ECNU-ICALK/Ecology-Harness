---
name: aquatic-microcosm-foodweb-design
description: Design enclosed freshwater microcosms that combine zooplankton, phytoplankton, benthic algae, and decomposer bacteria.
slug: aquatic-microcosm-foodweb-design
triggers: [/aquatic-microcosm-foodweb-design]
allowed-tools: [Skill, SkillRead, ListMcpServersTool, ListMcpToolsTool, ListEcologyToolkits, DescribeEcologyToolkit, WebSearch, WebFetch, Read]
context: inline
---
Use this for freshwater or shallow-water microcosms that include trophic interactions among zooplankton, phytoplankton, benthic algae, and bacterial decomposers.

Preferred workflow:
1. Identify the focal mechanism first: grazing control, cyanobacterial suppression, trophic cascades, benthic-pelagic coupling, decomposition, or nutrient recycling.
2. Separate the system into compartments: water column, benthic surface, biofilm, headspace, and sampling schedule.
3. Specify the biological cast clearly, such as Daphnia, Brachionus, Cyclops, Chlorella, Microcystis, Navicula, Cladophora, and nitrifying or Bacillus-based decomposer mixes.
4. Use `literature-multi-source-search` for species-combination precedents, stocking ratios, and microcosm protocols.
5. Use `unit-converter`, `jupyter-mcp`, and `influxdb3` when densities, grazing ratios, exposure regimes, or monitoring cadence need to be formalized.
6. Use `labarchives` when the result should become a reproducible microcosm design record.

Return:
- system compartments and food-web roles
- candidate stocking or inoculation logic
- highest-priority interaction hypotheses
- monitoring plan needed to resolve the mechanism
- major confounders such as sedimentation, wall growth, contamination, or top-down collapse

$ARGUMENTS
