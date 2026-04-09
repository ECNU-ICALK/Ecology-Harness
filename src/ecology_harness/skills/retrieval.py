from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
import math
from pathlib import Path
import re
from typing import Any, Protocol

from ecology_harness.runtime.messages import ChatMessage


class SkillRecord(Protocol):
    slug: str
    name: str
    description: str
    source: str
    content: str
    path: Path
    triggers: list[str]
    tools: list[str]
    when_to_use: str
    argument_hint: str
    arguments: list[str]
    model: str
    context: str
    user_invocable: bool


_EN_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "please",
    "show",
    "that",
    "the",
    "this",
    "to",
    "use",
    "using",
    "want",
    "we",
    "what",
    "with",
}

_ZH_STOPWORDS = {
    "一个",
    "一下",
    "以及",
    "我们",
    "怎么",
    "如何",
    "帮我",
    "我想",
    "有关",
    "关于",
    "可以",
    "哪个",
    "哪些",
    "这个",
    "这些",
    "那个",
    "那些",
    "还有",
    "进行",
    "需要",
}

_DEICTIC_HINTS = (
    "这个",
    "这个问题",
    "这个场景",
    "这个系统",
    "这里",
    "上述",
    "上面",
    "前面",
    "刚才",
    "继续",
    "接着",
    "它",
    "它们",
    "this",
    "that",
    "continue",
)

_DOMAIN_EXPANSIONS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("植物生长模拟", ("plant growth simulation", "crop growth model", "phenology", "biomass")),
    ("植物成长模拟", ("plant growth simulation", "crop growth model", "phenology", "biomass")),
    ("植物生长", ("plant growth", "crop growth", "phenology", "biomass")),
    ("植物", ("plant", "crop", "vegetation")),
    ("作物", ("crop", "agriculture", "yield")),
    ("玉米", ("maize", "corn")),
    ("小麦", ("wheat",)),
    ("水稻", ("rice",)),
    ("森林", ("forest", "woody plant", "stand dynamics")),
    ("木本", ("woody plant", "forest")),
    ("根系", ("root", "root architecture", "rhizosphere")),
    ("根际", ("rhizosphere", "root microbiome")),
    ("灌溉", ("irrigation", "water balance", "evapotranspiration")),
    ("干旱", ("drought", "water stress")),
    ("蒸散", ("evapotranspiration", "et")),
    ("水分平衡", ("water balance", "soil water")),
    ("流域", ("watershed", "hydrology", "ecohydrology")),
    ("水文", ("hydrology", "ecohydrology")),
    ("生态水文", ("ecohydrology", "watershed")),
    ("食物网", ("food web", "trophic", "ecosim")),
    ("营养级", ("trophic", "food web")),
    ("景观", ("landscape", "connectivity", "disturbance")),
    ("火干扰", ("fire disturbance", "landscape disturbance")),
    ("物种分布", ("species distribution", "occurrence", "range shift")),
    ("扩散", ("dispersal", "range shift", "connectivity")),
    ("个体行为", ("agent based", "abm", "behavior")),
    ("主体模型", ("agent based", "abm")),
    ("行为", ("behavior", "pose tracking")),
    ("群落", ("community", "assembly")),
    ("种群", ("population", "population dynamics")),
    ("微生物生态", ("microbial ecology", "microbiome", "community metabolism")),
    ("微生物群落", ("microbial community", "microbiome", "community metabolism")),
    ("微生物", ("microbial", "microbe", "microbiome")),
    ("代谢", ("metabolism", "metabolic", "flux")),
    ("代谢重建", ("metabolic reconstruction", "carveme", "cobrapy")),
    ("交叉喂养", ("cross feeding", "community metabolism")),
    ("共喂养", ("cross feeding", "community metabolism")),
    ("生物膜", ("biofilm", "periphyton", "reactor simulation")),
    ("反应器", ("reactor", "ode system", "biofilm")),
    ("藻类", ("algae", "microalgae")),
    ("浮游植物", ("phytoplankton", "algae", "microalgae")),
    ("浮游动物", ("zooplankton", "daphnia", "rotifer", "copepod")),
    ("底栖藻类", ("benthic algae", "periphyton", "biofilm")),
    ("底栖", ("benthic", "periphyton")),
    ("大型溞", ("daphnia magna", "daphnia")),
    ("轮虫", ("rotifer", "brachionus")),
    ("桡足类", ("copepod", "cyclops")),
    ("小球藻", ("chlorella vulgaris", "chlorella")),
    ("铜绿微囊藻", ("microcystis aeruginosa", "microcystis")),
    ("显微", ("microscopy", "image analysis", "classification")),
    ("显微镜", ("microscopy", "image analysis", "classification")),
    ("光谱", ("spectra", "spectral", "fluorescence")),
    ("荧光", ("fluorescence", "chlorophyll", "phycocyanin")),
    ("叶绿素", ("chlorophyll", "fluorescence")),
    ("藻蓝蛋白", ("phycocyanin", "fluorescence")),
    ("pcr", ("pcr", "amplicon", "sequencing")),
    ("扩增子", ("amplicon", "sequencing", "microbiome")),
    ("文献", ("literature", "paper", "evidence synthesis")),
    ("综述", ("literature review", "evidence synthesis")),
    ("统计", ("statistical analysis", "analysis")),
    ("可视化", ("visualization", "plotting", "figure")),
    ("科研绘图", ("scientific visualization", "plotting", "figure")),
    ("遥感", ("remote sensing", "satellite", "geospatial")),
    ("地理空间", ("geospatial", "gis", "remote sensing")),
    ("协议", ("protocol", "lab notebook")),
    ("实验记录", ("lab notebook", "provenance")),
)

_INTENT_PATTERNS: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    ("select-model", ("选择", "选型", "适合", "哪个模型", "哪种模型", "model selection", "best model"), ("model selection", "toolchain choice")),
    ("compare-models", ("比较", "对比", "比较一下", "cross-model", "compare"), ("model comparison", "cross model comparison")),
    ("design-workflow", ("设计", "规划", "workflow", "方案", "pipeline"), ("workflow design", "analysis workflow")),
    ("run-simulation", ("模拟", "仿真", "情景", "scenario", "simulate"), ("simulation run", "scenario analysis")),
    ("calibrate-validate", ("校准", "验证", "敏感性", "不确定性", "calibration", "validation", "sensitivity"), ("calibration", "validation", "sensitivity analysis")),
    ("monitoring-plan", ("监测", "监控", "跟踪", "观测", "monitor", "tracking"), ("monitoring plan", "observation workflow")),
    ("data-discovery", ("数据集", "数据", "dataset", "find data", "repository"), ("dataset discovery", "data sourcing")),
    ("literature-search", ("文献", "论文", "综述", "paper", "literature", "citation"), ("literature search", "evidence synthesis")),
    ("classification-identification", ("识别", "分类", "identify", "classification"), ("classification", "identification")),
    ("analysis-interpretation", ("分析", "解释", "解读", "interpret", "analyze"), ("analysis", "interpretation")),
    ("tool-execution", ("运行", "执行", "调用", "run", "execute", "call"), ("tool execution", "runtime execution")),
)

_MODALITY_PATTERNS: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    ("text", ("文献", "文本", "笔记", "markdown", "report", "paper"), ("text", "document")),
    ("document", ("pdf", "docx", "文档", "报告", "notebook"), ("document", "report")),
    ("image", ("图片", "照片", "图像", "image", "photo"), ("image", "photo")),
    ("video", ("视频", "video", "camera trap"), ("video", "frame sequence")),
    ("audio", ("音频", "声音", "鸟鸣", "audio", "acoustic"), ("audio", "ecoacoustics")),
    ("microscopy", ("显微", "显微镜", "microscopy", "cell"), ("microscopy", "image analysis")),
    ("timeseries", ("时间序列", "连续监测", "timeseries", "time series"), ("time series", "sensor logging")),
    ("geospatial", ("遥感", "地理空间", "栅格", "矢量", "地图", "satellite", "gis"), ("geospatial", "remote sensing")),
    ("omics", ("扩增子", "测序", "代谢重建", "amplicon", "omics", "blast"), ("omics", "sequence workflow")),
)

_SCALE_PATTERNS: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    ("organism", ("个体", "单株", "单个生物", "organism"), ("organism scale",)),
    ("population", ("种群", "population", "metapopulation"), ("population scale",)),
    ("community", ("群落", "community", "food web"), ("community scale",)),
    ("ecosystem", ("生态系统", "ecosystem", "biogeochemistry"), ("ecosystem scale",)),
    ("plot-field", ("田块", "样地", "地块", "field", "plot"), ("plot scale", "field scale")),
    ("watershed", ("流域", "watershed", "catchment"), ("watershed scale",)),
    ("landscape", ("景观", "连通性", "landscape"), ("landscape scale",)),
    ("regional", ("区域", "regional", "province"), ("regional scale",)),
    ("global", ("全球", "global change", "global"), ("global scale",)),
    ("lab-reactor", ("反应器", "微宇宙", "培养", "biofilm reactor", "microcosm"), ("lab reactor", "microcosm")),
)

_OUTPUT_PATTERNS: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    ("workflow-plan", ("方案", "流程", "workflow", "pipeline"), ("workflow plan",)),
    ("tool-recommendation", ("推荐", "适合", "best", "recommend"), ("tool recommendation",)),
    ("scenario-matrix", ("情景", "scenario", "treatment"), ("scenario matrix",)),
    ("calibration-plan", ("校准", "验证", "sensitivity", "uncertainty"), ("calibration plan", "validation plan")),
    ("monitoring-panel", ("监测指标", "panel", "监测面板"), ("monitoring panel",)),
    ("comparison-table", ("比较", "对比", "compare"), ("comparison table",)),
)

REWRITE_PROMPT_SPEC = """\
Rewrite the user's request into a retrieval-oriented intent query.

Goals:
1. Preserve the real research intent instead of copying surface wording.
2. Resolve vague references from recent user context when available.
3. Normalize Chinese and English domain terms into canonical retrieval language.
4. Surface task intent, target system, scale, modality, constraints, and desired outputs.
5. Expand only with high-confidence ecological, environmental, agricultural, or scientific synonyms.

Required slots:
- intent
- target_system
- entities_or_stressors
- scale
- modality_or_data
- method_family
- constraints
- desired_outputs
- bilingual_synonyms

Output style:
- compact
- retrieval oriented
- no conversational filler
- prioritize discriminative technical terms
"""


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        normalized = item.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _strip_trigger_prefix(text: str) -> str:
    normalized = _normalize_whitespace(text)
    if normalized.startswith("/") and " " in normalized:
        return normalized.split(" ", 1)[1].strip()
    return normalized


def tokenize_text(text: str) -> list[str]:
    normalized = (text or "").lower()
    tokens: list[str] = []

    for token in re.findall(r"[a-z0-9][a-z0-9\-\+._/]*", normalized):
        base = token.strip("./")
        if base and base not in _EN_STOPWORDS:
            tokens.append(base)
        for part in re.split(r"[-+_./]+", base):
            if len(part) > 1 and part not in _EN_STOPWORDS:
                tokens.append(part)

    for run in re.findall(r"[\u4e00-\u9fff]+", normalized):
        if run and run not in _ZH_STOPWORDS:
            tokens.append(run)
        if len(run) == 1:
            continue
        for idx in range(len(run) - 1):
            piece = run[idx : idx + 2]
            if piece not in _ZH_STOPWORDS:
                tokens.append(piece)

    return _unique(tokens)


def _needs_context(query: str) -> bool:
    normalized = query.lower()
    if any(hint in normalized for hint in _DEICTIC_HINTS):
        return True
    return len(tokenize_text(normalized)) <= 4


def _summarize_message(message: ChatMessage) -> str:
    return _normalize_whitespace(message.summary_text(max_document_chars=160))


def _extract_context(query: str, conversation: list[ChatMessage] | None, max_items: int) -> list[str]:
    if not conversation or not _needs_context(query):
        return []
    snippets: list[str] = []
    normalized_query = _normalize_whitespace(query)
    for message in reversed(conversation):
        if message.role != "user":
            continue
        snippet = _summarize_message(message)
        if not snippet or snippet == normalized_query:
            continue
        snippets.append(snippet)
        if len(snippets) >= max_items:
            break
    snippets.reverse()
    return snippets


def _expand_terms(text: str) -> list[str]:
    lowered = text.lower()
    expanded: list[str] = []
    for phrase, terms in _DOMAIN_EXPANSIONS:
        if phrase.lower() in lowered:
            expanded.extend(terms)
    return _unique(expanded)


def _skill_excerpt(content: str, max_chars: int = 1800) -> str:
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if not lines:
        return ""
    interesting = lines[:20]
    excerpt = " ".join(interesting)
    if len(excerpt) > max_chars:
        excerpt = excerpt[:max_chars].rstrip() + "..."
    return excerpt


def _build_document_text(skill: SkillRecord) -> str:
    tokens: list[str] = []
    tokens.extend([skill.name] * 4)
    tokens.extend([skill.slug] * 4)
    tokens.extend(skill.triggers * 3)
    if skill.description:
        tokens.extend([skill.description] * 3)
    if skill.when_to_use:
        tokens.extend([skill.when_to_use] * 2)
    if skill.argument_hint:
        tokens.append(skill.argument_hint)
    if skill.arguments:
        tokens.extend(skill.arguments)
    if skill.tools:
        tokens.extend(skill.tools)
    excerpt = _skill_excerpt(skill.content)
    if excerpt:
        tokens.append(excerpt)
    path_hint = " ".join(part for part in skill.path.parts[-4:] if part not in {"SKILL.md", ".md"})
    if path_hint:
        tokens.append(path_hint)
    return "\n".join(tokens)


@dataclass
class SkillQueryRewrite:
    original_query: str
    normalized_query: str
    context_snippets: list[str] = field(default_factory=list)
    intent_labels: list[str] = field(default_factory=list)
    target_labels: list[str] = field(default_factory=list)
    modality_labels: list[str] = field(default_factory=list)
    scale_labels: list[str] = field(default_factory=list)
    output_labels: list[str] = field(default_factory=list)
    expanded_terms: list[str] = field(default_factory=list)
    rewrite_spec: str = REWRITE_PROMPT_SPEC
    rewritten_query: str = ""
    query_tokens: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_query": self.original_query,
            "normalized_query": self.normalized_query,
            "context_snippets": self.context_snippets,
            "intent_labels": self.intent_labels,
            "target_labels": self.target_labels,
            "modality_labels": self.modality_labels,
            "scale_labels": self.scale_labels,
            "output_labels": self.output_labels,
            "expanded_terms": self.expanded_terms,
            "rewrite_spec": self.rewrite_spec,
            "rewritten_query": self.rewritten_query,
            "query_tokens": self.query_tokens,
        }


def _extract_labels(
    text: str,
    patterns: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...],
) -> tuple[list[str], list[str]]:
    lowered = text.lower()
    labels: list[str] = []
    expansions: list[str] = []
    for label, triggers, synonyms in patterns:
        if any(trigger.lower() in lowered for trigger in triggers):
            labels.append(label)
            expansions.extend(synonyms)
    return _unique(labels), _unique(expansions)


def _extract_target_labels(text: str) -> tuple[list[str], list[str]]:
    lowered = text.lower()
    labels: list[str] = []
    expansions: list[str] = []
    for phrase, synonyms in _DOMAIN_EXPANSIONS:
        if phrase.lower() in lowered:
            labels.append(phrase)
            expansions.extend(synonyms)
    return _unique(labels), _unique(expansions)


def _build_rewritten_query(
    normalized: str,
    context_snippets: list[str],
    intent_labels: list[str],
    target_labels: list[str],
    modality_labels: list[str],
    scale_labels: list[str],
    output_labels: list[str],
    expanded_terms: list[str],
) -> str:
    parts: list[str] = []
    if normalized:
        parts.append(normalized)
    if context_snippets:
        parts.append("context: " + " | ".join(context_snippets))
    if intent_labels:
        parts.append("intent: " + " ".join(intent_labels))
    if target_labels:
        parts.append("target: " + " ".join(target_labels))
    if scale_labels:
        parts.append("scale: " + " ".join(scale_labels))
    if modality_labels:
        parts.append("modality: " + " ".join(modality_labels))
    if output_labels:
        parts.append("desired_output: " + " ".join(output_labels))
    if expanded_terms:
        parts.append("synonyms: " + " ".join(expanded_terms))
    return _normalize_whitespace(" ".join(parts))


class SkillQueryRewriter:
    def __init__(self, history_turns: int = 4) -> None:
        self.history_turns = history_turns

    def rewrite(
        self,
        query: str,
        conversation: list[ChatMessage] | None = None,
    ) -> SkillQueryRewrite:
        normalized = _strip_trigger_prefix(query)
        context_snippets = _extract_context(normalized, conversation, self.history_turns)
        analysis_text = " ".join([normalized] + context_snippets)
        target_labels, target_expansions = _extract_target_labels(analysis_text)
        intent_labels, intent_expansions = _extract_labels(analysis_text, _INTENT_PATTERNS)
        modality_labels, modality_expansions = _extract_labels(analysis_text, _MODALITY_PATTERNS)
        scale_labels, scale_expansions = _extract_labels(analysis_text, _SCALE_PATTERNS)
        output_labels, output_expansions = _extract_labels(analysis_text, _OUTPUT_PATTERNS)
        expanded_terms = _unique(
            _expand_terms(analysis_text)
            + target_expansions
            + intent_expansions
            + modality_expansions
            + scale_expansions
            + output_expansions
        )
        rewritten_query = _build_rewritten_query(
            normalized=normalized,
            context_snippets=context_snippets,
            intent_labels=intent_labels,
            target_labels=target_labels,
            modality_labels=modality_labels,
            scale_labels=scale_labels,
            output_labels=output_labels,
            expanded_terms=expanded_terms,
        )
        query_tokens = tokenize_text(rewritten_query)

        return SkillQueryRewrite(
            original_query=query,
            normalized_query=normalized,
            context_snippets=context_snippets,
            intent_labels=intent_labels,
            target_labels=target_labels,
            modality_labels=modality_labels,
            scale_labels=scale_labels,
            output_labels=output_labels,
            expanded_terms=expanded_terms,
            rewritten_query=rewritten_query,
            query_tokens=query_tokens,
        )


@dataclass
class SkillSearchHit:
    skill: SkillRecord
    score: float
    matched_terms: list[str] = field(default_factory=list)
    exact_match: bool = False

    def to_index_dict(self) -> dict[str, Any]:
        payload = {
            "score": round(self.score, 4),
            "matched_terms": self.matched_terms,
            "exact_match": self.exact_match,
        }
        payload.update(getattr(self.skill, "to_index_dict")())
        return payload


@dataclass
class SkillSearchReport:
    rewrite: SkillQueryRewrite
    hits: list[SkillSearchHit]
    total_skills: int
    fallback_used: bool = False

    def to_prompt_dict(self) -> dict[str, Any]:
        return {
            "original_query": self.rewrite.original_query,
            "rewritten_query": self.rewrite.rewritten_query,
            "context_snippets": self.rewrite.context_snippets,
            "expanded_terms": self.rewrite.expanded_terms,
            "total_skills": self.total_skills,
            "fallback_used": self.fallback_used,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.rewrite.to_dict(),
            "total_skills": self.total_skills,
            "fallback_used": self.fallback_used,
            "hits": [item.to_index_dict() for item in self.hits],
        }


class SkillBM25Retriever:
    def __init__(self, skills: list[SkillRecord]) -> None:
        self.skills = skills
        self.documents = [_build_document_text(skill) for skill in skills]
        self.doc_tokens = [tokenize_text(document) for document in self.documents]
        self.doc_lengths = [len(tokens) for tokens in self.doc_tokens]
        self.avgdl = sum(self.doc_lengths) / len(self.doc_lengths) if self.doc_lengths else 0.0
        self.term_freqs = [Counter(tokens) for tokens in self.doc_tokens]
        self.doc_freqs: Counter[str] = Counter()
        for tokens in self.doc_tokens:
            self.doc_freqs.update(set(tokens))

    def search(self, rewrite: SkillQueryRewrite, limit: int = 8) -> list[SkillSearchHit]:
        if not self.skills:
            return []
        query_tokens = rewrite.query_tokens
        if not query_tokens:
            return []

        hits: list[SkillSearchHit] = []
        query_text = rewrite.rewritten_query.lower()
        for idx, skill in enumerate(self.skills):
            score = self._score_document(idx, query_tokens)
            exact_match = False
            if skill.slug.lower() in query_text or skill.name.lower() in query_text:
                score += 5.0
                exact_match = True
            for trigger in skill.triggers:
                if trigger.lower() in query_text:
                    score += 8.0
                    exact_match = True
            matched_terms = [term for term in query_tokens if term in self.term_freqs[idx]]
            if matched_terms:
                score += min(len(matched_terms), 6) * 0.15
            if score <= 0:
                continue
            hits.append(
                SkillSearchHit(
                    skill=skill,
                    score=score,
                    matched_terms=_unique(matched_terms)[:8],
                    exact_match=exact_match,
                )
            )
        hits.sort(
            key=lambda item: (
                -item.score,
                0 if item.exact_match else 1,
                item.skill.name.lower(),
            )
        )
        return hits[:limit]

    def _score_document(self, doc_index: int, query_tokens: list[str], k1: float = 1.5, b: float = 0.75) -> float:
        score = 0.0
        freqs = self.term_freqs[doc_index]
        doc_len = self.doc_lengths[doc_index] or 1
        avgdl = self.avgdl or 1.0
        for term in query_tokens:
            term_freq = freqs.get(term, 0)
            if not term_freq:
                continue
            doc_freq = self.doc_freqs.get(term, 0)
            idf = math.log(1.0 + ((len(self.skills) - doc_freq + 0.5) / (doc_freq + 0.5)))
            denom = term_freq + k1 * (1.0 - b + b * (doc_len / avgdl))
            score += idf * ((term_freq * (k1 + 1.0)) / denom)
        return score
