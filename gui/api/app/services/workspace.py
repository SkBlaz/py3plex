"""
Workspace save/load service
"""
from app.services.io import get_graph, GRAPH_REGISTRY
from app.deps import get_workspaces_dir, get_upload_dir
from app.schemas import WorkspaceSaveResponse, WorkspaceLoadResponse
import json
import zipfile
import os
import uuid
import shutil
import logging

logger = logging.getLogger(__name__)


def save_workspace(name: str, graph_id: str, view_state: dict = None):
    """Save workspace as a bundle"""
    entry = get_graph(graph_id)
    if not entry:
        raise ValueError(f"Graph {graph_id} not found")
    
    workspaces_dir = get_workspaces_dir()
    workspace_id = str(uuid.uuid4())
    workspace_file = f"{workspaces_dir}/{name}_{workspace_id}.zip"
    
    # Create workspace bundle
    with zipfile.ZipFile(workspace_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Save metadata
        metadata = {
            "workspace_id": workspace_id,
            "name": name,
            "graph_id": graph_id,
            "view_state": view_state or {}
        }
        zf.writestr("metadata.json", json.dumps(metadata, indent=2))
        
        # Save graph file if available
        if entry['filepath']:
            zf.write(entry['filepath'], arcname=os.path.basename(entry['filepath']))
        
        # Save positions if available
        if entry.get('positions'):
            positions_data = [p.dict() for p in entry['positions']]
            zf.writestr("positions.json", json.dumps(positions_data, indent=2))
    
    logger.info(f"Saved workspace {workspace_id} to {workspace_file}")
    
    return WorkspaceSaveResponse(
        workspace_id=workspace_id,
        filename=os.path.basename(workspace_file),
        message="Workspace saved successfully"
    )


def load_workspace(workspace_id: str):
    """Load workspace from bundle"""
    workspaces_dir = get_workspaces_dir()
    
    # Find workspace file
    workspace_file = None
    for filename in os.listdir(workspaces_dir):
        if workspace_id in filename and filename.endswith('.zip'):
            workspace_file = f"{workspaces_dir}/{filename}"
            break
    
    if not workspace_file or not os.path.exists(workspace_file):
        return None
    
    # Extract workspace
    with zipfile.ZipFile(workspace_file, 'r') as zf:
        # Read metadata
        metadata = json.loads(zf.read("metadata.json"))
        
        # Extract graph file
        graph_id = metadata['graph_id']
        upload_dir = get_upload_dir()
        extract_dir = f"{upload_dir}/{graph_id}"
        os.makedirs(extract_dir, exist_ok=True)
        
        for member in zf.namelist():
            if member not in ['metadata.json', 'positions.json']:
                zf.extract(member, extract_dir)
        
        # Load graph (simplified - would need proper reload logic)
        # For now, just return the metadata
        
        logger.info(f"Loaded workspace {workspace_id}")
        
        return WorkspaceLoadResponse(
            graph_id=graph_id,
            view_state=metadata.get('view_state'),
            message="Workspace loaded successfully"
        )
