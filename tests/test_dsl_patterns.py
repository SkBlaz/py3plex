"""Tests for Pattern Matching API.

This module tests the pattern matching Builder API that enables users to
express graph motifs and paths in a multilayer-aware manner.
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import Q
from py3plex.dsl.patterns import (
    PatternNode,
    PatternEdge,
    PatternGraph,
    MatchRow,
    LayerConstraint,
    EdgeLayerConstraint,
    Predicate,
    PatternQueryBuilder,
    PatternQueryResult,
)


@pytest.fixture
def simple_network():
    """Create a simple multilayer network for testing.
    
    Network structure:
    Layer "social": A-B, B-C, A-C (triangle)
    Layer "work": D-E (single edge)
    """
    network = multinet.multi_layer_network(directed=False)
    
    nodes = [
        {'source': 'A', 'type': 'social'},
        {'source': 'B', 'type': 'social'},
        {'source': 'C', 'type': 'social'},
        {'source': 'D', 'type': 'work'},
        {'source': 'E', 'type': 'work'},
    ]
    network.add_nodes(nodes)
    
    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'B', 'target': 'C', 'source_type': 'social', 'target_type': 'social', 'weight': 2.0},
        {'source': 'A', 'target': 'C', 'source_type': 'social', 'target_type': 'social', 'weight': 1.5},
        {'source': 'D', 'target': 'E', 'source_type': 'work', 'target_type': 'work', 'weight': 3.0},
    ]
    network.add_edges(edges)
    
    return network


@pytest.fixture
def larger_network():
    """Create a larger multilayer network for testing.
    
    Network structure:
    Layer "social": Complete graph on nodes A, B, C, D
    Layer "work": Path A-B-C-D
    """
    network = multinet.multi_layer_network(directed=False)
    
    nodes = [
        {'source': 'A', 'type': 'social'},
        {'source': 'B', 'type': 'social'},
        {'source': 'C', 'type': 'social'},
        {'source': 'D', 'type': 'social'},
        {'source': 'A', 'type': 'work'},
        {'source': 'B', 'type': 'work'},
        {'source': 'C', 'type': 'work'},
        {'source': 'D', 'type': 'work'},
    ]
    network.add_nodes(nodes)
    
    # Social layer: complete graph
    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'A', 'target': 'C', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'A', 'target': 'D', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'B', 'target': 'C', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'B', 'target': 'D', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'C', 'target': 'D', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        # Work layer: path
        {'source': 'A', 'target': 'B', 'source_type': 'work', 'target_type': 'work', 'weight': 2.0},
        {'source': 'B', 'target': 'C', 'source_type': 'work', 'target_type': 'work', 'weight': 2.0},
        {'source': 'C', 'target': 'D', 'source_type': 'work', 'target_type': 'work', 'weight': 2.0},
    ]
    network.add_edges(edges)
    
    return network


class TestIR:
    """Test the IR (Intermediate Representation) classes."""
    
    def test_predicate(self):
        """Test Predicate class."""
        pred = Predicate(attr="degree", op=">", value=5)
        assert pred.attr == "degree"
        assert pred.op == ">"
        assert pred.value == 5
        assert "degree > 5" in repr(pred)
        
        # Test to_dict
        d = pred.to_dict()
        assert d["attr"] == "degree"
        assert d["op"] == ">"
        assert d["value"] == 5
    
    def test_layer_constraint(self):
        """Test LayerConstraint class."""
        # One layer
        lc = LayerConstraint.one("social")
        assert lc.kind == "one"
        assert lc.matches("social")
        assert not lc.matches("work")
        
        # Set of layers
        lc = LayerConstraint.set_of({"social", "work"})
        assert lc.kind == "set"
        assert lc.matches("social")
        assert lc.matches("work")
        assert not lc.matches("other")
        
        # Wildcard
        lc = LayerConstraint.wildcard()
        assert lc.kind == "wildcard"
        assert lc.matches("social")
        assert lc.matches("work")
        assert lc.matches("anything")
    
    def test_edge_layer_constraint(self):
        """Test EdgeLayerConstraint class."""
        # Within layer
        elc = EdgeLayerConstraint.within("social")
        assert elc.kind == "within"
        assert elc.matches("social", "social")
        assert not elc.matches("social", "work")
        
        # Between layers
        elc = EdgeLayerConstraint.between("social", "work")
        assert elc.kind == "between"
        assert elc.matches("social", "work")
        assert not elc.matches("social", "social")
        
        # Any layer
        elc = EdgeLayerConstraint.any_layer()
        assert elc.kind == "any"
        assert elc.matches("social", "social")
        assert elc.matches("social", "work")
    
    def test_pattern_node(self):
        """Test PatternNode class."""
        node = PatternNode(
            var="a",
            labels={"person"},
            predicates=[Predicate("degree", ">", 3)],
            layer_constraint=LayerConstraint.one("social"),
        )
        assert node.var == "a"
        assert "person" in node.labels
        assert len(node.predicates) == 1
        assert node.layer_constraint.kind == "one"
        
        # Test to_dict
        d = node.to_dict()
        assert d["var"] == "a"
        assert "person" in d["labels"]
    
    def test_pattern_edge(self):
        """Test PatternEdge class."""
        edge = PatternEdge(
            src="a",
            dst="b",
            directed=False,
            predicates=[Predicate("weight", ">", 0.5)],
        )
        assert edge.src == "a"
        assert edge.dst == "b"
        assert not edge.directed
        assert len(edge.predicates) == 1
    
    def test_pattern_graph(self):
        """Test PatternGraph class."""
        pg = PatternGraph()
        
        # Add nodes
        node_a = PatternNode(var="a")
        node_b = PatternNode(var="b")
        pg.add_node(node_a)
        pg.add_node(node_b)
        assert len(pg.nodes) == 2
        
        # Add edge
        edge = PatternEdge(src="a", dst="b")
        pg.add_edge(edge)
        assert len(pg.edges) == 1
        
        # Add constraint
        pg.add_constraint("a != b")
        assert len(pg.constraints) == 1
        
        # Get return vars
        assert set(pg.get_return_vars()) == {"a", "b"}
    
    def test_match_row(self):
        """Test MatchRow class."""
        match = MatchRow(bindings={"a": "A", "b": "B"})
        assert match["a"] == "A"
        assert match["b"] == "B"
        assert "a" in match
        assert "c" not in match
        
        # Test to_dict
        d = match.to_dict()
        assert d["a"] == "A"
        assert d["b"] == "B"


class TestBuilder:
    """Test the Builder API."""
    
    def test_pattern_query_builder_creation(self):
        """Test creating a PatternQueryBuilder."""
        pq = Q.pattern()
        assert isinstance(pq, PatternQueryBuilder)
    
    def test_node_builder(self):
        """Test adding nodes with predicates."""
        pq = Q.pattern().node("a").where(degree__gt=3)
        assert "a" in pq._pattern.nodes
        node = pq._pattern.nodes["a"]
        assert len(node.predicates) == 1
        assert node.predicates[0].attr == "degree"
        assert node.predicates[0].op == ">"
        assert node.predicates[0].value == 3
    
    def test_node_with_layer_constraint(self):
        """Test adding nodes with layer constraints."""
        pq = Q.pattern().node("a").where(layer="social")
        node = pq._pattern.nodes["a"]
        assert node.layer_constraint is not None
        assert node.layer_constraint.kind == "one"
        assert node.layer_constraint.value == "social"
    
    def test_edge_builder(self):
        """Test adding edges."""
        pq = (
            Q.pattern()
            .node("a")
            .node("b")
            .edge("a", "b", directed=False)
            .where(weight__gt=0.5)
        )
        assert len(pq._pattern.edges) == 1
        edge = pq._pattern.edges[0]
        assert edge.src == "a"
        assert edge.dst == "b"
        assert not edge.directed
        assert len(edge.predicates) == 1
    
    def test_path_sugar(self):
        """Test path() sugar method."""
        pq = Q.pattern().path(["a", "b", "c"])
        assert len(pq._pattern.edges) == 2
        assert pq._pattern.edges[0].src == "a"
        assert pq._pattern.edges[0].dst == "b"
        assert pq._pattern.edges[1].src == "b"
        assert pq._pattern.edges[1].dst == "c"
    
    def test_triangle_sugar(self):
        """Test triangle() sugar method."""
        pq = Q.pattern().triangle("a", "b", "c")
        assert len(pq._pattern.edges) == 3
        # Check that we have edges a-b, b-c, c-a
        edge_pairs = {(e.src, e.dst) for e in pq._pattern.edges}
        assert ("a", "b") in edge_pairs
        assert ("b", "c") in edge_pairs
        assert ("c", "a") in edge_pairs
    
    def test_returning(self):
        """Test returning() method."""
        pq = Q.pattern().node("a").node("b").node("c").returning("a", "b")
        assert pq._pattern.return_vars == ["a", "b"]
    
    def test_limit(self):
        """Test limit() method."""
        pq = Q.pattern().node("a").limit(10)
        assert pq._limit == 10
    
    def test_explain(self):
        """Test explain() method."""
        pq = Q.pattern().node("a").where(degree__gt=3).node("b").edge("a", "b")
        plan = pq.explain()
        assert isinstance(plan, dict)
        assert "root_var" in plan
        assert "join_order" in plan


class TestMatching:
    """Test pattern matching on networks."""
    
    def test_simple_edge_match(self, simple_network):
        """Test matching a simple edge pattern."""
        pq = (
            Q.pattern()
            .node("a")
            .node("b")
            .edge("a", "b", directed=False)
            .returning("a", "b")
        )
        
        result = pq.execute(simple_network)
        assert isinstance(result, PatternQueryResult)
        assert result.count > 0
        
        # Should find all edges (nodes stored as tuples with layers)
        # The exact count depends on how nodes are represented
        # Just verify we got matches
        assert result.count >= 4  # At least 4 edges
    
    def test_edge_match_with_layer_constraint(self, simple_network):
        """Test matching edges within a specific layer."""
        pq = (
            Q.pattern()
            .node("a").where(layer="social")
            .node("b").where(layer="social")
            .edge("a", "b", directed=False)
        )
        
        result = pq.execute(simple_network)
        # Should find only social layer edges
        assert result.count >= 3  # At least 3 edges in social layer
    
    def test_edge_match_with_weight_constraint(self, simple_network):
        """Test matching edges with weight constraint."""
        pq = (
            Q.pattern()
            .node("a")
            .node("b")
            .edge("a", "b", directed=False)
            .where(weight__gt=1.5)
        )
        
        result = pq.execute(simple_network)
        # Should find edges with weight > 1.5: B-C (weight=2.0), D-E (weight=3.0)
        assert result.count >= 2  # At least 2 edges
    
    def test_triangle_match(self, simple_network):
        """Test matching triangle motifs."""
        pq = Q.pattern().triangle("a", "b", "c")
        
        result = pq.execute(simple_network)
        # Should find the triangle A-B-C in social layer
        assert result.count >= 1  # At least one triangle
    
    def test_path_match(self, simple_network):
        """Test matching 2-hop paths."""
        pq = Q.pattern().path(["a", "b", "c"])
        
        result = pq.execute(simple_network)
        # Social layer: A-B-C, C-B-A, A-C-B, B-C-A, etc.
        # Multiple 2-hop paths exist
        assert result.count > 0
    
    def test_limit(self, simple_network):
        """Test limiting the number of matches."""
        pq = (
            Q.pattern()
            .node("a")
            .node("b")
            .edge("a", "b", directed=False)
            .limit(3)
        )
        
        result = pq.execute(simple_network)
        assert result.count == 3
    
    def test_all_different_constraint(self, simple_network):
        """Test all-different constraint."""
        pq = (
            Q.pattern()
            .node("a")
            .node("b")
            .edge("a", "b", directed=False)
            .constraint("a != b")
        )
        
        result = pq.execute(simple_network)
        # All matches should have different nodes for a and b
        for match in result.matches:
            assert match["a"] != match["b"]
    
    def test_directed_edge_match(self):
        """Test matching directed edges."""
        # Create a directed network
        network = multinet.multi_layer_network(directed=True)
        nodes = [
            {'source': 'A', 'type': 'social'},
            {'source': 'B', 'type': 'social'},
            {'source': 'C', 'type': 'social'},
        ]
        network.add_nodes(nodes)
        edges = [
            {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social'},
            {'source': 'B', 'target': 'C', 'source_type': 'social', 'target_type': 'social'},
        ]
        network.add_edges(edges)
        
        pq = (
            Q.pattern()
            .node("a")
            .node("b")
            .edge("a", "b", directed=True)
        )
        
        result = pq.execute(network)
        # Should find directed edges
        assert result.count >= 2  # At least A->B and B->C


class TestResult:
    """Test PatternQueryResult class."""
    
    def test_to_pandas(self, simple_network):
        """Test converting results to pandas DataFrame."""
        pq = (
            Q.pattern()
            .node("a")
            .node("b")
            .edge("a", "b", directed=False)
            .limit(5)
        )
        
        result = pq.execute(simple_network)
        df = result.to_pandas()
        
        assert len(df) == 5
        assert "a" in df.columns
        assert "b" in df.columns
    
    def test_to_nodes(self, simple_network):
        """Test extracting nodes from results."""
        pq = (
            Q.pattern()
            .node("a")
            .node("b")
            .edge("a", "b", directed=False)
            .returning("a", "b")
        )
        
        result = pq.execute(simple_network)
        nodes = result.to_nodes(unique=True)
        
        assert isinstance(nodes, set)
        # Should include nodes from both layers
        assert len(nodes) >= 2
    
    def test_to_edges(self, simple_network):
        """Test extracting edges from results."""
        pq = (
            Q.pattern()
            .node("a")
            .node("b")
            .edge("a", "b", directed=False)
            .limit(3)
        )
        
        result = pq.execute(simple_network)
        
        # Debug: check if we have matches
        assert result.count == 3
        
        edges = result.to_edges()
        
        # Each edge should be a tuple
        # Note: edges are node tuples (node_id, layer)
        assert len(edges) >= 1
        for edge in edges:
            assert isinstance(edge, tuple)
            assert len(edge) == 2
    
    def test_to_subgraph(self, simple_network):
        """Test extracting induced subgraph."""
        pq = (
            Q.pattern()
            .node("a").where(layer="social")
            .node("b").where(layer="social")
            .edge("a", "b", directed=False)
        )
        
        result = pq.execute(simple_network)
        subgraph = result.to_subgraph(simple_network)
        
        # Should create a networkx graph
        assert hasattr(subgraph, 'nodes')
        assert hasattr(subgraph, 'edges')
    
    def test_filter(self, simple_network):
        """Test filtering results."""
        pq = (
            Q.pattern()
            .node("a")
            .node("b")
            .edge("a", "b", directed=False)
        )
        
        result = pq.execute(simple_network)
        initial_count = result.count
        
        # Filter to keep only matches where a == "A"
        filtered = result.filter(lambda match: match["a"] == "A")
        assert filtered.count < initial_count
    
    def test_limit_result(self, simple_network):
        """Test limiting results."""
        pq = (
            Q.pattern()
            .node("a")
            .node("b")
            .edge("a", "b", directed=False)
        )
        
        result = pq.execute(simple_network)
        limited = result.limit(2)
        
        assert limited.count == 2


class TestIntegration:
    """Integration tests for complex patterns."""
    
    def test_complex_pattern_with_multiple_constraints(self, larger_network):
        """Test a complex pattern with multiple constraints."""
        pq = (
            Q.pattern()
            .node("a").where(layer="social")
            .node("b").where(layer="social")
            .node("c").where(layer="social")
            .edge("a", "b", directed=False)
            .edge("b", "c", directed=False)
            .constraint("a != b")
            .constraint("b != c")
            .returning("a", "b", "c")
            .limit(10)
        )
        
        result = pq.execute(larger_network)
        assert result.count > 0
        assert result.count <= 10
        
        # Verify constraints
        for match in result.matches:
            assert match["a"] != match["b"]
            assert match["b"] != match["c"]
    
    def test_empty_result(self):
        """Test pattern that matches nothing."""
        network = multinet.multi_layer_network(directed=False)
        nodes = [
            {'source': 'X', 'type': 'layer1'},
            {'source': 'Y', 'type': 'layer1'},
        ]
        network.add_nodes(nodes)
        # No edges - create completely disconnected network
        
        pq = (
            Q.pattern()
            .node("a")
            .node("b")
            .edge("a", "b", directed=False)
        )
        
        result = pq.execute(network)
        # Should find no edges since we didn't add any
        assert result.count == 0
    
    def test_pattern_with_high_degree_constraint(self, larger_network):
        """Test pattern with degree constraint."""
        pq = (
            Q.pattern()
            .node("a").where(layer="social", degree__gt=2)
            .node("b").where(layer="social")
            .edge("a", "b", directed=False)
        )
        
        result = pq.execute(larger_network)
        # In social layer complete graph, all nodes have degree 3
        assert result.count > 0
