"""
Graph query and manipulation endpoints
"""
from fastapi import APIRouter, HTTPException
from app.schemas import GraphSummary, FilterSpec, FilterResponse, GraphPositions
from app.services.model import get_graph_summary, filter_graph, get_graph_positions, sample_graph
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/graphs/{graph_id}/summary", response_model=GraphSummary)
async def get_summary(graph_id: str):
    """Get graph summary statistics"""
    try:
        summary = get_graph_summary(graph_id)
        if not summary:
            raise HTTPException(status_code=404, detail="Graph not found")
        return summary
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/graphs/{graph_id}/filter", response_model=FilterResponse)
async def filter_graph_endpoint(graph_id: str, spec: FilterSpec):
    """Filter graph based on specifications"""
    try:
        result = filter_graph(graph_id, spec)
        if not result:
            raise HTTPException(status_code=404, detail="Graph not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error filtering graph: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graphs/{graph_id}/positions", response_model=GraphPositions)
async def get_positions(graph_id: str):
    """Get node positions for rendering"""
    try:
        positions = get_graph_positions(graph_id)
        if not positions:
            raise HTTPException(status_code=404, detail="Graph not found or no positions available")
        return positions
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting positions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graphs/{graph_id}/sample")
async def get_sample(graph_id: str, max_nodes: int = 500):
    """Get a sampled subgraph for preview"""
    try:
        result = sample_graph(graph_id, max_nodes)
        if not result:
            raise HTTPException(status_code=404, detail="Graph not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sampling graph: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
