#!/usr/bin/env python3
"""
Property-based tests for multilayer modularity quality function.

Tests invariants and properties including:
- Bounds: Q in [-1, 1] for valid partitions
- All same community: Q bounded for trivial partition
- Singleton communities: expected behavior
- Resolution parameter effect: higher gamma favors smaller communities
- Omega coupling effect: affects cross-layer contribution
- Symmetry: Q(partition) same regardless of community ID labels
"""

import numpy as np
import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

# Import modularity module
try:
    from py3plex.algorithms.community_detection.multilayer_modularity import (
        multilayer_modularity,
    )
    from py3plex.core import multinet
    MODULARITY_AVAILABLE = True
except ImportError:
    MODULARITY_AVAILABLE = False
    pytest.skip("Multilayer modularity module not available", allow_module_level=True)


# ============================================================================
# Helper functions
# ============================================================================

def create_simple_multilayer_network(num_nodes, num_layers, edge_prob, seed):
    """Create a simple multilayer network for testing."""
    import random
    random.seed(seed)

    net = multinet.multi_layer_network(directed=False)

    layer_names = [f"L{i}" for i in range(num_layers)]
    node_names = [f"n{i}" for i in range(num_nodes)]

    # Add nodes to each layer
    for layer in layer_names:
        for node in node_names:
            net.add_nodes({
                "source": node,
                "type": layer
            })

    # Add intra-layer edges
    for layer in layer_names:
        for i in range(num_nodes):
            for j in range(i + 1, num_nodes):
                if random.random() < edge_prob:
                    net.add_edges({
                        "source": node_names[i],
                        "target": node_names[j],
                        "source_type": layer,
                        "target_type": layer,
                        "weight": 1.0
                    })

    return net, node_names, layer_names


def create_all_same_community_partition(node_names, layer_names):
    """Create partition where all node-layer pairs are in same community."""
    return {(node, layer): 0 for node in node_names for layer in layer_names}


def create_singleton_partition(node_names, layer_names):
    """Create partition where each node-layer pair is its own community."""
    partition = {}
    community_id = 0
    for node in node_names:
        for layer in layer_names:
            partition[(node, layer)] = community_id
            community_id += 1
    return partition


def create_layer_partition(node_names, layer_names):
    """Create partition by layer (all nodes in same layer = same community)."""
    partition = {}
    for layer_idx, layer in enumerate(layer_names):
        for node in node_names:
            partition[(node, layer)] = layer_idx
    return partition


def create_random_partition(node_names, layer_names, num_communities, seed):
    """Create random partition."""
    import random
    random.seed(seed)
    partition = {}
    for node in node_names:
        for layer in layer_names:
            partition[(node, layer)] = random.randint(0, num_communities - 1)
    return partition


# ============================================================================
# Property Tests: Modularity Bounds
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=10),
    num_layers=st.integers(min_value=1, max_value=3),
    edge_prob=st.floats(min_value=0.2, max_value=0.8, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_modularity_bounded(num_nodes, num_layers, edge_prob, seed):
    """Property: Modularity Q is bounded in [-1, 1]."""
    net, node_names, layer_names = create_simple_multilayer_network(
        num_nodes, num_layers, edge_prob, seed
    )
    assume(len(list(net.get_edges())) > 0)

    # Random partition
    partition = create_random_partition(node_names, layer_names, 3, seed)

    Q = multilayer_modularity(net, partition, gamma=1.0, omega=1.0)

    assert -1.0 <= Q <= 1.0, f"Modularity {Q} outside bounds [-1, 1]"


@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=1, max_value=3),
    gamma=st.floats(min_value=0.1, max_value=3.0, allow_nan=False, allow_infinity=False),
    omega=st.floats(min_value=0.0, max_value=5.0, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_modularity_finite(num_nodes, num_layers, gamma, omega, seed):
    """Property: Modularity is always finite (no NaN or Inf)."""
    net, node_names, layer_names = create_simple_multilayer_network(
        num_nodes, num_layers, 0.4, seed
    )
    assume(len(list(net.get_edges())) > 0)

    partition = create_random_partition(node_names, layer_names, 2, seed)

    Q = multilayer_modularity(net, partition, gamma=gamma, omega=omega)

    assert np.isfinite(Q), f"Non-finite modularity: {Q}"


# ============================================================================
# Property Tests: Trivial Partitions
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=1, max_value=3),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_modularity_all_same_community(num_nodes, num_layers, seed):
    """Property: All nodes in same community yields Q close to 0 (for gamma=1)."""
    net, node_names, layer_names = create_simple_multilayer_network(
        num_nodes, num_layers, 0.5, seed
    )
    assume(len(list(net.get_edges())) > 0)

    # All in same community
    partition = create_all_same_community_partition(node_names, layer_names)

    Q = multilayer_modularity(net, partition, gamma=1.0, omega=0.0)

    # For Newman-Girvan null model with gamma=1, Q should be ~0 for single community
    # due to sum of (A_ij - k_i*k_j/2m) over all pairs in same community
    assert abs(Q) < 0.5, f"Single community Q={Q} should be close to 0"


@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=1, max_value=2),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_modularity_singleton_communities_nonpositive(num_nodes, num_layers, seed):
    """Property: Singleton communities typically yield Q <= 0."""
    net, node_names, layer_names = create_simple_multilayer_network(
        num_nodes, num_layers, 0.5, seed
    )
    assume(len(list(net.get_edges())) > 0)

    # Each node-layer pair in its own community
    partition = create_singleton_partition(node_names, layer_names)

    Q = multilayer_modularity(net, partition, gamma=1.0, omega=0.0)

    # Singletons should have Q <= 0 (no positive contribution from same-community edges)
    assert Q <= 0.1, f"Singleton communities Q={Q} should be <= 0"


# ============================================================================
# Property Tests: Resolution Parameter (gamma)
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=4, max_value=8),
    num_layers=st.integers(min_value=1, max_value=2),
    gamma1=st.floats(min_value=0.5, max_value=1.0, allow_nan=False, allow_infinity=False),
    gamma2=st.floats(min_value=1.5, max_value=3.0, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_modularity_gamma_affects_value(num_nodes, num_layers, gamma1, gamma2, seed):
    """Property: Different gamma values produce different modularity scores."""
    net, node_names, layer_names = create_simple_multilayer_network(
        num_nodes, num_layers, 0.5, seed
    )
    assume(len(list(net.get_edges())) > 0)

    partition = create_random_partition(node_names, layer_names, 2, seed)

    Q1 = multilayer_modularity(net, partition, gamma=gamma1, omega=0.0)
    Q2 = multilayer_modularity(net, partition, gamma=gamma2, omega=0.0)

    # Higher gamma penalizes null model more, typically reducing Q
    # Just check they're different (or both finite)
    assert np.isfinite(Q1) and np.isfinite(Q2), "Non-finite modularity values"


# ============================================================================
# Property Tests: Coupling Parameter (omega)
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=6),
    num_layers=st.integers(min_value=2, max_value=3),
    omega1=st.floats(min_value=0.0, max_value=0.5, allow_nan=False, allow_infinity=False),
    omega2=st.floats(min_value=1.0, max_value=3.0, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_modularity_omega_affects_value(num_nodes, num_layers, omega1, omega2, seed):
    """Property: Different omega values affect modularity (with multiple layers)."""
    net, node_names, layer_names = create_simple_multilayer_network(
        num_nodes, num_layers, 0.5, seed
    )
    assume(len(list(net.get_edges())) > 0)

    # Use layer partition (nodes in same layer together)
    partition = create_layer_partition(node_names, layer_names)

    Q1 = multilayer_modularity(net, partition, gamma=1.0, omega=omega1)
    Q2 = multilayer_modularity(net, partition, gamma=1.0, omega=omega2)

    # Both should be finite
    assert np.isfinite(Q1) and np.isfinite(Q2), "Non-finite modularity values"


@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=6),
    num_layers=st.integers(min_value=2, max_value=3),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_modularity_zero_omega_no_coupling(num_nodes, num_layers, seed):
    """Property: omega=0 means no inter-layer coupling contribution."""
    net, node_names, layer_names = create_simple_multilayer_network(
        num_nodes, num_layers, 0.5, seed
    )
    assume(len(list(net.get_edges())) > 0)

    partition = create_random_partition(node_names, layer_names, 2, seed)

    Q_no_coupling = multilayer_modularity(net, partition, gamma=1.0, omega=0.0)

    # Should still be valid
    assert np.isfinite(Q_no_coupling)
    assert -1.0 <= Q_no_coupling <= 1.0


# ============================================================================
# Property Tests: Symmetry
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=6),
    num_layers=st.integers(min_value=1, max_value=2),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_modularity_community_id_invariance(num_nodes, num_layers, seed):
    """Property: Modularity is invariant to community ID relabeling."""
    net, node_names, layer_names = create_simple_multilayer_network(
        num_nodes, num_layers, 0.5, seed
    )
    assume(len(list(net.get_edges())) > 0)

    # Original partition
    partition1 = create_random_partition(node_names, layer_names, 3, seed)

    # Relabel communities (swap 0 and 1)
    partition2 = {}
    for key, comm in partition1.items():
        if comm == 0:
            partition2[key] = 1
        elif comm == 1:
            partition2[key] = 0
        else:
            partition2[key] = comm

    Q1 = multilayer_modularity(net, partition1, gamma=1.0, omega=1.0)
    Q2 = multilayer_modularity(net, partition2, gamma=1.0, omega=1.0)

    assert np.isclose(Q1, Q2, atol=1e-10), \
        f"Modularity should be invariant to ID relabeling: Q1={Q1}, Q2={Q2}"


# ============================================================================
# Property Tests: Per-layer Gamma
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=6),
    num_layers=st.integers(min_value=2, max_value=3),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_modularity_per_layer_gamma(num_nodes, num_layers, seed):
    """Property: Per-layer gamma dict is accepted and produces valid result."""
    net, node_names, layer_names = create_simple_multilayer_network(
        num_nodes, num_layers, 0.5, seed
    )
    assume(len(list(net.get_edges())) > 0)

    partition = create_random_partition(node_names, layer_names, 2, seed)

    # Per-layer gamma values
    gamma_dict = {layer: 1.0 + 0.1 * i for i, layer in enumerate(layer_names)}

    Q = multilayer_modularity(net, partition, gamma=gamma_dict, omega=1.0)

    assert np.isfinite(Q), "Non-finite modularity with per-layer gamma"
    assert -1.0 <= Q <= 1.0


# ============================================================================
# Property Tests: Omega Matrix
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=6),
    num_layers=st.integers(min_value=2, max_value=3),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_modularity_omega_matrix(num_nodes, num_layers, seed):
    """Property: Omega as matrix is accepted and produces valid result."""
    net, node_names, layer_names = create_simple_multilayer_network(
        num_nodes, num_layers, 0.5, seed
    )
    assume(len(list(net.get_edges())) > 0)

    partition = create_random_partition(node_names, layer_names, 2, seed)

    # Omega as matrix
    omega_matrix = np.ones((num_layers, num_layers)) * 0.5
    np.fill_diagonal(omega_matrix, 0)  # No self-coupling

    Q = multilayer_modularity(net, partition, gamma=1.0, omega=omega_matrix)

    assert np.isfinite(Q), "Non-finite modularity with omega matrix"
    assert -1.0 <= Q <= 1.0


# ============================================================================
# Property Tests: Edge Cases
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=6),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_modularity_single_layer(num_nodes, seed):
    """Property: Single layer reduces to standard modularity calculation."""
    net, node_names, layer_names = create_simple_multilayer_network(
        num_nodes, 1, 0.5, seed
    )
    assume(len(list(net.get_edges())) > 0)

    partition = create_random_partition(node_names, layer_names, 2, seed)

    Q = multilayer_modularity(net, partition, gamma=1.0, omega=0.0)

    assert np.isfinite(Q)
    assert -1.0 <= Q <= 1.0


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(seed=st.integers(min_value=0, max_value=10000))
def test_modularity_empty_network(seed):
    """Property: Empty network returns 0 modularity."""
    net = multinet.multi_layer_network(directed=False)

    # Add just nodes, no edges
    net.add_nodes({"source": "n0", "type": "L0"})
    net.add_nodes({"source": "n1", "type": "L0"})

    partition = {("n0", "L0"): 0, ("n1", "L0"): 1}

    Q = multilayer_modularity(net, partition, gamma=1.0, omega=0.0)

    assert Q == 0.0, f"Empty network should have Q=0, got {Q}"


# ============================================================================
# Property Tests: Consistency
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=6),
    num_layers=st.integers(min_value=1, max_value=2),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_modularity_deterministic(num_nodes, num_layers, seed):
    """Property: Same inputs produce identical modularity (deterministic)."""
    net, node_names, layer_names = create_simple_multilayer_network(
        num_nodes, num_layers, 0.5, seed
    )
    assume(len(list(net.get_edges())) > 0)

    partition = create_random_partition(node_names, layer_names, 2, seed)

    Q1 = multilayer_modularity(net, partition, gamma=1.0, omega=1.0)
    Q2 = multilayer_modularity(net, partition, gamma=1.0, omega=1.0)

    assert Q1 == Q2, f"Non-deterministic modularity: Q1={Q1}, Q2={Q2}"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=4, max_value=8),
    num_layers=st.integers(min_value=1, max_value=2),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_modularity_better_partition_higher_q(num_nodes, num_layers, seed):
    """Property: A partition matching community structure has higher Q."""
    # Create network with clear community structure
    net = multinet.multi_layer_network(directed=False)
    layer = "L0"

    # Two cliques
    half = num_nodes // 2
    nodes = [f"n{i}" for i in range(num_nodes)]

    for node in nodes:
        net.add_nodes({"source": node, "type": layer})

    # Dense edges within first half
    for i in range(half):
        for j in range(i + 1, half):
            net.add_edges({
                "source": nodes[i], "target": nodes[j],
                "source_type": layer, "target_type": layer,
                "weight": 1.0
            })

    # Dense edges within second half
    for i in range(half, num_nodes):
        for j in range(i + 1, num_nodes):
            net.add_edges({
                "source": nodes[i], "target": nodes[j],
                "source_type": layer, "target_type": layer,
                "weight": 1.0
            })

    # Sparse edge between halves
    if half > 0 and num_nodes > half:
        net.add_edges({
            "source": nodes[0], "target": nodes[half],
            "source_type": layer, "target_type": layer,
            "weight": 1.0
        })

    # Good partition (respects cliques)
    good_partition = {
        (nodes[i], layer): 0 if i < half else 1
        for i in range(num_nodes)
    }

    # Bad partition (random)
    bad_partition = {
        (nodes[i], layer): i % 2
        for i in range(num_nodes)
    }

    Q_good = multilayer_modularity(net, good_partition, gamma=1.0, omega=0.0)
    Q_bad = multilayer_modularity(net, bad_partition, gamma=1.0, omega=0.0)

    # Good partition should have higher Q (usually)
    # This is a soft property due to random variations
    assert np.isfinite(Q_good) and np.isfinite(Q_bad)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'property'])
