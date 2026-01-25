"""
Test dynamics UQ integration.

Tests that .uq() wraps summary stats with confidence intervals.
"""

import pytest
import numpy as np
from py3plex.core import multinet
from py3plex.dsl import Q, D


@pytest.fixture
def simple_network():
    """Create a simple network for testing."""
    net = multinet.multi_layer_network(directed=False)
    net.add_nodes([
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'C', 'type': 'layer1'},
        {'source': 'D', 'type': 'layer1'},
        {'source': 'E', 'type': 'layer1'},
    ])
    net.add_edges([
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'B', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'C', 'target': 'D', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'D', 'target': 'E', 'source_type': 'layer1', 'target_type': 'layer1'},
    ])
    return net


class TestDynamicsUQIntegration:
    """Test UQ integration with dynamics."""

    def test_uq_basic(self, simple_network):
        """Test basic UQ functionality."""
        result = (
            Q.dynamics("SIS", beta=0.3, mu=0.1)
            .seed_infections(fraction=0.2)
            .run(steps=50, replicates=10)
            .uq(ci_level=0.95, method="dynamics_mc")
            .execute(simple_network)
        )
        
        # Verify UQ config in provenance
        assert 'uq_config' in result.meta['provenance']['dynamics_config']
        uq_config = result.meta['provenance']['dynamics_config']['uq_config']
        assert uq_config['ci_level'] == 0.95
        assert uq_config['method'] == "dynamics_mc"

    def test_uq_wraps_summary_stats(self, simple_network):
        """Test that UQ wraps summary stats with CI bounds."""
        result = (
            Q.dynamics("SIS", beta=0.3, mu=0.1)
            .seed_infections(fraction=0.2)
            .run(steps=50, replicates=20)
            .uq(ci_level=0.95, method="dynamics_mc")
            .execute(simple_network)
        )
        
        # Check mean_peak_time has UQ structure
        peak_time = result.mean_peak_time
        assert isinstance(peak_time, dict)
        assert 'mean' in peak_time
        assert 'ci_low' in peak_time
        assert 'ci_high' in peak_time
        
        # Verify CI bounds make sense
        assert peak_time['ci_low'] <= peak_time['mean']
        assert peak_time['mean'] <= peak_time['ci_high']
        assert peak_time['ci_low'] < peak_time['ci_high']

    def test_uq_different_ci_levels(self, simple_network):
        """Test different CI levels."""
        result_90 = (
            Q.dynamics("SIS", beta=0.3, mu=0.1)
            .seed_infections(fraction=0.2)
            .run(steps=50, replicates=20)
            .uq(ci_level=0.90)
            .execute(simple_network)
        )
        
        result_99 = (
            Q.dynamics("SIS", beta=0.3, mu=0.1)
            .seed_infections(fraction=0.2)
            .run(steps=50, replicates=20)
            .uq(ci_level=0.99)
            .execute(simple_network)
        )
        
        # 99% CI should be wider than 90% CI
        width_90 = result_90.mean_peak_time['ci_high'] - result_90.mean_peak_time['ci_low']
        width_99 = result_99.mean_peak_time['ci_high'] - result_99.mean_peak_time['ci_low']
        assert width_99 >= width_90

    def test_uq_with_d_simulate(self, simple_network):
        """Test UQ works with D.simulate() factory."""
        result = (
            D.simulate("SIS", beta=0.3, mu=0.1)
            .seed_infections(fraction=0.2)
            .run(steps=50, replicates=15)
            .uq(ci_level=0.95)
            .execute(simple_network)
        )
        
        # Should have UQ-wrapped stats
        assert isinstance(result.mean_peak_time, dict)
        assert 'mean' in result.mean_peak_time
        assert 'ci_low' in result.mean_peak_time
        assert 'ci_high' in result.mean_peak_time

    def test_uq_determinism(self, simple_network):
        """Test that UQ is deterministic with same seed."""
        result1 = (
            Q.dynamics("SIS", beta=0.3, mu=0.1)
            .seed_infections(fraction=0.2)
            .run(steps=50, replicates=10)
            .random_seed(42)
            .uq(ci_level=0.95)
            .execute(simple_network)
        )
        
        result2 = (
            Q.dynamics("SIS", beta=0.3, mu=0.1)
            .seed_infections(fraction=0.2)
            .run(steps=50, replicates=10)
            .random_seed(42)
            .uq(ci_level=0.95)
            .execute(simple_network)
        )
        
        # Should produce identical CI bounds
        assert result1.mean_peak_time['mean'] == result2.mean_peak_time['mean']
        assert result1.mean_peak_time['ci_low'] == result2.mean_peak_time['ci_low']
        assert result1.mean_peak_time['ci_high'] == result2.mean_peak_time['ci_high']

    def test_uq_without_sufficient_replicates(self, simple_network):
        """Test UQ with few replicates (edge case)."""
        # Should still work but may have wide CIs
        result = (
            Q.dynamics("SIS", beta=0.3, mu=0.1)
            .seed_infections(fraction=0.2)
            .run(steps=50, replicates=3)
            .uq(ci_level=0.95)
            .execute(simple_network)
        )
        
        # Should still have UQ structure
        assert isinstance(result.mean_peak_time, dict)
        assert 'mean' in result.mean_peak_time

    def test_uq_mean_final_infected(self, simple_network):
        """Test UQ wraps mean_final_infected correctly."""
        result = (
            Q.dynamics("SIS", beta=0.3, mu=0.1)
            .seed_infections(fraction=0.2)
            .run(steps=50, replicates=20)
            .uq(ci_level=0.95)
            .execute(simple_network)
        )
        
        final_infected = result.mean_final_infected
        assert isinstance(final_infected, dict)
        assert 'mean' in final_infected
        assert 'ci_low' in final_infected
        assert 'ci_high' in final_infected
        
        # Verify bounds are valid (between 0 and 1 since it's a fraction)
        assert 0 <= final_infected['ci_low'] <= 1
        assert 0 <= final_infected['mean'] <= 1
        assert 0 <= final_infected['ci_high'] <= 1

    def test_uq_sir_model(self, simple_network):
        """Test UQ with SIR model."""
        result = (
            Q.dynamics("SIR", beta=0.3, gamma=0.1)
            .seed_infections(fraction=0.2)
            .run(steps=50, replicates=15)
            .uq(ci_level=0.95)
            .execute(simple_network)
        )
        
        # Should have UQ-wrapped stats for SIR
        assert isinstance(result.mean_peak_time, dict)
        assert 'mean' in result.mean_peak_time

    def test_uq_with_n_jobs(self, simple_network):
        """Test UQ works correctly with parallel execution."""
        result = (
            Q.dynamics("SIS", beta=0.3, mu=0.1)
            .seed_infections(fraction=0.2)
            .run(steps=50, replicates=20, n_jobs=2)
            .random_seed(42)
            .uq(ci_level=0.95)
            .execute(simple_network)
        )
        
        # Should still have valid UQ structure
        peak_time = result.mean_peak_time
        assert isinstance(peak_time, dict)
        assert 'mean' in peak_time
        assert 'ci_low' in peak_time
        assert 'ci_high' in peak_time
        
        # CI bounds should be sensible
        assert peak_time['ci_low'] <= peak_time['mean'] <= peak_time['ci_high']

    def test_no_uq_by_default(self, simple_network):
        """Test that without .uq(), summary stats are scalars."""
        result = (
            Q.dynamics("SIS", beta=0.3, mu=0.1)
            .seed_infections(fraction=0.2)
            .run(steps=50, replicates=10)
            .execute(simple_network)
        )
        
        # Without UQ, should be scalar
        assert isinstance(result.mean_peak_time, (int, float))
        assert not isinstance(result.mean_peak_time, dict)

    def test_uq_ci_calculation_correctness(self, simple_network):
        """Test CI calculation is mathematically correct."""
        result = (
            Q.dynamics("SIS", beta=0.3, mu=0.1)
            .seed_infections(fraction=0.2)
            .run(steps=50, replicates=100)
            .random_seed(42)
            .uq(ci_level=0.95)
            .execute(simple_network)
        )
        
        # Get raw per-replicate peak times from trajectories
        peak_times = []
        for rep in range(100):
            rep_data = result.trajectories[result.trajectories['replicate'] == rep]
            if len(rep_data) > 0:
                # Peak is when infected count is highest
                peak_idx = rep_data['infected'].idxmax()
                peak_time = rep_data.loc[peak_idx, 'step']
                peak_times.append(peak_time)
        
        if len(peak_times) > 0:
            # Manually compute percentiles
            expected_mean = np.mean(peak_times)
            expected_ci_low = np.percentile(peak_times, 2.5)
            expected_ci_high = np.percentile(peak_times, 97.5)
            
            # Should match (with small tolerance)
            assert abs(result.mean_peak_time['mean'] - expected_mean) < 0.1
            assert abs(result.mean_peak_time['ci_low'] - expected_ci_low) < 0.1
            assert abs(result.mean_peak_time['ci_high'] - expected_ci_high) < 0.1
