"""
Test upload endpoint
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
import io

client = TestClient(app)


def test_upload_edgelist():
    """Test uploading a simple edge list"""
    # Create a simple edge list file
    content = b"1 2\n2 3\n3 4\n"
    files = {"file": ("test.edgelist", io.BytesIO(content), "text/plain")}
    
    response = client.post("/api/upload", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "graph_id" in data
    assert data["filename"] == "test.edgelist"
    assert "message" in data
