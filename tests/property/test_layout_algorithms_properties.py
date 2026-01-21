#!/usr/bin/env python3
"""
Property-based tests for visualization.layout_algorithms module.

Tests invariants and properties of graph layout algorithms:
- Layout returns positions for all nodes
- Position coordinates are finite (no NaN or Inf)
- Layout is deterministic with same seed
- Position dictionary keys match graph nodes
"""

import networkx as nx
import numpy as np
import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

# Import shared strategies
from .strategies import (
    small_graphs,
    connected_graphs,
)

# Import layout_algorithms module
try:
    from py3plex.visualization.layout_algorithms import (
        compute_force_directed_layout,
    )
    LAYOUT_AVAILABLE = True
except ImportError:
    LAYOUT_AVAILABLE = False
    pytest.skip("Layout algorithms module not available", allow_module_level=True)


# ============================================================================
# Property Tests: Force-Directed Layout
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=2, max_value=15),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_force_directed_layout_all_nodes_present(num_nodes, seed):
    """Property: Layout returns positions for all nodes."""
    G = nx.gnp_random_graph(num_nodes, 0.5, seed=seed)
    assume(G.number_of_edges() > 0)
    
    # Compute layout (use fallback spring layout, not ForceAtlas2)
    layout = compute_force_directed_layout(G, forceImport=False, seed=seed)
    
    # Should have position for every node
    assert len(layout) == num_nodes, \
        f"Layout should have {num_nodes} positions, got {len(layout)}"
    
    # All nodes should be in layout
    assert set(layout.keys()) == set(G.nodes()), \
        "Layout keys should match graph nodes"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=2, max_value=15),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_force_directed_layout_finite_coordinates(num_nodes, seed):
    """Property: All position coordinates are finite (no NaN or Inf)."""
    G = nx.gnp_random_graph(num_nodes, 0.5, seed=seed)
    assume(G.number_of_edges() > 0)
    
    layout = compute_force_directed_layout(G, forceImport=False, seed=seed)
    
    # Check all coordinates are finite
    for node, pos in layout.items():
        assert isinstance(pos, np.ndarray), f"Position should be numpy array for node {node}"
        assert len(pos) == 2, f"Position should be 2D for node {node}"
        assert np.all(np.isfinite(pos)), \
            f"Position coordinates should be finite for node {node}, got {pos}"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=2, max_value=15),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_force_directed_layout_reproducibility(num_nodes, seed):
    """Property: Same seed produces identical layouts."""
    G = nx.gnp_random_graph(num_nodes, 0.5, seed=seed)
    assume(G.number_of_edges() > 0)
    
    layout1 = compute_force_directed_layout(G, forceImport=False, seed=seed)
    layout2 = compute_force_directed_layout(G, forceImport=False, seed=seed)
    
    # Layouts should be identical
    assert set(layout1.keys()) == set(layout2.keys())
    for node in layout1.keys():
        assert np.allclose(layout1[node], layout2[node], atol=1e-6), \
            f"Positions should be identical for node {node}"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=2, max_value=12),
    gravity=st.floats(min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_force_directed_layout_gravity_parameter(num_nodes, gravity, seed):
    """Property: Layout respects gravity parameter bounds."""
    G = nx.gnp_random_graph(num_nodes, 0.5, seed=seed)
    assume(G.number_of_edges() > 0)
    
    # Should complete without error
    layout = compute_force_directed_layout(G, gravity=gravity, forceImport=False, seed=seed)
    
    assert len(layout) == num_nodes


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=2, max_value=12),
    scaling=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_force_directed_layout_scaling_parameter(num_nodes, scaling, seed):
    """Property: Layout respects scalingRatio parameter bounds."""
    G = nx.gnp_random_graph(num_nodes, 0.5, seed=seed)
    assume(G.number_of_edges() > 0)
    
    # Should complete without error
    layout = compute_force_directed_layout(G, scalingRatio=scaling, forceImport=False, seed=seed)
    
    assert len(layout) == num_nodes


# ============================================================================
# Property Tests: Layout Edge Cases
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=2, max_value=10)
)
def test_layout_complete_graph(num_nodes):
    """Property: Layout works correctly for complete graphs."""
    G = nx.complete_graph(num_nodes)
    
    layout = compute_force_directed_layout(G, forceImport=False, seed=42)
    
    # Should have positions for all nodes
    assert len(layout) == num_nodes
    
    # All positions should be finite
    for node, pos in layout.items():
        assert np.all(np.isfinite(pos))


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=15)
)
def test_layout_star_graph(num_nodes):
    """Property: Layout works for star graphs."""
    G = nx.star_graph(num_nodes - 1)
    
    layout = compute_force_directed_layout(G, forceImport=False, seed=42)
    
    # Should have positions for all nodes
    assert len(layout) == num_nodes
    
    # Center node (0) should exist
    assert 0 in layout


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=15)
)
def test_layout_path_graph(num_nodes):
    """Property: Layout works for path graphs."""
    G = nx.path_graph(num_nodes)
    
    layout = compute_force_directed_layout(G, forceImport=False, seed=42)
    
    # Should have positions for all nodes
    assert len(layout) == num_nodes


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=15)
)
def test_layout_cycle_graph(num_nodes):
    """Property: Layout works for cycle graphs."""
    G = nx.cycle_graph(num_nodes)
    
    layout = compute_force_directed_layout(G, forceImport=False, seed=42)
    
    # Should have positions for all nodes
    assert len(layout) == num_nodes


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=5, max_value=15),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_layout_disconnected_graph(num_nodes, seed):
    """Property: Layout handles disconnected graphs."""
    # Create a disconnected graph with two components
    half = num_nodes // 2
    G = nx.Graph()
    
    # Component 1: complete subgraph on first half nodes
    for i in range(half):
        for j in range(i + 1, half):
            G.add_edge(i, j)
    
    # Component 2: complete subgraph on second half nodes
    for i in range(half, num_nodes):
        for j in range(i + 1, num_nodes):
            G.add_edge(i, j)
    
    # This graph always has edges in both components
    assert G.number_of_edges() > 0
    
    layout = compute_force_directed_layout(G, forceImport=False, seed=seed)
    
    # Should have positions for all nodes
    assert len(layout) == num_nodes


# ============================================================================
# Property Tests: Layout Position Properties
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=12),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_layout_positions_distinct_for_different_nodes(num_nodes, seed):
    """Property: Different nodes should generally have different positions."""
    G = nx.gnp_random_graph(num_nodes, 0.5, seed=seed)
    assume(G.number_of_edges() > 0)
    
    layout = compute_force_directed_layout(G, forceImport=False, seed=seed)
    
    # Collect all positions
    positions = list(layout.values())
    
    # Most positions should be unique (allow some tolerance)
    unique_positions = []
    for pos in positions:
        is_duplicate = False
        for upos in unique_positions:
            if np.allclose(pos, upos, atol=1e-6):
                is_duplicate = True
                break
        if not is_duplicate:
            unique_positions.append(pos)
    
    # At least 80% of positions should be unique
    uniqueness_ratio = len(unique_positions) / len(positions)
    assert uniqueness_ratio >= 0.8, \
        f"Most nodes should have distinct positions, got {uniqueness_ratio:.2f} unique"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'property'])
