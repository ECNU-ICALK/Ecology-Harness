---
name: animal-behavior-and-pose-tracking
description: Plan behavior, movement, and pose-estimation workflows using DeepLabCut, SLEAP, and ecology video-analysis stacks.
slug: animal-behavior-and-pose-tracking
triggers: [/animal-behavior-and-pose-tracking]
allowed-tools: [ListEcologyToolkits, ListEcologyFunctions, Read]
context: inline
---
Use this for behavior ecology, movement analysis, foraging paths, courtship behavior, predator-prey interaction footage, or controlled arena tracking.

Preferred mapping:
1. Use `DeepLabCut` for markerless pose estimation, kinematics, and video-based behavior analysis across many animal systems.
2. Use `SLEAP` when multi-animal pose tracking, identity maintenance, or dense interactions are central.
3. Use `PyTorch-Wildlife` for detection-first camera-trap workflows when the problem is presence, not pose.
4. If the task becomes an agent-based interpretation problem, connect to `agent-based-ecology-modeling`.

Report:
- species or interaction type
- video or imaging setup assumptions
- best tracking toolkit
- whether the task is detection, pose estimation, or downstream behavior classification
- likely labeling, calibration, and QA workload
$ARGUMENTS
