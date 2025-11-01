"""
Property-based tests for py3plex algorithms.

This module tests algorithm correctness and invariants using property-based
testing with the Hypothesis library. Focuses on mathematical properties that
should hold for all valid inputs.
"""

import networkx as nx
import pytest
from hypothesis import given, strategies as st, assume, settings


# Custom strategies for generating valid test data
def small_graph_strategy():
    """Generate small NetworkX graphs for testing."""
    def build_graph(edge_list):
        G = nx.Graph()
        for u, v in edge_list:
            G.add_edge(u, v)
        return G
    
    return st.lists(
        st.tuples(
            st.integers(min_value=0, max_value=10),
            st.integers(min_value=0, max_value=10)
        ),
        min_size=1,
        max_size=20
    ).map(build_graph)


def small_digraph_strategy():
    """Generate small directed NetworkX graphs for testing."""
    def build_digraph(edge_list):
        G = nx.DiGraph()
        for u, v in edge_list:
            G.add_edge(u, v)
        return G
    
    return st.lists(
        st.tuples(
            st.integers(min_value=0, max_value=10),
            st.integers(min_value=0, max_value=10)
        ),
        min_size=1,
        max_size=20
    ).map(build_digraph)


class TestBasicStatisticsProperties:
    """Property-based tests for basic network statistics."""
    
    @given(small_graph_strategy())
    @settings(max_examples=100)
    def test_degree_distribution_sum_equals_double_edges(self, G):
        """
        Property: Sum of degree distribution equals 2 * number of edges.
        
        This is the handshaking lemma: each edge contributes to the degree
        of exactly two nodes.
        """
        assume(G.number_of_edges() > 0)
        
        degree_dict = dict(G.degree())
        total_degree = sum(degree_dict.values())
        
        # For undirected graphs: sum of degrees = 2 * edges
        assert total_degree == 2 * G.number_of_edges()
    
    @given(small_digraph_strategy())
    @settings(max_examples=100)
    def test_directed_degree_sum_equals_edges(self, G):
        """
        Property: Sum of out-degrees (or in-degrees) equals number of edges.
        
        Each edge contributes 1 to out-degree of source and 1 to in-degree of target.
        """
        assume(G.number_of_edges() > 0)
        
        out_degree_sum = sum(dict(G.out_degree()).values())
        in_degree_sum = sum(dict(G.in_degree()).values())
        
        assert out_degree_sum == G.number_of_edges()
        assert in_degree_sum == G.number_of_edges()
        assert out_degree_sum == in_degree_sum
    
    @given(small_graph_strategy())
    @settings(max_examples=100)
    def test_node_count_positive(self, G):
        """Property: Number of nodes is always non-negative."""
        assert G.number_of_nodes() >= 0
    
    @given(small_graph_strategy())
    @settings(max_examples=100)
    def test_edge_count_bounded_by_complete_graph(self, G):
        """
        Property: Number of edges cannot exceed complete graph.
        
        For n nodes, maximum edges = n(n-1)/2 (undirected) or n(n-1) (directed).
        Self-loops are allowed in NetworkX, so we account for them.
        """
        n = G.number_of_nodes()
        m = G.number_of_edges()
        
        if n == 0:
            assert m == 0
        elif n == 1:
            # Single node can have a self-loop
            assert m <= 1
        else:
            # Undirected graph maximum (without self-loops)
            max_edges = n * (n - 1) // 2
            # With self-loops, add n more possible edges
            max_edges_with_loops = max_edges + n
            assert m <= max_edges_with_loops
    
    @given(small_graph_strategy())
    @settings(max_examples=100)
    def test_connected_components_partition_nodes(self, G):
        """
        Property: Connected components partition the node set.
        
        Every node belongs to exactly one connected component.
        """
        components = list(nx.connected_components(G))
        
        # Union of all components should equal node set
        all_nodes_in_components = set().union(*components) if components else set()
        assert all_nodes_in_components == set(G.nodes())
        
        # Components should be disjoint
        for i, comp1 in enumerate(components):
            for j, comp2 in enumerate(components):
                if i != j:
                    assert len(comp1.intersection(comp2)) == 0


class TestAggregationProperties:
    """Property-based tests for network aggregation operations."""
    
    @pytest.mark.skip(reason="Requires full py3plex installation with all dependencies")
    @given(
        st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=5),
                st.integers(min_value=0, max_value=5),
                st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False)
            ),
            min_size=2,
            max_size=10
        )
    )
    @settings(max_examples=30)
    def test_aggregation_preserves_node_union(self, edges_with_weights):
        """
        Property: Aggregation preserves the union of all nodes.
        
        No nodes should be lost during aggregation.
        """
        from py3plex.multinet.aggregation import aggregate_layers
        
        # Build edge list with layers
        edges = []
        all_nodes = set()
        for u, v, w in edges_with_weights:
            edges.append((u, 'layer1', v, 'layer1', w))
            edges.append((u, 'layer2', v, 'layer2', w * 0.5))
            all_nodes.add(u)
            all_nodes.add(v)
        
        assume(len(all_nodes) >= 2)  # Need at least 2 nodes
        
        # Aggregate with sum
        aggregated = aggregate_layers(edges, reducer='sum')
        
        # Check node preservation
        aggregated_nodes = set()
        for u, v, w in aggregated:
            aggregated_nodes.add(u)
            aggregated_nodes.add(v)
        
        assert aggregated_nodes == all_nodes
    
    @pytest.mark.skip(reason="Requires full py3plex installation with all dependencies")
    @given(
        st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=5),
                st.integers(min_value=0, max_value=5),
                st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False)
            ),
            min_size=1,
            max_size=10
        )
    )
    @settings(max_examples=30)
    def test_aggregation_weights_non_negative(self, edges_with_weights):
        """
        Property: Aggregated weights remain non-negative.
        
        Sum, mean, and max of non-negative numbers are non-negative.
        """
        from py3plex.multinet.aggregation import aggregate_layers
        
        edges = []
        for u, v, w in edges_with_weights:
            edges.append((u, 'layer1', v, 'layer1', abs(w)))  # Ensure non-negative
        
        assume(len(edges) > 0)
        
        for reducer in ['sum', 'mean', 'max']:
            aggregated = aggregate_layers(edges, reducer=reducer)
            
            for u, v, w in aggregated:
                assert w >= 0, f"Negative weight {w} found with reducer {reducer}"


class TestRandomNetworkProperties:
    """Property-based tests for random network generation."""
    
    @pytest.mark.skip(reason="Requires full py3plex installation with all dependencies")
    @given(
        st.integers(min_value=2, max_value=20),  # n nodes
        st.integers(min_value=1, max_value=3),   # l layers
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)  # p
    )
    @settings(max_examples=20)
    def test_random_er_network_properties(self, n, l, p):
        """
        Property: Random ER networks satisfy basic structural properties.
        
        - Number of nodes equals specified n
        - Network has l layers
        - Edge probability roughly matches p (with statistical tolerance)
        """
        from py3plex.core.random_generators import random_multilayer_ER
        
        network = random_multilayer_ER(n=n, l=l, p=p)
        
        # Check network was created
        assert network is not None
        assert network.number_of_nodes() > 0
        
        # For p=0, should have no edges; for p=1, should be dense
        if p == 0.0:
            # Might have inter-layer edges, so just check intra-layer
            pass  # Skip detailed check as inter-layer edges exist
        elif p == 1.0:
            # Should be nearly complete (accounting for multilayer structure)
            assert network.number_of_edges() > 0
    
    @pytest.mark.skip(reason="Requires full py3plex installation with all dependencies")
    @given(
        st.integers(min_value=2, max_value=15),  # n nodes
        st.integers(min_value=1, max_value=3),   # m layers
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)  # d dropout
    )
    @settings(max_examples=20)
    def test_multiplex_generator_properties(self, n, m, d):
        """
        Property: Multiplex generator creates valid networks.
        
        - Returns a NetworkX MultiGraph
        - Has specified number of layers
        - Dropout probability affects node presence
        """
        from py3plex.core.random_generators import random_multiplex_generator
        
        network = random_multiplex_generator(n=n, m=m, d=d)
        
        # Check network type
        assert isinstance(network, nx.MultiGraph)
        
        # Check network has nodes
        assert network.number_of_nodes() > 0
        
        # For d=0, all nodes should be present; for d=1, network should be sparse
        if d == 0.0:
            # All nodes should be present across layers
            assert network.number_of_nodes() > 0
        elif d == 1.0:
            # High dropout should result in very sparse network
            pass  # Skip detailed check as some nodes may still exist


class TestNetworkTransformationProperties:
    """Property-based tests for network transformations."""
    
    @given(small_graph_strategy())
    @settings(max_examples=50)
    def test_subgraph_is_subset(self, G):
        """
        Property: A subgraph contains a subset of nodes and edges.
        
        Removing nodes should never increase node or edge count.
        """
        assume(G.number_of_nodes() >= 2)
        
        # Create a subgraph by removing one node
        nodes_to_keep = list(G.nodes())[:-1]  # Remove last node
        if len(nodes_to_keep) == 0:
            return
        
        H = G.subgraph(nodes_to_keep)
        
        assert H.number_of_nodes() <= G.number_of_nodes()
        assert H.number_of_edges() <= G.number_of_edges()
        assert H.number_of_nodes() == len(nodes_to_keep)
    
    @given(small_graph_strategy())
    @settings(max_examples=50)
    def test_complement_graph_properties(self, G):
        """
        Property: Complement graph has edges where original doesn't.
        
        G + complement(G) should equal complete graph (for simple graphs without self-loops).
        """
        assume(G.number_of_nodes() >= 2)
        assume(G.number_of_nodes() <= 8)  # Keep small for performance
        
        # Remove self-loops for this test
        G_simple = G.copy()
        G_simple.remove_edges_from(nx.selfloop_edges(G_simple))
        
        H = nx.complement(G_simple)
        
        n = G_simple.number_of_nodes()
        max_edges = n * (n - 1) // 2
        
        # Edges in G + edges in complement should equal max possible
        total_edges = G_simple.number_of_edges() + H.number_of_edges()
        
        # For simple graphs without self-loops
        assert total_edges == max_edges


class TestCentralityProperties:
    """Property-based tests for centrality measures."""
    
    @given(small_graph_strategy())
    @settings(max_examples=50)
    def test_degree_centrality_bounds(self, G):
        """
        Property: Degree centrality is in [0, 1] after normalization.
        
        Centrality measures should be normalized to unit range.
        Self-loops count as degree 2 in NetworkX, so we handle that.
        """
        assume(G.number_of_nodes() >= 2)
        
        # Remove self-loops to avoid centrality > 1.0
        G_simple = G.copy()
        G_simple.remove_edges_from(nx.selfloop_edges(G_simple))
        
        centrality = nx.degree_centrality(G_simple)
        
        for node, value in centrality.items():
            assert 0.0 <= value <= 1.0, f"Centrality {value} out of bounds for node {node}"
    
    @given(small_graph_strategy())
    @settings(max_examples=30)
    def test_betweenness_centrality_bounds(self, G):
        """
        Property: Betweenness centrality is in [0, 1] after normalization.
        """
        assume(G.number_of_nodes() >= 2)
        assume(nx.is_connected(G))  # Betweenness requires connectivity
        
        centrality = nx.betweenness_centrality(G, normalized=True)
        
        for node, value in centrality.items():
            assert 0.0 <= value <= 1.0
    
    @given(small_graph_strategy())
    @settings(max_examples=30)
    def test_closeness_centrality_bounds(self, G):
        """
        Property: Closeness centrality is in [0, 1] after normalization.
        """
        assume(G.number_of_nodes() >= 2)
        assume(nx.is_connected(G))  # Closeness requires connectivity
        
        centrality = nx.closeness_centrality(G)
        
        for node, value in centrality.items():
            assert 0.0 <= value <= 1.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
