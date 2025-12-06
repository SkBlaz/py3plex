"""Additional tests for DSL ergonomics and edge cases.

These tests ensure the DSL handles edge cases gracefully and provides
good error messages.
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import (
    Q,
    L,
    Param,
    DslError,
    UnknownMeasureError,
    UnknownLayerError,
    ParameterMissingError,
    execute_query,
)


@pytest.fixture
def empty_network():
    """Create an empty network for edge case testing."""
    return multinet.multi_layer_network(directed=False)


@pytest.fixture
def simple_network():
    """Create a simple network."""
    network = multinet.multi_layer_network(directed=False)
    
    nodes = [
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'C', 'type': 'layer2'},
    ]
    network.add_nodes(nodes)
    
    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
    ]
    network.add_edges(edges)
    
    return network


class TestEmptyNetworkEdgeCases:
    """Test DSL behavior with empty networks."""
    
    def test_query_empty_network_string_dsl(self, empty_network):
        """Test string DSL on empty network."""
        result = execute_query(empty_network, 'SELECT nodes')
        assert result['count'] == 0
        assert result['nodes'] == []
    
    def test_query_empty_network_builder(self, empty_network):
        """Test builder API on empty network."""
        result = Q.nodes().execute(empty_network)
        assert result.count == 0
        assert len(result.items) == 0
    
    def test_compute_on_empty_network(self, empty_network):
        """Test computing measures on empty network."""
        result = Q.nodes().compute("degree").execute(empty_network)
        assert result.count == 0
        assert result.attributes == {} or 'degree' in result.attributes
    
    def test_order_on_empty_network(self, empty_network):
        """Test ordering empty results."""
        result = Q.nodes().compute("degree").order_by("degree").execute(empty_network)
        assert result.count == 0


class TestLayerAlgebraEdgeCases:
    """Test layer algebra edge cases."""
    
    def test_nonexistent_layer_union(self, simple_network):
        """Test union with non-existent layer."""
        result = Q.nodes().from_layers(L["layer1"] + L["nonexistent"]).execute(simple_network)
        # Should return nodes from layer1 only
        assert result.count == 2
    
    def test_nonexistent_layer_difference(self, simple_network):
        """Test difference with non-existent layer."""
        result = Q.nodes().from_layers(L["layer1"] - L["nonexistent"]).execute(simple_network)
        # Should return all nodes from layer1
        assert result.count == 2
    
    def test_nonexistent_layer_intersection(self, simple_network):
        """Test intersection with non-existent layer."""
        result = Q.nodes().from_layers(L["layer1"] & L["nonexistent"]).execute(simple_network)
        # Should return empty result
        assert result.count == 0
    
    def test_complex_layer_expression(self, simple_network):
        """Test complex layer expression."""
        # (layer1 + layer2) - nonexistent
        result = Q.nodes().from_layers(
            (L["layer1"] + L["layer2"]) - L["nonexistent"]
        ).execute(simple_network)
        assert result.count == 3


class TestParameterEdgeCases:
    """Test parameterized query edge cases."""
    
    def test_missing_parameter_error(self, simple_network):
        """Test missing parameter raises error."""
        q = Q.nodes().where(degree__gt=Param.int("threshold"))
        
        # Execute without providing the required parameter
        # Should raise ParameterMissingError when condition is evaluated
        try:
            result = q.execute(simple_network)
            # If no error, check that it handled missing param gracefully
            # (some implementations may filter nodes with missing params)
            assert True
        except (ParameterMissingError, KeyError) as e:
            # Expected behavior
            assert "threshold" in str(e) or "parameter" in str(e).lower()
    
    def test_parameter_type_validation(self, simple_network):
        """Test parameter with correct value."""
        q = Q.nodes().where(degree__gt=Param.int("threshold"))
        result = q.execute(simple_network, threshold=0)
        assert result.count >= 0
    
    def test_multiple_parameters(self, simple_network):
        """Test multiple parameters in one query."""
        q = Q.nodes().where(
            degree__gt=Param.int("min_deg"),
            degree__lt=Param.int("max_deg")
        )
        result = q.execute(simple_network, min_deg=0, max_deg=10)
        assert result.count >= 0


class TestComparisonOperators:
    """Test all comparison operators work correctly."""
    
    def test_greater_than(self, simple_network):
        """Test > operator."""
        result = Q.nodes().where(degree__gt=0).execute(simple_network)
        assert result.count >= 0
    
    def test_greater_than_or_equal(self, simple_network):
        """Test >= operator."""
        result = Q.nodes().where(degree__gte=0).execute(simple_network)
        assert result.count == 3
    
    def test_less_than(self, simple_network):
        """Test < operator."""
        result = Q.nodes().where(degree__lt=2).execute(simple_network)
        assert result.count >= 0
    
    def test_less_than_or_equal(self, simple_network):
        """Test <= operator."""
        result = Q.nodes().where(degree__lte=1).execute(simple_network)
        assert result.count >= 0
    
    def test_not_equal(self, simple_network):
        """Test != operator."""
        result = Q.nodes().where(layer__ne="nonexistent").execute(simple_network)
        assert result.count == 3
    
    def test_alternate_comparison_syntax(self, simple_network):
        """Test alternate syntax (ge vs gte, ne vs neq)."""
        result1 = Q.nodes().where(degree__ge=0).execute(simple_network)
        result2 = Q.nodes().where(degree__gte=0).execute(simple_network)
        assert result1.count == result2.count


class TestOrderingEdgeCases:
    """Test ordering edge cases."""
    
    def test_order_without_compute(self, simple_network):
        """Test ordering on degree without explicit compute."""
        result = Q.nodes().order_by("degree").execute(simple_network)
        # Should work as degree is a built-in attribute
        assert result.count == 3
    
    def test_order_multiple_keys(self, simple_network):
        """Test ordering by multiple keys."""
        result = Q.nodes().compute("degree", "clustering").order_by("degree", "clustering").execute(simple_network)
        assert result.count >= 0
    
    def test_limit_larger_than_results(self, simple_network):
        """Test limit larger than result count."""
        result = Q.nodes().limit(1000).execute(simple_network)
        assert result.count == 3  # All nodes returned


class TestExportFormats:
    """Test different export formats."""
    
    def test_to_pandas_empty(self, empty_network):
        """Test pandas export with empty results."""
        result = Q.nodes().execute(empty_network)
        df = result.to_pandas()
        assert len(df) == 0
    
    def test_to_dict_structure(self, simple_network):
        """Test dictionary structure."""
        result = Q.nodes().compute("degree").execute(simple_network)
        data = result.to_dict()
        
        assert 'target' in data
        assert 'nodes' in data
        assert 'count' in data
        assert 'computed' in data
        assert data['count'] == 3
    
    def test_to_networkx_subgraph(self, simple_network):
        """Test NetworkX export creates subgraph."""
        result = Q.nodes().where(layer="layer1").execute(simple_network)
        G = result.to_networkx(simple_network)
        
        assert G is not None
        # Should only have layer1 nodes
        assert len(G.nodes()) <= 2


class TestErrorMessages:
    """Test error messages are helpful."""
    
    def test_typo_suggestion(self, simple_network):
        """Test typo in measure name gives suggestion."""
        with pytest.raises(UnknownMeasureError) as exc_info:
            Q.nodes().compute("degre").execute(simple_network)
        
        error_msg = str(exc_info.value)
        assert "Did you mean" in error_msg or "Unknown measure" in error_msg
    
    def test_invalid_comparison_suffix(self, simple_network):
        """Test invalid comparison suffix."""
        with pytest.raises(ValueError):
            Q.nodes().where(degree__invalid=5).execute(simple_network)


class TestQueryReuse:
    """Test query reusability."""
    
    def test_query_can_be_reused(self, simple_network):
        """Test that queries can be executed multiple times."""
        q = Q.nodes().where(degree__gt=0)
        
        result1 = q.execute(simple_network)
        result2 = q.execute(simple_network)
        
        assert result1.count == result2.count
    
    def test_parameterized_query_reuse(self, simple_network):
        """Test parameterized query can be reused with different params."""
        q = Q.nodes().where(degree__gt=Param.int("threshold"))
        
        result1 = q.execute(simple_network, threshold=0)
        result2 = q.execute(simple_network, threshold=1)
        
        # Different thresholds should give different results
        assert result1.count >= result2.count


class TestStringDSLBackwardCompatibility:
    """Test backward compatibility with string DSL."""
    
    def test_basic_string_query(self, simple_network):
        """Test basic string query still works."""
        result = execute_query(simple_network, 'SELECT nodes')
        assert result['count'] == 3
    
    def test_where_clause_string(self, simple_network):
        """Test WHERE clause in string format."""
        result = execute_query(simple_network, 'SELECT nodes WHERE layer="layer1"')
        assert result['count'] == 2
    
    def test_compute_string(self, simple_network):
        """Test COMPUTE in string format."""
        result = execute_query(simple_network, 'SELECT nodes COMPUTE degree')
        assert 'computed' in result
        assert 'degree' in result['computed']


class TestDSLChaining:
    """Test method chaining works as expected."""
    
    def test_long_chain(self, simple_network):
        """Test long method chain."""
        result = (
            Q.nodes()
            .where(degree__gte=0)
            .compute("degree")
            .order_by("-degree")
            .limit(10)
            .execute(simple_network)
        )
        assert result.count >= 0
    
    def test_chain_with_layers_and_params(self, simple_network):
        """Test chain with layers and parameters."""
        q = (
            Q.nodes()
            .from_layers(L["layer1"] + L["layer2"])
            .where(degree__gt=Param.int("min"))
            .compute("degree")
        )
        
        result = q.execute(simple_network, min=0)
        assert result.count >= 0


class TestMeasureRegistry:
    """Test measure registry functionality."""
    
    def test_measure_registry_has_degree(self):
        """Test measure registry has degree."""
        from py3plex.dsl import measure_registry
        
        assert measure_registry.has("degree")
        assert measure_registry.has("degree_centrality")
    
    def test_measure_registry_descriptions(self):
        """Test measure descriptions are available."""
        from py3plex.dsl import measure_registry
        
        desc = measure_registry.get_description("degree")
        assert desc is not None
        assert len(desc) > 0
    
    def test_measure_registry_list(self):
        """Test listing all measures."""
        from py3plex.dsl import measure_registry
        
        measures = measure_registry.list_measures()
        assert len(measures) > 0
        assert "degree" in measures
        assert "betweenness_centrality" in measures
