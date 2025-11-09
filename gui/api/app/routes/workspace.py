"""
Workspace management endpoints
"""
from fastapi import APIRouter, HTTPException
from app.schemas import WorkspaceSaveRequest, WorkspaceSaveResponse, WorkspaceLoadResponse
from app.services.workspace import save_workspace, load_workspace
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/workspaces/save", response_model=WorkspaceSaveResponse)
async def save_workspace_endpoint(request: WorkspaceSaveRequest):
    """Save workspace as a bundle"""
    try:
        result = save_workspace(
            name=request.name,
            graph_id=request.graph_id,
            view_state=request.view_state
        )
        return result
    except Exception as e:
        logger.error(f"Error saving workspace: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workspaces/load", response_model=WorkspaceLoadResponse)
async def load_workspace_endpoint(workspace_id: str):
    """Load workspace from bundle"""
    try:
        result = load_workspace(workspace_id)
        if not result:
            raise HTTPException(status_code=404, detail="Workspace not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading workspace: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
