---
name: microbial-ecology-sequence-workflow
description: Organize microbial ecology, metagenome, phylogeny, and conservation-genetic questions using NCBI Datasets, BLAST, and literature sources.
slug: microbial-ecology-sequence-workflow
triggers: [/microbial-ecology-sequence-workflow]
allowed-tools: [Skill, SkillRead, ListMcpServersTool, ListMcpToolsTool, WebSearch, WebFetch, Read]
context: inline
---
Use this for soil, water, root-zone, pathogen, or eDNA-adjacent questions where sequence, taxonomy, or genomic context matters.

Preferred workflow:
1. Clarify the organism group, marker, genome/gene target, and study objective.
2. Use `ncbi-datasets` for taxonomy, assemblies, gene context, orthologs, or lineage checks.
3. Use `bio-blast` when the question becomes sequence-similarity or custom-database oriented.
4. Use `literature-multi-source-search` or `simple-pubmed` for methods, markers, and ecological interpretation.
5. Make it explicit when the question really needs a wet-lab or bioinformatics pipeline beyond this harness layer.

Return:
- biological system
- likely sequence or taxonomy resources
- best MCP path
- practical caveats around marker choice, contamination, reference bias, or metadata
- next analysis step
$ARGUMENTS
