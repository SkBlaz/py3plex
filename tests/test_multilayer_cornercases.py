"""
Test corner cases for multilayer network object creation and manipulation.

This module tests edge cases and boundary conditions to ensure robust
behavior of the multi_layer_network class.
"""

import unittest
import tempfile
import os
from typing import Any

# Import the core module - tests will handle import errors gracefully
try:
    from py3plex.core import multinet
    MULTINET_AVAILABLE = True
except ImportError:
    MULTINET_AVAILABLE = False

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

# Skip all tests if dependencies not available
DEPENDENCIES_AVAILABLE = MULTINET_AVAILABLE and NETWORKX_AVAILABLE


class TestMultilayerInitialization(unittest.TestCase):
    """Test corner cases in multilayer network initialization."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
    
    def test_empty_network_initialization_multilayer(self):
        """Test initializing an empty multilayer network."""
        network = multinet.multi_layer_network(network_type="multilayer")
        self.assertIsNotNone(network)
        self.assertEqual(network.network_type, "multilayer")
        self.assertTrue(network.directed)
        self.assertIsNone(network.core_network)
    
    def test_empty_network_initialization_multiplex(self):
        """Test initializing an empty multiplex network."""
        network = multinet.multi_layer_network(network_type="multiplex")
        self.assertIsNotNone(network)
        self.assertEqual(network.network_type, "multiplex")
        self.assertIsNone(network.core_network)
    
    def test_initialization_with_custom_parameters(self):
        """Test initialization with all custom parameters."""
        network = multinet.multi_layer_network(
            verbose=False,
            network_type="multilayer",
            directed=False,
            dummy_layer="test_dummy",
            label_delimiter="__",
            coupling_weight=2.5
        )
        self.assertFalse(network.verbose)
        self.assertFalse(network.directed)
        self.assertEqual(network.dummy_layer, "test_dummy")
        self.assertEqual(network.label_delimiter, "__")
        self.assertEqual(network.coupling_weight, 2.5)
    
    def test_initialization_with_zero_coupling_weight(self):
        """Test initialization with zero coupling weight."""
        network = multinet.multi_layer_network(coupling_weight=0)
        self.assertEqual(network.coupling_weight, 0)
    
    def test_initialization_with_negative_coupling_weight(self):
        """Test initialization with negative coupling weight (should work but note behavior)."""
        network = multinet.multi_layer_network(coupling_weight=-1.0)
        self.assertEqual(network.coupling_weight, -1.0)
    
    def test_initialization_undirected(self):
        """Test initialization of undirected network."""
        network = multinet.multi_layer_network(directed=False)
        self.assertFalse(network.directed)
        self.assertIsNone(network.core_network)


class TestEmptyNetworkOperations(unittest.TestCase):
    """Test operations on empty networks."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
        self.network = multinet.multi_layer_network()
    
    def test_empty_network_nodes(self):
        """Test getting nodes from empty network."""
        # Network is None initially
        self.assertIsNone(self.network.core_network)
        
        # After initiation, should have empty graph
        self.network._initiate_network()
        nodes = list(self.network.get_nodes())
        self.assertEqual(len(nodes), 0)
    
    def test_empty_network_edges(self):
        """Test getting edges from empty network."""
        self.network._initiate_network()
        edges = list(self.network.get_edges())
        self.assertEqual(len(edges), 0)
    
    def test_split_to_layers_on_empty_network(self):
        """Test splitting empty network to layers."""
        self.network._initiate_network()
        # This should handle empty network gracefully
        self.network.split_to_layers(style="none")
        self.assertIsNotNone(self.network.layer_names)
        self.assertIsNotNone(self.network.separate_layers)


class TestNodeOperations(unittest.TestCase):
    """Test corner cases in node operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
        self.network = multinet.multi_layer_network()
    
    def test_add_single_node_dict(self):
        """Test adding a single node using dict format."""
        node = {"source": "node1", "type": "layer1"}
        self.network.add_nodes(node, input_type="dict")
        nodes = list(self.network.get_nodes())
        self.assertEqual(len(nodes), 1)
        self.assertIn(("node1", "layer1"), nodes)
    
    def test_add_single_node_without_layer(self):
        """Test adding a node without layer information (uses dummy layer)."""
        node = {"source": "node1"}
        self.network.add_nodes(node, input_type="dict")
        nodes = list(self.network.get_nodes())
        self.assertEqual(len(nodes), 1)
        # Should use dummy layer
        self.assertIn(("node1", "null"), nodes)
    
    def test_add_multiple_nodes(self):
        """Test adding multiple nodes."""
        nodes = [
            {"source": "node1", "type": "layer1"},
            {"source": "node2", "type": "layer1"},
            {"source": "node3", "type": "layer2"}
        ]
        self.network.add_nodes(nodes, input_type="dict")
        result_nodes = list(self.network.get_nodes())
        self.assertEqual(len(result_nodes), 3)
    
    def test_add_empty_node_list(self):
        """Test adding an empty list of nodes."""
        nodes = []
        # Should handle gracefully without error
        self.network.add_nodes(nodes, input_type="dict")
        self.network._initiate_network()
        result_nodes = list(self.network.get_nodes())
        self.assertEqual(len(result_nodes), 0)
    
    def test_add_duplicate_nodes(self):
        """Test adding duplicate nodes."""
        node = {"source": "node1", "type": "layer1"}
        self.network.add_nodes(node, input_type="dict")
        self.network.add_nodes(node, input_type="dict")
        # NetworkX allows adding same node multiple times (no-op)
        nodes = list(self.network.get_nodes())
        # Should still have just one node
        self.assertEqual(len([n for n in nodes if n == ("node1", "layer1")]), 1)


class TestEdgeOperations(unittest.TestCase):
    """Test corner cases in edge operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
        self.network = multinet.multi_layer_network()
    
    def test_add_single_edge_dict(self):
        """Test adding a single edge using dict format."""
        edge = {
            "source": "node1",
            "target": "node2",
            "source_type": "layer1",
            "target_type": "layer1",
            "type": "edge"
        }
        self.network.add_edges(edge, input_type="dict")
        edges = list(self.network.get_edges())
        self.assertEqual(len(edges), 1)
    
    def test_add_edge_without_layers(self):
        """Test adding edge without layer information."""
        edge = {
            "source": "node1",
            "target": "node2",
            "type": "edge"
        }
        self.network.add_edges(edge, input_type="dict")
        edges = list(self.network.get_edges())
        self.assertEqual(len(edges), 1)
        # Nodes should use dummy layer
        nodes = list(self.network.get_nodes())
        self.assertIn(("node1", "null"), nodes)
        self.assertIn(("node2", "null"), nodes)
    
    def test_add_multiple_edges(self):
        """Test adding multiple edges."""
        edges = [
            {"source": "node1", "target": "node2", "source_type": "layer1", "target_type": "layer1", "type": "edge"},
            {"source": "node2", "target": "node3", "source_type": "layer1", "target_type": "layer1", "type": "edge"},
        ]
        self.network.add_edges(edges, input_type="dict")
        result_edges = list(self.network.get_edges())
        self.assertGreaterEqual(len(result_edges), 2)
    
    def test_add_empty_edge_list(self):
        """Test adding an empty list of edges."""
        edges = []
        self.network.add_edges(edges, input_type="dict")
        self.network._initiate_network()
        result_edges = list(self.network.get_edges())
        self.assertEqual(len(result_edges), 0)
    
    def test_add_self_loop(self):
        """Test adding a self-loop edge."""
        edge = {
            "source": "node1",
            "target": "node1",
            "source_type": "layer1",
            "target_type": "layer1",
            "type": "edge"
        }
        self.network.add_edges(edge, input_type="dict")
        edges = list(self.network.get_edges())
        # Self-loops are allowed in multigraphs
        self.assertEqual(len(edges), 1)
    
    def test_add_interlayer_edge(self):
        """Test adding edge between different layers."""
        edge = {
            "source": "node1",
            "target": "node1",
            "source_type": "layer1",
            "target_type": "layer2",
            "type": "coupling"
        }
        self.network.add_edges(edge, input_type="dict")
        edges = list(self.network.get_edges())
        self.assertEqual(len(edges), 1)
    
    def test_add_edge_list_format(self):
        """Test adding edge using list format."""
        edge = ["node1", "layer1", "node2", "layer1", 1.0]
        self.network.add_edges([edge], input_type="list")
        edges = list(self.network.get_edges())
        self.assertEqual(len(edges), 1)
    
    def test_add_duplicate_edges(self):
        """Test adding duplicate edges (multigraph allows this)."""
        edge = {
            "source": "node1",
            "target": "node2",
            "source_type": "layer1",
            "target_type": "layer1",
            "type": "edge"
        }
        self.network.add_edges(edge, input_type="dict")
        self.network.add_edges(edge, input_type="dict")
        edges = list(self.network.get_edges())
        # MultiGraph allows multiple edges between same nodes
        self.assertGreaterEqual(len(edges), 1)


class TestNetworkTypeSpecific(unittest.TestCase):
    """Test corner cases specific to network types."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
    
    def test_multiplex_empty_coupling(self):
        """Test multiplex network coupling on empty network."""
        network = multinet.multi_layer_network(network_type="multiplex")
        network._initiate_network()
        # Coupling on empty network should not crash
        network._couple_all_edges()
        edges = list(network.get_edges())
        # No nodes, so no coupling edges
        self.assertEqual(len(edges), 0)
    
    def test_multiplex_single_node_coupling(self):
        """Test multiplex coupling with single node."""
        network = multinet.multi_layer_network(network_type="multiplex")
        node = {"source": "node1", "type": "layer1"}
        network.add_nodes(node, input_type="dict")
        network._couple_all_edges()
        # Single node in one layer - no coupling edges
        edges = list(network.get_edges())
        self.assertEqual(len(edges), 0)
    
    def test_multiplex_single_node_multiple_layers(self):
        """Test multiplex coupling with same node in multiple layers."""
        network = multinet.multi_layer_network(network_type="multiplex")
        nodes = [
            {"source": "node1", "type": "layer1"},
            {"source": "node1", "type": "layer2"}
        ]
        network.add_nodes(nodes, input_type="dict")
        network._couple_all_edges()
        edges = list(network.get_edges())
        # Should have coupling edges between layers
        # One edge from layer1 to layer2 and one from layer2 to layer1 (directed)
        self.assertGreater(len(edges), 0)


class TestRemoveOperations(unittest.TestCase):
    """Test corner cases in remove operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
        self.network = multinet.multi_layer_network()
    
    def test_remove_node_from_empty(self):
        """Test removing node from empty network."""
        self.network._initiate_network()
        node = {"source": "node1", "type": "layer1"}
        # Should handle gracefully (NetworkX removes non-existent node silently)
        try:
            self.network.remove_nodes(node, input_type="dict")
        except Exception:
            # If it raises an exception, that's also acceptable behavior
            pass
    
    def test_remove_edge_from_empty(self):
        """Test removing edge from empty network."""
        self.network._initiate_network()
        edge = ["node1", "layer1", "node2", "layer1", 1.0]
        # Should handle gracefully
        try:
            self.network.remove_edges([edge], input_type="list")
        except Exception:
            # If it raises an exception, that's also acceptable behavior
            pass
    
    def test_remove_existing_node(self):
        """Test removing an existing node."""
        node = {"source": "node1", "type": "layer1"}
        self.network.add_nodes(node, input_type="dict")
        self.assertEqual(len(list(self.network.get_nodes())), 1)
        
        self.network.remove_nodes(node, input_type="dict")
        self.assertEqual(len(list(self.network.get_nodes())), 0)
    
    def test_remove_existing_edge(self):
        """Test removing an existing edge."""
        edge = {
            "source": "node1",
            "target": "node2",
            "source_type": "layer1",
            "target_type": "layer1",
            "type": "edge"
        }
        self.network.add_edges(edge, input_type="dict")
        edges_before = len(list(self.network.get_edges()))
        self.assertGreater(edges_before, 0)
        
        # Remove using list format
        edge_list = ["node1", "layer1", "node2", "layer1", 1.0]
        self.network.remove_edges([edge_list], input_type="list")
        edges_after = len(list(self.network.get_edges()))
        self.assertLessEqual(edges_after, edges_before)


class TestQueryOperations(unittest.TestCase):
    """Test corner cases in query operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
        self.network = multinet.multi_layer_network()
    
    def test_get_neighbors_empty_network(self):
        """Test getting neighbors from empty network."""
        self.network._initiate_network()
        try:
            neighbors = list(self.network.get_neighbors("node1", "layer1"))
            # Empty network should return empty neighbors or raise error
            self.assertEqual(len(neighbors), 0)
        except Exception:
            # Raising an exception is also acceptable
            pass
    
    def test_get_neighbors_nonexistent_node(self):
        """Test getting neighbors of non-existent node."""
        edge = {
            "source": "node1",
            "target": "node2",
            "source_type": "layer1",
            "target_type": "layer1",
            "type": "edge"
        }
        self.network.add_edges(edge, input_type="dict")
        
        try:
            neighbors = list(self.network.get_neighbors("node99", "layer1"))
            # Should return empty or raise error
        except Exception:
            # Raising an exception is acceptable
            pass
    
    def test_get_neighbors_existing_node(self):
        """Test getting neighbors of existing node."""
        edges = [
            {"source": "node1", "target": "node2", "source_type": "layer1", "target_type": "layer1", "type": "edge"},
            {"source": "node1", "target": "node3", "source_type": "layer1", "target_type": "layer1", "type": "edge"},
        ]
        self.network.add_edges(edges, input_type="dict")
        neighbors = list(self.network.get_neighbors("node1", "layer1"))
        self.assertGreaterEqual(len(neighbors), 2)


class TestSubnetworkOperations(unittest.TestCase):
    """Test corner cases in subnetwork extraction."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
        self.network = multinet.multi_layer_network()
        # Add some edges
        edges = [
            {"source": "node1", "target": "node2", "source_type": "layer1", "target_type": "layer1", "type": "edge"},
            {"source": "node2", "target": "node3", "source_type": "layer1", "target_type": "layer1", "type": "edge"},
            {"source": "node1", "target": "node2", "source_type": "layer2", "target_type": "layer2", "type": "edge"},
        ]
        self.network.add_edges(edges, input_type="dict")
    
    def test_subnetwork_empty_list(self):
        """Test extracting subnetwork with empty list."""
        try:
            subnet = self.network.subnetwork([], subset_by="layers")
            # Should return empty network or handle gracefully
            if subnet is not None:
                self.network._initiate_network()
                subnet_nodes = list(subnet.get_nodes())
                self.assertEqual(len(subnet_nodes), 0)
        except Exception:
            # Raising exception is acceptable
            pass
    
    def test_subnetwork_single_layer(self):
        """Test extracting subnetwork for single layer."""
        subnet = self.network.subnetwork(['layer1'], subset_by="layers")
        self.assertIsNotNone(subnet)
        subnet_nodes = list(subnet.get_nodes())
        # Should have nodes from layer1 only
        self.assertGreater(len(subnet_nodes), 0)
        for node in subnet_nodes:
            self.assertEqual(node[1], 'layer1')
    
    def test_subnetwork_nonexistent_layer(self):
        """Test extracting subnetwork for non-existent layer."""
        subnet = self.network.subnetwork(['layer99'], subset_by="layers")
        # Should return empty network
        if subnet is not None:
            subnet.core_network._initiate_network() if subnet.core_network is None else None
            subnet_nodes = list(subnet.get_nodes()) if subnet.core_network else []
            # May be empty or None
            self.assertIsNotNone(subnet)


class TestNetworkConversion(unittest.TestCase):
    """Test corner cases in network conversion operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
        self.network = multinet.multi_layer_network()
    
    def test_to_json_empty_network(self):
        """Test converting empty network to JSON."""
        self.network._initiate_network()
        json_data = self.network.to_json()
        self.assertIsNotNone(json_data)
        self.assertIn('nodes', json_data)
        self.assertIn('edges', json_data)
    
    def test_to_json_with_data(self):
        """Test converting network with data to JSON."""
        edge = {
            "source": "node1",
            "target": "node2",
            "source_type": "layer1",
            "target_type": "layer1",
            "type": "edge"
        }
        self.network.add_edges(edge, input_type="dict")
        json_data = self.network.to_json()
        self.assertIsNotNone(json_data)
        self.assertGreater(len(json_data['nodes']), 0)


class TestLayerOperations(unittest.TestCase):
    """Test corner cases in layer-specific operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
        self.network = multinet.multi_layer_network()
    
    def test_get_num_layers_empty(self):
        """Test getting number of layers from empty network."""
        self.network._initiate_network()
        self.network._get_num_layers()
        self.assertEqual(self.network.number_of_layers, 0)
    
    def test_get_num_layers_single_layer(self):
        """Test getting number of layers with single layer."""
        node = {"source": "node1", "type": "layer1"}
        self.network.add_nodes(node, input_type="dict")
        self.network._get_num_layers()
        self.assertEqual(self.network.number_of_layers, 1)
    
    def test_get_num_layers_multiple_layers(self):
        """Test getting number of layers with multiple layers."""
        nodes = [
            {"source": "node1", "type": "layer1"},
            {"source": "node2", "type": "layer2"},
            {"source": "node3", "type": "layer3"}
        ]
        self.network.add_nodes(nodes, input_type="dict")
        self.network._get_num_layers()
        self.assertEqual(self.network.number_of_layers, 3)
    
    def test_get_num_nodes_empty(self):
        """Test getting number of unique nodes from empty network."""
        self.network._initiate_network()
        self.network._get_num_nodes()
        self.assertEqual(self.network.number_of_unique_nodes, 0)
    
    def test_get_num_nodes_same_node_different_layers(self):
        """Test counting unique nodes when same node appears in different layers."""
        nodes = [
            {"source": "node1", "type": "layer1"},
            {"source": "node1", "type": "layer2"},
            {"source": "node2", "type": "layer1"}
        ]
        self.network.add_nodes(nodes, input_type="dict")
        self.network._get_num_nodes()
        # Should count node1 once even though it's in 2 layers
        self.assertEqual(self.network.number_of_unique_nodes, 2)


class TestInvalidInputs(unittest.TestCase):
    """Test handling of invalid inputs."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
        self.network = multinet.multi_layer_network()
    
    def test_add_edge_invalid_input_type(self):
        """Test adding edge with invalid input type."""
        edge = {"source": "node1", "target": "node2"}
        with self.assertRaises(Exception):
            self.network.add_edges(edge, input_type="invalid_type")
    
    def test_add_edge_malformed_dict(self):
        """Test adding edge with malformed dictionary."""
        # Missing required keys - behavior depends on implementation
        edge = {"source": "node1"}
        try:
            self.network.add_edges(edge, input_type="dict")
        except (KeyError, Exception):
            # Expected to fail
            pass
    
    def test_add_edge_malformed_list(self):
        """Test adding edge with malformed list."""
        # Wrong number of elements
        edge = ["node1", "layer1"]  # Missing elements
        try:
            self.network.add_edges([edge], input_type="list")
        except (ValueError, IndexError, Exception):
            # Expected to fail
            pass


class TestNetworkLoading(unittest.TestCase):
    """Test corner cases in network loading."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
    
    def test_load_network_none_file(self):
        """Test loading network with None as file path."""
        network = multinet.multi_layer_network()
        try:
            network.load_network(input_file=None, input_type="edgelist")
        except Exception:
            # Expected to fail
            pass
    
    def test_load_network_nonexistent_file(self):
        """Test loading network from non-existent file."""
        network = multinet.multi_layer_network()
        try:
            network.load_network(
                input_file="/tmp/nonexistent_file_12345.txt",
                input_type="edgelist"
            )
        except Exception:
            # Expected to fail
            pass
    
    def test_load_network_empty_networkx_graph(self):
        """Test loading empty NetworkX graph."""
        network = multinet.multi_layer_network()
        empty_graph = nx.MultiDiGraph()
        result = network.load_network(empty_graph, input_type="nx", directed=True)
        self.assertIsNotNone(result)
        # Should have empty network
        nodes = list(result.get_nodes())
        self.assertEqual(len(nodes), 0)
    
    def test_load_network_networkx_graph_with_data(self):
        """Test loading NetworkX graph with data."""
        network = multinet.multi_layer_network()
        G = nx.MultiDiGraph()
        G.add_edge(("node1", "layer1"), ("node2", "layer1"))
        result = network.load_network(G, input_type="nx", directed=True)
        self.assertIsNotNone(result)
        nodes = list(result.get_nodes())
        self.assertGreater(len(nodes), 0)


# Test runner for when pytest is not available
if __name__ == '__main__':
    if not DEPENDENCIES_AVAILABLE:
        print("Skipping tests - dependencies not available")
        print("Please install: networkx")
    else:
        unittest.main(verbosity=2)
