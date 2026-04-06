---
name: species-photo-identification
description: Identify species or higher taxa from field photos by combining Pl@ntNet, iNaturalist, and cataloged biodiversity vision toolkits.
slug: species-photo-identification
triggers: [/species-photo-identification]
allowed-tools: [PlantNetIdentify, INaturalistSearchTaxa, INaturalistSearchObservations, ListEcologyToolkits, ListEcologyFunctions, Read]
context: inline
---
Use this when the user has one or more organism photos and wants an identification workflow.

Preferred order:
1. If the image is clearly a plant and `PLANTNET_API_KEY` is available, use `PlantNetIdentify`.
2. Use `INaturalistSearchTaxa` to normalize the winning name or inspect close taxonomic alternatives.
3. Use `INaturalistSearchObservations` to check whether the candidate taxon is plausible in the target place or season.
4. If the image is not a plant or if local/offline inference is preferred, inspect `ListEcologyToolkits` for `pybioclip`, `nature-id`, or a more specialized toolkit.

Return:
- likely taxon
- confidence caveats
- whether the result is species-level or higher-taxon only
- what source or toolkit should be used next if confidence is weak
$ARGUMENTS
