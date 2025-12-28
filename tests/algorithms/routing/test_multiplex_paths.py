"""
Unit tests for multiplex path routing algorithms.

Tests the multiplex_shortest_path function with various scenarios including:
- Zero vs high switch costs
- Asymmetric switch cost matrices
- Pareto optimality
- Disconnected layers
- Layer filtering
"""

import pytest
from py3plex.core import multinet
from py3plex.algorithms.routing import multiplex_shortest_path
from py3plex.exceptions import InvalidNodeError, AlgorithmError


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def simple_multiplex():
    """Create a simple multiplex network with two layers.
    
    Layer 'social': A -- B -- C (weights: 1, 1)
    Layer 'work': A -- C (weight: 0.5)
    
    Without switch cost, shortest A->C is through 'work' (0.5)
    With high switch cost, might prefer 'social' path (2.0)
    """
    net = multinet.multi_layer_network(directed=False, verbose=False)
    edges = [
        ['A', 'social', 'B', 'social', 1.0],
        ['B', 'social', 'C', 'social', 1.0],
        ['A', 'work', 'C', 'work', 0.5],
    ]
    net.add_edges(edges, input_type="list")
    return net


@pytest.fixture
def three_layer_network():
    """Create a three-layer network for testing layer switches.
    
    Layer 'L1': A -- B -- C
    Layer 'L2': A -- B
    Layer 'L3': B -- C
    """
    net = multinet.multi_layer_network(directed=False, verbose=False)
    edges = [
        ['A', 'L1', 'B', 'L1', 1.0],
        ['B', 'L1', 'C', 'L1', 1.0],
        ['A', 'L2', 'B', 'L2', 1.0],
        ['B', 'L3', 'C', 'L3', 1.0],
    ]
    net.add_edges(edges, input_type="list")
    return net


@pytest.fixture
def disconnected_layers():
    """Create network with disconnected layers.
    
    Layer 'L1': A -- B
    Layer 'L2': C -- D (no connection to L1)
    """
    net = multinet.multi_layer_network(directed=False, verbose=False)
    edges = [
        ['A', 'L1', 'B', 'L1', 1.0],
        ['C', 'L2', 'D', 'L2', 1.0],
    ]
    net.add_edges(edges, input_type="list")
    return net


@pytest.fixture
def weighted_multiplex():
    """Create multiplex with various edge weights for testing cost calculations."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    edges = [
        ['A', 'L1', 'B', 'L1', 1.0],
        ['B', 'L1', 'C', 'L1', 2.0],
        ['A', 'L2', 'B', 'L2', 0.5],
        ['B', 'L2', 'C', 'L2', 0.5],
    ]
    net.add_edges(edges, input_type="list")
    return net


# ============================================================================
# Basic Functionality Tests
# ============================================================================


class TestBasicRouting:
    """Test basic routing functionality."""
    
    def test_simple_path_no_switch_cost(self, simple_multiplex):
        """Test that zero switch cost finds the shortest absolute path."""
        result = multiplex_shortest_path(
            simple_multiplex, 'A', 'C', switch_cost=0.0
        )
        
        assert result['success'] is True
        assert result['total_distance'] == 0.5
        assert result['path'] == [('A', 'work'), ('C', 'work')]
        assert result['num_switches'] == 0
    
    def test_simple_path_high_switch_cost(self, simple_multiplex):
        """Test that high switch cost biases towards single-layer paths."""
        result = multiplex_shortest_path(
            simple_multiplex, 'A', 'C', switch_cost=10.0
        )
        
        assert result['success'] is True
        # Should prefer the direct 'work' path (0.5) over 'social' path (2.0)
        assert result['total_distance'] == 0.5
        assert result['path'] == [('A', 'work'), ('C', 'work')]
    
    def test_path_metadata(self, simple_multiplex):
        """Test that path metadata is correctly populated."""
        result = multiplex_shortest_path(
            simple_multiplex, 'A', 'C', switch_cost=1.0
        )
        
        assert 'path' in result
        assert 'total_distance' in result
        assert 'num_switches' in result
        assert 'layers_visited' in result
        assert 'success' in result
        assert result['source'] == 'A'
        assert result['target'] == 'C'
    
    def test_path_with_switch(self, three_layer_network):
        """Test path that requires layer switching."""
        result = multiplex_shortest_path(
            three_layer_network, 'A', 'C', switch_cost=0.5
        )
        
        assert result['success'] is True
        # Path should go A->B in some layer, then B->C possibly in another
        assert result['path'][0][0] == 'A'
        assert result['path'][-1][0] == 'C'
        assert len(result['layers_visited']) >= 1


# ============================================================================
# Switch Cost Tests
# ============================================================================


class TestSwitchCosts:
    """Test different switch cost scenarios."""
    
    def test_zero_switch_cost_behavior(self, weighted_multiplex):
        """Test that zero switch cost reduces to flattened shortest path."""
        result = multiplex_shortest_path(
            weighted_multiplex, 'A', 'C', switch_cost=0.0
        )
        
        assert result['success'] is True
        # Should find path through L2 (total: 1.0) rather than L1 (total: 3.0)
        assert result['total_distance'] == 1.0
    
    def test_high_switch_cost_bias(self, weighted_multiplex):
        """Test that high switch cost biases against layer switching."""
        result = multiplex_shortest_path(
            weighted_multiplex, 'A', 'C', switch_cost=100.0
        )
        
        assert result['success'] is True
        # Should prefer single-layer path even if longer
        # L2 path (1.0) vs L1 path (3.0), both better than switching
        path_layers = [state[1] for state in result['path']]
        # Check that path uses minimal switches
        switches = sum(1 for i in range(1, len(path_layers)) 
                      if path_layers[i] != path_layers[i-1])
        assert switches <= 1
    
    def test_asymmetric_switch_cost_matrix(self, three_layer_network):
        """Test asymmetric switch cost matrix."""
        switch_matrix = {
            ('L1', 'L2'): 0.1,  # Cheap to go L1 -> L2
            ('L2', 'L1'): 10.0,  # Expensive to go L2 -> L1
            ('L1', 'L3'): 0.1,
            ('L2', 'L3'): 0.1,
        }
        
        result = multiplex_shortest_path(
            three_layer_network, 'A', 'C',
            switch_cost=1.0,
            switch_cost_matrix=switch_matrix
        )
        
        assert result['success'] is True
        # Path should be found
        assert len(result['path']) >= 2


# ============================================================================
# Multi-Objective Tests
# ============================================================================


class TestMultiObjective:
    """Test multi-objective routing."""
    
    def test_pareto_optimal_paths(self, weighted_multiplex):
        """Test that Pareto-optimal paths are returned."""
        result = multiplex_shortest_path(
            weighted_multiplex, 'A', 'C',
            switch_cost=1.5,
            objective="pareto"
        )
        
        assert result['success'] is True
        assert 'paths' in result
        assert 'objectives' in result
        assert len(result['paths']) == len(result['objectives'])
        assert len(result['paths']) >= 1
        
        # Check that objectives are (distance, switches) tuples
        for obj in result['objectives']:
            assert len(obj) == 2
            assert isinstance(obj[0], (int, float))
            assert isinstance(obj[1], int)
    
    def test_pareto_dominance(self, weighted_multiplex):
        """Test that returned paths are non-dominated."""
        result = multiplex_shortest_path(
            weighted_multiplex, 'A', 'C',
            switch_cost=1.0,
            objective="pareto"
        )
        
        assert result['success'] is True
        objectives = result['objectives']
        
        # Check no path dominates another
        for i, (dist1, sw1) in enumerate(objectives):
            for j, (dist2, sw2) in enumerate(objectives):
                if i != j:
                    # Neither should strictly dominate the other
                    dominates = (dist1 <= dist2 and sw1 <= sw2 and 
                               (dist1 < dist2 or sw1 < sw2))
                    assert not dominates, f"Path {i} dominates path {j}"


# ============================================================================
# Layer Filtering Tests
# ============================================================================


class TestLayerFiltering:
    """Test layer filtering and constraints."""
    
    def test_allowed_layers_restriction(self, three_layer_network):
        """Test that allowed_layers restricts the search space."""
        result = multiplex_shortest_path(
            three_layer_network, 'A', 'C',
            switch_cost=1.0,
            allowed_layers=['L1']
        )
        
        assert result['success'] is True
        # Path should only use L1
        for state in result['path']:
            assert state[1] == 'L1'
    
    def test_allowed_layers_no_path(self, three_layer_network):
        """Test behavior when allowed_layers prevents finding a path."""
        result = multiplex_shortest_path(
            three_layer_network, 'A', 'C',
            switch_cost=1.0,
            allowed_layers=['L2']  # L2 only has A-B, not B-C
        )
        
        # Should fail to find path or return error
        assert result['success'] is False


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_invalid_source_node(self, simple_multiplex):
        """Test error handling for invalid source node."""
        with pytest.raises(InvalidNodeError):
            multiplex_shortest_path(simple_multiplex, 'X', 'C')
    
    def test_invalid_target_node(self, simple_multiplex):
        """Test error handling for invalid target node."""
        with pytest.raises(InvalidNodeError):
            multiplex_shortest_path(simple_multiplex, 'A', 'X')
    
    def test_disconnected_nodes(self, disconnected_layers):
        """Test behavior when nodes are in disconnected components."""
        result = multiplex_shortest_path(
            disconnected_layers, 'A', 'C',
            switch_cost=1.0
        )
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_same_source_target(self, simple_multiplex):
        """Test routing from node to itself."""
        # This should find a trivial path (the node in some layer)
        result = multiplex_shortest_path(
            simple_multiplex, 'A', 'A', switch_cost=1.0
        )
        
        # Behavior: might return empty path or single-node path
        # Both are acceptable
        assert result['success'] is True or result['path'] == []
    
    def test_invalid_objective(self, simple_multiplex):
        """Test error handling for invalid objective parameter."""
        with pytest.raises(AlgorithmError):
            multiplex_shortest_path(
                simple_multiplex, 'A', 'C',
                objective="invalid"
            )
    
    def test_invalid_method(self, simple_multiplex):
        """Test error handling for invalid method parameter."""
        with pytest.raises(AlgorithmError):
            multiplex_shortest_path(
                simple_multiplex, 'A', 'C',
                method="invalid"
            )


# ============================================================================
# Determinism and Reproducibility Tests
# ============================================================================


class TestDeterminism:
    """Test that results are deterministic and reproducible."""
    
    def test_deterministic_single_path(self, simple_multiplex):
        """Test that the same query returns the same result."""
        result1 = multiplex_shortest_path(
            simple_multiplex, 'A', 'C', switch_cost=1.0
        )
        result2 = multiplex_shortest_path(
            simple_multiplex, 'A', 'C', switch_cost=1.0
        )
        
        assert result1['path'] == result2['path']
        assert result1['total_distance'] == result2['total_distance']
        assert result1['num_switches'] == result2['num_switches']
    
    def test_deterministic_pareto(self, weighted_multiplex):
        """Test that Pareto-optimal paths are deterministic."""
        result1 = multiplex_shortest_path(
            weighted_multiplex, 'A', 'C',
            switch_cost=1.0,
            objective="pareto"
        )
        result2 = multiplex_shortest_path(
            weighted_multiplex, 'A', 'C',
            switch_cost=1.0,
            objective="pareto"
        )
        
        # Same number of paths
        assert len(result1['paths']) == len(result2['paths'])
        # Same objectives (may be in different order)
        assert set(result1['objectives']) == set(result2['objectives'])


# ============================================================================
# Complex Scenario Tests
# ============================================================================


class TestComplexScenarios:
    """Test complex routing scenarios."""
    
    def test_long_chain_with_switches(self):
        """Test routing on a longer path requiring multiple switches."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        edges = [
            ['A', 'L1', 'B', 'L1', 1.0],
            ['B', 'L2', 'C', 'L2', 1.0],
            ['C', 'L3', 'D', 'L3', 1.0],
        ]
        net.add_edges(edges, input_type="list")
        
        result = multiplex_shortest_path(net, 'A', 'D', switch_cost=0.5)
        
        assert result['success'] is True
        assert result['path'][0][0] == 'A'
        assert result['path'][-1][0] == 'D'
        # Should require 2 switches: L1->L2 at B, L2->L3 at C
        assert result['num_switches'] == 2
    
    def test_multiple_paths_same_cost(self):
        """Test network with multiple paths of same cost."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        edges = [
            # Two parallel paths with same total cost
            ['A', 'L1', 'B', 'L1', 1.0],
            ['B', 'L1', 'C', 'L1', 1.0],
            ['A', 'L2', 'B', 'L2', 1.0],
            ['B', 'L2', 'C', 'L2', 1.0],
        ]
        net.add_edges(edges, input_type="list")
        
        result = multiplex_shortest_path(net, 'A', 'C', switch_cost=0.0)
        
        assert result['success'] is True
        assert result['total_distance'] == 2.0
        # Should find one of the two equivalent paths
    
    def test_directed_network(self):
        """Test routing on directed multiplex network."""
        net = multinet.multi_layer_network(directed=True, verbose=False)
        edges = [
            {'source': 'A', 'target': 'B', 
             'source_type': 'L1', 'target_type': 'L1', 'weight': 1.0},
            {'source': 'B', 'target': 'C', 
             'source_type': 'L1', 'target_type': 'L1', 'weight': 1.0},
        ]
        net.add_edges(edges)
        
        # Forward path should work
        result = multiplex_shortest_path(net, 'A', 'C', switch_cost=1.0)
        assert result['success'] is True
        
        # Reverse path should not work (directed)
        result_reverse = multiplex_shortest_path(net, 'C', 'A', switch_cost=1.0)
        assert result_reverse['success'] is False


# ============================================================================
# Performance and Scalability Tests
# ============================================================================


@pytest.mark.slow
class TestPerformance:
    """Test performance on larger networks (marked as slow)."""
    
    def test_large_multiplex(self):
        """Test routing on a larger multiplex network."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        
        # Create a chain of 50 nodes across 3 layers
        layers = ['L1', 'L2', 'L3']
        for i in range(49):
            for layer in layers:
                net.add_edges([
                    [f'N{i}', layer, f'N{i+1}', layer, 1.0]
                ], input_type="list")
        
        result = multiplex_shortest_path(
            net, 'N0', 'N49', switch_cost=1.0
        )
        
        assert result['success'] is True
        assert len(result['path']) >= 50


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests with other py3plex components."""
    
    def test_with_dict_edges(self):
        """Test using dict-based edge format."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        edges = [
            {'source': 'A', 'target': 'B', 
             'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
            {'source': 'B', 'target': 'C', 
             'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        ]
        net.add_edges(edges)
        
        result = multiplex_shortest_path(net, 'A', 'C', switch_cost=1.0)
        
        assert result['success'] is True
        assert result['path'][0][0] == 'A'
        assert result['path'][-1][0] == 'C'
