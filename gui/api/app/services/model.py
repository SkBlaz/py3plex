"""
Graph model and query service
"""
from app.services.io import get_graph, GRAPH_REGISTRY
from app.schemas import GraphSummary, FilterSpec, FilterResponse, NodePosition, GraphPositions
import networkx as nx
import uuid
import logging
import random

logger = logging.getLogger(__name__)


def get_graph_summary(graph_id: str):
    """Get summary statistics for a graph"""
    entry = get_graph(graph_id)
    if not entry:
        return None
    
    graph = entry['graph']
    
    # Extract layers
    layers = set()
    for u, v, data in graph.edges(data=True):
        if 'layer' in data:
            layers.add(data['layer'])
    
    # Extract attributes
    attributes = set()
    for node, data in graph.nodes(data=True):
        attributes.update(data.keys())
    
    return GraphSummary(
        graph_id=graph_id,
        nodes=graph.number_of_nodes(),
        edges=graph.number_of_edges(),
        layers=sorted(list(layers)) if layers else ["default"],
        attributes=sorted(list(attributes))
    )


def filter_graph(graph_id: str, spec: FilterSpec):
    """Filter graph based on specification"""
    entry = get_graph(graph_id)
    if not entry:
        return None
    
    graph = entry['graph']
    subgraph = graph.copy()
    
    # Filter by degree
    if spec.min_degree is not None or spec.max_degree is not None:
        nodes_to_remove = []
        for node in subgraph.nodes():
            degree = subgraph.degree(node)
            if spec.min_degree and degree < spec.min_degree:
                nodes_to_remove.append(node)
            if spec.max_degree and degree > spec.max_degree:
                nodes_to_remove.append(node)
        subgraph.remove_nodes_from(nodes_to_remove)
    
    # Filter by layers
    if spec.layers:
        edges_to_remove = []
        for u, v, key, data in subgraph.edges(keys=True, data=True):
            if 'layer' in data and data['layer'] not in spec.layers:
                edges_to_remove.append((u, v, key))
        subgraph.remove_edges_from(edges_to_remove)
    
    # Generate new subgraph ID
    subgraph_id = str(uuid.uuid4())
    GRAPH_REGISTRY[subgraph_id] = {
        'graph': subgraph,
        'filepath': None,
        'positions': None,
        'metadata': {'parent': graph_id}
    }
    
    return FilterResponse(
        subgraph_id=subgraph_id,
        original_graph_id=graph_id,
        nodes=subgraph.number_of_nodes(),
        edges=subgraph.number_of_edges()
    )


def get_graph_positions(graph_id: str):
    """Get node positions for visualization"""
    entry = get_graph(graph_id)
    if not entry:
        return None
    
    # Use stored positions or generate default
    positions = entry.get('positions')
    if not positions:
        graph = entry['graph']
        # Generate spring layout as default
        pos_dict = nx.spring_layout(graph, seed=42)
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
    
    return GraphPositions(
        graph_id=graph_id,
        positions=positions
    )


def sample_graph(graph_id: str, max_nodes: int = 500):
    """Sample a subgraph for preview"""
    entry = get_graph(graph_id)
    if not entry:
        return None
    
    graph = entry['graph']
    
    if graph.number_of_nodes() <= max_nodes:
        # Return full graph if small enough
        return get_graph_summary(graph_id)
    
    # Sample nodes
    nodes = list(graph.nodes())
    sampled_nodes = random.sample(nodes, max_nodes)
    subgraph = graph.subgraph(sampled_nodes)
    
    return {
        "graph_id": graph_id,
        "sampled": True,
        "nodes": subgraph.number_of_nodes(),
        "edges": subgraph.number_of_edges(),
        "total_nodes": graph.number_of_nodes(),
        "total_edges": graph.number_of_edges()
    }
