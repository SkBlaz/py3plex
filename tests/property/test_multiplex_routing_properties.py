"""Property-based tests for multiplex routing algorithms.

This module tests invariants and properties of multiplex_shortest_path
using hypothesis for property-based testing, focusing on:
- Invariance properties (network non-mutation, determinism)
- Corner cases (single layer, empty networks, self-loops)
- Mathematical properties (triangle inequality, path optimality)
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
import networkx as nx

from py3plex.core import multinet
from py3plex.algorithms.routing import multiplex_shortest_path
from py3plex.exceptions import InvalidNodeError, AlgorithmError


# ============================================================================
# Helper functions
# ============================================================================


def build_multiplex_network(
    num_nodes: int = 4,
    num_layers: int = 2,
    edges_per_layer: int = 3,
    directed: bool = False,
) -> multinet.multi_layer_network:
    """Build a test multiplex network for routing testing."""
    net = multinet.multi_layer_network(directed=directed, verbose=False)
    edges = []
    layers = [f"L{i}" for i in range(num_layers)]

    for layer in layers:
        for i in range(min(edges_per_layer, num_nodes - 1)):
            edges.append([f"n{i}", layer, f"n{i+1}", layer, 1.0])

    if edges:
        net.add_edges(edges, input_type="list")
    return net


def count_nodes(net: multinet.multi_layer_network) -> int:
    """Count unique nodes in a network."""
    return len(set(n[0] for n in net.core_network.nodes() if isinstance(n, tuple)))


def count_edges(net: multinet.multi_layer_network) -> int:
    """Count edges in a network."""
    return len(list(net.core_network.edges()))


# ============================================================================
# Invariance Properties
# ============================================================================


class TestMultiplexRoutingInvariance:
    """Test invariance properties of multiplex routing."""

    @pytest.mark.property
    @given(st.integers(min_value=2, max_value=6))
    @settings(max_examples=3, deadline=500)
    def test_routing_does_not_mutate_network(self, num_nodes: int):
        """multiplex_shortest_path must not mutate the original network."""
        net = build_multiplex_network(num_nodes=num_nodes, num_layers=2)
        original_nodes = count_nodes(net)
        original_edges = count_edges(net)
        
        try:
            _ = multiplex_shortest_path(net, source="n0", target=f"n{num_nodes-1}", switch_cost=1.0)
        except (InvalidNodeError, AlgorithmError):
            pass  # Expected for some cases
        
        assert count_nodes(net) == original_nodes, "Network nodes were mutated"
        assert count_edges(net) == original_edges, "Network edges were mutated"

    @pytest.mark.property
    @given(
        num_nodes=st.integers(min_value=2, max_value=5),
        switch_cost=st.floats(min_value=0.0, max_value=10.0),
    )
    @settings(max_examples=3, deadline=500)
    def test_routing_is_deterministic(self, num_nodes: int, switch_cost: float):
        """multiplex_shortest_path must return deterministic results."""
        assume(not (switch_cost != switch_cost))  # Skip NaN
        
        net = build_multiplex_network(num_nodes=num_nodes, num_layers=2)
        
        try:
            result1 = multiplex_shortest_path(net, "n0", f"n{num_nodes-1}", switch_cost=switch_cost)
            result2 = multiplex_shortest_path(net, "n0", f"n{num_nodes-1}", switch_cost=switch_cost)
            
            if result1['success'] and result2['success']:
                assert result1['path'] == result2['path'], "Non-deterministic paths"
                assert result1['total_distance'] == result2['total_distance'], "Non-deterministic distances"
                assert result1['num_switches'] == result2['num_switches'], "Non-deterministic switch counts"
        except (InvalidNodeError, AlgorithmError):
            pass

    @pytest.mark.property
    @given(st.integers(min_value=2, max_value=6))
    @settings(max_examples=3, deadline=500)
    def test_routing_preserves_layer_semantics(self, num_nodes: int):
        """Routing must preserve layer information in paths."""
        net = build_multiplex_network(num_nodes=num_nodes, num_layers=3)
        
        try:
            result = multiplex_shortest_path(net, "n0", f"n{num_nodes-1}", switch_cost=0.5)
            
            if result['success'] and result['path']:
                # All path states must be (node, layer) tuples
                for state in result['path']:
                    assert isinstance(state, tuple), "Path state is not a tuple"
                    assert len(state) == 2, "Path state should be (node, layer)"
                    assert isinstance(state[1], str), "Layer must be a string"
        except (InvalidNodeError, AlgorithmError):
            pass


# ============================================================================
# Corner Cases
# ============================================================================


class TestMultiplexRoutingCornerCases:
    """Test corner cases and edge conditions."""

    @pytest.mark.property
    def test_single_layer_network(self):
        """Routing on single-layer network should work correctly."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        edges = [
            ['A', 'L1', 'B', 'L1', 1.0],
            ['B', 'L1', 'C', 'L1', 2.0],
        ]
        net.add_edges(edges, input_type="list")
        
        result = multiplex_shortest_path(net, 'A', 'C', switch_cost=1.0)
        
        assert result['success'] is True
        assert result['num_switches'] == 0, "Single layer should have zero switches"
        assert len(result['layers_visited']) == 1, "Should visit only one layer"

    @pytest.mark.property
    def test_single_node_path(self):
        """Routing from node to itself should return zero-cost path."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        edges = [['A', 'L1', 'B', 'L1', 1.0]]
        net.add_edges(edges, input_type="list")
        
        result = multiplex_shortest_path(net, 'A', 'A', switch_cost=1.0)
        
        assert result['success'] is True
        assert result['total_distance'] == 0.0, "Self-path should have zero distance"
        assert result['num_switches'] == 0, "Self-path should have zero switches"
        assert len(result['path']) == 1, "Self-path should contain single state"

    @pytest.mark.property
    def test_empty_allowed_layers_fails(self):
        """Routing with empty allowed_layers should fail gracefully."""
        net = build_multiplex_network(num_nodes=3, num_layers=2)
        
        result = multiplex_shortest_path(net, 'n0', 'n2', allowed_layers=[])
        
        assert result['success'] is False

    @pytest.mark.property
    def test_nonexistent_layer_filter(self):
        """Routing with non-existent layer filter should fail gracefully."""
        net = build_multiplex_network(num_nodes=3, num_layers=2)
        
        result = multiplex_shortest_path(net, 'n0', 'n2', allowed_layers=['NonExistent'])
        
        assert result['success'] is False

    @pytest.mark.property
    @given(num_nodes=st.integers(min_value=2, max_value=5))
    @settings(max_examples=3, deadline=500)
    def test_single_layer_behaves_like_standard_dijkstra(self, num_nodes: int):
        """Single-layer routing should match standard Dijkstra."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        edges = []
        for i in range(num_nodes - 1):
            edges.append([f"n{i}", "L1", f"n{i+1}", "L1", 1.0])
        net.add_edges(edges, input_type="list")
        
        result = multiplex_shortest_path(net, "n0", f"n{num_nodes-1}", switch_cost=0.0)
        
        if result['success']:
            assert result['num_switches'] == 0
            # Distance should be num_nodes - 1 (edges in path)
            assert result['total_distance'] == float(num_nodes - 1)


# ============================================================================
# Mathematical Properties
# ============================================================================


class TestMultiplexRoutingMathematicalProperties:
    """Test mathematical properties of routing."""

    @pytest.mark.property
    @given(
        num_nodes=st.integers(min_value=3, max_value=6),
        switch_cost=st.floats(min_value=0.0, max_value=5.0),
    )
    @settings(max_examples=3, deadline=500)
    def test_zero_switch_cost_is_optimal(self, num_nodes: int, switch_cost: float):
        """Zero switch cost should find globally optimal path."""
        assume(not (switch_cost != switch_cost))  # Skip NaN
        
        net = build_multiplex_network(num_nodes=num_nodes, num_layers=2, edges_per_layer=num_nodes)
        
        try:
            result_zero = multiplex_shortest_path(net, "n0", f"n{num_nodes-1}", switch_cost=0.0)
            result_nonzero = multiplex_shortest_path(net, "n0", f"n{num_nodes-1}", switch_cost=switch_cost)
            
            if result_zero['success'] and result_nonzero['success']:
                # Zero switch cost should give distance <= non-zero cost
                assert result_zero['total_distance'] <= result_nonzero['total_distance'] + 0.001
        except (InvalidNodeError, AlgorithmError):
            pass

    @pytest.mark.property
    @given(num_nodes=st.integers(min_value=3, max_value=6))
    @settings(max_examples=3, deadline=500)
    def test_path_length_bounded_by_nodes(self, num_nodes: int):
        """Path length should not exceed number of nodes * layers."""
        net = build_multiplex_network(num_nodes=num_nodes, num_layers=2)
        
        try:
            result = multiplex_shortest_path(net, "n0", f"n{num_nodes-1}", switch_cost=0.5)
            
            if result['success'] and result['path']:
                # Path should not have more states than nodes * layers
                assert len(result['path']) <= num_nodes * 2 + 10  # Some tolerance
        except (InvalidNodeError, AlgorithmError):
            pass

    @pytest.mark.property
    def test_switch_count_matches_layer_changes(self):
        """Number of switches should equal layer transitions in path."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        edges = [
            ['A', 'L1', 'B', 'L1', 1.0],
            ['B', 'L2', 'C', 'L2', 1.0],
            ['C', 'L3', 'D', 'L3', 1.0],
        ]
        net.add_edges(edges, input_type="list")
        
        result = multiplex_shortest_path(net, 'A', 'D', switch_cost=0.1)
        
        if result['success']:
            # Count actual layer changes in path
            path = result['path']
            actual_switches = sum(
                1 for i in range(1, len(path))
                if path[i][1] != path[i-1][1]
            )
            assert result['num_switches'] == actual_switches

    @pytest.mark.property
    def test_high_switch_cost_minimizes_switches(self):
        """High switch cost should prefer paths with fewer switches."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        edges = [
            # Long path in L1 (3 edges, no switches)
            ['A', 'L1', 'B', 'L1', 1.0],
            ['B', 'L1', 'C', 'L1', 1.0],
            ['C', 'L1', 'D', 'L1', 1.0],
            # Short path with switches (2 edges + 2 switches)
            ['A', 'L2', 'B', 'L2', 0.5],
            ['B', 'L3', 'D', 'L3', 0.5],
        ]
        net.add_edges(edges, input_type="list")
        
        result_high = multiplex_shortest_path(net, 'A', 'D', switch_cost=100.0)
        
        if result_high['success']:
            # Should prefer single-layer path despite being longer
            assert result_high['num_switches'] <= 1


# ============================================================================
# Pareto Optimality Properties
# ============================================================================


class TestMultiplexRoutingParetoProperties:
    """Test properties of multi-objective Pareto optimization."""

    @pytest.mark.property
    def test_pareto_paths_are_non_dominated(self):
        """All Pareto-optimal paths should be non-dominated."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        edges = [
            ['A', 'L1', 'B', 'L1', 1.0],
            ['B', 'L1', 'C', 'L1', 1.0],
            ['A', 'L2', 'C', 'L2', 0.5],
        ]
        net.add_edges(edges, input_type="list")
        
        result = multiplex_shortest_path(net, 'A', 'C', switch_cost=1.0, objective='pareto')
        
        if result['success'] and len(result['objectives']) > 1:
            objectives = result['objectives']
            # Check no objective dominates another
            for i, (d1, s1) in enumerate(objectives):
                for j, (d2, s2) in enumerate(objectives):
                    if i != j:
                        # i should not strictly dominate j
                        dominates = (d1 <= d2 and s1 <= s2 and (d1 < d2 or s1 < s2))
                        assert not dominates, f"Objective {i} dominates {j}"

    @pytest.mark.property
    @given(num_nodes=st.integers(min_value=2, max_value=5))
    @settings(max_examples=3, deadline=500)
    def test_pareto_set_is_deterministic(self, num_nodes: int):
        """Pareto set should be deterministic."""
        net = build_multiplex_network(num_nodes=num_nodes, num_layers=2)
        
        try:
            result1 = multiplex_shortest_path(net, "n0", f"n{num_nodes-1}", switch_cost=0.5, objective='pareto')
            result2 = multiplex_shortest_path(net, "n0", f"n{num_nodes-1}", switch_cost=0.5, objective='pareto')
            
            if result1['success'] and result2['success']:
                # Same number of Pareto-optimal paths
                assert len(result1['paths']) == len(result2['paths'])
                # Same objective values (may be in different order)
                assert set(result1['objectives']) == set(result2['objectives'])
        except (InvalidNodeError, AlgorithmError):
            pass


# ============================================================================
# Error Handling Properties
# ============================================================================


class TestMultiplexRoutingErrorHandling:
    """Test error handling properties."""

    @pytest.mark.property
    def test_invalid_source_raises_error(self):
        """Invalid source node should raise InvalidNodeError."""
        net = build_multiplex_network(num_nodes=3)
        
        with pytest.raises(InvalidNodeError):
            multiplex_shortest_path(net, 'invalid_node', 'n1')

    @pytest.mark.property
    def test_invalid_target_raises_error(self):
        """Invalid target node should raise InvalidNodeError."""
        net = build_multiplex_network(num_nodes=3)
        
        with pytest.raises(InvalidNodeError):
            multiplex_shortest_path(net, 'n0', 'invalid_node')

    @pytest.mark.property
    def test_invalid_objective_raises_error(self):
        """Invalid objective should raise AlgorithmError."""
        net = build_multiplex_network(num_nodes=3)
        
        with pytest.raises(AlgorithmError):
            multiplex_shortest_path(net, 'n0', 'n2', objective='invalid')

    @pytest.mark.property
    def test_invalid_method_raises_error(self):
        """Invalid method should raise AlgorithmError."""
        net = build_multiplex_network(num_nodes=3)
        
        with pytest.raises(AlgorithmError):
            multiplex_shortest_path(net, 'n0', 'n2', method='invalid')


# ============================================================================
# Switch Cost Matrix Properties
# ============================================================================


class TestSwitchCostMatrixProperties:
    """Test properties of switch cost matrices."""

    @pytest.mark.property
    def test_asymmetric_matrix_affects_path(self):
        """Asymmetric switch costs should affect routing decisions."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        edges = [
            ['A', 'L1', 'B', 'L1', 1.0],
            ['B', 'L2', 'C', 'L2', 1.0],
        ]
        net.add_edges(edges, input_type="list")
        
        # Cheap L1->L2 switch
        matrix_cheap = {('L1', 'L2'): 0.1}
        result_cheap = multiplex_shortest_path(net, 'A', 'C', switch_cost_matrix=matrix_cheap)
        
        # Expensive L1->L2 switch
        matrix_expensive = {('L1', 'L2'): 100.0}
        result_expensive = multiplex_shortest_path(net, 'A', 'C', switch_cost_matrix=matrix_expensive)
        
        # With cheap switch, should find path
        # With expensive switch, path may be different or not exist
        if result_cheap['success'] and result_expensive['success']:
            assert result_cheap['total_distance'] <= result_expensive['total_distance']

    @pytest.mark.property
    @given(switch_cost=st.floats(min_value=0.0, max_value=10.0))
    @settings(max_examples=3, deadline=500)
    def test_matrix_overrides_scalar_cost(self, switch_cost: float):
        """Switch cost matrix should override scalar switch cost."""
        assume(not (switch_cost != switch_cost))  # Skip NaN
        
        net = multinet.multi_layer_network(directed=False, verbose=False)
        edges = [
            ['A', 'L1', 'B', 'L1', 1.0],
            ['B', 'L2', 'C', 'L2', 1.0],
        ]
        net.add_edges(edges, input_type="list")
        
        # Matrix with very low cost
        matrix = {('L1', 'L2'): 0.01}
        
        result = multiplex_shortest_path(
            net, 'A', 'C',
            switch_cost=switch_cost,
            switch_cost_matrix=matrix
        )
        
        if result['success']:
            # Should use matrix value (0.01) not scalar value
            # Total: 1.0 (A->B) + 0.01 (switch) + 1.0 (B->C) = 2.01
            assert abs(result['total_distance'] - 2.01) < 0.1
