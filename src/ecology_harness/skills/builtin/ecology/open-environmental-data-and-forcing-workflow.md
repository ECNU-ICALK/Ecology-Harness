---
name: open-environmental-data-and-forcing-workflow
description: Assemble hydrology, soil, air-quality, weather, and Earth-observation forcing data for ecology, agroecology, SDM, and watershed workflows.
slug: open-environmental-data-and-forcing-workflow
triggers: [/open-environmental-data-and-forcing-workflow]
allowed-tools: [Skill, SkillRead, ListEcologyFunctions, ListEcologyToolkits, DescribeEcologyToolkit, McpSearchTool, ListMcpServersTool, WebSearch, WebFetch, Read]
context: inline
---
Use this when the task asks for environmental covariates, model forcing files, USGS water data, soil information, air quality, STAC scenes, Google Earth Engine layers, or an OpenAPI adapter for a public environmental API.

Preferred workflow:
1. Translate the scientific question into required forcing variables: weather, flow, water quality, soil, land cover, terrain, air pollutants, or remote-sensing indices.
2. Choose sources:
   - `dataretrieval-python` for USGS NWIS and Water Quality Portal data.
   - `PyGeoHydro` for watershed and hydrography web-service access.
   - `soilDB` and `SoilGrids API` for site and gridded soil context.
   - `OpenAQ Python Client` for air-quality observations.
   - `pystac-client`, `stackstac`, `odc-stac`, `geemap`, and `leafmap` for Earth-observation discovery and loading.
   - `WhiteboxTools` and `exactextract` for terrain derivatives and raster-to-tabular feature extraction.
   - `openapi-environment-adapter` when a useful environmental REST API has an OpenAPI spec but no dedicated MCP server.
3. Keep units and coordinate systems explicit. Record source, endpoint, time range, spatial resolution, CRS, aggregation window, and missing-data handling.
4. Build model-ready outputs only after checking temporal alignment, spatial alignment, and licensing or API limits.

Useful sources and upstream tools:
- dataretrieval-python: https://github.com/DOI-USGS/dataretrieval-python
- PyGeoHydro: https://github.com/hyriver/pygeohydro
- soilDB: https://github.com/ncss-tech/soilDB
- SoilGrids: https://soilgrids.org/
- OpenAQ Python client: https://github.com/openaq/openaq-python
- pystac-client: https://github.com/stac-utils/pystac-client
- stackstac: https://github.com/gjoseph92/stackstac
- odc-stac: https://github.com/opendatacube/odc-stac
- geemap: https://github.com/gee-community/geemap
- leafmap: https://github.com/opengeos/leafmap
- WhiteboxTools: https://github.com/jblindsay/whitebox-tools
- exactextract: https://github.com/isciences/exactextract
- OpenAPI MCP Server: https://github.com/ivo-toby/mcp-openapi-server

Return:
- variables and sources
- spatial/temporal alignment plan
- API or MCP access route
- units, CRS, and resolution notes
- model-ready table/raster/file plan
- validation checks before simulation or modeling
$ARGUMENTS
