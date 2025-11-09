"""
Analysis endpoints (layout, centrality, community detection)
"""
from fastapi import APIRouter, HTTPException
from app.schemas import (
    LayoutRequest, LayoutResponse,
    CentralityRequest, LayoutResponse as AnalysisResponse,
    CommunityRequest
)
from app.workers.tasks import run_layout, run_centrality, run_community
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/graphs/{graph_id}/layout", response_model=LayoutResponse)
async def compute_layout(graph_id: str, request: LayoutRequest):
    """Compute graph layout asynchronously"""
    try:
        task = run_layout.delay(
            graph_id=graph_id,
            algorithm=request.algorithm.value,
            seed=request.seed,
            dimensions=request.dimensions,
            iterations=request.iterations
        )
        return LayoutResponse(job_id=task.id, status="queued")
    except Exception as e:
        logger.error(f"Error starting layout job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/graphs/{graph_id}/analysis/centrality", response_model=AnalysisResponse)
async def compute_centrality(graph_id: str, request: CentralityRequest):
    """Compute centrality metrics asynchronously"""
    try:
        task = run_centrality.delay(
            graph_id=graph_id,
            metrics=[m.value for m in request.metrics],
            layers=request.layers
        )
        return AnalysisResponse(job_id=task.id, status="queued")
    except Exception as e:
        logger.error(f"Error starting centrality job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/graphs/{graph_id}/analysis/community", response_model=AnalysisResponse)
async def compute_community(graph_id: str, request: CommunityRequest):
    """Compute community detection asynchronously"""
    try:
        task = run_community.delay(
            graph_id=graph_id,
            algorithm=request.algorithm.value,
            resolution=request.resolution,
            seed=request.seed
        )
        return AnalysisResponse(job_id=task.id, status="queued")
    except Exception as e:
        logger.error(f"Error starting community detection job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
