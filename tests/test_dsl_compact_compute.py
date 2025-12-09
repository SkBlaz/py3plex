"""Tests for DSL compact COMPUTE syntax (Feature 2).

Tests cover:
- Comma-separated metrics in COMPUTE clause
- Repeated COMPUTE clauses
- Mixed forms (comma-separated and repeated)
- Backward compatibility with space-separated metrics
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import execute_query, Q


@pytest.fixture
def sample_network():
    """Create a sample network for testing."""
    network = multinet.multi_layer_network(directed=False)
    
    nodes = [
        {'source': 'A', 'type': 'social'},
        {'source': 'B', 'type': 'social'},
        {'source': 'C', 'type': 'social'},
        {'source': 'D', 'type': 'work'},
    ]
    network.add_nodes(nodes)
    
    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'B', 'target': 'C', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'A', 'target': 'C', 'source_type': 'social', 'target_type': 'social'},
    ]
    network.add_edges(edges)
    
    return network


class TestCompactComputeSyntax:
    """Test compact COMPUTE syntax in string DSL."""
    
    def test_comma_separated_metrics(self, sample_network):
        """Test comma-separated metrics in COMPUTE clause."""
        result = execute_query(
            sample_network,
            'SELECT nodes WHERE layer="social" COMPUTE degree, betweenness_centrality, clustering'
        )
        
        computed = result.get('computed', {})
        assert 'degree' in computed
        assert 'betweenness_centrality' in computed
        assert 'clustering' in computed
    
    def test_comma_separated_with_spaces(self, sample_network):
        """Test comma-separated with extra spaces."""
        result = execute_query(
            sample_network,
            'SELECT nodes WHERE layer="social" COMPUTE degree , betweenness_centrality , clustering'
        )
        
        computed = result.get('computed', {})
        assert 'degree' in computed
        assert 'betweenness_centrality' in computed
        assert 'clustering' in computed
    
    def test_space_separated_still_works(self, sample_network):
        """Test that space-separated metrics still work (backward compatibility)."""
        result = execute_query(
            sample_network,
            'SELECT nodes WHERE layer="social" COMPUTE degree betweenness_centrality'
        )
        
        computed = result.get('computed', {})
        assert 'degree' in computed
        assert 'betweenness_centrality' in computed
    
    def test_repeated_compute_clauses(self, sample_network):
        """Test repeated COMPUTE clauses."""
        result = execute_query(
            sample_network,
            'SELECT nodes WHERE layer="social" COMPUTE degree COMPUTE betweenness_centrality COMPUTE clustering'
        )
        
        computed = result.get('computed', {})
        assert 'degree' in computed
        assert 'betweenness_centrality' in computed
        assert 'clustering' in computed
    
    def test_mixed_comma_and_repeated(self, sample_network):
        """Test mixing comma-separated and repeated COMPUTE."""
        result = execute_query(
            sample_network,
            'SELECT nodes WHERE layer="social" COMPUTE degree, clustering COMPUTE betweenness_centrality'
        )
        
        computed = result.get('computed', {})
        assert 'degree' in computed
        assert 'clustering' in computed
        assert 'betweenness_centrality' in computed
    
    def test_single_metric_still_works(self, sample_network):
        """Test single metric in COMPUTE (most common case)."""
        result = execute_query(
            sample_network,
            'SELECT nodes WHERE layer="social" COMPUTE degree'
        )
        
        computed = result.get('computed', {})
        assert 'degree' in computed
        assert len(computed) == 1


class TestBuilderAPIMultipleMetrics:
    """Test that builder API supports multiple metrics (should already work)."""
    
    def test_multiple_metrics_builder(self, sample_network):
        """Test builder API with multiple metrics."""
        result = (
            Q.nodes()
             .where(layer="social")
             .compute("degree", "betweenness_centrality", "clustering")
             .execute(sample_network)
        )
        
        df = result.to_pandas()
        assert 'degree' in df.columns
        assert 'betweenness_centrality' in df.columns
        assert 'clustering' in df.columns
    
    def test_multiple_compute_calls_builder(self, sample_network):
        """Test multiple compute() calls in builder API."""
        result = (
            Q.nodes()
             .where(layer="social")
             .compute("degree")
             .compute("betweenness_centrality")
             .compute("clustering")
             .execute(sample_network)
        )
        
        df = result.to_pandas()
        assert 'degree' in df.columns
        assert 'betweenness_centrality' in df.columns
        assert 'clustering' in df.columns
    
    def test_single_metric_builder(self, sample_network):
        """Test single metric in builder API."""
        result = (
            Q.nodes()
             .where(layer="social")
             .compute("degree")
             .execute(sample_network)
        )
        
        df = result.to_pandas()
        assert 'degree' in df.columns


class TestComputeSerializeToString:
    """Test that builder API serializes to compact string DSL."""
    
    def test_serialize_multiple_metrics(self):
        """Test that multiple metrics serialize to comma-separated form."""
        q = Q.nodes().compute("degree", "betweenness_centrality", "clustering")
        dsl_string = q.to_dsl()
        
        # Should use comma-separated form
        assert "COMPUTE degree, betweenness_centrality, clustering" in dsl_string
    
    def test_serialize_single_metric(self):
        """Test that single metric serializes correctly."""
        q = Q.nodes().compute("degree")
        dsl_string = q.to_dsl()
        
        assert "COMPUTE degree" in dsl_string


class TestEquivalence:
    """Test that all forms produce equivalent results."""
    
    def test_all_forms_equivalent(self, sample_network):
        """Test that comma-separated, space-separated, and repeated forms are equivalent."""
        # Comma-separated
        result1 = execute_query(
            sample_network,
            'SELECT nodes WHERE layer="social" COMPUTE degree, betweenness_centrality'
        )
        
        # Space-separated
        result2 = execute_query(
            sample_network,
            'SELECT nodes WHERE layer="social" COMPUTE degree betweenness_centrality'
        )
        
        # Repeated
        result3 = execute_query(
            sample_network,
            'SELECT nodes WHERE layer="social" COMPUTE degree COMPUTE betweenness_centrality'
        )
        
        # Builder API
        result4 = (
            Q.nodes()
             .where(layer="social")
             .compute("degree", "betweenness_centrality")
             .execute(sample_network)
        )
        
        # All should compute the same measures
        computed1 = set(result1.get('computed', {}).keys())
        computed2 = set(result2.get('computed', {}).keys())
        computed3 = set(result3.get('computed', {}).keys())
        
        assert computed1 == computed2 == computed3
        assert computed1 == {'degree', 'betweenness_centrality'}
        
        # Builder API result should have the same columns
        df4 = result4.to_pandas()
        assert 'degree' in df4.columns
        assert 'betweenness_centrality' in df4.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
