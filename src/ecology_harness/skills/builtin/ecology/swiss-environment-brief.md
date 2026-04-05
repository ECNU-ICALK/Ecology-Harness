---
name: swiss-environment-brief
description: Build a Switzerland-focused environmental and ecology brief using swiss-environment and WSL EnviDat sources.
slug: swiss-environment-brief
triggers: [/swiss-environment-brief]
allowed-tools: [ListMcpServersTool, ListMcpToolsTool, WebSearch, WebFetch, Read]
context: inline
---
Use the Swiss public-data MCP sources when the question is geographically in Switzerland.

Preferred split:
- `swiss-environment` for live environmental conditions, flood warnings, wildfire danger, and BAFU catalog search
- `wsl-envidat` for forest, biodiversity, avalanche, and natural-hazard research datasets

Return:
- current condition signals
- relevant Swiss research datasets
- environmental or ecological watchouts
- suggested next retrieval path

If the question is not in Switzerland, say this skill is probably not the best fit and redirect to a broader ecology workflow.
$ARGUMENTS
