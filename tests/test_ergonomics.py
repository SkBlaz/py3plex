"""
Tests for ergonomic improvements to the multi_layer_network class.

These tests verify Pythonic interface features:
- __len__, __bool__, __contains__, __iter__
- Property accessors (node_count, edge_count, layer_count, layers, is_empty)
- Method chaining support
- Factory methods (from_edges, from_networkx)
"""

import networkx as nx

from py3plex.core.multinet import multi_layer_network


class TestDunderMethods:
    """Test special method implementations for Pythonic interface."""

    def test_len_empty_network(self):
        """Empty network should have length 0."""
        net = multi_layer_network()
        assert len(net) == 0

    def test_len_with_nodes(self):
        """Network with nodes should report correct length."""
        net = multi_layer_network()
        net.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
            {'source': 'C', 'type': 'layer2'},
        ])
        assert len(net) == 3

    def test_bool_empty_network(self):
        """Empty network should be falsy."""
        net = multi_layer_network()
        assert not net
        assert not bool(net)

    def test_bool_nonempty_network(self):
        """Non-empty network should be truthy."""
        net = multi_layer_network()
        net.add_nodes([{'source': 'A', 'type': 'layer1'}])
        assert net
        assert bool(net)

    def test_contains_node_exists(self):
        """Node that exists should be found with 'in' operator."""
        net = multi_layer_network()
        net.add_nodes([{'source': 'A', 'type': 'layer1'}])
        assert ('A', 'layer1') in net

    def test_contains_node_not_exists(self):
        """Node that doesn't exist should not be found."""
        net = multi_layer_network()
        net.add_nodes([{'source': 'A', 'type': 'layer1'}])
        assert ('B', 'layer1') not in net
        assert ('A', 'layer2') not in net

    def test_contains_edge_exists(self):
        """Edge that exists should be found with 'in' operator."""
        net = multi_layer_network()
        net.add_edges([{
            'source': 'A', 'target': 'B',
            'source_type': 'layer1', 'target_type': 'layer1'
        }])
        assert (('A', 'layer1'), ('B', 'layer1')) in net

    def test_contains_edge_not_exists(self):
        """Edge that doesn't exist should not be found."""
        net = multi_layer_network()
        net.add_edges([{
            'source': 'A', 'target': 'B',
            'source_type': 'layer1', 'target_type': 'layer1'
        }])
        assert (('A', 'layer1'), ('C', 'layer1')) not in net

    def test_contains_empty_network(self):
        """Empty network should not contain anything."""
        net = multi_layer_network()
        assert ('A', 'layer1') not in net

    def test_iter_empty_network(self):
        """Iterating over empty network should yield nothing."""
        net = multi_layer_network()
        nodes = list(net)
        assert nodes == []

    def test_iter_with_nodes(self):
        """Iterating over network should yield all nodes."""
        net = multi_layer_network()
        net.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'}
        ])
        nodes = list(net)
        assert len(nodes) == 2
        assert ('A', 'layer1') in nodes
        assert ('B', 'layer1') in nodes

    def test_iter_for_loop(self):
        """For loop should work on network."""
        net = multi_layer_network()
        net.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'}
        ])
        count = 0
        for node in net:
            count += 1
        assert count == 2


class TestPropertyAccessors:
    """Test property-based access to network attributes."""

    def test_node_count_empty(self):
        """node_count should be 0 for empty network."""
        net = multi_layer_network()
        assert net.node_count == 0

    def test_node_count_with_nodes(self):
        """node_count should reflect number of nodes."""
        net = multi_layer_network()
        net.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'}
        ])
        assert net.node_count == 2

    def test_edge_count_empty(self):
        """edge_count should be 0 for network without edges."""
        net = multi_layer_network()
        assert net.edge_count == 0

    def test_edge_count_with_edges(self):
        """edge_count should reflect number of edges."""
        net = multi_layer_network()
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'l1', 'target_type': 'l1'},
            {'source': 'B', 'target': 'C', 'source_type': 'l1', 'target_type': 'l1'}
        ])
        assert net.edge_count == 2

    def test_layer_count_empty(self):
        """layer_count should be 0 for empty network."""
        net = multi_layer_network()
        assert net.layer_count == 0

    def test_layer_count_single_layer(self):
        """layer_count should be 1 for single-layer network."""
        net = multi_layer_network()
        net.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'}
        ])
        assert net.layer_count == 1

    def test_layer_count_multiple_layers(self):
        """layer_count should count distinct layers."""
        net = multi_layer_network()
        net.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer2'},
            {'source': 'C', 'type': 'layer3'}
        ])
        assert net.layer_count == 3

    def test_layers_property_empty(self):
        """layers property should return empty list for empty network."""
        net = multi_layer_network()
        assert net.layers == []

    def test_layers_property_sorted(self):
        """layers property should return sorted list of layer names."""
        net = multi_layer_network()
        net.add_nodes([
            {'source': 'A', 'type': 'zebra'},
            {'source': 'B', 'type': 'alpha'},
            {'source': 'C', 'type': 'beta'}
        ])
        assert net.layers == ['alpha', 'beta', 'zebra']

    def test_is_empty_true(self):
        """is_empty should be True for empty network."""
        net = multi_layer_network()
        assert net.is_empty is True

    def test_is_empty_false(self):
        """is_empty should be False for non-empty network."""
        net = multi_layer_network()
        net.add_nodes([{'source': 'A', 'type': 'layer1'}])
        assert net.is_empty is False


class TestMethodChaining:
    """Test method chaining support."""

    def test_add_nodes_returns_self(self):
        """add_nodes should return self for chaining."""
        net = multi_layer_network()
        result = net.add_nodes([{'source': 'A', 'type': 'layer1'}])
        assert result is net

    def test_add_edges_returns_self(self):
        """add_edges should return self for chaining."""
        net = multi_layer_network()
        result = net.add_edges([{
            'source': 'A', 'target': 'B',
            'source_type': 'layer1', 'target_type': 'layer1'
        }])
        assert result is net

    def test_chained_node_additions(self):
        """Multiple add_nodes calls should chain correctly."""
        net = (multi_layer_network()
               .add_nodes([{'source': 'A', 'type': 'layer1'}])
               .add_nodes([{'source': 'B', 'type': 'layer1'}])
               .add_nodes([{'source': 'C', 'type': 'layer2'}]))
        assert len(net) == 3
        assert net.layer_count == 2

    def test_chained_edge_additions(self):
        """Multiple add_edges calls should chain correctly."""
        net = (multi_layer_network()
               .add_edges([{'source': 'A', 'target': 'B',
                           'source_type': 'l1', 'target_type': 'l1'}])
               .add_edges([{'source': 'B', 'target': 'C',
                           'source_type': 'l1', 'target_type': 'l1'}]))
        assert net.edge_count == 2

    def test_mixed_chaining(self):
        """Mixing add_nodes and add_edges in chain should work."""
        net = (multi_layer_network()
               .add_nodes([{'source': 'X', 'type': 'extra'}])
               .add_edges([{'source': 'A', 'target': 'B',
                           'source_type': 'l1', 'target_type': 'l1'}])
               .add_nodes([{'source': 'Y', 'type': 'extra'}]))
        assert ('X', 'extra') in net
        assert ('Y', 'extra') in net
        assert net.edge_count == 1


class TestFactoryMethods:
    """Test factory/class method constructors."""

    def test_from_edges_dict_format(self):
        """from_edges should create network from dict-format edges."""
        net = multi_layer_network.from_edges([
            {'source': 'A', 'target': 'B',
             'source_type': 'layer1', 'target_type': 'layer1'},
            {'source': 'B', 'target': 'C',
             'source_type': 'layer1', 'target_type': 'layer1'}
        ])
        assert net.node_count == 3
        assert net.edge_count == 2

    def test_from_edges_list_format(self):
        """from_edges should create network from list-format edges."""
        net = multi_layer_network.from_edges([
            ['A', 'layer1', 'B', 'layer1', 1],
            ['B', 'layer1', 'C', 'layer1', 1]
        ], input_type='list')
        assert net.node_count == 3
        assert net.edge_count == 2

    def test_from_edges_directed(self):
        """from_edges should respect directed parameter."""
        net = multi_layer_network.from_edges([
            {'source': 'A', 'target': 'B',
             'source_type': 'l1', 'target_type': 'l1'}
        ], directed=True)
        assert net.directed is True

    def test_from_edges_undirected(self):
        """from_edges should respect directed=False parameter."""
        net = multi_layer_network.from_edges([
            {'source': 'A', 'target': 'B',
             'source_type': 'l1', 'target_type': 'l1'}
        ], directed=False)
        assert net.directed is False

    def test_from_networkx_basic(self):
        """from_networkx should convert NetworkX graph."""
        G = nx.Graph()
        G.add_node(('A', 'layer1'))
        G.add_node(('B', 'layer1'))
        G.add_edge(('A', 'layer1'), ('B', 'layer1'))

        net = multi_layer_network.from_networkx(G)
        assert net.node_count == 2
        assert net.edge_count == 1

    def test_from_networkx_infers_directed(self):
        """from_networkx should infer directedness from graph."""
        G = nx.DiGraph()
        G.add_edge(('A', 'l1'), ('B', 'l1'))
        net = multi_layer_network.from_networkx(G)
        assert net.directed is True

        G2 = nx.Graph()
        G2.add_edge(('A', 'l1'), ('B', 'l1'))
        net2 = multi_layer_network.from_networkx(G2)
        assert net2.directed is False


class TestConditionalExpressions:
    """Test using network in conditional expressions."""

    def test_if_statement_empty(self):
        """Empty network should fail if check."""
        net = multi_layer_network()
        result = "empty" if not net else "not empty"
        assert result == "empty"

    def test_if_statement_nonempty(self):
        """Non-empty network should pass if check."""
        net = multi_layer_network()
        net.add_nodes([{'source': 'A', 'type': 'l1'}])
        result = "not empty" if net else "empty"
        assert result == "not empty"

    def test_ternary_expression(self):
        """Network should work in ternary expressions."""
        net = multi_layer_network()
        msg = "has nodes" if net else "is empty"
        assert msg == "is empty"

        net.add_nodes([{'source': 'A', 'type': 'l1'}])
        msg = "has nodes" if net else "is empty"
        assert msg == "has nodes"
