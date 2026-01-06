"""Tests for semiring path algorithms."""

import pytest
import math
from py3plex.algebra import (
    BooleanSemiring,
    MinPlusSemiring,
    MaxTimesSemiring,
    WeightLiftSpec,
    sssp,
    closure,
    get_backend,
)


class TestSSSPMinPlus:
    """Test single-source shortest path with min-plus semiring."""
    
    def test_simple_shortest_path(self):
        """Test basic shortest path finding."""
        # Simple graph: A -> B (weight 2), B -> C (weight 3), A -> C (weight 10)
        nodes = ['A', 'B', 'C']
        edges = [
            ('A', 'B', {'weight': 2.0}),
            ('B', 'C', {'weight': 3.0}),
            ('A', 'C', {'weight': 10.0}),
        ]
        
        semiring = MinPlusSemiring()
        lift_spec = WeightLiftSpec(attr='weight', default=1.0)
        
        result = sssp(nodes, edges, 'A', semiring, lift_spec)
        
        assert result.distances['A'] == 0.0
        assert result.distances['B'] == 2.0
        assert result.distances['C'] == 5.0  # Via B, not direct
        assert result.algorithm in ('dijkstra', 'bellman_ford')
    
    def test_unreachable_node(self):
        """Test unreachable node has infinite distance."""
        nodes = ['A', 'B', 'C']
        edges = [
            ('A', 'B', {'weight': 1.0}),
            # C is unreachable
        ]
        
        semiring = MinPlusSemiring()
        lift_spec = WeightLiftSpec(attr='weight', default=1.0)
        
        result = sssp(nodes, edges, 'A', semiring, lift_spec)
        
        assert result.distances['A'] == 0.0
        assert result.distances['B'] == 1.0
        assert math.isinf(result.distances['C'])
    
    def test_path_reconstruction(self):
        """Test reconstructing shortest path from predecessors."""
        nodes = ['A', 'B', 'C', 'D']
        edges = [
            ('A', 'B', {'weight': 1.0}),
            ('B', 'C', {'weight': 2.0}),
            ('C', 'D', {'weight': 1.0}),
        ]
        
        semiring = MinPlusSemiring()
        lift_spec = WeightLiftSpec(attr='weight', default=1.0)
        
        result = sssp(nodes, edges, 'A', semiring, lift_spec)
        
        path = result.get_path('D')
        assert path == ['A', 'B', 'C', 'D']
    
    def test_default_weight(self):
        """Test using default weight when attribute missing."""
        nodes = ['A', 'B', 'C']
        edges = [
            ('A', 'B', {}),  # No weight attribute
            ('B', 'C', {'weight': 2.0}),
        ]
        
        semiring = MinPlusSemiring()
        lift_spec = WeightLiftSpec(attr='weight', default=1.0)
        
        result = sssp(nodes, edges, 'A', semiring, lift_spec)
        
        assert result.distances['B'] == 1.0  # Default weight
        assert result.distances['C'] == 3.0
    
    def test_max_hops_limit(self):
        """Test maximum hop constraint."""
        nodes = ['A', 'B', 'C', 'D']
        edges = [
            ('A', 'B', {'weight': 1.0}),
            ('B', 'C', {'weight': 1.0}),
            ('C', 'D', {'weight': 1.0}),
        ]
        
        semiring = MinPlusSemiring()
        lift_spec = WeightLiftSpec(attr='weight', default=1.0)
        
        # Limit to 2 hops
        result = sssp(nodes, edges, 'A', semiring, lift_spec, max_hops=2)
        
        assert result.distances['A'] == 0.0
        assert result.distances['B'] == 1.0
        assert result.distances['C'] == 2.0
        # D is 3 hops away, should be unreachable
        assert math.isinf(result.distances['D'])
    
    def test_algorithm_selection(self):
        """Test automatic algorithm selection based on semiring."""
        nodes = ['A', 'B', 'C']
        edges = [('A', 'B', {'weight': 1.0})]
        
        # Min-plus should use Dijkstra (idempotent + monotone)
        semiring = MinPlusSemiring()
        lift_spec = WeightLiftSpec(attr='weight', default=1.0)
        
        result = sssp(nodes, edges, 'A', semiring, lift_spec)
        assert result.algorithm == 'dijkstra'


class TestSSSPBoolean:
    """Test reachability with boolean semiring."""
    
    def test_reachability(self):
        """Test boolean semiring for reachability analysis."""
        nodes = ['A', 'B', 'C', 'D']
        edges = [
            ('A', 'B', {}),
            ('B', 'C', {}),
            # D is unreachable
        ]
        
        semiring = BooleanSemiring()
        lift_spec = WeightLiftSpec(attr=None, default=True)
        
        result = sssp(nodes, edges, 'A', semiring, lift_spec)
        
        assert result.distances['A'] == True
        assert result.distances['B'] == True
        assert result.distances['C'] == True
        assert result.distances['D'] == False


class TestSSSPMaxTimes:
    """Test most reliable path with max-times semiring."""
    
    def test_most_reliable_path(self):
        """Test finding most reliable path (max probability product)."""
        nodes = ['A', 'B', 'C']
        edges = [
            ('A', 'B', {'reliability': 0.9}),
            ('B', 'C', {'reliability': 0.8}),
            ('A', 'C', {'reliability': 0.6}),  # Direct but less reliable
        ]
        
        semiring = MaxTimesSemiring()
        lift_spec = WeightLiftSpec(attr='reliability', default=1.0)
        
        result = sssp(nodes, edges, 'A', semiring, lift_spec)
        
        assert result.distances['A'] == 1.0
        assert abs(result.distances['B'] - 0.9) < 1e-10
        # Via B: 0.9 * 0.8 = 0.72 > 0.6 direct
        assert abs(result.distances['C'] - 0.72) < 1e-10


class TestClosure:
    """Test transitive closure operations."""
    
    def test_boolean_closure_reachability(self):
        """Test boolean closure equals reachability closure."""
        nodes = ['A', 'B', 'C']
        edges = [
            ('A', 'B', {}),
            ('B', 'C', {}),
        ]
        
        semiring = BooleanSemiring()
        lift_spec = WeightLiftSpec(attr=None, default=True)
        
        result = closure(nodes, edges, semiring, lift_spec)
        
        # Check reachability
        assert result[('A', 'A')] == True  # Self
        assert result[('A', 'B')] == True
        assert result[('A', 'C')] == True  # Transitive
        assert result[('B', 'C')] == True
        assert result[('C', 'A')] == False  # Not reachable
    
    def test_min_plus_closure_apsp(self):
        """Test min-plus closure gives all-pairs shortest paths."""
        nodes = ['A', 'B', 'C']
        edges = [
            ('A', 'B', {'weight': 1.0}),
            ('B', 'C', {'weight': 2.0}),
            ('A', 'C', {'weight': 5.0}),
        ]
        
        semiring = MinPlusSemiring()
        lift_spec = WeightLiftSpec(attr='weight', default=1.0)
        
        result = closure(nodes, edges, semiring, lift_spec, method='floyd_warshall')
        
        assert result[('A', 'A')] == 0.0
        assert result[('A', 'B')] == 1.0
        assert result[('A', 'C')] == 3.0  # Via B, not direct
        assert result[('B', 'C')] == 2.0
    
    def test_closure_method_selection(self):
        """Test automatic method selection based on graph size."""
        # Small graph should use Floyd-Warshall
        nodes = ['A', 'B', 'C']
        edges = [('A', 'B', {'weight': 1.0})]
        
        semiring = MinPlusSemiring()
        lift_spec = WeightLiftSpec(attr='weight', default=1.0)
        
        result = closure(nodes, edges, semiring, lift_spec, method='auto')
        assert result is not None  # Should complete successfully


class TestBackend:
    """Test backend dispatch system."""
    
    def test_get_graph_backend(self):
        """Test getting graph backend."""
        backend = get_backend('graph')
        assert backend.name == 'graph'
    
    def test_graph_backend_sssp(self):
        """Test graph backend SSSP."""
        backend = get_backend('graph')
        
        nodes = ['A', 'B']
        edges = [('A', 'B', {'weight': 1.0})]
        semiring = MinPlusSemiring()
        lift_spec = WeightLiftSpec(attr='weight', default=1.0)
        
        result = backend.sssp(nodes, edges, 'A', semiring, lift_spec)
        assert result.distances['B'] == 1.0
    
    def test_matrix_backend_not_implemented(self):
        """Test that matrix backend raises not implemented error."""
        from py3plex.exceptions import Py3plexException
        
        backend = get_backend('matrix')
        
        with pytest.raises(Py3plexException, match="not yet implemented"):
            backend.sssp([], [], 'A', MinPlusSemiring(), WeightLiftSpec())


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_graph(self):
        """Test SSSP on empty graph."""
        nodes = []
        edges = []
        
        semiring = MinPlusSemiring()
        lift_spec = WeightLiftSpec(attr='weight', default=1.0)
        
        # Should handle gracefully (no source node to query from)
        # This is a degenerate case
        # Just verify no crash
        try:
            result = sssp(nodes, edges, 'A', semiring, lift_spec)
            # Source not in nodes, should get zero/inf pattern
        except Exception:
            pass  # Acceptable to raise exception
    
    def test_single_node(self):
        """Test SSSP on single node graph."""
        nodes = ['A']
        edges = []
        
        semiring = MinPlusSemiring()
        lift_spec = WeightLiftSpec(attr='weight', default=1.0)
        
        result = sssp(nodes, edges, 'A', semiring, lift_spec)
        assert result.distances['A'] == 0.0
    
    def test_parallel_edges(self):
        """Test graph with parallel edges (multiple edges between same nodes)."""
        nodes = ['A', 'B']
        edges = [
            ('A', 'B', {'weight': 5.0}),
            ('A', 'B', {'weight': 2.0}),  # Better parallel edge
        ]
        
        semiring = MinPlusSemiring()
        lift_spec = WeightLiftSpec(attr='weight', default=1.0)
        
        result = sssp(nodes, edges, 'A', semiring, lift_spec)
        # Should take better edge
        assert result.distances['B'] == 2.0
