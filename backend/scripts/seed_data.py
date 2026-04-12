"""Seed sample documents for demo/testing."""

from __future__ import annotations

import asyncio
import hashlib
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from search_angel.config import get_settings
from search_angel.core.deduplication import compute_simhash
from search_angel.core.evidence import EvidenceAnalyzer
from search_angel.db.engine import get_session_factory
from search_angel.db.repositories import DocumentRepository, SourceRepository
from search_angel.embeddings.encoder import EmbeddingEncoder
from search_angel.search.client import OpenSearchClient

SAMPLE_DOCUMENTS = [
    {
        "url": "https://reuters.com/technology/ai-breakthrough-2024",
        "title": "New AI Model Achieves Human-Level Reasoning in Scientific Tasks",
        "content": (
            "Researchers at a leading AI lab have developed a new model that demonstrates "
            "human-level performance on complex scientific reasoning benchmarks. The system "
            "uses a novel architecture combining transformer attention mechanisms with "
            "symbolic reasoning modules. Independent evaluators confirmed the results across "
            "multiple test sets including mathematical proofs, physics problems, and "
            "biological analysis tasks. The breakthrough has implications for drug discovery "
            "and materials science."
        ),
        "published_at": datetime.now(timezone.utc) - timedelta(days=2),
    },
    {
        "url": "https://nature.com/articles/ai-reasoning-study",
        "title": "Evaluating Machine Reasoning: A Comprehensive Benchmark Study",
        "content": (
            "This peer-reviewed study presents a comprehensive evaluation of current AI "
            "systems on scientific reasoning tasks. Our methodology includes controlled "
            "experiments across physics, chemistry, and biology domains. Results indicate "
            "that while recent models show significant improvement, true human-level "
            "reasoning remains elusive in edge cases requiring intuitive leaps. We propose "
            "a new benchmark framework that better captures reasoning depth."
        ),
        "published_at": datetime.now(timezone.utc) - timedelta(days=5),
    },
    {
        "url": "https://bbc.com/news/technology-ai-privacy",
        "title": "Privacy Concerns Rise as AI Search Engines Track User Queries",
        "content": (
            "Consumer advocacy groups have raised alarms about the extent to which AI-powered "
            "search engines collect and retain user data. A new report reveals that major "
            "search platforms store detailed query histories and behavioral profiles, often "
            "without clear user consent. Privacy experts recommend using search engines that "
            "implement strong anonymization and do not track individual users."
        ),
        "published_at": datetime.now(timezone.utc) - timedelta(days=7),
    },
    {
        "url": "https://arxiv.org/abs/2024.hybrid-search",
        "title": "Hybrid Search: Combining BM25 and Dense Retrieval for Better Results",
        "content": (
            "We present a hybrid search approach that combines traditional BM25 scoring with "
            "dense vector retrieval using Reciprocal Rank Fusion. Our experiments on MS MARCO "
            "and BEIR benchmarks show consistent improvements of 8-15% in NDCG@10 compared to "
            "either method alone. The approach is particularly effective for queries requiring "
            "both lexical matching and semantic understanding. We provide an open implementation."
        ),
        "published_at": datetime.now(timezone.utc) - timedelta(days=14),
    },
    {
        "url": "https://theguardian.com/technology/ai-misinformation",
        "title": "AI-Generated Content Floods Search Results, Raising Misinformation Concerns",
        "content": (
            "Search engines are struggling to cope with an unprecedented volume of AI-generated "
            "content that often contains factual errors. Experts warn that without better "
            "evidence-based ranking systems, users may increasingly encounter unreliable "
            "information. Several tech companies are developing source verification tools "
            "and evidence chain analysis to combat the problem."
        ),
        "published_at": datetime.now(timezone.utc) - timedelta(days=3),
    },
    {
        "url": "https://wsj.com/articles/tech-companies-privacy-regulations",
        "title": "New Privacy Regulations Force Tech Companies to Rethink Data Collection",
        "content": (
            "Upcoming privacy regulations in the EU and US are compelling technology companies "
            "to fundamentally restructure their data collection practices. Companies that rely "
            "heavily on user tracking for advertising revenue face significant business model "
            "challenges. Privacy-first alternatives are gaining market share as consumers "
            "become more aware of data collection practices."
        ),
        "published_at": datetime.now(timezone.utc) - timedelta(days=1),
    },
    {
        "url": "https://cnn.com/2024/search-engine-comparison",
        "title": "Comparing Search Engines: Which Protects Your Privacy Best?",
        "content": (
            "Our analysis of the top ten search engines reveals stark differences in privacy "
            "practices. While some engines store queries for up to 18 months, others delete "
            "them immediately. Key factors include IP anonymization, query logging policies, "
            "and whether the engine uses behavioral profiling for ad targeting. We rank each "
            "engine on a comprehensive privacy scorecard."
        ),
        "published_at": datetime.now(timezone.utc) - timedelta(days=10),
    },
    {
        "url": "https://pubmed.ncbi.nlm.nih.gov/ai-drug-discovery",
        "title": "Machine Learning Applications in Drug Discovery: A Systematic Review",
        "content": (
            "This systematic review examines 847 studies published between 2020-2024 on "
            "the application of machine learning to drug discovery. We find that AI-driven "
            "approaches have reduced early-stage screening costs by an estimated 40% and "
            "time-to-candidate by 30%. However, clinical trial success rates for AI-discovered "
            "compounds remain comparable to traditional methods, suggesting that the greatest "
            "current value is in efficiency rather than novel target discovery."
        ),
        "published_at": datetime.now(timezone.utc) - timedelta(days=30),
    },
]


async def main() -> None:
    settings = get_settings()
    encoder = EmbeddingEncoder(settings.embedding_model, settings.embedding_dimension)
    evidence_analyzer = EvidenceAnalyzer()
    os_client = OpenSearchClient(settings)
    session_factory = get_session_factory()

    print(f"Seeding {len(SAMPLE_DOCUMENTS)} sample documents...")

    async with session_factory() as db:
        source_repo = SourceRepository(db)
        doc_repo = DocumentRepository(db)

        for i, doc_data in enumerate(SAMPLE_DOCUMENTS):
            url = doc_data["url"]
            print(f"  [{i + 1}/{len(SAMPLE_DOCUMENTS)}] {doc_data['title'][:60]}...")

            # Classify source
            classification = evidence_analyzer.classify_source(url)
            source = await source_repo.get_or_create(
                domain=classification.domain,
                source_type=classification.source_type,
                credibility_score=classification.credibility_score,
                bias_label=classification.bias_label,
            )

            # Compute hashes
            url_hash = hashlib.sha256(url.lower().encode()).hexdigest()
            content_hash = hashlib.sha256(doc_data["content"].encode()).hexdigest()

            # Check if already exists
            existing = await doc_repo.get_by_url_hash(url_hash)
            if existing:
                print(f"    Skipping (already exists)")
                continue

            # Compute embedding
            embedding = encoder.encode(
                f"{doc_data['title']} {doc_data['content'][:1000]}"
            )

            # Create document
            doc = await doc_repo.create(
                source_id=source.id,
                url=url,
                url_hash=url_hash,
                title=doc_data["title"],
                content=doc_data["content"],
                content_hash=content_hash,
                language="en",
                word_count=len(doc_data["content"].split()),
                embedding=embedding,
                published_at=doc_data["published_at"],
                indexed_at=datetime.now(timezone.utc),
            )

            # Index in OpenSearch
            os_doc = {
                "doc_id": str(doc.id),
                "url": url,
                "title": doc_data["title"],
                "content": doc_data["content"],
                "word_count": len(doc_data["content"].split()),
                "embedding": embedding,
                "source": {
                    "source_id": str(source.id),
                    "domain": classification.domain,
                    "source_type": classification.source_type,
                    "credibility_score": classification.credibility_score,
                    "bias_label": classification.bias_label,
                },
                "published_at": doc_data["published_at"].isoformat(),
                "indexed_at": datetime.now(timezone.utc).isoformat(),
                "content_hash": content_hash,
            }
            try:
                await os_client.index_document(str(doc.id), os_doc)
            except Exception as e:
                print(f"    WARNING: Failed to index in OpenSearch: {e}")

        await db.commit()

    await os_client.close()
    print("Done! Sample data seeded.")


if __name__ == "__main__":
    asyncio.run(main())
