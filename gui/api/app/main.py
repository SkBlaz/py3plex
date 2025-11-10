"""
FastAPI application for Py3plex GUI
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import logging

from app.routes import health, upload, graphs, jobs, analysis, workspace

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Py3plex GUI API",
    description="Backend API for multilayer network analysis and visualization",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add GZip compression middleware for better performance
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(graphs.router, prefix="/api", tags=["Graphs"])
app.include_router(jobs.router, prefix="/api", tags=["Jobs"])
app.include_router(analysis.router, prefix="/api", tags=["Analysis"])
app.include_router(workspace.router, prefix="/api", tags=["Workspace"])

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Py3plex GUI API...")
    
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Py3plex GUI API...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
