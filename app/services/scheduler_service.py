from __future__ import annotations
import asyncio
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.core.config import settings
from app.core.logger import logger
from app.data.seed_data import get_fabricated_articles
from app.services.data_service import articles_to_chunks
from app.services.pinecone_service import PineconeService

scheduler = BackgroundScheduler()
_force_flag: dict = {"triggered": False}

def set_force_flag():
    _force_flag["triggered"] = True
    logger.info("Force sync flag set — will run on next check")

def run_sync_job(force: bool = False):
    logger.info("=" * 50)
    logger.info(f"Sync job started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"  Trigger: {'FORCED' if force else 'SCHEDULED (5pm)'}")
    logger.info("=" * 50)

    if _force_flag["triggered"]:
        _force_flag["triggered"] = False

    try:
        articles = get_fabricated_articles()
        chunks = articles_to_chunks(articles)
        svc = PineconeService()
        result = svc.upsert_chunks_batch(chunks)
        logger.info(f"Sync complete — upserted={result['upserted']} errors={result['errors']}")
        return result
    except Exception as exc:
        logger.error(f"Sync job failed: {exc}", exc_info=True)
        return {"upserted": 0, "errors": 1}

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
    logger.info(f"Scheduler started — daily sync at {settings.sync_trigger_hour:02d}:{settings.sync_trigger_minute:02d}")

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
