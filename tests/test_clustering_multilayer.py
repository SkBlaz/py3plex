"""Test clustering computation on multilayer networks.

This test ensures that clustering examples in documentation actually work.
It addresses the issue that clustering computation was failing on MultiGraph
networks (which py3plex uses) because NetworkX's clustering() doesn't support
MultiGraphs by default.

The fix converts MultiGraph to a simple Graph before computing clustering.
"""

import pandas as pd
import pytest
from py3plex.core import multinet
from py3plex.dsl import Q, L, execute_query


class TestClusteringComputation:
    """Test clustering computation works correctly on multilayer networks."""

    @pytest.fixture
    def sample_network(self):
        """Create a sample multilayer network for testing."""
        network = multinet.multi_layer_network()
        
        # Add nodes
        network.add_nodes([
            {"source": "alice", "type": "social"},
            {"source": "bob", "type": "social"},
            {"source": "charlie", "type": "social"},
            {"source": "diana", "type": "social"},
        ])
        
        # Add edges forming a triangle plus one isolated connection
        network.add_edges([
            {"source": "alice", "target": "bob", "source_type": "social", "target_type": "social"},
            {"source": "bob", "target": "charlie", "source_type": "social", "target_type": "social"},
            {"source": "alice", "target": "charlie", "source_type": "social", "target_type": "social"},
            {"source": "charlie", "target": "diana", "source_type": "social", "target_type": "social"},
        ])
        
        return network

    def test_clustering_with_legacy_dsl_string_syntax(self, sample_network):
        """Test clustering computation using legacy DSL string syntax."""
        # This tests the example pattern from documentation
        result = execute_query(
            sample_network,
            'SELECT nodes WHERE layer="social" COMPUTE clustering'
        )
        
        # Legacy DSL returns dict with 'computed' key
        assert 'computed' in result
        assert 'clustering' in result['computed']
        
        clustering_values = result['computed']['clustering']
        
        # Verify we got results for all nodes
        assert len(clustering_values) == 4
        
        # Verify clustering values are in valid range [0, 1]
        for node, value in clustering_values.items():
            assert isinstance(value, (int, float))
            assert 0 <= value <= 1
    
    def test_clustering_with_builder_api(self, sample_network):
        """Test clustering computation using builder API (Q, L)."""
        # This tests the example pattern from documentation
        result = (
            Q.nodes()
             .compute("degree", "clustering")
             .execute(sample_network)
        )
        
        # Builder API returns QueryResult that can be converted to pandas
        df = result.to_pandas()
        
        # Verify clustering column exists
        assert 'clustering' in df.columns
        
        # Verify we got results for all nodes
        assert len(df) == 4
        
        # Verify clustering values are in valid range [0, 1]
        assert df['clustering'].min() >= 0
        assert df['clustering'].max() <= 1
        
        # Verify clustering values make sense for our triangle topology
        # Alice, Bob form a triangle with Charlie -> clustering = 1.0
        # Diana is only connected to Charlie -> clustering = 0
        clustering_dict = dict(zip(df['id'], df['clustering']))
        
        # At least one node in the triangle should have high clustering
        max_clustering = df['clustering'].max()
        assert max_clustering > 0.9, "Triangle nodes should have high clustering"
    
    def test_clustering_with_multiple_layers(self):
        """Test clustering computation across multiple layers."""
        network = multinet.multi_layer_network()
        
        # Add nodes and edges for multiple layers
        for layer in ['friends', 'work']:
            for i in range(4):
                network.add_nodes([{"source": f"node{i}", "type": layer}])
            
            # Add edges forming triangles (nodes 0, 1, 2 form a triangle, node3 is isolated)
            network.add_edges([
                {"source": "node0", "target": "node1", "source_type": layer, "target_type": layer},
                {"source": "node1", "target": "node2", "source_type": layer, "target_type": layer},
                {"source": "node0", "target": "node2", "source_type": layer, "target_type": layer},
            ])
        
        # Test layer-by-layer computation
        # get_layers() returns tuple: (layer_names, graphs, positions)
        layer_names = network.get_layers()[0]
        
        for layer_name in layer_names:
            result = (
                Q.nodes()
                 .from_layers(L[layer_name])
                 .compute("clustering")
                 .execute(network)
            )
            
            df = result.to_pandas()
            
            # Should have computed clustering for all nodes in this layer
            assert len(df) > 0, f"Should have nodes in layer {layer_name}"
            assert 'clustering' in df.columns
            
            # Nodes with edges should have valid clustering values
            # Isolated nodes (degree 0) or nodes with degree 1 have clustering = 0 or NaN
            for _, row in df.iterrows():
                clustering_val = row['clustering']
                # Either a valid number in [0, 1] or NaN for isolated/low-degree nodes
                if pd.notna(clustering_val):
                    assert 0 <= clustering_val <= 1
    
    def test_clustering_with_degree_filter(self, sample_network):
        """Test combining clustering with degree filtering (common pattern)."""
        # This tests a common pattern from documentation
        result = (
            Q.nodes()
             .where(degree__gt=1)
             .compute("degree", "clustering")
             .execute(sample_network)
        )
        
        df = result.to_pandas()
        
        # Should filter out nodes with degree <= 1
        assert len(df) > 0
        assert (df['degree'] > 1).all()
        
        # Should still compute clustering correctly
        assert 'clustering' in df.columns
        assert df['clustering'].notna().all()
    
    def test_clustering_matches_networkx_on_simple_graph(self):
        """Verify clustering values match NetworkX for simple graphs."""
        import networkx as nx
        
        # Create a simple network without parallel edges
        network = multinet.multi_layer_network()
        network.add_nodes([
            {"source": "A", "type": "layer1"},
            {"source": "B", "type": "layer1"},
            {"source": "C", "type": "layer1"},
        ])
        network.add_edges([
            {"source": "A", "target": "B", "source_type": "layer1", "target_type": "layer1"},
            {"source": "B", "target": "C", "source_type": "layer1", "target_type": "layer1"},
            {"source": "A", "target": "C", "source_type": "layer1", "target_type": "layer1"},
        ])
        
        # Compute clustering using DSL
        result = Q.nodes().compute("clustering").execute(network)
        df = result.to_pandas()
        
        # Compute clustering using NetworkX directly on simple graph
        G = nx.Graph()
        G.add_edges_from([("A", "B"), ("B", "C"), ("A", "C")])
        nx_clustering = nx.clustering(G)
        
        # Values should match (all nodes in perfect triangle have clustering = 1.0)
        for _, row in df.iterrows():
            node_id = row['id'][0] if isinstance(row['id'], tuple) else row['id']
            assert abs(row['clustering'] - nx_clustering[node_id]) < 0.001
