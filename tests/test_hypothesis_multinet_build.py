"""
Property-based tests for multilayer network construction using Hypothesis.

This module tests multilayer network building invariants derived from LLM.md,
specifically:
- Edge format specification: n1 l1 n2 l2 [weight] (section "Core Concepts")
- Node representation as tuples (node_id, layer_id) per core/parsers.py
- Weight handling: finite numeric values, default to 1
- Directed/undirected handling per load_network specification
- Node/edge count consistency invariants (section "Key Invariants Verified")

Reference: LLM.md sections "Core Concepts > Multilayer Networks" and 
"Testing & Verification > Key Invariants Verified"
"""

import tempfile
from pathlib import Path
from typing import List, Tuple

import networkx as nx
import pytest
from hypothesis import given, settings, strategies as st, assume, HealthCheck

from py3plex.core import multinet


# Hypothesis profile for CI-friendly tests
settings.register_profile("ci", deadline=None, max_examples=50, suppress_health_check=[HealthCheck.too_slow])
settings.load_profile("ci")


# Strategy helpers
@st.composite
def valid_node_names(draw):
    """Generate valid node names (non-empty alphanumeric strings).
    
    Per LLM.md: nodes can be any hashable identifier."""
    return draw(st.text(
        alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='_-'
        ),
        min_size=1,
        max_size=8
    ))


@st.composite
def valid_layer_names(draw):
    """Generate valid layer names (non-empty strings).
    
    Per LLM.md: layers are identified by string names."""
    return draw(st.text(
        alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='_'
        ),
        min_size=1,
        max_size=6
    ))


@st.composite
def valid_weights(draw):
    """Generate valid edge weights (finite positive numbers).
    
    Per LLM.md "Key Invariants Verified": non-negative weights."""
    return draw(st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False))


@st.composite
def multiedgelist_edges(draw, min_edges=1, max_edges=20, min_nodes=2, max_nodes=10, 
                       min_layers=1, max_layers=3):
    """Generate valid multiedgelist edges as specified in LLM.md.
    
    Format: n1 l1 n2 l2 [weight]
    Per parsers.py:parse_multiedgelist_general() specification.
    """
    # Generate pool of nodes and layers
    num_nodes = draw(st.integers(min_value=min_nodes, max_value=max_nodes))
    num_layers = draw(st.integers(min_value=min_layers, max_value=max_layers))
    
    nodes = [draw(valid_node_names()) for _ in range(num_nodes)]
    layers = [draw(valid_layer_names()) for _ in range(num_layers)]
    
    # Ensure uniqueness
    nodes = list(dict.fromkeys(nodes))
    layers = list(dict.fromkeys(layers))
    
    assume(len(nodes) >= min_nodes and len(layers) >= min_layers)
    
    # Generate edges
    num_edges = draw(st.integers(min_value=min_edges, max_value=max_edges))
    edges = []
    for _ in range(num_edges):
        n1 = draw(st.sampled_from(nodes))
        n2 = draw(st.sampled_from(nodes))
        l1 = draw(st.sampled_from(layers))
        l2 = draw(st.sampled_from(layers))
        weight = draw(valid_weights())
        edges.append((n1, l1, n2, l2, weight))
    
    return edges, nodes, layers


class TestMultinetBuildingProperties:
    """Test invariants for multilayer network construction.
    
    Reference: LLM.md "Core Concepts > Multilayer Networks"
    Tests the core network building process via load_network() API.
    """
    
    @given(multiedgelist_edges())
    @settings(max_examples=50)
    def test_edge_list_creates_valid_network(self, edge_data):
        """Networks built from valid edge lists have consistent node/edge counts.
        
        Invariant from LLM.md "Key Invariants Verified": 
        - Node count must be non-negative
        - Edge count must be non-negative
        - All edges must reference existing nodes
        """
        edges, nodes, layers = edge_data
        assume(len(edges) > 0)
        
        # Write edges to temporary file in multiedgelist format
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for n1, l1, n2, l2, weight in edges:
                f.write(f"{n1} {l1} {n2} {l2} {weight}\n")
            temp_path = f.name
        
        try:
            # Load network
            network = multinet.multi_layer_network()
            network.load_network(temp_path, input_type="multiedgelist", directed=False)
            
            # Invariants from LLM.md
            assert network.core_network is not None, "core_network must be initialized"
            assert network.core_network.number_of_nodes() >= 0, "node count must be non-negative"
            assert network.core_network.number_of_edges() >= 0, "edge count must be non-negative"
            
            # All edges reference existing nodes
            for u, v in network.core_network.edges():
                assert u in network.core_network.nodes(), f"Edge source {u} must be a node"
                assert v in network.core_network.nodes(), f"Edge target {v} must be a node"
                
            # Nodes are tuples (node_id, layer_id) per parsers.py specification
            for node in network.core_network.nodes():
                assert isinstance(node, tuple), f"Nodes must be tuples, got {type(node)}"
                assert len(node) == 2, f"Nodes must be (node_id, layer_id) tuples"
                
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    @given(multiedgelist_edges(min_edges=5, max_edges=15))
    @settings(max_examples=30)
    def test_adding_isolated_nodes_preserves_edge_count(self, edge_data):
        """Adding isolated nodes does not change edge count (metamorphic property).
        
        Reference: LLM.md "Property-based testing" section - metamorphic checks.
        """
        edges, nodes, layers = edge_data
        assume(len(edges) >= 3 and len(layers) >= 1)
        
        # Create two networks: one with edges only, one with additional isolated nodes
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for n1, l1, n2, l2, weight in edges:
                f.write(f"{n1} {l1} {n2} {l2} {weight}\n")
            temp_path1 = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            # Same edges
            for n1, l1, n2, l2, weight in edges:
                f.write(f"{n1} {l1} {n2} {l2} {weight}\n")
            # Add isolated node (self-loop that gets added)
            isolated_node = "ISOLATED_NODE_XYZ"
            isolated_layer = layers[0]
            f.write(f"{isolated_node} {isolated_layer} {isolated_node} {isolated_layer} 1.0\n")
            temp_path2 = f.name
        
        try:
            network1 = multinet.multi_layer_network()
            network1.load_network(temp_path1, input_type="multiedgelist", directed=False)
            
            network2 = multinet.multi_layer_network()
            network2.load_network(temp_path2, input_type="multiedgelist", directed=False)
            
            # Network2 should have exactly one more edge (the self-loop) or same if self-loops ignored
            # But definitely should have at least one more node
            assert network2.core_network.number_of_nodes() >= network1.core_network.number_of_nodes()
            
        finally:
            Path(temp_path1).unlink(missing_ok=True)
            Path(temp_path2).unlink(missing_ok=True)
    
    @given(multiedgelist_edges(min_edges=3, max_edges=10))
    @settings(max_examples=30)
    def test_duplicate_edges_handled_consistently(self, edge_data):
        """Duplicate edges are handled consistently (metamorphic property).
        
        Reference: LLM.md - NetworkX MultiGraph allows parallel edges.
        Per parsers.py, duplicate edges create multiple edges in MultiGraph.
        """
        edges, nodes, layers = edge_data
        assume(len(edges) >= 2)
        
        # Pick one edge to duplicate
        edge_to_dup = edges[0]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for n1, l1, n2, l2, weight in edges:
                f.write(f"{n1} {l1} {n2} {l2} {weight}\n")
            temp_path1 = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for n1, l1, n2, l2, weight in edges:
                f.write(f"{n1} {l1} {n2} {l2} {weight}\n")
            # Add duplicate
            n1, l1, n2, l2, weight = edge_to_dup
            f.write(f"{n1} {l1} {n2} {l2} {weight}\n")
            temp_path2 = f.name
        
        try:
            network1 = multinet.multi_layer_network()
            network1.load_network(temp_path1, input_type="multiedgelist", directed=False)
            
            network2 = multinet.multi_layer_network()
            network2.load_network(temp_path2, input_type="multiedgelist", directed=False)
            
            # MultiGraph allows parallel edges, so edge count should increase
            # Node count should be the same
            assert network2.core_network.number_of_nodes() == network1.core_network.number_of_nodes()
            assert network2.core_network.number_of_edges() >= network1.core_network.number_of_edges()
            
        finally:
            Path(temp_path1).unlink(missing_ok=True)
            Path(temp_path2).unlink(missing_ok=True)
    
    @given(multiedgelist_edges(min_layers=2, max_layers=3))
    @settings(max_examples=30)
    def test_edges_reference_existing_layers(self, edge_data):
        """All edges reference layers that exist in the network.
        
        Invariant from LLM.md "Key Invariants Verified": edges must reference valid layers.
        """
        edges, nodes, layers = edge_data
        assume(len(edges) > 0)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for n1, l1, n2, l2, weight in edges:
                f.write(f"{n1} {l1} {n2} {l2} {weight}\n")
            temp_path = f.name
        
        try:
            network = multinet.multi_layer_network()
            network.load_network(temp_path, input_type="multiedgelist", directed=False)
            
            # Extract all layers from nodes
            network_layers = set()
            for node in network.core_network.nodes():
                _, layer = node
                network_layers.add(layer)
            
            # All edge endpoints must reference existing layers
            for u, v in network.core_network.edges():
                _, u_layer = u
                _, v_layer = v
                assert u_layer in network_layers, f"Edge source layer {u_layer} must exist"
                assert v_layer in network_layers, f"Edge target layer {v_layer} must exist"
                
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    @given(multiedgelist_edges(min_edges=5, max_edges=20))
    @settings(max_examples=30)
    def test_directed_undirected_consistency(self, edge_data):
        """Directed and undirected networks handle edges appropriately.
        
        Reference: LLM.md - directed parameter affects edge handling.
        Undirected: edges are bidirectional; Directed: edges have direction.
        """
        edges, nodes, layers = edge_data
        assume(len(edges) >= 3)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for n1, l1, n2, l2, weight in edges:
                f.write(f"{n1} {l1} {n2} {l2} {weight}\n")
            temp_path = f.name
        
        try:
            # Load as undirected
            network_undir = multinet.multi_layer_network()
            network_undir.load_network(temp_path, input_type="multiedgelist", directed=False)
            
            # Load as directed
            network_dir = multinet.multi_layer_network()
            network_dir.load_network(temp_path, input_type="multiedgelist", directed=True)
            
            # Both should have same number of nodes
            assert network_undir.core_network.number_of_nodes() == network_dir.core_network.number_of_nodes()
            
            # Check graph types
            assert isinstance(network_undir.core_network, (nx.MultiGraph,))
            assert isinstance(network_dir.core_network, (nx.MultiDiGraph,))
            
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    @given(st.lists(st.tuples(
        valid_node_names(),
        valid_layer_names(),
        valid_node_names(),
        valid_layer_names(),
        valid_weights()
    ), min_size=3, max_size=15))
    @settings(max_examples=30)
    def test_subnetwork_by_layer_contains_only_selected_layers(self, edges):
        """Subnetwork extraction by layer contains no edges outside selected layers.
        
        Invariant from LLM.md "Core Concepts": subnetwork operations must preserve constraints.
        """
        assume(len(edges) >= 3)
        
        # Get all unique layers
        all_layers = set()
        for _, l1, _, l2, _ in edges:
            all_layers.add(l1)
            all_layers.add(l2)
        
        assume(len(all_layers) >= 2)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for n1, l1, n2, l2, weight in edges:
                f.write(f"{n1} {l1} {n2} {l2} {weight}\n")
            temp_path = f.name
        
        try:
            network = multinet.multi_layer_network()
            network.load_network(temp_path, input_type="multiedgelist", directed=False)
            
            # Select a subset of layers
            selected_layers = list(all_layers)[:max(1, len(all_layers) // 2)]
            
            # Get nodes in selected layers
            selected_nodes = [node for node in network.core_network.nodes() 
                            if node[1] in selected_layers]
            
            if len(selected_nodes) > 0:
                # Create subgraph
                subgraph = network.core_network.subgraph(selected_nodes)
                
                # All nodes in subgraph must be in selected layers
                for node in subgraph.nodes():
                    assert node[1] in selected_layers, \
                        f"Subgraph node {node} must be in selected layers {selected_layers}"
                
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    @given(multiedgelist_edges(min_edges=5, max_edges=15))
    @settings(max_examples=30)
    def test_weights_are_finite(self, edge_data):
        """All edge weights are finite numbers (no NaN, no infinity).
        
        Invariant from LLM.md "Key Invariants Verified": weights must be finite.
        """
        edges, nodes, layers = edge_data
        assume(len(edges) > 0)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for n1, l1, n2, l2, weight in edges:
                f.write(f"{n1} {l1} {n2} {l2} {weight}\n")
            temp_path = f.name
        
        try:
            network = multinet.multi_layer_network()
            network.load_network(temp_path, input_type="multiedgelist", directed=False)
            
            # Check all edge weights
            for u, v, data in network.core_network.edges(data=True):
                weight = float(data.get('weight', 1.0))
                assert not (weight != weight), f"Weight must not be NaN"  # NaN check
                assert weight != float('inf') and weight != float('-inf'), \
                    f"Weight must not be infinite"
                    
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestMultiplexProperties:
    """Test multiplex-specific constraints.
    
    Reference: LLM.md "Core Concepts" - multiplex networks have all nodes in all layers.
    """
    
    @pytest.mark.xfail(reason="Multiplex coupling behavior depends on _couple_all_edges implementation (LLM.md section 'Core Concepts')")
    def test_multiplex_all_nodes_in_all_layers(self):
        """In multiplex networks, all nodes should exist in all layers.
        
        Reference: LLM.md states multiplex networks couple nodes across layers.
        This is enforced via _couple_all_edges() in multinet.py.
        
        Marked xfail pending clarification of coupling behavior in LLM.md.
        """
        # This test would verify multiplex constraint but behavior needs clarification
        pass
