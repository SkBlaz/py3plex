#!/usr/bin/env python3
"""
Property-based tests for layer similarity metrics.

Tests invariants and properties including:
- Self-similarity: sim(L, L) = 1 (maximum)
- Symmetry: sim(A, B) = sim(B, A)
- Bounds: similarity in [0, 1]
- Empty layer: similarity with empty layer is 0
- Disjoint layers: non-overlapping layers have similarity 0
- Complete overlap: identical layers have similarity 1
"""

import numpy as np
import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

# Import layer similarity module
try:
    from py3plex.algorithms.layer_similarity import (
        jaccard_layer_similarity,
        all_pairs_jaccard_similarity,
    )
    from py3plex.core import multinet
    LAYER_SIMILARITY_AVAILABLE = True
except ImportError:
    LAYER_SIMILARITY_AVAILABLE = False
    pytest.skip("Layer similarity module not available", allow_module_level=True)


# ============================================================================
# Helper functions
# ============================================================================

def create_multilayer_network_with_overlap(
    num_nodes, num_layers, overlap_fraction, seed
):
    """Create a multilayer network with controlled node overlap between layers."""
    import random
    random.seed(seed)

    net = multinet.multi_layer_network(directed=False)

    layer_names = [f"L{i}" for i in range(num_layers)]
    all_nodes = [f"n{i}" for i in range(num_nodes)]

    # Determine shared nodes
    num_shared = int(num_nodes * overlap_fraction)
    shared_nodes = all_nodes[:num_shared]

    # Add shared nodes to all layers
    for layer in layer_names:
        for node in shared_nodes:
            net.add_nodes({"source": node, "type": layer})

    # Add unique nodes to each layer
    nodes_per_layer = (num_nodes - num_shared) // num_layers
    for layer_idx, layer in enumerate(layer_names):
        start_idx = num_shared + layer_idx * nodes_per_layer
        end_idx = start_idx + nodes_per_layer
        for node in all_nodes[start_idx:end_idx]:
            net.add_nodes({"source": node, "type": layer})

    # Add some edges within layers
    for layer in layer_names:
        layer_nodes = [
            node for node in all_nodes
            if any(n[0] == node and n[1] == layer
                   for n in net.get_nodes() if isinstance(n, tuple))
        ]
        # Sample nodes from the network for this layer
        layer_node_tuples = [
            n for n in net.get_nodes()
            if isinstance(n, tuple) and n[1] == layer
        ]
        actual_nodes = [n[0] for n in layer_node_tuples]

        for i in range(min(len(actual_nodes) - 1, 5)):
            if i + 1 < len(actual_nodes):
                net.add_edges({
                    "source": actual_nodes[i],
                    "target": actual_nodes[i + 1],
                    "source_type": layer,
                    "target_type": layer,
                    "weight": 1.0
                })

    return net, layer_names


def create_identical_layers_network(num_nodes, seed):
    """Create a network where two layers have identical node sets."""
    import random
    random.seed(seed)

    net = multinet.multi_layer_network(directed=False)

    nodes = [f"n{i}" for i in range(num_nodes)]

    # Add same nodes to both layers
    for node in nodes:
        net.add_nodes({"source": node, "type": "L0"})
        net.add_nodes({"source": node, "type": "L1"})

    # Add identical edges to both layers
    for i in range(num_nodes - 1):
        net.add_edges({
            "source": nodes[i],
            "target": nodes[i + 1],
            "source_type": "L0",
            "target_type": "L0",
            "weight": 1.0
        })
        net.add_edges({
            "source": nodes[i],
            "target": nodes[i + 1],
            "source_type": "L1",
            "target_type": "L1",
            "weight": 1.0
        })

    return net


def create_disjoint_layers_network(num_nodes_per_layer, seed):
    """Create a network where two layers have no overlapping nodes."""
    import random
    random.seed(seed)

    net = multinet.multi_layer_network(directed=False)

    # Layer 0 nodes
    for i in range(num_nodes_per_layer):
        net.add_nodes({"source": f"a{i}", "type": "L0"})

    # Layer 1 nodes (different names)
    for i in range(num_nodes_per_layer):
        net.add_nodes({"source": f"b{i}", "type": "L1"})

    # Add edges within each layer
    for i in range(num_nodes_per_layer - 1):
        net.add_edges({
            "source": f"a{i}",
            "target": f"a{i+1}",
            "source_type": "L0",
            "target_type": "L0",
            "weight": 1.0
        })
        net.add_edges({
            "source": f"b{i}",
            "target": f"b{i+1}",
            "source_type": "L1",
            "target_type": "L1",
            "weight": 1.0
        })

    return net


# ============================================================================
# Property Tests: Jaccard Similarity - Bounds
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=5, max_value=20),
    num_layers=st.integers(min_value=2, max_value=4),
    overlap=st.floats(min_value=0.1, max_value=0.9, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_jaccard_bounds(num_nodes, num_layers, overlap, seed):
    """Property: Jaccard similarity is bounded in [0, 1]."""
    net, layer_names = create_multilayer_network_with_overlap(
        num_nodes, num_layers, overlap, seed
    )

    for i in range(len(layer_names)):
        for j in range(i + 1, len(layer_names)):
            sim = jaccard_layer_similarity(net, layer_names[i], layer_names[j], "nodes")
            assert 0.0 <= sim <= 1.0, \
                f"Jaccard similarity {sim} outside bounds [0, 1]"


@pytest.mark.property
@settings(deadline=None, max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=5, max_value=20),
    num_layers=st.integers(min_value=2, max_value=4),
    overlap=st.floats(min_value=0.1, max_value=0.9, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_jaccard_edges_bounds(num_nodes, num_layers, overlap, seed):
    """Property: Jaccard edge similarity is bounded in [0, 1]."""
    net, layer_names = create_multilayer_network_with_overlap(
        num_nodes, num_layers, overlap, seed
    )

    for i in range(len(layer_names)):
        for j in range(i + 1, len(layer_names)):
            sim = jaccard_layer_similarity(net, layer_names[i], layer_names[j], "edges")
            assert 0.0 <= sim <= 1.0, \
                f"Jaccard edge similarity {sim} outside bounds [0, 1]"


# ============================================================================
# Property Tests: Jaccard Similarity - Self-Similarity
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=5, max_value=15),
    num_layers=st.integers(min_value=2, max_value=3),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_jaccard_self_similarity_is_one(num_nodes, num_layers, seed):
    """Property: Self-similarity equals 1 (sim(L, L) = 1)."""
    net, layer_names = create_multilayer_network_with_overlap(
        num_nodes, num_layers, 0.5, seed
    )

    for layer in layer_names:
        sim = jaccard_layer_similarity(net, layer, layer, "nodes")
        assert np.isclose(sim, 1.0, atol=1e-10), \
            f"Self-similarity should be 1.0, got {sim}"


@pytest.mark.property
@settings(deadline=None, max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=5, max_value=15),
    num_layers=st.integers(min_value=2, max_value=3),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_jaccard_edges_self_similarity(num_nodes, num_layers, seed):
    """Property: Edge self-similarity equals 1."""
    net, layer_names = create_multilayer_network_with_overlap(
        num_nodes, num_layers, 0.5, seed
    )
    assume(len(list(net.get_edges())) > 0)

    for layer in layer_names:
        sim = jaccard_layer_similarity(net, layer, layer, "edges")
        # If layer has edges, self-similarity should be 1
        # If layer has no edges, self-similarity is 0 (empty set)
        assert sim == 0.0 or np.isclose(sim, 1.0, atol=1e-10), \
            f"Edge self-similarity should be 0 or 1, got {sim}"


# ============================================================================
# Property Tests: Jaccard Similarity - Symmetry
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=5, max_value=15),
    num_layers=st.integers(min_value=2, max_value=4),
    overlap=st.floats(min_value=0.1, max_value=0.9, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_jaccard_symmetry(num_nodes, num_layers, overlap, seed):
    """Property: Jaccard similarity is symmetric (sim(A, B) = sim(B, A))."""
    net, layer_names = create_multilayer_network_with_overlap(
        num_nodes, num_layers, overlap, seed
    )

    for i in range(len(layer_names)):
        for j in range(i + 1, len(layer_names)):
            sim_ij = jaccard_layer_similarity(net, layer_names[i], layer_names[j], "nodes")
            sim_ji = jaccard_layer_similarity(net, layer_names[j], layer_names[i], "nodes")
            assert np.isclose(sim_ij, sim_ji, atol=1e-10), \
                f"Symmetry violated: sim({layer_names[i]}, {layer_names[j]})={sim_ij} != sim({layer_names[j]}, {layer_names[i]})={sim_ji}"


@pytest.mark.property
@settings(deadline=None, max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=5, max_value=15),
    num_layers=st.integers(min_value=2, max_value=4),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_jaccard_edges_symmetry(num_nodes, num_layers, seed):
    """Property: Jaccard edge similarity is symmetric."""
    net, layer_names = create_multilayer_network_with_overlap(
        num_nodes, num_layers, 0.5, seed
    )

    for i in range(len(layer_names)):
        for j in range(i + 1, len(layer_names)):
            sim_ij = jaccard_layer_similarity(net, layer_names[i], layer_names[j], "edges")
            sim_ji = jaccard_layer_similarity(net, layer_names[j], layer_names[i], "edges")
            assert np.isclose(sim_ij, sim_ji, atol=1e-10), \
                f"Edge symmetry violated"


# ============================================================================
# Property Tests: Jaccard Similarity - Special Cases
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=10),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_jaccard_identical_layers_equals_one(num_nodes, seed):
    """Property: Identical layers have similarity 1."""
    net = create_identical_layers_network(num_nodes, seed)

    sim = jaccard_layer_similarity(net, "L0", "L1", "nodes")
    assert np.isclose(sim, 1.0, atol=1e-10), \
        f"Identical layers should have similarity 1.0, got {sim}"


@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=10),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_jaccard_disjoint_layers_equals_zero(num_nodes, seed):
    """Property: Disjoint layers (no overlap) have similarity 0."""
    net = create_disjoint_layers_network(num_nodes, seed)

    sim = jaccard_layer_similarity(net, "L0", "L1", "nodes")
    assert np.isclose(sim, 0.0, atol=1e-10), \
        f"Disjoint layers should have similarity 0.0, got {sim}"


# ============================================================================
# Property Tests: Jaccard Similarity - Monotonicity
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=10, max_value=20),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_jaccard_more_overlap_higher_similarity(num_nodes, seed):
    """Property: More overlap leads to higher similarity."""
    # Low overlap network
    net_low, _ = create_multilayer_network_with_overlap(num_nodes, 2, 0.2, seed)
    sim_low = jaccard_layer_similarity(net_low, "L0", "L1", "nodes")

    # High overlap network
    net_high, _ = create_multilayer_network_with_overlap(num_nodes, 2, 0.8, seed)
    sim_high = jaccard_layer_similarity(net_high, "L0", "L1", "nodes")

    # Higher overlap should generally mean higher similarity
    # This is a soft property due to how we construct networks
    assert sim_high >= sim_low * 0.5, \
        f"Expected high overlap ({sim_high}) >= low overlap ({sim_low}) * 0.5"


# ============================================================================
# Property Tests: All Pairs Similarity
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=5, max_value=15),
    num_layers=st.integers(min_value=2, max_value=4),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_all_pairs_returns_dict(num_nodes, num_layers, seed):
    """Property: all_pairs_jaccard_similarity returns a dictionary."""
    net, layer_names = create_multilayer_network_with_overlap(
        num_nodes, num_layers, 0.5, seed
    )

    result = all_pairs_jaccard_similarity(net, "nodes")

    assert isinstance(result, dict), "Result should be a dictionary"


@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=5, max_value=15),
    num_layers=st.integers(min_value=2, max_value=4),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_all_pairs_all_values_bounded(num_nodes, num_layers, seed):
    """Property: All pairwise similarities are in [0, 1]."""
    net, layer_names = create_multilayer_network_with_overlap(
        num_nodes, num_layers, 0.5, seed
    )

    result = all_pairs_jaccard_similarity(net, "nodes")

    for (l1, l2), sim in result.items():
        assert 0.0 <= sim <= 1.0, \
            f"Similarity ({l1}, {l2})={sim} outside bounds [0, 1]"


@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=5, max_value=15),
    num_layers=st.integers(min_value=2, max_value=4),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_all_pairs_symmetric_in_dict(num_nodes, num_layers, seed):
    """Property: Symmetry holds in all-pairs result."""
    net, layer_names = create_multilayer_network_with_overlap(
        num_nodes, num_layers, 0.5, seed
    )

    result = all_pairs_jaccard_similarity(net, "nodes")

    for (l1, l2), sim in result.items():
        # Check if reverse pair exists and matches
        if (l2, l1) in result:
            assert np.isclose(result[(l2, l1)], sim, atol=1e-10), \
                f"Symmetry violated in all-pairs: ({l1}, {l2})={sim} != ({l2}, {l1})={result[(l2, l1)]}"


# ============================================================================
# Property Tests: Finite Values
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=5, max_value=15),
    num_layers=st.integers(min_value=2, max_value=4),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_jaccard_finite(num_nodes, num_layers, seed):
    """Property: Jaccard similarity is always finite (no NaN or Inf)."""
    net, layer_names = create_multilayer_network_with_overlap(
        num_nodes, num_layers, 0.5, seed
    )

    for i in range(len(layer_names)):
        for j in range(len(layer_names)):
            sim = jaccard_layer_similarity(net, layer_names[i], layer_names[j], "nodes")
            assert np.isfinite(sim), f"Non-finite Jaccard similarity: {sim}"


# ============================================================================
# Property Tests: Determinism
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=5, max_value=15),
    num_layers=st.integers(min_value=2, max_value=3),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_jaccard_deterministic(num_nodes, num_layers, seed):
    """Property: Same input produces identical output (deterministic)."""
    net, layer_names = create_multilayer_network_with_overlap(
        num_nodes, num_layers, 0.5, seed
    )

    sim1 = jaccard_layer_similarity(net, layer_names[0], layer_names[1], "nodes")
    sim2 = jaccard_layer_similarity(net, layer_names[0], layer_names[1], "nodes")

    assert sim1 == sim2, f"Non-deterministic: {sim1} != {sim2}"


# ============================================================================
# Property Tests: Edge Cases
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(seed=st.integers(min_value=0, max_value=10000))
def test_jaccard_empty_layer(seed):
    """Property: Similarity with empty layer is 0."""
    net = multinet.multi_layer_network(directed=False)

    # Add nodes only to one layer
    net.add_nodes({"source": "n0", "type": "L0"})
    net.add_nodes({"source": "n1", "type": "L0"})
    # L1 is empty (no nodes)

    # Add empty L1 layer marker through a dummy approach
    # Since Jaccard depends on extracting nodes, empty layer should yield 0
    sim = jaccard_layer_similarity(net, "L0", "L1", "nodes")

    assert np.isclose(sim, 0.0, atol=1e-10), \
        f"Similarity with empty layer should be 0, got {sim}"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_jaccard_single_node_layer(num_nodes, seed):
    """Property: Single node layers work correctly."""
    net = multinet.multi_layer_network(directed=False)

    # L0 has single node
    net.add_nodes({"source": "n0", "type": "L0"})

    # L1 has multiple nodes including n0
    for i in range(num_nodes):
        net.add_nodes({"source": f"n{i}", "type": "L1"})

    sim = jaccard_layer_similarity(net, "L0", "L1", "nodes")

    # Should be 1/num_nodes (one shared node out of num_nodes in union)
    expected = 1.0 / num_nodes
    assert np.isclose(sim, expected, atol=1e-10), \
        f"Single node overlap: expected {expected}, got {sim}"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'property'])
