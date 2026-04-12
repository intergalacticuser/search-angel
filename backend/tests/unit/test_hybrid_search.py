"""Tests for hybrid search RRF fusion."""

from search_angel.search.bm25 import ScoredDocument
from search_angel.search.hybrid import HybridSearchEngine


def _make_scored(doc_id: str, score: float) -> ScoredDocument:
    return ScoredDocument(
        doc_id=doc_id,
        score=score,
        title=f"Doc {doc_id}",
        content="content",
        url=f"https://example.com/{doc_id}",
    )


class TestRRF:
    def test_rrf_basic_fusion(self):
        bm25 = [_make_scored("a", 10.0), _make_scored("b", 8.0), _make_scored("c", 5.0)]
        vector = [_make_scored("b", 0.95), _make_scored("a", 0.90), _make_scored("d", 0.85)]

        # Use a mock engine just to access the static method
        engine = HybridSearchEngine.__new__(HybridSearchEngine)
        fused = engine._reciprocal_rank_fusion(bm25, vector, k=60)

        # Both a and b appear in both lists, so should score highest
        doc_ids = [d.doc_id for d in fused]
        assert "a" in doc_ids[:2]
        assert "b" in doc_ids[:2]

    def test_rrf_document_in_one_list(self):
        bm25 = [_make_scored("a", 10.0)]
        vector = [_make_scored("b", 0.95)]

        engine = HybridSearchEngine.__new__(HybridSearchEngine)
        fused = engine._reciprocal_rank_fusion(bm25, vector, k=60)

        assert len(fused) == 2
        # Both should have equal RRF score (both rank 1 in their list)
        assert fused[0].rrf_score == fused[1].rrf_score

    def test_rrf_scores_positive(self):
        bm25 = [_make_scored("a", 10.0), _make_scored("b", 5.0)]
        vector = [_make_scored("c", 0.9)]

        engine = HybridSearchEngine.__new__(HybridSearchEngine)
        fused = engine._reciprocal_rank_fusion(bm25, vector, k=60)

        for doc in fused:
            assert doc.rrf_score > 0

    def test_rrf_empty_lists(self):
        engine = HybridSearchEngine.__new__(HybridSearchEngine)
        fused = engine._reciprocal_rank_fusion([], [], k=60)
        assert fused == []

    def test_rrf_preserves_metadata(self):
        bm25 = [_make_scored("a", 10.0)]
        vector = []

        engine = HybridSearchEngine.__new__(HybridSearchEngine)
        fused = engine._reciprocal_rank_fusion(bm25, vector, k=60)

        assert fused[0].doc_id == "a"
        assert fused[0].title == "Doc a"
        assert fused[0].bm25_rank == 1
        assert fused[0].vector_rank is None
