"""Tests for the uncertainty module.

This module tests the core uncertainty types and context management.
"""

import numpy as np
import pytest

from py3plex.core import multinet
from py3plex.uncertainty import (
    StatSeries,
    StatMatrix,
    CommunityStats,
    ResamplingStrategy,
    UncertaintyMode,
    UncertaintyConfig,
    get_uncertainty_config,
    set_uncertainty_config,
    uncertainty_enabled,
    estimate_uncertainty,
)
from py3plex.uncertainty.context import uncertainty_disabled


class TestStatSeries:
    """Tests for StatSeries type."""
    
    def test_deterministic_creation(self):
        """Test creating a deterministic StatSeries."""
        s = StatSeries(
            index=['a', 'b', 'c'],
            mean=np.array([1.0, 2.0, 3.0])
        )
        
        assert s.is_deterministic
        assert s.certainty == 1.0
        assert len(s) == 3
        assert list(s.mean) == [1.0, 2.0, 3.0]
        assert s.std is None
        assert s.quantiles is None
    
    def test_uncertain_creation(self):
        """Test creating an uncertain StatSeries."""
        s = StatSeries(
            index=['a', 'b', 'c'],
            mean=np.array([1.0, 2.0, 3.0]),
            std=np.array([0.1, 0.2, 0.15]),
            quantiles={
                0.025: np.array([0.8, 1.6, 2.7]),
                0.975: np.array([1.2, 2.4, 3.3])
            }
        )
        
        assert not s.is_deterministic
        assert s.certainty == 0.0
        assert len(s) == 3
        assert s.std is not None
        assert s.quantiles is not None
        assert 0.025 in s.quantiles
        assert 0.975 in s.quantiles
    
    def test_array_conversion(self):
        """Test conversion to numpy array."""
        s = StatSeries(
            index=['a', 'b', 'c'],
            mean=np.array([1.0, 2.0, 3.0])
        )
        
        arr = np.array(s)
        assert isinstance(arr, np.ndarray)
        assert list(arr) == [1.0, 2.0, 3.0]
    
    def test_getitem(self):
        """Test dictionary-like access."""
        s = StatSeries(
            index=['a', 'b', 'c'],
            mean=np.array([1.0, 2.0, 3.0]),
            std=np.array([0.1, 0.2, 0.15])
        )
        
        item = s['a']
        assert item['mean'] == 1.0
        assert item['std'] == 0.1
        
        with pytest.raises(KeyError):
            _ = s['nonexistent']
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        s = StatSeries(
            index=['a', 'b'],
            mean=np.array([1.0, 2.0]),
            std=np.array([0.1, 0.2])
        )
        
        d = s.to_dict()
        assert 'a' in d
        assert 'b' in d
        assert d['a']['mean'] == 1.0
        assert d['a']['std'] == 0.1
    
    def test_validation_mean_length(self):
        """Test validation of mean length."""
        with pytest.raises(ValueError, match="mean length"):
            StatSeries(
                index=['a', 'b', 'c'],
                mean=np.array([1.0, 2.0])  # Wrong length
            )
    
    def test_validation_std_length(self):
        """Test validation of std length."""
        with pytest.raises(ValueError, match="std length"):
            StatSeries(
                index=['a', 'b', 'c'],
                mean=np.array([1.0, 2.0, 3.0]),
                std=np.array([0.1, 0.2])  # Wrong length
            )


class TestStatMatrix:
    """Tests for StatMatrix type."""
    
    def test_deterministic_creation(self):
        """Test creating a deterministic StatMatrix."""
        m = StatMatrix(
            index=['a', 'b', 'c'],
            mean=np.array([
                [0, 1, 0],
                [1, 0, 1],
                [0, 1, 0]
            ], dtype=float)
        )
        
        assert m.is_deterministic
        assert m.certainty == 1.0
        assert len(m) == 3
        assert m.mean.shape == (3, 3)
    
    def test_uncertain_creation(self):
        """Test creating an uncertain StatMatrix."""
        m = StatMatrix(
            index=['a', 'b'],
            mean=np.array([[0, 1], [1, 0]], dtype=float),
            std=np.array([[0, 0.1], [0.1, 0]], dtype=float)
        )
        
        assert not m.is_deterministic
        assert m.certainty == 0.0
        assert m.std is not None
    
    def test_array_conversion(self):
        """Test conversion to numpy array."""
        m = StatMatrix(
            index=['a', 'b'],
            mean=np.array([[0, 1], [1, 0]], dtype=float)
        )
        
        arr = np.array(m)
        assert isinstance(arr, np.ndarray)
        assert arr.shape == (2, 2)
    
    def test_validation_shape(self):
        """Test validation of matrix shape."""
        with pytest.raises(ValueError, match="mean shape"):
            StatMatrix(
                index=['a', 'b', 'c'],
                mean=np.array([[0, 1], [1, 0]], dtype=float)  # Wrong shape
            )


class TestCommunityStats:
    """Tests for CommunityStats type."""
    
    def test_deterministic_creation(self):
        """Test creating deterministic community stats."""
        cs = CommunityStats(
            labels={'a': 0, 'b': 0, 'c': 1},
            modularity=0.42,
            n_communities=2
        )
        
        assert cs.is_deterministic
        assert cs.certainty == 1.0
        assert len(cs) == 3
        assert cs.n_communities == 2
        assert cs.labels['a'] == 0
    
    def test_uncertain_creation(self):
        """Test creating uncertain community stats."""
        cs = CommunityStats(
            labels={'a': 0, 'b': 0, 'c': 1},
            modularity=0.42,
            modularity_std=0.05,
            n_communities=2
        )
        
        assert not cs.is_deterministic
        assert cs.certainty == 0.0
        assert cs.modularity_std == 0.05
    
    def test_auto_compute_n_communities(self):
        """Test automatic computation of n_communities."""
        cs = CommunityStats(
            labels={'a': 0, 'b': 0, 'c': 1, 'd': 2}
        )
        
        assert cs.n_communities == 3


class TestUncertaintyContext:
    """Tests for uncertainty context management."""
    
    def test_default_config(self):
        """Test default uncertainty configuration."""
        cfg = get_uncertainty_config()
        
        assert cfg.mode == UncertaintyMode.OFF
        assert cfg.default_n_runs == 50
        assert cfg.default_resampling == ResamplingStrategy.SEED
    
    def test_set_config(self):
        """Test setting uncertainty configuration."""
        new_cfg = UncertaintyConfig(
            mode=UncertaintyMode.ON,
            default_n_runs=100
        )
        
        token = set_uncertainty_config(new_cfg)
        
        cfg = get_uncertainty_config()
        assert cfg.mode == UncertaintyMode.ON
        assert cfg.default_n_runs == 100
        
        # Reset
        from py3plex.uncertainty.context import _uncertainty_ctx
        _uncertainty_ctx.reset(token)
    
    def test_uncertainty_enabled_context(self):
        """Test uncertainty_enabled context manager."""
        # Check initial state
        cfg = get_uncertainty_config()
        initial_mode = cfg.mode
        
        # Enter context
        with uncertainty_enabled(n_runs=100):
            cfg = get_uncertainty_config()
            assert cfg.mode == UncertaintyMode.ON
            assert cfg.default_n_runs == 100
        
        # Check state after exit
        cfg = get_uncertainty_config()
        assert cfg.mode == initial_mode
    
    def test_uncertainty_disabled_context(self):
        """Test uncertainty_disabled context manager."""
        with uncertainty_enabled():
            # Within enabled context
            cfg = get_uncertainty_config()
            assert cfg.mode == UncertaintyMode.ON
            
            # Nested disabled context
            with uncertainty_disabled():
                cfg = get_uncertainty_config()
                assert cfg.mode == UncertaintyMode.OFF
            
            # Back to enabled
            cfg = get_uncertainty_config()
            assert cfg.mode == UncertaintyMode.ON


class TestEstimateUncertainty:
    """Tests for estimate_uncertainty function."""
    
    def build_simple_network(self):
        """Build a simple test network."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        edges = [
            ["a", "L0", "b", "L0", 1.0],
            ["b", "L0", "c", "L0", 1.0],
            ["c", "L0", "a", "L0", 1.0],
        ]
        net.add_edges(edges, input_type="list")
        return net
    
    def test_estimate_with_dict_metric(self):
        """Test estimation with per-node metric."""
        net = self.build_simple_network()
        
        def degree_metric(network):
            """Compute degree for each node."""
            degrees = {}
            for node in network.get_nodes():
                degrees[node] = network.core_network.degree(node)
            return degrees
        
        result = estimate_uncertainty(
            net,
            degree_metric,
            n_runs=10,
            resampling=ResamplingStrategy.PERTURBATION,
            perturbation_params={"edge_drop_p": 0.1},
            random_seed=42
        )
        
        assert isinstance(result, StatSeries)
        assert len(result) == 3
        assert result.std is not None
        assert result.quantiles is not None
    
    def test_estimate_with_scalar_metric(self):
        """Test estimation with scalar metric."""
        net = self.build_simple_network()
        
        def edge_count_metric(network):
            """Count edges."""
            return len(list(network.get_edges()))
        
        result = estimate_uncertainty(
            net,
            edge_count_metric,
            n_runs=10,
            resampling=ResamplingStrategy.PERTURBATION,
            perturbation_params={"edge_drop_p": 0.1},
            random_seed=42
        )
        
        assert isinstance(result, float)
        assert result > 0
    
    def test_estimate_uses_config_defaults(self):
        """Test that estimation uses config defaults."""
        net = self.build_simple_network()
        
        def simple_metric(network):
            return {"node": 1.0}
        
        # Set config with specific defaults
        with uncertainty_enabled(n_runs=20):
            result = estimate_uncertainty(
                net,
                simple_metric,
                resampling=ResamplingStrategy.SEED,
                random_seed=42
            )
            
            assert isinstance(result, StatSeries)
            assert result.meta.get("n_samples") == 20
    
    def test_estimate_invalid_n_runs(self):
        """Test validation of n_runs parameter."""
        net = self.build_simple_network()
        
        def simple_metric(network):
            return 1.0
        
        with pytest.raises(ValueError, match="n_runs must be positive"):
            estimate_uncertainty(net, simple_metric, n_runs=0)
    
    def test_estimate_seed_strategy(self):
        """Test estimation with SEED strategy."""
        net = self.build_simple_network()
        
        def simple_metric(network):
            nodes = list(network.get_nodes())
            return {node: float(len(nodes)) for node in nodes}
        
        result = estimate_uncertainty(
            net,
            simple_metric,
            n_runs=5,
            resampling=ResamplingStrategy.SEED,
            random_seed=42
        )
        
        assert isinstance(result, StatSeries)
        # For deterministic metrics, std should be 0
        assert np.all(result.std == 0)


class TestEnums:
    """Tests for enum types."""
    
    def test_resampling_strategy_values(self):
        """Test ResamplingStrategy enum values."""
        assert ResamplingStrategy.SEED.value == "seed"
        assert ResamplingStrategy.BOOTSTRAP.value == "bootstrap"
        assert ResamplingStrategy.JACKKNIFE.value == "jackknife"
        assert ResamplingStrategy.PERTURBATION.value == "perturbation"
    
    def test_uncertainty_mode_values(self):
        """Test UncertaintyMode enum values."""
        assert UncertaintyMode.OFF.value == "off"
        assert UncertaintyMode.ON.value == "on"
        assert UncertaintyMode.AUTO.value == "auto"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
