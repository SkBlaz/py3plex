"""Tests for DSL Layer Set Algebra feature.

Tests cover:
- LayerSet creation and basic operations
- Set algebra operators (|, &, -, ~)
- String expression parsing
- Named layer groups
- Integration with DSL queries
- Property-based tests for algebra laws
"""

import pytest
from hypothesis import given, strategies as st, assume
from py3plex.core import multinet
from py3plex.dsl import Q, L, LayerSet
from py3plex.dsl.errors import DslSyntaxError, UnknownLayerError


@pytest.fixture
def sample_network():
    """Create a sample multilayer network for testing."""
    network = multinet.multi_layer_network(directed=False)
    
    nodes = [
        {'source': 'A', 'type': 'social'},
        {'source': 'B', 'type': 'social'},
        {'source': 'C', 'type': 'work'},
        {'source': 'D', 'type': 'work'},
        {'source': 'E', 'type': 'hobby'},
        {'source': 'F', 'type': 'coupling'},
    ]
    network.add_nodes(nodes)
    
    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'C', 'target': 'D', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'E', 'target': 'E', 'source_type': 'hobby', 'target_type': 'hobby'},
        {'source': 'F', 'target': 'A', 'source_type': 'coupling', 'target_type': 'social'},
    ]
    network.add_edges(edges)
    
    return network


class TestLayerSetConstruction:
    """Test LayerSet creation and basic properties."""
    
    def test_create_from_string(self):
        """Test creating LayerSet from layer name."""
        ls = LayerSet("social")
        assert ls.expr.kind == "term"
        assert ls.expr.value == "social"
    
    def test_create_wildcard(self):
        """Test creating wildcard LayerSet."""
        ls = LayerSet("*")
        assert ls.expr.kind == "term"
        assert ls.expr.value == "*"
    
    def test_repr(self):
        """Test string representation."""
        ls = LayerSet("social")
        assert "social" in repr(ls)


class TestLayerSetOperators:
    """Test set algebra operators."""
    
    def test_union_operator(self):
        """Test union: A | B."""
        a = LayerSet("social")
        b = LayerSet("work")
        c = a | b
        
        assert c.expr.kind == "union"
        assert c.expr.left.value == "social"
        assert c.expr.right.value == "work"
    
    def test_intersection_operator(self):
        """Test intersection: A & B."""
        a = LayerSet("social")
        b = LayerSet("work")
        c = a & b
        
        assert c.expr.kind == "intersection"
    
    def test_difference_operator(self):
        """Test difference: A - B."""
        a = LayerSet("social")
        b = LayerSet("work")
        c = a - b
        
        assert c.expr.kind == "difference"
    
    def test_complement_operator(self):
        """Test complement: ~A."""
        a = LayerSet("social")
        c = ~a
        
        assert c.expr.kind == "complement"
        assert c.expr.operand.value == "social"
    
    def test_complex_expression(self):
        """Test combining multiple operators."""
        a = LayerSet("social")
        b = LayerSet("work")
        c = LayerSet("hobby")
        
        # (A | B) & ~C
        result = (a | b) & ~c
        
        assert result.expr.kind == "intersection"


class TestLayerSetParsing:
    """Test string expression parsing."""
    
    def test_parse_single_layer(self):
        """Test parsing single layer name."""
        ls = LayerSet.parse("social")
        assert ls.expr.kind == "term"
        assert ls.expr.value == "social"
    
    def test_parse_wildcard(self):
        """Test parsing wildcard."""
        ls = LayerSet.parse("*")
        assert ls.expr.kind == "term"
        assert ls.expr.value == "*"
    
    def test_parse_union(self):
        """Test parsing union expression."""
        ls = LayerSet.parse("social | work")
        assert ls.expr.kind == "union"
        assert ls.expr.left.value == "social"
        assert ls.expr.right.value == "work"
    
    def test_parse_union_alt_syntax(self):
        """Test parsing union with + operator."""
        ls = LayerSet.parse("social + work")
        assert ls.expr.kind == "union"
    
    def test_parse_intersection(self):
        """Test parsing intersection expression."""
        ls = LayerSet.parse("social & work")
        assert ls.expr.kind == "intersection"
    
    def test_parse_difference(self):
        """Test parsing difference expression."""
        ls = LayerSet.parse("social - work")
        assert ls.expr.kind == "difference"
    
    def test_parse_complement(self):
        """Test parsing complement expression."""
        ls = LayerSet.parse("~social")
        assert ls.expr.kind == "complement"
        assert ls.expr.operand.value == "social"
    
    def test_parse_parentheses(self):
        """Test parsing with parentheses."""
        ls = LayerSet.parse("(social | work) & hobby")
        assert ls.expr.kind == "intersection"
        assert ls.expr.left.kind == "union"
    
    def test_parse_complex_expression(self):
        """Test parsing complex expression."""
        ls = LayerSet.parse("* - coupling - transport")
        assert ls.expr.kind == "difference"
    
    def test_parse_nested_parentheses(self):
        """Test parsing nested parentheses."""
        ls = LayerSet.parse("((a | b) & c) - d")
        # Should parse without error
        assert ls.expr is not None
    
    def test_parse_empty_raises_error(self):
        """Test that empty expression raises error."""
        with pytest.raises(DslSyntaxError):
            LayerSet.parse("")
    
    def test_parse_invalid_syntax_raises_error(self):
        """Test that invalid syntax raises error."""
        with pytest.raises(DslSyntaxError):
            LayerSet.parse("social &")  # Missing right operand
    
    def test_parse_unmatched_paren_raises_error(self):
        """Test that unmatched parenthesis raises error."""
        with pytest.raises(DslSyntaxError):
            LayerSet.parse("(social | work")


class TestLayerSetResolution:
    """Test resolving layer expressions against networks."""
    
    def test_resolve_single_layer(self, sample_network):
        """Test resolving single layer."""
        ls = LayerSet("social")
        result = ls.resolve(sample_network)
        assert result == {"social"}
    
    def test_resolve_wildcard(self, sample_network):
        """Test resolving wildcard to all layers."""
        ls = LayerSet("*")
        result = ls.resolve(sample_network)
        assert result == {"social", "work", "hobby", "coupling"}
    
    def test_resolve_union(self, sample_network):
        """Test resolving union."""
        ls = LayerSet("social") | LayerSet("work")
        result = ls.resolve(sample_network)
        assert result == {"social", "work"}
    
    def test_resolve_intersection(self, sample_network):
        """Test resolving intersection."""
        # Create an intersection that results in empty set
        a = LayerSet("social") | LayerSet("work")
        b = LayerSet("hobby") | LayerSet("coupling")
        ls = a & b
        result = ls.resolve(sample_network, warn_empty=False)
        assert result == set()
    
    def test_resolve_difference(self, sample_network):
        """Test resolving difference."""
        ls = LayerSet("*") - LayerSet("coupling")
        result = ls.resolve(sample_network)
        assert result == {"social", "work", "hobby"}
    
    def test_resolve_complement(self, sample_network):
        """Test resolving complement."""
        ls = ~LayerSet("coupling")
        result = ls.resolve(sample_network)
        assert result == {"social", "work", "hobby"}
    
    def test_resolve_complex_expression(self, sample_network):
        """Test resolving complex expression."""
        # (social | work) - coupling
        ls = (LayerSet("social") | LayerSet("work")) - LayerSet("coupling")
        result = ls.resolve(sample_network)
        assert result == {"social", "work"}
    
    def test_resolve_parsed_expression(self, sample_network):
        """Test resolving parsed string expression."""
        ls = LayerSet.parse("* - coupling")
        result = ls.resolve(sample_network)
        assert result == {"social", "work", "hobby"}
    
    def test_resolve_unknown_layer_non_strict(self, sample_network):
        """Test resolving unknown layer in non-strict mode (default)."""
        ls = LayerSet("nonexistent")
        result = ls.resolve(sample_network, strict=False, warn_empty=False)
        assert result == set()
    
    def test_resolve_unknown_layer_strict(self, sample_network):
        """Test resolving unknown layer in strict mode raises error."""
        ls = LayerSet("nonexistent")
        with pytest.raises(UnknownLayerError):
            ls.resolve(sample_network, strict=True)
    
    def test_resolve_warns_on_empty(self, sample_network):
        """Test that empty result triggers warning."""
        ls = LayerSet("nonexistent")
        with pytest.warns(UserWarning, match="empty set"):
            ls.resolve(sample_network, strict=False, warn_empty=True)


class TestLayerSetExplain:
    """Test LayerSet introspection and explanation."""
    
    def test_explain_single_layer(self):
        """Test explaining single layer."""
        ls = LayerSet("social")
        explanation = ls.explain()
        assert "social" in explanation
        assert "layer" in explanation
    
    def test_explain_wildcard(self):
        """Test explaining wildcard."""
        ls = LayerSet("*")
        explanation = ls.explain()
        assert "*" in explanation
        assert "all_layers" in explanation
    
    def test_explain_union(self):
        """Test explaining union."""
        ls = LayerSet("social") | LayerSet("work")
        explanation = ls.explain()
        assert "union" in explanation
        assert "social" in explanation
        assert "work" in explanation
    
    def test_explain_with_network(self, sample_network):
        """Test explaining with network resolution."""
        ls = LayerSet("*") - LayerSet("coupling")
        explanation = ls.explain(sample_network)
        assert "difference" in explanation
        assert "resolved to" in explanation
        # Should show the resolved layers
        assert "social" in explanation or "work" in explanation


class TestNamedLayerGroups:
    """Test named layer group functionality."""
    
    def setup_method(self):
        """Clear groups before each test."""
        LayerSet.clear_groups()
    
    def teardown_method(self):
        """Clear groups after each test."""
        LayerSet.clear_groups()
    
    def test_define_group(self):
        """Test defining a named group."""
        bio = LayerSet("ppi") | LayerSet("gene")
        LayerSet.define_group("bio", bio)
        
        groups = LayerSet.list_groups()
        assert "bio" in groups
    
    def test_reference_group(self, sample_network):
        """Test referencing a defined group."""
        # Define group
        LayerSet.define_group("core", LayerSet("social") | LayerSet("work"))
        
        # Reference in new expression
        ls = LayerSet("core")
        result = ls.resolve(sample_network)
        assert result == {"social", "work"}
    
    def test_group_in_expression(self, sample_network):
        """Test using group in complex expression."""
        LayerSet.define_group("core", LayerSet("social") | LayerSet("work"))
        
        # Use group in expression
        ls = LayerSet.parse("core & work")
        result = ls.resolve(sample_network)
        assert result == {"work"}
    
    def test_list_groups(self):
        """Test listing all groups."""
        LayerSet.define_group("group1", LayerSet("a"))
        LayerSet.define_group("group2", LayerSet("b"))
        
        groups = LayerSet.list_groups()
        assert len(groups) == 2
        assert "group1" in groups
        assert "group2" in groups
    
    def test_clear_groups(self):
        """Test clearing all groups."""
        LayerSet.define_group("group1", LayerSet("a"))
        LayerSet.clear_groups()
        
        groups = LayerSet.list_groups()
        assert len(groups) == 0
    
    def test_l_define_method(self, sample_network):
        """Test L.define() convenience method."""
        bio = LayerSet("social") | LayerSet("work")
        L.define("bio", bio)
        
        # Use the defined group
        ls = LayerSet("bio")
        result = ls.resolve(sample_network)
        assert result == {"social", "work"}


class TestLayerProxyIntegration:
    """Test integration with LayerProxy (L) syntax."""
    
    def test_l_simple_name(self):
        """Test L["name"] for simple layer name."""
        result = L["social"]
        # Should return LayerExprBuilder for backward compatibility
        assert hasattr(result, '_to_ast')
    
    def test_l_expression_string(self):
        """Test L["expr"] for expression strings."""
        result = L["* - coupling"]
        # Should return LayerSet
        assert isinstance(result, LayerSet)
    
    def test_l_with_operators(self):
        """Test L["a | b"] with operators."""
        result = L["social | work"]
        assert isinstance(result, LayerSet)
        assert result.expr.kind == "union"
    
    def test_l_with_parentheses(self):
        """Test L["(a | b) & c"] with parentheses."""
        result = L["(social | work) & hobby"]
        assert isinstance(result, LayerSet)
        assert result.expr.kind == "intersection"
    
    def test_l_multiple_names(self):
        """Test L["a", "b"] for multiple names (backward compat)."""
        result = L["social", "work"]
        # Should return LayerExprBuilder for backward compatibility
        assert hasattr(result, '_to_ast')


class TestDSLIntegration:
    """Test integration with DSL queries."""
    
    def test_from_layers_with_layer_set(self, sample_network):
        """Test from_layers() with LayerSet."""
        result = (
            Q.nodes()
             .from_layers(L["* - coupling"])
             .execute(sample_network)
        )
        
        df = result.to_pandas()
        layers = set(df['layer'].unique())
        assert layers == {"social", "work", "hobby"}
    
    def test_from_layers_with_union(self, sample_network):
        """Test from_layers() with union expression."""
        result = (
            Q.nodes()
             .from_layers(L["social | work"])
             .execute(sample_network)
        )
        
        df = result.to_pandas()
        layers = set(df['layer'].unique())
        assert layers == {"social", "work"}
    
    def test_from_layers_with_parsed_expression(self, sample_network):
        """Test from_layers() with parsed expression."""
        ls = LayerSet.parse("(social | work) & work")
        result = (
            Q.nodes()
             .from_layers(ls)
             .execute(sample_network)
        )
        
        df = result.to_pandas()
        assert all(df['layer'] == 'work')
    
    def test_backward_compatibility_old_style(self, sample_network):
        """Test that old L["a"] + L["b"] style still works."""
        result = (
            Q.nodes()
             .from_layers(L["social"] + L["work"])
             .execute(sample_network)
        )
        
        df = result.to_pandas()
        layers = set(df['layer'].unique())
        assert layers == {"social", "work"}
    
    def test_with_compute(self, sample_network):
        """Test LayerSet with compute() clause."""
        result = (
            Q.nodes()
             .from_layers(L["* - coupling"])
             .compute("degree")
             .execute(sample_network)
        )
        
        df = result.to_pandas()
        assert 'degree' in df.columns
        assert "coupling" not in df['layer'].values


class TestPropertyBasedAlgebra:
    """Property-based tests for algebra laws."""
    
    @given(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))))
    def test_idempotence_union(self, layer_name):
        """Test A | A = A (idempotence of union)."""
        # Create a test network with the layer
        network = multinet.multi_layer_network(directed=False)
        network.add_nodes([{'source': 'X', 'type': layer_name}])
        
        a = LayerSet(layer_name)
        result = a | a
        
        resolved_a = a.resolve(network, warn_empty=False)
        resolved_result = result.resolve(network, warn_empty=False)
        
        assert resolved_a == resolved_result
    
    @given(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))))
    def test_idempotence_intersection(self, layer_name):
        """Test A & A = A (idempotence of intersection)."""
        network = multinet.multi_layer_network(directed=False)
        network.add_nodes([{'source': 'X', 'type': layer_name}])
        
        a = LayerSet(layer_name)
        result = a & a
        
        resolved_a = a.resolve(network, warn_empty=False)
        resolved_result = result.resolve(network, warn_empty=False)
        
        assert resolved_a == resolved_result
    
    def test_commutativity_union(self, sample_network):
        """Test A | B = B | A (commutativity of union)."""
        a = LayerSet("social")
        b = LayerSet("work")
        
        ab = a | b
        ba = b | a
        
        assert ab.resolve(sample_network) == ba.resolve(sample_network)
    
    def test_commutativity_intersection(self, sample_network):
        """Test A & B = B & A (commutativity of intersection)."""
        a = LayerSet("social")
        b = LayerSet("work")
        
        ab = a & b
        ba = b & a
        
        assert ab.resolve(sample_network) == ba.resolve(sample_network)
    
    def test_associativity_union(self, sample_network):
        """Test (A | B) | C = A | (B | C) (associativity of union)."""
        a = LayerSet("social")
        b = LayerSet("work")
        c = LayerSet("hobby")
        
        left = (a | b) | c
        right = a | (b | c)
        
        assert left.resolve(sample_network) == right.resolve(sample_network)
    
    def test_associativity_intersection(self, sample_network):
        """Test (A & B) & C = A & (B & C) (associativity of intersection)."""
        # Use all layers then intersect to test
        a = LayerSet("*")
        b = LayerSet("*")
        c = LayerSet("*")
        
        left = (a & b) & c
        right = a & (b & c)
        
        assert left.resolve(sample_network) == right.resolve(sample_network)
    
    def test_difference_self_is_empty(self, sample_network):
        """Test A - A = ∅ (difference with self is empty)."""
        a = LayerSet("social")
        result = a - a
        
        resolved = result.resolve(sample_network, warn_empty=False)
        assert resolved == set()
    
    def test_union_with_complement_is_all(self, sample_network):
        """Test A | ~A = * (union with complement is universe)."""
        a = LayerSet("social")
        result = a | ~a
        
        resolved = result.resolve(sample_network)
        all_layers = LayerSet("*").resolve(sample_network)
        
        assert resolved == all_layers
    
    def test_distributivity_intersection_over_union(self, sample_network):
        """Test A & (B | C) = (A & B) | (A & C) (distributivity)."""
        a = LayerSet("*")  # All layers
        b = LayerSet("social")
        c = LayerSet("work")
        
        left = a & (b | c)
        right = (a & b) | (a & c)
        
        assert left.resolve(sample_network) == right.resolve(sample_network)
    
    def test_de_morgan_union(self, sample_network):
        """Test ~(A | B) = ~A & ~B (De Morgan's law for union)."""
        a = LayerSet("social")
        b = LayerSet("work")
        
        left = ~(a | b)
        right = ~a & ~b
        
        assert left.resolve(sample_network) == right.resolve(sample_network)
    
    def test_de_morgan_intersection(self, sample_network):
        """Test ~(A & B) = ~A | ~B (De Morgan's law for intersection)."""
        a = LayerSet("social")
        b = LayerSet("work")
        
        left = ~(a & b)
        right = ~a | ~b
        
        assert left.resolve(sample_network) == right.resolve(sample_network)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
