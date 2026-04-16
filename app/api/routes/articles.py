from __future__ import annotations
import time
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.core.config import settings
from app.core.logger import logger
from app.models.article import ArticleSummary, SyncResult
from app.services.intercom_service import IntercomService
from app.services.pinecone_service import PineconeService

router = APIRouter(prefix="/api/articles", tags=["Articles"])

@router.get("", response_model=dict, summary="List all Intercom articles")
async def list_all_articles(state: Optional[str] = Query(default=None)):
    try:
        async with IntercomService() as svc:
            articles: list[ArticleSummary] = await svc.list_all_articles()
        if state:
            articles = [a for a in articles if a.state == state]
        return {"total": len(articles), "articles": [a.model_dump() for a in articles]}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Intercom API error: {str(exc)}")

@router.get("/updated", response_model=dict, summary="Articles updated in last N hours")
async def get_updated_articles(hours: int = Query(default=settings.sync_lookback_hours, ge=1, le=720)):
    try:
        async with IntercomService() as svc:
            articles = await svc.get_articles_updated_since(hours=hours)
        return {"lookback_hours": hours, "total": len(articles), "articles": [a.model_dump() for a in articles]}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Intercom API error: {str(exc)}")

@router.post("/sync", response_model=SyncResult, summary="Sync updated articles to Pinecone")
async def sync_updated_articles(hours: int = Query(default=settings.sync_lookback_hours, ge=1, le=720)):
    start = time.monotonic()
    pinecone_svc = PineconeService()
    processed_ids, upserted, skipped, errors, updated_summaries = [], 0, 0, 0, []
    try:
        async with IntercomService() as intercom_svc:
            updated_summaries = await intercom_svc.get_articles_updated_since(hours=hours)
            logger.info(f"Starting sync - {len(updated_summaries)} articles to process")
            for idx, summary in enumerate(updated_summaries, start=1):
                logger.info(f"[{idx}/{len(updated_summaries)}] Processing article id={summary.id}")
                doc = await intercom_svc.get_article_by_id(summary.id)
                if doc is None:
                    skipped += 1
                    continue
                if await pinecone_svc.upsert_article(doc):
                    upserted += 1
                    processed_ids.append(doc.id)
                else:
                    errors += 1
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(exc)}")
    duration = round(time.monotonic() - start, 2)
    logger.info(f"Sync complete - upserted={upserted} skipped={skipped} errors={errors} duration={duration}s")
    return SyncResult(total_updated=len(updated_summaries), upserted=upserted, skipped=skipped,
                      errors=errors, duration_seconds=duration, article_ids=processed_ids)

@router.get("/index-stats", summary="Pinecone index statistics")
async def get_index_stats():
    try:
        return {"index": settings.pinecone_index_name, "stats": PineconeService().index_stats()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
