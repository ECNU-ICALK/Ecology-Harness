from __future__ import annotations

import json
import mimetypes
import os
from pathlib import Path
import re
from typing import Any
from urllib import error, parse, request
import uuid

from ecology_harness.tools.base import ToolContext, ToolDefinition, ToolError, ToolResult
from ecology_harness.tools.registry import ToolRegistry


def register_ecology_tools(registry: ToolRegistry) -> None:
    registry.register(
        ToolDefinition(
            name="ListEcologyFunctions",
            description="List foundational ecology observation, identification, phenotyping, counting, monitoring, lab workflow, and bioreactor-analysis functions grouped by task family.",
            input_schema={
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                    "query": {"type": "string"},
                },
            },
            handler=_list_ecology_functions,
            read_only=True,
            concurrent_safe=True,
        )
    )
    registry.register(
        ToolDefinition(
            name="ListEcologyToolkits",
            description="List installed or cataloged ecology, laboratory, automation, notebook, and monitoring toolkits or MCP-backed analysis servers.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "capability": {"type": "string"},
                    "modality": {"type": "string"},
                },
            },
            handler=_list_ecology_toolkits,
            read_only=True,
            concurrent_safe=True,
        )
    )
    registry.register(
        ToolDefinition(
            name="DescribeEcologyToolkit",
            description="Describe one ecology or lab-analysis toolkit, including modalities, capabilities, source repository, and install guidance.",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                },
                "required": ["name"],
            },
            handler=_describe_ecology_toolkit,
            read_only=True,
            concurrent_safe=True,
        )
    )
    registry.register(
        ToolDefinition(
            name="INaturalistSearchTaxa",
            description="Search iNaturalist taxa by scientific or common name and return candidate taxonomic matches.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "rank": {"type": "string"},
                    "per_page": {"type": "integer"},
                },
                "required": ["query"],
            },
            handler=_inaturalist_search_taxa,
            read_only=True,
            concurrent_safe=True,
            tags=("ecology", "biodiversity", "taxonomy"),
        )
    )
    registry.register(
        ToolDefinition(
            name="INaturalistSearchObservations",
            description="Search iNaturalist observations by taxon name and other simple filters.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "taxon_name": {"type": "string"},
                    "place_id": {"type": "integer"},
                    "quality_grade": {"type": "string"},
                    "per_page": {"type": "integer"},
                },
            },
            handler=_inaturalist_search_observations,
            read_only=True,
            concurrent_safe=True,
            tags=("ecology", "biodiversity", "observation"),
        )
    )
    registry.register(
        ToolDefinition(
            name="PlantNetIdentify",
            description="Identify plants from one or more local images using the Pl@ntNet API.",
            input_schema={
                "type": "object",
                "properties": {
                    "image_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "organs": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "project": {"type": "string"},
                },
                "required": ["image_paths"],
            },
            handler=_plantnet_identify,
            read_only=True,
            concurrent_safe=False,
            tags=("ecology", "plant", "identification", "vision"),
        )
    )


def _catalog_path() -> Path:
    return Path(__file__).resolve().parents[2] / "ecology" / "toolkits" / "ecology_basic_toolkits.json"


def _load_catalog() -> dict[str, Any]:
    return json.loads(_catalog_path().read_text(encoding="utf-8"))


_QUERY_EXPANSIONS = {
    "物种分布": "species distribution ecological niche modeling sdm maxent habitat suitability occurrence",
    "分布模型": "species distribution ecological niche modeling sdm maxent habitat suitability occurrence",
    "生态位": "ecological niche modeling maxent habitat suitability",
    "栖息地": "habitat suitability landscape connectivity occurrence",
    "生物多样性": "biodiversity occurrence taxonomy gbif obis ebird",
    "鸟": "bird avian ebird acoustic ecoacoustic bioacoustic",
    "鸟类": "bird avian ebird acoustic ecoacoustic bioacoustic",
    "声学": "acoustic ecoacoustic bioacoustic audio birdnet opensoundscape",
    "运动": "movement tracking telemetry animal movement trajectory ctmm movebank",
    "迁徙": "migration movement telemetry animal movement trajectory movebank",
    "水文": "hydrology streamflow watershed usgs pygeohydro dataretrieval",
    "流量": "streamflow discharge water data usgs hydrology",
    "土壤": "soil soilgrids soildb soil profile nutrient",
    "空气质量": "air quality openaq pollution exposure",
    "海洋": "marine ocean obis biodiversity occurrence",
    "遥感": "remote sensing stac earth observation satellite raster",
    "地球观测": "earth observation stac satellite raster",
    "灌溉": "irrigation crop water drought evapotranspiration",
    "干旱": "drought crop water irrigation climate stress",
    "玉米": "maize crop growth simulation irrigation drought",
    "作物": "crop growth simulation irrigation drought agroecosystem",
    "成长": "growth simulation plant crop microbial",
    "生长": "growth simulation plant crop microbial",
    "微生物": "microbial microbiome community metabolism biofilm amplicon",
    "生物膜": "biofilm microbial reactor periphyton",
    "3d": "3d point cloud photogrammetry lidar mesh terrain visualization",
}


_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "for",
    "in",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
    "的",
    "和",
    "与",
    "及",
}


def _expand_query_text(query: str) -> str:
    text = (query or "").strip().lower()
    if not text:
        return ""
    additions = [value for key, value in _QUERY_EXPANSIONS.items() if key in text]
    return " ".join([text, *additions]).strip()


def _query_terms(query: str) -> list[str]:
    expanded = _expand_query_text(query)
    terms = re.findall(r"[a-z0-9][a-z0-9+_.-]*|[\u4e00-\u9fff]+", expanded)
    return [term for term in terms if term not in _STOP_WORDS and len(term) > 1]


def _score_query_match(query: str, haystack: str) -> int:
    raw_query = (query or "").strip().lower()
    if not raw_query:
        return 1
    score = 0
    if raw_query in haystack:
        score += 8
    expanded_query = _expand_query_text(query)
    if expanded_query and expanded_query != raw_query and expanded_query in haystack:
        score += 4
    for term in _query_terms(query):
        if term in haystack:
            score += 1
    return score


def _list_ecology_functions(params: dict[str, Any], context: ToolContext) -> ToolResult:
    del context
    catalog = _load_catalog()
    category_filter = str(params.get("category", "")).strip().lower()
    query = str(params.get("query", "")).strip().lower()
    categories = []
    for item in catalog.get("functions", []):
        haystack = " ".join(
            [item.get("category", "")]
            + list(item.get("capabilities", []))
            + list(item.get("examples", []))
        ).lower()
        if category_filter and category_filter not in item.get("category", "").lower():
            continue
        if query and _score_query_match(query, haystack) <= 0:
            continue
        categories.append(item)

    if not categories:
        return ToolResult(content="No ecology function groups matched.", data={"functions": []})

    blocks = []
    for item in categories:
        lines = [item["category"]]
        for capability in item.get("capabilities", []):
            lines.append("- %s" % capability)
        if item.get("examples"):
            lines.append("Examples: %s" % "; ".join(item["examples"]))
        blocks.append("\n".join(lines))
    return ToolResult(
        content="\n\n".join(blocks),
        data={"functions": categories},
    )


def _list_ecology_toolkits(params: dict[str, Any], context: ToolContext) -> ToolResult:
    del context
    catalog = _load_catalog()
    query = str(params.get("query", "")).strip().lower()
    capability = str(params.get("capability", "")).strip().lower()
    modality = str(params.get("modality", "")).strip().lower()
    scored_toolkits = []
    for item in catalog.get("toolkits", []):
        haystack = " ".join(
            [
                item.get("slug", ""),
                item.get("name", ""),
                item.get("summary", ""),
                item.get("modality", ""),
                item.get("status", ""),
            ]
            + list(item.get("capabilities", []))
            + list(item.get("good_for", []))
        ).lower()
        score = _score_query_match(query, haystack)
        if query and score <= 0:
            continue
        if capability and capability not in " ".join(item.get("capabilities", [])).lower():
            continue
        if modality and modality != item.get("modality", "").lower():
            continue
        scored_toolkits.append((score, item))

    toolkits = [item for _, item in sorted(scored_toolkits, key=lambda row: (-row[0], row[1].get("slug", "")))]

    if not toolkits:
        return ToolResult(content="No ecology toolkits matched.", data={"toolkits": []})

    lines = []
    for item in toolkits:
        lines.append(
            "%s\t%s\t%s\t%s"
            % (
                item["slug"],
                item.get("modality", ""),
                item.get("status", ""),
                item.get("summary", ""),
            )
        )
    return ToolResult(
        content="\n".join(lines),
        data={"toolkits": toolkits},
    )


def _describe_ecology_toolkit(params: dict[str, Any], context: ToolContext) -> ToolResult:
    del context
    needle = str(params["name"]).strip().lower()
    catalog = _load_catalog()
    for item in catalog.get("toolkits", []):
        if needle not in {item.get("slug", "").lower(), item.get("name", "").lower()}:
            continue
        lines = [
            item["name"],
            "slug: %s" % item["slug"],
            "status: %s" % item.get("status", ""),
            "modality: %s" % item.get("modality", ""),
            "summary: %s" % item.get("summary", ""),
            "repo: %s" % item.get("repo", ""),
            "install: %s" % item.get("install", ""),
        ]
        if item.get("good_for"):
            lines.append("good_for: %s" % ", ".join(item["good_for"]))
        if item.get("capabilities"):
            lines.append("capabilities: %s" % ", ".join(item["capabilities"]))
        if item.get("notes"):
            lines.append("notes: %s" % item["notes"])
        return ToolResult(content="\n".join(lines), data=item)
    raise ToolError("Unknown ecology toolkit: %s" % params["name"])


def _inaturalist_search_taxa(params: dict[str, Any], context: ToolContext) -> ToolResult:
    query = str(params["query"]).strip()
    if not query:
        raise ToolError("query is required")
    per_page = max(1, min(int(params.get("per_page", 5) or 5), 20))
    query_params = {"q": query, "per_page": str(per_page)}
    rank = str(params.get("rank", "")).strip()
    if rank:
        query_params["rank"] = rank
    payload = _fetch_json(
        "https://api.inaturalist.org/v1/taxa?%s" % parse.urlencode(query_params),
        context,
    )
    results = payload.get("results", []) or []
    if not results:
        return ToolResult(content="No iNaturalist taxa matched.", data={"results": []})
    rows = []
    lines = []
    for item in results[:per_page]:
        row = {
            "id": item.get("id"),
            "name": item.get("name", ""),
            "preferred_common_name": item.get("preferred_common_name", ""),
            "rank": item.get("rank", ""),
            "observations_count": item.get("observations_count", 0),
            "matched_term": item.get("matched_term", ""),
        }
        rows.append(row)
        lines.append(
            "%s\t%s\t%s\tobs=%s"
            % (
                row["id"],
                row["rank"] or "?",
                row["preferred_common_name"] or row["name"],
                row["observations_count"],
            )
        )
    return ToolResult(content="\n".join(lines), data={"query": query, "results": rows})


def _inaturalist_search_observations(params: dict[str, Any], context: ToolContext) -> ToolResult:
    per_page = max(1, min(int(params.get("per_page", 5) or 5), 20))
    query_params = {"per_page": str(per_page)}
    for key in ("query", "taxon_name", "quality_grade"):
        value = str(params.get(key, "")).strip()
        if value:
            mapped = "q" if key == "query" else key
            query_params[mapped] = value
    if params.get("place_id") is not None:
        query_params["place_id"] = str(int(params["place_id"]))
    payload = _fetch_json(
        "https://api.inaturalist.org/v1/observations?%s" % parse.urlencode(query_params),
        context,
    )
    results = payload.get("results", []) or []
    if not results:
        return ToolResult(content="No iNaturalist observations matched.", data={"results": []})
    rows = []
    lines = []
    for item in results[:per_page]:
        taxon = item.get("taxon") or {}
        row = {
            "id": item.get("id"),
            "observed_on": item.get("observed_on_string") or item.get("observed_on"),
            "quality_grade": item.get("quality_grade", ""),
            "place_guess": item.get("place_guess", ""),
            "taxon_name": taxon.get("name", ""),
            "common_name": taxon.get("preferred_common_name", ""),
            "uri": item.get("uri", ""),
        }
        rows.append(row)
        label = row["common_name"] or row["taxon_name"] or "unknown taxon"
        lines.append(
            "%s\t%s\t%s\t%s"
            % (
                row["id"],
                row["observed_on"] or "?",
                label,
                row["place_guess"] or "",
            )
        )
    return ToolResult(content="\n".join(lines), data={"results": rows})


def _plantnet_identify(params: dict[str, Any], context: ToolContext) -> ToolResult:
    if not context.settings.sandbox_allow_network:
        raise ToolError("PlantNetIdentify is unavailable because sandbox network access is disabled.")
    api_key = os.environ.get("PLANTNET_API_KEY", "").strip()
    if not api_key:
        raise ToolError("PLANTNET_API_KEY is not set.")
    image_paths = params.get("image_paths") or []
    if not isinstance(image_paths, list) or not image_paths:
        raise ToolError("image_paths must be a non-empty array.")
    if len(image_paths) > 5:
        raise ToolError("PlantNetIdentify accepts up to 5 images.")
    organs = params.get("organs") or []
    if organs and not isinstance(organs, list):
        raise ToolError("organs must be an array.")
    project = str(params.get("project", "all") or "all").strip() or "all"
    files = []
    for raw_path in image_paths:
        path = _resolve_read_path(context, str(raw_path))
        if not path.exists() or not path.is_file():
            raise ToolError("Image file does not exist: %s" % raw_path)
        files.append(path)

    url = "https://my-api.plantnet.org/v2/identify/%s?api-key=%s" % (
        parse.quote(project),
        parse.quote(api_key),
    )
    body, content_type = _build_multipart_request(files, [str(item) for item in organs])
    req = request.Request(
        url,
        data=body,
        headers={
            "Content-Type": content_type,
            "User-Agent": "EcologyHarness/0.1",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=context.settings.command_timeout_sec) as response:
            payload = json.loads(response.read(context.settings.max_web_bytes).decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise ToolError("PlantNetIdentify HTTP error %s: %s" % (exc.code, detail[:400])) from exc
    except error.URLError as exc:
        raise ToolError("PlantNetIdentify connection error: %s" % exc) from exc
    except json.JSONDecodeError as exc:
        raise ToolError("PlantNetIdentify returned invalid JSON.") from exc

    results = payload.get("results", []) or []
    if not results:
        return ToolResult(content="PlantNet returned no candidate species.", data={"results": []})
    rows = []
    lines = []
    for item in results[:5]:
        species = item.get("species") or {}
        common_names = species.get("commonNames") or []
        row = {
            "score": item.get("score", 0),
            "scientific_name": species.get("scientificNameWithoutAuthor")
            or species.get("scientificName")
            or "",
            "common_names": common_names,
            "family": ((species.get("family") or {}).get("scientificNameWithoutAuthor") or ""),
            "genus": ((species.get("genus") or {}).get("scientificNameWithoutAuthor") or ""),
        }
        rows.append(row)
        label = row["scientific_name"] or "unknown"
        common = common_names[0] if common_names else ""
        lines.append(
            "%.3f\t%s\t%s" % (float(row["score"] or 0), label, common)
        )
    return ToolResult(
        content="\n".join(lines),
        data={"project": project, "results": rows},
    )


def _fetch_json(url: str, context: ToolContext) -> dict[str, Any]:
    if not context.settings.sandbox_allow_network:
        raise ToolError("Network access is disabled.")
    req = request.Request(
        url,
        headers={"User-Agent": "EcologyHarness/0.1"},
        method="GET",
    )
    try:
        with request.urlopen(req, timeout=context.settings.command_timeout_sec) as response:
            return json.loads(response.read(context.settings.max_web_bytes).decode("utf-8"))
    except error.HTTPError as exc:
        raise ToolError("HTTP error %s for %s" % (exc.code, url)) from exc
    except error.URLError as exc:
        raise ToolError("Connection error for %s: %s" % (url, exc)) from exc
    except json.JSONDecodeError as exc:
        raise ToolError("Invalid JSON response from %s" % url) from exc


def _build_multipart_request(files: list[Path], organs: list[str]) -> tuple[bytes, str]:
    boundary = "----EcologyHarness%s" % uuid.uuid4().hex
    parts: list[bytes] = []
    for organ in organs:
        parts.extend(
            [
                ("--%s\r\n" % boundary).encode("utf-8"),
                b'Content-Disposition: form-data; name="organs"\r\n\r\n',
                organ.encode("utf-8"),
                b"\r\n",
            ]
        )
    for file_path in files:
        mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        parts.extend(
            [
                ("--%s\r\n" % boundary).encode("utf-8"),
                (
                    'Content-Disposition: form-data; name="images"; filename="%s"\r\n'
                    % file_path.name
                ).encode("utf-8"),
                ("Content-Type: %s\r\n\r\n" % mime_type).encode("utf-8"),
                file_path.read_bytes(),
                b"\r\n",
            ]
        )
    parts.append(("--%s--\r\n" % boundary).encode("utf-8"))
    return b"".join(parts), "multipart/form-data; boundary=%s" % boundary


def _resolve_read_path(context: ToolContext, raw_path: str) -> Path:
    sandbox = context.services.get("sandbox")
    if sandbox is not None:
        try:
            return sandbox.resolve_path(raw_path, access="read")
        except Exception as exc:
            raise ToolError(str(exc)) from exc
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = context.settings.workspace_root / candidate
    return candidate.resolve()
