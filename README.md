# CareSmartz360 RAG Knowledge Base Pipeline

A FastAPI-based Retrieval-Augmented Generation (RAG) service that powers an AI chatbot over the CareSmartz360 Intercom help center. The pipeline syncs published Intercom articles, embeds them into Pinecone, and answers user questions using a Groq-hosted LLM grounded in the retrieved article content.

---

## Overview

This service automatically keeps a vector index of CareSmartz360's Intercom Help Center in sync and exposes a conversational `/api/chat` endpoint. When a user asks a question, the pipeline retrieves the most relevant article chunks from Pinecone and uses them as grounding context for the LLM's response — so answers are accurate, current, and traceable back to source articles.

```
Intercom Help Center  --->  Sync Pipeline  --->  Pinecone (vector index)
                                                        |
                                                        v
                            User Question  --->  Retrieval  --->  Groq LLM  --->  Answer + Sources
```

---

## Tech Stack

| Component | Technology |
|---|---|
| API framework | FastAPI |
| Vector database | Pinecone (serverless) |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` (384-dim, HuggingFace) |
| LLM | Groq (`llama3-8b-8192`) |
| Article source | Intercom API |
| Scheduling | APScheduler (daily sync cron) |
| HTML parsing | BeautifulSoup4 |
| Config | Pydantic Settings (`.env`) |

---

## Project Structure

```
rag-intercom-sync/
├── app/
│   ├── main.py                  # FastAPI app factory, lifespan, router registration
│   ├── core/
│   │   ├── config.py            # Pydantic settings loaded from .env
│   │   └── logger.py            # Centralized logging configuration
│   ├── models/
│   │   └── article.py           # RawArticle, ChatRequest, ChatResponse schemas
│   ├── services/
│   │   ├── intercom_service.py  # Async Intercom API client (paginated article fetch)
│   │   ├── pinecone_service.py  # Pinecone index management, embedding, upsert, query
│   │   ├── data_service.py      # HTML cleaning + chunking (400-word windows)
│   │   ├── rag_service.py       # Retrieval + Groq LLM answer generation
│   │   └── scheduler_service.py # APScheduler daily delta sync job
│   ├── data/
│   │   ├── articles.json        # Local cache of synced article metadata
│   │   └── seed_data.py
│   └── api/routes/
│       ├── articles.py          # Article listing, sync status, index stats
│       ├── sync.py              # Manual sync trigger endpoints
│       └── chat.py              # Chat endpoint (/api/chat)
├── scripts/
│   ├── chatbot.py                # Interactive terminal chatbot for /api/chat
│   └── seed_pinecone.py          # One-shot Pinecone index seeding script
├── observations_report.md       # System verification & fix log
├── requirements.txt
└── .env                          # Environment configuration (not committed)
```

---

## How It Works

### 1. Ingestion (Sync Pipeline)

- `intercom_service.py` paginates through the Intercom Articles API and fetches all published help articles.
- `data_service.py` cleans HTML from article bodies and splits each article into overlapping ~400-word chunks (50-word overlap).
- `pinecone_service.py` embeds each chunk with `all-MiniLM-L6-v2` and upserts it into a single Pinecone index, storing metadata (title, source URL, article ID, image URLs).
- `scheduler_service.py` runs this sync automatically once per day via APScheduler, using a configurable lookback window (`SYNC_LOOKBACK_HOURS`) to pick up recently updated articles.

### 2. Retrieval & Generation (Chat Pipeline)

- A user question is embedded with the same model and used to query Pinecone for the top-k most similar chunks (default `k=3`).
- `rag_service.py` assembles a prompt containing the retrieved chunks as context and sends it to Groq's `llama3-8b-8192` model.
- The response includes the generated answer, the source articles (with titles and URLs), and any associated image URLs — or a graceful fallback message if no relevant content is found.

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Service health check, environment, and version info |
| `GET` | `/api/articles` | List synced article metadata (IDs, titles, status) |
| `GET` | `/api/articles/updated` | List articles updated within the last N hours |
| `GET` | `/api/articles/index-stats` | Pinecone index dimension and vector count |
| `POST` | `/api/sync/trigger` | Manually trigger a background sync of updated articles |
| `GET` | `/api/sync/status` | Scheduler status and next scheduled run time |
| `POST` | `/api/chat` | Ask the RAG chatbot a question |

### Example: `/api/chat`

**Request**
```json
{
  "question": "How do I add a new caregiver?"
}
```

**Response**
```json
{
  "answer": "To add a caregiver in CareSmartz360, go to the Caregivers section, click Add Caregiver, fill in the required details, and click Save.\n\nSources: Adding a Caregiver",
  "sources": [
    {
      "title": "Adding a Caregiver",
      "url": "https://intercom.help/caresmartz/en/articles/...",
      "score": 0.91
    }
  ],
  "image_urls": []
}
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- A Pinecone account and API key
- A Groq API key
- An Intercom access token with read access to Articles

### Installation

```bash
git clone https://github.com/kashish-devgan/caresmartz-rag-pipeline.git
cd caresmartz-rag-pipeline/rag-intercom-sync

python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
INTERCOM_ACCESS_TOKEN=your_intercom_token
INTERCOM_API_BASE=https://api.intercom.io

HUGGINGFACE_API_KEY=your_huggingface_key
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSIONS=384

PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX_NAME=intercom-articles-hf
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1

GROQ_API_KEY=your_groq_key
GROQ_MODEL=llama3-8b-8192

APP_ENV=development
LOG_LEVEL=INFO
SYNC_LOOKBACK_HOURS=24
SYNC_TRIGGER_HOUR=17
SYNC_TRIGGER_MINUTE=0
```

### Initial Index Seed

To populate Pinecone with all currently published articles (rather than waiting for the daily sync window):

```bash
# Temporarily widen the lookback window to cover all articles
# (set SYNC_LOOKBACK_HOURS=100000 in .env), then:
python scripts/seed_pinecone.py
```

Restore `SYNC_LOOKBACK_HOURS` to its normal value (e.g. `24`) afterward so the daily scheduler only picks up recent changes.

### Run the Server

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`, with interactive docs at `http://localhost:8000/docs`.

### Try the Chatbot

```bash
python scripts/chatbot.py
```

---

## Operational Notes

- **Daily sync**: APScheduler triggers a delta sync automatically at `SYNC_TRIGGER_HOUR:SYNC_TRIGGER_MINUTE` (UTC), ingesting only articles updated within `SYNC_LOOKBACK_HOURS`.
- **Idempotent upserts**: Articles are chunked and upserted with deterministic IDs (`{article_id}_chunk_{n}`), so re-syncing an article overwrites its existing vectors rather than duplicating them.
- **Pagination handling**: The Intercom Articles API returns `next` page cursors as full URL strings; `intercom_service.py` parses these correctly to paginate through all results.

See `observations_report.md` for a detailed log of system verification, known issues, and applied fixes.

---

## Roadmap

This repository also contains an in-progress **Hierarchical RAG** extension (Phase 3) on the `feature/hierarchical-rag` branch, which restructures the index into parent (full-article) and child (chunk-level) vectors for improved retrieval precision and richer LLM context — without modifying any of the endpoints or behavior described above.

---

## License

Internal project — Netsmartz LLC. Not for external distribution.
