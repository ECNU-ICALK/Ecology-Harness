---
name: microalgae-strain-and-inoculation
description: Choose microalgal strains, inoculation density, and aseptic startup strategy for closed reactors and controlled cultivation experiments.
slug: microalgae-strain-and-inoculation
triggers: [/microalgae-strain-and-inoculation]
allowed-tools: [Skill, SkillRead, ListMcpServersTool, ListMcpToolsTool, WebSearch, WebFetch, Read]
context: inline
---
Use this for strain selection, inoculum preparation, startup density, axenic culture handling, and experimental alignment between species traits and reactor goals.

Preferred workflow:
1. Clarify the use case: lipid production, biomass, carbon fixation, water polishing, physiology, or interaction experiments.
2. List constraints: salinity, temperature, light regime, nutrient regime, reactor geometry, contamination tolerance, and whether axenic culture is required.
3. Use `literature-multi-source-search` to compare candidate genera or species, inoculum ranges, and startup practices.
4. Use `openalex-research`, `scientific-papers`, `simple-pubmed`, or `semantic-scholar` for trait summaries, culturing precedents, and contamination notes.
5. Use `ncbi-datasets` when taxonomy, strain lineage, marker genes, or genome-aware screening matters.
6. Use `labarchives` when the output should become a reproducible startup protocol or culture-log entry.

Return:
- candidate strains and why they fit
- inoculation-density guidance and tradeoffs
- sterility or contamination-control requirements
- key missing metadata such as medium, salinity, or light regime
- best next paper, dataset, or culture reference to inspect

$ARGUMENTS
