"""
Hierarchical ingestion service for the CareSmartz RAG pipeline.

Fetches articles from Intercom, converts them to parent + child
representations, and upserts both into Pinecone.

Two modes of operation:

  Full sync  — ingests all 705 published articles from scratch.
               Use once on initial setup or after a schema change.
               Triggered via POST /api/hrag/sync/full

  Delta sync — ingests only articles updated in the last N hours.
               Runs on the existing APScheduler daily cron.
               Triggered via POST /api/hrag/sync/trigger (or scheduler)

Both modes are idempotent: re-running upserts by deterministic IDs so
no duplicate vectors are created.
"""
from __future__ import annotations

import asyncio
import time
from datetime import datetime

from app.core.config import settings
from app.core.logger import logger
from app.models.article import RawArticle
from app.models.hierarchical_models import HierarchicalIngestResult
from app.services.intercom_service import IntercomService          # reused from Phase 2
from app.services.hierarchical.chunker import articles_to_hierarchy
from app.services.hierarchical.pinecone_hrag import HierarchicalPineconeService


# ---------------------------------------------------------------------------
# Internal async worker
# ---------------------------------------------------------------------------

async def _run_ingest(
    hours: int | None,
    label: str,
) -> HierarchicalIngestResult:
    """
    Core async ingestion worker shared by full and delta sync paths.

    Args:
        hours:  Lookback window in hours. None means fetch ALL articles.
        label:  Log label to distinguish full vs delta runs.
    """
    start_time = time.time()
    pinecone_svc = HierarchicalPineconeService()

    all_raw: list[RawArticle] = []
    skipped = 0

    async with IntercomService() as intercom:
        if hours is None:
            # Full sync: fetch all article summaries then each full article
            summaries = await intercom.list_all_articles()
            logger.info(
                f"[{label}] Full sync: {len(summaries)} articles to ingest"
            )
        else:
            summaries = await intercom.get_articles_updated_since(hours=hours)
            logger.info(
                f"[{label}] Delta sync: {len(summaries)} articles updated "
                f"in the last {hours} hours"
            )

        for idx, summary in enumerate(summaries, start=1):
            if idx % 50 == 0 or idx == len(summaries):
                logger.info(
                    f"[{label}] Fetching article "
                    f"[{idx}/{len(summaries)}] id={summary.id}"
                )
            doc = await intercom.get_article_by_id(summary.id)
            if doc is None:
                skipped += 1
                continue

            all_raw.append(RawArticle(
                id=doc.id,
                title=doc.title,
                description=doc.description,
                body=doc.body,
                url=doc.source_url,
                updated_at=doc.updated_at,
                image_urls=doc.image_urls,
            ))

    if not all_raw:
        logger.warning(f"[{label}] No articles to ingest after fetching")
        return HierarchicalIngestResult(
            total_articles=len(summaries),
            parents_upserted=0,
            children_upserted=0,
            skipped=skipped,
            errors=0,
            duration_seconds=round(time.time() - start_time, 2),
        )

    # --- Chunking ---
    logger.info(f"[{label}] Building hierarchical representations...")
    parents, children = articles_to_hierarchy(all_raw)

    # --- Upsert parents ---
    logger.info(f"[{label}] Upserting {len(parents)} parent documents...")
    parent_result = pinecone_svc.upsert_parents_batch(parents)

    # --- Upsert children ---
    logger.info(f"[{label}] Upserting {len(children)} child chunks...")
    child_result = pinecone_svc.upsert_children_batch(children)

    duration = round(time.time() - start_time, 2)
    total_errors = parent_result["errors"] + child_result["errors"]

    logger.info(
        f"[{label}] Ingestion complete in {duration}s — "
        f"parents={parent_result['upserted']} "
        f"children={child_result['upserted']} "
        f"skipped={skipped} errors={total_errors}"
    )

    return HierarchicalIngestResult(
        total_articles=len(all_raw),
        parents_upserted=parent_result["upserted"],
        children_upserted=child_result["upserted"],
        skipped=skipped,
        errors=total_errors,
        duration_seconds=duration,
        article_ids=[str(a.id) for a in all_raw],
    )


# ---------------------------------------------------------------------------
# Public sync functions (called by routes + scheduler)
# ---------------------------------------------------------------------------

def run_full_sync() -> HierarchicalIngestResult:
    """
    Ingest ALL 705 Intercom articles from scratch.
    Blocking wrapper around the async worker — safe to call from
    a background thread (APScheduler) or a FastAPI route via asyncio.run().
    """
    logger.info("=" * 60)
    logger.info(f"HRAG FULL SYNC started at {datetime.now():%Y-%m-%d %H:%M:%S}")
    logger.info("=" * 60)
    try:
        return asyncio.run(_run_ingest(hours=None, label="FULL"))
    except Exception as exc:
        logger.error(f"HRAG full sync failed: {exc}", exc_info=True)
        return HierarchicalIngestResult(
            total_articles=0, parents_upserted=0, children_upserted=0,
            skipped=0, errors=1, duration_seconds=0.0,
        )


def run_delta_sync(hours: int | None = None) -> HierarchicalIngestResult:
    """
    Ingest only articles updated in the last N hours.
    Uses settings.sync_lookback_hours if hours is not provided.
    Blocking wrapper — same thread-safety contract as run_full_sync().
    """
    lookback = hours or settings.sync_lookback_hours
    logger.info("=" * 60)
    logger.info(
        f"HRAG DELTA SYNC started at {datetime.now():%Y-%m-%d %H:%M:%S} "
        f"(lookback: {lookback}h)"
    )
    logger.info("=" * 60)
    try:
        return asyncio.run(_run_ingest(hours=lookback, label="DELTA"))
    except Exception as exc:
        logger.error(f"HRAG delta sync failed: {exc}", exc_info=True)
        return HierarchicalIngestResult(
            total_articles=0, parents_upserted=0, children_upserted=0,
            skipped=0, errors=1, duration_seconds=0.0,
        )