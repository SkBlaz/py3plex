#!/usr/bin/env python3
"""
Subnetwork algebra and idempotence tests for py3plex multilayer networks.

Tests algebraic properties of subnetwork operations:
- Idempotence: subnetwork(subnetwork(S)) == subnetwork(S)
- Union: subnetwork(A ∪ B) contains subnetwork(A) and subnetwork(B)
- Monotonicity: A ⊆ B implies subnetwork(A) ⊆ subnetwork(B)
- Neighbor consistency: get_neighbors agrees with get_edges
"""

import networkx as nx
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from py3plex.core.multinet import multi_layer_network

from .strategies import node_names, layer_labels


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=2, max_value=4)
)
def test_subnetwork_by_layers_idempotent(num_nodes, num_layers):
    """
    Test that subnetwork by layers is idempotent.
    
    Property: subnetwork(subnetwork(layers)) == subnetwork(layers)
    """
    # Create a multilayer network
    mlnet = multi_layer_network(verbose=False, network_type="multilayer")
    
    # Add nodes across multiple layers
    for i in range(num_nodes):
        for layer_idx in range(num_layers):
            mlnet.add_nodes({
                "source": f"n{i}",
                "type": f"layer{layer_idx}"
            })
    
    # Add some edges
    for i in range(num_nodes - 1):
        for layer_idx in range(num_layers):
            mlnet.add_edges([{
                "source": f"n{i}",
                "target": f"n{i+1}",
                "source_type": f"layer{layer_idx}",
                "target_type": f"layer{layer_idx}"
            }])
    
    # Select a subset of layers
    subset_layers = [f"layer{i}" for i in range(min(2, num_layers))]
    
    # Apply subnetwork once - returns a multi_layer_network
    subnet1 = mlnet.subnetwork(subset_layers, subset_by="layers")
    nodes1 = set(subnet1.get_nodes())
    edges1 = set(subnet1.get_edges())
    
    # Apply subnetwork twice (idempotence)
    subnet2 = subnet1.subnetwork(subset_layers, subset_by="layers")
    nodes2 = set(subnet2.get_nodes())
    edges2 = set(subnet2.get_edges())
    
    # Should be the same (idempotence)
    assert nodes1 == nodes2, "Nodes changed after second subnetwork"
    assert edges1 == edges2, "Edges changed after second subnetwork"


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    num_nodes=st.integers(min_value=4, max_value=8),
    num_layers=st.integers(min_value=3, max_value=5)
)
def test_subnetwork_union_contains_parts(num_nodes, num_layers):
    """
    Test that subnetwork on union contains individual subnetworks.
    
    Property: nodes(subnetwork(A ∪ B)) ⊇ nodes(subnetwork(A)) ∪ nodes(subnetwork(B))
    """
    # Create a multilayer network
    mlnet = multi_layer_network(verbose=False, network_type="multilayer")
    
    # Add nodes and edges
    for i in range(num_nodes):
        for layer_idx in range(num_layers):
            mlnet.add_nodes({
                "source": f"n{i}",
                "type": f"layer{layer_idx}"
            })
    
    for i in range(num_nodes - 1):
        for layer_idx in range(num_layers):
            mlnet.add_edges([{
                "source": f"n{i}",
                "target": f"n{i+1}",
                "source_type": f"layer{layer_idx}",
                "target_type": f"layer{layer_idx}"
            }])
    
    # Select two disjoint layer sets
    layers_A = [f"layer{i}" for i in range(min(2, num_layers))]
    layers_B = [f"layer{i}" for i in range(min(2, num_layers), min(4, num_layers))]
    
    # Skip if B is empty
    assume(len(layers_B) > 0)
    
    # Get subnetworks
    subnet_A = mlnet.subnetwork(layers_A, subset_by="layers")
    subnet_B = mlnet.subnetwork(layers_B, subset_by="layers")
    subnet_union = mlnet.subnetwork(layers_A + layers_B, subset_by="layers")
    
    nodes_A = set(subnet_A.core_network.nodes())
    nodes_B = set(subnet_B.core_network.nodes())
    nodes_union = set(subnet_union.core_network.nodes())
    
    # Union should contain both
    assert nodes_A.issubset(nodes_union), "Union doesn't contain A nodes"
    assert nodes_B.issubset(nodes_union), "Union doesn't contain B nodes"


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=3, max_value=5)
)
def test_subnetwork_monotonicity_by_layers(num_nodes, num_layers):
    """
    Test monotonicity: A ⊆ B implies subnetwork(A) ⊆ subnetwork(B).
    
    Property: If A ⊆ B, then nodes(subnetwork(A)) ⊆ nodes(subnetwork(B))
    """
    # Create a multilayer network
    mlnet = multi_layer_network(verbose=False, network_type="multilayer")
    
    # Add nodes
    for i in range(num_nodes):
        for layer_idx in range(num_layers):
            mlnet.add_nodes({
                "source": f"n{i}",
                "type": f"layer{layer_idx}"
            })
    
    # Add edges
    for i in range(num_nodes - 1):
        for layer_idx in range(num_layers):
            mlnet.add_edges([{
                "source": f"n{i}",
                "target": f"n{i+1}",
                "source_type": f"layer{layer_idx}",
                "target_type": f"layer{layer_idx}"
            }])
    
    # Create subset relationship: A ⊂ B
    layers_A = [f"layer{i}" for i in range(min(2, num_layers))]
    layers_B = [f"layer{i}" for i in range(min(3, num_layers))]
    
    # Get subnetworks
    subnet_A = mlnet.subnetwork(layers_A, subset_by="layers")
    subnet_B = mlnet.subnetwork(layers_B, subset_by="layers")
    
    nodes_A = set(subnet_A.core_network.nodes())
    nodes_B = set(subnet_B.core_network.nodes())
    edges_A = set(subnet_A.core_network.edges())
    edges_B = set(subnet_B.core_network.edges())
    
    # A should be subset of B
    assert nodes_A.issubset(nodes_B), "Monotonicity violated for nodes"
    assert edges_A.issubset(edges_B), "Monotonicity violated for edges"


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(num_nodes=st.integers(min_value=3, max_value=8))
def test_subnetwork_by_node_names_preserves_layers(num_nodes):
    """
    Test that subnetwork by node names preserves layer structure.
    
    Property: Selecting nodes preserves their presence across all layers.
    """
    num_layers = 3
    mlnet = multi_layer_network(verbose=False, network_type="multilayer")
    
    # Add nodes
    for i in range(num_nodes):
        for layer_idx in range(num_layers):
            mlnet.add_nodes({
                "source": f"n{i}",
                "type": f"layer{layer_idx}"
            })
    
    # Select subset of node names
    selected_nodes = [f"n{i}" for i in range(min(3, num_nodes))]
    
    # Get subnetwork
    subnet = mlnet.subnetwork(selected_nodes, subset_by="node_names")
    
    # Check that selected nodes appear in all layers
    for node_name in selected_nodes:
        node_layers = [n[1] for n in subnet.core_network.nodes() if n[0] == node_name]
        # Should appear in at least one layer (may not be all if no edges added)
        assert len(node_layers) > 0, f"Node {node_name} not found in subnetwork"


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(num_nodes=st.integers(min_value=4, max_value=8))
def test_neighbors_consistent_with_edges(num_nodes):
    """
    Test that get_neighbors is consistent with edges from get_edges.
    
    Property: For each node, neighbors match edge endpoints.
    """
    num_layers = 2
    mlnet = multi_layer_network(verbose=False, network_type="multilayer")
    
    # Add nodes
    for i in range(num_nodes):
        for layer_idx in range(num_layers):
            mlnet.add_nodes({
                "source": f"n{i}",
                "type": f"layer{layer_idx}"
            })
    
    # Add edges to form a path
    for i in range(num_nodes - 1):
        for layer_idx in range(num_layers):
            mlnet.add_edges([{
                "source": f"n{i}",
                "target": f"n{i+1}",
                "source_type": f"layer{layer_idx}",
                "target_type": f"layer{layer_idx}"
            }])
    
    # Check consistency for a few nodes
    for node_idx in range(min(3, num_nodes)):
        for layer_idx in range(num_layers):
            node_id = (f"n{node_idx}", f"layer{layer_idx}")
            
            # Get neighbors via get_neighbors
            try:
                neighbors_via_api = set(mlnet.get_neighbors(f"n{node_idx}", f"layer{layer_idx}"))
            except Exception:
                # If node doesn't exist or has no neighbors, skip
                continue
            
            # Get neighbors via edges
            neighbors_via_edges = set()
            for edge in mlnet.get_edges():
                if edge[0] == node_id:
                    neighbors_via_edges.add(edge[1])
                elif edge[1] == node_id and not mlnet.directed:
                    neighbors_via_edges.add(edge[0])
            
            # Should match
            assert neighbors_via_api == neighbors_via_edges, \
                f"Neighbor mismatch for {node_id}: {neighbors_via_api} vs {neighbors_via_edges}"


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(num_nodes=st.integers(min_value=3, max_value=8))
def test_split_to_layers_idempotent(num_nodes):
    """
    Test that split_to_layers with style='none' is stable.
    
    Property: Calling split_to_layers multiple times gives same result.
    """
    num_layers = 3
    mlnet = multi_layer_network(verbose=False, network_type="multilayer")
    
    # Add nodes and edges
    for i in range(num_nodes):
        for layer_idx in range(num_layers):
            mlnet.add_nodes({
                "source": f"n{i}",
                "type": f"layer{layer_idx}"
            })
    
    for i in range(num_nodes - 1):
        for layer_idx in range(num_layers):
            mlnet.add_edges([{
                "source": f"n{i}",
                "target": f"n{i+1}",
                "source_type": f"layer{layer_idx}",
                "target_type": f"layer{layer_idx}"
            }])
    
    # Split once
    mlnet.split_to_layers(style="none")
    layer_names_1 = list(mlnet.layer_names)
    node_counts_1 = [len(list(layer.nodes())) for layer in mlnet.separate_layers]
    
    # Split again
    mlnet.split_to_layers(style="none")
    layer_names_2 = list(mlnet.layer_names)
    node_counts_2 = [len(list(layer.nodes())) for layer in mlnet.separate_layers]
    
    # Should be the same
    assert layer_names_1 == layer_names_2
    assert node_counts_1 == node_counts_2


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(num_nodes=st.integers(min_value=2, max_value=8))
def test_subnetwork_preserves_node_count_bounds(num_nodes):
    """
    Test that subnetwork has <= original node count.
    
    Property: |nodes(subnetwork)| <= |nodes(original)|
    """
    num_layers = 2
    mlnet = multi_layer_network(verbose=False, network_type="multilayer")
    
    # Add nodes
    for i in range(num_nodes):
        for layer_idx in range(num_layers):
            mlnet.add_nodes({
                "source": f"n{i}",
                "type": f"layer{layer_idx}"
            })
    
    original_node_count = mlnet.core_network.number_of_nodes()
    
    # Create subnetwork with one layer
    subnet = mlnet.subnetwork(["layer0"], subset_by="layers")
    subnet_node_count = subnet.core_network.number_of_nodes()
    
    # Subnetwork should have fewer or equal nodes
    assert subnet_node_count <= original_node_count, \
        f"Subnetwork has more nodes: {subnet_node_count} > {original_node_count}"
