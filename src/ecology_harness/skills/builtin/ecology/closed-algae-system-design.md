---
name: closed-algae-system-design
description: Design a closed algal cultivation or photobioreactor setup around vessel geometry, materials, mixing, sampling, sterility, and mass-balance closure.
slug: closed-algae-system-design
triggers: [/closed-algae-system-design]
allowed-tools: [Skill, SkillRead, ListMcpServersTool, ListMcpToolsTool, ListEcologyToolkits, DescribeEcologyToolkit, WebSearch, WebFetch, Read]
context: inline
---
Use this for sealed algae culture vessels, flat-panel or tubular photobioreactors, benchtop closed systems, and pilot setups where geometry, closure, sterility, and material compatibility matter.

Preferred workflow:
1. Identify the objective first: biomass, lipids, carbon capture, wastewater polishing, physiology, or stress experiment.
2. Define the boundary conditions: working volume, light path, headspace, gas loop, sampling ports, sterilization path, and whether the system must stay materially closed.
3. Use `literature-multi-source-search` when the main bottleneck is reactor precedents, strain-specific setup choices, or reactor geometry tradeoffs.
4. Use `unit-converter` for light-path, area, volume, gas-flow, power, pressure, or density conversions.
5. Use `jupyter-mcp` when sizing calculations, residence-time estimates, or mass-balance tables should be worked out in a notebook.
6. Use `labarchives` when the output should be captured as a design record, SOP draft, or provenance-linked experiment plan.
7. Inspect `DescribeEcologyToolkit` for `pylabrobot` or `opentrons` if automated media prep, sterile transfer, or dosing is part of the design.

Return:
- reactor objective and boundary assumptions
- vessel geometry and material recommendations
- light-path and mixing implications
- gas, sampling, and sterilization design points
- top failure modes or contamination risks
- what should be prototyped or simulated next

$ARGUMENTS
