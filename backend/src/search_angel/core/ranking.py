"""Evidence-based re-ranking engine."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from search_angel.search.hybrid import RankedDocument

logger = logging.getLogger(__name__)


@dataclass
class RankingWeights:
    rrf: float = 0.5
    credibility: float = 0.2
    evidence: float = 0.15
    recency: float = 0.1
    originality: float = 0.05


# Per-mode weight presets
MODE_WEIGHTS: dict[str, RankingWeights] = {
    "standard": RankingWeights(rrf=0.5, credibility=0.2, evidence=0.15, recency=0.1, originality=0.05),
    "deep": RankingWeights(rrf=0.3, credibility=0.25, evidence=0.25, recency=0.1, originality=0.1),
    "evidence": RankingWeights(rrf=0.3, credibility=0.25, evidence=0.25, recency=0.1, originality=0.1),
    "open_web": RankingWeights(rrf=0.5, credibility=0.2, evidence=0.15, recency=0.1, originality=0.05),
    "compare_narratives": RankingWeights(rrf=0.3, credibility=0.15, evidence=0.15, recency=0.1, originality=0.3),
    "private": RankingWeights(rrf=0.5, credibility=0.2, evidence=0.15, recency=0.1, originality=0.05),
}


@dataclass
class EvidenceStats:
    supports_count: int = 0
    contradicts_count: int = 0
    cites_count: int = 0
    cited_by_count: int = 0
    related_count: int = 0
    avg_confidence: float = 0.0


@dataclass
class RerankedDocument:
    doc_id: str
    final_score: float
    rrf_score: float
    credibility_score: float
    evidence_score: float
    recency_score: float
    originality_score: float
    title: str
    content: str
    url: str
    source: dict[str, Any] = field(default_factory=dict)
    highlight: dict[str, list[str]] = field(default_factory=dict)
    published_at: str | None = None
    evidence_stats: EvidenceStats = field(default_factory=EvidenceStats)
    explanation: dict[str, float] = field(default_factory=dict)


class EvidenceRanker:
    def rerank(
        self,
        documents: list[RankedDocument],
        mode: str = "standard",
        evidence_map: dict[str, EvidenceStats] | None = None,
        duplicate_map: dict[str, int] | None = None,
    ) -> list[RerankedDocument]:
        weights = MODE_WEIGHTS.get(mode, MODE_WEIGHTS["standard"])
        evidence_map = evidence_map or {}
        duplicate_map = duplicate_map or {}

        # Normalize RRF scores to [0, 1]
        max_rrf = max((d.rrf_score for d in documents), default=1.0) or 1.0

        reranked: list[RerankedDocument] = []
        for doc in documents:
            norm_rrf = doc.rrf_score / max_rrf

            # Source credibility (from denormalized source data in doc)
            cred = float(doc.source.get("credibility_score", 0.5))

            # Evidence score
            ev_stats = evidence_map.get(doc.doc_id, EvidenceStats())
            ev_score = self._compute_evidence_score(ev_stats)

            # Recency score (decay over time)
            rec_score = self._compute_recency_score(doc.published_at)

            # Originality score (based on duplicate cluster size)
            cluster_size = duplicate_map.get(doc.doc_id, 1)
            orig_score = self._compute_originality_score(cluster_size)

            # Composite weighted score
            final = (
                weights.rrf * norm_rrf
                + weights.credibility * cred
                + weights.evidence * ev_score
                + weights.recency * rec_score
                + weights.originality * orig_score
            )

            explanation = {
                "rrf_component": weights.rrf * norm_rrf,
                "credibility_component": weights.credibility * cred,
                "evidence_component": weights.evidence * ev_score,
                "recency_component": weights.recency * rec_score,
                "originality_component": weights.originality * orig_score,
            }

            reranked.append(
                RerankedDocument(
                    doc_id=doc.doc_id,
                    final_score=final,
                    rrf_score=doc.rrf_score,
                    credibility_score=cred,
                    evidence_score=ev_score,
                    recency_score=rec_score,
                    originality_score=orig_score,
                    title=doc.title,
                    content=doc.content,
                    url=doc.url,
                    source=doc.source,
                    highlight=doc.highlight,
                    published_at=doc.published_at,
                    evidence_stats=ev_stats,
                    explanation=explanation,
                )
            )

        reranked.sort(key=lambda d: d.final_score, reverse=True)
        return reranked

    @staticmethod
    def _compute_evidence_score(stats: EvidenceStats) -> float:
        if stats.avg_confidence == 0:
            return 0.0
        raw = (
            stats.supports_count * 0.3
            + stats.cites_count * 0.2
            + stats.cited_by_count * 0.15
            - stats.contradicts_count * 0.1
        )
        # Normalize to [0, 1] with sigmoid-like capping
        return min(1.0, max(0.0, raw * stats.avg_confidence))

    @staticmethod
    def _compute_recency_score(published_at: str | None) -> float:
        if not published_at:
            return 0.3  # Neutral score for undated documents

        try:
            pub_date = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            days_old = (now - pub_date).days
            # Exponential decay: half-life of 180 days
            return math.exp(-0.00385 * days_old)
        except (ValueError, TypeError):
            return 0.3

    @staticmethod
    def _compute_originality_score(cluster_size: int) -> float:
        if cluster_size <= 1:
            return 1.0  # Unique document
        # Canonical doc in a large cluster = high originality
        # Score decreases as there are more duplicates (non-canonical)
        return 1.0 / (1.0 + 0.1 * (cluster_size - 1))
