#!/usr/bin/env python3
"""
Reusable Hypothesis strategies for py3plex property-based tests.

This module provides common strategies for generating:
- Node names and layer labels
- Weight values
- NetworkX graphs (via hypothesis-networkx)
- Multilayer-specific structures (node-layer tuples, layer sets)
- Probability values
- Integer node IDs

Strategy naming conventions:
- Functions ending in '_strategy' return Hypothesis strategies
- Functions without suffix are callable that return strategies (parametric)
- Strategies prefixed with 'small_' generate small inputs for fast testing
"""

from typing import List, Tuple

import networkx as nx
import numpy as np
from hypothesis import strategies as st

# Try to import hypothesis-networkx if available
try:
    from hypothesis_networkx import graph_builder
    HYPOTHESIS_NETWORKX_AVAILABLE = True
except ImportError:
    HYPOTHESIS_NETWORKX_AVAILABLE = False
    graph_builder = None


# ============================================================================
# Basic primitives
# ============================================================================

def node_names(min_size=1, max_size=10):
    """
    Generate short ASCII lowercase node names.
    
    Args:
        min_size: Minimum string length
        max_size: Maximum string length
    
    Returns:
        Hypothesis strategy for node name strings
        
    Example:
        >>> from hypothesis import given
        >>> @given(node_names())
        ... def test_node_processing(name):
        ...     assert len(name) >= 1
    """
    return st.text(
        min_size=min_size,
        max_size=max_size,
        alphabet=st.characters(min_codepoint=97, max_codepoint=122)  # a-z
    )


def integer_node_ids(min_value=0, max_value=100):
    """
    Generate integer node IDs.
    
    Args:
        min_value: Minimum node ID
        max_value: Maximum node ID
    
    Returns:
        Hypothesis strategy for integer node IDs
    """
    return st.integers(min_value=min_value, max_value=max_value)


def layer_labels(min_size=1, max_size=10):
    """
    Generate short ASCII lowercase layer labels.
    
    Args:
        min_size: Minimum string length
        max_size: Maximum string length
    
    Returns:
        Hypothesis strategy for layer label strings
    """
    return st.text(
        min_size=min_size,
        max_size=max_size,
        alphabet=st.characters(min_codepoint=97, max_codepoint=122)  # a-z
    )


def finite_weights(min_value=0.0, max_value=10.0):
    """
    Generate finite non-negative float weights.
    
    Args:
        min_value: Minimum weight value (inclusive)
        max_value: Maximum weight value (inclusive)
    
    Returns:
        Hypothesis strategy for finite float weights
    """
    return st.floats(
        min_value=min_value,
        max_value=max_value,
        allow_nan=False,
        allow_infinity=False
    )


def positive_weights(min_value=0.01, max_value=10.0):
    """
    Generate strictly positive finite float weights.
    
    Args:
        min_value: Minimum weight value (must be > 0)
        max_value: Maximum weight value
    
    Returns:
        Hypothesis strategy for positive float weights
    """
    return st.floats(
        min_value=min_value,
        max_value=max_value,
        allow_nan=False,
        allow_infinity=False
    )


def probabilities(min_value=0.0, max_value=1.0):
    """
    Generate probability values in [0, 1].
    
    Args:
        min_value: Minimum probability (default 0.0)
        max_value: Maximum probability (default 1.0)
    
    Returns:
        Hypothesis strategy for probability values
    """
    return st.floats(
        min_value=min_value,
        max_value=max_value,
        allow_nan=False,
        allow_infinity=False
    )


# ============================================================================
# NetworkX graph strategies (using hypothesis-networkx if available)
# ============================================================================

def small_graphs(min_nodes=2, max_nodes=8, directed=False, connected=False):
    """
    Generate small NetworkX graphs.
    
    Args:
        min_nodes: Minimum number of nodes
        max_nodes: Maximum number of nodes
        directed: Whether to generate directed graphs
        connected: Whether to enforce connectivity (undirected only)
    
    Returns:
        Hypothesis strategy for NetworkX Graph or DiGraph
    """
    if not HYPOTHESIS_NETWORKX_AVAILABLE:
        # Fallback: generate simple Erdos-Renyi graphs
        @st.composite
        def erdos_renyi_fallback(draw):
            n = draw(st.integers(min_value=min_nodes, max_value=max_nodes))
            p = draw(st.floats(min_value=0.3, max_value=0.8))
            seed = draw(st.integers(min_value=0, max_value=2**31-1))
            
            if directed:
                G = nx.gnp_random_graph(n, p, seed=seed, directed=True)
            else:
                G = nx.gnp_random_graph(n, p, seed=seed)
                if connected and G.number_of_nodes() > 0:
                    # Try to make connected by adding edges if needed
                    if not nx.is_connected(G):
                        # Add edges between components
                        components = list(nx.connected_components(G))
                        for i in range(len(components) - 1):
                            u = list(components[i])[0]
                            v = list(components[i+1])[0]
                            G.add_edge(u, v)
            
            return G
        
        return erdos_renyi_fallback()
    
    # Use hypothesis-networkx
    node_strategy = st.integers(min_value=0, max_value=max_nodes-1)
    
    if directed:
        base = graph_builder(
            graph_type=nx.DiGraph,
            node_keys=node_strategy,
            min_nodes=min_nodes,
            max_nodes=max_nodes
        )
    else:
        base = graph_builder(
            graph_type=nx.Graph,
            node_keys=node_strategy,
            min_nodes=min_nodes,
            max_nodes=max_nodes
        )
    
    if connected and not directed:
        # Filter for connected graphs
        return base.filter(lambda G: G.number_of_nodes() == 0 or nx.is_connected(G))
    
    return base


def connected_graphs(min_nodes=3, max_nodes=8, directed=False):
    """Generate small connected graphs (or weakly connected for directed)."""
    return small_graphs(
        min_nodes=min_nodes,
        max_nodes=max_nodes,
        directed=directed,
        connected=True
    )


def weighted_graphs(min_nodes=2, max_nodes=8, directed=False, connected=False):
    """Generate small weighted NetworkX graphs."""
    @st.composite
    def add_weights(draw):
        G = draw(small_graphs(min_nodes, max_nodes, directed, connected))
        
        # Add random weights to edges
        for u, v in G.edges():
            weight = draw(positive_weights(min_value=0.1, max_value=5.0))
            G[u][v]['weight'] = weight
        
        return G
    
    return add_weights()


# ============================================================================
# Multilayer-specific strategies
# ============================================================================

def node_layer_tuples(max_nodes=5, max_layers=3):
    """Generate (node_name, layer_label) tuples."""
    return st.tuples(
        node_names(max_size=8),
        layer_labels(max_size=8)
    )


def layer_sets(min_layers=1, max_layers=4):
    """Generate sets of layer labels."""
    return st.sets(
        layer_labels(max_size=8),
        min_size=min_layers,
        max_size=max_layers
    )


def node_sets(min_nodes=1, max_nodes=5):
    """Generate sets of node names."""
    return st.sets(
        node_names(max_size=8),
        min_size=min_nodes,
        max_size=max_nodes
    )


def edge_dicts(max_nodes=5, max_layers=3):
    """Generate edge dictionaries for py3plex add_edges()."""
    @st.composite
    def build_edge_dict(draw):
        source = draw(node_names(max_size=8))
        target = draw(node_names(max_size=8))
        source_type = draw(layer_labels(max_size=8))
        target_type = draw(layer_labels(max_size=8))
        
        edge_dict = {
            "source": source,
            "target": target,
            "source_type": source_type,
            "target_type": target_type
        }
        
        # Optionally add weight
        if draw(st.booleans()):
            edge_dict["weight"] = draw(positive_weights())
        
        # Optionally add type
        if draw(st.booleans()):
            edge_dict["type"] = draw(st.sampled_from(["intra", "inter", "coupling"]))
        
        return edge_dict
    
    return build_edge_dict()


def node_dicts(max_nodes=5, max_layers=3):
    """Generate node dictionaries for py3plex add_nodes()."""
    @st.composite
    def build_node_dict(draw):
        source = draw(node_names(max_size=8))
        node_type = draw(layer_labels(max_size=8))
        
        return {
            "source": source,
            "type": node_type
        }
    
    return build_node_dict()


# ============================================================================
# Multilayer network parameters
# ============================================================================

def multilayer_params(min_nodes=3, max_nodes=10, min_layers=1, max_layers=4):
    """Generate parameters for random multilayer networks."""
    @st.composite
    def build_params(draw):
        N = draw(st.integers(min_value=min_nodes, max_value=max_nodes))
        L = draw(st.integers(min_value=min_layers, max_value=max_layers))
        p = draw(st.floats(min_value=0.2, max_value=0.8))
        
        return {
            "N": N,
            "L": L,
            "p": p
        }
    
    return build_params()


# ============================================================================
# Edge list strategies for different formats
# ============================================================================

def edge_lists_with_weights(min_edges=1, max_edges=10):
    """
    Generate edge lists in list format: [[n1, l1, n2, l2, weight], ...].
    
    Args:
        min_edges: Minimum number of edges
        max_edges: Maximum number of edges
    
    Returns:
        Hypothesis strategy for edge lists with weights
    """
    @st.composite
    def build_edge_list(draw):
        num_edges = draw(st.integers(min_value=min_edges, max_value=max_edges))
        edges = []
        for _ in range(num_edges):
            n1 = draw(node_names(max_size=8))
            l1 = draw(layer_labels(max_size=8))
            n2 = draw(node_names(max_size=8))
            l2 = draw(layer_labels(max_size=8))
            w = draw(positive_weights())
            edges.append([n1, l1, n2, l2, w])
        return edges
    
    return build_edge_list()


def simple_edge_lists(min_edges=1, max_edges=10, allow_self_loops=True):
    """
    Generate simple edge lists: [[n1, n2], [n3, n4], ...].
    
    Args:
        min_edges: Minimum number of edges
        max_edges: Maximum number of edges
        allow_self_loops: Whether to allow edges from node to itself
    
    Returns:
        Hypothesis strategy for simple edge lists
    """
    @st.composite
    def build_simple_edge_list(draw):
        num_edges = draw(st.integers(min_value=min_edges, max_value=max_edges))
        edges = []
        for _ in range(num_edges):
            n1 = draw(integer_node_ids(max_value=20))
            n2 = draw(integer_node_ids(max_value=20))
            if not allow_self_loops and n1 == n2:
                # Try one more time
                n2 = (n1 + 1) % 21
            edges.append([n1, n2])
        return edges
    
    return build_simple_edge_list()


# ============================================================================
# Complex multilayer network structures
# ============================================================================

def multilayer_network_spec(min_nodes=3, max_nodes=10, min_layers=1, max_layers=4):
    """
    Generate specifications for creating multilayer networks.
    
    Returns:
        Dictionary with keys: nodes (list), layers (list), edges (list of dicts)
    """
    @st.composite
    def build_network_spec(draw):
        # Generate nodes and layers
        num_nodes = draw(st.integers(min_value=min_nodes, max_value=max_nodes))
        num_layers = draw(st.integers(min_value=min_layers, max_value=max_layers))
        
        nodes = [f"n{i}" for i in range(num_nodes)]
        layers = [f"l{i}" for i in range(num_layers)]
        
        # Generate edges (randomly connect nodes within and across layers)
        num_edges = draw(st.integers(min_value=1, max_value=num_nodes * 2))
        edges = []
        for _ in range(num_edges):
            n1 = draw(st.sampled_from(nodes))
            n2 = draw(st.sampled_from(nodes))
            l1 = draw(st.sampled_from(layers))
            l2 = draw(st.sampled_from(layers))
            w = draw(positive_weights())
            
            edges.append({
                "source": n1,
                "target": n2,
                "source_type": l1,
                "target_type": l2,
                "weight": w
            })
        
        return {
            "nodes": nodes,
            "layers": layers,
            "edges": edges
        }
    
    return build_network_spec()


# ============================================================================
# Utility functions
# ============================================================================

def relabel_graph(G: nx.Graph, seed: int = None) -> Tuple[nx.Graph, dict]:
    """
    Create an isomorphic copy of G with randomly permuted node labels.
    
    Args:
        G: Input graph
        seed: Random seed for reproducibility
    
    Returns:
        (H, mapping): Isomorphic graph H and node mapping dict
    """
    import random
    
    if seed is not None:
        random.seed(seed)
    
    nodes = list(G.nodes())
    shuffled = nodes.copy()
    random.shuffle(shuffled)
    
    mapping = {old: new for old, new in zip(nodes, shuffled)}
    H = nx.relabel_nodes(G, mapping, copy=True)
    
    return H, mapping


def is_valid_partition(partition: dict, nodes: set) -> bool:
    """
    Check if a community partition is valid.
    
    Args:
        partition: Dict mapping nodes to community IDs
        nodes: Set of expected nodes
    
    Returns:
        True if partition is valid (all nodes covered, community IDs are integers)
    """
    if not isinstance(partition, dict):
        return False
    
    # All nodes should be in partition
    if set(partition.keys()) != nodes:
        return False
    
    # All community IDs should be non-negative integers
    return all(isinstance(c, int) and c >= 0 for c in partition.values())


# ============================================================================
# Composite strategies for common test patterns
# ============================================================================

def connected_weighted_graph_with_params(min_nodes=3, max_nodes=8):
    """
    Generate a connected weighted graph with test parameters.
    
    Returns:
        Tuple of (graph, weight_key, test_params)
    """
    @st.composite
    def build(draw):
        G = draw(connected_graphs(min_nodes=min_nodes, max_nodes=max_nodes))
        
        # Add weights
        for u, v in G.edges():
            G[u][v]['weight'] = draw(positive_weights())
        
        weight_key = 'weight'
        test_params = {
            'num_nodes': G.number_of_nodes(),
            'num_edges': G.number_of_edges(),
            'is_connected': nx.is_connected(G)
        }
        
        return G, weight_key, test_params
    
    return build()
