"""
Dependencies and utilities for dependency injection
"""
import os
from typing import Optional

# Configuration
DATA_DIR = os.getenv("DATA_DIR", "/data")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "512"))

# Ensure directories exist (with error handling for test environments)
try:
    os.makedirs(f"{DATA_DIR}/uploads", exist_ok=True)
    os.makedirs(f"{DATA_DIR}/artifacts", exist_ok=True)
    os.makedirs(f"{DATA_DIR}/workspaces", exist_ok=True)
except (PermissionError, OSError) as e:
    # In test environments without /data, use temp directory
    import tempfile
    DATA_DIR = tempfile.mkdtemp()
    os.makedirs(f"{DATA_DIR}/uploads", exist_ok=True)
    os.makedirs(f"{DATA_DIR}/artifacts", exist_ok=True)
    os.makedirs(f"{DATA_DIR}/workspaces", exist_ok=True)


def get_upload_dir() -> str:
    """Get upload directory path"""
    return f"{DATA_DIR}/uploads"


def get_artifacts_dir() -> str:
    """Get artifacts directory path"""
    return f"{DATA_DIR}/artifacts"


def get_workspaces_dir() -> str:
    """Get workspaces directory path"""
    return f"{DATA_DIR}/workspaces"
