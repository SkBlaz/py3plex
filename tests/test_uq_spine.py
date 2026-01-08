"""Tests for UQ execution spine.

This module tests the core UQ execution infrastructure:
- UQPlan validation
- run_uq() execution semantics
- NoNoise model
- Reducer integration
"""

import numpy as np
import pytest

from py3plex.uncertainty.plan import UQPlan, UQResult
from py3plex.uncertainty.runner import run_uq
from py3plex.uncertainty.noise_models import NoNoise, EdgeDrop
from py3plex.uncertainty.partition_types import PartitionOutput
from py3plex.uncertainty.partition_reducers import NodeMarginalReducer
from py3plex.core import multinet


class TestUQPlan:
    """Test UQPlan validation and construction."""
    
    def test_valid_plan_construction(self):
        """Test creating a valid UQPlan."""
        def dummy_callable(net, rng):
            return PartitionOutput(labels={'A': 0, 'B': 0})
        
        plan = UQPlan(
            base_callable=dummy_callable,
            strategy="seed",
            noise_model=NoNoise(),
            n_samples=10,
            seed=42,
            reducers=[],
            storage_mode="sketch",
            backend="python"
        )
        
        assert plan.strategy == "seed"
        assert plan.n_samples == 10
        assert plan.seed == 42
        assert plan.storage_mode == "sketch"
    
    def test_perturbation_requires_noise_model(self):
        """Test that perturbation strategy requires noise_model."""
        def dummy_callable(net, rng):
            return PartitionOutput(labels={'A': 0})
        
        with pytest.raises(ValueError, match="noise_model is required"):
            UQPlan(
                base_callable=dummy_callable,
                strategy="perturbation",
                noise_model=None,
                n_samples=10,
                seed=42,
                reducers=[]
            )
    
    def test_invalid_strategy(self):
        """Test that invalid strategy raises error."""
        def dummy_callable(net, rng):
            return PartitionOutput(labels={'A': 0})
        
        with pytest.raises(ValueError, match="Invalid strategy"):
            UQPlan(
                base_callable=dummy_callable,
                strategy="invalid",
                noise_model=NoNoise(),
                n_samples=10,
                seed=42,
                reducers=[]
            )
    
    def test_invalid_n_samples(self):
        """Test that n_samples must be positive."""
        def dummy_callable(net, rng):
            return PartitionOutput(labels={'A': 0})
        
        with pytest.raises(ValueError, match="n_samples must be >= 1"):
            UQPlan(
                base_callable=dummy_callable,
                strategy="seed",
                noise_model=NoNoise(),
                n_samples=0,
                seed=42,
                reducers=[]
            )


class TestNoNoise:
    """Test NoNoise model."""
    
    def test_no_noise_returns_copy(self):
        """Test that NoNoise returns unmodified copy."""
        net = multinet.multi_layer_network(directed=False)
        net.add_nodes([{'source': 'A', 'type': 'social'}])
        
        noise = NoNoise()
        perturbed = noise.apply(net, seed=42)
        
        # Should be different object (copy)
        assert perturbed is not net
        
        # But same structure
        assert len(list(perturbed.get_nodes())) == len(list(net.get_nodes()))
    
    def test_no_noise_serialization(self):
        """Test NoNoise serialization."""
        noise = NoNoise()
        d = noise.to_dict()
        
        assert d == {"type": "NoNoise"}


class TestRunUQ:
    """Test run_uq() execution."""
    
    def test_basic_execution(self):
        """Test basic UQ execution."""
        # Create dummy network
        net = multinet.multi_layer_network(directed=False)
        net.add_nodes([
            {'source': 'A', 'type': 'social'},
            {'source': 'B', 'type': 'social'},
            {'source': 'C', 'type': 'social'},
        ])
        
        # Define deterministic algorithm
        def deterministic_partition(network, rng):
            return PartitionOutput(labels={'A': 0, 'B': 0, 'C': 1})
        
        # Create reducer
        reducer = NodeMarginalReducer(n_nodes=3, node_ids=['A', 'B', 'C'])
        
        # Create plan
        plan = UQPlan(
            base_callable=deterministic_partition,
            strategy="seed",
            noise_model=NoNoise(),
            n_samples=5,
            seed=42,
            reducers=[reducer],
            storage_mode="sketch"
        )
        
        # Execute
        result = run_uq(plan, net)
        
        # Check result
        assert isinstance(result, UQResult)
        assert result.n_samples == 5
        assert 'NodeMarginalReducer' in result.reducer_outputs
        assert result.samples is None  # sketch mode
    
    def test_deterministic_algorithm_zero_entropy(self):
        """Test that deterministic algorithm produces zero entropy."""
        # Create network
        net = multinet.multi_layer_network(directed=False)
        net.add_nodes([
            {'source': 'A', 'type': 'social'},
            {'source': 'B', 'type': 'social'},
        ])
        
        # Deterministic algorithm always returns same partition
        def deterministic(network, rng):
            return PartitionOutput(labels={'A': 0, 'B': 1})
        
        reducer = NodeMarginalReducer(n_nodes=2, node_ids=['A', 'B'])
        
        plan = UQPlan(
            base_callable=deterministic,
            strategy="seed",
            noise_model=NoNoise(),
            n_samples=10,
            seed=42,
            reducers=[reducer]
        )
        
        result = run_uq(plan, net)
        stats = result.reducer_outputs['NodeMarginalReducer']
        
        # Entropy should be zero (deterministic)
        assert np.allclose(stats['entropy'], 0.0)
        # p_max should be 1.0 (always same label)
        assert np.allclose(stats['p_max'], 1.0)
    
    def test_reproducibility_with_seed(self):
        """Test that same seed produces same results."""
        net = multinet.multi_layer_network(directed=False)
        net.add_nodes([{'source': 'A', 'type': 'social'}])
        
        # Algorithm with randomness
        def random_partition(network, rng):
            label = int(rng.integers(0, 2))
            return PartitionOutput(labels={'A': label})
        
        reducer1 = NodeMarginalReducer(n_nodes=1, node_ids=['A'])
        reducer2 = NodeMarginalReducer(n_nodes=1, node_ids=['A'])
        
        plan1 = UQPlan(
            base_callable=random_partition,
            strategy="seed",
            noise_model=NoNoise(),
            n_samples=20,
            seed=42,
            reducers=[reducer1]
        )
        
        plan2 = UQPlan(
            base_callable=random_partition,
            strategy="seed",
            noise_model=NoNoise(),
            n_samples=20,
            seed=42,
            reducers=[reducer2]
        )
        
        result1 = run_uq(plan1, net)
        result2 = run_uq(plan2, net)
        
        stats1 = result1.reducer_outputs['NodeMarginalReducer']
        stats2 = result2.reducer_outputs['NodeMarginalReducer']
        
        # Should produce identical results
        assert np.allclose(stats1['entropy'], stats2['entropy'])
        assert np.allclose(stats1['p_max'], stats2['p_max'])
    
    def test_storage_mode_samples(self):
        """Test that storage_mode='samples' stores samples."""
        net = multinet.multi_layer_network(directed=False)
        net.add_nodes([{'source': 'A', 'type': 'social'}])
        
        def dummy(network, rng):
            return PartitionOutput(labels={'A': 0})
        
        plan = UQPlan(
            base_callable=dummy,
            strategy="seed",
            noise_model=NoNoise(),
            n_samples=5,
            seed=42,
            reducers=[],
            storage_mode="samples"
        )
        
        result = run_uq(plan, net)
        
        # Samples should be stored
        assert result.samples is not None
        assert len(result.samples) == 5
    
    def test_provenance_tracking(self):
        """Test that provenance is properly tracked."""
        net = multinet.multi_layer_network(directed=False)
        net.add_nodes([{'source': 'A', 'type': 'social'}])
        
        def dummy(network, rng):
            return PartitionOutput(labels={'A': 0})
        
        plan = UQPlan(
            base_callable=dummy,
            strategy="perturbation",
            noise_model=EdgeDrop(p=0.1),
            n_samples=10,
            seed=42,
            reducers=[]
        )
        
        result = run_uq(plan, net)
        
        # Check provenance
        assert 'randomness' in result.provenance
        assert result.provenance['randomness']['seed'] == 42
        assert result.provenance['randomness']['n_samples'] == 10
        assert result.provenance['randomness']['strategy'] == "perturbation"
        assert result.provenance['randomness']['noise_model']['type'] == "EdgeDrop"
        
        assert 'execution' in result.provenance
        assert result.provenance['execution']['storage_mode'] == "sketch"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
