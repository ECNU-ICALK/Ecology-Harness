---
name: cross-model-scenario-comparison
description: Structure cross-model comparison across ABM, crop, watershed, trophic, and terrestrial process models without mixing assumptions carelessly.
slug: cross-model-scenario-comparison
triggers: [/cross-model-scenario-comparison]
allowed-tools: [ListEcologyToolkits, Read]
context: inline
---
Use this when the user wants to compare multiple ecological models or compare one scenario family across more than one simulator.

Preferred mapping:
1. Align the ecological question first: crop yield, hydrology, trophic structure, disturbance, or vegetation dynamics.
2. Compare only models with similar state variables, temporal scales, and scenario meaning.
3. Use `jupyter-mcp` for harmonizing outputs, common plots, and derived metrics.
4. Use `unit-converter` and explicit metadata review before drawing cross-model conclusions.
5. Treat differences in model structure as findings, not noise to be averaged away.

Report:
- models being compared
- common output variables
- mismatched assumptions
- normalization steps
- strongest comparison caveats
$ARGUMENTS
