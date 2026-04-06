---
name: food-web-and-trophic-simulation
description: Plan trophic, food-web, fisheries, and biomass-flow simulation workflows using Ecopath with Ecosim and related ecosystem-model framing.
slug: food-web-and-trophic-simulation
triggers: [/food-web-and-trophic-simulation]
allowed-tools: [ListEcologyToolkits, Read]
context: inline
---
Use this for trophic balance, biomass flow, fisheries, food-web structure, or ecosystem network scenario questions.

Preferred mapping:
1. `Ecopath with Ecosim` for food-web structure, ecosystem and fisheries scenarios, and trophic-balance workflows.
2. `Madingley Model` when the problem is broader ecosystem structure and multi-trophic response rather than one calibrated food-web system.
3. Pair with `literature-multi-source-search` or `ecology-evidence-synthesis` when trophic coefficients or diet matrices must be justified from literature.

Report:
- trophic system or food-web question
- recommended simulator
- biomass or diet inputs needed
- scenario levers
- outputs to compare across trophic levels
$ARGUMENTS
