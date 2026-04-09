# Ecology Harness

[English](README.md) | [简体中文](README.zh-CN.md)

Ecology Harness is a Python-first agent harness for ecology, environment, and
agroecology workflows. It now includes a growing ecology pack of domain skills,
MCP catalogs, and practical tools for literature review, geospatial reasoning,
aquatic microcosms, photobioreactors, biodiversity observation, microscopy, and
multimodal analysis.

The project combines a stable generic runtime with an ecology-first extension
surface, so new skills, MCP servers, and tools can keep accumulating without
making the core messy. Contributions are very welcome, and we would love help
from the community to keep improving and expanding the ecology stack together.

Current release: `0.2.0 beta` (`0.2.0b0` package version).
See [CHANGELOG.md](CHANGELOG.md) for release notes and [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidance.

## News

- `2026-04-06`: released `0.2.0 beta` as the first publishable beta build of Ecology Harness.
- `2026-04-09`: upgraded skills and MCP catalogs to query-aware retrieval, using local query rewriting plus BM25 ranking so only relevant skills and MCP servers are injected into the model context.
- `2026-04-09`: imported a curated scientific research skill set from `K-Dense-AI/claude-scientific-skills`, adding upstream bundles for literature review, paper lookup, geospatial analysis, statistics, visualization, bioinformatics, lab notebooks, and protocol automation.
- `2026-04-09`: added three more builtin skill packs: workflow skills from `obra/superpowers`, writing cleanup with `blader/humanizer`, and a large AI research stack from `Orchestra-Research/AI-Research-SKILLs`.

## Startup Preview

![Ecology Harness startup screen](imgs/start_img.png)

## Project Structure

```text
EcologyHarness/
├── .github/workflows/        # CI for tests and package smoke checks
├── docs/                     # Pack notes, architecture, and domain references
├── imgs/                     # README and startup screenshots
├── scripts/                  # Local install helpers
├── src/ecology_harness/
│   ├── agents/               # Multi-agent coordination and task state
│   ├── config/               # Settings and runtime configuration
│   ├── ecology/              # Ecology catalogs and domain extension surface
│   ├── mcp/                  # MCP registry, catalogs, and bridge logic
│   ├── memory/               # Persistent memory management
│   ├── permissions/          # Access policy and safety checks
│   ├── plugins/              # Bundled plugin manifests and loaders
│   ├── runtime/              # Agent loop, providers, sessions, compaction
│   ├── sandbox/              # File, shell, and network sandbox helpers
│   ├── skills/               # Built-in skills, including ecology, scientific, workflow, writing, and AI research packs
│   ├── tasks/                # User and agent task tracking
│   ├── tools/                # Built-in CLI/runtime tools
│   ├── ui/                   # Terminal UI and REPL presentation
│   ├── app.py                # Application assembly
│   └── cli.py                # `eh` command entrypoint
├── tests/unit/               # Standard-library unit test suite
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
└── pyproject.toml
```

## What Is Included

- package-based architecture with modular runtime boundaries
- CLI + REPL entrypoints with a claw-inspired natural command flow
- event-driven terminal UI with status header, trace stream, and session panels
- agent loop with tool-use execution
- unified provider layer for local and remote model backends
- built-in support for `mock`, `anthropic`, `openai`, `openrouter`, `gemini`, `kimi`, `qwen`, `zhipu`, `deepseek`, `ollama`, `lmstudio`, and `custom`
- managed session persistence with resume support and compaction metadata
- context compaction with continuation summaries for long conversations
- configurable sandbox policy for file, shell, and network boundaries
- tool registry with typed metadata and validation
- built-in file, shell, web, memory, skill, task, and subagent tools
- multimodal prompt attachments for local images, audio, documents, and sampled video frames
- document-analysis tools for `pdf`, `docx`, `md`, `csv`, `json`, `html`, and `ipynb`
- dual-scope persistent memory with relevance ranking and auto-generated `MEMORY.md` indexes
- specialized agent types, background subagents, dependency-aware coordination, and internal agent task tracking
- task tracking with status, owner, metadata, and dependency edges
- built-in markdown skills
- curated ecology skill bundles from high-quality upstream repositories
- vendored scientific research skill bundles for literature, stats, geo, omics, visualization, and lab workflows
- workflow engineering skills from `obra/superpowers`
- writing cleanup and anti-AI-slop editing with `humanizer`
- broad AI research skill bundles for model training, evaluation, serving, multimodal work, MLOps, and paper writing
- curated agriculture/environment/ecology MCP server catalog
- closed-algae-system and photobioreactor skills plus lab-analysis MCP catalog entries
- permission policy for read-only and workspace-write modes
- unit test suite built on the standard library

## Installed Skill Packs

- `ecology`: project-authored ecology, environment, and agroecology workflows plus imported domain bundles such as Mapbox, Open-Meteo, and Semantic Scholar related packs.
- `scientific`: curated scientific skills from `K-Dense-AI/claude-scientific-skills`, including `literature-review`, `paper-lookup`, `geopandas`, `statistical-analysis`, `scientific-visualization`, `biopython`, and `scikit-bio`.
- `superpowers`: workflow and engineering guidance from `obra/superpowers`, including `systematic-debugging`, `test-driven-development`, `verification-before-completion`, `writing-plans`, and `using-git-worktrees`.
- `writing`: writing cleanup helpers, currently including `humanizer` from `blader/humanizer`.
- `ai-research`: a large AI research skill tree from `Orchestra-Research/AI-Research-SKILLs`, covering `autoresearch`, model architecture, fine-tuning, evaluation, inference serving, MLOps, multimodal systems, ML paper writing, and research ideation.

## Ecology Pack

This repository now ships with a curated ecology pack that combines installed
skill bundles and discoverable MCP server configs.

The current ecology capability map is easiest to read by subdomain:

Clickable entries below point to original online upstream sources. Plain-text
skill names are project-authored skills or composite workflows that do not map
cleanly to a single external upstream repository.

| Subdomain | Typical Research Tasks | Available Skills | Available MCP / Tools |
|---|---|---|---|
| 植物、作物与微生物成长模拟 | 作物生长、灌溉、木本植被、根-茎结构、植物-土壤耦合、微生物增长、生物膜、参数拟合 | `plant-growth-model-selection`<br>`crop-growth-simulation-workflow`<br>`crop-water-and-irrigation-simulation`<br>`functional-structural-plant-modeling`<br>`root-and-rhizosphere-architecture-modeling`<br>`woody-plant-and-forest-simulation`<br>`microbial-growth-and-community-simulation`<br>`microbial-community-metabolism-simulation`<br>`microbial-biofilm-and-reactor-simulation`<br>`microbiome-timeseries-and-benchmark-simulation`<br>`plant-soil-microbe-coupled-simulation`<br>`growth-model-calibration-and-validation` | [jupyter-mcp](https://github.com/datalayer/jupyter-mcp-server)<br>[labarchives](https://github.com/SamuelBrudner/lab_archives_mcp)<br>[unit-converter](https://github.com/zazencodes/unit-converter-mcp)<br>[weather-open-meteo](https://github.com/cmer81/open-meteo-mcp)<br>[nasa](https://github.com/ProgramComputer/NASA-MCP-server)<br>[APSIM Next Generation](https://github.com/APSIMInitiative/ApsimX)<br>[PCSE / WOFOST](https://github.com/ajwdewit/pcse)<br>[AquaCrop-OSPy](https://github.com/aquacropos/aquacrop)<br>[BioCro](https://github.com/biocro/biocro)<br>[pyfao56](https://github.com/kthorp/pyfao56)<br>[CPlantBox](https://github.com/Plant-Root-Soil-Interactions-Modelling/CPlantBox)<br>[OpenAlea L-Py](https://github.com/openalea/lpy)<br>[OpenSimRoot](https://rootsystemml.github.io/ISMCROOT/opensimroot/)<br>[r3PG](https://github.com/trotsiuk/r3PG)<br>[medfate](https://github.com/emf-creaf/medfate)<br>[pyrealm](https://github.com/ImperialCollegeLondon/pyrealm)<br>[FATES](https://github.com/NGEET/fates)<br>[COBRApy](https://github.com/opencobra/cobrapy)<br>[MICOM](https://github.com/micom-dev/micom)<br>[COMETS](https://github.com/segrelab/comets)<br>[BacArena](https://github.com/euba/BacArena)<br>[Community Simulator](https://github.com/Emergent-Behaviors-in-Biology/community-simulator)<br>[NUFEB](https://github.com/nufeb/NUFEB)<br>[miaSim](https://github.com/microbiome/miaSim)<br>[CarveMe](https://github.com/cdanielmachado/carveme)<br>[PyCoMo](https://github.com/univieCUBE/PyCoMo) |
| 传统生态过程模型与主体模型 | 主体生态、流域模拟、食物网情景、森林干扰、陆地生态过程、多模型比较 | `process-model-selection`<br>`agent-based-ecology-modeling`<br>`watershed-and-ecohydrology-modeling`<br>`food-web-and-trophic-simulation`<br>`forest-landscape-disturbance-modeling`<br>`terrestrial-biosphere-and-vegetation-modeling`<br>`model-calibration-and-sensitivity`<br>`cross-model-scenario-comparison` | [NetLogo](https://github.com/NetLogo/NetLogo)<br>[Mesa](https://github.com/projectmesa/mesa)<br>[GAMA Platform](https://github.com/gama-platform/gama)<br>[DSSAT Cropping System Model](https://github.com/DSSAT/dssat-csm-os)<br>[SWAT+](https://swatplus.gitbook.io/docs/)<br>[Ecopath with Ecosim](https://ecopath.org/)<br>[LPJ-GUESS](https://web.nateko.lu.se/lpj-guess/index.html)<br>[FATES](https://github.com/NGEET/fates)<br>[ED2](https://github.com/EDmodel/ED2)<br>[Biome-BGC](https://carbonmodel.org/biome_bgc/)<br>[CENTURY / DayCent](https://www.nrel.colostate.edu/projects/century/)<br>[RHESSys](https://github.com/RHESSys/RHESSys)<br>[LANDIS-II](https://www.landis-ii.org/home)<br>[Madingley Model](https://madingley.github.io/)<br>[RangeShifter 2.0](https://rangeshifter.github.io/software/rangeshifter2.0/) |
| Lake, reservoir, and aquatic ecosystem modeling | thermal structure, dissolved oxygen, blooms, nutrient scenarios, aquatic biogeochemistry | `aquatic-ecodynamics-and-water-quality-modeling` | [GLM](https://github.com/AquaticEcoDynamics/GLM)<br>[glm-py](https://github.com/AquaticEcoDynamics/glm-py)<br>[FABM](https://github.com/fabm-model/fabm) |
| 淡水微宇宙、浮游群落与生物膜 | 摄食微宇宙、浮游变化、底栖生物膜、水质、荧光、显微分类 | `aquatic-microcosm-foodweb-design`<br>`zooplankton-grazing-and-plankton-dynamics`<br>`benthic-biofilm-and-periphyton-monitoring`<br>`water-quality-and-nutrient-panel`<br>`plankton-microscopy-and-auto-classification`<br>`fluorescence-spectra-and-molecular-assays` | [jupyter-mcp](https://github.com/datalayer/jupyter-mcp-server)<br>[influxdb3](https://github.com/influxdata/influxdb3_mcp_server)<br>[labarchives](https://github.com/SamuelBrudner/lab_archives_mcp)<br>[unit-converter](https://github.com/zazencodes/unit-converter-mcp)<br>[scientific-papers](https://github.com/benedict2310/Scientific-Papers-MCP)<br>[openalex-research](https://github.com/oksure/openalex-research-mcp)<br>[simple-pubmed](https://github.com/andybrandt/mcp-simple-pubmed)<br>[pubchem](https://github.com/Augmented-Nature/PubChem-MCP-Server)<br>[MorphoCut](https://github.com/morphocut/morphocut)<br>[GLM](https://github.com/AquaticEcoDynamics/GLM)<br>[glm-py](https://github.com/AquaticEcoDynamics/glm-py)<br>[FABM](https://github.com/fabm-model/fabm) |
| 封闭藻类系统与光生物反应器 | 封闭反应器设计、光径、pH / CO2 控制、污染排查、生长曲线、物质平衡 | [closed-algae-system-design](https://github.com/K-Dense-AI/claude-scientific-skills)<br>[photobioreactor-environment-control](https://github.com/K-Dense-AI/claude-scientific-skills)<br>[microalgae-strain-and-inoculation](https://github.com/K-Dense-AI/claude-scientific-skills)<br>[algal-monitoring-plan](https://github.com/K-Dense-AI/claude-scientific-skills)<br>[photobioreactor-troubleshooting](https://github.com/K-Dense-AI/claude-scientific-skills)<br>[algal-timeseries-and-mass-balance](https://github.com/K-Dense-AI/claude-scientific-skills) | [jupyter-mcp](https://github.com/datalayer/jupyter-mcp-server)<br>[influxdb3](https://github.com/influxdata/influxdb3_mcp_server)<br>[labarchives](https://github.com/SamuelBrudner/lab_archives_mcp)<br>[unit-converter](https://github.com/zazencodes/unit-converter-mcp)<br>[scientific-papers](https://github.com/benedict2310/Scientific-Papers-MCP)<br>[openalex-research](https://github.com/oksure/openalex-research-mcp)<br>[pubchem](https://github.com/Augmented-Nature/PubChem-MCP-Server) |
| 植物表型与性状提取 | 叶片性状、形态测量、腊叶标本测量、器官检测 | `plant-phenotyping-and-traits`<br>`root-phenotyping-and-rhizosphere-imaging` | [PlantCV](https://github.com/danforthcenter/plantcv)<br>[LeafMachine2](https://github.com/Gene-Weaver/LeafMachine2)<br>[RhizoVision Explorer](https://github.com/noble-research-group/RhizoVisionExplorer)<br>[RootPainter](https://github.com/Abe404/root_painter)<br>[OpenSimRoot](https://rootsystemml.github.io/ISMCROOT/opensimroot/) |
| 生态计数与分割 | 植株计数、树木计数、动物检测、树冠分割 | `ecology-counting-and-segmentation` | [DeepForest](https://github.com/weecology/DeepForest)<br>[detectree2](https://github.com/PatBall1/detectree2)<br>[TreeCountSegHeight](https://github.com/sizhuoli/TreeCountSegHeight)<br>[PyTorch-Wildlife](https://github.com/microsoft/CameraTraps) |
| Behavioral ecology and pose tracking | movement, foraging, courtship, interaction video analysis, multi-animal tracking | `animal-behavior-and-pose-tracking` | [DeepLabCut](https://github.com/DeepLabCut/DeepLabCut)<br>[SLEAP](https://github.com/talmolab/sleap)<br>[PyTorch-Wildlife](https://github.com/microsoft/CameraTraps) |
| 生态系统生物地球化学与土壤系统 | 碳、甲烷、养分循环、土壤健康、修复背景 | `ecosystem-biogeochemistry-workup`<br>`soil-health-and-nutrient-screen` | [weather-open-meteo](https://github.com/cmer81/open-meteo-mcp)<br>[nasa](https://github.com/ProgramComputer/NASA-MCP-server)<br>[eosc-data-commons](https://github.com/EOSC-Data-Commons/data-commons-mcp)<br>[dataverse](https://github.com/gdcc/mcp-dataverse)<br>[wsl-envidat](https://github.com/malkreide/wsl-envidat-mcp) |
| 环境化学与暴露 | 污染物、PFAS、微塑料、农药归趋、毒理交叉文献 | `environmental-chemistry-risk-scan`<br>`literature-multi-source-search` | [pubchem](https://github.com/Augmented-Nature/PubChem-MCP-Server)<br>[simple-pubmed](https://github.com/andybrandt/mcp-simple-pubmed)<br>[scientific-papers](https://github.com/benedict2310/Scientific-Papers-MCP)<br>[weather-open-meteo](https://github.com/cmer81/open-meteo-mcp)<br>[swiss-environment](https://github.com/malkreide/swiss-environment-mcp) |
| 微生物生态与保育遗传 | 分类、marker、组装、直系同源、BLAST 工作流 | `microbial-ecology-sequence-workflow`<br>`amplicon-and-metabolic-reconstruction-workflow` | [ncbi-datasets](https://github.com/Augmented-Nature/NCBI-Datasets-MCP-Server)<br>[bio-blast](https://github.com/bio-mcp/bio-mcp-blast)<br>[simple-pubmed](https://github.com/andybrandt/mcp-simple-pubmed)<br>[mothur](https://github.com/mothur/mothur)<br>[VSEARCH](https://github.com/torognes/vsearch)<br>[CarveMe](https://github.com/cdanielmachado/carveme)<br>[PyCoMo](https://github.com/univieCUBE/PyCoMo) |
| 生态声学 | 鸟声识别、被动声学筛查、批量音频回顾 | `ecoacoustics-screen` | [BirdNET-Analyzer](https://github.com/birdnet-team/BirdNET-Analyzer) |
| 保护与恢复 | 恢复预筛查、生态压力、场地背景 | `environmental-site-screen`<br>`ecology-evidence-synthesis` | [mapbox](https://github.com/mapbox/mcp-server)<br>[gis-mcp](https://github.com/mahdin75/gis-mcp)<br>[nasa](https://github.com/ProgramComputer/NASA-MCP-server) |
| 开放数据与科研仓储 | 数据集发现、DOI 级数据记录、复现材料 | `research-data-repository-hunt`<br>`ecology-dataset-hunt` | [dataverse](https://github.com/gdcc/mcp-dataverse)<br>[eosc-data-commons](https://github.com/EOSC-Data-Commons/data-commons-mcp)<br>[wsl-envidat](https://github.com/malkreide/wsl-envidat-mcp) |
| 区域公共环境数据 | 区域环境监测和公开研究数据 | `swiss-environment-brief` | [swiss-environment](https://github.com/malkreide/swiss-environment-mcp)<br>[wsl-envidat](https://github.com/malkreide/wsl-envidat-mcp) |
| Cartography and map presentation | map design, visual hierarchy, report-ready maps | [mapbox-cartography](https://github.com/mapbox/mapbox-agent-skills)<br>[mapbox-data-visualization-patterns](https://github.com/mapbox/mapbox-agent-skills) | [mapbox](https://github.com/mapbox/mcp-server) |

You can inspect them directly:

```bash
eh skills
eh mcp
```

MCP status meanings in this build:

- `connected`: in-process server is active now
- `configured`: server is enabled and intended to run through a remote transport
- `cataloged`: server metadata is installed in the repository and ready for later activation

Upstream source notes are tracked in [docs/ecology-pack.md](docs/ecology-pack.md).

Closed-system algae and photobioreactor-specific notes are tracked in [docs/algae-photobioreactor-pack.md](docs/algae-photobioreactor-pack.md).

Freshwater microcosm and plankton-specific notes are tracked in [docs/aquatic-microcosm-pack.md](docs/aquatic-microcosm-pack.md).

Plant, crop, and microbial growth-simulation notes are tracked in [docs/plant-growth-simulation-pack.md](docs/plant-growth-simulation-pack.md).

That pack now also covers plant-type-specific modeling for annual crops,
irrigation and water balance, woody vegetation and forests, rhizosphere
structure, and microbial-community or biofilm simulation.

Traditional ecological process-model and ABM notes are tracked in [docs/ecology-process-modeling-pack.md](docs/ecology-process-modeling-pack.md).

Example prompts:

```bash
eh prompt '/closed-algae-system-design flat-panel Chlorella reactor for wastewater polishing'
eh prompt '/photobioreactor-environment-control CO2 and pH control for sealed Spirulina cultivation'
eh prompt '/algal-timeseries-and-mass-balance interpret pH, dissolved oxygen, and nitrate drawdown in a batch reactor'
eh prompt '/aquatic-microcosm-foodweb-design Daphnia Chlorella Microcystis Navicula freshwater microcosm'
eh prompt '/plankton-microscopy-and-auto-classification microscope camera workflow for Daphnia rotifers and algal colonies'
eh prompt '/plant-growth-model-selection maize drought simulation with irrigation treatments'
eh prompt '/crop-growth-simulation-workflow rice yield under heat stress and delayed sowing'
eh prompt '/woody-plant-and-forest-simulation drought stress and stand development in pine plantations'
eh prompt '/microbial-community-metabolism-simulation cross-feeding in a synthetic rhizosphere consortium'
eh prompt '/microbial-growth-and-community-simulation rhizosphere consortium cross-feeding under carbon pulses'
eh prompt '/process-model-selection restoration grazing fire and hydrology interactions in a catchment'
eh prompt '/agent-based-ecology-modeling pollinator movement in fragmented farmland'
eh prompt '/watershed-and-ecohydrology-modeling watershed nutrient export under changing fertilizer inputs'
```

This pass also expanded coverage for finer-grained research directions that are common in ecology, agriculture, and environment projects:

- organismal stress and physiological ecology
- population, invasion, and metapopulation screening
- community assembly and disturbance response
- ecosystem biogeochemistry, carbon, methane, and nutrient cycling
- landscape connectivity and remote-sensing catalog selection
- global-change ecology and climate-risk framing
- microbial ecology, eDNA-adjacent taxonomy, and conservation genetics
- environmental chemistry, pollutant fate, and toxicity screening

## Ecology Basic Tools

This repository now also includes a basic ecology observation-tool layer:

- native lightweight tools for taxa and observation lookup
- native plant identification via Pl@ntNet
- a catalog of heavier local toolkits for phenotyping, counting, segmentation, camera traps, and ecoacoustics

See [docs/ecology-basic-tools.md](docs/ecology-basic-tools.md) for the full function map.

This catalog now also includes laboratory and bioprocess analysis entries such as
`Jupyter MCP Server`, `InfluxDB 3 MCP Server`, `LabArchives MCP Server`,
`unit-converter-mcp`, `PyLabRobot`, and `Opentrons`.

It now also includes plant and microbial growth-simulation frameworks such as
`APSIM Next Generation`, `PCSE / WOFOST`, `AquaCrop-OSPy`, `CPlantBox`,
`OpenAlea L-Py`, `pyrealm`, `COBRApy`, `MICOM`, `Tellurium`, `COPASI`,
`PySCeS`, `MDSINE2`, and `pyPESTO`.

It now also includes traditional ecological simulators and ABM systems such as
`NetLogo`, `Mesa`, `GAMA Platform`, `DSSAT Cropping System Model`, `SWAT+`,
`Ecopath with Ecosim`, `LPJ-GUESS`, `ED2`, `Biome-BGC`, `CENTURY / DayCent`,
`RHESSys`, `LANDIS-II`, `Madingley Model`, and `RangeShifter 2.0`.

It now also includes microscopy, plankton, and molecular-analysis toolkits such as
`Fiji / ImageJ`, `PyImageJ`, `CellProfiler`, `napari`, `ilastik`,
`EcoTaxa Python Client`, `PlanktoScope`, `QIIME 2 / Rachis Framework`, and `DADA2`.

You can inspect the new layer directly:

```bash
eh tool ListEcologyFunctions '{}'
eh tool ListEcologyToolkits '{}'
eh tool DescribeEcologyToolkit '{"name":"plantcv"}'
eh tool INaturalistSearchTaxa '{"query":"Quercus alba"}'
eh tool INaturalistSearchObservations '{"taxon_name":"Quercus alba","per_page":3}'
```

If you have a Pl@ntNet API key:

```bash
export PLANTNET_API_KEY=your_key_here
eh tool PlantNetIdentify '{"image_paths":["leaf.jpg"],"organs":["leaf"]}'
```

## Multimodal and Document Analysis

The runtime now supports local multimodal inputs in the main conversation loop:

- image attachments are passed as real multimodal content blocks for providers that support vision
- audio attachments are passed natively for the OpenAI provider and fall back to metadata-aware context elsewhere
- document attachments are normalized for analysis, with provider-specific handling where possible and plain-text fallback elsewhere
- video attachments are expanded into sampled frames for frame-by-frame review, inspired by claw-style attachment preprocessing
- REPL attachment flow is inspired by `claw-code`, with `/attach`, `/image`, `/doc`, and `/attachments`

You can use it directly from the CLI:

```bash
# attach a local image
eh --provider openai --model gpt-4o --attach imgs/specimen.jpg \
  "identify the likely species and explain the visual cues"

# attach a local paper or report
eh --attach docs/wetland_report.pdf \
  "summarize the methods, main findings, and restoration implications"

# attach local audio
eh --provider openai --model gpt-4o-audio-preview --attach audio/birdsong.wav \
  "identify the likely bird species and describe the calling pattern"

# attach local video; Ecology Harness will sample frames for analysis
eh --attach video/camera_trap.mp4 \
  "describe the observed animal activity across sampled frames"

# inspect a document without going through the model loop
eh tool DocumentInspect '{"path":"docs/wetland_report.pdf"}'
eh tool DocumentExtract '{"path":"notes/field_log.docx","max_chars":12000}'
eh tool AudioInspect '{"path":"audio/birdsong.wav"}'
eh tool VideoInspect '{"path":"video/camera_trap.mp4"}'
eh tool VideoSampleFrames '{"path":"video/camera_trap.mp4","frame_count":6}'
```

Inside the REPL:

```text
/attach docs/wetland_report.pdf
/image imgs/specimen.jpg
/audio audio/birdsong.wav
/video video/camera_trap.mp4
/attachments
summarize the attached materials
```

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
eh skills
eh mcp

# use OpenRouter directly
export OPENROUTER_API_KEY="sk-or-..."
eh --provider openrouter --model openai/gpt-4.1-mini \
  "summarize this repository in 5 bullets"

# one-shot prompt using the natural shorthand
eh "summarize this repository in 5 bullets"

# explicit prompt command
eh prompt '/tool Read {"path":"README.md"}'

# multimodal prompt with local attachments
eh --attach docs/wetland_report.pdf prompt "summarize this report"

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
/attach docs/wetland_report.pdf
/image imgs/specimen.jpg
/audio audio/birdsong.wav
/video video/camera_trap.mp4
/doc notes/field_log.docx
/attachments
/ecology-dataset-hunt estuary methane flux datasets 2018-2024
/ecology-evidence-synthesis blue carbon mangroves
/literature-multi-source-search wetland methane ebullition
/open-access-paper-harvest 10.1038/nclimate2616
/research-data-repository-hunt peatland carbon flux tower data
/biodiversity-data-triage alpine pollinator decline
/species-occurrence-workbench Panthera leo occurrences in Kenya
/species-photo-identification oak leaf with lobed margins
/plant-phenotyping-and-traits herbarium leaf length width area extraction
/ecology-counting-and-segmentation count trees in UAV imagery
/ecoacoustics-screen batch bird-call screening workflow
/remote-sensing-catalog-hunt mangrove canopy disturbance in South China
/global-change-ecology-brief climate-driven range shift for alpine pollinators
/microbial-ecology-sequence-workflow soil microbiome drought marker genes
/environmental-chemistry-risk-scan PFAS wetland food web exposure
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
- `/attach`
- `/image`
- `/doc`
- `/audio`
- `/video`
- `/attachments`
- `/clear-attachments`
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

The runtime supports these provider families:

- `anthropic` for Claude
- `openai` for GPT and o-series
- `openrouter` for routed multi-provider model access
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

### OpenRouter Provider

OpenRouter is exposed as a first-class provider in this build. Model names should keep the
router format, for example `openai/gpt-4.1-mini` or `anthropic/claude-3.7-sonnet`.

```bash
export OPENROUTER_API_KEY="sk-or-..."

# optional but recommended for OpenRouter app attribution
export OPENROUTER_HTTP_REFERER="https://github.com/ECNU-ICALK/Ecology-Harness"
export OPENROUTER_TITLE="Ecology Harness"

eh \
  --provider openrouter \
  --model openai/gpt-4.1-mini \
  prompt "Inspect the current workspace."

eh \
  --provider openrouter \
  --model anthropic/claude-3.7-sonnet \
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
python3 -m ecology_harness --exec-tool MemorySave --params '{"name":"Project Goal","description":"Current direction","content":"Build a reusable ecology harness core.","type":"project","scope":"project"}'

# list persisted state
python3 -m ecology_harness memories
python3 -m ecology_harness tasks

# inspect sandbox configuration
python3 -m ecology_harness sandbox
```

## Core Runtime Features

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
