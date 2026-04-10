# Changelog

## 0.3.1 beta - 2026-04-10

- added `SkillHub` pack browsing and `SkillView(file_path)` progressive bundle inspection for large installed skill packs
- hardened compatibility for legacy skill snapshots so newly added hub metadata is rehydrated instead of silently degrading to generic core entries
- added public API compatibility helpers with `Settings` alias support and `SkillLoader.from_settings()` for external scripts and downstream integrations
- completed a release audit covering unit tests, wheel/sdist builds, twine metadata validation, and installed-wheel smoke checks

## 0.3.0 beta - 2026-04-10

- promoted the project to a substantially more complete beta focused on ecology-first research operations
- added query-aware skill and MCP retrieval with rewritten queries, BM25 ranking, and top-k context injection
- added historical session recall, fenced memory/profile/session context injection, and post-run review for memory and skill candidate generation
- added provider-backed memory lifecycle hooks, project/research profile layers, and trajectory export, compression, replay scoring, and benchmark summaries
- strengthened skill governance with readiness/setup metadata, snapshot caching, usage telemetry, overlap reporting, lifecycle controls, and candidate merge behavior
- expanded bundled ecology, scientific, workflow, writing, and AI research skill packs and refreshed release documentation

## 0.2.0 beta - 2026-04-06

- promoted Ecology Harness to a publishable beta package
- added bilingual README navigation and release-oriented project metadata
- packaged ecology skills, MCP catalogs, plugin assets, and toolkit catalogs into wheel and sdist outputs
- expanded ecology coverage for literature, geospatial workflows, aquatic systems, photobioreactors, process models, plant-type-specific simulation, and microbial ecology
- added multimodal document, image, audio, and video analysis support
- added CLI, REPL, sandbox, provider, memory, subagent, and packaging test coverage

## 0.1.0 - 2026-04-05

- initial public harness foundation
- basic CLI, runtime loop, tool registry, memory, skills, sandbox, and provider support
