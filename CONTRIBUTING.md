# Contributing

Ecology Harness welcomes contributions across core runtime work and domain
content such as tools, skills, MCP catalogs, and documentation.

## Development Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install -e .[dev]
```

## Run Locally

```bash
eh --list-tools
eh --list-skills
eh --repl
```

## Test

```bash
PYTHONPATH=src python3 -m unittest discover -s tests/unit -v
python3 -m build
python3 -m twine check dist/*
```

## Contribution Areas

- runtime, providers, memory, sandbox, and subagent execution
- ecology tools and adapters
- ecology skills and workflow prompts
- MCP catalog entries and transport integrations
- documentation, examples, and release notes

## Adding A New Skill

- put lightweight markdown skills in `src/ecology_harness/skills/builtin/`
- put ecology-focused skills in `src/ecology_harness/skills/builtin/ecology/`
- if a skill bundle needs references or scripts, keep it self-contained under its bundle directory
- add or update tests in `tests/unit/test_skills.py` when new built-in skills should be discoverable

## Adding A New Toolkit Or MCP Entry

- update `src/ecology_harness/ecology/toolkits/ecology_basic_toolkits.json` for toolkit discovery
- update `src/ecology_harness/mcp/builtin/` for MCP catalog entries
- add or update docs so the capability map stays readable
- add focused tests in `tests/unit/test_ecology_tools.py` when the catalog should expose the new entry

## Pull Request Notes

- keep changes scoped and explain the research workflow the addition enables
- prefer official or well-maintained upstream sources
- avoid claiming a heavy external simulator is bundled if it is only cataloged
- include verification steps in the PR description
