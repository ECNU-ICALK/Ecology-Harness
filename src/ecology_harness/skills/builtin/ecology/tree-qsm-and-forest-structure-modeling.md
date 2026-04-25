---
name: tree-qsm-and-forest-structure-modeling
description: Organize single-tree and plot-scale quantitative structure modeling workflows from terrestrial laser scanning and high-quality tree point clouds.
slug: tree-qsm-and-forest-structure-modeling
triggers: [/tree-qsm-and-forest-structure-modeling]
allowed-tools: [ListEcologyToolkits, ListMcpServersTool, DescribeEcologyToolkit, Read]
context: inline
---
Use this for single-tree quantitative structure models, woody volume estimation, branch topology analysis, and plot-scale forest structure workflows built from TLS or cleaned tree point clouds.

Preferred mapping:
1. `TreeQSM` for single-tree cylinder-based quantitative structure models and branch-level topology when a clean tree cloud is available.
2. `SimpleForest` for TLS-driven tree reconstruction and practical forest-plot structural workflows, especially in Computree-style pipelines.
3. `CloudCompare` for tree-cloud cleanup, registration review, and geometry QA before QSM fitting.
4. `Blender` when QSM outputs need communication-quality visualization or structural annotation.

Report:
- tree or plot target
- point-cloud assumptions and preprocessing needs
- recommended QSM stack
- structural outputs and uncertainty notes
- expected ecological metrics
$ARGUMENTS
