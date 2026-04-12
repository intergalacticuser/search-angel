"""Live web search via self-hosted SearXNG meta search engine."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from search_angel.core.evidence import EvidenceAnalyzer
from search_angel.search.bm25 import ScoredDocument

logger = logging.getLogger(__name__)

_evidence_analyzer = EvidenceAnalyzer()

# SearXNG category mapping
CATEGORY_MAP = {
    "web": "general",
    "general": "general",
    "images": "images",
    "videos": "videos",
    "news": "news",
    "science": "science",
    "books": "general",  # SearXNG uses general + specific engines for books
    "music": "music",
    "files": "files",
    "it": "it",
    "social": "social media",
}

# Additional engine params per category
CATEGORY_ENGINES = {
    "books": "google scholar,arxiv,openlibrary,wikidata",
}


class WebRetriever:
    """Retrieves live web results from SearXNG.

    SearXNG is self-hosted - queries never leave our infrastructure.
    It aggregates results from Google, Bing, DuckDuckGo, Wikipedia, etc.

    Supports categories: general, images, videos, news, science, books, music, files
    """

    def __init__(
        self,
        searxng_url: str = "http://sa-searxng:8080",
        timeout: float = 10.0,
    ) -> None:
        self._base_url = searxng_url.rstrip("/")
        self._timeout = timeout

    async def search(
        self,
        query: str,
        *,
        top_k: int = 20,
        categories: list[str] | None = None,
        language: str = "en",
    ) -> list[ScoredDocument]:
        cats = categories or ["general"]

        try:
            tasks = [
                self._search_category(query, cat, language, top_k)
                for cat in cats
            ]
            results_per_cat = await asyncio.gather(*tasks, return_exceptions=True)

            seen_urls: set[str] = set()
            all_results: list[ScoredDocument] = []

            for cat_results in results_per_cat:
                if isinstance(cat_results, Exception):
                    logger.warning("SearXNG category search failed: %s", cat_results)
                    continue
                for doc in cat_results:
                    if doc.url not in seen_urls:
                        seen_urls.add(doc.url)
                        all_results.append(doc)

            all_results.sort(key=lambda d: d.score, reverse=True)
            return all_results[:top_k]

        except Exception:
            logger.exception("Web search failed entirely, returning empty results")
            return []

    async def search_category(
        self,
        query: str,
        category: str,
        *,
        top_k: int = 30,
        language: str = "en",
    ) -> list[ScoredDocument]:
        """Public method to search a single specific category."""
        try:
            return await self._search_category(query, category, language, top_k)
        except Exception:
            logger.exception("Category search failed for %s", category)
            return []

    async def _search_category(
        self,
        query: str,
        category: str,
        language: str,
        top_k: int,
    ) -> list[ScoredDocument]:
        searxng_cat = CATEGORY_MAP.get(category, category)

        params: dict[str, Any] = {
            "q": query,
            "format": "json",
            "categories": searxng_cat,
            "language": language,
            "pageno": 1,
        }

        # Add specific engines for special categories
        if category in CATEGORY_ENGINES:
            params["engines"] = CATEGORY_ENGINES[category]

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(
                f"{self._base_url}/search",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

        results = data.get("results", [])
        documents: list[ScoredDocument] = []

        for i, result in enumerate(results[:top_k]):
            score = result.get("score", 1.0 - (i * 0.02))
            content = result.get("content", "") or result.get("title", "")

            # Classify source for real credibility scoring
            url = result.get("url", "")
            classification = _evidence_analyzer.classify_source(url)

            doc = ScoredDocument(
                doc_id=f"web_{hash(url) & 0xFFFFFFFF:08x}",
                score=float(score),
                title=result.get("title", ""),
                content=content,
                url=url,
                source={
                    "domain": classification.domain,
                    "source_type": classification.source_type,
                    "credibility_score": classification.credibility_score,
                    "bias_label": classification.bias_label,
                    "engine": result.get("engine", "unknown"),
                    "category": category,
                },
                published_at=result.get("publishedDate"),
                category=category,
                thumbnail=result.get("thumbnail"),
                img_src=result.get("img_src") or result.get("thumbnail"),
                video_url=result.get("url") if category == "videos" else None,
                iframe_src=result.get("iframe_src"),
                author=result.get("author"),
                metadata={
                    "engine": result.get("engine", ""),
                    "img_format": result.get("img_format"),
                    "resolution": result.get("resolution"),
                    "duration": result.get("duration"),
                    "filesize": result.get("filesize"),
                    "publisher": result.get("publisher"),
                    "isbn": result.get("isbn", []),
                },
            )
            documents.append(doc)

        return documents

    @staticmethod
    def _extract_domain(url: str) -> str:
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.hostname or ""
            if domain.startswith("www."):
                domain = domain[4:]
            return domain.lower()
        except Exception:
            return "unknown"

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{self._base_url}/healthz")
                return response.status_code == 200
        except Exception:
            return False
