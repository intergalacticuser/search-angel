"""Full search pipeline orchestrator."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from search_angel.core.deduplication import Deduplicator
from search_angel.core.query_processor import QueryProcessor, SearchParams
from search_angel.core.ranking import EvidenceRanker, EvidenceStats, RerankedDocument
from search_angel.core.summarizer import Summarizer, SummaryResult
from search_angel.search.bm25 import SearchFilters
from search_angel.search.hybrid import HybridSearchEngine

logger = logging.getLogger(__name__)


@dataclass
class PipelineRequest:
    query: str
    mode: str = "standard"
    filters: SearchFilters | None = None
    include_summary: bool = False
    offset: int = 0
    limit: int = 10


@dataclass
class PipelineResponse:
    results: list[RerankedDocument]
    total: int
    summary: SummaryResult | None = None
    query_params: SearchParams | None = None
    timing_ms: float = 0.0
    metadata: dict[str, object] = field(default_factory=dict)


class SearchPipeline:
    """Orchestrates the full search pipeline:
    query_processor -> hybrid_engine -> ranker -> deduplicator -> summarizer
    """

    def __init__(
        self,
        query_processor: QueryProcessor,
        hybrid_engine: HybridSearchEngine,
        ranker: EvidenceRanker,
        deduplicator: Deduplicator,
        summarizer: Summarizer,
    ) -> None:
        self._query_processor = query_processor
        self._hybrid_engine = hybrid_engine
        self._ranker = ranker
        self._deduplicator = deduplicator
        self._summarizer = summarizer

    async def execute(self, request: PipelineRequest) -> PipelineResponse:
        start = time.monotonic()

        # 1. Process query
        params = self._query_processor.build_search_params(
            request.query, request.mode
        )
        logger.info(
            "Query processed: intent=%s, entities=%d, expansions=%d",
            params.intent.value,
            len(params.entities),
            len(params.expanded_terms),
        )

        # 2. Hybrid retrieval (BM25 + vector in parallel)
        candidates = await self._hybrid_engine.search(
            params.processed_query,
            mode=request.mode,
            filters=request.filters,
            expanded_terms=params.expanded_terms,
        )
        logger.info("Hybrid search returned %d candidates", len(candidates))

        # 3. Evidence-based re-ranking
        # In production, evidence_map would be loaded from PostgreSQL
        evidence_map: dict[str, EvidenceStats] = {}
        ranked = self._ranker.rerank(
            candidates,
            mode=request.mode,
            evidence_map=evidence_map,
        )

        # 4. Deduplication
        deduplicated = self._deduplicator.collapse(ranked)
        logger.info(
            "After dedup: %d -> %d results", len(ranked), len(deduplicated)
        )

        # 5. Optional AI summary
        summary = None
        should_summarize = (
            request.mode in ("deep", "evidence", "compare_narratives")
            or request.include_summary
        )
        if should_summarize and deduplicated:
            summary = await self._summarizer.summarize(
                request.query, deduplicated[:10], request.mode
            )

        # 6. Paginate
        total = len(deduplicated)
        page = deduplicated[request.offset : request.offset + request.limit]

        elapsed = (time.monotonic() - start) * 1000

        return PipelineResponse(
            results=page,
            total=total,
            summary=summary,
            query_params=params,
            timing_ms=round(elapsed, 2),
            metadata={
                "candidates_before_rerank": len(candidates),
                "candidates_before_dedup": len(ranked),
                "mode": request.mode,
                "intent": params.intent.value,
            },
        )
