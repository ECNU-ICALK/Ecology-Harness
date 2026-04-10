# Changelog

## 0.5.0 beta - 2026-04-11

- added `doctor`, `setup`, and read-only `explore` surfaces inspired by oh-my-codex so operators can inspect workspace health, scaffold bootstrap files, and safely explore repositories without broadening write access
- added workflow-oriented builtin skill aliases `deep-interview`, `ralplan`, and `ralph` to make clarify → plan → execute flows easier to trigger while still reusing the existing skill/runtime architecture
- expanded internal runtime coverage with workspace bootstrap management and reusable doctor tooling that can be called from both the CLI and the agent tool layer
- completed another release hardening pass with updated README guidance, focused regression tests, full unit-test coverage, and fresh wheel/sdist validation

## 0.4.1 beta - 2026-04-10

- added OpenClaw-style workspace bootstrap context loading for `STANDING_ORDERS.md`, `AGENTS.md`, `BOOTSTRAP.md`, `HEARTBEAT.md`, and related operator files so long-lived local guidance is injected without bloating the core prompt
- added lightweight heartbeat inspection and execution so a workspace can keep periodic maintenance instructions in `HEARTBEAT.md` and run them on demand without inventing a second automation stack
- expanded plugin lifecycle hooks to cover `SessionStart`, `SessionResume`, `PreRun`, `PostRun`, `OnCompaction`, and `OnError`, turning plugins into a more useful runtime event surface
- marked browser-fetched content as untrusted external input and tightened prompt guidance so web pages and browser output are treated as analyzable data rather than hidden instructions
- fixed duplicate profile/provider context injection while preserving active profile guidance in the prompt

## 0.4.0 beta - 2026-04-10

- added provider routing with fallback chains, retry handling, auxiliary model slots, and simple credential-pool strategies so long-running ecology workflows are more resilient to rate limits and flaky upstream providers
- added session titles, recaps, SQLite-backed session indexing, and stronger session recall fallback behavior for long-lived research threads
- added checkpoint capture/restore, profile management, lightweight automation scheduling, a minimal OpenAI-compatible API server surface, browser fetch/action tools, and constrained Python code execution hooks
- expanded skill governance with quarantine/approval flows, repo-based skill import, and hub auditing while keeping query-aware skill and MCP retrieval as the default selection path
- completed a broader compatibility and packaging audit covering the full unit test suite plus fresh sdist/wheel builds

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
