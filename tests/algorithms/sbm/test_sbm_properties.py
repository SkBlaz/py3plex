"""
Property-based tests for multilayer SBM.

This module tests SBM properties using Hypothesis for property-based testing,
ensuring correctness across a wide range of inputs.
"""

import numpy as np
import pytest

try:
    from hypothesis import given, strategies as st, assume, settings
    from hypothesis.strategies import integers, floats, lists
    HYPOTHESIS_AVAILABLE = True
except ImportError:
    HYPOTHESIS_AVAILABLE = False
    pytest.skip("hypothesis not available", allow_module_level=True)

from py3plex.core import multinet
from py3plex.algorithms.sbm import fit_multilayer_sbm, SBMFittedModel
from py3plex.algorithms.sbm.utils import compute_ari, compute_nmi


def generate_multilayer_network_from_edges(n_nodes, edge_list_per_layer):
    """
    Generate a node-aligned multilayer network from edge lists.
    
    Args:
        n_nodes: Number of nodes
        edge_list_per_layer: List of (layer_name, [(u, v), ...])
    
    Returns:
        py3plex multi_layer_network
    """
    net = multinet.multi_layer_network(directed=False)
    
    # Ensure all nodes exist in all layers
    layer_names = [name for name, _ in edge_list_per_layer]
    for node_id in range(n_nodes):
        for layer in layer_names:
            # Add edge to ensure node exists
            net.add_edges([{
                'source': node_id,
                'target': (node_id + 1) % max(n_nodes, 2),
                'source_type': layer,
                'target_type': layer
            }])
    
    # Add the actual edges
    for layer_name, edges in edge_list_per_layer:
        for u, v in edges:
            if u != v and 0 <= u < n_nodes and 0 <= v < n_nodes:
                net.add_edges([{
                    'source': u,
                    'target': v,
                    'source_type': layer_name,
                    'target_type': layer_name
                }])
    
    return net


@pytest.mark.property
@settings(max_examples=10, deadline=5000)
@given(
    n_nodes=integers(min_value=4, max_value=12),
    n_blocks=integers(min_value=2, max_value=3),
    n_layers=integers(min_value=1, max_value=3),
    seed=integers(min_value=0, max_value=100)
)
def test_sbm_output_shapes(n_nodes, n_blocks, n_layers, seed):
    """Property: SBM output shapes should be correct regardless of input."""
    # Generate random edges
    np.random.seed(seed)
    
    edge_lists = []
    for layer_idx in range(n_layers):
        layer_name = f'L{layer_idx}'
        edges = []
        # Generate some random edges
        for _ in range(min(n_nodes, 10)):
            u = np.random.randint(0, n_nodes)
            v = np.random.randint(0, n_nodes)
            if u != v:
                edges.append((u, v))
        edge_lists.append((layer_name, edges))
    
    # Create network
    net = generate_multilayer_network_from_edges(n_nodes, edge_lists)
    
    # Fit SBM
    model = fit_multilayer_sbm(
        net,
        n_blocks=n_blocks,
        model="sbm",
        n_init=1,
        max_iter=20,
        verbose=False,
        seed=seed
    )
    
    # Check output shapes
    assert model.memberships_.shape == (n_nodes, n_blocks)
    assert model.hard_membership_.shape == (n_nodes,)
    assert len(model.elbo_history_) > 0
    assert model.K_ == n_blocks
    
    # Check membership probabilities sum to 1
    membership_sums = model.memberships_.sum(axis=1)
    np.testing.assert_allclose(membership_sums, np.ones(n_nodes), rtol=1e-5)
    
    # Check hard assignments are valid
    assert all(0 <= label < n_blocks for label in model.hard_membership_)


@pytest.mark.property
@settings(max_examples=10, deadline=5000)
@given(
    n_nodes=integers(min_value=6, max_value=10),
    n_layers=integers(min_value=1, max_value=2),
    seed=integers(min_value=0, max_value=50)
)
def test_dc_sbm_degree_params_positive(n_nodes, n_layers, seed):
    """Property: DC-SBM degree parameters should always be positive."""
    np.random.seed(seed)
    
    # Generate network with some edges
    edge_lists = []
    for layer_idx in range(n_layers):
        layer_name = f'L{layer_idx}'
        edges = [(i, (i+1) % n_nodes) for i in range(n_nodes)]
        edge_lists.append((layer_name, edges))
    
    net = generate_multilayer_network_from_edges(n_nodes, edge_lists)
    
    # Fit DC-SBM
    model = fit_multilayer_sbm(
        net,
        n_blocks=2,
        model="dc_sbm",
        n_init=1,
        max_iter=20,
        verbose=False,
        seed=seed
    )
    
    # Check degree parameters are positive
    assert model.degree_params_ is not None
    assert len(model.degree_params_) == n_nodes
    assert all(theta > 0 for theta in model.degree_params_)


@pytest.mark.property
@settings(max_examples=10, deadline=5000)
@given(
    n_nodes=integers(min_value=6, max_value=12),
    n_blocks=integers(min_value=2, max_value=3),
    seed=integers(min_value=0, max_value=50)
)
def test_elbo_monotonic_or_stable(n_nodes, n_blocks, seed):
    """Property: ELBO should generally increase or remain stable."""
    np.random.seed(seed)
    
    # Generate simple network
    edge_lists = [('L1', [(i, (i+1) % n_nodes) for i in range(n_nodes)])]
    net = generate_multilayer_network_from_edges(n_nodes, edge_lists)
    
    # Fit SBM
    model = fit_multilayer_sbm(
        net,
        n_blocks=n_blocks,
        model="sbm",
        n_init=1,
        max_iter=50,
        verbose=False,
        seed=seed
    )
    
    # Check ELBO doesn't decrease significantly
    elbo_history = model.elbo_history_
    if len(elbo_history) > 1:
        diffs = np.diff(elbo_history)
        # Allow small numerical decreases
        large_decreases = np.sum(diffs < -1e-3)
        # Most iterations should not have large decreases
        assert large_decreases < len(diffs) * 0.2


@pytest.mark.property
@settings(max_examples=8, deadline=5000)
@given(
    n_nodes=integers(min_value=8, max_value=12),
    n_layers=integers(min_value=2, max_value=3),
    seed=integers(min_value=0, max_value=50)
)
def test_layer_coupling_modes_consistency(n_nodes, n_layers, seed):
    """Property: Different layer coupling modes should produce valid outputs."""
    np.random.seed(seed)
    
    # Generate network
    edge_lists = []
    for layer_idx in range(n_layers):
        edges = [(i, (i+1) % n_nodes) for i in range(n_nodes)]
        edge_lists.append((f'L{layer_idx}', edges))
    
    net = generate_multilayer_network_from_edges(n_nodes, edge_lists)
    
    modes = ['independent', 'shared_blocks', 'shared_affinity']
    
    for mode in modes:
        model = fit_multilayer_sbm(
            net,
            n_blocks=2,
            layer_mode=mode,
            n_init=1,
            max_iter=20,
            verbose=False,
            seed=seed
        )
        
        # Check basic properties
        assert model.memberships_.shape[0] == n_nodes
        assert model.layer_mode_ == mode
        
        # Check block affinity structure
        if mode == 'shared_affinity':
            assert len(model.block_affinity_) == 1
        else:
            assert len(model.block_affinity_) == n_layers


@pytest.mark.property
@settings(max_examples=10, deadline=5000)
@given(
    n_nodes=integers(min_value=6, max_value=10),
    seed=integers(min_value=0, max_value=50)
)
def test_link_prediction_bounds(n_nodes, seed):
    """Property: Link prediction probabilities should be non-negative."""
    np.random.seed(seed)
    
    # Generate simple network
    edge_lists = [('L1', [(i, (i+1) % n_nodes) for i in range(n_nodes)])]
    net = generate_multilayer_network_from_edges(n_nodes, edge_lists)
    
    # Fit model
    model = fit_multilayer_sbm(
        net,
        n_blocks=2,
        n_init=1,
        max_iter=20,
        verbose=False,
        seed=seed
    )
    
    # Test link predictions
    for _ in range(5):
        u = np.random.randint(0, n_nodes)
        v = np.random.randint(0, n_nodes)
        if u != v:
            prob = model.predict_proba(u, v, 'L1')
            assert prob >= 0.0, f"Link prediction probability should be non-negative, got {prob}"


@pytest.mark.property
@settings(max_examples=10, deadline=5000)
@given(
    n_nodes=integers(min_value=6, max_value=10),
    n_blocks=integers(min_value=2, max_value=3),
    seed=integers(min_value=0, max_value=50)
)
def test_partition_vector_consistency(n_nodes, n_blocks, seed):
    """Property: Partition vector should match hard membership."""
    np.random.seed(seed)
    
    # Generate network
    edge_lists = [('L1', [(i, (i+1) % n_nodes) for i in range(n_nodes)])]
    net = generate_multilayer_network_from_edges(n_nodes, edge_lists)
    
    # Fit model
    model = fit_multilayer_sbm(
        net,
        n_blocks=n_blocks,
        n_init=1,
        max_iter=20,
        verbose=False,
        seed=seed
    )
    
    # Get partition
    partition = model.to_partition_vector()
    
    # Check consistency
    assert len(partition) == n_nodes
    for node_id in range(n_nodes):
        assert partition[node_id] == model.hard_membership_[node_id]


@pytest.mark.property
@settings(max_examples=8, deadline=5000)
@given(
    n_nodes=integers(min_value=6, max_value=10),
    seed=integers(min_value=0, max_value=50)
)
def test_uncertainty_metrics_valid(n_nodes, seed):
    """Property: Uncertainty metrics should be in valid ranges."""
    np.random.seed(seed)
    
    # Generate network
    edge_lists = [('L1', [(i, (i+1) % n_nodes) for i in range(n_nodes)])]
    net = generate_multilayer_network_from_edges(n_nodes, edge_lists)
    
    # Fit model
    model = fit_multilayer_sbm(
        net,
        n_blocks=2,
        n_init=1,
        max_iter=20,
        verbose=False,
        seed=seed
    )
    
    # Check uncertainty metrics
    assert 'entropy' in model.uncertainty_
    assert 'confidence' in model.uncertainty_
    
    # Entropy should be non-negative
    assert all(h >= 0 for h in model.uncertainty_['entropy'])
    
    # Confidence should be in [0, 1]
    assert all(0 <= c <= 1 for c in model.uncertainty_['confidence'])


@pytest.mark.property
@settings(max_examples=5, deadline=10000)
@given(
    n_nodes=integers(min_value=8, max_value=12),
    K_min=integers(min_value=2, max_value=3),
    seed=integers(min_value=0, max_value=50)
)
def test_model_selection_returns_valid_K(n_nodes, K_min, seed):
    """Property: Model selection should return one of the candidate K values."""
    assume(K_min < n_nodes // 2)  # Ensure K is reasonable
    
    np.random.seed(seed)
    
    # Generate network
    edge_lists = [('L1', [(i, (i+1) % n_nodes) for i in range(n_nodes)])]
    net = generate_multilayer_network_from_edges(n_nodes, edge_lists)
    
    # Model selection
    K_list = [K_min, K_min + 1]
    model, info = fit_multilayer_sbm(
        net,
        n_blocks=K_list,
        n_init=1,
        max_iter=20,
        verbose=False,
        seed=seed
    )
    
    # Check that selected K is in the list
    assert info['best_K'] in K_list
    assert model.K_ == info['best_K']


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "property"])
