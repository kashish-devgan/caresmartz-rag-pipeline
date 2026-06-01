# CareSmartz360 Hierarchical RAG (Phase 3)

The Advanced Hierarchical Retrieval-Augmented Generation (HRAG) pipeline enhancement package for CareSmartz360. Resolves the classic RAG dilemma by indexing highly focused sentence-level child vectors for precise matching while feeding full context-rich parent articles to the LLM.

---

## What this does

- **Sentence-Aware Chunker**: Normalizes text and slides a sentence-aware window to produce:
  - **Parent Documents**: Full body of help articles to preserve absolute context (Level-2).
  - **Child Chunks**: Overlapping sub-sections (~100 words) ensuring targeted similarity (Level-3).
- **Dual-Namespace Pinecone Partitioning**: Implements distinct namespaces in your Pinecone index:
  - `hrag_parents` for Level-2 articles.
  - `hrag_children` for Level-3 text snippets.
- **Two-Stage Precision Search**:
  1. Embeds the user prompt and queries `hrag_children` for top-N exact matches.
  2. Aggregates unique parent IDs and fetches corresponding complete articles directly from `hrag_parents`.
  3. Sorts and ranks parent articles by the highest cosine score and sends them as context to the LLM.
- **Idempotency Safeguards**: Detaches and deletes existing vectors for modified articles before re-indexing to ensure vector data integrity.
- **Sync Workers**: Supports background asynchronous crawl jobs ( APScheduler delta + full sync API triggers).

---

## Tech stack

| Component               | Technology                                                         |
| ----------------------- | ------------------------------------------------------------------ |
| **API Framework**       | FastAPI + Uvicorn                                                  |
| **Embeddings**          | HuggingFace `all-MiniLM-L6-v2` (384-dim, local execution)          |
| **Vector DB Partition** | Pinecone Serverless (Namespaces: `hrag_parents` & `hrag_children`) |
| **LLM Synthesis**       | Groq (`llama3-8b-8192` with structured citation instructions)      |
| **Ingestion Engine**    | Asynchronous HTTPX crawl workers + Pydantic v2 validation          |
| **CLI & Tools**         | stand-alone Seeder and Debug Terminal Chatbot                      |
| **Validation Suite**    | Curated Automated test runner (`run_hrag_tests.py`)                |

---

## Quick start

```bash
# 1. Install dependencies (fully backwards compatible — no new dependencies)
pip install -r requirements.txt

# 2. Seed the Hierarchical Index (fetches and indexes all 705+ articles, ~5-15 mins)
python scripts/seed_hrag.py

# 3. Start the FastAPI server
uvicorn app.main:app --reload --port 8000

# 4. Interact with the Debug Terminal Chatbot
python scripts/chatbot_hrag.py
```

---

## API endpoints

Mounted side-by-side with Phase 2 routes under `/api/hrag/*` to prevent any disruptions to legacy integrations:

| Method | Path                     | Description                                                    |
| ------ | ------------------------ | -------------------------------------------------------------- |
| POST   | `/api/hrag/chat`         | Submit a query to the Hierarchical RAG chatbot                 |
| POST   | `/api/hrag/sync/full`    | Trigger an asynchronous full sync of all 705 Intercom articles |
| POST   | `/api/hrag/sync/trigger` | Trigger daily delta sync (based on lookback hours config)      |
| GET    | `/api/hrag/admin/stats`  | Fetch vector counts inside parents and children namespaces     |

### Example Chat Request

```bash
curl -X POST http://localhost:8000/api/hrag/chat \
     -H "Content-Type: application/json" \
     -d '{
       "question": "How do I schedule a shift?",
       "top_k_children": 10,
       "top_k_parents": 3
     }'
```

---

## Terminal chatbot

The advanced hierarchical CLI chatbot provides real-time relevancy monitoring and vector metrics tracking:

```bash
python scripts/chatbot_hrag.py
```

### In-Session Commands

- `/debug`: Toggle vector scoring visibility (shows matched parent scores & top chunk ranks).
- `/k <n>`: Dynamically adjust `top_k_parents` parameter (default 3) for the current session.
- `/quit` / `/exit` / `/q`: End terminal session safely.

---

## Project structure

This package consists strictly of isolated hierarchical modules and administrative developer scripts:

```
app/
  models/
    hierarchical_models.py     ParentDocument, ChildChunk, & Hierarchical API schemas
  services/
    hierarchical/
      __init__.py              Clean public surface exports
      chunker.py               Sentence-aware 2-level text splitting logic
      pinecone_hrag.py         Dual-namespace vector lookups & direct fetch
      rag_hrag.py              Orchestration, prompt construction, and Groq integration
      ingest.py                Idempotent background full & delta sync workers
  api/routes/
    hrag_router.py             FastAPI endpoints (/api/hrag/*)
scripts/
  seed_hrag.py                 Standalone one-shot index seeder with progress logs
  chatbot_hrag.py              Interactive terminal debugger chatbot CLI
tests/
  run_hrag_tests.py            Automated test suite (15 curated cases)
  test_report.md               Markdown report containing logs for all 15 cases (100% PASS)
```

---

## Environment variables

Configured strictly under `.env` alongside Phase 2 parameters:

```ini
INTERCOM_ACCESS_TOKEN=your-intercom-token
PINECONE_API_KEY=your-pinecone-key
PINECONE_INDEX_NAME=intercom-articles-hf
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=llama3-8b-8192
SYNC_LOOKBACK_HOURS=24
```

---

## Running tests

The advanced hierarchical RAG pipeline comes with an automated testing validation suite covering **15 critical test categories** (including edge-cases, Special characters, out-of-domain conversational queries, etc.):

```bash
python tests/run_hrag_tests.py
```

All test outcomes, precise latency timings, referenced sources lists, and LLM generated snippets are compiled and saved in a detailed report:

- Local report: [tests/test_report.md](file:///e:/rag-intercom-sync/tests/test_report.md) _(Prerecorded flawless 100% success rate)_.
- App artifact report: [test_report.md](file:///C:/Users/HP/.gemini/antigravity/brain/70fe34bb-5092-4bcd-9121-d3c12aef1cda/test_report.md).

---

## Phase roadmap

- **Phase 1 (Complete)**: Manual help articles scraping and static vector storage.
- **Phase 2 (Complete)**: standard Flat RAG pipeline (400-word chunks, single namespace).
- **Phase 3 (Complete)**: 2-Level Hierarchical RAG (Sentence-aware splitting, child-parent lookup), double-namespace vector partitions, delta sync workflows, developer CLI debugger and seed utilities, and an automated 15-case verification suite.
