---
name: open-meteo
description: Use when the user asks about current weather, forecasts, historical weather, air quality, marine conditions, flooding, or elevation for any location worldwide.
---

# Open-Meteo MCP

## Overview

This MCP server provides direct access to Open-Meteo weather APIs via dedicated tools. No direct API calls needed — call the appropriate tool with coordinates and the variables you want.

If you only have a city name, call `geocoding` first to obtain coordinates and timezone.

## Which Tool to Use

| Scenario | Tool |
|----------|------|
| City name -> coordinates + timezone | `geocoding` |
| Current weather or forecast (up to 16 days) | `weather_forecast` |
| Historical weather (past dates) | `weather_archive` |
| Air quality, pollutants, pollen | `air_quality` |
| Wave height, swell, sea temperature, currents | `marine_weather` |
| River discharge, flood risk (up to 210 days) | `flood_forecast` |
| Elevation / altitude of a location | `elevation` |
| Specific model, forecast > 16 days, seasonal, or climate projection | -> use `open-meteo-advanced` |

## Key Parameters

### `geocoding`

| Parameter | Required | Notes |
|-----------|----------|-------|
| `name` | Yes | City or place name |
| `count` | No | Max results (default 1) |
| `language` | No | Response language (e.g., `fr`, `en`) |

Returns `latitude`, `longitude`, `timezone`, and `country`.

### `weather_forecast`

| Parameter | Required | Notes |
|-----------|----------|-------|
| `latitude`, `longitude` | Yes | WGS84 coordinates |
| `hourly` | No* | Hourly time series |
| `daily` | No* | Day-level aggregates |
| `current` | No* | Current conditions |
| `forecast_days` | No | 1-16, default 7 |
| `past_days` | No | 1-92 recent history |
| `timezone` | No** | Required for `daily`; use `auto` |

\* At least one of `hourly`, `daily`, or `current` is required.  
\** Always set `timezone=auto` for daily variables.

### `weather_archive`

Use for older historical dates with `start_date` and `end_date`.

### `air_quality`

Common variables include `pm2_5`, `pm10`, `european_aqi`, `us_aqi`, `carbon_monoxide`, `nitrogen_dioxide`, `ozone`, `uv_index`, and pollen indicators.

### `marine_weather`

Use for `wave_height`, `wave_period`, `swell_wave_height`, `sea_surface_temperature`, and current variables.

### `flood_forecast`

Use for `river_discharge`, `river_discharge_mean`, `river_discharge_max`, and related flood variables.

## Examples

- "What is the weather like in Lyon tomorrow?"
  1. `geocoding`
  2. `weather_forecast` with `daily` variables and `timezone: "auto"`
- "Is the air quality good in Paris right now?"
  1. `geocoding`
  2. `air_quality`
- "What are the wave conditions near Biarritz this weekend?"
  1. `geocoding`
  2. `marine_weather`

## Best Practices

- Geocode first when the user provides only a place name.
- Request only the variables you need.
- Use `current` for instant conditions, `hourly` for time series, `daily` for summaries.
- For model comparison, ensemble uncertainty, seasonal outlooks, or climate projections, use `open-meteo-advanced`.
