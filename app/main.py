"""
CareSmartz RAG API — main application factory.

Version 3.0 adds the Hierarchical RAG router at /api/hrag.
All Phase 2 routes (/api/chat, /api/sync, /api/articles) are unchanged.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logger import logger

# --- Phase 2 imports (unchanged) ---
from app.api.routes.articles import router as articles_router
from app.api.routes.sync import router as sync_router
from app.api.routes.chat import router as chat_router
from app.services.pinecone_service import ensure_pinecone_index
from app.services.scheduler_service import start_scheduler, stop_scheduler

# --- Phase 3: Hierarchical RAG ---
from app.api.routes.hrag_router import router as hrag_router
from app.services.hierarchical.pinecone_hrag import ensure_hierarchical_index


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("CareSmartz RAG service starting...")
    logger.info(f"  Environment : {settings.app_env}")
    logger.info(f"  Pinecone    : {settings.pinecone_index_name}")
    logger.info(f"  Embed model : {settings.embedding_model}")
    logger.info(f"  LLM         : {settings.groq_model}")
    logger.info(f"  Daily sync  : {settings.sync_trigger_hour:02d}:{settings.sync_trigger_minute:02d} UTC")

    # Phase 2 index (flat, default namespace)
    ensure_pinecone_index()

    # Phase 3 namespaces (hrag_parents, hrag_children) — idempotent
    ensure_hierarchical_index()

    start_scheduler()
    logger.info("Ready to serve requests.")
    yield
    stop_scheduler()
    logger.info("Shutting down.")


app = FastAPI(
    title="CareSmartz RAG API",
    version="3.0.0",
    lifespan=lifespan,
    description=(
        "Phase 2: flat RAG at /api/chat\n"
        "Phase 3: hierarchical RAG at /api/hrag"
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.app_env == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Register all routers ---
app.include_router(articles_router)     # /api/articles  (Phase 2, unchanged)
app.include_router(sync_router)         # /api/sync       (Phase 2, unchanged)
app.include_router(chat_router)         # /api/chat       (Phase 2, unchanged)
app.include_router(hrag_router)         # /api/hrag       (Phase 3, new)


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "env": settings.app_env,
        "version": "3.0.0",
        "systems": {
            "flat_rag": "/api/chat",
            "hierarchical_rag": "/api/hrag/chat",
        },
    }