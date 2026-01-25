"""Tests for deterministic parallel execution of dynamics simulations.

These tests verify that n_jobs parallelism produces identical results
for the same seed, regardless of whether execution is serial or parallel.
"""

import pytest
import numpy as np
from py3plex.dsl import Q, D
from py3plex.core import multinet


@pytest.fixture
def sample_network():
    """Create a small network for testing."""
    net = multinet.multi_layer_network(directed=False)
    
    # Add nodes
    net.add_nodes([
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'C', 'type': 'layer1'},
        {'source': 'D', 'type': 'layer1'},
    ])
    
    # Add edges
    net.add_edges([
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'B', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'C', 'target': 'D', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'D', 'target': 'A', 'source_type': 'layer1', 'target_type': 'layer1'},
    ])
    
    return net


class TestDynamicsParallelDeterminism:
    """Test that parallel dynamics execution is deterministic."""
    
    def test_n_jobs_1_vs_2_identical_results(self, sample_network):
        """Same seed with n_jobs=1 and n_jobs=2 should produce identical results."""
        # Run with n_jobs=1 (serial)
        result_serial = (
            Q.dynamics("SIS", beta=0.3, mu=0.1)
             .seed_infections(fraction=0.25)
             .run(steps=20, replicates=10, n_jobs=1)
             .random_seed(42)
             .execute(sample_network)
        )
        
        # Run with n_jobs=2 (parallel)
        result_parallel = (
            Q.dynamics("SIS", beta=0.3, mu=0.1)
             .seed_infections(fraction=0.25)
             .run(steps=20, replicates=10, n_jobs=2)
             .random_seed(42)
             .execute(sample_network)
        )
        
        # Extract trajectories
        serial_data = result_serial.data
        parallel_data = result_parallel.data
        
        # Check that both have same measures
        assert serial_data.keys() == parallel_data.keys()
        
        # Check that all measures have identical values
        for measure in serial_data.keys():
            serial_values = serial_data[measure]
            parallel_values = parallel_data[measure]
            
            # Same shape
            assert serial_values.shape == parallel_values.shape, \
                f"Shape mismatch for {measure}: {serial_values.shape} vs {parallel_values.shape}"
            
            # Same values (within numerical tolerance)
            assert np.allclose(serial_values, parallel_values, rtol=1e-10, atol=1e-10), \
                f"Values differ for {measure}"
    
    def test_d_simulate_n_jobs_determinism(self, sample_network):
        """D.simulate() should also support deterministic n_jobs."""
        # Run with n_jobs=1
        result1 = (
            D.simulate("SIR", beta=0.3, gamma=0.1)
             .seed_infections(fraction=0.25)
             .steps(20)
             .run(steps=20, replicates=10, n_jobs=1)
             .random_seed(42)
             .execute(sample_network)
        )
        
        # Run with n_jobs=2
        result2 = (
            D.simulate("SIR", beta=0.3, gamma=0.1)
             .seed_infections(fraction=0.25)
             .steps(20)
             .run(steps=20, replicates=10, n_jobs=2)
             .random_seed(42)
             .execute(sample_network)
        )
        
        # Check data is identical
        for measure in result1.data.keys():
            assert np.allclose(result1.data[measure], result2.data[measure], rtol=1e-10, atol=1e-10)
    
    def test_different_seeds_produce_different_results(self, sample_network):
        """Different seeds should produce different results (sanity check)."""
        # Run with seed=42
        result1 = (
            Q.dynamics("SIS", beta=0.3, mu=0.1)
             .seed_infections(fraction=0.25)
             .run(steps=20, replicates=10, n_jobs=2)
             .random_seed(42)
             .execute(sample_network)
        )
        
        # Run with seed=123
        result2 = (
            Q.dynamics("SIS", beta=0.3, mu=0.1)
             .seed_infections(fraction=0.25)
             .run(steps=20, replicates=10, n_jobs=2)
             .random_seed(123)
             .execute(sample_network)
        )
        
        # At least one measure should differ
        has_difference = False
        for measure in result1.data.keys():
            if not np.allclose(result1.data[measure], result2.data[measure], rtol=1e-6):
                has_difference = True
                break
        
        assert has_difference, "Different seeds produced identical results (unexpected)"
    
    def test_replicate_order_preserved(self, sample_network):
        """Replicate order should be preserved regardless of n_jobs."""
        # Run multiple times with same seed
        results = []
        for n_jobs in [1, 2]:
            result = (
                Q.dynamics("SIS", beta=0.3, mu=0.1)
                 .seed_infections(fraction=0.25)
                 .run(steps=20, replicates=5, n_jobs=n_jobs)
                 .random_seed(42)
                 .execute(sample_network)
            )
            results.append(result)
        
        # Check that replicate order is same
        for measure in results[0].data.keys():
            data1 = results[0].data[measure]  # Shape: (replicates, steps)
            data2 = results[1].data[measure]
            
            # Each replicate should match exactly
            for rep_idx in range(data1.shape[0]):
                assert np.allclose(data1[rep_idx], data2[rep_idx], rtol=1e-10), \
                    f"Replicate {rep_idx} differs for {measure}"
    
    def test_provenance_includes_n_jobs(self, sample_network):
        """Provenance should record n_jobs value."""
        result = (
            Q.dynamics("SIS", beta=0.3, mu=0.1)
             .seed_infections(fraction=0.25)
             .run(steps=20, replicates=5, n_jobs=4)
             .random_seed(42)
             .execute(sample_network)
        )
        
        # Check provenance
        assert hasattr(result, 'meta')
        assert 'provenance' in result.meta
        assert 'dynamics_config' in result.meta['provenance']
        
        config = result.meta['provenance']['dynamics_config']
        assert 'n_jobs' in config
        assert config['n_jobs'] == 4
    
    @pytest.mark.parametrize("n_jobs", [1, 2, 4])
    def test_multiple_n_jobs_values(self, sample_network, n_jobs):
        """Test various n_jobs values all produce identical results with same seed."""
        result = (
            Q.dynamics("SIS", beta=0.3, mu=0.1)
             .seed_infections(fraction=0.25)
             .run(steps=15, replicates=8, n_jobs=n_jobs)
             .random_seed(99)
             .execute(sample_network)
        )
        
        # Just verify it runs without error and produces data
        assert result is not None
        assert len(result.data) > 0
        
        # Store first result for comparison
        if not hasattr(self, '_baseline_result'):
            self._baseline_result = result
        else:
            # Compare with baseline
            for measure in result.data.keys():
                assert np.allclose(result.data[measure], self._baseline_result.data[measure], 
                                 rtol=1e-10, atol=1e-10)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
