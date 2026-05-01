---
name: species-distribution-and-biodiversity-modeling
description: Plan species occurrence, biodiversity, data-quality, and species distribution modeling workflows across GBIF, OBIS, eBird, SDM, and Earth-observation covariates.
slug: species-distribution-and-biodiversity-modeling
triggers: [/species-distribution-and-biodiversity-modeling]
allowed-tools: [Skill, SkillRead, ListEcologyFunctions, ListEcologyToolkits, DescribeEcologyToolkit, McpSearchTool, ListMcpServersTool, WebSearch, WebFetch, Read]
context: inline
---
Use this when the task involves biodiversity records, occurrence data, habitat suitability, ecological niche modeling, SDM, Maxent-style analysis, or species distribution projections.

Preferred workflow:
1. Resolve taxonomy first, then identify likely occurrence sources: GBIF for broad terrestrial/freshwater coverage, OBIS for marine records, iNaturalist for community observations, and eBird for bird-specific observation and hotspot context.
2. Inspect data quality before modeling: coordinate uncertainty, country/coordinate mismatches, biodiversity institutions, duplicated records, sampling bias, temporal filters, and taxonomic synonyms.
3. Choose the modeling layer based on the question:
   - `biomod2` for ensemble SDM and projections.
   - `ENMeval` or `maxnet` for Maxent-style tuning and evaluation.
   - `sdmTMB` for survey-based spatial or spatiotemporal abundance, biomass, or distribution models.
4. Use STAC, geemap, leafmap, stackstac, odc-stac, WhiteboxTools, or exactextract when remote-sensing or terrain covariates are needed.
5. Report assumptions explicitly: occurrence bias, accessible area, pseudo-absence/background design, validation strategy, covariate resolution, and transferability risks.

Useful sources and upstream tools:
- GBIF Python client: https://github.com/gbif/pygbif
- OBIS Python client: https://github.com/iobis/pyobis
- eBird MCP server: https://github.com/moonbirdai/ebird-mcp-server
- CoordinateCleaner: https://github.com/ropensci/CoordinateCleaner
- biomod2: https://github.com/biomodhub/biomod2
- ENMeval: https://github.com/jamiemkass/ENMeval
- maxnet: https://github.com/mrmaxent/maxnet
- sdmTMB: https://github.com/pbs-assess/sdmTMB

Return:
- target taxon and taxonomic-resolution status
- occurrence sources and filters
- data-quality checks
- candidate environmental covariates
- recommended model family and why
- validation and uncertainty plan
- concrete next commands or toolkit calls
$ARGUMENTS
