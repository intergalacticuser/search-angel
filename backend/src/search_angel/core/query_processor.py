"""Query processor - intent classification, expansion, and entity extraction."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class QueryIntent(str, Enum):
    FACTUAL = "factual"
    OPINION = "opinion"
    COMPARISON = "comparison"
    NAVIGATIONAL = "navigational"
    INVESTIGATIVE = "investigative"


@dataclass
class Entity:
    text: str
    label: str  # PERSON, ORG, GPE, DATE, etc.


@dataclass
class SearchParams:
    original_query: str
    processed_query: str
    intent: QueryIntent
    entities: list[Entity] = field(default_factory=list)
    expanded_terms: list[str] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)


# Synonym/expansion map for common terms
SYNONYM_MAP: dict[str, list[str]] = {
    "AI": ["artificial intelligence", "machine learning", "deep learning"],
    "ML": ["machine learning"],
    "NLP": ["natural language processing"],
    "COVID": ["COVID-19", "coronavirus", "SARS-CoV-2"],
    "US": ["United States", "America"],
    "UK": ["United Kingdom", "Britain"],
    "EU": ["European Union", "Europe"],
    "GDP": ["gross domestic product"],
    "CEO": ["chief executive officer"],
    "API": ["application programming interface"],
    "IOT": ["internet of things"],
}

# Intent classification patterns
COMPARISON_PATTERNS = [
    r"\bvs\.?\b",
    r"\bversus\b",
    r"\bcompare\b",
    r"\bdifference between\b",
    r"\bcompared to\b",
    r"\bbetter than\b",
    r"\bworse than\b",
]

OPINION_PATTERNS = [
    r"\bshould\b",
    r"\bbest\b",
    r"\brecommend",
    r"\bopinion\b",
    r"\bthink about\b",
    r"\bworth\b",
    r"\bpros and cons\b",
]

NAVIGATIONAL_PATTERNS = [
    r"\bwebsite\b",
    r"\bhomepage\b",
    r"\blogin\b",
    r"\bofficial\b",
    r"\bdownload\b",
    r"\.com\b",
    r"\.org\b",
]

INVESTIGATIVE_PATTERNS = [
    r"\bwhy\b.*\?",
    r"\bhow\b.*\?",
    r"\binvestigat",
    r"\banalyz",
    r"\bevidence\b",
    r"\bproof\b",
    r"\bcause\b",
    r"\breason\b",
    r"\btruth\b",
]


class QueryProcessor:
    def __init__(self) -> None:
        self._spacy_model = None

    def classify_intent(self, query: str) -> QueryIntent:
        q_lower = query.lower()

        for pattern in COMPARISON_PATTERNS:
            if re.search(pattern, q_lower):
                return QueryIntent.COMPARISON

        for pattern in INVESTIGATIVE_PATTERNS:
            if re.search(pattern, q_lower):
                return QueryIntent.INVESTIGATIVE

        for pattern in OPINION_PATTERNS:
            if re.search(pattern, q_lower):
                return QueryIntent.OPINION

        for pattern in NAVIGATIONAL_PATTERNS:
            if re.search(pattern, q_lower):
                return QueryIntent.NAVIGATIONAL

        return QueryIntent.FACTUAL

    def expand_query(self, query: str) -> list[str]:
        expanded: list[str] = []
        words = query.split()
        for word in words:
            upper = word.upper().strip(".,!?;:")
            if upper in SYNONYM_MAP:
                expanded.extend(SYNONYM_MAP[upper])
        return expanded

    def extract_entities(self, query: str) -> list[Entity]:
        try:
            if self._spacy_model is None:
                import spacy

                self._spacy_model = spacy.load("en_core_web_sm")
            doc = self._spacy_model(query)
            return [Entity(text=ent.text, label=ent.label_) for ent in doc.ents]
        except (ImportError, OSError):
            logger.debug("spaCy not available, skipping entity extraction")
            return self._fallback_entity_extraction(query)

    def _fallback_entity_extraction(self, query: str) -> list[Entity]:
        """Basic regex-based entity extraction when spaCy is unavailable."""
        entities: list[Entity] = []
        # Detect capitalized multi-word phrases as potential entities
        for match in re.finditer(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b", query):
            entities.append(Entity(text=match.group(1), label="ENTITY"))

        # Detect years
        for match in re.finditer(r"\b(19|20)\d{2}\b", query):
            entities.append(Entity(text=match.group(0), label="DATE"))

        return entities

    def build_search_params(self, query: str, mode: str = "standard") -> SearchParams:
        intent = self.classify_intent(query)
        entities = self.extract_entities(query)
        expanded = self.expand_query(query)

        processed = query.strip()

        metadata: dict[str, object] = {
            "intent": intent.value,
            "mode": mode,
            "entity_count": len(entities),
            "expansion_count": len(expanded),
        }

        return SearchParams(
            original_query=query,
            processed_query=processed,
            intent=intent,
            entities=entities,
            expanded_terms=expanded,
            metadata=metadata,
        )
