# Ecology Pack Sources

This document records the upstream repositories used to build the first
agriculture, environment, and ecology pack for Ecology Harness.

## Installed Skill Bundles

- `semantic-scholar-skills`
  - repo: https://github.com/zongmin-yu/semantic-scholar-skills
  - installed bundles:
    - `expand-references`
    - `trace-citations`
    - `paper-triage`
  - why selected:
    - self-contained skill bundles
    - literature workflows that fit environment and ecology review work
    - optional MCP server from the same codebase

- `mapbox-agent-skills`
  - repo: https://github.com/mapbox/mapbox-agent-skills
  - installed bundles:
    - `mapbox-geospatial-operations`
    - `mapbox-cartography`
    - `mapbox-data-visualization-patterns`
  - why selected:
    - official Mapbox repository
    - practical geospatial reasoning patterns for screening and mapping workflows
    - lightweight markdown-first bundles with reference files

## Installed MCP Catalog Entries

- `mapbox`
  - repo: https://github.com/mapbox/mcp-server
  - rationale: official hosted and npm-backed geospatial MCP server

- `baidu-maps`
  - repo: https://github.com/baidu-maps/mcp
  - rationale: official China-focused mapping MCP server with strong local relevance

- `weather-open-meteo`
  - repo: https://github.com/isdaniel/mcp_weather_server
  - rationale: weather and air-quality coverage, multiple transports, clear packaging

- `nasa`
  - repo: https://github.com/ProgramComputer/NASA-MCP-server
  - rationale: useful Earth-observation, hazard, wildfire, and POWER endpoints

- `eosc-data-commons`
  - repo: https://github.com/EOSC-Data-Commons/data-commons-mcp
  - rationale: dataset discovery for open-access research assets

- `semantic-scholar`
  - repo: https://github.com/zongmin-yu/semantic-scholar-skills
  - rationale: literature MCP entry paired with the installed research skills

- `gis-mcp`
  - repo: https://github.com/mahdin75/gis-mcp
  - rationale: broad geospatial analysis server with climate, biodiversity, land-cover, and raster workflows

- `scientific-papers`
  - repo: https://github.com/benedict2310/Scientific-Papers-MCP
  - rationale: broad literature coverage across arXiv, OpenAlex, PMC, Europe PMC, bioRxiv, and CORE

- `simple-pubmed`
  - repo: https://github.com/andybrandt/mcp-simple-pubmed
  - rationale: well-scoped PubMed/PMC search and full-text retrieval server for life-science evidence workflows

- `crossref`
  - repo: https://github.com/BotanicaStudios/crossref-mcp
  - rationale: lightweight DOI metadata lookup for literature cleanup and citation normalization

- `unpaywall`
  - repo: https://github.com/ElliotPadfield/unpaywall-mcp
  - rationale: open-access fulltext discovery and PDF-text extraction for paper follow-up

- `dataverse`
  - repo: https://github.com/gdcc/mcp-dataverse
  - rationale: research-data repository search and DOI-to-Croissant conversion

- `noaa-tides-currents`
  - repo: https://github.com/RyanCardin15/NOAA-Tides-And-Currents-MCP
  - rationale: strong coastal and marine-adjacent coverage for tides, currents, sea level, and flooding

- `swiss-environment`
  - repo: https://github.com/malkreide/swiss-environment-mcp
  - rationale: high-quality public environmental data server with air, hydrology, hazards, and wildfire tools

- `wsl-envidat`
  - repo: https://github.com/malkreide/wsl-envidat-mcp
  - rationale: strong Swiss research-data source for forest, biodiversity, avalanche, and natural-hazard datasets

## Candidate Backlog

These looked promising during the expanded search but were not installed as
default catalog entries yet:

- `paperclip`
  - repo: https://github.com/matsjfunke/paperclip
  - why not default yet:
    - strong ecology-adjacent literature coverage through EarthArXiv, EcoEvoRxiv, MarXiv, and AgriXiv
    - current recommended path is self-hosting a remote endpoint, so install friction is higher

- `gbif-mcp`
  - repo: https://github.com/tyson-swetnam/gbif-mcp
  - why not default yet:
    - domain fit is excellent for biodiversity occurrences and GBIF literature
    - packaging and distribution are less turnkey than the currently installed catalog items

- `alex-mcp`
  - repo: https://github.com/drAbreu/alex-mcp
  - why not default yet:
    - useful for author disambiguation and OpenAlex-specific author workflows
    - narrower than the broader multi-source literature servers already installed

## Notes

- In the current Ecology Harness build, remote MCP transports are cataloged and
  discoverable, but only in-process MCP servers execute end-to-end.
- The catalog is still worth installing now because it lets the harness expose a
  stable ecology source inventory and keeps later transport support
  configuration-compatible.
