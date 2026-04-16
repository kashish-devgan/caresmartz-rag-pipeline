# CareSmartz360 RAG Knowledge Base Pipeline

Phase 2 of the CareSmartz360 RAG chatbot project. Automates article retrieval from Intercom, stores embeddings in Pinecone, and exposes a conversational RAG chatbot.

## What this does

- Fetches help articles from the Intercom API with cursor-based pagination
- Filters articles updated in the last 24 hours
- Chunks article text and generates vector embeddings via HuggingFace (free, local)
- Stores vectors + metadata (title, body, source URL, image URLs) in Pinecone
- Schedules daily sync at 5pm UTC via APScheduler
- Exposes a RAG chatbot answering user questions using Groq LLM
- Admin image gallery for viewing article-associated images

## Tech stack

| Component | Technology |
|-----------|-----------|
| API framework | FastAPI + uvicorn |
| Embeddings | HuggingFace all-MiniLM-L6-v2 (384-dim, local, free) |
| Vector DB | Pinecone serverless |
| LLM | Groq llama-3.1-8b-instant |
| Scheduler | APScheduler (CronTrigger, 5pm UTC daily) |
| HTTP client | httpx (async) |
| Data validation | Pydantic v2 |

## Quick start

\\\ash
# 1. Clone and install
git clone https://github.com/yourusername/caresmartz-rag-pipeline.git
cd caresmartz-rag-pipeline
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Fill in your API keys in .env

# 3. Seed the database
python scripts/seed_pinecone.py

# 4. Start the server
uvicorn app.main:app --reload --port 8000
\\\

Open http://127.0.0.1:8000/docs for the interactive API documentation.

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| GET | /api/articles | List all Intercom articles |
| GET | /api/articles/updated | Articles updated in last N hours |
| POST | /api/articles/sync | Sync updated articles to Pinecone |
| POST | /api/sync/trigger | Force trigger a sync immediately |
| GET | /api/sync/status | Scheduler status and next run time |
| POST | /api/chat | Ask the RAG chatbot |
| GET | /api/admin/images/{id} | Get article image URLs |
| GET | /api/admin/images/{id}/gallery | View images as HTML gallery |
| GET | /api/admin/index-stats | Pinecone index statistics |

## Terminal chatbot

\\\ash
# Requires server running in another terminal
python scripts/chatbot.py
\\\

## Project structure

\\\
app/
  core/          config.py, logger.py
  models/        article.py (all Pydantic schemas)
  services/      intercom, pinecone, data, rag, scheduler
  api/routes/    articles, sync, chat, admin
  data/          articles.json (30 fabricated CareSmartz articles)
  main.py        FastAPI app factory
scripts/
  seed_pinecone.py   One-time DB population
  sync_job.py        Standalone CLI sync
  chatbot.py         Interactive terminal chatbot
tests/
  test_services.py   pytest unit tests
\\\

## Environment variables

Copy \.env.example\ to \.env\ and fill in:

\\\
INTERCOM_ACCESS_TOKEN=
HUGGINGFACE_API_KEY=
PINECONE_API_KEY=
PINECONE_INDEX_NAME=intercom-articles-hf
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1
GROQ_API_KEY=
GROQ_MODEL=llama-3.1-8b-instant
SYNC_TRIGGER_HOUR=17
SYNC_TRIGGER_MINUTE=0
\\\

## Running tests

\\\ash
pytest tests/ -v
\\\

## Phase roadmap

- Phase 1 (complete): Manual article scraping and static knowledge base
- Phase 2 (this repo): Automated Intercom sync + RAG chatbot
- Phase 3 (planned): Frontend UI, API authentication, live web scraping
