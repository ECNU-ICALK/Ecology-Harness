---
name: movement-ecology-and-telemetry-analysis
description: Plan animal telemetry, movement-track cleaning, Movebank import, home-range estimation, and step-selection workflows.
slug: movement-ecology-and-telemetry-analysis
triggers: [/movement-ecology-and-telemetry-analysis]
allowed-tools: [Skill, SkillRead, ListEcologyFunctions, ListEcologyToolkits, DescribeEcologyToolkit, WebSearch, WebFetch, Read]
context: inline
---
Use this when the task involves animal movement, GPS collars, telemetry, Movebank data, migration corridors, home ranges, step-selection, or habitat-selection analysis.

Preferred workflow:
1. Inventory the data: animal ID, timestamp, coordinate reference system, fix interval, location error, deployment metadata, behavioral states, and environmental covariates.
2. Clean and standardize tracks before modeling: impossible speeds, duplicate timestamps, missing fixes, CRS, daylight/timezone, and deployment boundaries.
3. Choose the analysis layer:
   - `move2` for movement data handling and Movebank-oriented ingestion.
   - `ctmm` for autocorrelation-aware continuous-time movement models and AKDE home ranges.
   - `amt` for step generation, random steps, and integrated step-selection or habitat-selection workflows.
4. Connect movement outputs to ecological questions: corridor use, home-range overlap, habitat preference, dispersal, migration timing, or management boundaries.
5. Report model assumptions around independence, autocorrelation, fix interval, location error, and sampling bias.

Useful sources and upstream tools:
- ctmm: https://github.com/ctmm-initiative/ctmm
- amt: https://github.com/jmsigner/amt
- move2: https://gitlab.com/bartk/move2

Return:
- data-readiness checklist
- recommended movement-analysis package and why
- cleaning and filtering steps
- model plan and diagnostics
- ecological interpretation outputs
$ARGUMENTS
