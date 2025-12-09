"""Tests for DSL layer selection clarification (Feature 1).

Tests cover:
- FROM layer="..." as the canonical layer selection method
- WHERE layer="..." backward compatibility
- Equivalence between FROM and WHERE layer selection
- Builder API from_layers() consistency
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import execute_query, Q, L


@pytest.fixture
def sample_network():
    """Create a sample multilayer network for testing."""
    network = multinet.multi_layer_network(directed=False)
    
    nodes = [
        {'source': 'A', 'type': 'social'},
        {'source': 'B', 'type': 'social'},
        {'source': 'C', 'type': 'social'},
        {'source': 'D', 'type': 'work'},
        {'source': 'E', 'type': 'work'},
        {'source': 'F', 'type': 'hobbies'},
    ]
    network.add_nodes(nodes)
    
    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'B', 'target': 'C', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'D', 'target': 'E', 'source_type': 'work', 'target_type': 'work'},
    ]
    network.add_edges(edges)
    
    return network


class TestFromLayerSyntax:
    """Test the canonical FROM layer="..." syntax."""
    
    def test_from_layer_basic(self, sample_network):
        """Test basic FROM layer selection."""
        result = execute_query(sample_network, 'SELECT nodes FROM layer="social"')
        
        nodes = result['nodes']
        assert len(nodes) == 3
        assert all(layer == 'social' for _, layer in nodes)
    
    def test_from_layer_with_where(self, sample_network):
        """Test FROM layer with additional WHERE conditions."""
        result = execute_query(
            sample_network,
            'SELECT nodes FROM layer="social" WHERE layer="social"'
        )
        
        nodes = result['nodes']
        # Should only get social layer nodes
        assert len(nodes) == 3
        assert all(layer == 'social' for _, layer in nodes)
    
    def test_from_layer_with_compute(self, sample_network):
        """Test FROM layer with COMPUTE."""
        result = execute_query(
            sample_network,
            'SELECT nodes FROM layer="social" COMPUTE degree, clustering'
        )
        
        computed = result.get('computed', {})
        assert 'degree' in computed
        assert 'clustering' in computed
    
    def test_from_layer_work(self, sample_network):
        """Test FROM layer with work layer."""
        result = execute_query(sample_network, 'SELECT nodes FROM layer="work"')
        
        nodes = result['nodes']
        assert len(nodes) == 2
        assert all(layer == 'work' for _, layer in nodes)


class TestWhereLayerBackwardCompatibility:
    """Test that WHERE layer="..." still works for backward compatibility."""
    
    def test_where_layer_basic(self, sample_network):
        """Test WHERE layer selection (backward compat)."""
        result = execute_query(sample_network, 'SELECT nodes WHERE layer="social"')
        
        nodes = result['nodes']
        assert len(nodes) == 3
        assert all(layer == 'social' for _, layer in nodes)
    
    def test_where_layer_with_condition(self, sample_network):
        """Test WHERE layer with additional conditions."""
        result = execute_query(
            sample_network,
            'SELECT nodes WHERE layer="social" AND layer="social"'
        )
        
        nodes = result['nodes']
        assert len(nodes) == 3
        assert all(layer == 'social' for _, layer in nodes)
    
    def test_where_layer_with_compute(self, sample_network):
        """Test WHERE layer with COMPUTE."""
        result = execute_query(
            sample_network,
            'SELECT nodes WHERE layer="work" COMPUTE degree'
        )
        
        nodes = result['nodes']
        assert len(nodes) == 2
        assert all(layer == 'work' for _, layer in nodes)
        assert 'degree' in result.get('computed', {})


class TestFromWhereEquivalence:
    """Test that FROM layer and WHERE layer produce equivalent results."""
    
    def test_basic_equivalence(self, sample_network):
        """Test that FROM and WHERE layer produce same results."""
        result_from = execute_query(sample_network, 'SELECT nodes FROM layer="social"')
        result_where = execute_query(sample_network, 'SELECT nodes WHERE layer="social"')
        
        assert result_from['nodes'] == result_where['nodes']
    
    def test_with_compute_equivalence(self, sample_network):
        """Test equivalence with COMPUTE."""
        result_from = execute_query(
            sample_network,
            'SELECT nodes FROM layer="social" COMPUTE degree'
        )
        result_where = execute_query(
            sample_network,
            'SELECT nodes WHERE layer="social" COMPUTE degree'
        )
        
        assert result_from['nodes'] == result_where['nodes']
        assert set(result_from.get('computed', {}).keys()) == set(result_where.get('computed', {}).keys())
    
    def test_with_where_condition_equivalence(self, sample_network):
        """Test equivalence with additional WHERE conditions."""
        result_from = execute_query(
            sample_network,
            'SELECT nodes FROM layer="social" WHERE layer="social"'
        )
        result_where = execute_query(
            sample_network,
            'SELECT nodes WHERE layer="social" AND layer="social"'
        )
        
        assert result_from['nodes'] == result_where['nodes']
    
    def test_work_layer_equivalence(self, sample_network):
        """Test equivalence for work layer."""
        result_from = execute_query(sample_network, 'SELECT nodes FROM layer="work"')
        result_where = execute_query(sample_network, 'SELECT nodes WHERE layer="work"')
        
        assert result_from['nodes'] == result_where['nodes']


class TestBuilderAPIConsistency:
    """Test that builder API from_layers() is consistent with string DSL."""
    
    def test_from_layers_basic(self, sample_network):
        """Test from_layers() matches string DSL."""
        # Builder API
        result_builder = Q.nodes().from_layers(L["social"]).execute(sample_network)
        df_builder = result_builder.to_pandas()
        
        # String DSL with FROM
        result_string = execute_query(sample_network, 'SELECT nodes FROM layer="social"')
        
        # Should have same nodes
        assert len(df_builder) == len(result_string['nodes'])
        assert all(df_builder['layer'] == 'social')
    
    def test_from_layers_with_where(self, sample_network):
        """Test from_layers() with where() filter."""
        result = (
            Q.nodes()
             .from_layers(L["social"])
             .where(layer="social")  # Redundant but tests combination
             .execute(sample_network)
        )
        
        df = result.to_pandas()
        assert all(df['layer'] == 'social')
        assert len(df) == 3
    
    def test_from_layers_with_compute(self, sample_network):
        """Test from_layers() with compute()."""
        result = (
            Q.nodes()
             .from_layers(L["social"])
             .compute("degree")
             .execute(sample_network)
        )
        
        df = result.to_pandas()
        assert 'degree' in df.columns
        assert all(df['layer'] == 'social')
    
    def test_from_layers_work_layer(self, sample_network):
        """Test from_layers() with work layer."""
        result = Q.nodes().from_layers(L["work"]).execute(sample_network)
        df = result.to_pandas()
        
        assert all(df['layer'] == 'work')
        assert len(df) == 2


class TestEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_nonexistent_layer(self, sample_network):
        """Test selecting from a layer that doesn't exist."""
        result = execute_query(sample_network, 'SELECT nodes FROM layer="nonexistent"')
        
        assert len(result['nodes']) == 0
    
    def test_empty_layer_name(self, sample_network):
        """Test with empty layer name."""
        result = execute_query(sample_network, 'SELECT nodes FROM layer=""')
        
        assert len(result['nodes']) == 0
    
    def test_multiple_layers_in_where(self, sample_network):
        """Test WHERE with multiple layer conditions."""
        # This tests that WHERE layer still works with OR
        result = execute_query(
            sample_network,
            'SELECT nodes WHERE layer="social" OR layer="work"'
        )
        
        nodes = result['nodes']
        # Should get nodes from both layers
        assert len(nodes) == 5  # 3 social + 2 work


class TestDocumentationExamples:
    """Test examples that should appear in documentation."""
    
    def test_doc_example_1(self, sample_network):
        """Canonical way: FROM layer for layer selection."""
        result = execute_query(
            sample_network,
            'SELECT nodes FROM layer="social" WHERE layer="social" COMPUTE betweenness_centrality'
        )
        
        assert len(result['nodes']) > 0
        assert 'betweenness_centrality' in result.get('computed', {})
    
    def test_doc_example_2(self, sample_network):
        """Builder API equivalent."""
        result = (
            Q.nodes()
             .from_layers(L["social"])
             .compute("betweenness_centrality")
             .execute(sample_network)
        )
        
        df = result.to_pandas()
        assert 'betweenness_centrality' in df.columns
        assert all(df['layer'] == 'social')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
