"""Tests for query processor."""

from search_angel.core.query_processor import QueryIntent, QueryProcessor


class TestQueryProcessor:
    def setup_method(self):
        self.processor = QueryProcessor()

    def test_classify_factual(self):
        assert self.processor.classify_intent("what is photosynthesis") == QueryIntent.FACTUAL

    def test_classify_comparison(self):
        assert self.processor.classify_intent("Python vs JavaScript") == QueryIntent.COMPARISON
        assert self.processor.classify_intent("compare React and Vue") == QueryIntent.COMPARISON

    def test_classify_opinion(self):
        assert self.processor.classify_intent("should I learn Rust") == QueryIntent.OPINION
        assert self.processor.classify_intent("best programming language") == QueryIntent.OPINION

    def test_classify_navigational(self):
        assert self.processor.classify_intent("github.com login") == QueryIntent.NAVIGATIONAL
        assert self.processor.classify_intent("download Python") == QueryIntent.NAVIGATIONAL

    def test_classify_investigative(self):
        assert self.processor.classify_intent("why did the stock market crash?") == QueryIntent.INVESTIGATIVE
        assert self.processor.classify_intent("evidence for climate change") == QueryIntent.INVESTIGATIVE

    def test_expand_query_with_acronyms(self):
        expanded = self.processor.expand_query("AI and ML advances")
        assert "artificial intelligence" in expanded
        assert "machine learning" in expanded

    def test_expand_query_no_expansions(self):
        expanded = self.processor.expand_query("regular search terms")
        assert expanded == []

    def test_build_search_params(self):
        params = self.processor.build_search_params("AI research 2024", "deep")
        assert params.original_query == "AI research 2024"
        assert params.processed_query == "AI research 2024"
        assert params.intent == QueryIntent.FACTUAL
        assert "artificial intelligence" in params.expanded_terms
        assert params.metadata["mode"] == "deep"

    def test_fallback_entity_extraction(self):
        entities = self.processor._fallback_entity_extraction(
            "Barack Obama visited New York in 2024"
        )
        entity_texts = [e.text for e in entities]
        assert "Barack Obama" in entity_texts or "New York" in entity_texts
        assert any(e.label == "DATE" for e in entities)
