"""Tests for py3plex.semiring.types module.

Tests type definitions and data structures for semiring operations.
"""

import pytest
from py3plex.semiring.types import PathResult, EdgeView, LiftFn
from typing import get_type_hints


class TestPathResult:
    """Test PathResult dataclass."""
    
    def test_path_result_creation_minimal(self):
        """Test creating PathResult with just value."""
        result = PathResult(value=10.5)
        
        assert result.value == 10.5
        assert result.path is None
        assert result.meta == {}
    
    def test_path_result_creation_with_path(self):
        """Test creating PathResult with path witness."""
        path = ['A', 'B', 'C']
        result = PathResult(value=3.0, path=path)
        
        assert result.value == 3.0
        assert result.path == ['A', 'B', 'C']
        assert len(result.path) == 3
    
    def test_path_result_creation_with_meta(self):
        """Test creating PathResult with metadata."""
        meta = {"algorithm": "dijkstra", "iterations": 5}
        result = PathResult(value=15.0, meta=meta)
        
        assert result.value == 15.0
        assert result.meta["algorithm"] == "dijkstra"
        assert result.meta["iterations"] == 5
    
    def test_path_result_complete(self):
        """Test creating PathResult with all fields."""
        path = [('A', 'layer1'), ('B', 'layer1'), ('C', 'layer2')]
        meta = {"algorithm": "bellman_ford", "negative_cycles": False}
        result = PathResult(value=7.5, path=path, meta=meta)
        
        assert result.value == 7.5
        assert result.path == path
        assert result.meta["algorithm"] == "bellman_ford"
        assert result.meta["negative_cycles"] is False
    
    def test_path_result_value_types(self):
        """Test PathResult can hold different value types."""
        # Numeric value
        result1 = PathResult(value=42)
        assert isinstance(result1.value, int)
        
        # Float value
        result2 = PathResult(value=3.14)
        assert isinstance(result2.value, float)
        
        # Boolean value (for reachability)
        result3 = PathResult(value=True)
        assert isinstance(result3.value, bool)
        
        # String value
        result4 = PathResult(value="reachable")
        assert isinstance(result4.value, str)
    
    def test_path_result_path_types(self):
        """Test PathResult path can be different sequence types."""
        # Node path
        result1 = PathResult(value=5.0, path=['A', 'B', 'C'])
        assert len(result1.path) == 3
        
        # Edge path
        result2 = PathResult(value=5.0, path=[('A', 'B'), ('B', 'C')])
        assert len(result2.path) == 2
        
        # Empty path
        result3 = PathResult(value=0.0, path=[])
        assert result3.path == []
    
    def test_path_result_meta_dict(self):
        """Test PathResult meta is a mutable dict."""
        result = PathResult(value=10.0)
        
        # Should be able to add metadata
        result.meta["foo"] = "bar"
        assert result.meta["foo"] == "bar"
    
    def test_path_result_default_factory(self):
        """Test that each PathResult gets its own meta dict."""
        result1 = PathResult(value=1.0)
        result2 = PathResult(value=2.0)
        
        result1.meta["key"] = "value1"
        result2.meta["key"] = "value2"
        
        assert result1.meta["key"] == "value1"
        assert result2.meta["key"] == "value2"


class TestPathResultUsage:
    """Test typical usage patterns for PathResult."""
    
    def test_shortest_path_result(self):
        """Test PathResult for shortest path."""
        result = PathResult(
            value=15.5,
            path=['A', 'B', 'C', 'D'],
            meta={"algorithm": "dijkstra", "hops": 3}
        )
        
        assert result.value == 15.5  # Total distance
        assert len(result.path) == 4  # 4 nodes
        assert result.meta["hops"] == 3  # 3 edges
    
    def test_boolean_reachability_result(self):
        """Test PathResult for boolean reachability."""
        result = PathResult(
            value=True,
            path=['A', 'intermediate1', 'intermediate2', 'B'],
            meta={"algorithm": "boolean", "distance": 3}
        )
        
        assert result.value is True  # Reachable
        assert 'A' in result.path
        assert 'B' in result.path
    
    def test_max_reliability_result(self):
        """Test PathResult for most reliable path."""
        result = PathResult(
            value=0.85,  # Reliability
            path=[('A', 'B', 0.9), ('B', 'C', 0.95)],  # Edges with reliabilities
            meta={"algorithm": "max_times", "semiring": "tropical"}
        )
        
        assert result.value == 0.85
        assert len(result.path) == 2  # 2 edges
    
    def test_no_path_result(self):
        """Test PathResult when no path exists."""
        result = PathResult(
            value=float('inf'),
            path=None,
            meta={"reachable": False}
        )
        
        assert result.value == float('inf')
        assert result.path is None
        assert result.meta["reachable"] is False


class TestEdgeViewProtocol:
    """Test EdgeView protocol."""
    
    def test_edge_view_protocol_attributes(self):
        """Test that EdgeView protocol defines required attributes."""
        # Get type hints from protocol
        hints = get_type_hints(EdgeView)
        
        # Should have source, target, attrs properties
        assert 'source' in dir(EdgeView)
        assert 'target' in dir(EdgeView)
        assert 'attrs' in dir(EdgeView)
    
    def test_edge_view_implementation(self):
        """Test that a class can implement EdgeView protocol."""
        class MyEdge:
            def __init__(self, src, dst, attributes):
                self._source = src
                self._target = dst
                self._attrs = attributes
            
            @property
            def source(self):
                return self._source
            
            @property
            def target(self):
                return self._target
            
            @property
            def attrs(self):
                return self._attrs
        
        edge = MyEdge('A', 'B', {'weight': 1.5, 'type': 'directed'})
        
        # Should satisfy protocol
        assert edge.source == 'A'
        assert edge.target == 'B'
        assert edge.attrs['weight'] == 1.5
        assert edge.attrs['type'] == 'directed'


class TestLiftFnType:
    """Test LiftFn type alias."""
    
    def test_lift_fn_basic(self):
        """Test basic lift function."""
        def lift_weight(attrs: dict) -> float:
            return attrs.get('weight', 1.0)
        
        # Test with weighted edge
        assert lift_weight({'weight': 2.5}) == 2.5
        
        # Test with unweighted edge
        assert lift_weight({}) == 1.0
    
    def test_lift_fn_boolean(self):
        """Test boolean lift function for reachability."""
        def lift_bool(attrs: dict) -> bool:
            return True  # All edges exist
        
        assert lift_bool({}) is True
        assert lift_bool({'weight': 5.0}) is True
    
    def test_lift_fn_custom_semiring(self):
        """Test lift function for custom semiring values."""
        def lift_capacity(attrs: dict) -> int:
            return attrs.get('capacity', 0)
        
        assert lift_capacity({'capacity': 100}) == 100
        assert lift_capacity({}) == 0
    
    def test_lift_fn_with_transformation(self):
        """Test lift function that transforms values."""
        def lift_log_weight(attrs: dict) -> float:
            import math
            weight = attrs.get('weight', 1.0)
            return -math.log(weight) if weight > 0 else float('inf')
        
        # Test with positive weight
        result = lift_log_weight({'weight': 0.5})
        assert result > 0  # -log(0.5) is positive
        
        # Test with zero weight
        result = lift_log_weight({'weight': 0})
        assert result == float('inf')


class TestTypesIntegration:
    """Test how types work together."""
    
    def test_path_result_with_edge_view(self):
        """Test PathResult storing EdgeView-like objects in path."""
        class SimpleEdge:
            def __init__(self, src, dst, attrs):
                self._source = src
                self._target = dst
                self._attrs = attrs
            
            @property
            def source(self):
                return self._source
            
            @property
            def target(self):
                return self._target
            
            @property
            def attrs(self):
                return self._attrs
        
        edges = [
            SimpleEdge('A', 'B', {'weight': 1.0}),
            SimpleEdge('B', 'C', {'weight': 2.0})
        ]
        
        result = PathResult(
            value=3.0,
            path=edges,
            meta={"edge_count": 2}
        )
        
        assert result.value == 3.0
        assert len(result.path) == 2
        assert result.path[0].source == 'A'
        assert result.path[1].target == 'C'
    
    def test_lift_fn_creating_path_result(self):
        """Test lift function as part of path computation."""
        def lift_weight(attrs: dict) -> float:
            return attrs.get('weight', 1.0)
        
        # Simulate computing path value
        edges = [
            {'weight': 1.5},
            {'weight': 2.0},
            {'weight': 3.5}
        ]
        
        total = sum(lift_weight(e) for e in edges)
        
        result = PathResult(
            value=total,
            path=['A', 'B', 'C', 'D'],
            meta={"lift_fn": "weight"}
        )
        
        assert result.value == 7.0
        assert len(result.path) == 4
