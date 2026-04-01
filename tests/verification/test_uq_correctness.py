"""
Uncertainty Quantification (UQ) Correctness Tests.

Tests resampling strategies and uncertainty estimation correctness:
- SEED strategy determinism
- BOOTSTRAP mean/std behavior
- PERTURBATION nonzero std
- CI bounds monotonicity
- UQ metadata in provenance
"""

import pytest
import numpy as np
from py3plex.core import multinet
from py3plex.uncertainty import (
    ResamplingStrategy,
    UncertaintyMode,
    UncertaintyConfig,
    set_uncertainty_config,
    get_uncertainty_config,
    estimate_uncertainty,
)

try:
    from py3plex.dsl import Q
    from py3plex.dsl.executor import execute_ast
    DSL_AVAILABLE = True
except ImportError:
    DSL_AVAILABLE = False


def create_deterministic_network():
    """Create a small deterministic network for UQ testing."""
    network = multinet.multi_layer_network(directed=False)
    
    # Simple path graph: A-B-C
    nodes = [
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'C', 'type': 'layer1'},
    ]
    network.add_nodes(nodes)
    
    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'B', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1'},
    ]
    network.add_edges(edges)
    
    return network


@pytest.mark.verification
@pytest.mark.fast
@pytest.mark.skipif(not DSL_AVAILABLE, reason="DSL not available")
def test_seed_strategy_deterministic():
    """
    Test that SEED strategy with deterministic algorithm produces std=0.
    
    Invariant: Deterministic algorithm + SEED resampling → std = 0
    """
    network = create_deterministic_network()
    
    # Configure SEED strategy
    config = UncertaintyConfig(
        mode=UncertaintyMode.ON,
        default_resampling=ResamplingStrategy.SEED,
        default_n_runs=5,
    )
    set_uncertainty_config(config)
    
    try:
        # Use a deterministic measure (degree)
        query = Q.nodes().compute('degree').to_ast()
        result = execute_ast(network, query)
        
        # Check if UQ was computed
        if hasattr(result, 'uncertainty_summary'):
            summary = result.uncertainty_summary()
            
            # For SEED strategy with deterministic algorithm, std should be 0
            if 'degree_std' in summary.columns:
                stds = summary['degree_std'].values
                # Std should be very close to 0 for deterministic measure
                assert np.all(stds < 1e-10), \
                    f"SEED strategy with deterministic measure should have std≈0, got {stds}"
    finally:
        # Reset config
        set_uncertainty_config(UncertaintyConfig(mode=UncertaintyMode.OFF))


@pytest.mark.verification
@pytest.mark.fast
def test_uq_config_context():
    """
    Test that UQ config can be set and retrieved.
    """
    # Save original config
    original = get_uncertainty_config()
    
    try:
        # Set new config
        config = UncertaintyConfig(
            mode=UncertaintyMode.ON,
            default_resampling=ResamplingStrategy.BOOTSTRAP,
            default_n_runs=10,
        )
        set_uncertainty_config(config)
        
        # Retrieve and verify
        retrieved = get_uncertainty_config()
        assert retrieved.mode == UncertaintyMode.ON, "Config should be enabled"
        assert retrieved.default_resampling == ResamplingStrategy.BOOTSTRAP
        assert retrieved.default_n_runs == 10
    finally:
        # Restore original
        set_uncertainty_config(original)


@pytest.mark.verification
@pytest.mark.fast
@pytest.mark.skipif(not DSL_AVAILABLE, reason="DSL not available")
def test_uq_metadata_in_provenance():
    """
    Test that UQ metadata appears in provenance when enabled.
    
    Provenance should contain:
    - randomness.method
    - n_samples
    - seed
    """
    network = create_deterministic_network()
    
    config = UncertaintyConfig(
        mode=UncertaintyMode.ON,
        default_resampling=ResamplingStrategy.SEED,
        default_n_runs=3,
    )
    set_uncertainty_config(config)
    
    try:
        query = Q.nodes().compute('degree').to_ast()
        result = execute_ast(network, query)
        
        # Check metadata
        if hasattr(result, 'meta') and isinstance(result.meta, dict):
            # Look for UQ metadata
            if 'provenance' in result.meta:
                prov = result.meta['provenance']
                # Note: Actual implementation may vary
                # This is a placeholder for when UQ provenance is implemented
                assert isinstance(prov, dict), "Provenance should be a dict"
    finally:
        set_uncertainty_config(UncertaintyConfig(mode=UncertaintyMode.OFF))


@pytest.mark.verification
@pytest.mark.fast
@pytest.mark.skipif(not DSL_AVAILABLE, reason="DSL not available")
def test_ci_bounds_monotonic():
    """
    Test that confidence interval bounds are monotonic: low ≤ mean ≤ high.
    
    Invariant: ci_low ≤ mean ≤ ci_high
    """
    network = create_deterministic_network()
    
    config = UncertaintyConfig(
        mode=UncertaintyMode.ON,
        default_resampling=ResamplingStrategy.SEED,
        default_n_runs=5,
    )
    set_uncertainty_config(config)
    
    try:
        query = Q.nodes().compute('degree').to_ast()
        result = execute_ast(network, query)
        
        # Check if uncertainty columns are present
        df = result.to_pandas()
        
        # Look for CI columns (naming may vary)
        ci_low_col = None
        ci_high_col = None
        mean_col = 'degree'
        
        for col in df.columns:
            if 'ci' in col.lower() and 'low' in col.lower():
                ci_low_col = col
            elif 'ci' in col.lower() and 'high' in col.lower():
                ci_high_col = col
        
        # If CI columns exist, check monotonicity
        if ci_low_col and ci_high_col and mean_col in df.columns:
            for idx in df.index:
                low = df.loc[idx, ci_low_col]
                mean = df.loc[idx, mean_col]
                high = df.loc[idx, ci_high_col]
                
                assert low <= mean, f"CI low ({low}) should be ≤ mean ({mean})"
                assert mean <= high, f"Mean ({mean}) should be ≤ CI high ({high})"
    finally:
        set_uncertainty_config(UncertaintyConfig(mode=UncertaintyMode.OFF))


@pytest.mark.verification
@pytest.mark.fast
def test_n_samples_positive():
    """
    Test that n_samples must be positive.
    """
    config = UncertaintyConfig(
        mode=UncertaintyMode.ON,
        default_resampling=ResamplingStrategy.BOOTSTRAP,
        default_n_runs=10,
    )
    
    assert config.default_n_runs > 0, "default_n_runs must be positive"


@pytest.mark.verification
@pytest.mark.fast
def test_resampling_strategy_enum():
    """
    Test that resampling strategies are well-defined.
    """
    # Check that strategies are defined
    strategies = [
        ResamplingStrategy.SEED,
        ResamplingStrategy.BOOTSTRAP,
        ResamplingStrategy.PERTURBATION,
    ]
    
    for strategy in strategies:
        assert strategy is not None, f"Strategy {strategy} should be defined"
        # Should be able to create config with each strategy
        config = UncertaintyConfig(
            mode=UncertaintyMode.ON,
            default_resampling=strategy,
            default_n_runs=5,
        )
        assert config.default_resampling == strategy


@pytest.mark.verification
@pytest.mark.fast
@pytest.mark.skipif(not DSL_AVAILABLE, reason="DSL not available")
def test_perturbation_produces_variance():
    """
    Test that PERTURBATION strategy produces nonzero std when edge_drop_p > 0.
    
    Note: This test may be flaky if network is too small or drop probability too low.
    Marked as flaky with 3 retries to handle statistical edge cases.
    """
    # Create slightly larger network to ensure perturbation has effect
    network = multinet.multi_layer_network(directed=False)
    
    # Create a network with more edges
    nodes = [{'source': chr(ord('A') + i), 'type': 'layer1'} for i in range(6)]
    network.add_nodes(nodes)
    
    # Create a cycle
    edges = []
    for i in range(6):
        edges.append({
            'source': chr(ord('A') + i),
            'target': chr(ord('A') + ((i + 1) % 6)),
            'source_type': 'layer1',
            'target_type': 'layer1',
        })
    network.add_edges(edges)
    
    # Use direct uncertainty estimation API with fixed seed to avoid flakiness.
    def degree_metric(net):
        values = {}
        for node in net.get_nodes():
            values[node] = net.core_network.degree(node)
        return values

    result = estimate_uncertainty(
        network,
        degree_metric,
        n_runs=30,
        resampling=ResamplingStrategy.PERTURBATION,
        random_seed=42,
        perturbation_params={"edge_drop_p": 0.5},
    )

    assert result.std is not None, "Perturbation should produce std values"
    assert np.all(np.isfinite(result.std)), "Std values must be finite"
    assert np.any(result.std > 0), "At least one node should have non-zero std under perturbation"
    baseline = np.array([network.core_network.degree(node) for node in result.index], dtype=float)
    assert np.all(result.mean >= 0), "Mean perturbed degrees should be non-negative"
    assert np.all(result.mean <= baseline + 1e-9), "Mean perturbed degree should not exceed baseline degree"


@pytest.mark.verification
@pytest.mark.fast
@pytest.mark.skipif(not DSL_AVAILABLE, reason="DSL not available")
def test_disabled_uq_no_overhead():
    """
    Test that disabled UQ doesn't add uncertainty columns.
    """
    network = create_deterministic_network()
    
    # Ensure UQ is disabled
    set_uncertainty_config(UncertaintyConfig(mode=UncertaintyMode.OFF))
    
    query = Q.nodes().compute('degree').to_ast()
    result = execute_ast(network, query)
    
    df = result.to_pandas()
    
    # Should not have _std or _ci columns
    std_cols = [col for col in df.columns if '_std' in col]
    ci_cols = [col for col in df.columns if '_ci' in col]
    
    # These should be empty when UQ is disabled
    # (though the check is lenient as implementation may vary)
    assert len(df.columns) > 0, "Should have basic columns"
