---
name: microbial-biofilm-and-reactor-simulation
description: Organize microbial biofilm, reactor, spatial diffusion, and custom process-based simulation workflows.
slug: microbial-biofilm-and-reactor-simulation
triggers: [/microbial-biofilm-and-reactor-simulation]
allowed-tools: [ListEcologyToolkits, Read]
context: inline
---
Use this for biofilms, reactor systems, nutrient gradients, inhibition, spatial structure, or custom process compositions in microbial ecology.

Preferred mapping:
1. `NUFEB` for individual-based biofilms, 3D microbial communities, and diffusion-limited systems.
2. `Tellurium`, `COPASI`, or `PySCeS` for mechanistic ODE and reaction-network reactor models.
3. `Vivarium Core` for custom multi-process or hybrid microbial simulations that combine several process modules.
4. `COMETS` if metabolite diffusion and spatial community metabolism are more important than biofilm mechanics.

Report:
- reactor or habitat type
- recommended simulator
- spatial structure assumptions
- measurements needed
- output variables to track
$ARGUMENTS
