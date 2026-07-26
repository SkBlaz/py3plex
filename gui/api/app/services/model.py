"""
Graph model and query service
"""
from app.services.io import get_graph, GRAPH_REGISTRY
from app.schemas import GraphSummary, FilterSpec, FilterResponse, NodePosition, GraphPositions, GraphEdge
import networkx as nx
import uuid
import logging
import random
from functools import lru_cache

logger = logging.getLogger(__name__)

# Cache for expensive computations
SUMMARY_CACHE = {}
POSITION_CACHE = {}


def get_graph_summary(graph_id: str):
    """Get summary statistics for a graph (cached)"""
    # Check cache first
    if graph_id in SUMMARY_CACHE:
        logger.debug(f"Using cached summary for graph {graph_id}")
        return SUMMARY_CACHE[graph_id]
    
    entry = get_graph(graph_id)
    if not entry:
        return None
    
    graph = entry['graph']
    
    # Extract layers (optimized with set comprehension)
    layers = {data.get('layer') for u, v, data in graph.edges(data=True) if 'layer' in data}
    
    # Extract attributes (optimized)
    attributes = set()
    for node, data in graph.nodes(data=True):
        attributes.update(data.keys())
    
    summary = GraphSummary(
        graph_id=graph_id,
        nodes=graph.number_of_nodes(),
        edges=graph.number_of_edges(),
        layers=sorted(list(layers)) if layers else ["default"],
        attributes=sorted(list(attributes))
    )
    
    # Cache the result
    SUMMARY_CACHE[graph_id] = summary
    logger.debug(f"Cached summary for graph {graph_id}")
    
    return summary


def filter_graph(graph_id: str, spec: FilterSpec):
    """Filter graph based on specification (optimized)"""
    entry = get_graph(graph_id)
    if not entry:
        return None
    
    graph = entry['graph']
    
    # Use subgraph view for better performance when possible
    nodes_to_keep = set(graph.nodes())
    
    # Filter by degree (optimized with list comprehension)
    if spec.min_degree is not None or spec.max_degree is not None:
        degree_dict = dict(graph.degree())
        nodes_to_keep = {
            node for node in nodes_to_keep
            if (spec.min_degree is None or degree_dict[node] >= spec.min_degree) and
               (spec.max_degree is None or degree_dict[node] <= spec.max_degree)
        }
    
    # Create subgraph from filtered nodes
    subgraph = graph.subgraph(nodes_to_keep).copy()
    
    # Filter by layers if specified
    if spec.layers:
        edges_to_remove = [
            (u, v, key) for u, v, key, data in subgraph.edges(keys=True, data=True)
            if 'layer' in data and data['layer'] not in spec.layers
        ]
        subgraph.remove_edges_from(edges_to_remove)
    
    # Generate new subgraph ID
    subgraph_id = str(uuid.uuid4())
    GRAPH_REGISTRY[subgraph_id] = {
        'graph': subgraph,
        'filepath': None,
        'positions': None,
        'metadata': {'parent': graph_id}
    }
    
    # Invalidate caches for new subgraph
    logger.debug(f"Created filtered subgraph {subgraph_id} from {graph_id}")
    
    return FilterResponse(
        subgraph_id=subgraph_id,
        original_graph_id=graph_id,
        nodes=subgraph.number_of_nodes(),
        edges=subgraph.number_of_edges()
    )


def get_graph_positions(graph_id: str):
    """Get node positions for visualization (cached)"""
    # Check cache first
    if graph_id in POSITION_CACHE:
        logger.debug(f"Using cached positions for graph {graph_id}")
        return POSITION_CACHE[graph_id]
    
    entry = get_graph(graph_id)
    if not entry:
        return None

    graph = entry['graph']

    # Use stored positions or generate default
    positions = entry.get('positions')
    if not positions:
        # For large graphs, use faster layout algorithm
        num_nodes = graph.number_of_nodes()
        if num_nodes > 1000:
            logger.info(f"Large graph ({num_nodes} nodes), using random layout for speed")
            pos_dict = nx.random_layout(graph, seed=42)
        else:
            # Generate spring layout as default with limited iterations
            pos_dict = nx.spring_layout(graph, seed=42, iterations=20)
        
        positions = [
            NodePosition(
                node_id=str(node),
                x=float(coords[0]),
                y=float(coords[1]),
                layer="default"
            )
            for node, coords in pos_dict.items()
        ]
        entry['positions'] = positions

    edges = [
        GraphEdge(source=str(u), target=str(v), layer=data.get('layer'))
        for u, v, data in graph.edges(data=True)
    ]

    result = GraphPositions(
        graph_id=graph_id,
        positions=positions,
        edges=edges
    )
    
    # Cache the result
    POSITION_CACHE[graph_id] = result
    logger.debug(f"Cached positions for graph {graph_id}")
    
    return result


def sample_graph(graph_id: str, max_nodes: int = 500):
    """Sample a subgraph for preview (optimized)"""
    entry = get_graph(graph_id)
    if not entry:
        return None
    
    graph = entry['graph']
    
    if graph.number_of_nodes() <= max_nodes:
        # Return full graph if small enough
        return get_graph_summary(graph_id)
    
    # Sample nodes (optimized with random.sample)
    sampled_nodes = random.sample(list(graph.nodes()), max_nodes)
    subgraph = graph.subgraph(sampled_nodes)
    
    return {
        "graph_id": graph_id,
        "sampled": True,
        "nodes": subgraph.number_of_nodes(),
        "edges": subgraph.number_of_edges(),
        "total_nodes": graph.number_of_nodes(),
        "total_edges": graph.number_of_edges()
    }


def clear_cache(graph_id: str = None):
    """Clear caches for specific graph or all graphs"""
    global SUMMARY_CACHE, POSITION_CACHE
    
    if graph_id:
        SUMMARY_CACHE.pop(graph_id, None)
        POSITION_CACHE.pop(graph_id, None)
        logger.info(f"Cleared cache for graph {graph_id}")
    else:
        SUMMARY_CACHE.clear()
        POSITION_CACHE.clear()
        logger.info("Cleared all caches")


def get_cache_stats():
    """Get cache statistics for monitoring"""
    return {
        "summary_cache_size": len(SUMMARY_CACHE),
        "position_cache_size": len(POSITION_CACHE),
        "graph_registry_size": len(GRAPH_REGISTRY)
    }
