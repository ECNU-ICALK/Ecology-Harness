# Architecture

This repository implements a lightweight but complete harness core with a package
layout that is ready to grow into a more modular `OpenHarness`-style system.

## Runtime Flow

```text
User / CLI / REPL
  -> app.py
  -> prompt_builder.py
  -> agent_loop.py
  -> session_store.py
  -> provider
  -> tool registry
  -> permissions
  -> built-in tools, plugins, MCP bridge, and state managers
  -> tool results back into the loop
```

## Current Modules

- `config/`
  - workspace-local paths
  - provider configuration
  - permission and runtime limits
- `runtime/`
  - chat message protocol
  - provider abstraction
  - mock provider
  - OpenAI-compatible provider
  - agent loop
  - managed session persistence
  - continuation-style context compaction
  - system prompt assembly
- `tools/`
  - typed tool definitions
  - registry and schema validation
  - built-in file, shell, web, memory, skill, task, agent, plugin, MCP, and claw-compat tools
- `memory/`
  - dual-scope memory store (`user` + `project`)
  - `MEMORY.md` index regeneration
  - manifest scanning and freshness warnings
  - prompt-aware memory relevance ranking
- `skills/`
  - built-in markdown skills
  - user + project skill loading
  - inline or forked skill execution
- `plugins/`
  - claw-style plugin manifest scanning
  - bundled plugin manifests and hook support
  - runtime plugin health snapshots
- `mcp/`
  - MCP server registry
  - claw-style MCP bridge naming (`mcp__server__tool`)
  - in-process MCP catalog server for compatibility assets
- `tasks/`
  - JSON-backed task store
  - status and dependency graph metadata
- `permissions/`
  - read-only / workspace-write / allow-all policy
- `sandbox/`
  - internal sandbox policy for path and command boundaries
  - optional macOS `sandbox-exec` wrapping for shell commands
- `agents/`
  - specialized agent definitions
  - threaded background subagents with result tracking and follow-up messaging
  - delegation briefs, dependency waiting, and coordination notes
  - separate internal agent-task persistence so user tasks remain clean
- `claw_compat.py`
  - curated compatibility catalog for common `claw-code` tools and bundled skills

## Design Choices

- Standard library first:
  the project runs without mandatory third-party runtime dependencies.
- Offline development path:
  the mock provider makes the full tool-use loop testable without API keys.
- Workspace-local state:
  project state lives in `.ecology_harness/`, while user-scope memory, skills, and agent
  definitions can also live in `~/.ecology_harness/`.
- Continuation over truncation:
  long contexts are compacted into structured continuation summaries instead of being blindly chopped.
- Coordination-first delegation:
  subagents inherit concise shared context, ownership, expected-output hints, and dependency metadata.
- Tool-oriented extension path:
  ecology-specific capability should arrive first as tools and skills, not as special
  cases in the runtime.

## Near-Term Extension Points

- `ecology/tools/`
  - dataset inspection
  - CSV / GeoJSON / raster helpers
  - ecological indicator calculators
- `ecology/skills/`
  - survey summarization
  - ecological reasoning patterns
  - literature extraction workflows
- `evaluation/`
  - benchmark tasks
  - scorer interfaces
  - regression datasets
