# Agent Framework Patterns

This note records external agent-framework patterns that Ecology Harness adopts
selectively. The goal is not to clone another agent, but to keep useful ideas
that improve ecology research workflows without adding uncontrolled complexity.

## Sources Reviewed

- [Hermes Agent persistent memory](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory/)
- [Hermes Agent skills hub](https://hermes-agent.nousresearch.com/docs/skills/)
- [Hermes Agent built-in tools reference](https://hermes-agent.nousresearch.com/docs/reference/tools-reference/)
- [OpenClaw skills overview](https://openclawdoc.com/docs/skills/overview/)
- [ClawHub agent-memory security scan](https://clawhub.ai/theshadowrose/agent-memory-sr)

## Adopted Patterns

- Curated memory rather than unbounded memory. Hermes documents strict memory
  budgets, duplicate prevention, session search separation, and memory security
  scanning. Ecology Harness now keeps query-aware memory retrieval and adds
  `MemoryHealth` so large, stale, overlapping, or unsafe memories can be audited
  before they silently bloat prompts.
- Skills as higher-level workflows over low-level tools. OpenClaw describes
  skills as user-facing capabilities with manifests, lifecycle, configuration,
  and discoverability. Ecology Harness keeps this distinction through SkillHub,
  progressive `SkillView`, readiness metadata, and query-aware skill selection.
- Runtime tool availability should be explicit. Hermes separates built-in
  toolsets, MCP tools, and environment-dependent tools. Ecology Harness follows
  the same direction with MCP readiness/probe metadata and direct adapters only
  when commands are reachable.
- Persistent workspace files are powerful and risky. ClawHub's memory-skill scan
  highlights that startup files and handoff files can become persistent behavior
  modifiers. Ecology Harness therefore treats bootstrap files as trusted
  workspace guidance, adds `MEMORY_GUIDE.md`, and keeps risky memory/candidate
  content visible through governance checks.
- Self-evolution needs evidence and review gates. Automatically generated
  memories and skills now carry confidence, evidence, risk flags, and
  `requires_review` metadata. Auto-apply skips candidates that need review.

## Not Adopted

- Installing every external skill or provider by default. Ecology Harness keeps
  domain relevance, trust level, setup cost, and runtime readiness as selection
  gates.
- Letting remote/community skills directly change system prompts. Imported
  skills can be viewed and used, but durable prompt-affecting files stay under
  workspace bootstrap and memory-governance controls.
- Replacing established ecology models with model-generated simulations. The
  harness remains an orchestration layer around process models, ABMs, MCPs, and
  scientific tools.
