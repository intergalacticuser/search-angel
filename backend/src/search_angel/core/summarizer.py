"""AI-powered summary generation via configurable LLM provider."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import httpx

from search_angel.config import Settings

logger = logging.getLogger(__name__)


@dataclass
class SummaryResult:
    text: str
    citations: list[Citation] = field(default_factory=list)
    model_used: str = ""
    confidence: str = "medium"


@dataclass
class Citation:
    doc_id: str
    title: str
    url: str
    relevance: str = "high"


class Summarizer:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def summarize(
        self,
        query: str,
        documents: list,
        mode: str = "standard",
    ) -> SummaryResult:
        if not documents or not self._settings.llm_api_key:
            return self._fallback_summary(query, documents)

        # Build context from top documents
        context = self._build_context(documents, mode)
        prompt = self._build_prompt(query, context, mode)

        try:
            response_text = await self._call_llm(prompt)
            citations = self._extract_citations(documents[:5])

            return SummaryResult(
                text=response_text,
                citations=citations,
                model_used=self._settings.llm_model,
                confidence=self._assess_confidence(documents),
            )
        except Exception:
            logger.exception("LLM summarization failed, using fallback")
            return self._fallback_summary(query, documents)

    async def _call_llm(self, prompt: str) -> str:
        provider = self._settings.llm_provider

        if provider == "openai":
            return await self._call_openai(prompt)
        elif provider == "anthropic":
            return await self._call_anthropic(prompt)
        else:
            return f"[Summary generation not available for provider: {provider}]"

    async def _call_openai(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._settings.llm_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._settings.llm_model,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are a search engine summary assistant. "
                                "Provide concise, factual summaries based on the provided sources. "
                                "Cite sources by their number [1], [2], etc."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": self._settings.llm_max_tokens,
                    "temperature": 0.3,
                },
            )
            response.raise_for_status()
            data = response.json()
            return str(data["choices"][0]["message"]["content"])

    async def _call_anthropic(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self._settings.llm_api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._settings.llm_model,
                    "max_tokens": self._settings.llm_max_tokens,
                    "system": (
                        "You are a search engine summary assistant. "
                        "Provide concise, factual summaries based on the provided sources. "
                        "Cite sources by their number [1], [2], etc."
                    ),
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            response.raise_for_status()
            data = response.json()
            return str(data["content"][0]["text"])

    @staticmethod
    def _build_context(documents: list, mode: str) -> str:
        max_docs = 10 if mode in ("deep", "evidence") else 5
        parts: list[str] = []
        for i, doc in enumerate(documents[:max_docs]):
            title = getattr(doc, "title", "Unknown")
            content = getattr(doc, "content", "")
            # Truncate content to avoid token limits
            snippet = content[:500] if len(content) > 500 else content
            source_info = getattr(doc, "source", {})
            domain = source_info.get("domain", "unknown")
            parts.append(f"[{i + 1}] {title} ({domain})\n{snippet}")
        return "\n\n".join(parts)

    @staticmethod
    def _build_prompt(query: str, context: str, mode: str) -> str:
        if mode == "compare_narratives":
            return (
                f"Query: {query}\n\n"
                f"Sources:\n{context}\n\n"
                "Compare the different perspectives presented in these sources. "
                "Identify areas of agreement and disagreement. "
                "Present a balanced summary citing each source."
            )
        elif mode == "evidence":
            return (
                f"Query: {query}\n\n"
                f"Sources:\n{context}\n\n"
                "Summarize the evidence found across these sources. "
                "Note the level of agreement between sources. "
                "Highlight any contradictions. Cite each source used."
            )
        else:
            return (
                f"Query: {query}\n\n"
                f"Sources:\n{context}\n\n"
                "Provide a concise, factual answer based on these sources. "
                "Cite each source used with [N] notation."
            )

    @staticmethod
    def _extract_citations(documents: list) -> list[Citation]:
        citations: list[Citation] = []
        for doc in documents:
            citations.append(
                Citation(
                    doc_id=getattr(doc, "doc_id", ""),
                    title=getattr(doc, "title", "Unknown"),
                    url=getattr(doc, "url", ""),
                )
            )
        return citations

    @staticmethod
    def _assess_confidence(documents: list) -> str:
        if not documents:
            return "low"
        avg_cred = 0.0
        count = 0
        for doc in documents[:5]:
            source = getattr(doc, "source", {})
            cred = source.get("credibility_score", 0.5)
            avg_cred += float(cred)
            count += 1
        if count > 0:
            avg_cred /= count
        if avg_cred >= 0.8:
            return "high"
        elif avg_cred >= 0.6:
            return "medium"
        return "low"

    @staticmethod
    def _fallback_summary(query: str, documents: list) -> SummaryResult:
        """Generate a basic extractive summary without an LLM."""
        if not documents:
            return SummaryResult(
                text=f"No results found for: {query}",
                confidence="low",
            )

        top_doc = documents[0]
        title = getattr(top_doc, "title", "")
        content = getattr(top_doc, "content", "")
        snippet = content[:300] if len(content) > 300 else content

        text = f"Based on {len(documents)} sources, the top result is \"{title}\": {snippet}..."
        citations = [
            Citation(
                doc_id=getattr(doc, "doc_id", ""),
                title=getattr(doc, "title", ""),
                url=getattr(doc, "url", ""),
            )
            for doc in documents[:3]
        ]

        return SummaryResult(
            text=text,
            citations=citations,
            confidence="low",
        )
