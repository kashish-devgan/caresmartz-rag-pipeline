from __future__ import annotations
import asyncio
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.core.config import settings
from app.core.logger import logger

scheduler = BackgroundScheduler()
_force_flag: dict = {"triggered": False}

def set_force_flag():
    _force_flag["triggered"] = True
    logger.info("Force sync flag set - will run on next check")

async def _async_run_sync_job(hours: int) -> dict:
    from app.services.intercom_service import IntercomService
    from app.services.pinecone_service import PineconeService
    from app.services.data_service import articles_to_chunks
    from app.models.article import RawArticle

    pinecone_svc = PineconeService()
    processed_ids, upserted, skipped, errors = [], 0, 0, 0

    async with IntercomService() as intercom_svc:
        updated_summaries = await intercom_svc.get_articles_updated_since(hours=hours)
        logger.info(f"Sync job fetching and processing {len(updated_summaries)} updated Intercom articles (lookback: {hours} hours)")

        for idx, summary in enumerate(updated_summaries, start=1):
            logger.info(f"Processing article [{idx}/{len(updated_summaries)}] id={summary.id}")
            doc = await intercom_svc.get_article_by_id(summary.id)
            if doc is None:
                skipped += 1
                continue

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

    return {
        "total_updated": len(updated_summaries),
        "upserted": upserted,
        "skipped": skipped,
        "errors": errors,
        "article_ids": processed_ids,
    }

def run_sync_job(force: bool = False):
    logger.info("=" * 50)
    logger.info(f"Sync job started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"  Trigger: {'FORCED' if force else 'SCHEDULED (5pm)'}")
    logger.info("=" * 50)

    if _force_flag["triggered"]:
        _force_flag["triggered"] = False

    try:
        lookback_hours = settings.sync_lookback_hours
        result = asyncio.run(_async_run_sync_job(lookback_hours))
        logger.info(f"Sync complete - upserted={result['upserted']} errors={result['errors']} total_updated={result['total_updated']}")
        return result
    except Exception as exc:
        logger.error(f"Sync job failed: {exc}", exc_info=True)
        return {"upserted": 0, "errors": 1, "total_updated": 0}

def start_scheduler():
    scheduler.add_job(
        run_sync_job,
        trigger=CronTrigger(
            hour=settings.sync_trigger_hour,
            minute=settings.sync_trigger_minute,
        ),
        id="caresmartz_daily_sync",
        name=f"CareSmartz daily sync at {settings.sync_trigger_hour:02d}:{settings.sync_trigger_minute:02d}",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()
    logger.info(f"Scheduler started - daily sync at {settings.sync_trigger_hour:02d}:{settings.sync_trigger_minute:02d}")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")

def get_scheduler_status() -> dict:
    if not scheduler.running:
        return {"running": False, "next_run": None}
    jobs = scheduler.get_jobs()
    return {
        "running": True,
        "next_run": str(jobs[0].next_run_time) if jobs else None,
        "trigger_time": f"{settings.sync_trigger_hour:02d}:{settings.sync_trigger_minute:02d} UTC daily",
    }
