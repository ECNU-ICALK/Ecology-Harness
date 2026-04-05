---
name: community-assembly-review
description: Organize community-ecology questions about coexistence, assembly, interaction networks, disturbance, and diversity patterns.
slug: community-assembly-review
triggers: [/community-assembly-review]
allowed-tools: [Skill, SkillRead, ListMcpServersTool, ListMcpToolsTool, WebSearch, WebFetch, Read]
context: inline
---
Use this for community assembly, coexistence, trophic interaction, pollination, beta diversity, or disturbance-recovery questions.

Preferred workflow:
1. Clarify taxa, habitat, disturbance, and response variables.
2. Use `literature-multi-source-search` or `openalex-research` for synthesis and theory framing.
3. Use `gbif` for occurrence breadth and taxonomic context when observational assembly questions are involved.
4. Use `stac`, `gis-mcp`, and `mapbox` when land-cover, fragmentation, or habitat heterogeneity is central.
5. If interaction networks are agricultural or restoration-focused, chain to `environmental-site-screen` or `agri-climate-screen`.

Output:
- community system
- key ecological interactions
- likely data streams
- scale and disturbance context
- recommended analysis direction
$ARGUMENTS
