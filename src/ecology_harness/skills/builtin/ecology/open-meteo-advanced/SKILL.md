---
name: open-meteo-advanced
description: Use when the user wants a specific weather model, needs ensemble uncertainty ranges, requests seasonal outlooks, or asks for long-term climate projections.
---

# Open-Meteo MCP - Advanced

## Overview

Use this skill when:
- the user asks for a specific weather model
- the user wants to compare models
- forecasts beyond 16 days are needed
- ensemble uncertainty is requested
- a seasonal outlook or climate projection is needed

For everyday weather questions, use `open-meteo`.

## Model Selection Guide

| Tool | Provider | Best For |
|------|----------|----------|
| `ecmwf_forecast` | ECMWF IFS | Highest global accuracy |
| `gfs_forecast` | NOAA GFS | Global, especially Americas |
| `dwd_icon_forecast` | DWD ICON | High-resolution Europe |
| `meteofrance_forecast` | Météo-France | France and nearby regions |
| `jma_forecast` | JMA | Japan and Asia-Pacific |
| `metno_forecast` | MET Norway | Nordic region |
| `gem_forecast` | Environment Canada GEM | Canada and North America |
| `ensemble_forecast` | Multi-model | Forecast uncertainty |
| `seasonal_forecast` | ECMWF SEAS5 | 1-9 month outlook |
| `climate_projection` | CMIP6 | Scenario-based future climate |

## Key Parameters

All model-specific forecast tools share the same parameter pattern as `weather_forecast`, plus a model key where required.

### `ensemble_forecast`

Use hourly variables and derive uncertainty ranges from the member arrays.

### `seasonal_forecast`

Use for anomaly-style outlooks from 45 to 274 days.

### `climate_projection`

Use `start_date`, `end_date`, one or more CMIP6 `models`, and one or more `daily` variables.

## Examples

- "Compare DWD ICON and GFS forecasts for Berlin this week"
  1. `geocoding`
  2. Parallel calls to `dwd_icon_forecast` and `gfs_forecast`
- "Show me forecast uncertainty for Paris next week"
  1. `geocoding`
  2. `ensemble_forecast`
- "What will the climate be like in Lyon in 2040?"
  1. `geocoding`
  2. `climate_projection`

## Best Practices

- Do not use regional models outside their intended coverage.
- Treat `seasonal_forecast` as anomaly guidance rather than exact day-to-day prediction.
- Treat `climate_projection` as scenario analysis, not observed historical weather.
- Geocode first when the user provides only a location name.
