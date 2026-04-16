from fastapi import APIRouter, HTTPException
from app.services.scheduler_service import (
    get_scheduler_status,
    run_sync_job,
    start_scheduler,
    stop_scheduler,
    scheduler,
)
from app.core.logger import logger

router = APIRouter(prefix="/api/scheduler", tags=["Scheduler"])


@router.get("", summary="Get scheduler status and next run time")
async def get_status():
    return get_scheduler_status()


@router.post("/trigger", summary="Manually trigger a sync right now")
async def trigger_sync():
    try:
        logger.info("Manual trigger called from API")
        import threading
        thread = threading.Thread(target=run_sync_job)
        thread.daemon = True
        thread.start()
        return {"message": "Sync job triggered. Check server logs for progress."}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/pause", summary="Pause the scheduled sync")
async def pause_scheduler():
    try:
        scheduler.pause()
        return {"message": "Scheduler paused"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/resume", summary="Resume the scheduled sync")
async def resume_scheduler():
    try:
        scheduler.resume()
        return {"message": "Scheduler resumed"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
