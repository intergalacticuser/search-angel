"""Search endpoints - main search, deep search, narrative comparison."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from search_angel.api.dependencies import get_ip_hash, get_search_pipeline
from search_angel.core.pipeline import PipelineRequest, SearchPipeline
from search_angel.models.schemas.common import SearchMode, SourceInfo
from search_angel.models.schemas.search import (
    CategorySearchRequest,
    CategorySearchResponse,
    CompareRequest,
    CompareResponse,
    DeepSearchResponse,
    PerspectiveGroup,
    QueryMetadata,
    SearchFilterSchema,
    SearchRequest,
    SearchResponse,
    SearchResult,
    SummarySchema,
    CitationSchema,
)
from search_angel.privacy.audit import PrivacyAuditor
from search_angel.search.bm25 import SearchFilters

router = APIRouter(prefix="/search", tags=["search"])


def _to_search_filters(schema: SearchFilterSchema | None) -> SearchFilters | None:
    if schema is None:
        return None
    return SearchFilters(
        date_from=schema.date_from,
        date_to=schema.date_to,
        source_types=schema.source_types or [],
        language=schema.language,
        min_credibility=schema.min_credibility,
    )


def _to_search_result(doc: object) -> SearchResult:
    source_data = getattr(doc, "source", {})
    highlight = getattr(doc, "highlight", {})

    # Build snippet from highlight or content
    if highlight and "content" in highlight:
        snippet = " ... ".join(highlight["content"][:2])
    else:
        content = getattr(doc, "content", "")
        snippet = content[:300] + "..." if len(content) > 300 else content

    return SearchResult(
        id=getattr(doc, "doc_id", ""),
        url=getattr(doc, "url", ""),
        title=getattr(doc, "title", ""),
        snippet=snippet,
        score=round(getattr(doc, "final_score", getattr(doc, "rrf_score", 0.0)), 4),
        source=SourceInfo(
            source_id=source_data.get("source_id"),
            domain=source_data.get("domain", "unknown"),
            name=source_data.get("name"),
            source_type=source_data.get("source_type", "unknown"),
            credibility_score=float(source_data.get("credibility_score", 0.5)),
            bias_label=source_data.get("bias_label", "unknown"),
        ),
        evidence_count=getattr(
            getattr(doc, "evidence_stats", None), "supports_count", 0
        ) + getattr(
            getattr(doc, "evidence_stats", None), "contradicts_count", 0
        ),
        published_at=getattr(doc, "published_at", None),
        explanation=getattr(doc, "explanation", None),
        category=getattr(doc, "category", "general"),
        thumbnail=getattr(doc, "thumbnail", None),
        img_src=getattr(doc, "img_src", None),
        video_url=getattr(doc, "video_url", None),
        iframe_src=getattr(doc, "iframe_src", None),
        author=getattr(doc, "author", None),
        media_metadata=getattr(doc, "metadata", None) or None,
    )


@router.post("", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    pipeline: SearchPipeline = Depends(get_search_pipeline),
    ip_hash: str = Depends(get_ip_hash),
) -> SearchResponse:
    """Main search endpoint supporting all search modes."""
    pipe_request = PipelineRequest(
        query=request.query,
        mode=request.mode.value,
        filters=_to_search_filters(request.filters),
        include_summary=request.include_summary,
        offset=request.offset,
        limit=request.limit,
    )

    result = await pipeline.execute(pipe_request)

    # Audit log (no query content)
    PrivacyAuditor.log_search(ip_hash, request.mode.value, result.total)

    # Build response
    query_meta = None
    if result.query_params:
        query_meta = QueryMetadata(
            intent=result.query_params.intent.value,
            mode=result.query_params.metadata.get("mode", "standard"),  # type: ignore[arg-type]
            entity_count=len(result.query_params.entities),
            expansion_count=len(result.query_params.expanded_terms),
            entities=[
                {"text": e.text, "label": e.label}
                for e in result.query_params.entities
            ],
            expanded_terms=result.query_params.expanded_terms,
        )

    summary = None
    if result.summary:
        summary = SummarySchema(
            text=result.summary.text,
            citations=[
                CitationSchema(
                    doc_id=c.doc_id, title=c.title, url=c.url, relevance=c.relevance
                )
                for c in result.summary.citations
            ],
            model_used=result.summary.model_used,
            confidence=result.summary.confidence,
        )

    return SearchResponse(
        results=[_to_search_result(doc) for doc in result.results],
        total=result.total,
        summary=summary,
        query_metadata=query_meta,
        timing_ms=result.timing_ms,
    )


@router.post("/deep", response_model=DeepSearchResponse)
async def deep_search(
    request: SearchRequest,
    pipeline: SearchPipeline = Depends(get_search_pipeline),
    ip_hash: str = Depends(get_ip_hash),
) -> DeepSearchResponse:
    """Deep search with evidence chains and comprehensive analysis."""
    pipe_request = PipelineRequest(
        query=request.query,
        mode=SearchMode.DEEP.value,
        filters=_to_search_filters(request.filters),
        include_summary=True,
        offset=request.offset,
        limit=request.limit,
    )

    result = await pipeline.execute(pipe_request)
    PrivacyAuditor.log_search(ip_hash, "deep", result.total)

    # Build source distribution
    source_dist: dict[str, int] = {}
    for doc in result.results:
        src_type = getattr(doc, "source", {}).get("source_type", "unknown")
        source_dist[src_type] = source_dist.get(src_type, 0) + 1

    query_meta = None
    if result.query_params:
        query_meta = QueryMetadata(
            intent=result.query_params.intent.value,
            mode="deep",
            entity_count=len(result.query_params.entities),
            expansion_count=len(result.query_params.expanded_terms),
        )

    summary = None
    if result.summary:
        summary = SummarySchema(
            text=result.summary.text,
            citations=[
                CitationSchema(
                    doc_id=c.doc_id, title=c.title, url=c.url, relevance=c.relevance
                )
                for c in result.summary.citations
            ],
            model_used=result.summary.model_used,
            confidence=result.summary.confidence,
        )

    return DeepSearchResponse(
        results=[_to_search_result(doc) for doc in result.results],
        total=result.total,
        summary=summary,
        query_metadata=query_meta,
        timing_ms=result.timing_ms,
        evidence_graph=[],  # Populated when evidence DB is seeded
        source_distribution=source_dist,
        confidence_assessment=result.summary.confidence if result.summary else "unknown",
    )


@router.post("/compare", response_model=CompareResponse)
async def compare_narratives(
    request: CompareRequest,
    pipeline: SearchPipeline = Depends(get_search_pipeline),
    ip_hash: str = Depends(get_ip_hash),
) -> CompareResponse:
    """Compare narratives across different sources/perspectives."""
    pipe_request = PipelineRequest(
        query=request.query,
        mode=SearchMode.COMPARE_NARRATIVES.value,
        filters=_to_search_filters(request.filters),
        include_summary=True,
        offset=0,
        limit=50,  # Fetch more to find diverse perspectives
    )

    result = await pipeline.execute(pipe_request)
    PrivacyAuditor.log_search(ip_hash, "compare_narratives", result.total)

    # Group results by bias label to create perspectives
    bias_groups: dict[str, list[object]] = {}
    for doc in result.results:
        bias = getattr(doc, "source", {}).get("bias_label", "unknown")
        bias_groups.setdefault(bias, []).append(doc)

    perspectives: list[PerspectiveGroup] = []
    bias_labels = {
        "left": "Left-leaning sources",
        "center_left": "Center-left sources",
        "center": "Centrist/neutral sources",
        "center_right": "Center-right sources",
        "right": "Right-leaning sources",
        "unknown": "Unclassified sources",
    }

    for bias, docs in sorted(bias_groups.items()):
        if docs:
            perspectives.append(
                PerspectiveGroup(
                    label=bias_labels.get(bias, f"{bias} sources"),
                    source_bias=bias,
                    results=[_to_search_result(d) for d in docs[:5]],
                )
            )

    summary_text = result.summary.text if result.summary else ""

    return CompareResponse(
        query=request.query,
        perspectives=perspectives[:request.perspectives],
        summary=summary_text,
        timing_ms=result.timing_ms,
    )


@router.post("/category", response_model=CategorySearchResponse)
async def category_search(
    request: CategorySearchRequest,
    pipeline: SearchPipeline = Depends(get_search_pipeline),
    ip_hash: str = Depends(get_ip_hash),
) -> CategorySearchResponse:
    """Search a specific media category: images, videos, news, science, books, music, files."""
    import time

    start = time.monotonic()

    # Get appropriate web retriever (Tor or normal)
    if request.tor_mode:
        from search_angel.api.dependencies import get_web_retriever_tor
        from search_angel.config import get_settings
        web = get_web_retriever_tor(get_settings())
    else:
        web = pipeline._hybrid_engine._web
        if web is None:
            from search_angel.api.dependencies import get_web_retriever
            from search_angel.config import get_settings
            web = get_web_retriever(get_settings())

    if web is None:
        return CategorySearchResponse(
            results=[], total=0, category=request.category, timing_ms=0.0
        )

    results = await web.search_category(
        request.query,
        request.category,
        top_k=request.limit + request.offset,
    )

    PrivacyAuditor.log_search(ip_hash, f"category:{request.category}", len(results))

    # Paginate
    page = results[request.offset : request.offset + request.limit]
    elapsed = (time.monotonic() - start) * 1000

    return CategorySearchResponse(
        results=[_to_search_result(doc) for doc in page],
        total=len(results),
        category=request.category,
        timing_ms=round(elapsed, 2),
    )
