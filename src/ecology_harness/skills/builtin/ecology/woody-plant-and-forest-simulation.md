---
name: woody-plant-and-forest-simulation
description: Select models for woody plants, forests, shrublands, plantations, drought stress, and stand-level vegetation dynamics.
slug: woody-plant-and-forest-simulation
triggers: [/woody-plant-and-forest-simulation]
allowed-tools: [ListEcologyToolkits, Read]
context: inline
---
Use this for forest stands, tree plantations, shrublands, woody-plant drought response, or long-term vegetation-structure questions.

Preferred mapping:
1. `r3PG` for plantation productivity, stand development, and lighter forest-growth screening.
2. `medfate` for woody vegetation water balance, plant hydraulics, and drought-response studies.
3. `ED2` when cohort structure, demography, and stand composition matter.
4. `LPJ-GUESS` for longer-term vegetation and carbon-water-nitrogen response under climate scenarios.
5. `LANDIS-II` when disturbance, management, and landscape-scale forest dynamics are the core question.

Report:
- vegetation type
- recommended simulator
- spatial and temporal scale
- forcing and inventory data needed
- biggest structural assumptions
$ARGUMENTS
