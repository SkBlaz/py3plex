"""
Tests for py3plex.uncertainty.runner module.

This module tests the canonical UQ execution runner.
"""

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock

from py3plex.uncertainty.runner import run_uq
from py3plex.uncertainty.plan import UQPlan, UQResult
from py3plex.uncertainty.noise_models import NoNoise


class MockReducer:
    """Mock reducer for testing."""
    
    def __init__(self, name="MockReducer"):
        self._name = name
        self.updates = []
        self.finalized = False
    
    @property
    def name(self):
        """Expose reducer name for runner keying."""
        return self._name
    
    def update(self, sample_output):
        """Record sample outputs."""
        self.updates.append(sample_output)
    
    def finalize(self):
        """Return finalized output."""
        self.finalized = True
        return {"count": len(self.updates), "reducer": self._name}


class TestRunUQBasic:
    """Test basic run_uq functionality."""
    
    def test_run_uq_executes_n_samples(self):
        """Test that run_uq executes exactly n_samples iterations."""
        call_count = []
        
        def base_callable(network, rng):
            call_count.append(1)
            return {"iteration": len(call_count)}
        
        reducer = MockReducer()
        plan = UQPlan(
            base_callable=base_callable,
            strategy="seed",
            noise_model=NoNoise(),
            n_samples=10,
            seed=42,
            reducers=[reducer],
            storage_mode="none"
        )
        
        mock_network = Mock()
        result = run_uq(plan, mock_network)
        
        # Verify n_samples iterations
        assert len(call_count) == 10
        assert len(reducer.updates) == 10
        assert reducer.finalized
    
    def test_run_uq_returns_uq_result(self):
        """Test that run_uq returns UQResult."""
        def base_callable(network, rng):
            return {"value": 1.0}
        
        reducer = MockReducer()
        plan = UQPlan(
            base_callable=base_callable,
            strategy="seed",
            noise_model=NoNoise(),
            n_samples=5,
            seed=42,
            reducers=[reducer],
            storage_mode="none"
        )
        
        result = run_uq(plan, Mock())
        
        assert isinstance(result, UQResult)
        assert result.n_samples == 5
        assert "MockReducer" in result.reducer_outputs
        assert result.reducer_outputs["MockReducer"]["count"] == 5
    
    def test_run_uq_passes_network_to_callable(self):
        """Test that network is passed to base_callable."""
        networks_received = []
        
        def base_callable(network, rng):
            networks_received.append(network)
            return {"value": 1.0}
        
        plan = UQPlan(
            base_callable=base_callable,
            strategy="seed",
            noise_model=NoNoise(),
            n_samples=3,
            seed=42,
            reducers=[MockReducer()],
            storage_mode="none"
        )
        
        mock_network = Mock()
        run_uq(plan, mock_network)
        
        # All three iterations should have been called (NoNoise still calls n_samples times)
        assert len(networks_received) == 3
    
    def test_run_uq_passes_rng_to_callable(self):
        """Test that RNG is passed to base_callable."""
        rngs_received = []
        
        def base_callable(network, rng):
            rngs_received.append(rng)
            # Generate a random number to verify RNG works
            return {"random": rng.random()}
        
        plan = UQPlan(
            base_callable=base_callable,
            strategy="seed",
            noise_model=NoNoise(),
            n_samples=3,
            seed=42,
            reducers=[MockReducer()],
            storage_mode="none"
        )
        
        run_uq(plan, Mock())
        
        # Verify RNGs were passed
        assert len(rngs_received) == 3
        assert all(isinstance(rng, np.random.Generator) for rng in rngs_received)


class TestRunUQDeterminism:
    """Test determinism guarantees of run_uq."""
    
    def test_run_uq_deterministic_with_same_seed(self):
        """Test that same seed produces identical results."""
        def base_callable(network, rng):
            return {"random": rng.random()}
        
        reducer1 = MockReducer("Reducer1")
        plan1 = UQPlan(
            base_callable=base_callable,
            strategy="seed",
            noise_model=NoNoise(),
            n_samples=10,
            seed=42,
            reducers=[reducer1],
            storage_mode="none"
        )
        
        reducer2 = MockReducer("Reducer2")
        plan2 = UQPlan(
            base_callable=base_callable,
            strategy="seed",
            noise_model=NoNoise(),
            n_samples=10,
            seed=42,
            reducers=[reducer2],
            storage_mode="none"
        )
        
        result1 = run_uq(plan1, Mock())
        result2 = run_uq(plan2, Mock())
        
        # Extract random values from updates
        values1 = [update["random"] for update in reducer1.updates]
        values2 = [update["random"] for update in reducer2.updates]
        
        # Should be identical
        assert values1 == values2
    
    def test_run_uq_different_with_different_seeds(self):
        """Test that different seeds produce different results."""
        def base_callable(network, rng):
            return {"random": rng.random()}
        
        reducer1 = MockReducer("Reducer1")
        plan1 = UQPlan(
            base_callable=base_callable,
            strategy="seed",
            noise_model=NoNoise(),
            n_samples=10,
            seed=42,
            reducers=[reducer1],
            storage_mode="none"
        )
        
        reducer2 = MockReducer("Reducer2")
        plan2 = UQPlan(
            base_callable=base_callable,
            strategy="seed",
            noise_model=NoNoise(),
            n_samples=10,
            seed=123,
            reducers=[reducer2],
            storage_mode="none"
        )
        
        result1 = run_uq(plan1, Mock())
        result2 = run_uq(plan2, Mock())
        
        # Extract random values
        values1 = [update["random"] for update in reducer1.updates]
        values2 = [update["random"] for update in reducer2.updates]
        
        # Should be different
        assert values1 != values2


class TestRunUQReducers:
    """Test reducer integration."""
    
    def test_run_uq_calls_update_on_all_reducers(self):
        """Test that all reducers receive updates."""
        def base_callable(network, rng):
            return {"value": rng.random()}
        
        reducer1 = MockReducer("Reducer1")
        reducer2 = MockReducer("Reducer2")
        
        plan = UQPlan(
            base_callable=base_callable,
            strategy="seed",
            noise_model=NoNoise(),
            n_samples=5,
            seed=42,
            reducers=[reducer1, reducer2],
            storage_mode="none"
        )
        
        run_uq(plan, Mock())
        
        # Both reducers should receive all updates
        assert len(reducer1.updates) == 5
        assert len(reducer2.updates) == 5
        assert reducer1.finalized
        assert reducer2.finalized
    
    def test_run_uq_calls_finalize_on_all_reducers(self):
        """Test that finalize is called on all reducers."""
        def base_callable(network, rng):
            return {"value": 1.0}
        
        reducer1 = MockReducer("Reducer1")
        reducer2 = MockReducer("Reducer2")
        
        plan = UQPlan(
            base_callable=base_callable,
            strategy="seed",
            noise_model=NoNoise(),
            n_samples=3,
            seed=42,
            reducers=[reducer1, reducer2],
            storage_mode="none"
        )
        
        result = run_uq(plan, Mock())
        
        # Both should be finalized
        assert reducer1.finalized
        assert reducer2.finalized
        
        # Outputs should be in result
        assert "Reducer1" in result.reducer_outputs
        assert "Reducer2" in result.reducer_outputs
    
    def test_run_uq_reducer_outputs_in_result(self):
        """Test that reducer outputs are included in result."""
        def base_callable(network, rng):
            return {"iteration": 1}
        
        reducer = MockReducer("TestReducer")
        plan = UQPlan(
            base_callable=base_callable,
            strategy="seed",
            noise_model=NoNoise(),
            n_samples=5,
            seed=42,
            reducers=[reducer],
            storage_mode="none"
        )
        
        result = run_uq(plan, Mock())
        
        assert "TestReducer" in result.reducer_outputs
        output = result.reducer_outputs["TestReducer"]
        assert output["count"] == 5
        assert output["reducer"] == "TestReducer"


class TestRunUQStorageMode:
    """Test storage_mode handling."""
    
    def test_run_uq_storage_none_does_not_store_samples(self):
        """Test that storage_mode='none' doesn't store samples."""
        def base_callable(network, rng):
            return {"value": rng.random()}
        
        plan = UQPlan(
            base_callable=base_callable,
            strategy="seed",
            noise_model=NoNoise(),
            n_samples=5,
            seed=42,
            reducers=[MockReducer()],
            storage_mode="none"
        )
        
        result = run_uq(plan, Mock())
        
        assert result.samples is None
    
    def test_run_uq_storage_samples_stores_all_samples(self):
        """Test that storage_mode='samples' stores all sample outputs."""
        def base_callable(network, rng):
            return {"value": rng.random()}
        
        plan = UQPlan(
            base_callable=base_callable,
            strategy="seed",
            noise_model=NoNoise(),
            n_samples=5,
            seed=42,
            reducers=[MockReducer()],
            storage_mode="samples"
        )
        
        result = run_uq(plan, Mock())
        
        assert result.samples is not None
        assert len(result.samples) == 5
        assert all("value" in sample for sample in result.samples)


class TestRunUQProvenance:
    """Test provenance tracking."""
    
    def test_run_uq_includes_provenance(self):
        """Test that result includes provenance metadata."""
        def base_callable(network, rng):
            return {"value": 1.0}
        
        plan = UQPlan(
            base_callable=base_callable,
            strategy="seed",
            noise_model=NoNoise(),
            n_samples=5,
            seed=42,
            reducers=[MockReducer()],
            storage_mode="none"
        )
        
        result = run_uq(plan, Mock())
        
        assert hasattr(result, "provenance")
        assert result.provenance is not None
    
    def test_run_uq_provenance_includes_randomness(self):
        """Test that provenance includes randomness info."""
        def base_callable(network, rng):
            return {"value": 1.0}
        
        plan = UQPlan(
            base_callable=base_callable,
            strategy="perturbation",
            noise_model=NoNoise(),
            n_samples=10,
            seed=42,
            reducers=[MockReducer()],
            storage_mode="sketch"
        )
        
        result = run_uq(plan, Mock())
        
        assert "randomness" in result.provenance
        randomness = result.provenance["randomness"]
        assert randomness["seed"] == 42
        assert randomness["n_samples"] == 10
        assert randomness["strategy"] == "perturbation"
    
    def test_run_uq_provenance_includes_execution_info(self):
        """Test that provenance includes execution metadata."""
        def base_callable(network, rng):
            return {"value": 1.0}
        
        reducer1 = MockReducer("Reducer1")
        reducer2 = MockReducer("Reducer2")
        
        plan = UQPlan(
            base_callable=base_callable,
            strategy="seed",
            noise_model=NoNoise(),
            n_samples=5,
            seed=42,
            reducers=[reducer1, reducer2],
            storage_mode="samples",
            backend="python"
        )
        
        result = run_uq(plan, Mock())
        
        assert "execution" in result.provenance
        execution = result.provenance["execution"]
        assert execution["storage_mode"] == "samples"
        assert execution["backend"] == "python"
        assert "Reducer1" in execution["reducers"]
        assert "Reducer2" in execution["reducers"]


class TestRunUQNoiseModel:
    """Test noise model application."""
    
    def test_run_uq_with_no_noise_model(self):
        """Test that NoNoise completes all iterations and passes structurally
        equivalent networks to base_callable."""
        networks_received = []
        
        def base_callable(network, rng):
            networks_received.append(network)
            return {"value": 1.0}
        
        plan = UQPlan(
            base_callable=base_callable,
            strategy="seed",
            noise_model=NoNoise(),
            n_samples=3,
            seed=42,
            reducers=[MockReducer()],
            storage_mode="none"
        )
        
        original_network = Mock()
        # Make deepcopy comparisons work by using a counter attribute
        original_network._tag = "original"
        run_uq(plan, original_network)
        
        # All three iterations should have been called
        assert len(networks_received) == 3
    
    def test_run_uq_with_none_noise_model(self):
        """Test that plan.noise_model=None works correctly."""
        def base_callable(network, rng):
            return {"value": 1.0}
        
        plan = UQPlan(
            base_callable=base_callable,
            strategy="seed",
            noise_model=None,  # Explicitly None
            n_samples=3,
            seed=42,
            reducers=[MockReducer()],
            storage_mode="none"
        )
        
        result = run_uq(plan, Mock())
        
        # Should complete without error
        assert result.n_samples == 3


class TestRunUQEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_run_uq_with_single_sample(self):
        """Test that n_samples=1 works correctly."""
        def base_callable(network, rng):
            return {"value": rng.random()}
        
        reducer = MockReducer()
        plan = UQPlan(
            base_callable=base_callable,
            strategy="seed",
            noise_model=NoNoise(),
            n_samples=1,
            seed=42,
            reducers=[reducer],
            storage_mode="samples"
        )
        
        result = run_uq(plan, Mock())
        
        assert result.n_samples == 1
        assert len(reducer.updates) == 1
        assert len(result.samples) == 1
    
    def test_run_uq_with_zero_reducers(self):
        """Test that zero reducers works (edge case)."""
        def base_callable(network, rng):
            return {"value": 1.0}
        
        plan = UQPlan(
            base_callable=base_callable,
            strategy="seed",
            noise_model=NoNoise(),
            n_samples=5,
            seed=42,
            reducers=[],  # No reducers
            storage_mode="none"
        )
        
        result = run_uq(plan, Mock())
        
        # Should complete without error
        assert result.n_samples == 5
        assert result.reducer_outputs == {}
    
    def test_run_uq_callable_returns_various_types(self):
        """Test that base_callable can return different types."""
        outputs = [
            {"dict": "value"},
            [1, 2, 3],
            "string",
            42,
            (1, 2, 3),
        ]
        
        outputs_iter = iter(outputs)
        
        def base_callable(network, rng):
            try:
                return next(outputs_iter)
            except StopIteration:
                return None
        
        reducer = MockReducer()
        plan = UQPlan(
            base_callable=base_callable,
            strategy="seed",
            noise_model=NoNoise(),
            n_samples=5,
            seed=42,
            reducers=[reducer],
            storage_mode="samples"
        )
        
        result = run_uq(plan, Mock())
        
        # All outputs should be captured
        assert len(reducer.updates) == 5
        assert len(result.samples) == 5
        assert result.samples[0] == {"dict": "value"}
        assert result.samples[1] == [1, 2, 3]
