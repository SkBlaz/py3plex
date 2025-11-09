"""
Job monitoring endpoints
"""
from fastapi import APIRouter, HTTPException
from app.schemas import JobResponse
from app.workers.celery_app import celery_app
from celery.result import AsyncResult
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str):
    """Get job status and results"""
    try:
        task = AsyncResult(job_id, app=celery_app)
        
        if task.state == "PENDING":
            return JobResponse(
                job_id=job_id,
                status="queued",
                progress=0
            )
        elif task.state == "STARTED" or task.state == "PROGRESS":
            info = task.info or {}
            return JobResponse(
                job_id=job_id,
                status="running",
                progress=info.get("progress", 0),
                phase=info.get("phase", "processing")
            )
        elif task.state == "SUCCESS":
            result = task.result or {}
            return JobResponse(
                job_id=job_id,
                status="completed",
                progress=100,
                result=result,
                artifacts=result.get("artifacts", [])
            )
        elif task.state == "FAILURE":
            return JobResponse(
                job_id=job_id,
                status="failed",
                error=str(task.info)
            )
        else:
            return JobResponse(
                job_id=job_id,
                status="queued"
            )
    except Exception as e:
        logger.error(f"Error getting job status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a running job (best effort)"""
    try:
        task = AsyncResult(job_id, app=celery_app)
        task.revoke(terminate=True)
        return {"message": "Job cancellation requested", "job_id": job_id}
    except Exception as e:
        logger.error(f"Error cancelling job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
