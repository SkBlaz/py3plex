"""
Tests for vectorized aggregation integration with multi_layer_network object.

Tests the integration of aggregate_layers function with the main
multi_layer_network class, ensuring compatibility and correctness.
"""

import numpy as np
import pytest
import scipy.sparse as sp

from py3plex.core import multinet, random_generators
from py3plex.multinet.aggregation import aggregate_layers


class TestMultilayerIntegration:
    """Test integration with multi_layer_network object."""
    
    @pytest.fixture
    def simple_network(self):
        """Create a simple multilayer network."""
        network = multinet.multi_layer_network(directed=False)
        
        # Add edges across multiple layers
        edges = [
            {"source": 0, "target": 1, "source_type": "layer1", "target_type": "layer1", "type": "edge"},
            {"source": 1, "target": 2, "source_type": "layer1", "target_type": "layer1", "type": "edge"},
            {"source": 0, "target": 1, "source_type": "layer2", "target_type": "layer2", "type": "edge"},
            {"source": 2, "target": 3, "source_type": "layer2", "target_type": "layer2", "type": "edge"},
        ]
        network.add_edges(edges)
        return network
    
    @pytest.fixture
    def random_multiplex(self):
        """Create a random multiplex network."""
        return random_generators.random_multiplex_ER(100, 3, 0.05, directed=False)
    
    def _extract_edges_from_network(self, network):
        """
        Helper to extract edges from multi_layer_network in aggregate_layers format.
        
        Returns:
            np.ndarray: Array of shape (E, 4) with (layer, src, dst, weight)
        """
        edge_list = []
        layer_map = {}
        layer_counter = 0
        
        for edge in network.get_edges(data=True):
            src_node = edge[0]
            dst_node = edge[1]
            
            src_id = src_node[0]
            src_layer = src_node[1]
            dst_id = dst_node[0]
            
            if src_layer not in layer_map:
                layer_map[src_layer] = layer_counter
                layer_counter += 1
            
            layer_idx = layer_map[src_layer]
            # Handle edge data - might be int (key) or dict
            weight = 1.0
            if len(edge) > 2 and isinstance(edge[2], dict):
                weight = edge[2].get('weight', 1.0)
            
            edge_list.append([layer_idx, int(src_id), int(dst_id), weight])
        
        return np.array(edge_list), layer_map
    
    def test_extract_edges_from_simple_network(self, simple_network):
        """Test edge extraction from multi_layer_network."""
        edges, layer_map = self._extract_edges_from_network(simple_network)
        
        # Check we got edges
        assert len(edges) > 0
        assert edges.shape[1] == 4  # (layer, src, dst, weight)
        
        # Check layer mapping
        assert len(layer_map) > 0
        assert all(isinstance(k, str) for k in layer_map.keys())
        assert all(isinstance(v, int) for v in layer_map.values())
    
    def test_vectorized_aggregation_on_multilayer_network(self, simple_network):
        """Test vectorized aggregation on multi_layer_network object."""
        edges, layer_map = self._extract_edges_from_network(simple_network)
        
        # Aggregate with vectorized method
        mat = aggregate_layers(edges, reducer="sum", to_sparse=True)
        
        # Check result
        assert sp.isspmatrix_csr(mat)
        assert mat.shape[0] > 0
        assert mat.nnz > 0
    
    def test_vectorized_aggregation_works_correctly(self, simple_network):
        """Test that vectorized aggregation produces correct results on multi_layer_network."""
        edges, layer_map = self._extract_edges_from_network(simple_network)
        
        # Vectorized aggregation
        vec_mat = aggregate_layers(edges, reducer="sum", to_sparse=False)
        
        # Verify results
        assert vec_mat.shape[0] > 0
        # Edge (0,1) appears in multiple layers, so should have weight > 1
        assert vec_mat[0, 1] > 1.0
    
    def test_vectorized_performance_on_larger_network(self, random_multiplex):
        """Test that vectorized method performs well on larger network."""
        import time
        
        # Extract edges
        edges, _ = self._extract_edges_from_network(random_multiplex)
        
        # Time vectorized method - should complete quickly
        t0 = time.perf_counter()
        vec_mat = aggregate_layers(edges, reducer="sum", to_sparse=True)
        vec_time = time.perf_counter() - t0
        
        # Should complete in reasonable time
        assert vec_time < 0.5, f"Vectorized method too slow: {vec_time:.4f}s"
        assert vec_mat.nnz > 0
    
    def test_multiple_reducer_modes_on_network(self, simple_network):
        """Test different reducer modes on network edges."""
        edges, _ = self._extract_edges_from_network(simple_network)
        
        # Test all reducer modes
        mat_sum = aggregate_layers(edges, reducer="sum", to_sparse=True)
        mat_mean = aggregate_layers(edges, reducer="mean", to_sparse=True)
        mat_max = aggregate_layers(edges, reducer="max", to_sparse=True)
        
        # All should produce valid matrices
        assert sp.isspmatrix_csr(mat_sum)
        assert sp.isspmatrix_csr(mat_mean)
        assert sp.isspmatrix_csr(mat_max)
        
        # All should have same shape
        assert mat_sum.shape == mat_mean.shape == mat_max.shape
    
    def test_weighted_network_aggregation(self):
        """Test aggregation with weighted edges."""
        network = multinet.multi_layer_network(directed=False)
        
        # Add weighted edges
        edges = [
            {"source": 0, "target": 1, "source_type": "layer1", "target_type": "layer1", 
             "type": "edge", "weight": 2.0},
            {"source": 0, "target": 1, "source_type": "layer2", "target_type": "layer2", 
             "type": "edge", "weight": 3.0},
        ]
        network.add_edges(edges)
        
        # Extract and aggregate
        edge_array, _ = self._extract_edges_from_network(network)
        mat = aggregate_layers(edge_array, reducer="sum", to_sparse=False)
        
        # Check aggregated weight (should be 2.0 + 3.0 = 5.0)
        assert mat[0, 1] == pytest.approx(5.0, abs=1e-6)
    
    def test_sparse_output_from_network(self, random_multiplex):
        """Test that sparse output is memory efficient."""
        edges, _ = self._extract_edges_from_network(random_multiplex)
        
        # Get sparse and dense versions
        mat_sparse = aggregate_layers(edges, reducer="sum", to_sparse=True)
        mat_dense = aggregate_layers(edges, reducer="sum", to_sparse=False)
        
        # Sparse should use less memory
        sparse_bytes = (
            mat_sparse.data.nbytes + 
            mat_sparse.indices.nbytes + 
            mat_sparse.indptr.nbytes
        )
        dense_bytes = mat_dense.nbytes
        
        assert sparse_bytes < dense_bytes * 0.5, (
            "Sparse matrix should use significantly less memory"
        )
    
    def test_networkx_conversion(self, simple_network):
        """Test conversion of aggregated matrix to NetworkX graph."""
        import networkx as nx
        
        edges, _ = self._extract_edges_from_network(simple_network)
        mat = aggregate_layers(edges, reducer="sum", to_sparse=True)
        
        # Convert to NetworkX
        G = nx.from_scipy_sparse_array(mat, create_using=nx.Graph)
        
        # Check graph is valid
        assert G.number_of_nodes() > 0
        assert G.number_of_edges() > 0
    
    def test_networkx_algorithms_on_aggregated(self, random_multiplex):
        """Test that standard NetworkX algorithms work on aggregated network."""
        import networkx as nx
        
        edges, _ = self._extract_edges_from_network(random_multiplex)
        mat = aggregate_layers(edges, reducer="sum", to_sparse=True)
        
        # Convert to NetworkX
        G = nx.from_scipy_sparse_array(mat, create_using=nx.Graph)
        
        # Test various algorithms
        degree_cent = nx.degree_centrality(G)
        assert len(degree_cent) == G.number_of_nodes()
        
        clustering = nx.clustering(G)
        assert len(clustering) == G.number_of_nodes()
        
        # Check we can get connected components
        components = list(nx.connected_components(G))
        assert len(components) > 0


class TestMultiplexNetworkCases:
    """Test specific multiplex network scenarios."""
    
    def test_multiplex_with_coupling_edges(self):
        """Test aggregation handles multiplex networks with coupling edges."""
        network = multinet.multi_layer_network(
            network_type="multiplex",
            directed=False
        )
        
        # Add both intra-layer and inter-layer edges
        edges = [
            # Intra-layer edges
            {"source": 0, "target": 1, "source_type": "layer1", "target_type": "layer1", "type": "edge"},
            {"source": 0, "target": 1, "source_type": "layer2", "target_type": "layer2", "type": "edge"},
            # Coupling edge (between layers) - should be ignored in aggregation
            {"source": 0, "target": 0, "source_type": "layer1", "target_type": "layer2", "type": "coupling"},
        ]
        network.add_edges(edges)
        
        # Extract edges (should only get intra-layer edges)
        edge_list = []
        layer_map = {}
        layer_counter = 0
        
        for edge in network.get_edges(data=True, multiplex_edges=False):
            src_node = edge[0]
            dst_node = edge[1]
            src_layer = src_node[1]
            
            if src_layer not in layer_map:
                layer_map[src_layer] = layer_counter
                layer_counter += 1
            
            edge_list.append([
                layer_map[src_layer],
                int(src_node[0]),
                int(dst_node[0]),
                1.0
            ])
        
        edges_array = np.array(edge_list)
        mat = aggregate_layers(edges_array, reducer="sum", to_sparse=True)
        
        # Should have aggregated the two edges (0,1) from different layers
        assert mat.nnz > 0
    
    def test_directed_multilayer_network(self):
        """Test aggregation on directed multilayer network."""
        network = multinet.multi_layer_network(directed=True)
        
        edges = [
            {"source": 0, "target": 1, "source_type": "layer1", "target_type": "layer1", "type": "edge"},
            {"source": 1, "target": 0, "source_type": "layer1", "target_type": "layer1", "type": "edge"},  # Reverse
            {"source": 0, "target": 1, "source_type": "layer2", "target_type": "layer2", "type": "edge"},
        ]
        network.add_edges(edges)
        
        # Extract and aggregate
        edge_list = []
        for edge in network.get_edges(data=True):
            src_node, dst_node = edge[0], edge[1]
            edge_list.append([0, int(src_node[0]), int(dst_node[0]), 1.0])
        
        edges_array = np.array(edge_list)
        mat = aggregate_layers(edges_array, reducer="sum", to_sparse=False)
        
        # For directed graph, (0,1) and (1,0) should be different
        # Edge (0,1) appears in layer1 and layer2, so weight should be 2
        # Edge (1,0) appears only in layer1, so weight should be 1
        assert mat[0, 1] == pytest.approx(2.0, abs=1e-6)
        assert mat[1, 0] == pytest.approx(1.0, abs=1e-6)


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""
    
    def test_large_multiplex_performance(self):
        """Test performance on larger multiplex network."""
        # Generate larger network
        network = random_generators.random_multiplex_ER(500, 5, 0.01, directed=False)
        
        # Extract edges
        edge_list = []
        layer_map = {}
        layer_counter = 0
        
        for edge in network.get_edges(data=True):
            src_node = edge[0]
            src_layer = src_node[1]
            
            if src_layer not in layer_map:
                layer_map[src_layer] = layer_counter
                layer_counter += 1
            
            edge_list.append([
                layer_map[src_layer],
                int(src_node[0]),
                int(edge[1][0]),
                1.0
            ])
        
        edges_array = np.array(edge_list)
        
        # Should complete quickly
        import time
        t0 = time.perf_counter()
        mat = aggregate_layers(edges_array, reducer="sum", to_sparse=True)
        elapsed = time.perf_counter() - t0
        
        assert elapsed < 1.0, f"Aggregation too slow: {elapsed:.4f}s for {len(edges_array)} edges"
        assert mat.nnz > 0
    
    def test_extract_and_aggregate_workflow(self):
        """Test complete workflow: create -> extract -> aggregate -> analyze."""
        # Step 1: Create network
        network = random_generators.random_multiplex_ER(100, 3, 0.05, directed=False)
        
        # Step 2: Extract edges
        edge_list = []
        layer_map = {}
        layer_counter = 0
        
        for edge in network.get_edges(data=True):
            src_node = edge[0]
            src_layer = src_node[1]
            
            if src_layer not in layer_map:
                layer_map[src_layer] = layer_counter
                layer_counter += 1
            
            edge_list.append([
                layer_map[src_layer],
                int(src_node[0]),
                int(edge[1][0]),
                1.0  # Use fixed weight for simplicity
            ])
        
        edges_array = np.array(edge_list)
        
        # Step 3: Aggregate
        mat = aggregate_layers(edges_array, reducer="sum", to_sparse=True)
        
        # Step 4: Convert to NetworkX
        import networkx as nx
        G = nx.from_scipy_sparse_array(mat, create_using=nx.Graph)
        
        # Step 5: Analyze
        degree_cent = nx.degree_centrality(G)
        avg_clustering = nx.average_clustering(G)
        
        # Sanity checks
        assert len(degree_cent) > 0
        assert 0 <= avg_clustering <= 1
