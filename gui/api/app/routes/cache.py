"""
Cache management endpoints
"""
from fastapi import APIRouter, HTTPException
from app.services.model import clear_cache, get_cache_stats
from app.services.io import GRAPH_REGISTRY
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/cache/stats")
async def cache_stats():
    """Get cache statistics"""
    try:
        stats = get_cache_stats()
        return {
            "status": "ok",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache")
async def clear_all_cache():
    """Clear all caches"""
    try:
        clear_cache()
        return {
            "status": "ok",
            "message": "All caches cleared"
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache/{graph_id}")
async def clear_graph_cache(graph_id: str):
    """Clear cache for a specific graph"""
    try:
        clear_cache(graph_id)
        return {
            "status": "ok",
            "message": f"Cache cleared for graph {graph_id}"
        }
    except Exception as e:
        logger.error(f"Error clearing cache for graph {graph_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
