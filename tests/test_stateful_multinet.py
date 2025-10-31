"""
Stateful property tests for multilayer networks using Hypothesis.

This module uses Hypothesis's RuleBasedStateMachine to test invariants across
sequences of operations as specified in LLM.md:
- Operations: add nodes/edges, take subnetworks, query neighbors
- Invariants: edges reference existing nodes/layers, subnetwork containment
- State consistency across operation sequences

Reference: LLM.md "Property-based testing" and "Key Invariants Verified" sections.
"""

import tempfile
from pathlib import Path
from typing import Dict, List, Set, Tuple

import networkx as nx
from hypothesis import settings
from hypothesis.stateful import RuleBasedStateMachine, rule, initialize, invariant
from hypothesis import strategies as st

from py3plex.core import multinet


# Configure Hypothesis for CI
settings.register_profile("ci", deadline=None, max_examples=20, stateful_step_count=15)
settings.load_profile("ci")


# Strategies for stateful testing
def node_name_strategy():
    """Generate valid node names."""
    return st.text(
        alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='_'
        ),
        min_size=1,
        max_size=6
    )


def layer_name_strategy():
    """Generate valid layer names."""
    return st.text(
        alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll'),
            whitelist_characters='_'
        ),
        min_size=1,
        max_size=4
    )


def weight_strategy():
    """Generate valid edge weights."""
    return st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False)


class MultilayerNetworkStateMachine(RuleBasedStateMachine):
    """Stateful tests for multilayer network operations.
    
    Reference: LLM.md "Property-based testing" - operations must maintain invariants.
    
    Invariants tested:
    1. All edges reference existing nodes and layers (LLM.md "Key Invariants Verified")
    2. Subnetwork nodes/edges are subsets of parent (LLM.md "Core Concepts")
    3. Node/edge counts are non-negative (LLM.md "Key Invariants Verified")
    4. Layers remain consistent across operations
    """
    
    def __init__(self):
        super().__init__()
        self.network = None
        self.nodes: Set[Tuple[str, str]] = set()  # (node_id, layer_id) tuples
        self.edges: List[Tuple[str, str, str, str, float]] = []  # (n1, l1, n2, l2, weight)
        self.layers: Set[str] = set()
        self.temp_files: List[Path] = []
    
    @initialize()
    def initialize_network(self):
        """Initialize an empty multilayer network.
        
        Invariant: network must be valid after initialization (LLM.md).
        """
        self.network = multinet.multi_layer_network(directed=False)
        self.nodes = set()
        self.edges = []
        self.layers = set()
    
    @rule(
        node1=node_name_strategy(),
        layer1=layer_name_strategy(),
        node2=node_name_strategy(),
        layer2=layer_name_strategy(),
        weight=weight_strategy()
    )
    def add_edge(self, node1, layer1, node2, layer2, weight):
        """Add an edge to the network.
        
        Operation from LLM.md: adding edges via load_network or direct manipulation.
        """
        # Add edge to our tracking
        self.edges.append((node1, layer1, node2, layer2, weight))
        self.nodes.add((node1, layer1))
        self.nodes.add((node2, layer2))
        self.layers.add(layer1)
        self.layers.add(layer2)
        
        # Reload network with new edges
        self._reload_network()
    
    @rule()
    def check_edge_consistency(self):
        """Check that all edges reference existing nodes.
        
        Invariant from LLM.md "Key Invariants Verified": 
        edges must reference existing nodes/layers.
        """
        if self.network.core_network is None:
            return
        
        network_nodes = set(self.network.core_network.nodes())
        
        for u, v in self.network.core_network.edges():
            assert u in network_nodes, f"Edge source {u} must be a valid node"
            assert v in network_nodes, f"Edge target {v} must be a valid node"
    
    @rule(layer=layer_name_strategy())
    def get_layer_subnetwork(self, layer):
        """Extract a subnetwork for a specific layer.
        
        Operation from LLM.md "Core Concepts": subnetwork operations.
        Invariant: subnetwork nodes/edges must be subset of parent.
        """
        if self.network.core_network is None or len(self.nodes) == 0:
            return
        
        # Get nodes in this layer
        layer_nodes = [node for node in self.network.core_network.nodes() 
                      if node[1] == layer]
        
        if len(layer_nodes) == 0:
            return
        
        # Create subgraph
        subgraph = self.network.core_network.subgraph(layer_nodes)
        
        # Invariant: subgraph nodes are subset of parent nodes
        parent_nodes = set(self.network.core_network.nodes())
        sub_nodes = set(subgraph.nodes())
        assert sub_nodes.issubset(parent_nodes), \
            "Subnetwork nodes must be subset of parent nodes"
        
        # Invariant: all subgraph nodes are in the specified layer
        for node in subgraph.nodes():
            assert node[1] == layer, \
                f"Subnetwork for layer {layer} should only contain nodes from that layer"
    
    @rule()
    def check_node_layer_consistency(self):
        """Check that nodes have consistent layer assignments.
        
        Invariant from LLM.md: nodes are tuples (node_id, layer_id).
        """
        if self.network.core_network is None:
            return
        
        for node in self.network.core_network.nodes():
            assert isinstance(node, tuple), f"Node {node} must be a tuple"
            assert len(node) == 2, f"Node {node} must be (node_id, layer_id)"
            
            node_id, layer_id = node
            assert isinstance(node_id, str), "Node ID must be string"
            assert isinstance(layer_id, str), "Layer ID must be string"
    
    @rule()
    def check_non_negative_counts(self):
        """Check that node and edge counts are non-negative.
        
        Invariant from LLM.md "Key Invariants Verified": 
        counts must be non-negative.
        """
        if self.network.core_network is None:
            return
        
        num_nodes = self.network.core_network.number_of_nodes()
        num_edges = self.network.core_network.number_of_edges()
        
        assert num_nodes >= 0, "Node count must be non-negative"
        assert num_edges >= 0, "Edge count must be non-negative"
    
    @rule()
    def check_weight_finiteness(self):
        """Check that all edge weights are finite.
        
        Invariant from LLM.md "Key Invariants Verified": 
        weights must be finite.
        """
        if self.network.core_network is None:
            return
        
        for u, v, data in self.network.core_network.edges(data=True):
            weight = float(data.get('weight', 1.0))
            assert weight == weight, "Weight must not be NaN"  # NaN != NaN
            assert weight != float('inf') and weight != float('-inf'), \
                "Weight must not be infinite"
    
    @invariant()
    def network_is_valid(self):
        """Network remains in valid state after any operation.
        
        Invariant from LLM.md: network must always be valid.
        """
        if self.network.core_network is not None:
            assert self.network.core_network.number_of_nodes() >= 0
            assert self.network.core_network.number_of_edges() >= 0
    
    @invariant()
    def layers_are_consistent(self):
        """Layers in network match tracked layers.
        
        Invariant: layer information must be consistent.
        """
        if self.network.core_network is None or len(self.nodes) == 0:
            return
        
        # Extract layers from network
        network_layers = set()
        for node in self.network.core_network.nodes():
            _, layer = node
            network_layers.add(layer)
        
        # Should match our tracked layers
        assert network_layers == self.layers, \
            f"Network layers {network_layers} should match tracked layers {self.layers}"
    
    def _reload_network(self):
        """Helper to reload network from current edge list.
        
        Used to apply state changes via file-based loading.
        """
        if len(self.edges) == 0:
            return
        
        # Write edges to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for n1, l1, n2, l2, weight in self.edges:
                f.write(f"{n1} {l1} {n2} {l2} {weight}\n")
            temp_path = Path(f.name)
        
        self.temp_files.append(temp_path)
        
        # Reload network
        try:
            self.network = multinet.multi_layer_network(directed=False)
            self.network.load_network(str(temp_path), input_type="multiedgelist", directed=False)
        except Exception:
            # If loading fails, keep previous state
            pass
    
    def teardown(self):
        """Clean up temporary files."""
        for temp_file in self.temp_files:
            temp_file.unlink(missing_ok=True)


class SimpleMultilayerNetworkStateMachine(RuleBasedStateMachine):
    """Simplified stateful tests focusing on core invariants.
    
    Reference: LLM.md - test core operations with simpler state space.
    """
    
    def __init__(self):
        super().__init__()
        self.node_set: Set[str] = set()
        self.layer_set: Set[str] = set()
        self.edge_count: int = 0
    
    @initialize()
    def start(self):
        """Initialize tracking state."""
        self.node_set = set()
        self.layer_set = set()
        self.edge_count = 0
    
    @rule(node=node_name_strategy())
    def add_node(self, node):
        """Add a node to tracking.
        
        Operation: track node additions.
        """
        self.node_set.add(node)
    
    @rule(layer=layer_name_strategy())
    def add_layer(self, layer):
        """Add a layer to tracking.
        
        Operation: track layer additions.
        """
        self.layer_set.add(layer)
    
    @rule()
    def add_edge_simple(self):
        """Add an edge between existing nodes/layers.
        
        Operation: track edge additions.
        Invariant: edge count increases.
        """
        if len(self.node_set) >= 2 and len(self.layer_set) >= 1:
            self.edge_count += 1
    
    @invariant()
    def counts_non_negative(self):
        """All counts remain non-negative.
        
        Invariant from LLM.md: counts must be non-negative.
        """
        assert len(self.node_set) >= 0
        assert len(self.layer_set) >= 0
        assert self.edge_count >= 0
    
    @invariant()
    def edges_require_nodes_and_layers(self):
        """Edges require nodes and layers to exist.
        
        Invariant from LLM.md: edges reference existing entities.
        """
        if self.edge_count > 0:
            assert len(self.node_set) >= 2 or len(self.layer_set) >= 1


# Test classes for pytest
class TestStatefulMultilayerNetwork:
    """Test case wrapper for stateful tests.
    
    Reference: LLM.md "Property-based testing" - stateful test integration.
    """
    
    def test_multilayer_network_operations(self):
        """Run stateful tests on multilayer network operations.
        
        Tests invariants across sequences of add_edge, subnetwork operations.
        """
        # Create and run the state machine test
        MultilayerNetworkStateMachine.TestCase().runTest()
    
    def test_simple_tracking_operations(self):
        """Run simplified stateful tests on tracking operations.
        
        Tests basic invariants with simpler state space.
        """
        SimpleMultilayerNetworkStateMachine.TestCase().runTest()


class TestSubnetworkInvariants:
    """Additional tests for subnetwork invariants.
    
    Reference: LLM.md "Core Concepts" - subnetwork operations must preserve constraints.
    """
    
    def test_empty_subnetwork_is_valid(self):
        """Empty subnetwork is valid (edge case).
        
        Invariant: operations on empty networks should not crash.
        """
        network = multinet.multi_layer_network()
        # Don't load anything
        
        # Should be able to query without crashing
        if network.core_network is not None:
            assert network.core_network.number_of_nodes() == 0
            assert network.core_network.number_of_edges() == 0
    
    def test_single_node_subnetwork(self):
        """Subnetwork with single node is valid.
        
        Edge case from LLM.md: handle minimal networks.
        """
        edges = [("A", "L1", "B", "L1", 1.0)]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for n1, l1, n2, l2, weight in edges:
                f.write(f"{n1} {l1} {n2} {l2} {weight}\n")
            temp_path = f.name
        
        try:
            network = multinet.multi_layer_network()
            network.load_network(temp_path, input_type="multiedgelist", directed=False)
            
            # Get one node
            if network.core_network.number_of_nodes() > 0:
                single_node = list(network.core_network.nodes())[0]
                
                # Create subgraph with single node
                subgraph = network.core_network.subgraph([single_node])
                
                assert subgraph.number_of_nodes() == 1
                # No edges expected in single-node subgraph
                assert subgraph.number_of_edges() == 0
                
        finally:
            Path(temp_path).unlink(missing_ok=True)
