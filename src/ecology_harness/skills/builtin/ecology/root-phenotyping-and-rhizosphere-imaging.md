---
name: root-phenotyping-and-rhizosphere-imaging
description: Plan root image analysis, root-system architecture measurement, and rhizosphere imaging workflows using RhizoVision Explorer, RootPainter, OpenSimRoot, and related toolkits.
slug: root-phenotyping-and-rhizosphere-imaging
triggers: [/root-phenotyping-and-rhizosphere-imaging]
allowed-tools: [ListEcologyToolkits, ListEcologyFunctions, Read]
context: inline
---
Use this for root crowns, washed-root scans, rhizobox images, minirhizotron-style image review, or questions about linking measured root traits to root-architecture models.

Preferred mapping:
1. Use `RhizoVision Explorer` for root-image measurement, standardized trait extraction, and root morphology review.
2. Use `RootPainter` when the bottleneck is segmentation or corrective annotation of roots against soil or noisy backgrounds.
3. Use `OpenSimRoot` when the task moves from measurement into mechanistic root-system simulation or root competition.
4. If the user needs crop-scale coupling, connect the root workflow back to `root-and-rhizosphere-architecture-modeling` or `plant-soil-microbe-coupled-simulation`.

Report:
- root imaging or root-modeling target
- best toolkit for the current stage
- likely input image or parameter requirements
- whether the task is measurement, segmentation, or mechanistic simulation
- next step to bridge from root traits into ecology or crop analysis
$ARGUMENTS
