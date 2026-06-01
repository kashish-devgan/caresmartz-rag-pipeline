# CareSmartz360 RAG Knowledge Base Pipeline

A robust, enterprise-grade Retrieval-Augmented Generation (RAG) platform for the CareSmartz360 knowledge base. Features both a standard Flat RAG pipeline (Phase 2) and an advanced 2-Level Hierarchical RAG pipeline (Phase 3) running side-by-side.

---

## What this does

### Standard Flat RAG (Phase 2)
- **Crawl**: Fetches help articles from the Intercom API with cursor-based pagination.
- **Chunking**: Splits articles into fixed-size 400-word chunks.
- **Storage**: Embeds and stores chunks in the default Pinecone namespace.
- **Chat**: Retrieves the top 3 similar chunks to synthesize answers using the Groq LLM.

### Advanced Hierarchical RAG (Phase 3)
- **Chunking (2-Level Precision)**: Employs a sentence-aware splitting mechanism to generate:
  - **Level-2 Parent Documents**: The full, context-rich article body.
  - **Level-3 Child Chunks**: Highly focused overlapping sentence-level windows (~100 words).
- **Storage**: Stores parents in the `hrag_parents` namespace and child chunks in the `hrag_children` namespace.
- **Dual-Namespace Query Orchestrator**: Performs semantic lookups over child segments (high precision) and matches their `parent_id` tags to fetch and load full parent articles, feeding maximum context to the LLM.
- **Idempotency**: Features drift and duplicate protection via deterministic metadata-based purges.
- **Sync Workers**: Integrates full sync (705+ articles) and incremental delta workers with APScheduler automation.

---

## Tech stack

| Component | standard Flat RAG (Phase 2) | Advanced Hierarchical RAG (Phase 3) |
|---|---|---|
| **API Framework** | FastAPI + Uvicorn | FastAPI + Uvicorn |
| **Embeddings** | all-MiniLM-L6-v2 (384-dim, local) | all-MiniLM-L6-v2 (384-dim, local, memory-reused) |
| **Vector DB** | Pinecone (Default Namespace) | Pinecone (`hrag_parents` & `hrag_children` Namespaces) |
| **LLM** | Groq (`llama-3.1-8b-instant`) | Groq (`llama3-8b-8192` or configured env) |
| **Scheduler** | APScheduler (5pm UTC daily) | APScheduler (Daily Delta Cronlookups) |
| **Testing** | Manual Verification | Automated Suite (15 Curated Test Cases) |

---

## Quick start

```bash
# 1. Clone and install
git clone https://github.com/yourusername/caresmartz-rag-pipeline.git
cd caresmartz-rag-pipeline
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate.ps1
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Open .env and populate your API credentials (Pinecone, Intercom, Groq)

# 3. Seed vector spaces
# standard Flat RAG seeding
python scripts/seed_pinecone.py
# Advanced Hierarchical RAG seeding
python scripts/seed_hrag.py

# 4. Start the server
uvicorn app.main:app --reload --port 8000
```

Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) to explore the interactive FastAPI swagger documentation.

---

## API endpoints

The platform runs both standard and hierarchical pipelines concurrently without conflict:

### 🟢 standard Flat RAG Routes (Phase 2)
| Method | Path | Description |
|---|---|---|
| GET | `/health` | API Health & Systems availability status |
| GET | `/api/articles` | List all synced Intercom article summaries |
| GET | `/api/articles/updated` | Fetch articles modified in the last N hours |
| POST | `/api/articles/sync` | Sync delta articles to Flat Pinecone index |
| POST | `/api/sync/trigger` | Force trigger scheduler daily sync job |
| GET | `/api/sync/status` | Fetch scheduler details and next runtime |
| POST | `/api/chat` | Query standard Flat RAG chatbot |
| GET | `/api/admin/images/{id}/gallery` | View article images as HTML gallery |
| GET | `/api/admin/index-stats` | Retrieve standard Flat index details |

### 🔵 Advanced Hierarchical RAG Routes (Phase 3)
| Method | Path | Description |
|---|---|---|
| POST | `/api/hrag/chat` | Query advanced Hierarchical RAG chatbot |
| POST | `/api/hrag/sync/full` | Asynchronously index all 705 Intercom articles from scratch |
| POST | `/api/hrag/sync/trigger` | Trigger incremental delta sync (last N hours) |
| GET | `/api/hrag/admin/stats` | Pinecone namespaces (`hrag_parents`/`hrag_children`) vector counts |

---

## Terminal chatbots

Two standalone interactive CLI chatbots are provided to query and test RAG pipelines directly from your console:

### standard Flat Chatbot
```bash
# Requires uvicorn server running
python scripts/chatbot.py
```

### Advanced Hierarchical Chatbot (with Debug metrics)
```bash
# Requires uvicorn server running
python scripts/chatbot_hrag.py
```
*Supports in-session commands: `/debug` (toggle retrieval scores), `/k <n>` (alter parent context count), and `/quit`.*

---

## Project structure

```
app/
  core/           config.py, logger.py
  models/
    article.py             Flat RAG schemas
    hierarchical_models.py ParentDocument, ChildChunk, and HRAG API schemas [NEW]
  services/
    intercom_service.py    Intercom API client
    pinecone_service.py    Flat Pinecone client & SentenceTransformer
    rag_service.py         Flat RAG generation orchestrator
    data_service.py        Text parsing utilities
    scheduler_service.py   APScheduler cron triggers
    hierarchical/          [NEW]
      __init__.py          Public hierarchical surface
      chunker.py           Sentence-aware 2-level splitter
      pinecone_hrag.py     Two-namespace Pinecone manager
      rag_hrag.py          Hierarchical search & Groq synthesis
      ingest.py            Full & delta sync async workers
  api/routes/
    articles.py            Flat article router
    sync.py                Flat scheduler router
    chat.py                Flat chatbot router
    hrag_router.py         Hierarchical RAG router (/api/hrag/*) [NEW]
  main.py                  FastAPI server registry (Version 3.0)
scripts/
  seed_pinecone.py         One-time Flat DB seeder
  chatbot.py               Flat terminal chatbot CLI
  seed_hrag.py             One-time Hierarchical DB seeder [NEW]
  chatbot_hrag.py          Hierarchical debug chatbot CLI [NEW]
tests/
  test_services.py         Flat RAG service unit tests
  run_hrag_tests.py        Automated Hierarchical Test suite (15 cases) [NEW]
  test_report.md           Pristine test results of the 15 cases (100% PASS) [NEW]
```

---

## Environment variables

Create a `.env` file at the root of the workspace using the following configuration:

```ini
INTERCOM_ACCESS_TOKEN=your-intercom-token
PINECONE_API_KEY=your-pinecone-key
PINECONE_INDEX_NAME=intercom-articles-hf
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=llama3-8b-8192
SYNC_LOOKBACK_HOURS=24
SYNC_TRIGGER_HOUR=17
SYNC_TRIGGER_MINUTE=0
```

---

## Running tests

### Flat RAG Tests
```bash
pytest tests/ -v
```

### Hierarchical RAG Test Suite
Runs **15 curated test cases** (Conversational, Procedural, Billing, Security, Negative test, special characters, etc.) with automatic transient retries, scoring verification, and complete reports generation:
```bash
python tests/run_hrag_tests.py
```
*Generated reports will be available at [tests/test_report.md](file:///e:/rag-intercom-sync/tests/test_report.md) showing a flawless **100% success rate**.*

---

## Phase roadmap

- **Phase 1 (Complete)**: Manual article scraping and static knowledge base.
- **Phase 2 (Complete)**: Automated Intercom sync + standard Flat RAG chatbot.
- **Phase 3 (Complete)**: 2-Level Hierarchical RAG pipeline integration (precision child vector chunk matching resolved directly to context-rich parent documents), multi-namespace Pinecone support, API routes, seeder and chatbot CLI tools, and an automated 15-case test suite.
