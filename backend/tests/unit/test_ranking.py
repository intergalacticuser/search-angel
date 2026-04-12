"""Tests for evidence-based ranking."""

from search_angel.core.ranking import EvidenceRanker, EvidenceStats
from search_angel.search.hybrid import RankedDocument


def _make_doc(doc_id: str, rrf: float, credibility: float = 0.5) -> RankedDocument:
    return RankedDocument(
        doc_id=doc_id,
        rrf_score=rrf,
        bm25_score=rrf,
        vector_score=rrf,
        bm25_rank=1,
        vector_rank=1,
        title=f"Doc {doc_id}",
        content="Test content",
        url=f"https://example.com/{doc_id}",
        source={"credibility_score": credibility, "source_type": "news"},
    )


class TestEvidenceRanker:
    def setup_method(self):
        self.ranker = EvidenceRanker()

    def test_basic_ranking_preserves_order(self):
        docs = [
            _make_doc("a", rrf=0.05, credibility=0.9),
            _make_doc("b", rrf=0.03, credibility=0.5),
        ]
        ranked = self.ranker.rerank(docs, mode="standard")
        assert ranked[0].doc_id == "a"
        assert ranked[1].doc_id == "b"

    def test_evidence_boosts_score(self):
        docs = [
            _make_doc("a", rrf=0.04, credibility=0.5),
            _make_doc("b", rrf=0.04, credibility=0.5),
        ]
        evidence_map = {
            "b": EvidenceStats(
                supports_count=5, avg_confidence=0.8
            ),
        }
        ranked = self.ranker.rerank(docs, mode="evidence", evidence_map=evidence_map)
        # Doc b should rank higher due to evidence
        assert ranked[0].doc_id == "b"

    def test_credibility_affects_ranking(self):
        docs = [
            _make_doc("low_cred", rrf=0.04, credibility=0.2),
            _make_doc("high_cred", rrf=0.04, credibility=0.95),
        ]
        ranked = self.ranker.rerank(docs, mode="standard")
        assert ranked[0].doc_id == "high_cred"

    def test_explanation_present(self):
        docs = [_make_doc("a", rrf=0.05)]
        ranked = self.ranker.rerank(docs)
        assert "rrf_component" in ranked[0].explanation
        assert "credibility_component" in ranked[0].explanation

    def test_recency_score_for_none(self):
        score = EvidenceRanker._compute_recency_score(None)
        assert score == 0.3

    def test_originality_unique_doc(self):
        score = EvidenceRanker._compute_originality_score(1)
        assert score == 1.0

    def test_originality_duplicate_cluster(self):
        score = EvidenceRanker._compute_originality_score(10)
        assert score < 1.0
