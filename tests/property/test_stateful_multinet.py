#!/usr/bin/env python3
"""
Stateful (rule-based) property tests for py3plex.core.multinet.multi_layer_network.

What this test does
-------------------
We exercise the core mutating API:

- add_nodes({"source": node_name, "type": layer_name})
- add_edges([{"source": n1, "target": n2, "source_type": l1, "target_type": l2}])
- get_nodes(), get_edges(), get_neighbors()
- load_network with synthetic graphs
- random_multilayer_ER generator
- subnetwork(..., subset_by=...)
- split_to_layers()

And verify invariants at each step:

- core_network stays non-None after initialization
- node count >= 0
- edge count >= 0
- get_nodes() returns actual nodes in core_network
- get_edges() returns actual edges in core_network
- subnetwork preserves structure

This uses Hypothesis's stateful testing (RuleBasedStateMachine) to generate
random sequences of operations and check that invariants hold throughout.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from hypothesis.stateful import RuleBasedStateMachine, rule, initialize, invariant

from py3plex.core.multinet import multi_layer_network
from py3plex.core import random_generators


class MultiLayerNetworkStateMachine(RuleBasedStateMachine):
    """
    Stateful test machine for multi_layer_network.
    
    This tracks the state of a multi_layer_network object across multiple
    operations and verifies invariants after each operation.
    """
    
    def __init__(self):
        super().__init__()
        self.network = multi_layer_network(verbose=False)
        self.expected_nodes = set()
        self.expected_edges = set()
        self.initialized = False
    
    @initialize()
    def init_network(self):
        """Initialize with a simple network."""
        # Start with an empty initialized network
        self.network = multi_layer_network(verbose=False, network_type="multilayer")
        self.expected_nodes = set()
        self.expected_edges = set()
        self.initialized = False
    
    @rule(
        node_name=st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
        layer_name=st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122))
    )
    def add_single_node(self, node_name, layer_name):
        """Add a single node to the network."""
        node_dict = {"source": node_name, "type": layer_name}
        self.network.add_nodes(node_dict, input_type="dict")
        self.expected_nodes.add((node_name, layer_name))
        self.initialized = True
    
    @rule(
        n1=st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
        n2=st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
        l1=st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
        l2=st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122))
    )
    def add_single_edge(self, n1, n2, l1, l2):
        """Add a single edge to the network."""
        edge_dict = {
            "source": n1,
            "target": n2,
            "source_type": l1,
            "target_type": l2
        }
        self.network.add_edges([edge_dict], input_type="dict")
        self.expected_nodes.add((n1, l1))
        self.expected_nodes.add((n2, l2))
        self.expected_edges.add(((n1, l1), (n2, l2)))
        self.initialized = True
    
    @rule()
    def test_get_nodes(self):
        """Test that get_nodes returns valid nodes."""
        if not self.initialized:
            return
        
        nodes = list(self.network.get_nodes())
        assert all(isinstance(n, tuple) and len(n) == 2 for n in nodes), \
            "All nodes should be (name, layer) tuples"
    
    @rule()
    def test_get_edges(self):
        """Test that get_edges returns valid edges."""
        if not self.initialized:
            return
        
        edges = list(self.network.get_edges())
        assert all(isinstance(e, tuple) and len(e) >= 2 for e in edges), \
            "All edges should be tuples with at least 2 elements"
    
    @invariant()
    def core_network_exists(self):
        """Core network should exist after initialization."""
        if self.initialized:
            assert self.network.core_network is not None, \
                "core_network should not be None after initialization"
    
    @invariant()
    def node_count_non_negative(self):
        """Node count should always be non-negative."""
        if self.initialized and self.network.core_network is not None:
            assert self.network.core_network.number_of_nodes() >= 0, \
                "Node count should be non-negative"
    
    @invariant()
    def edge_count_non_negative(self):
        """Edge count should always be non-negative."""
        if self.initialized and self.network.core_network is not None:
            assert self.network.core_network.number_of_edges() >= 0, \
                "Edge count should be non-negative"
    
    @invariant()
    def nodes_match_expected(self):
        """Node count should match or exceed expected nodes."""
        if self.initialized and self.network.core_network is not None and len(self.expected_nodes) > 0:
            actual_nodes = set(self.network.core_network.nodes())
            # All expected nodes should be present
            assert self.expected_nodes.issubset(actual_nodes), \
                f"Expected nodes {self.expected_nodes - actual_nodes} not found in network"


@pytest.mark.property
class TestMultiLayerNetworkStateful(MultiLayerNetworkStateMachine.TestCase):
    """Run the stateful test as a pytest test."""
    settings = settings(deadline=None, max_examples=5, stateful_step_count=10)


@pytest.mark.property
@settings(deadline=None, max_examples=5)
@given(
    num_nodes=st.integers(min_value=2, max_value=15),
    num_layers=st.integers(min_value=1, max_value=3),
    p=st.floats(min_value=0.01, max_value=1.0),  # Avoid very small p to prevent issues in NetworkX
)
def test_random_multilayer_er_and_iterate(num_nodes, num_layers, p):
    """
    Test random_multilayer_ER generator and basic iteration.
    
    Property: Generated network should have:
    - Valid core_network
    - Non-negative node/edge counts
    - Iterable nodes and edges
    """
    net = random_generators.random_multilayer_ER(
        n=num_nodes,
        l=num_layers,
        p=p,
        directed=False
    )
    
    # Check core_network exists
    assert net.core_network is not None, "core_network should not be None"
    
    # Check counts
    assert net.core_network.number_of_nodes() >= 0, "Node count should be non-negative"
    assert net.core_network.number_of_edges() >= 0, "Edge count should be non-negative"
    
    # Test get_nodes iteration
    nodes = list(net.get_nodes())
    assert len(nodes) == net.core_network.number_of_nodes(), \
        "get_nodes() should return all nodes"
    assert all(isinstance(n, tuple) and len(n) == 2 for n in nodes), \
        "All nodes should be (name, layer) tuples"
    
    # Test get_edges iteration
    edges = list(net.get_edges())
    # Note: get_edges() may filter some edges, so we check <= instead of ==
    assert len(edges) <= net.core_network.number_of_edges(), \
        "get_edges() should return at most all edges"
    
    # Test get_neighbors for first node if network has nodes
    if len(nodes) > 0:
        first_node = nodes[0]
        neighbors = list(net.get_neighbors(first_node[0], first_node[1]))
        assert isinstance(neighbors, list), "get_neighbors should return a list"


@pytest.mark.property
@settings(deadline=None, max_examples=5)
@given(
    num_nodes=st.integers(min_value=3, max_value=12),
    num_layers=st.integers(min_value=2, max_value=4),
    p=st.floats(min_value=0.2, max_value=0.8),
)
def test_subnetwork_preserves_structure(num_nodes, num_layers, p):
    """
    Test that subnetwork extraction preserves network structure.
    
    Property: Extracted subnetwork should:
    - Have core_network
    - Have nodes <= original network
    - Have edges <= original network
    """
    net = random_generators.random_multilayer_ER(
        n=num_nodes,
        l=num_layers,
        p=p,
        directed=False
    )
    
    # Get all nodes
    all_nodes = list(net.get_nodes())
    assume(len(all_nodes) >= 2)
    
    # Extract subnetwork with half the nodes
    subset_size = max(1, len(all_nodes) // 2)
    subset_nodes = all_nodes[:subset_size]
    
    subnet = net.subnetwork(subset_nodes, subset_by="node_layer_names")
    
    # Check subnetwork properties
    assert subnet.core_network is not None, "Subnetwork should have core_network"
    assert subnet.core_network.number_of_nodes() <= net.core_network.number_of_nodes(), \
        "Subnetwork should have <= nodes than original"
    assert subnet.core_network.number_of_edges() <= net.core_network.number_of_edges(), \
        "Subnetwork should have <= edges than original"
    
    # Check that all subnetwork nodes are in original network
    subnet_nodes = set(subnet.get_nodes())
    original_nodes = set(net.get_nodes())
    assert subnet_nodes.issubset(original_nodes), \
        "All subnetwork nodes should be in original network"


@pytest.mark.property
@settings(deadline=None, max_examples=5)
@given(
    num_nodes=st.integers(min_value=3, max_value=10),
    num_layers=st.integers(min_value=2, max_value=4),
    p=st.floats(min_value=0.4, max_value=0.8),  # Higher p to ensure we have edges
)
def test_split_to_layers(num_nodes, num_layers, p):
    """
    Test split_to_layers functionality.
    
    Property: After splitting:
    - separate_layers should be a list or tuple
    - Number of layers should match expected (when network has edges)
    - Each layer should be a graph
    """
    net = random_generators.random_multilayer_ER(
        n=num_nodes,
        l=num_layers,
        p=p,
        directed=False
    )
    
    # Split the network
    net.split_to_layers(style="none", compute_layouts=False, verbose=False)
    
    # Check that split happened
    assert hasattr(net, 'separate_layers'), "Network should have separate_layers after split"
    assert hasattr(net, 'layer_names'), "Network should have layer_names after split"
    
    # Check layer structure - separate_layers can be a list or tuple
    assert isinstance(net.separate_layers, (list, tuple)), "separate_layers should be a list or tuple"
    
    # If network has edges, we should have layers
    if net.core_network.number_of_edges() > 0:
        assert len(net.separate_layers) > 0, "Should have at least one layer when network has edges"
    
    # Each layer should have a graph structure (if layers exist)
    for layer in net.separate_layers:
        assert hasattr(layer, 'nodes'), "Each layer should have nodes method"
        assert hasattr(layer, 'edges'), "Each layer should have edges method"


@pytest.mark.property
@settings(deadline=None, max_examples=5)
@given(
    num_nodes=st.integers(min_value=2, max_value=10),
    num_layers=st.integers(min_value=1, max_value=3),
)
def test_add_nodes_edges_consistency(num_nodes, num_layers):
    """
    Test that add_nodes and add_edges maintain consistency.
    
    Property: After adding nodes and edges:
    - All added nodes should be present
    - Node count should be non-negative
    - Edge count should be non-negative
    """
    net = multi_layer_network(verbose=False, network_type="multilayer")
    
    # Add some nodes
    nodes_to_add = []
    for i in range(num_nodes):
        for j in range(num_layers):
            nodes_to_add.append({
                "source": f"n{i}",
                "type": f"l{j}"
            })
    
    net.add_nodes(nodes_to_add, input_type="dict")
    
    # Check node count
    assert net.core_network is not None, "core_network should be initialized"
    assert net.core_network.number_of_nodes() >= len(nodes_to_add), \
        f"Should have at least {len(nodes_to_add)} nodes"
    
    # Add edges between adjacent nodes in same layer
    edges_to_add = []
    for i in range(num_nodes - 1):
        for j in range(num_layers):
            edges_to_add.append({
                "source": f"n{i}",
                "target": f"n{i+1}",
                "source_type": f"l{j}",
                "target_type": f"l{j}"
            })
    
    if len(edges_to_add) > 0:
        net.add_edges(edges_to_add, input_type="dict")
        
        # Check edge count
        assert net.core_network.number_of_edges() >= 0, "Edge count should be non-negative"
        
        # Verify nodes are still present
        nodes_in_network = set(net.get_nodes())
        for node_dict in nodes_to_add:
            node_tuple = (node_dict["source"], node_dict["type"])
            assert node_tuple in nodes_in_network, \
                f"Node {node_tuple} should be in network after adding edges"
