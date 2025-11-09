"""
Visualization service for serializing graph data for frontend
"""
from app.services.io import get_graph
import logging

logger = logging.getLogger(__name__)


def serialize_graph_for_viz(graph_id: str, include_positions: bool = True):
    """Serialize graph data for visualization"""
    entry = get_graph(graph_id)
    if not entry:
        return None
    
    graph = entry['graph']
    
    # Serialize nodes
    nodes = []
    for node in graph.nodes(data=True):
        nodes.append({
            "id": str(node[0]),
            "attributes": node[1] if len(node) > 1 else {}
        })
    
    # Serialize edges
    edges = []
    for u, v, data in graph.edges(data=True):
        edges.append({
            "source": str(u),
            "target": str(v),
            "layer": data.get('layer', 'default'),
            "weight": data.get('weight', 1.0),
            "attributes": {k: v for k, v in data.items() if k not in ['layer', 'weight']}
        })
    
    result = {
        "graph_id": graph_id,
        "nodes": nodes,
        "edges": edges
    }
    
    # Add positions if available
    if include_positions and entry.get('positions'):
        result['positions'] = [p.dict() for p in entry['positions']]
    
    return result
