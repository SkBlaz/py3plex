"""
Layout computation service
"""
from app.services.io import get_graph, GRAPH_REGISTRY
from app.schemas import NodePosition
import networkx as nx
import logging

logger = logging.getLogger(__name__)

# Thresholds for layout algorithm selection
MAX_NODES_SPRING_LAYOUT = 2000
MAX_NODES_KAMADA_KAWAI = 1000


def compute_layout(graph_id: str, algorithm: str = "spring", seed: int = 42, 
                   dimensions: int = 2, iterations: int = 50):
    """Compute graph layout (optimized for large graphs)"""
    entry = get_graph(graph_id)
    if not entry:
        raise ValueError(f"Graph {graph_id} not found")
    
    graph = entry['graph']
    num_nodes = graph.number_of_nodes()
    
    # Adjust algorithm and parameters based on graph size
    if num_nodes > MAX_NODES_SPRING_LAYOUT and algorithm == "spring":
        logger.warning(f"Large graph ({num_nodes} nodes), switching to faster random layout")
        algorithm = "random"
    elif num_nodes > MAX_NODES_KAMADA_KAWAI and algorithm == "kamada_kawai":
        logger.warning(f"Graph too large for Kamada-Kawai ({num_nodes} nodes), using spring layout")
        algorithm = "spring"
        iterations = min(iterations, 20)  # Limit iterations for large graphs
    
    # Compute layout based on algorithm
    logger.info(f"Computing {algorithm} layout for {num_nodes} nodes")
    
    if algorithm == "spring":
        # Optimize iterations based on graph size
        if num_nodes > 1000:
            iterations = min(iterations, 30)
        elif num_nodes > 500:
            iterations = min(iterations, 40)
        
        pos_dict = nx.spring_layout(graph, k=None, iterations=iterations, seed=seed, dim=dimensions)
        
    elif algorithm == "kamada_kawai":
        pos_dict = nx.kamada_kawai_layout(graph, dim=dimensions)
        
    elif algorithm == "circular":
        pos_dict = nx.circular_layout(graph, dim=dimensions)
        
    elif algorithm == "random":
        pos_dict = nx.random_layout(graph, seed=seed, dim=dimensions)
        
    else:
        # Default to spring with optimized settings
        iterations = min(iterations, 30) if num_nodes > 500 else iterations
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
    
    logger.info(f"Computed {algorithm} layout for graph {graph_id} ({num_nodes} nodes)")
    return positions
