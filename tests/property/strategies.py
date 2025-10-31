#!/usr/bin/env python3
"""
Reusable Hypothesis strategies for py3plex property-based tests.

This module provides common strategies for generating:
- Node names and layer labels
- Weight values
- NetworkX graphs (via hypothesis-networkx)
- Multilayer-specific structures (node-layer tuples, layer sets)
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
    """Generate short ASCII lowercase node names."""
    return st.text(
        min_size=min_size,
        max_size=max_size,
        alphabet=st.characters(min_codepoint=97, max_codepoint=122)  # a-z
    )


def layer_labels(min_size=1, max_size=10):
    """Generate short ASCII lowercase layer labels."""
    return st.text(
        min_size=min_size,
        max_size=max_size,
        alphabet=st.characters(min_codepoint=97, max_codepoint=122)  # a-z
    )


def finite_weights(min_value=0.0, max_value=10.0):
    """Generate finite non-negative float weights."""
    return st.floats(
        min_value=min_value,
        max_value=max_value,
        allow_nan=False,
        allow_infinity=False
    )


def positive_weights(min_value=0.01, max_value=10.0):
    """Generate strictly positive finite float weights."""
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
