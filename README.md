<p align="center">
  <img src="backend/search_angel_logo.png" alt="Search Angel" width="250">
</p>

<h1 align="center">Search Angel</h1>

<p align="center">
  <strong>Privacy-First Search Engine</strong><br>
  <sub>Hybrid search. Evidence-based ranking. Zero tracking.</sub>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12+-blue?style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/tracking-zero-brightgreen?style=flat-square" alt="Zero Tracking">
  <img src="https://img.shields.io/badge/status-beta-orange?style=flat-square" alt="Status">
</p>

---

## What is this

Search Angel is a search engine that doesn't spy on you.

It combines multiple privacy-respecting search providers (DuckDuckGo, Brave Search, Startpage, Mojeek) through a self-hosted [SearXNG](https://github.com/searxng/searxng) instance, adds hybrid ranking (BM25 + vector embeddings), source credibility scoring, and an AI summary layer - all without logging a single query.

**Google and Bing are intentionally disabled.** They log every query. That defeats the entire purpose.

This is the search engine behind [Atlas Browser](https://github.com/intergalacticuser/atlas-browser). It also runs standalone at any domain you point it to.

## Architecture

```
User query
    |
    v
FastAPI backend ──> Query Processor (intent, entities, expansion)
    |
    ├──> BM25 search (OpenSearch)        ─┐
    ├──> Vector search (384-dim kNN)      ├──> RRF Fusion ──> Evidence Ranking ──> Results
    └──> Live web (SearXNG)              ─┘
              |
              ├── DuckDuckGo
              ├── Brave Search
              ├── Startpage
              ├── Mojeek
              └── Qwant
```

**What happens to your data:**
- Query exists in RAM for milliseconds, then gone. No database. No log file.
- IP is one-way hashed with a daily rotating salt. Original never stored.
- Zero cookies. Zero analytics. Zero behavioral profiling.

## Features

- **Hybrid search** - BM25 text + vector embeddings + live web, fused with Reciprocal Rank Fusion
- **Privacy-only engines** - Google/Bing disabled. Only DuckDuckGo, Brave, Startpage, Mojeek, Qwant
- **Self-hosted SearXNG** - Meta-search runs on YOUR server. Queries never leave your infrastructure
- **Evidence-based ranking** - Source credibility scoring (120+ domains), bias labels, contradiction detection
- **Category search** - Web, Images, Videos, News, Science, Books, Music, Files
- **AI summaries** - Optional LLM-powered summaries with citations (OpenAI/Anthropic)
- **Phantom Mode** - Ephemeral Docker containers. Session ends = container destroyed = zero trace
- **Tor integration** - Dedicated SearXNG instance that routes all queries through Tor
- **Source transparency** - Every result shows credibility score, source type, bias label

## Quick Start

```bash
git clone https://github.com/intergalacticuser/search-angel.git
cd search-angel/backend

# Copy and edit config
cp .env.example .env
# Edit .env with your passwords

# Start everything
docker compose up -d

# Run database migrations
docker compose exec app alembic upgrade head

# Done - API at http://localhost:8000
# Docs at http://localhost:8000/docs
```

## Stack

| Component | Technology |
|-----------|-----------|
| API | FastAPI (Python 3.12) |
| Database | PostgreSQL 16 + pgvector |
| Search Index | OpenSearch 2.12 |
| Meta Search | SearXNG (self-hosted) |
| Embeddings | all-MiniLM-L6-v2 (384 dims) |
| Tor | SOCKS5 proxy container |
| Frontend | Next.js 15 + Tailwind CSS |
| Deployment | Docker Compose |

## API Endpoints

| Method | Path | What it does |
|--------|------|-------------|
| POST | `/api/v1/search` | Main search (all modes) |
| POST | `/api/v1/search/deep` | Deep search with evidence |
| POST | `/api/v1/search/compare` | Narrative comparison |
| POST | `/api/v1/search/category` | Category search (images, videos, news...) |
| POST | `/api/v1/phantom/start` | Start Phantom Mode container |
| DELETE | `/api/v1/phantom/end/{id}` | Destroy Phantom container |
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/documents/{id}` | Document detail |
| GET | `/api/v1/evidence/{id}` | Evidence chain |

## Project Structure

```
backend/
├── src/search_angel/
│   ├── api/           # FastAPI routers + middleware
│   ├── core/          # Query processor, ranking, evidence, pipeline
│   ├── search/        # OpenSearch client, BM25, vector, hybrid, web
│   ├── models/        # Pydantic schemas + SQLAlchemy models
│   ├── db/            # Database engine + repositories
│   ├── privacy/       # IP anonymizer, session manager, audit
│   ├── embeddings/    # Sentence transformer encoder
│   ├── auth/          # User auth (JWT)
│   └── premium/       # Phantom Mode (ephemeral containers)
├── searxng/           # SearXNG config (privacy-only engines)
├── alembic/           # Database migrations
├── docker-compose.yml # Dev stack
└── docker-compose.prod.yml  # Production stack

frontend/
├── app/               # Next.js pages (home, search, privacy)
├── components/        # React components
└── lib/               # API client + types
```

## Privacy Claims - Verified

| Claim | How |
|-------|-----|
| No query logging | Queries pass through RAM only. No database writes. No log files. Check `pipeline.py`. |
| No IP storage | IPs hashed with daily salt in `anonymizer.py`. One-way SHA-256. Original discarded. |
| No cookies | Privacy middleware strips all Set-Cookie headers. Check `middleware/privacy.py`. |
| No Google/Bing | Disabled in `searxng/settings.yml`. They log queries. |
| No telemetry | Zero analytics scripts in frontend. No tracking pixels. No error reporting. |

Don't trust me - read the code. That's why it's open source.

## Contributing

PRs welcome. Issues welcome. Ideas welcome.

This is a beta. It needs work. If you care about search privacy, help make it better.

## License

MIT

---

<p align="center">
  <sub>Part of the <a href="https://github.com/intergalacticuser/atlas-browser">Atlas Browser</a> project</sub>
</p>
