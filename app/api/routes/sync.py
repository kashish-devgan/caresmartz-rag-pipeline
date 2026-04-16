from fastapi import APIRouter, HTTPException
from app.services.scheduler_service import run_sync_job, set_force_flag, get_scheduler_status
from app.core.logger import logger

router = APIRouter(prefix="/api/sync", tags=["Sync"])

@router.post("/trigger", summary="Force trigger a sync immediately")
async def force_trigger():
    try:
        logger.info("Force trigger called via API")
        set_force_flag()
        import threading
        thread = threading.Thread(target=lambda: run_sync_job(force=True))
        thread.daemon = True
        thread.start()
        return {"message": "Sync triggered. Check server logs for progress."}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.get("/status", summary="Get scheduler status and next run time")
async def sync_status():
    return get_scheduler_status()
