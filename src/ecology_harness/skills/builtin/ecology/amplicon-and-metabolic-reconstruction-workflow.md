---
name: amplicon-and-metabolic-reconstruction-workflow
description: Connect amplicon denoising, taxonomy workflows, and microbial metabolic-model reconstruction using mothur, VSEARCH, CarveMe, PyCoMo, and the existing microbial stack.
slug: amplicon-and-metabolic-reconstruction-workflow
triggers: [/amplicon-and-metabolic-reconstruction-workflow]
allowed-tools: [ListEcologyToolkits, ListEcologyFunctions, Read]
context: inline
---
Use this for 16S, ITS, marker-gene, eDNA-adjacent amplicon workflows, or when taxonomy results need to feed into microbial metabolic reconstruction.

Preferred mapping:
1. Use `mothur` or `VSEARCH` for amplicon preprocessing, clustering, chimera handling, and taxonomy-oriented sequence workflows.
2. Use `QIIME 2 / Rachis Framework` or `DADA2` when provenance-aware denoising and sequence-variant workflows are more appropriate.
3. Use `CarveMe` when the goal is genome-scale metabolic reconstruction from microbial genomes.
4. Use `PyCoMo`, `MICOM`, or `COMETS` when single models need to become community metabolism or cross-feeding analyses.
5. Make the transition from sequence data to metabolic modeling explicit, including the assumptions and missing information.

Return:
- sequence or genome input type
- best preprocessing or reconstruction tools
- where taxonomy ends and mechanistic modeling begins
- likely outputs and quality-control checkpoints
- next step for ecological interpretation
$ARGUMENTS
