"""
FastAPI routes for the Hierarchical RAG system.

Mounted at /api/hrag — completely separate from the Phase 2 /api/chat routes.
Both systems run side-by-side; no existing endpoint is touched.

Endpoints:
  POST /api/hrag/chat          — hierarchical RAG chatbot
  POST /api/hrag/sync/full     — ingest all 705 articles from scratch
  POST /api/hrag/sync/trigger  — delta sync (recently updated articles)
  GET  /api/hrag/sync/status   — scheduler + index health
  GET  /api/hrag/admin/stats   — Pinecone namespace vector counts
"""
from __future__ import annotations

import threading

from fastapi import APIRouter, HTTPException

from app.core.logger import logger
from app.models.hierarchical_models import (
    HierarchicalChatRequest,
    HierarchicalChatResponse,
    HierarchicalIngestResult,
)
from app.services.hierarchical import (
    HierarchicalRAGService,
    HierarchicalPineconeService,
    run_full_sync,
    run_delta_sync,
)

router = APIRouter(prefix="/api/hrag", tags=["Hierarchical RAG"])


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

@router.post(
    "/chat",
    response_model=HierarchicalChatResponse,
    summary="Ask the hierarchical RAG chatbot",
    description=(
        "Two-stage retrieval: searches child chunks for precision, "
        "fetches full parent articles for context, then generates an answer "
        "with Groq LLM."
    ),
)
async def hrag_chat(request: HierarchicalChatRequest):
    try:
        svc = HierarchicalRAGService()
        return svc.answer(request)
    except Exception as exc:
        logger.error(f"HRAG chat error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------

@router.post(
    "/sync/full",
    response_model=HierarchicalIngestResult,
    summary="Full sync — ingest all 705 Intercom articles",
    description=(
        "Fetches every published Intercom article and builds the full "
        "hierarchical index (parents + children namespaces). "
        "Runs in the background; check /api/hrag/admin/stats to monitor progress. "
        "Safe to re-run — upserts are idempotent."
    ),
)
async def hrag_full_sync():
    """
    Triggers a full sync in a background thread so the HTTP response
    returns immediately. Monitor progress via server logs or /admin/stats.
    """
    try:
        logger.info("HRAG full sync triggered via API")
        thread = threading.Thread(target=run_full_sync, daemon=True)
        thread.start()
        return {
            "message": (
                "Full hierarchical sync started in background. "
                "This will ingest all 705 Intercom articles. "
                "Monitor progress in server logs or GET /api/hrag/admin/stats."
            ),
            "total_articles": 0,
            "parents_upserted": 0,
            "children_upserted": 0,
            "skipped": 0,
            "errors": 0,
            "duration_seconds": 0.0,
        }
    except Exception as exc:
        logger.error(f"HRAG full sync trigger failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post(
    "/sync/trigger",
    summary="Delta sync — ingest recently updated articles",
    description=(
        "Ingests only articles updated within the configured lookback window "
        "(SYNC_LOOKBACK_HOURS env var, default 24h). "
        "This is the same trigger as the daily scheduler."
    ),
)
async def hrag_delta_sync():
    try:
        logger.info("HRAG delta sync triggered via API")
        thread = threading.Thread(target=run_delta_sync, daemon=True)
        thread.start()
        return {
            "message": (
                "Delta hierarchical sync started in background. "
                "Check server logs for progress."
            )
        }
    except Exception as exc:
        logger.error(f"HRAG delta sync trigger failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Admin / Stats
# ---------------------------------------------------------------------------

@router.get(
    "/admin/stats",
    summary="Pinecone index stats — parents and children namespace counts",
)
async def hrag_index_stats():
    try:
        svc = HierarchicalPineconeService()
        return svc.index_stats()
    except Exception as exc:
        logger.error(f"HRAG stats error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))