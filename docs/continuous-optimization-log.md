# Continuous Optimization Log

This log records module-by-module maintenance passes so larger cleanup work
stays reviewable and does not become a vague rewrite.

## 2026-05-02

### Feature 1: Capability Readiness Preflight

- Value: users can ask a domain question and see relevant skills, MCP servers,
  built-in tools, readiness states, setup gaps, and next actions before the
  agent attempts a fragile execution path.
- MVP: added the read-only `CapabilityReadinessReport` tool plus the
  `eh capability "<query>"` and `/capability <query>` entry points. It reuses
  the existing query-aware skill and MCP retrieval, adds lightweight built-in
  tool matching, and renders a concise preflight report with recommendations.
- Files: `src/ecology_harness/tools/builtin/capability_tools.py`,
  `src/ecology_harness/tools/builtin/__init__.py`,
  `src/ecology_harness/cli.py`, `README.md`,
  `tests/unit/test_capability_tools.py`, `tests/unit/test_cli.py`.
- Validation: `PYTHONPATH=src python3 -m unittest tests.unit.test_capability_tools tests.unit.test_skills tests.unit.test_mcp_retrieval -q`
  passed with 34 tests; after adding the CLI entry point,
  `PYTHONPATH=src python3 -m unittest tests.unit.test_capability_tools tests.unit.test_cli -q`
  passed with 45 tests. Final regression for this pass:
  `PYTHONPATH=src python3 -m unittest discover -s tests/unit -q` passed with
  247 tests, package build passed, and `twine check` passed with only the local
  LibreSSL warning from `urllib3`.
- Reflection: this is intentionally diagnostic only. It does not auto-install
  dependencies or mutate configuration, which keeps the first version useful
  without creating permission, security, or environment-management surprises.

### Module 1: Agent Loop Tool Execution

- Change: unexpected exceptions from tool handlers are now converted into
  auditable tool-result messages instead of crashing the whole agent loop.
- Files: `src/ecology_harness/runtime/agent_loop.py`,
  `tests/unit/test_agent_loop.py`.
- Validation: `PYTHONPATH=src python3 -m unittest tests.unit.test_agent_loop -q`
  passed with 9 tests.
- Remaining risk: unexpected provider exceptions still intentionally fail fast;
  a future pass can decide whether selected provider errors should become
  resumable session states.

### Module 2: Tool Registry Input Validation

- Change: tool input validation now checks nested object fields, array item
  schemas, enum values, and `additionalProperties: false` while preserving the
  previous default of allowing extension fields.
- Files: `src/ecology_harness/tools/registry.py`,
  `tests/unit/test_tool_registry.py`.
- Validation: `PYTHONPATH=src python3 -m unittest tests.unit.test_tool_registry tests.unit.test_agent_loop -q`
  passed with 14 tests.
- Remaining risk: this is still a deliberately small JSON-schema subset; future
  passes can add `minimum`, `maximum`, `minItems`, or pattern validation only
  where real tool schemas need them.

### Module 3: Persistent Memory Edge Cases

- Change: non-ASCII memory titles now get stable hash-backed slugs instead of
  collapsing to `item.md`; memory search and overlap checks no longer key
  internal term indexes by slug alone, avoiding user/project scope collisions.
- Files: `src/ecology_harness/memory/manager.py`,
  `tests/unit/test_memory.py`.
- Validation: `PYTHONPATH=src python3 -m unittest tests.unit.test_memory tests.unit.test_evolution -q`
  passed with 16 tests.
- Remaining risk: existing older `item.md` memories are not automatically
  migrated; a future maintenance tool could detect and rename legacy collisions.

### Module 4: MCP Catalog Robustness

- Change: malformed project/user MCP JSON files are skipped instead of breaking
  registry initialization; malformed `input_schema`, `tools`, `resources`,
  `env`, `headers`, and `args` values are coerced to safe defaults where
  possible.
- Files: `src/ecology_harness/mcp/registry.py`,
  `tests/unit/test_mcp_retrieval.py`.
- Validation: `PYTHONPATH=src python3 -m unittest tests.unit.test_mcp_retrieval tests.unit.test_platform_features -q`
  passed with 46 tests.
- Remaining risk: skipped malformed catalog files are not surfaced in a
  user-facing diagnostics list yet; a future `eh doctor` pass should report
  ignored config paths.

### Module 5: Frontmatter Persistence

- Change: frontmatter serialization now has regression coverage for multiline
  metadata so memory, profile, review, and skill documents can safely persist
  descriptive fields containing line breaks.
- Files: `src/ecology_harness/utils.py`, `tests/unit/test_utils.py`.
- Validation: `PYTHONPATH=src python3 -m unittest tests.unit.test_utils tests.unit.test_memory tests.unit.test_evolution -q`
  passed with 18 tests.
- Remaining risk: the parser is intentionally a lightweight frontmatter parser,
  not a full YAML implementation; richer YAML features should be added only if
  project-authored files require them.

### Module 6: MCP Diagnostics

- Change: malformed MCP catalog files remain non-fatal but are now reported
  through `McpServerRegistry.list_config_issues()` and `DoctorReport` so users
  can see which JSON files were skipped and why.
- Files: `src/ecology_harness/mcp/registry.py`,
  `src/ecology_harness/runtime/doctor.py`,
  `tests/unit/test_mcp_retrieval.py`.
- Validation: `PYTHONPATH=src python3 -m unittest tests.unit.test_mcp_retrieval tests.unit.test_platform_features -q`
  passed with 46 tests.
- Remaining risk: `eh mcp` still lists only loaded servers; a future UX pass can
  show catalog parse issues directly beside MCP server status.

### Final Validation

- `git diff --check`: passed.
- JSON catalog parse check over `src/ecology_harness/**/*.json`: passed.
- `PYTHONPATH=src python3 -m unittest discover -s tests/unit -q`: passed with
  242 tests.
- `python3 -m build --no-isolation --outdir /tmp/ecology_harness_continuous_build`:
  passed.
- `python3 -m twine check /tmp/ecology_harness_continuous_build/*`: passed;
  emitted only the local LibreSSL warning from `urllib3`.
- `python3 -m pytest -q`: not runnable in the system Python because `pytest`
  is not installed. In the local `py310` conda environment, pytest is installed
  but the process segfaulted or hung before test results, indicating an
  environment/tooling issue rather than a project assertion failure.
