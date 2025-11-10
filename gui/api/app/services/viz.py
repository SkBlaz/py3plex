"""
Visualization service for serializing graph data for frontend
"""
from app.services.io import get_graph
import logging

logger = logging.getLogger(__name__)

# Maximum items to serialize at once to prevent memory issues
MAX_NODES_FULL_SERIALIZATION = 5000
MAX_EDGES_FULL_SERIALIZATION = 10000


def serialize_graph_for_viz(graph_id: str, include_positions: bool = True, 
                           limit_nodes: int = None, limit_edges: int = None):
    """Serialize graph data for visualization (optimized with optional limits)"""
    entry = get_graph(graph_id)
    if not entry:
        return None
    
    graph = entry['graph']
    num_nodes = graph.number_of_nodes()
    num_edges = graph.number_of_edges()
    
    # Apply automatic limits for large graphs
    if limit_nodes is None and num_nodes > MAX_NODES_FULL_SERIALIZATION:
        limit_nodes = MAX_NODES_FULL_SERIALIZATION
        logger.warning(f"Large graph ({num_nodes} nodes), limiting to {limit_nodes}")
    
    if limit_edges is None and num_edges > MAX_EDGES_FULL_SERIALIZATION:
        limit_edges = MAX_EDGES_FULL_SERIALIZATION
        logger.warning(f"Large graph ({num_edges} edges), limiting to {limit_edges}")
    
    # Serialize nodes (with optional limit)
    nodes = []
    for i, (node, data) in enumerate(graph.nodes(data=True)):
        if limit_nodes and i >= limit_nodes:
            break
        nodes.append({
            "id": str(node),
            "attributes": data if data else {}
        })
    
    # Serialize edges (with optional limit)
    edges = []
    for i, (u, v, data) in enumerate(graph.edges(data=True)):
        if limit_edges and i >= limit_edges:
            break
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
        "edges": edges,
        "metadata": {
            "total_nodes": num_nodes,
            "total_edges": num_edges,
            "nodes_serialized": len(nodes),
            "edges_serialized": len(edges),
            "truncated": (limit_nodes and len(nodes) < num_nodes) or 
                        (limit_edges and len(edges) < num_edges)
        }
    }
    
    # Add positions if available
    if include_positions and entry.get('positions'):
        # Limit positions to match nodes if truncated
        positions = entry['positions']
        if limit_nodes and len(positions) > limit_nodes:
            positions = positions[:limit_nodes]
        result['positions'] = [p.dict() for p in positions]
    
    return result
