---
name: aquatic-ecodynamics-and-water-quality-modeling
description: Organize lake, reservoir, and water-quality process modeling workflows using GLM, glm-py, FABM, and the existing aquatic analysis stack.
slug: aquatic-ecodynamics-and-water-quality-modeling
triggers: [/aquatic-ecodynamics-and-water-quality-modeling]
allowed-tools: [ListEcologyToolkits, ListEcologyFunctions, Read]
context: inline
---
Use this for lakes, ponds, reservoirs, algal blooms, thermal stratification, oxygen dynamics, nutrient cycling, or aquatic biogeochemistry questions.

Preferred mapping:
1. Use `GLM` for lake and reservoir hydrodynamics, thermal structure, and baseline water-column simulations.
2. Use `glm-py` when the user needs a Python-native setup, batch experiments, or reproducible notebook-driven runs around GLM.
3. Use `FABM` when the question needs modular aquatic biogeochemistry, custom ecosystem process coupling, or marine-freshwater flexibility.
4. If microscopy, fluorescence, or plankton image pipelines are central, connect to `plankton-microscopy-and-auto-classification` and `aquatic-microcosm-foodweb-design`.

Return:
- water body and management or research question
- recommended model stack
- forcing, bathymetry, water-quality, and calibration inputs needed
- outputs to compare across scenarios
- caveats around mixing, stratification, parameter identifiability, or biological complexity
$ARGUMENTS
