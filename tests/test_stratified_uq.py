"""Tests for stratified perturbation uncertainty quantification.

This module tests the stratified resampling infrastructure that reduces
estimator variance while maintaining determinism and backward compatibility.
"""

import pytest
import numpy as np
from py3plex.core import multinet
from py3plex.dsl import Q
from py3plex.uncertainty import (
    ResamplingStrategy,
    estimate_uncertainty,
    StratificationSpec,
    auto_select_strata,
    compute_composite_strata,
    compute_variance_reduction_ratio,
)
from py3plex.uncertainty.stratification import (
    stratify_nodes_by_degree,
    stratify_nodes_by_layer,
    stratify_edges_by_layer_pair,
    stratify_edges_by_weight,
)


def build_test_network():
    """Build a simple multilayer network for testing."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    edges = [
        # Layer 0: Triangle (3 nodes)
        ["a", "L0", "b", "L0", 1.0],
        ["b", "L0", "c", "L0", 1.0],
        ["c", "L0", "a", "L0", 1.0],
        # Layer 1: Chain (5 nodes)
        ["a", "L1", "b", "L1", 1.0],
        ["b", "L1", "c", "L1", 1.0],
        ["c", "L1", "d", "L1", 1.0],
        ["d", "L1", "e", "L1", 1.0],
        # Inter-layer connections
        ["a", "L0", "a", "L1", 1.0],
        ["b", "L0", "b", "L1", 1.0],
        ["c", "L0", "c", "L1", 1.0],
    ]
    net.add_edges(edges, input_type="list")
    return net


def build_weighted_network():
    """Build a network with varying edge weights."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    edges = [
        ["a", "L0", "b", "L0", 0.5],
        ["b", "L0", "c", "L0", 1.0],
        ["c", "L0", "d", "L0", 2.0],
        ["d", "L0", "e", "L0", 3.0],
        ["e", "L0", "a", "L0", 5.0],
    ]
    net.add_edges(edges, input_type="list")
    return net


class TestStratificationSpec:
    """Tests for StratificationSpec configuration."""
    
    def test_spec_creation(self):
        """Test creating a stratification spec."""
        spec = StratificationSpec(
            strata=["degree", "layer"],
            bins={"degree": 5},
            seed=42
        )
        assert spec.strata == ["degree", "layer"]
        assert spec.bins["degree"] == 5
        assert spec.seed == 42
    
    def test_spec_defaults(self):
        """Test default bin values are set."""
        spec = StratificationSpec(strata=["degree", "weight"])
        assert spec.bins["degree"] == 5
        assert spec.bins["weight"] == 5
    
    def test_spec_invalid_stratum(self):
        """Test that invalid strata raise error."""
        with pytest.raises(ValueError, match="Unknown stratification dimension"):
            StratificationSpec(strata=["invalid"])
    
    def test_spec_to_dict(self):
        """Test serialization to dict."""
        spec = StratificationSpec(
            strata=["degree"],
            bins={"degree": 3},
            seed=123
        )
        d = spec.to_dict()
        assert d["strata"] == ["degree"]
        assert d["bins"] == {"degree": 3}
        assert d["seed"] == 123


class TestAutoSelectStrata:
    """Tests for automatic stratum selection."""
    
    def test_auto_select_nodes(self):
        """Test auto-selection for node queries."""
        strata = auto_select_strata("nodes")
        assert strata == ["degree"]
    
    def test_auto_select_edges(self):
        """Test auto-selection for edge queries."""
        strata = auto_select_strata("edges")
        assert strata == ["layer_pair"]
    
    def test_auto_select_unknown(self):
        """Test auto-selection for unknown target."""
        strata = auto_select_strata("unknown")
        assert strata == []


class TestDegreeStratification:
    """Tests for degree-based stratification."""
    
    def test_stratify_by_degree(self):
        """Test node stratification by degree."""
        net = build_test_network()
        strata = stratify_nodes_by_degree(net, n_bins=3)
        
        # Should have some strata
        assert len(strata) > 0
        
        # All nodes should be in some stratum
        all_nodes = set()
        for nodes in strata.values():
            all_nodes.update(nodes)
        assert all_nodes == set(net.get_nodes())
    
    def test_degree_stratification_empty_network(self):
        """Test degree stratification on empty network."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        strata = stratify_nodes_by_degree(net, n_bins=5)
        assert strata == {0: []}
    
    def test_degree_stratification_few_unique_values(self):
        """Test degree stratification with few unique degree values."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        # Create a network where all nodes have the same degree
        edges = [
            ["a", "L0", "b", "L0", 1.0],
            ["c", "L0", "d", "L0", 1.0],
        ]
        net.add_edges(edges, input_type="list")
        
        strata = stratify_nodes_by_degree(net, n_bins=5)
        # Should still work even with few unique values
        assert len(strata) >= 1


class TestLayerStratification:
    """Tests for layer-based stratification."""
    
    def test_stratify_by_layer(self):
        """Test node stratification by layer."""
        net = build_test_network()
        strata = stratify_nodes_by_layer(net)
        
        # Should have strata for layers
        assert len(strata) >= 1
        
        # Check that nodes are assigned to appropriate layers
        for layer, nodes in strata.items():
            assert len(nodes) > 0


class TestLayerPairStratification:
    """Tests for layer-pair stratification."""
    
    def test_stratify_by_layer_pair(self):
        """Test edge stratification by layer pair."""
        net = build_test_network()
        strata = stratify_edges_by_layer_pair(net)
        
        # Should have strata for different layer pairs
        assert len(strata) > 0
        
        # All edges should be in some stratum
        all_edges = set()
        for edges in strata.values():
            all_edges.update(edges)
        
        # Count total edges in network
        n_edges = net.core_network.number_of_edges()
        assert len(all_edges) == n_edges


class TestWeightStratification:
    """Tests for weight-based stratification."""
    
    def test_stratify_by_weight(self):
        """Test edge stratification by weight."""
        net = build_weighted_network()
        strata = stratify_edges_by_weight(net, n_bins=3)
        
        # Should have some strata
        assert len(strata) > 0
        
        # All edges should be in some stratum
        all_edges = set()
        for edges in strata.values():
            all_edges.update(edges)
        assert len(all_edges) == net.core_network.number_of_edges()


class TestCompositeStratification:
    """Tests for composite (multi-dimensional) stratification."""
    
    def test_composite_degree_layer(self):
        """Test composite stratification by degree and layer."""
        net = build_test_network()
        spec = StratificationSpec(
            strata=["degree", "layer"],
            bins={"degree": 3}
        )
        
        strata = compute_composite_strata(net, spec, target="nodes")
        
        # Should have composite strata
        assert len(strata) > 0
        
        # Keys should be tuples (for composite strata)
        for key in strata.keys():
            if key != ():  # Empty tuple for no stratification
                assert isinstance(key, tuple)
    
    def test_composite_no_strata(self):
        """Test composite stratification with no dimensions."""
        net = build_test_network()
        spec = StratificationSpec(strata=[])
        
        strata = compute_composite_strata(net, spec, target="nodes")
        
        # Should have one stratum with all items
        assert len(strata) == 1
        assert () in strata


class TestVarianceReduction:
    """Tests for variance reduction metrics."""
    
    def test_variance_reduction_calculation(self):
        """Test variance reduction ratio calculation."""
        baseline_std = np.array([0.5, 0.6, 0.4])
        stratified_std = np.array([0.3, 0.4, 0.2])
        
        ratio = compute_variance_reduction_ratio(baseline_std, stratified_std)
        
        # Ratio should be positive (variance reduced)
        assert ratio > 0
        assert ratio < 1.0
    
    def test_variance_reduction_zero_baseline(self):
        """Test variance reduction with zero baseline."""
        baseline_std = np.array([0.0, 0.0, 0.0])
        stratified_std = np.array([0.1, 0.2, 0.1])
        
        ratio = compute_variance_reduction_ratio(baseline_std, stratified_std)
        
        # Should return 0 when baseline is 0
        assert ratio == 0.0


class TestStratifiedPerturbationEstimation:
    """Tests for stratified perturbation via estimate_uncertainty."""
    
    def test_stratified_perturbation_basic(self):
        """Test basic stratified perturbation."""
        net = build_test_network()
        
        def degree_metric(network):
            return dict(network.core_network.degree())
        
        result = estimate_uncertainty(
            net,
            degree_metric,
            n_runs=20,
            resampling=ResamplingStrategy.STRATIFIED_PERTURBATION,
            random_seed=42,
            perturbation_params={
                "edge_drop_p": 0.1,
                "strata": ["degree"],
                "bins": {"degree": 3}
            }
        )
        
        # Should return StatSeries
        from py3plex.uncertainty.types import StatSeries
        assert isinstance(result, StatSeries)
        
        # Should have mean and std
        assert result.mean is not None
        assert result.std is not None
        
        # Check metadata
        assert "stratification" in result.meta
        assert result.meta["stratification"]["strata"] == ["degree"]
    
    def test_stratified_perturbation_determinism(self):
        """Test that stratified perturbation is deterministic with same seed."""
        net = build_test_network()
        
        def degree_metric(network):
            return dict(network.core_network.degree())
        
        # Run twice with same seed
        result1 = estimate_uncertainty(
            net,
            degree_metric,
            n_runs=10,
            resampling=ResamplingStrategy.STRATIFIED_PERTURBATION,
            random_seed=42,
            perturbation_params={
                "edge_drop_p": 0.1,
                "strata": ["degree"]
            }
        )
        
        result2 = estimate_uncertainty(
            net,
            degree_metric,
            n_runs=10,
            resampling=ResamplingStrategy.STRATIFIED_PERTURBATION,
            random_seed=42,
            perturbation_params={
                "edge_drop_p": 0.1,
                "strata": ["degree"]
            }
        )
        
        # Results should be identical
        np.testing.assert_array_almost_equal(result1.mean, result2.mean)
        np.testing.assert_array_almost_equal(result1.std, result2.std)
    
    def test_stratified_perturbation_auto_strata(self):
        """Test stratified perturbation with auto-selected strata."""
        net = build_test_network()
        
        def degree_metric(network):
            return dict(network.core_network.degree())
        
        result = estimate_uncertainty(
            net,
            degree_metric,
            n_runs=20,
            resampling=ResamplingStrategy.STRATIFIED_PERTURBATION,
            random_seed=42,
            perturbation_params={
                "edge_drop_p": 0.1,
                "strata": None  # Auto-select
            }
        )
        
        # Should work and auto-select degree for node metrics
        from py3plex.uncertainty.types import StatSeries
        assert isinstance(result, StatSeries)
        assert "stratification" in result.meta
    
    def test_stratified_perturbation_fallback_to_regular(self):
        """Test fallback to regular perturbation when stratification fails."""
        net = build_test_network()
        
        def degree_metric(network):
            return dict(network.core_network.degree())
        
        # Empty strata list should fall back
        result = estimate_uncertainty(
            net,
            degree_metric,
            n_runs=10,
            resampling=ResamplingStrategy.STRATIFIED_PERTURBATION,
            random_seed=42,
            perturbation_params={
                "edge_drop_p": 0.1,
                "strata": []  # Empty - should fall back
            }
        )
        
        # Should still work via fallback
        from py3plex.uncertainty.types import StatSeries
        assert isinstance(result, StatSeries)


class TestDSLIntegration:
    """Tests for DSL integration with stratified UQ."""
    
    def test_dsl_stratified_perturbation(self):
        """Test stratified perturbation via DSL."""
        net = build_test_network()
        
        result = (
            Q.nodes()
            .compute("degree")
            .uq(
                method="stratified_perturbation",
                n_samples=20,
                seed=42,
                strata=["degree"],
                bins={"degree": 3},
                edge_drop_p=0.1
            )
            .execute(net)
        )
        
        # Should return result
        assert len(result) > 0
    
    def test_dsl_stratified_perturbation_auto(self):
        """Test stratified perturbation with auto strata via DSL."""
        net = build_test_network()
        
        result = (
            Q.nodes()
            .compute("degree")
            .uq(
                method="stratified_perturbation",
                n_samples=20,
                seed=42,
                edge_drop_p=0.1
            )
            .execute(net)
        )
        
        # Should work with auto-selected strata
        assert len(result) > 0


class TestBackwardCompatibility:
    """Tests for backward compatibility with existing UQ methods."""
    
    def test_regular_perturbation_still_works(self):
        """Test that regular perturbation still works."""
        net = build_test_network()
        
        def degree_metric(network):
            return dict(network.core_network.degree())
        
        result = estimate_uncertainty(
            net,
            degree_metric,
            n_runs=10,
            resampling=ResamplingStrategy.PERTURBATION,
            random_seed=42,
            perturbation_params={"edge_drop_p": 0.1}
        )
        
        from py3plex.uncertainty.types import StatSeries
        assert isinstance(result, StatSeries)
    
    def test_default_behavior_unchanged(self):
        """Test that default UQ behavior is unchanged."""
        net = build_test_network()
        
        # Default should still be SEED strategy
        from py3plex.uncertainty import get_uncertainty_config
        cfg = get_uncertainty_config()
        assert cfg.default_resampling == ResamplingStrategy.SEED


class TestPicklability:
    """Tests for picklability of stratification components."""
    
    def test_stratification_spec_picklable(self):
        """Test that StratificationSpec is picklable."""
        import pickle
        
        spec = StratificationSpec(
            strata=["degree", "layer"],
            bins={"degree": 5},
            seed=42
        )
        
        # Should be picklable
        pickled = pickle.dumps(spec)
        unpickled = pickle.loads(pickled)
        
        assert unpickled.strata == spec.strata
        assert unpickled.bins == spec.bins
        assert unpickled.seed == spec.seed
    
    def test_stat_series_with_stratification_picklable(self):
        """Test that StatSeries with stratification metadata is picklable."""
        import pickle
        from py3plex.uncertainty.types import StatSeries
        
        result = StatSeries(
            index=['a', 'b', 'c'],
            mean=np.array([1.0, 2.0, 3.0]),
            std=np.array([0.1, 0.2, 0.15]),
            meta={
                "stratification": {
                    "strata": ["degree"],
                    "bins": {"degree": 5}
                },
                "n_strata": 3
            }
        )
        
        # Should be picklable
        pickled = pickle.dumps(result)
        unpickled = pickle.loads(pickled)
        
        assert unpickled.index == result.index
        np.testing.assert_array_equal(unpickled.mean, result.mean)
        assert unpickled.meta["stratification"]["strata"] == ["degree"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
