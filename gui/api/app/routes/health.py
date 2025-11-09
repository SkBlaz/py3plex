"""
Health check endpoints
"""
from fastapi import APIRouter
from app.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="ok", version="0.1.0")
