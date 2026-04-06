# Closed Algae and Photobioreactor Pack

This document records the closed-algae-system and photobioreactor-specific skills
and MCP catalog entries added for Ecology Harness.

## Installed Skills

- `closed-algae-system-design`
  - purpose: reactor boundary definition, geometry, material choice, sterility, sampling, and closure assumptions
- `photobioreactor-environment-control`
  - purpose: light, temperature, pH, CO2, gas exchange, nutrient, and control-loop planning
- `microalgae-strain-and-inoculation`
  - purpose: strain fit, inoculum density, startup strategy, and aseptic handling
- `algal-monitoring-plan`
  - purpose: biology, chemistry, and physics monitoring design with logging cadence
- `photobioreactor-troubleshooting`
  - purpose: contamination, precipitation, stratification, overheating, and unstable growth diagnosis
- `algal-timeseries-and-mass-balance`
  - purpose: growth-curve analysis, sensor telemetry interpretation, and mass-balance framing

## Installed MCP Catalog Entries

- `jupyter-mcp`
  - repo: https://github.com/datalayer/jupyter-mcp-server
  - rationale: best notebook-native analysis layer for interactive calculations, plots, and reproducible run notebooks

- `influxdb3`
  - repo: https://github.com/influxdata/influxdb3_mcp_server
  - rationale: high-value telemetry layer for pH, dissolved oxygen, temperature, irradiance, turbidity, and dosing logs

- `labarchives`
  - repo: https://github.com/SamuelBrudner/lab_archives_mcp
  - rationale: useful ELN and provenance bridge for experiment records, SOPs, corrective actions, and notebook uploads

- `unit-converter`
  - repo: https://github.com/zazencodes/unit-converter-mcp
  - rationale: highly practical for reconciling mixed units across sensors, methods, and literature

## Related External Toolkits

- `PyLabRobot`
  - repo: https://github.com/PyLabRobot/pylabrobot
  - rationale: vendor-agnostic liquid handling and lab automation

- `Opentrons`
  - repo: https://github.com/Opentrons/opentrons
  - rationale: official OT-2 and Flex protocol stack for reproducible liquid-handling workflows

## Supporting Sources Used For This Pass

- `claude-scientific-skills`
  - repo: https://github.com/K-Dense-AI/claude-scientific-skills
  - specifically reviewed:
    - `protocolsio-integration`
    - `labarchive-integration`
    - `pylabrobot`
    - `opentrons-integration`
    - `statistical-analysis`
    - `scientific-visualization`
  - rationale: high-quality scientific workflow patterns that informed the new algae- and lab-facing skills

## Notes

- These additions focus on closed cultivation systems, not open ponds or broad remote-sensing ecology.
- In the current build, remote MCP transports remain cataloged unless separately connected at runtime.
- The new skills are still useful without live MCP transport because they route work through the right literature, chemistry, notebook, and telemetry layers.
