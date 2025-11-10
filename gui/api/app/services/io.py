"""
I/O service for loading and saving graph files
"""
import os
import aiofiles
from fastapi import UploadFile
from app.deps import get_upload_dir
import uuid
import logging
import networkx as nx

logger = logging.getLogger(__name__)

# In-memory graph registry
GRAPH_REGISTRY = {}


async def save_upload(file: UploadFile, graph_id: str) -> str:
    """Save uploaded file to disk"""
    upload_dir = get_upload_dir()
    graph_dir = f"{upload_dir}/{graph_id}"
    os.makedirs(graph_dir, exist_ok=True)
    
    filepath = f"{graph_dir}/{file.filename}"
    
    async with aiofiles.open(filepath, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    logger.info(f"Saved upload to {filepath}")
    return filepath


def load_graph_from_file(graph_id: str, filepath: str) -> bool:
    """Load graph from file into registry"""
    try:
        # Try to detect format and load
        if filepath.endswith('.edgelist') or filepath.endswith('.txt'):
            # Try multilayer format first (node1 node2 layer weight)
            try:
                graph = load_multilayer_edgelist(filepath)
            except:
                # Fall back to simple edgelist
                graph = nx.read_edgelist(filepath)
        elif filepath.endswith('.gml'):
            graph = nx.read_gml(filepath)
        elif filepath.endswith('.gpickle'):
            graph = nx.read_gpickle(filepath)
        else:
            # Default to edgelist
            graph = nx.read_edgelist(filepath)
        
        # Store in registry
        GRAPH_REGISTRY[graph_id] = {
            'graph': graph,
            'filepath': filepath,
            'positions': None,
            'metadata': {}
        }
        
        logger.info(f"Loaded graph {graph_id}: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
        return True
    except Exception as e:
        logger.error(f"Error loading graph: {e}", exc_info=True)
        return False


def load_multilayer_edgelist(filepath: str) -> nx.MultiGraph:
    """Load multilayer network from edgelist format
    
    Supports formats:
    - node1 node2 layer weight
    - node1 node2 layer
    - node1 node2
    
    Lines starting with # are treated as comments and ignored.
    """
    G = nx.MultiGraph()
    
    with open(filepath, 'r') as f:
        for line in f:
            # Skip empty lines and comments
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split()
            if len(parts) >= 2:
                node1, node2 = parts[0], parts[1]
                layer = parts[2] if len(parts) > 2 else "default"
                weight = float(parts[3]) if len(parts) > 3 else 1.0
                
                G.add_edge(node1, node2, layer=layer, weight=weight)
    
    return G


def get_graph(graph_id: str):
    """Get graph from registry"""
    return GRAPH_REGISTRY.get(graph_id)


def list_graphs():
    """List all graphs in registry"""
    return list(GRAPH_REGISTRY.keys())
