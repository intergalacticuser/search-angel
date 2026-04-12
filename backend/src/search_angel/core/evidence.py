"""Evidence layer - source classification and contradiction detection."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Known source classifications - comprehensive database
SOURCE_CLASSIFICATIONS: dict[str, dict[str, object]] = {
    # ── Wire services / Agencies (highest credibility) ───────────────
    "reuters.com": {"type": "news", "credibility": 0.95, "bias": "center"},
    "apnews.com": {"type": "news", "credibility": 0.95, "bias": "center"},
    "afp.com": {"type": "news", "credibility": 0.9, "bias": "center"},
    # ── Major international news ─────────────────────────────────────
    "bbc.com": {"type": "news", "credibility": 0.88, "bias": "center"},
    "bbc.co.uk": {"type": "news", "credibility": 0.88, "bias": "center"},
    "nytimes.com": {"type": "news", "credibility": 0.82, "bias": "center_left"},
    "washingtonpost.com": {"type": "news", "credibility": 0.8, "bias": "center_left"},
    "wsj.com": {"type": "news", "credibility": 0.82, "bias": "center_right"},
    "economist.com": {"type": "news", "credibility": 0.88, "bias": "center"},
    "theguardian.com": {"type": "news", "credibility": 0.78, "bias": "center_left"},
    "ft.com": {"type": "news", "credibility": 0.85, "bias": "center"},
    "bloomberg.com": {"type": "news", "credibility": 0.83, "bias": "center"},
    "aljazeera.com": {"type": "news", "credibility": 0.72, "bias": "center_left"},
    "dw.com": {"type": "news", "credibility": 0.8, "bias": "center"},
    "france24.com": {"type": "news", "credibility": 0.78, "bias": "center"},
    "abc.net.au": {"type": "news", "credibility": 0.82, "bias": "center"},
    "cbc.ca": {"type": "news", "credibility": 0.8, "bias": "center"},
    "npr.org": {"type": "news", "credibility": 0.82, "bias": "center_left"},
    "pbs.org": {"type": "news", "credibility": 0.82, "bias": "center"},
    # ── US news ──────────────────────────────────────────────────────
    "cnn.com": {"type": "news", "credibility": 0.7, "bias": "center_left"},
    "foxnews.com": {"type": "news", "credibility": 0.6, "bias": "right"},
    "msnbc.com": {"type": "news", "credibility": 0.62, "bias": "left"},
    "nbcnews.com": {"type": "news", "credibility": 0.72, "bias": "center_left"},
    "cbsnews.com": {"type": "news", "credibility": 0.72, "bias": "center"},
    "abcnews.go.com": {"type": "news", "credibility": 0.72, "bias": "center"},
    "usatoday.com": {"type": "news", "credibility": 0.7, "bias": "center"},
    "politico.com": {"type": "news", "credibility": 0.75, "bias": "center_left"},
    "thehill.com": {"type": "news", "credibility": 0.72, "bias": "center"},
    "axios.com": {"type": "news", "credibility": 0.75, "bias": "center"},
    "time.com": {"type": "news", "credibility": 0.75, "bias": "center_left"},
    "newsweek.com": {"type": "news", "credibility": 0.65, "bias": "center"},
    "huffpost.com": {"type": "news", "credibility": 0.58, "bias": "left"},
    "breitbart.com": {"type": "news", "credibility": 0.4, "bias": "right"},
    "dailywire.com": {"type": "news", "credibility": 0.5, "bias": "right"},
    "vox.com": {"type": "news", "credibility": 0.62, "bias": "left"},
    "theatlantic.com": {"type": "news", "credibility": 0.75, "bias": "center_left"},
    "newyorker.com": {"type": "news", "credibility": 0.78, "bias": "center_left"},
    # ── Tech news ────────────────────────────────────────────────────
    "techcrunch.com": {"type": "news", "credibility": 0.72, "bias": "center"},
    "theverge.com": {"type": "news", "credibility": 0.7, "bias": "center_left"},
    "arstechnica.com": {"type": "news", "credibility": 0.78, "bias": "center"},
    "wired.com": {"type": "news", "credibility": 0.72, "bias": "center_left"},
    "zdnet.com": {"type": "news", "credibility": 0.68, "bias": "center"},
    "engadget.com": {"type": "news", "credibility": 0.65, "bias": "center"},
    "thenextweb.com": {"type": "news", "credibility": 0.62, "bias": "center"},
    "venturebeat.com": {"type": "news", "credibility": 0.65, "bias": "center"},
    # ── Academic / Research ──────────────────────────────────────────
    "nature.com": {"type": "academic", "credibility": 0.96, "bias": "center"},
    "science.org": {"type": "academic", "credibility": 0.96, "bias": "center"},
    "sciencedirect.com": {"type": "academic", "credibility": 0.9, "bias": "center"},
    "pubmed.ncbi.nlm.nih.gov": {"type": "academic", "credibility": 0.92, "bias": "center"},
    "ncbi.nlm.nih.gov": {"type": "academic", "credibility": 0.92, "bias": "center"},
    "arxiv.org": {"type": "academic", "credibility": 0.82, "bias": "center"},
    "scholar.google.com": {"type": "academic", "credibility": 0.8, "bias": "center"},
    "jstor.org": {"type": "academic", "credibility": 0.9, "bias": "center"},
    "springer.com": {"type": "academic", "credibility": 0.88, "bias": "center"},
    "wiley.com": {"type": "academic", "credibility": 0.88, "bias": "center"},
    "researchgate.net": {"type": "academic", "credibility": 0.75, "bias": "center"},
    "semanticscholar.org": {"type": "academic", "credibility": 0.8, "bias": "center"},
    "plos.org": {"type": "academic", "credibility": 0.85, "bias": "center"},
    "ieee.org": {"type": "academic", "credibility": 0.9, "bias": "center"},
    "acm.org": {"type": "academic", "credibility": 0.88, "bias": "center"},
    "cell.com": {"type": "academic", "credibility": 0.95, "bias": "center"},
    "thelancet.com": {"type": "academic", "credibility": 0.95, "bias": "center"},
    "bmj.com": {"type": "academic", "credibility": 0.9, "bias": "center"},
    "nejm.org": {"type": "academic", "credibility": 0.95, "bias": "center"},
    # ── Government / Official ────────────────────────────────────────
    "gov.uk": {"type": "government", "credibility": 0.85, "bias": "center"},
    "usa.gov": {"type": "government", "credibility": 0.85, "bias": "center"},
    "who.int": {"type": "government", "credibility": 0.88, "bias": "center"},
    "cdc.gov": {"type": "government", "credibility": 0.88, "bias": "center"},
    "nih.gov": {"type": "government", "credibility": 0.88, "bias": "center"},
    "fda.gov": {"type": "government", "credibility": 0.85, "bias": "center"},
    "europa.eu": {"type": "government", "credibility": 0.82, "bias": "center"},
    "un.org": {"type": "government", "credibility": 0.85, "bias": "center"},
    "nasa.gov": {"type": "government", "credibility": 0.92, "bias": "center"},
    "whitehouse.gov": {"type": "government", "credibility": 0.75, "bias": "center"},
    "congress.gov": {"type": "government", "credibility": 0.85, "bias": "center"},
    "worldbank.org": {"type": "government", "credibility": 0.82, "bias": "center"},
    "imf.org": {"type": "government", "credibility": 0.82, "bias": "center"},
    # ── Wiki / Reference ─────────────────────────────────────────────
    "wikipedia.org": {"type": "wiki", "credibility": 0.72, "bias": "center"},
    "en.wikipedia.org": {"type": "wiki", "credibility": 0.72, "bias": "center"},
    "wikidata.org": {"type": "wiki", "credibility": 0.75, "bias": "center"},
    "britannica.com": {"type": "wiki", "credibility": 0.85, "bias": "center"},
    "merriam-webster.com": {"type": "wiki", "credibility": 0.82, "bias": "center"},
    # ── Fact-checking ────────────────────────────────────────────────
    "snopes.com": {"type": "news", "credibility": 0.82, "bias": "center"},
    "factcheck.org": {"type": "news", "credibility": 0.85, "bias": "center"},
    "politifact.com": {"type": "news", "credibility": 0.82, "bias": "center"},
    "fullfact.org": {"type": "news", "credibility": 0.82, "bias": "center"},
    # ── Tech / Developer ─────────────────────────────────────────────
    "github.com": {"type": "corporate", "credibility": 0.75, "bias": "center"},
    "stackoverflow.com": {"type": "wiki", "credibility": 0.72, "bias": "center"},
    "docs.python.org": {"type": "wiki", "credibility": 0.88, "bias": "center"},
    "developer.mozilla.org": {"type": "wiki", "credibility": 0.88, "bias": "center"},
    "microsoft.com": {"type": "corporate", "credibility": 0.72, "bias": "center"},
    "cloud.google.com": {"type": "corporate", "credibility": 0.72, "bias": "center"},
    "aws.amazon.com": {"type": "corporate", "credibility": 0.72, "bias": "center"},
    # ── Video / Media platforms ──────────────────────────────────────
    "youtube.com": {"type": "social_media", "credibility": 0.5, "bias": "unknown"},
    "vimeo.com": {"type": "social_media", "credibility": 0.55, "bias": "unknown"},
    "dailymotion.com": {"type": "social_media", "credibility": 0.45, "bias": "unknown"},
    "twitch.tv": {"type": "social_media", "credibility": 0.45, "bias": "unknown"},
    # ── Social media ─────────────────────────────────────────────────
    "twitter.com": {"type": "social_media", "credibility": 0.35, "bias": "unknown"},
    "x.com": {"type": "social_media", "credibility": 0.35, "bias": "unknown"},
    "reddit.com": {"type": "social_media", "credibility": 0.4, "bias": "unknown"},
    "facebook.com": {"type": "social_media", "credibility": 0.3, "bias": "unknown"},
    "instagram.com": {"type": "social_media", "credibility": 0.3, "bias": "unknown"},
    "tiktok.com": {"type": "social_media", "credibility": 0.25, "bias": "unknown"},
    "linkedin.com": {"type": "social_media", "credibility": 0.5, "bias": "unknown"},
    # ── Blogs / Content platforms ────────────────────────────────────
    "medium.com": {"type": "blog", "credibility": 0.45, "bias": "unknown"},
    "substack.com": {"type": "blog", "credibility": 0.45, "bias": "unknown"},
    "wordpress.com": {"type": "blog", "credibility": 0.35, "bias": "unknown"},
    "blogspot.com": {"type": "blog", "credibility": 0.3, "bias": "unknown"},
    "quora.com": {"type": "social_media", "credibility": 0.4, "bias": "unknown"},
    # ── Books / Libraries ────────────────────────────────────────────
    "openlibrary.org": {"type": "wiki", "credibility": 0.75, "bias": "center"},
    "gutenberg.org": {"type": "wiki", "credibility": 0.8, "bias": "center"},
    "goodreads.com": {"type": "social_media", "credibility": 0.55, "bias": "unknown"},
    "amazon.com": {"type": "corporate", "credibility": 0.55, "bias": "unknown"},
    # ── Images ───────────────────────────────────────────────────────
    "unsplash.com": {"type": "corporate", "credibility": 0.65, "bias": "center"},
    "pexels.com": {"type": "corporate", "credibility": 0.65, "bias": "center"},
    "flickr.com": {"type": "social_media", "credibility": 0.5, "bias": "unknown"},
    "gettyimages.com": {"type": "corporate", "credibility": 0.7, "bias": "center"},
}


@dataclass
class SourceClassification:
    domain: str
    source_type: str
    credibility_score: float
    bias_label: str


@dataclass
class ContradictionResult:
    doc_a_id: str
    doc_b_id: str
    confidence: float
    method: str
    explanation: str


class EvidenceAnalyzer:
    def classify_source(self, url: str) -> SourceClassification:
        domain = self._extract_domain(url)

        # Check exact match first, then check parent domains
        info = SOURCE_CLASSIFICATIONS.get(domain)
        if info is None:
            # Check parent domain (e.g., news.bbc.co.uk -> bbc.co.uk)
            parts = domain.split(".")
            for i in range(len(parts) - 1):
                parent = ".".join(parts[i:])
                info = SOURCE_CLASSIFICATIONS.get(parent)
                if info:
                    break

        if info:
            return SourceClassification(
                domain=domain,
                source_type=str(info["type"]),
                credibility_score=float(info["credibility"]),  # type: ignore[arg-type]
                bias_label=str(info["bias"]),
            )

        # Default classification for unknown sources
        return SourceClassification(
            domain=domain,
            source_type=self._guess_type(domain),
            credibility_score=0.5,
            bias_label="unknown",
        )

    def detect_contradiction(
        self,
        text_a: str,
        text_b: str,
        embedding_a: list[float] | None = None,
        embedding_b: list[float] | None = None,
    ) -> ContradictionResult | None:
        """Detect if two texts contradict each other.

        Uses keyword heuristics as a baseline. Can be upgraded to
        an NLI model for production accuracy.
        """
        # Negation-based heuristic
        negation_words = {
            "not", "no", "never", "false", "incorrect", "wrong",
            "deny", "denied", "denies", "refute", "refuted", "debunk",
            "misleading", "disproven", "untrue",
        }

        words_a = set(text_a.lower().split())
        words_b = set(text_b.lower().split())

        # Check if one text contains negation of claims in the other
        neg_in_a = words_a & negation_words
        neg_in_b = words_b & negation_words

        # Simple heuristic: if one has negation words and shares topic words
        shared_topic = (words_a & words_b) - negation_words - _STOP_WORDS
        if len(shared_topic) >= 3 and (neg_in_a ^ neg_in_b):  # XOR - only one has negation
            confidence = min(0.7, len(shared_topic) * 0.1)
            return ContradictionResult(
                doc_a_id="",  # Caller fills in
                doc_b_id="",
                confidence=confidence,
                method="nlp_entailment",
                explanation=f"Shared topic words with opposing negation: {shared_topic}",
            )

        # Embedding similarity check (high similarity + negation = contradiction)
        if embedding_a and embedding_b:
            similarity = self._cosine_similarity(embedding_a, embedding_b)
            if similarity > 0.7 and (neg_in_a ^ neg_in_b):
                return ContradictionResult(
                    doc_a_id="",
                    doc_b_id="",
                    confidence=min(0.8, similarity),
                    method="cosine_similarity",
                    explanation=f"High semantic similarity ({similarity:.2f}) with opposing negation",
                )

        return None

    @staticmethod
    def _extract_domain(url: str) -> str:
        try:
            parsed = urlparse(url)
            domain = parsed.hostname or ""
            if domain.startswith("www."):
                domain = domain[4:]
            return domain.lower()
        except Exception:
            return ""

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    @staticmethod
    def _guess_type(domain: str) -> str:
        if any(x in domain for x in [".edu", ".ac.", "university", "college"]):
            return "academic"
        if any(x in domain for x in [".gov", ".mil"]):
            return "government"
        if any(x in domain for x in ["blog", "medium.com", "substack"]):
            return "blog"
        if any(x in domain for x in ["twitter", "facebook", "reddit", "x.com"]):
            return "social_media"
        if "wiki" in domain:
            return "wiki"
        return "unknown"


# Common stop words to exclude from topic overlap
_STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "about", "that",
    "this", "it", "its", "they", "them", "their", "we", "our", "and",
    "or", "but", "if", "so", "than", "too", "very", "just", "also",
}
