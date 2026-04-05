---
name: organismal-stress-screen
description: Screen organism-level ecology questions around stress, physiology, behavior, life-history, and acclimation using literature, climate, and sequence-ready sources.
slug: organismal-stress-screen
triggers: [/organismal-stress-screen]
allowed-tools: [Skill, SkillRead, ListMcpServersTool, ListMcpToolsTool, WebSearch, WebFetch, Read]
context: inline
---
Use this for individual-level ecology questions such as heat tolerance, drought response, salinity stress, phenotypic plasticity, migration cues, or reproductive stress.

Preferred workflow:
1. Identify the organism, stressor, response trait, and study setting.
2. Use `literature-multi-source-search` or `openalex-research` to map the evidence base.
3. Use `simple-pubmed` when the question becomes physiological, toxicological, or biomedical.
4. Use `weather-open-meteo` when local heat, cold, drought, flood, or air-quality exposure context matters.
5. Use `ncbi-datasets` only when the question clearly needs gene, genome, or ortholog context.

Report:
- focal organism and stressor
- likely response dimensions
- best evidence sources
- likely confounders such as season, acclimation, ontogeny, or geography
- next experiment, dataset, or paper set to inspect
$ARGUMENTS
