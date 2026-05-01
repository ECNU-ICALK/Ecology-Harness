---
name: ecoacoustic-monitoring-and-bird-observation
description: Combine passive acoustic monitoring, bird sound classifiers, eBird observations, and ecological interpretation for avian and broader bioacoustic surveys.
slug: ecoacoustic-monitoring-and-bird-observation
triggers: [/ecoacoustic-monitoring-and-bird-observation]
allowed-tools: [Skill, SkillRead, ListEcologyFunctions, ListEcologyToolkits, DescribeEcologyToolkit, McpSearchTool, ListMcpServersTool, WebSearch, WebFetch, Read]
context: inline
---
Use this when the task involves bird calls, passive acoustic monitoring, ecoacoustic indices, audio classification, or linking sound detections to field-observation context.

Preferred workflow:
1. Clarify the monitoring design: site coordinates, recording schedule, device type, target taxa, season, habitat, and whether the goal is detection, richness proxy, occupancy, or behavior.
2. Choose the tool:
   - `BirdNET-Analyzer` for broad bird sound recognition and batch screening.
   - `OpenSoundscape` for custom ecoacoustic classifiers, preprocessing, and trainable pipelines.
   - `eBird MCP Server` for recent observations, nearby observations, hotspots, and taxonomy context.
3. Treat audio detections as evidence, not ground truth. Ask for confidence thresholds, manual validation sample size, false-positive review, background noise, and time-of-day bias.
4. For ecological reporting, connect detections to habitat, weather, migration timing, and local bird-observation context rather than only listing species.
5. When evidence is weak, recommend a validation subset and a confusion-matrix or precision-review workflow before downstream occupancy or trend analysis.

Useful sources and upstream tools:
- BirdNET-Analyzer: https://github.com/birdnet-team/BirdNET-Analyzer
- OpenSoundscape: https://github.com/kitzeslab/opensoundscape
- eBird MCP server: https://github.com/moonbirdai/ebird-mcp-server

Return:
- monitoring objective and data inventory
- recommended acoustic toolchain
- eBird or local observation context to retrieve
- validation and threshold plan
- expected outputs such as detection table, review clips, occupancy-ready table, or site summary
$ARGUMENTS
