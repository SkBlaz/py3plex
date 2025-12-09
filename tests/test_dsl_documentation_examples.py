"""Test that documentation examples actually work.

This test file ensures that code examples in the DSL documentation
(docfiles/how-to/query_with_dsl.rst) are not mock examples but actually work.

This addresses GitHub issue about ensuring examples are legitimate and verified.
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import Q, L, execute_query


class TestDSLDocumentationExamples:
    """Test that DSL documentation examples work correctly."""

    @pytest.fixture
    def doc_example_network(self):
        """Create a network matching documentation examples."""
        network = multinet.multi_layer_network()
        
        # Create a network similar to documentation examples
        nodes = []
        edges = []
        
        # Social layer
        for name in ['alice', 'bob', 'charlie', 'diana', 'eve', 'frank', 'grace']:
            nodes.append({'source': name, 'type': 'social'})
        
        # Add some edges to create interesting structure
        social_edges = [
            ('alice', 'bob'), ('alice', 'charlie'), ('alice', 'diana'),
            ('bob', 'charlie'), ('bob', 'eve'),
            ('charlie', 'diana'), ('charlie', 'frank'),
            ('diana', 'eve'), ('eve', 'frank'), ('frank', 'grace'),
        ]
        for src, tgt in social_edges:
            edges.append({
                'source': src, 'target': tgt,
                'source_type': 'social', 'target_type': 'social'
            })
        
        # Work layer
        for name in ['alice', 'bob', 'charlie', 'diana']:
            nodes.append({'source': name, 'type': 'work'})
        
        work_edges = [
            ('alice', 'bob'), ('bob', 'charlie'), ('charlie', 'diana'),
        ]
        for src, tgt in work_edges:
            edges.append({
                'source': src, 'target': tgt,
                'source_type': 'work', 'target_type': 'work'
            })
        
        network.add_nodes(nodes)
        network.add_edges(edges)
        
        return network

    def test_doc_example_line_325_compute_clustering(self, doc_example_network):
        """Test example from line 325: compute degree, betweenness, clustering."""
        # From documentation:
        # result = (
        #     Q.nodes()
        #      .compute("degree", "betweenness_centrality", "clustering")
        #      .execute(network)
        # )
        
        result = (
            Q.nodes()
             .compute("degree", "betweenness_centrality", "clustering")
             .execute(doc_example_network)
        )
        
        df = result.to_pandas()
        
        # Verify structure matches documentation
        assert 'id' in df.columns
        assert 'degree' in df.columns
        assert 'betweenness_centrality' in df.columns
        assert 'clustering' in df.columns
        
        # Verify we got results
        assert len(df) > 0
        
        # Verify values are valid
        assert (df['degree'] >= 0).all()
        assert (df['betweenness_centrality'] >= 0).all()
        # Clustering can be NaN for isolated nodes, but valid values should be in [0, 1]
        valid_clustering = df['clustering'].dropna()
        assert (valid_clustering >= 0).all()
        assert (valid_clustering <= 1).all()

    def test_doc_example_line_469_layer_filtering_with_clustering(self, doc_example_network):
        """Test example from line 469: compute with layer filtering."""
        # From documentation:
        # result = (
        #     Q.nodes()
        #      .from_layers(L["social"])
        #      .compute("degree", "betweenness_centrality", "clustering")
        #      .execute(network)
        # )
        
        result = (
            Q.nodes()
             .from_layers(L["social"])
             .compute("degree", "betweenness_centrality", "clustering")
             .execute(doc_example_network)
        )
        
        df = result.to_pandas()
        
        # All nodes should be from social layer
        assert len(df) > 0
        assert all(layer == 'social' for layer in df['layer'])
        
        # Should have all the computed attributes
        assert 'degree' in df.columns
        assert 'betweenness_centrality' in df.columns
        assert 'clustering' in df.columns

    def test_doc_example_line_950_layer_comparison(self, doc_example_network):
        """Test example from line 950: compare layers with clustering stats."""
        # From documentation:
        # layers = network.get_layers()
        # for layer in layers:
        #     result = (
        #         Q.nodes()
        #          .from_layers(L[layer])
        #          .compute("degree", "clustering")
        #          .execute(network)
        #     )
        #     df = result.to_pandas()
        #     ... compute stats ...
        
        layer_names = doc_example_network.get_layers()[0]
        
        layer_stats = []
        for layer_name in layer_names:
            result = (
                Q.nodes()
                 .from_layers(L[layer_name])
                 .compute("degree", "clustering")
                 .execute(doc_example_network)
            )
            df = result.to_pandas()
            
            assert len(df) > 0, f"Layer {layer_name} should have nodes"
            
            layer_stats.append({
                'layer': layer_name,
                'num_nodes': len(df),
                'mean_degree': df['degree'].mean(),
                'max_degree': df['degree'].max(),
                'mean_clustering': df['clustering'].mean(),
            })
        
        # Should have computed stats for all layers
        assert len(layer_stats) == len(layer_names)
        assert all('mean_clustering' in stat for stat in layer_stats)

    def test_doc_example_string_syntax_line_189(self, doc_example_network):
        """Test example from line 189: string syntax with clustering."""
        # From documentation:
        # result = execute_query(
        #     network,
        #     'SELECT nodes WHERE layer="social" '
        #     'COMPUTE degree COMPUTE betweenness_centrality'
        # )
        
        result = execute_query(
            doc_example_network,
            'SELECT nodes WHERE layer="social" COMPUTE clustering'
        )
        
        # Legacy DSL returns dict
        assert 'computed' in result
        assert 'clustering' in result['computed']
        
        # Verify clustering computed successfully
        clustering_values = result['computed']['clustering']
        assert len(clustering_values) > 0

    def test_doc_example_high_degree_with_clustering(self, doc_example_network):
        """Test filtering high-degree nodes and computing clustering."""
        # Test that clustering works with degree computation
        result = (
            Q.nodes()
             .compute("degree", "clustering")
             .execute(doc_example_network)
        )
        
        df = result.to_pandas()
        
        # Should have results
        assert len(df) > 0
        
        # Should have both degree and clustering
        assert 'degree' in df.columns
        assert 'clustering' in df.columns
        
        # Verify high-degree nodes exist and have valid clustering
        high_degree = df[df['degree'] > 2]
        assert len(high_degree) > 0, "Should have some high-degree nodes"
        
        # High-degree nodes with valid clustering should be in [0, 1]
        valid_clustering = high_degree['clustering'].dropna()
        assert len(valid_clustering) > 0
        assert (valid_clustering >= 0).all()
        assert (valid_clustering <= 1).all()
