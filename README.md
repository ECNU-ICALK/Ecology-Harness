# Ecology Harness

[English](README.md) | [简体中文](README.zh-CN.md)

Ecology Harness is a Python-first agent harness foundation for ecological data analysis
and reasoning workflows.

This version focuses on a complete generic harness core first, so ecology-specific tools
and skills can be added on top of a stable runtime.

## Startup Preview

![Ecology Harness startup screen](imgs/start_img.png)

## What Is Included

- package-based architecture with modular runtime boundaries
- CLI + REPL entrypoints with a claw-inspired natural command flow
- event-driven terminal UI with status header, trace stream, and session panels
- agent loop with tool-use execution
- provider layer aligned with `nano-claude-code`
- built-in support for `mock`, `anthropic`, `openai`, `gemini`, `kimi`, `qwen`, `zhipu`, `deepseek`, `ollama`, `lmstudio`, and `custom`
- managed session persistence with resume support and compaction metadata
- context compaction with continuation summaries for long conversations
- configurable sandbox policy for file, shell, and network boundaries
- tool registry with typed metadata and validation
- built-in file, shell, web, memory, skill, task, and subagent tools
- dual-scope persistent memory with relevance ranking and auto-generated `MEMORY.md` indexes
- specialized agent types, background subagents, dependency-aware coordination, and internal agent task tracking
- task tracking with status, owner, metadata, and dependency edges
- built-in markdown skills
- permission policy for read-only and workspace-write modes
- unit test suite built on the standard library

## Quick Start

### One-Command Setup

This project now supports an OpenHarness-style local install script:

```bash
bash scripts/install.sh
```

With development dependencies:

```bash
bash scripts/install.sh --with-dev
```

If you prefer `uv`:

```bash
bash scripts/install.sh --uv
```

### Install From Source

```bash
# 1. clone the repository
git clone <your-repo-url>
cd EcologyHarness

# 2. create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. upgrade packaging tools
python3 -m pip install --upgrade pip setuptools wheel

# 4. install the package in editable mode
python3 -m pip install -e .

# optional: install development extras
python3 -m pip install -e '.[dev]'
```

If you prefer `uv`, you can also do:

```bash
uv sync
uv run eh --help
```

After installation, you can enter the program directly with:

```bash
eh --help
```

`eh` is the recommended short command. `ecology-harness` and `python3 -m ecology_harness`
remain available as equivalent entrypoints.

If you do not want to install the package yet, you can also run it directly from source with:

```bash
PYTHONPATH=src python3 -m ecology_harness --help
```

### Run

After installation, these are the fastest ways to verify the harness is working:

```bash
# status overview
eh status

# list built-in tools
eh tools

# list bundled plugins and MCP servers
eh plugins
eh mcp

# list supported providers
eh providers

# one-shot prompt using the natural shorthand
eh "summarize this repository in 5 bullets"

# explicit prompt command
eh prompt '/tool Read {"path":"README.md"}'

# resume the latest saved session in the REPL
eh --resume latest repl
```

By default, `--prompt` and `--repl` show intermediate execution trace, including steps,
assistant decisions, tool calls, and tool result summaries. Use `--quiet` to suppress
that trace, or `--json` to get structured output with an `events` array.

The REPL is stateful: each new input continues the current conversation until you call
`/reset` or `/new`.

When using the installed REPL, typing `/` proactively opens slash-command suggestions, and
the bottom status bar shows the active provider, model, permissions, sandbox mode, trace
state, turn count, and tool count.

Model requests now use a separate provider timeout. By default it is disabled, so complex
tasks can wait indefinitely. If you want to restore a finite timeout, set it explicitly with
`--provider-timeout`, for example:

```bash
eh --provider-timeout 600 prompt "Analyze this large codebase and propose a refactor plan."
```

Equivalent source-mode commands:

```bash
PYTHONPATH=src python3 -m ecology_harness status
PYTHONPATH=src python3 -m ecology_harness tools
PYTHONPATH=src python3 -m ecology_harness prompt '/tool Read {"path":"README.md"}'
PYTHONPATH=src python3 -m ecology_harness --resume latest repl
```

## Examples

### Local Mock Run

This is the simplest end-to-end run and does not require any API key.

```bash
eh prompt '/tool TaskCreate {"title":"Bootstrap harness"}'

# suppress intermediate trace and print only the final result
eh --quiet prompt '/tool TaskCreate {"title":"Bootstrap harness"}'
```

### Direct Tool Execution

You can execute a built-in tool without going through the model loop.

```bash
eh tool Read '{"path":"README.md"}'
eh --describe-tool Read --json
```

### Interactive REPL

```bash
eh repl
```

Inside the REPL you can try:

```text
/help
/status
/config
/permissions
/model sonnet
/session
/plugins
/mcp
/tool Read {"path":"README.md"}
/tool TaskCreate {"title":"Inspect project"}
/trace off
/new
```

Useful REPL commands:

- `/help`
- `/status`
- `/config`
- `/permissions`
- `/model`
- `/session`
- `/cost`
- `/tools`
- `/skills`
- `/plugins`
- `/mcp`
- `/memories`
- `/tasks`
- `/providers`
- `/sandbox`
- `/trace on`
- `/trace off`
- `/new`
- `/reset`
- `/clear`
- `/quit`

### Natural CLI Patterns

You do not need to remember `-p` for normal use anymore. These all work:

```bash
eh "explain src/ecology_harness/cli.py"
eh prompt "review the current project layout"
eh status
eh config
eh model sonnet
eh permissions read-only
eh session
eh plugins
eh mcp
eh tool Read '{"path":"README.md"}'
```

Session resume is built in:

```bash
eh --resume latest repl
eh --resume latest prompt "continue from the previous discussion"
```

### Memory, Session, And Compaction

The runtime now keeps more structure around long-running work:

- project and user memories are ranked against the current prompt before being injected into the system prompt
- sessions are persisted as managed snapshots with `session_id`, timestamps, message history, and latest compaction metadata
- when context gets too large, the runtime builds a continuation summary instead of doing a blind truncation
- the compaction summary keeps recent user requests, tools used, pending work, key files, and a short timeline

This behavior is inspired by the session and compaction model in `claw-code`, adapted to the lighter Python harness here.

### Claw-Code Compatibility Bundle

This build includes a bundled compatibility layer inspired by
[`ultraworkers/claw-code`](https://github.com/ultraworkers/claw-code):

- bundled plugins:
  `claw-compat`, `example-bundled`, `sample-hooks`
- claw-style tool surface:
  `AgentTool`, `AskUserQuestionTool`, `BashTool`, `BriefTool`, `ConfigTool`,
  `EnterPlanModeTool`, `ExitPlanModeV2Tool`, `FileReadTool`, `FileEditTool`,
  `GlobTool`, `GrepTool`, `ListDirectoryTool`, `TodoWriteTool`,
  `MCPTool`, `ListMcpResourcesTool`, `ReadMcpResourceTool`, `McpAuthTool`,
  `MemoryReadTool`, `MemoryWriteTool`, `SkillTool`, `WebFetchTool`, `WebSearchTool`
- claw-inspired skills:
  `remember`, `verify`, `stuck`, `batch`, `loop`, `update-config`
- bundled in-process MCP server:
  `claw-reference`

Quick checks:

```bash
eh plugins
eh mcp
eh tool MCPTool '{"server":"claw-reference","tool":"list_tools"}'
eh tool ReadMcpResourceTool '{"server":"claw-reference","uri":"claw://skills"}'
eh tool FileReadTool '{"path":"README.md","offset":0,"limit":20}'
```

### Multi-Agent Coordination

The subagent layer is now closer to a coordination framework than a raw thread pool:

- built-in agent types include `planner` and `coordinator` in addition to `coder`, `reviewer`, `researcher`, and `tester`
- delegated agents receive a structured delegation brief with ownership, expected output, dependency info, and summarized parent context
- background agents track handoff history, dependency metadata, and coordination notes
- internal agent coordination tasks are persisted separately from user task tracking, so agent bookkeeping does not pollute user task IDs

You can inspect the built-in agent roster with:

```bash
eh prompt '/tool ListAgentTypes {}'
```

## Provider Usage

### Offline Mock Provider

The mock provider is deterministic and useful for local development.

```bash
eh prompt '/tool TaskCreate {"title":"Bootstrap"}'
```

### Supported Provider Sources

The runtime now matches the provider families supported by `nano-claude-code`:

- `anthropic` for Claude
- `openai` for GPT and o-series
- `gemini` for Google Gemini
- `kimi` for Moonshot / Kimi
- `qwen` for DashScope / Qwen
- `zhipu` for GLM
- `deepseek` for DeepSeek
- `ollama` for local Ollama
- `lmstudio` for local LM Studio
- `custom` for any OpenAI-compatible endpoint
- `mock` for deterministic offline development

You can inspect them from the CLI:

```bash
eh providers
```

### Anthropic Provider

```bash
export ANTHROPIC_API_KEY=your_key
eh \
  --provider anthropic \
  --model claude-sonnet-4-6 \
  prompt "Summarize this repository and propose 3 refactors."
```

### OpenAI-Compatible Providers

This covers `openai`, `gemini`, `kimi`, `qwen`, `zhipu`, `deepseek`, `lmstudio`, and `custom`.

```bash
export OPENAI_API_KEY=your_key
eh \
  --provider openai \
  --model gpt-4o-mini \
  --base-url https://api.openai.com/v1 \
  prompt "Summarize this repository and propose 3 refactors."
```

Example for Gemini:

```bash
export GEMINI_API_KEY=your_key
eh \
  --provider gemini \
  --model gemini-2.0-flash \
  prompt "Inspect the current workspace."
```

Example for a custom OpenAI-compatible endpoint:

```bash
export CUSTOM_API_KEY=your_key
export CUSTOM_BASE_URL=https://example.com/v1
eh \
  --provider custom \
  --model custom/my-model \
  prompt "Inspect the current workspace."
```

### Local Providers

Ollama uses its native `/api/chat` endpoint and LM Studio uses an OpenAI-compatible local endpoint.

Example for Ollama:

```bash
eh \
  --provider ollama \
  --model ollama/qwen2.5-coder \
  prompt "Inspect the current workspace."
```

Example for LM Studio:

```bash
eh \
  --provider lmstudio \
  --model lmstudio/local-model \
  prompt "Inspect the current workspace."
```

## Built-in Tools

### File and Search

- `Read`
- `Write`
- `Edit`
- `Glob`
- `Grep`

### Runtime and Web

- `Bash`
- `WebFetch`
- `WebSearch`
- `GetDiagnostics`
- `NotebookEdit`
- `SandboxStatus`
- `Agent`
- `SendMessage`
- `CheckAgentResult`
- `ListAgentTasks`
- `ListAgentTypes`
- `PluginList`
- `PluginRead`
- `ListMcpServersTool`
- `ListMcpToolsTool`
- `MCPTool`
- `ListMcpResourcesTool`
- `ReadMcpResourceTool`
- `McpAuthTool`
- `ClawToolCatalog`
- `AgentTool`
- `AskUserQuestionTool`
- `BashTool`
- `BriefTool`
- `ConfigTool`
- `EnterPlanModeTool`
- `ExitPlanModeV2Tool`
- `FileReadTool`
- `FileEditTool`
- `GlobTool`
- `GrepTool`
- `ListDirectoryTool`
- `TodoWriteTool`
- `WebFetchTool`
- `WebSearchTool`

### Memory and Skills

- `MemorySave`
- `MemoryList`
- `MemoryRead`
- `MemoryDelete`
- `MemorySearch`
- `MemoryReadTool`
- `MemoryWriteTool`
- `Skill`
- `SkillList`
- `SkillRead`
- `SkillTool`

### Tasks

- `TaskCreate`
- `TaskList`
- `TaskGet`
- `TaskUpdate`

## CLI Examples

```bash
# inspect a tool schema
python3 -m ecology_harness --describe-tool Read --json

# execute a tool directly
python3 -m ecology_harness tool Write '{"path":"notes.txt","content":"hello"}'

# run diagnostics
python3 -m ecology_harness prompt '/tool GetDiagnostics {"path":"src/ecology_harness/cli.py"}'

# save durable memory in project scope
python3 -m ecology_harness --exec-tool MemorySave --params '{"name":"Project Goal","description":"Current direction","content":"Build a nano-inspired ecology harness.","type":"project","scope":"project"}'

# list persisted state
python3 -m ecology_harness memories
python3 -m ecology_harness tasks

# inspect sandbox configuration
python3 -m ecology_harness sandbox
```

## Nano-Style Core Features

- Memory:
  user-level and project-level memory scopes, per-memory markdown files, automatic `MEMORY.md` regeneration, manifest scanning, freshness warnings, and prompt-aware relevance ranking.
- Sessions and compaction:
  managed session snapshots with resume support, compaction metadata, continuation summaries, and compressed long-context bridges.
- Agents:
  built-in specialized agent types (`coder`, `reviewer`, `researcher`, `tester`, `planner`, `coordinator`, `general-purpose`), dependency-aware coordination, follow-up messaging, structured delegation briefs, and optional git worktree isolation.
- Skills:
  markdown skills with triggers, argument substitution, tool restrictions, and inline or forked execution contexts.
- Default skills:
  `commit`, `test`, `fix`, `implement`, `simplify`, `explain`, `plan`, `review`, `debug`, `summarize`.
- Tasks:
  sequential task IDs, structured status, owner, metadata, and `blocks` / `blocked_by` dependency edges.
- Context:
  system prompt assembly includes environment info, git context, `CLAUDE.md`, available skills/agents, and durable memory context.
- Sandbox:
  internal sandbox policy guards workspace file access, shell execution roots, and optional network access; macOS `sandbox-exec` backend can be requested when available.

## Tests

```bash
# source-mode
PYTHONPATH=src python3 -m unittest discover -s tests/unit -v

# or, after installing dev extras
python3 -m unittest discover -s tests/unit -v
```

## Project Layout

```text
src/ecology_harness/
  app.py                 # dependency wiring
  cli.py                 # CLI + REPL
  runtime/               # agent loop, providers, prompt assembly
  tools/                 # tool contracts, registry, built-ins
  memory/                # persistent memory store
  skills/                # markdown skill loading
  tasks/                 # task persistence
  permissions/           # execution policy
  agents/                # subagent manager
```

## Next Direction

The next layer is ecology-specific:

- ecology tools for datasets, tabular analysis, remote sensing, and GIS
- ecology memory schemas and reusable skill packs
- benchmark and evaluation harnesses for ecological reasoning tasks
