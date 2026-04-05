---
name: ecology-evidence-synthesis
description: Build a literature-backed evidence brief for agriculture, environment, or ecology topics using the installed Semantic Scholar skills.
slug: ecology-evidence-synthesis
triggers: [/ecology-evidence-synthesis]
allowed-tools: [Skill, SkillRead, Read, Bash, WebSearch]
context: inline
---
Produce an evidence brief grounded in the installed Semantic Scholar workflows.

Preferred sequence:
1. If the user starts with a vague topic or half-remembered title, run `paper-triage`.
2. Once you have one to three anchor papers, run `expand-references` to widen the reading set.
3. If one paper becomes central, run `trace-citations` to map supporting, bridge, and downstream work.
4. Synthesize the results into a short evidence map.

Required synthesis fields:
- research question
- core findings
- methods and data sources
- geography and ecosystem or crop context
- time horizon
- limitations and disagreement
- what evidence is still missing

Use ecology-specific framing:
- name species, habitats, watersheds, or biomes when present
- separate observational evidence from experimental or modeling evidence
- do not overstate causality

If the skill bundle exposes scripts or references, resolve them from the skill bundle root shown in the prompt.
$ARGUMENTS
