---
name: ecoacoustics-screen
description: Screen acoustic-species-identification workflows using BirdNET and related ecological monitoring context.
slug: ecoacoustics-screen
triggers: [/ecoacoustics-screen]
allowed-tools: [ListEcologyToolkits, ListEcologyFunctions, Read]
context: inline
---
Use this for bird-audio identification, passive acoustic monitoring, or large-batch screening of recordings.

Preferred mapping:
1. Use `BirdNET-Analyzer` for bird sound recognition and scientific audio processing.
2. If the user needs species context, chain to `INaturalistSearchTaxa` or `literature-multi-source-search`.
3. Make it explicit when the task requires a full acoustic workflow rather than a quick screening answer.

Return:
- acoustic target
- likely best toolkit
- expected recording format or workflow
- next validation step
$ARGUMENTS
