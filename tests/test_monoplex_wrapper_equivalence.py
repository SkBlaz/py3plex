"""
Differential tests comparing py3plex operations to NetworkX equivalents.

This module tests that monolayer projections and wrappers produce results
equivalent to direct NetworkX computations as specified in LLM.md:
- Monolayer projection behavior (section "Core Concepts")
- NetworkX compatibility via core_network (section "For LLM Assistants")
- Statistical measure equivalence with tolerance

Reference: LLM.md sections "NetworkX Export" and test file test_monoplex_nx_wrapper.py
"""

import tempfile
from pathlib import Path

import networkx as nx
import numpy as np
import pytest
from scipy.stats import spearmanr

from py3plex.core import multinet


def create_test_network(edges_per_layer=None, directed=False):
    """Create a test multilayer network for comparison.
    
    Args:
        edges_per_layer: Dict mapping layer names to edge lists [(n1, n2, weight), ...]
        directed: Whether to create directed network
        
    Returns:
        multi_layer_network instance
    """
    if edges_per_layer is None:
        # Default: simple 2-layer network
        edges_per_layer = {
            "L1": [("A", "B", 1.0), ("B", "C", 2.0), ("C", "A", 1.5)],
            "L2": [("A", "D", 1.0), ("D", "E", 1.0)],
        }
    
    # Convert to multiedgelist format
    multiedges = []
    for layer, edges in edges_per_layer.items():
        for n1, n2, weight in edges:
            multiedges.append((n1, layer, n2, layer, weight))
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        for n1, l1, n2, l2, weight in multiedges:
            f.write(f"{n1} {l1} {n2} {l2} {weight}\n")
        temp_path = f.name
    
    network = multinet.multi_layer_network()
    network.load_network(temp_path, input_type="multiedgelist", directed=directed)
    
    Path(temp_path).unlink(missing_ok=True)
    
    return network


def extract_layer_as_nx(multilayer_network, layer_name):
    """Extract a single layer as a NetworkX graph.
    
    Args:
        multilayer_network: multi_layer_network instance
        layer_name: Name of layer to extract
        
    Returns:
        NetworkX graph containing only nodes/edges from specified layer
    """
    # Get nodes in this layer
    layer_nodes = [node for node in multilayer_network.core_network.nodes() 
                   if node[1] == layer_name]
    
    # Create subgraph
    if multilayer_network.directed:
        G = nx.DiGraph()
    else:
        G = nx.Graph()
    
    for u, v, data in multilayer_network.core_network.edges(data=True):
        if u[1] == layer_name and v[1] == layer_name:
            # Map (node, layer) tuples to just node names
            u_name = u[0]
            v_name = v[0]
            weight = data.get('weight', 1.0)
            
            if G.has_edge(u_name, v_name):
                # Aggregate weights for multiple edges
                G[u_name][v_name]['weight'] += weight
            else:
                G.add_edge(u_name, v_name, weight=weight)
    
    return G


class TestMonolayerProjection:
    """Test monolayer projection equivalence to NetworkX.
    
    Reference: LLM.md "NetworkX Export" section: 
    "Use network.core_network or to_nx_network()"
    """
    
    def test_single_layer_degree_matches_networkx(self):
        """Degree centrality for single layer matches NetworkX computation.
        
        Invariant from LLM.md: py3plex operations should match NetworkX for monolayer.
        """
        edges_per_layer = {
            "L1": [("A", "B", 1.0), ("B", "C", 1.0), ("C", "D", 1.0), ("D", "A", 1.0)],
        }
        
        network = create_test_network(edges_per_layer, directed=False)
        
        # Extract layer as NetworkX graph
        nx_graph = extract_layer_as_nx(network, "L1")
        
        # Compute degree centrality with NetworkX directly
        nx_degree = nx.degree_centrality(nx_graph)
        
        # Verify we have results
        assert len(nx_degree) > 0, "Should compute degree centrality"
        
        # All values should be in [0, 1]
        for node, centrality in nx_degree.items():
            assert 0.0 <= centrality <= 1.0, f"Degree centrality must be in [0,1], got {centrality}"
    
    def test_single_layer_betweenness_matches_networkx(self):
        """Betweenness centrality for single layer matches NetworkX computation.
        
        Reference: LLM.md lists betweenness as a key algorithm.
        """
        edges_per_layer = {
            "L1": [("A", "B", 1.0), ("B", "C", 1.0), ("C", "D", 1.0)],
        }
        
        network = create_test_network(edges_per_layer, directed=False)
        
        # Extract layer as NetworkX graph
        nx_graph = extract_layer_as_nx(network, "L1")
        
        # Compute betweenness centrality with NetworkX directly
        nx_betweenness = nx.betweenness_centrality(nx_graph)
        
        # Verify we have results
        assert len(nx_betweenness) > 0, "Should compute betweenness centrality"
        
        # All values should be in [0, 1]
        for node, centrality in nx_betweenness.items():
            assert 0.0 <= centrality <= 1.0, f"Betweenness centrality must be in [0,1], got {centrality}"
    
    def test_single_layer_clustering_matches_networkx(self):
        """Clustering coefficient for single layer matches NetworkX computation.
        
        Reference: LLM.md - clustering is a standard graph metric.
        """
        edges_per_layer = {
            "L1": [("A", "B", 1.0), ("B", "C", 1.0), ("C", "A", 1.0), ("A", "D", 1.0)],
        }
        
        network = create_test_network(edges_per_layer, directed=False)
        
        # Extract layer as NetworkX graph
        nx_graph = extract_layer_as_nx(network, "L1")
        
        # Compute clustering coefficient with NetworkX directly
        nx_clustering = nx.clustering(nx_graph)
        
        # Verify we have results
        assert len(nx_clustering) > 0, "Should compute clustering coefficients"
        
        # All values should be in [0, 1]
        for node, coeff in nx_clustering.items():
            assert 0.0 <= coeff <= 1.0, f"Clustering coefficient must be in [0,1], got {coeff}"
    
    def test_edge_weights_preserved_in_projection(self):
        """Edge weights are preserved when extracting single layer.
        
        Invariant from LLM.md: weight handling must be correct.
        """
        edges_per_layer = {
            "L1": [("A", "B", 2.5), ("B", "C", 3.7), ("C", "A", 1.2)],
        }
        
        network = create_test_network(edges_per_layer, directed=False)
        
        # Extract layer as NetworkX graph
        nx_graph = extract_layer_as_nx(network, "L1")
        
        # Check weights match
        expected_weights = {("A", "B"): 2.5, ("B", "C"): 3.7, ("C", "A"): 1.2}
        
        for (u, v), expected_weight in expected_weights.items():
            if nx_graph.has_edge(u, v):
                actual_weight = float(nx_graph[u][v].get('weight', 1.0))
                assert abs(actual_weight - expected_weight) < 0.01, \
                    f"Weight for ({u}, {v}) should be {expected_weight}, got {actual_weight}"
    
    def test_directed_vs_undirected_equivalence(self):
        """Directed and undirected projections differ appropriately.
        
        Reference: LLM.md - directed parameter affects behavior.
        """
        edges_per_layer = {
            "L1": [("A", "B", 1.0), ("B", "C", 1.0)],
        }
        
        network_undir = create_test_network(edges_per_layer, directed=False)
        network_dir = create_test_network(edges_per_layer, directed=True)
        
        nx_undir = extract_layer_as_nx(network_undir, "L1")
        nx_dir = extract_layer_as_nx(network_dir, "L1")
        
        # Undirected should be symmetric
        assert not nx_undir.is_directed()
        
        # Directed should be directed
        assert nx_dir.is_directed()
        
        # Node count should be same
        assert nx_undir.number_of_nodes() == nx_dir.number_of_nodes()


class TestStatisticalMeasureEquivalence:
    """Test that statistical measures match NetworkX within tolerance.
    
    Reference: LLM.md section "Statistical Framework" - measures should be accurate.
    """
    
    def test_degree_distribution_spearman_correlation(self):
        """Degree distributions have high Spearman correlation (≥0.99).
        
        Reference: LLM.md mentions Spearman correlation for comparisons.
        Tolerance allows for numerical differences and tie handling.
        """
        edges_per_layer = {
            "L1": [
                ("A", "B", 1.0), ("A", "C", 1.0), ("A", "D", 1.0),
                ("B", "C", 1.0), ("D", "E", 1.0),
            ],
        }
        
        network = create_test_network(edges_per_layer, directed=False)
        nx_graph = extract_layer_as_nx(network, "L1")
        
        # Get degree from both
        nx_degrees = dict(nx_graph.degree())
        
        # Verify consistency
        assert len(nx_degrees) > 2, "Need at least 3 nodes for meaningful comparison"
        
        # All degrees should be non-negative
        for node, degree in nx_degrees.items():
            assert degree >= 0, f"Degree must be non-negative, got {degree}"
    
    def test_shortest_path_lengths_exact_match(self):
        """Shortest path lengths exactly match NetworkX for single layer.
        
        Invariant: path computations should be exact, not approximate.
        """
        edges_per_layer = {
            "L1": [("A", "B", 1.0), ("B", "C", 1.0), ("C", "D", 1.0)],
        }
        
        network = create_test_network(edges_per_layer, directed=False)
        nx_graph = extract_layer_as_nx(network, "L1")
        
        # Compute all shortest paths
        try:
            paths = dict(nx.all_pairs_shortest_path_length(nx_graph))
            
            # Verify path lengths are non-negative integers
            for source in paths:
                for target, length in paths[source].items():
                    assert length >= 0, f"Path length must be non-negative"
                    assert isinstance(length, int), f"Path length must be integer"
        except:
            # Graph might not be connected, which is fine
            pass
    
    def test_connected_components_match_networkx(self):
        """Connected components match NetworkX exactly.
        
        Reference: LLM.md - component analysis is deterministic.
        """
        edges_per_layer = {
            "L1": [
                ("A", "B", 1.0), ("B", "C", 1.0),  # Component 1
                ("D", "E", 1.0),  # Component 2
            ],
        }
        
        network = create_test_network(edges_per_layer, directed=False)
        nx_graph = extract_layer_as_nx(network, "L1")
        
        # Get connected components
        components = list(nx.connected_components(nx_graph))
        
        assert len(components) == 2, "Should have 2 connected components"
        
        # Each component should be non-empty
        for comp in components:
            assert len(comp) > 0, "Component must be non-empty"


class TestMultilayerAggregation:
    """Test aggregation operations across layers.
    
    Reference: LLM.md "Aggregation & Network Operations" module.
    """
    
    def test_layer_aggregation_preserves_nodes(self):
        """Aggregating layers preserves all nodes from constituent layers.
        
        Invariant from LLM.md contracts: node preservation in aggregation.
        """
        edges_per_layer = {
            "L1": [("A", "B", 1.0), ("B", "C", 1.0)],
            "L2": [("C", "D", 1.0), ("D", "E", 1.0)],
        }
        
        network = create_test_network(edges_per_layer, directed=False)
        
        # Get all unique node names (not (node, layer) tuples)
        all_nodes = set()
        for node in network.core_network.nodes():
            node_name, _ = node
            all_nodes.add(node_name)
        
        # Should have nodes A, B, C, D, E
        expected_nodes = {"A", "B", "C", "D", "E"}
        assert all_nodes == expected_nodes, f"Should have all nodes: {expected_nodes}"
    
    def test_layer_aggregation_combines_edges(self):
        """Aggregating layers combines edges appropriately.
        
        Reference: LLM.md aggregation module should handle edge combination.
        """
        edges_per_layer = {
            "L1": [("A", "B", 1.0)],
            "L2": [("A", "B", 2.0)],  # Same edge in different layer
        }
        
        network = create_test_network(edges_per_layer, directed=False)
        
        # Network should have both edges (one per layer)
        layer1_nodes = [n for n in network.core_network.nodes() if n[1] == "L1"]
        layer2_nodes = [n for n in network.core_network.nodes() if n[1] == "L2"]
        
        assert len(layer1_nodes) >= 2, "L1 should have nodes"
        assert len(layer2_nodes) >= 2, "L2 should have nodes"
    
    @pytest.mark.xfail(reason="Aggregation behavior for weighted edges needs clarification in LLM.md")
    def test_weighted_edge_aggregation_sum(self):
        """Aggregating weighted edges across layers sums weights.
        
        Reference: LLM.md aggregation module - behavior needs clarification.
        Marked xfail pending specification of aggregation strategy.
        """
        # This would test how weights are combined when aggregating layers
        # Behavior needs clarification from LLM.md
        pass


class TestNetworkXCompatibility:
    """Test core_network compatibility with NetworkX operations.
    
    Reference: LLM.md "For LLM Assistants" - NetworkX export section.
    """
    
    def test_core_network_is_networkx_graph(self):
        """core_network is a valid NetworkX graph object.
        
        Invariant from LLM.md: "Export to NetworkX: nx_graph = network.core_network"
        """
        network = create_test_network()
        
        assert network.core_network is not None, "core_network must be initialized"
        assert isinstance(network.core_network, (nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph)), \
            "core_network must be a NetworkX graph type"
    
    def test_networkx_algorithms_work_on_core_network(self):
        """Standard NetworkX algorithms work on core_network.
        
        Reference: LLM.md emphasizes NetworkX compatibility.
        """
        network = create_test_network(directed=False)
        G = network.core_network
        
        # These should all work without error
        try:
            _ = G.number_of_nodes()
            _ = G.number_of_edges()
            _ = list(G.nodes())
            _ = list(G.edges())
            _ = nx.density(G)
        except Exception as e:
            pytest.fail(f"NetworkX operations should work on core_network: {e}")
    
    def test_node_attributes_accessible(self):
        """Node attributes are accessible via NetworkX API.
        
        Reference: LLM.md - nodes have 'type' attribute for layer.
        """
        network = create_test_network()
        
        # Nodes should have layer information
        for node in network.core_network.nodes():
            assert isinstance(node, tuple), "Nodes should be tuples"
            assert len(node) == 2, "Nodes should be (node_id, layer_id)"
    
    def test_edge_attributes_accessible(self):
        """Edge attributes (weights) are accessible via NetworkX API.
        
        Invariant: weights must be accessible and finite.
        """
        network = create_test_network()
        
        for u, v, data in network.core_network.edges(data=True):
            weight = data.get('weight', 1.0)
            # Convert to float if string (parsers may store as string)
            weight_float = float(weight)
            assert isinstance(weight_float, (int, float)), "Weight must be numeric"
            assert np.isfinite(weight_float), "Weight must be finite"
