"""
File upload endpoints
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.schemas import UploadResponse
from app.services.io import save_upload, load_graph_from_file
import uuid
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload a network file"""
    try:
        # Generate unique graph ID
        graph_id = str(uuid.uuid4())
        
        # Save uploaded file
        filepath = await save_upload(file, graph_id)
        
        # Load graph
        success = load_graph_from_file(graph_id, filepath)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to parse network file")
        
        return UploadResponse(
            graph_id=graph_id,
            filename=file.filename,
            message="File uploaded and parsed successfully"
        )
    except Exception as e:
        logger.error(f"Upload error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
