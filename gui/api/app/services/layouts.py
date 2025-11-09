"""
Layout computation service
"""
from app.services.io import get_graph, GRAPH_REGISTRY
from app.schemas import NodePosition
import networkx as nx
import logging

logger = logging.getLogger(__name__)


def compute_layout(graph_id: str, algorithm: str = "spring", seed: int = 42, 
                   dimensions: int = 2, iterations: int = 50):
    """Compute graph layout"""
    entry = get_graph(graph_id)
    if not entry:
        raise ValueError(f"Graph {graph_id} not found")
    
    graph = entry['graph']
    
    # Compute layout based on algorithm
    if algorithm == "spring":
        pos_dict = nx.spring_layout(graph, k=None, iterations=iterations, seed=seed, dim=dimensions)
    elif algorithm == "kamada_kawai":
        pos_dict = nx.kamada_kawai_layout(graph, dim=dimensions)
    elif algorithm == "circular":
        pos_dict = nx.circular_layout(graph, dim=dimensions)
    elif algorithm == "random":
        pos_dict = nx.random_layout(graph, seed=seed, dim=dimensions)
    else:
        # Default to spring
        pos_dict = nx.spring_layout(graph, seed=seed, dim=dimensions, iterations=iterations)
    
    # Convert to position list
    positions = []
    for node, coords in pos_dict.items():
        pos = NodePosition(
            node_id=str(node),
            x=float(coords[0]),
            y=float(coords[1])
        )
        if dimensions == 3:
            pos.z = float(coords[2])
        positions.append(pos)
    
    # Store positions
    entry['positions'] = positions
    
    logger.info(f"Computed {algorithm} layout for graph {graph_id}")
    return positions
