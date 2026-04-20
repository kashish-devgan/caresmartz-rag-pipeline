from __future__ import annotations
import time
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.core.config import settings
from app.core.logger import logger
from app.models.article import ArticleSummary, RawArticle, SyncResult
from app.services.intercom_service import IntercomService
from app.services.pinecone_service import PineconeService
from app.services.data_service import articles_to_chunks  

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

@router.post("/sync", response_model=SyncResult,
             summary="Sync updated articles to Pinecone")
async def sync_updated_articles(
    hours: int = Query(default=settings.sync_lookback_hours, ge=1, le=720)):
    start = time.monotonic()
    pinecone_svc = PineconeService()
    processed_ids, upserted, skipped, errors = [], 0, 0, 0
    updated_summaries = []

    try:
        async with IntercomService() as intercom_svc:
            updated_summaries = await intercom_svc.get_articles_updated_since(hours=hours)
            logger.info(f"Starting sync - {len(updated_summaries)} articles to process")

            for idx, summary in enumerate(updated_summaries, start=1):
                logger.info(f"[{idx}/{len(updated_summaries)}] id={summary.id}")
                doc = await intercom_svc.get_article_by_id(summary.id)
                if doc is None:
                    skipped += 1
                    continue

                # Convert ArticleDocument → RawArticle → chunks → upsert
                raw = RawArticle(
                    id=doc.id,
                    title=doc.title,
                    description=doc.description,
                    body=doc.body,
                    url=doc.source_url,
                    updated_at=doc.updated_at,
                    image_urls=doc.image_urls,
                )
                chunks = articles_to_chunks([raw])
                if not chunks:
                    logger.warning(f"Article {doc.id} produced no chunks - skipping")
                    skipped += 1
                    continue

                result = pinecone_svc.upsert_chunks_batch(chunks)
                if result["errors"] == 0:
                    upserted += result["upserted"]
                    processed_ids.append(doc.id)
                else:
                    logger.warning(
                        f"Article {doc.id} partially failed: "
                        f"upserted={result['upserted']} errors={result['errors']}"
                    )
                    upserted += result["upserted"]
                    errors += result["errors"]
                    processed_ids.append(doc.id)

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(exc)}")

    duration = round(time.monotonic() - start, 2)
    return SyncResult(
        total_updated=len(updated_summaries),
        upserted=upserted,
        skipped=skipped,
        errors=errors,
        duration_seconds=duration,
        article_ids=processed_ids,
    )

@router.get("/index-stats", summary="Pinecone index statistics")
async def get_index_stats():
    try:
        return {"index": settings.pinecone_index_name, "stats": PineconeService().index_stats()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
