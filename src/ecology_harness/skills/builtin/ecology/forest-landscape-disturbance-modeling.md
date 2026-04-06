---
name: forest-landscape-disturbance-modeling
description: Plan forest landscape, succession, fire, harvest, and disturbance workflows using LANDIS-II and related terrestrial process models.
slug: forest-landscape-disturbance-modeling
triggers: [/forest-landscape-disturbance-modeling]
allowed-tools: [ListEcologyToolkits, Read]
context: inline
---
Use this for forest succession, disturbance regimes, fire, harvest, management treatment, or long-term landscape forecasting.

Preferred mapping:
1. `LANDIS-II` for explicit forest landscape, disturbance, and management scenarios over long time horizons.
2. `ED2` if demographic vegetation structure and ecosystem response matter more than explicit disturbance extensions.
3. Use `nasa`, `stac`, or `remote-sensing-catalog-hunt` when disturbance mapping and remote-sensing context are required.

Report:
- forest landscape question
- disturbance or management regime
- recommended model
- spatial and temporal scale
- outputs relevant to management or restoration
$ARGUMENTS
