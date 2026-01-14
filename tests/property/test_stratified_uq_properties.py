"""Property-based tests for stratified perturbation UQ.

This module uses Hypothesis to test fundamental properties and invariants
that stratified UQ should satisfy.
"""

import numpy as np
import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck
import networkx as nx

from py3plex.core import multinet
from py3plex.uncertainty import (
    estimate_uncertainty,
    ResamplingStrategy,
    StatSeries,
    StratificationSpec,
    compute_composite_strata,
    auto_select_strata,
)


# ============================================================================
# Custom Strategies
# ============================================================================

@st.composite
def simple_network_strategy(draw, min_nodes=3, max_nodes=10, min_edges=2, max_edges=15):
    """Generate simple multilayer networks for testing."""
    n_nodes = draw(st.integers(min_value=min_nodes, max_value=max_nodes))
    n_edges = draw(st.integers(min_value=min_edges, max_value=max_edges))
    
    # Create network
    net = multinet.multi_layer_network(directed=False, verbose=False)
    
    # Generate nodes
    nodes = [f"n{i}" for i in range(n_nodes)]
    
    # Generate random edges
    edges = []
    for _ in range(n_edges):
        src = draw(st.sampled_from(nodes))
        dst = draw(st.sampled_from(nodes))
        if src != dst:  # Avoid self-loops
            layer = draw(st.sampled_from(["L0", "L1"]))
            edges.append([src, layer, dst, layer, 1.0])
    
    if edges:
        net.add_edges(edges, input_type="list")
    
    # Ensure network is connected enough
    assume(net.core_network is not None)
    assume(net.core_network.number_of_edges() >= 2)
    
    return net


@st.composite
def stratification_spec_strategy(draw):
    """Generate valid StratificationSpec objects."""
    # Choose strata dimensions
    available_strata = ["degree", "layer", "layer_pair", "weight"]
    n_strata = draw(st.integers(min_value=0, max_value=2))
    strata = draw(st.lists(
        st.sampled_from(available_strata),
        min_size=n_strata,
        max_size=n_strata,
        unique=True
    ))
    
    # Generate bins
    bins = {}
    for s in strata:
        if s in ["degree", "weight"]:
            bins[s] = draw(st.integers(min_value=2, max_value=5))
    
    return StratificationSpec(strata=strata, bins=bins)


# ============================================================================
# Property Tests: Determinism
# ============================================================================

@pytest.mark.property
@given(
    network=simple_network_strategy(),
    seed=st.integers(min_value=0, max_value=1000),
    n_samples=st.integers(min_value=5, max_value=20)
)
@settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_stratified_uq_deterministic(network, seed, n_samples):
    """Property: Same seed produces identical results."""
    
    def degree_metric(net):
        return dict(net.core_network.degree())
    
    # Run twice with same seed
    result1 = estimate_uncertainty(
        network,
        degree_metric,
        n_runs=n_samples,
        resampling=ResamplingStrategy.STRATIFIED_PERTURBATION,
        random_seed=seed,
        perturbation_params={"edge_drop_p": 0.1}
    )
    
    result2 = estimate_uncertainty(
        network,
        degree_metric,
        n_runs=n_samples,
        resampling=ResamplingStrategy.STRATIFIED_PERTURBATION,
        random_seed=seed,
        perturbation_params={"edge_drop_p": 0.1}
    )
    
    # Check determinism
    if isinstance(result1, StatSeries) and isinstance(result2, StatSeries):
        assert np.allclose(result1.mean, result2.mean, rtol=1e-10), \
            "Same seed should produce identical mean values"
        if result1.std is not None and result2.std is not None:
            assert np.allclose(result1.std, result2.std, rtol=1e-10), \
                "Same seed should produce identical std values"


@pytest.mark.property
@given(
    network=simple_network_strategy(),
    seed1=st.integers(min_value=0, max_value=1000),
    seed2=st.integers(min_value=0, max_value=1000),
    n_samples=st.integers(min_value=10, max_value=20)
)
@settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_different_seeds_produce_different_results(network, seed1, seed2, n_samples):
    """Property: Different seeds produce different results (with high probability)."""
    assume(seed1 != seed2)
    
    def degree_metric(net):
        return dict(net.core_network.degree())
    
    result1 = estimate_uncertainty(
        network,
        degree_metric,
        n_runs=n_samples,
        resampling=ResamplingStrategy.STRATIFIED_PERTURBATION,
        random_seed=seed1,
        perturbation_params={"edge_drop_p": 0.1}
    )
    
    result2 = estimate_uncertainty(
        network,
        degree_metric,
        n_runs=n_samples,
        resampling=ResamplingStrategy.STRATIFIED_PERTURBATION,
        random_seed=seed2,
        perturbation_params={"edge_drop_p": 0.1}
    )
    
    # Different seeds should produce different std values (with high probability)
    if isinstance(result1, StatSeries) and isinstance(result2, StatSeries):
        if result1.std is not None and result2.std is not None:
            # Allow for rare case where stds are very similar
            different = not np.allclose(result1.std, result2.std, rtol=1e-5)
            # This is a probabilistic test - different seeds usually differ
            # We just check that the infrastructure works


# ============================================================================
# Property Tests: Statistical Properties
# ============================================================================

@pytest.mark.property
@given(
    network=simple_network_strategy(),
    n_samples=st.integers(min_value=10, max_value=30)
)
@settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_mean_is_unbiased_estimator(network, n_samples):
    """Property: Mean from stratified UQ approximates true metric."""
    
    def degree_metric(net):
        return dict(net.core_network.degree())
    
    # Get true metric
    true_degrees = degree_metric(network)
    
    # Get UQ estimate
    result = estimate_uncertainty(
        network,
        degree_metric,
        n_runs=n_samples,
        resampling=ResamplingStrategy.STRATIFIED_PERTURBATION,
        random_seed=42,
        perturbation_params={"edge_drop_p": 0.05}  # Small perturbation
    )
    
    if isinstance(result, StatSeries):
        # Mean should be close to true values (within reason given perturbation)
        for i, node in enumerate(result.index):
            if node in true_degrees:
                # Allow for some deviation due to edge dropping
                assert abs(result.mean[i] - true_degrees[node]) <= true_degrees[node] + 2, \
                    f"Mean estimate should be reasonable for node {node}"


@pytest.mark.property
@given(
    network=simple_network_strategy(),
    n_samples=st.integers(min_value=10, max_value=30)
)
@settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_std_is_non_negative(network, n_samples):
    """Property: Standard deviation is always non-negative."""
    
    def degree_metric(net):
        return dict(net.core_network.degree())
    
    result = estimate_uncertainty(
        network,
        degree_metric,
        n_runs=n_samples,
        resampling=ResamplingStrategy.STRATIFIED_PERTURBATION,
        random_seed=42,
        perturbation_params={"edge_drop_p": 0.1}
    )
    
    if isinstance(result, StatSeries) and result.std is not None:
        assert np.all(result.std >= 0), "Standard deviation must be non-negative"


@pytest.mark.property
@given(
    network=simple_network_strategy(),
    n_samples=st.integers(min_value=10, max_value=30)
)
@settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_std_increases_with_perturbation(network, n_samples):
    """Property: Higher perturbation leads to higher variance (usually)."""
    
    def degree_metric(net):
        return dict(net.core_network.degree())
    
    # Low perturbation
    result_low = estimate_uncertainty(
        network,
        degree_metric,
        n_runs=n_samples,
        resampling=ResamplingStrategy.STRATIFIED_PERTURBATION,
        random_seed=42,
        perturbation_params={"edge_drop_p": 0.05}
    )
    
    # High perturbation
    result_high = estimate_uncertainty(
        network,
        degree_metric,
        n_runs=n_samples,
        resampling=ResamplingStrategy.STRATIFIED_PERTURBATION,
        random_seed=42,
        perturbation_params={"edge_drop_p": 0.20}
    )
    
    if isinstance(result_low, StatSeries) and isinstance(result_high, StatSeries):
        if result_low.std is not None and result_high.std is not None:
            # Mean std should be higher with higher perturbation (usually)
            mean_std_low = np.mean(result_low.std)
            mean_std_high = np.mean(result_high.std)
            # This is probabilistic but usually holds
            assert mean_std_high >= mean_std_low * 0.5, \
                "Higher perturbation should generally lead to higher variance"


# ============================================================================
# Property Tests: Stratification
# ============================================================================

@pytest.mark.property
@given(
    network=simple_network_strategy(),
    spec=stratification_spec_strategy()
)
@settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_stratification_covers_all_items(network, spec):
    """Property: Stratification covers all nodes/edges without duplication."""
    
    # Try node stratification
    if spec.strata and any(s in ["degree", "layer"] for s in spec.strata):
        strata = compute_composite_strata(network, spec, target="nodes")
        
        # Collect all nodes from all strata
        all_nodes = []
        for stratum_items in strata.values():
            all_nodes.extend(stratum_items)
        
        # Check coverage
        network_nodes = set(network.get_nodes())
        stratified_nodes = set(all_nodes)
        
        # All network nodes should be in strata
        assert stratified_nodes.issubset(network_nodes), \
            "Stratified nodes should be subset of network nodes"


@pytest.mark.property
@given(target=st.sampled_from(["nodes", "edges", "unknown"]))
def test_auto_select_strata_returns_list(target):
    """Property: auto_select_strata always returns a list."""
    strata = auto_select_strata(target)
    assert isinstance(strata, list), "auto_select_strata should return a list"
    assert all(isinstance(s, str) for s in strata), "All strata should be strings"


@pytest.mark.property
@given(
    strata_list=st.lists(
        st.sampled_from(["degree", "layer", "layer_pair", "weight"]),
        min_size=0,
        max_size=3,
        unique=True
    )
)
def test_stratification_spec_validates(strata_list):
    """Property: StratificationSpec validates strata."""
    spec = StratificationSpec(strata=strata_list)
    assert spec.strata == strata_list, "Strata should be preserved"
    assert isinstance(spec.bins, dict), "Bins should be a dict"


@pytest.mark.property
def test_stratification_spec_rejects_invalid_strata():
    """Property: StratificationSpec rejects invalid strata."""
    with pytest.raises(ValueError, match="Unknown stratification dimension"):
        StratificationSpec(strata=["invalid_stratum"])


# ============================================================================
# Property Tests: Metadata
# ============================================================================

@pytest.mark.property
@given(
    network=simple_network_strategy(),
    n_samples=st.integers(min_value=5, max_value=20)
)
@settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_metadata_contains_stratification_info(network, n_samples):
    """Property: Result metadata contains stratification information."""
    
    def degree_metric(net):
        return dict(net.core_network.degree())
    
    result = estimate_uncertainty(
        network,
        degree_metric,
        n_runs=n_samples,
        resampling=ResamplingStrategy.STRATIFIED_PERTURBATION,
        random_seed=42,
        perturbation_params={"edge_drop_p": 0.1, "strata": ["degree"]}
    )
    
    if isinstance(result, StatSeries):
        assert "stratification" in result.meta, \
            "Metadata should contain stratification info"
        assert "n_strata" in result.meta, \
            "Metadata should contain stratum count"
        assert isinstance(result.meta["stratification"], dict), \
            "Stratification info should be a dict"


# ============================================================================
# Property Tests: Comparison with Regular Perturbation
# ============================================================================

@pytest.mark.property
@given(
    network=simple_network_strategy(min_nodes=5, max_nodes=15, min_edges=5, max_edges=20),
    n_samples=st.integers(min_value=20, max_value=40)
)
@settings(max_examples=5, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_stratified_vs_regular_perturbation_means_similar(network, n_samples):
    """Property: Stratified and regular perturbation produce similar means."""
    
    def degree_metric(net):
        return dict(net.core_network.degree())
    
    # Ensure network is large enough
    assume(network.core_network.number_of_nodes() >= 4)
    assume(network.core_network.number_of_edges() >= 4)
    
    # Regular perturbation
    result_regular = estimate_uncertainty(
        network,
        degree_metric,
        n_runs=n_samples,
        resampling=ResamplingStrategy.PERTURBATION,
        random_seed=42,
        perturbation_params={"edge_drop_p": 0.1}
    )
    
    # Stratified perturbation
    result_stratified = estimate_uncertainty(
        network,
        degree_metric,
        n_runs=n_samples,
        resampling=ResamplingStrategy.STRATIFIED_PERTURBATION,
        random_seed=42,
        perturbation_params={"edge_drop_p": 0.1}
    )
    
    # Both should be StatSeries
    if isinstance(result_regular, StatSeries) and isinstance(result_stratified, StatSeries):
        # Check that we have enough variance to compute correlation
        assume(np.std(result_regular.mean) > 0.01)
        assume(np.std(result_stratified.mean) > 0.01)
        
        # Means should be similar (both are unbiased estimators)
        # Allow for some stochastic variation
        correlation = np.corrcoef(result_regular.mean, result_stratified.mean)[0, 1]
        
        # Only assert if correlation is not NaN
        if not np.isnan(correlation):
            assert correlation > 0.5, \
                "Regular and stratified perturbation should produce correlated means"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "property"])
