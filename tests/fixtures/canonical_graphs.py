"""
Canonical small graph fixtures for deterministic testing.

These graphs are designed to be:
- Small enough for fast testing
- Diverse enough to cover edge cases
- Deterministic and reproducible
- Well-documented with known properties
"""

from py3plex.core.multinet import multi_layer_network


def tiny_two_layer():
    """
    Create a tiny 4-node, 2-layer network for basic testing.
    
    Structure:
        Layer 0: A-B-C (path)
        Layer 1: B-C-D (path)
        
    Properties:
        - 4 unique nodes (A, B, C, D)
        - 2 layers
        - 6 total nodes (node-layer pairs)
        - 4 edges
        - Connected within each layer
        - Nodes B and C appear in both layers
        
    Returns:
        multi_layer_network: Small test network
    """
    net = multi_layer_network(directed=False)
    
    # Add nodes
    net.add_nodes([
        {'source': 'A', 'type': 0},
        {'source': 'B', 'type': 0},
        {'source': 'C', 'type': 0},
        {'source': 'B', 'type': 1},
        {'source': 'C', 'type': 1},
        {'source': 'D', 'type': 1},
    ])
    
    # Add edges
    net.add_edges([
        {'source': 'A', 'target': 'B', 'source_type': 0, 'target_type': 0},
        {'source': 'B', 'target': 'C', 'source_type': 0, 'target_type': 0},
        {'source': 'B', 'target': 'C', 'source_type': 1, 'target_type': 1},
        {'source': 'C', 'target': 'D', 'source_type': 1, 'target_type': 1},
    ])
    
    return net


def small_three_layer():
    """
    Create a small 5-node, 3-layer network.
    
    Structure:
        Layer 0: A-B, B-C (star with B as center)
        Layer 1: B-C, C-D (path)
        Layer 2: D-E (single edge)
        
    Properties:
        - 5 unique nodes (A, B, C, D, E)
        - 3 layers
        - Varying density per layer
        - Node B and C appear in layers 0 and 1
        - Node D appears in layers 1 and 2
        
    Returns:
        multi_layer_network: Small test network
    """
    net = multi_layer_network(directed=False)
    
    # Add nodes
    net.add_nodes([
        {'source': 'A', 'type': 0},
        {'source': 'B', 'type': 0},
        {'source': 'C', 'type': 0},
        {'source': 'B', 'type': 1},
        {'source': 'C', 'type': 1},
        {'source': 'D', 'type': 1},
        {'source': 'D', 'type': 2},
        {'source': 'E', 'type': 2},
    ])
    
    # Add edges
    net.add_edges([
        {'source': 'A', 'target': 'B', 'source_type': 0, 'target_type': 0},
        {'source': 'B', 'target': 'C', 'source_type': 0, 'target_type': 0},
        {'source': 'B', 'target': 'C', 'source_type': 1, 'target_type': 1},
        {'source': 'C', 'target': 'D', 'source_type': 1, 'target_type': 1},
        {'source': 'D', 'target': 'E', 'source_type': 2, 'target_type': 2},
    ])
    
    return net


def two_cliques_bridge():
    """
    Create a network with two cliques connected by a bridge.
    
    This is a canonical structure for testing community detection
    with a known strong signal.
    
    Structure:
        Layer 0: Clique(A, B, C) -- C-D bridge -- Clique(D, E, F)
        
    Properties:
        - 6 unique nodes
        - 1 layer
        - Two K3 cliques connected by a single bridge edge
        - Expected communities: {A, B, C} and {D, E, F}
        - C and D are bridge nodes
        
    Returns:
        multi_layer_network: Network with clear community structure
    """
    net = multi_layer_network(directed=False)
    
    # Add nodes
    net.add_nodes([
        {'source': 'A', 'type': 0},
        {'source': 'B', 'type': 0},
        {'source': 'C', 'type': 0},
        {'source': 'D', 'type': 0},
        {'source': 'E', 'type': 0},
        {'source': 'F', 'type': 0},
    ])
    
    # Add edges for first clique (A-B-C)
    net.add_edges([
        {'source': 'A', 'target': 'B', 'source_type': 0, 'target_type': 0},
        {'source': 'A', 'target': 'C', 'source_type': 0, 'target_type': 0},
        {'source': 'B', 'target': 'C', 'source_type': 0, 'target_type': 0},
    ])
    
    # Add bridge edge
    net.add_edges([
        {'source': 'C', 'target': 'D', 'source_type': 0, 'target_type': 0},
    ])
    
    # Add edges for second clique (D-E-F)
    net.add_edges([
        {'source': 'D', 'target': 'E', 'source_type': 0, 'target_type': 0},
        {'source': 'D', 'target': 'F', 'source_type': 0, 'target_type': 0},
        {'source': 'E', 'target': 'F', 'source_type': 0, 'target_type': 0},
    ])
    
    return net


def path_graph_multilayer(n=5, layers=2):
    """
    Create a path graph replicated across multiple layers.
    
    Structure:
        Each layer: 0-1-2-3-...-n (path graph)
        
    Properties:
        - n nodes per layer
        - Symmetric across layers
        - Known shortest path distances
        - Good for testing path algorithms
        
    Args:
        n: Number of nodes in the path (default: 5)
        layers: Number of layers (default: 2)
        
    Returns:
        multi_layer_network: Path graph network
    """
    net = multi_layer_network(directed=False)
    
    # Add nodes for each layer
    for layer in range(layers):
        for node_id in range(n):
            net.add_nodes([{'source': node_id, 'type': layer}])
    
    # Add edges (path structure) for each layer
    for layer in range(layers):
        for i in range(n - 1):
            net.add_edges([{
                'source': i,
                'target': i + 1,
                'source_type': layer,
                'target_type': layer
            }])
    
    return net
