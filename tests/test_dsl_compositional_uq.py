"""Tests for compositional uncertainty quantification in DSL.

This module tests the new compositional UQ capabilities:
- Aggregate/summarize with UQ
- Order_by/limit with ranking stability
- Coverage with membership probability
"""

import pytest
import numpy as np
from py3plex.core import multinet
from py3plex.dsl import Q, L, UQ


@pytest.fixture
def simple_network():
    """Create a simple multilayer network for testing."""
    network = multinet.multi_layer_network(directed=False)
    
    nodes = [
        {'source': 'A', 'type': 'L0'},
        {'source': 'B', 'type': 'L0'},
        {'source': 'C', 'type': 'L0'},
        {'source': 'D', 'type': 'L0'},
        {'source': 'A', 'type': 'L1'},
        {'source': 'B', 'type': 'L1'},
        {'source': 'C', 'type': 'L1'},
    ]
    network.add_nodes(nodes)
    
    edges = [
        # L0: Star topology (B is hub)
        {'source': 'A', 'target': 'B', 'source_type': 'L0', 'target_type': 'L0', 'weight': 1.0},
        {'source': 'B', 'target': 'C', 'source_type': 'L0', 'target_type': 'L0', 'weight': 1.0},
        {'source': 'B', 'target': 'D', 'source_type': 'L0', 'target_type': 'L0', 'weight': 1.0},
        # L1: Triangle
        {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1', 'weight': 1.0},
        {'source': 'B', 'target': 'C', 'source_type': 'L1', 'target_type': 'L1', 'weight': 1.0},
        {'source': 'A', 'target': 'C', 'source_type': 'L1', 'target_type': 'L1', 'weight': 1.0},
    ]
    network.add_edges(edges)
    
    return network


class TestCompositionalUQDetection:
    """Test that compositional UQ is correctly detected."""
    
    def test_uq_detected_with_aggregate(self, simple_network):
        """Test that UQ is detected when using aggregate()."""
        query = (
            Q.nodes()
             .compute("degree")
             .per_layer()
             .aggregate(avg_degree="mean(degree)")
             .uq(method="perturbation", n_samples=5, seed=42)
        )
        
        # Execute query
        result = query.execute(simple_network)
        
        # Check that UQ metadata is present
        assert "uq" in result.meta
        assert result.meta["uq"]["type"] == "compositional"
        assert result.meta["uq"]["n_samples"] == 5
        assert result.meta["uq"]["has_aggregate"] is True
    
    def test_uq_detected_with_order_by(self, simple_network):
        """Test that UQ is detected when using order_by()."""
        query = (
            Q.nodes()
             .compute("degree")
             .order_by("-degree")
             .limit(3)
             .uq(method="perturbation", n_samples=5, seed=42)
        )
        
        # Execute query
        result = query.execute(simple_network)
        
        # Check that UQ metadata is present
        assert "uq" in result.meta
        # order_by + limit without aggregate uses selection UQ, not compositional
        assert result.meta["uq"]["type"] == "selection"
        
        # Check for ranking attributes (not in metadata but in attributes)
        assert "rank_mean" in result.attributes or "present_prob" in result.attributes


class TestAggregateWithUQ:
    """Test aggregate operations with uncertainty quantification."""
    
    def test_summarize_with_uq_basic(self, simple_network):
        """Test basic summarize with UQ."""
        result = (
            Q.nodes()
             .compute("degree")
             .summarize(mean_degree="mean(degree)")
             .uq(method="seed", n_samples=10, seed=42)
             .execute(simple_network)
        )
        
        # Check structure
        assert len(result.items) == 1  # One global summary
        assert "mean_degree" in result.attributes
        
        # Check that result has uncertainty info
        mean_deg_val = result.attributes["mean_degree"][result.items[0]]
        assert isinstance(mean_deg_val, dict)
        assert "mean" in mean_deg_val
        assert "std" in mean_deg_val
        assert "n_samples" in mean_deg_val
        assert mean_deg_val["n_samples"] == 10
    
    def test_aggregate_per_layer_with_uq(self, simple_network):
        """Test per-layer aggregation with UQ."""
        result = (
            Q.nodes()
             .compute("degree")
             .per_layer()
             .aggregate(
                 avg_degree="mean(degree)",
                 node_count="count()"
             )
             .uq(method="perturbation", n_samples=8, seed=123)
             .execute(simple_network)
        )
        
        # Check that we have per-layer results
        assert len(result.items) == 2  # Two layers
        assert "avg_degree" in result.attributes
        assert "node_count" in result.attributes
        
        # Check uncertainty structure
        for item in result.items:
            avg_val = result.attributes["avg_degree"][item]
            assert isinstance(avg_val, dict)
            assert "mean" in avg_val
            assert "std" in avg_val


class TestRankingWithUQ:
    """Test order_by/limit with ranking stability."""
    
    def test_order_by_with_uq(self, simple_network):
        """Test ranking with UQ produces stability metrics."""
        result = (
            Q.nodes()
             .compute("degree")
             .order_by("-degree")
             .uq(method="perturbation", n_samples=10, seed=42)
             .execute(simple_network)
        )
        
        # Check that rank stability is computed
        assert "rank_stability" in result.meta
        
        rank_stab = result.meta["rank_stability"]
        assert "rank_means" in rank_stab
        assert "rank_stds" in rank_stab
        assert "kendall_tau_mean" in rank_stab
        assert rank_stab["n_samples"] == 10
    
    def test_limit_with_uq(self, simple_network):
        """Test that limit works with UQ."""
        result = (
            Q.nodes()
             .compute("degree")
             .order_by("-degree")
             .limit(3)
             .uq(method="perturbation", n_samples=5, seed=42)
             .execute(simple_network)
        )
        
        # Items should be aggregated across resamples
        assert len(result.items) > 0
        # Check for ranking attributes
        assert "rank_mean" in result.attributes or "present_prob" in result.attributes


class TestDeterminism:
    """Test that UQ execution is deterministic given a seed."""
    
    def test_same_seed_same_results(self, simple_network):
        """Test that same seed produces identical results."""
        query = (
            Q.nodes()
             .compute("degree")
             .summarize(mean_degree="mean(degree)")
             .uq(method="perturbation", n_samples=10, seed=42)
        )
        
        # Execute twice with same seed
        result1 = query.execute(simple_network)
        result2 = query.execute(simple_network)
        
        # Extract mean values
        val1 = result1.attributes["mean_degree"][result1.items[0]]
        val2 = result2.attributes["mean_degree"][result2.items[0]]
        
        # Should be identical (within floating point precision)
        assert abs(val1["mean"] - val2["mean"]) < 1e-10
        assert abs(val1["std"] - val2["std"]) < 1e-10


class TestBackwardCompatibility:
    """Test that non-UQ queries still work as before."""
    
    def test_aggregate_without_uq(self, simple_network):
        """Test that aggregate without UQ returns deterministic values."""
        result = (
            Q.nodes()
             .compute("degree")
             .summarize(mean_degree="mean(degree)")
             .execute(simple_network)
        )
        
        # Should not have UQ metadata
        assert "uq" not in result.meta or result.meta.get("uq", {}).get("type") != "compositional"
        
        # Value should be a scalar, not a dict
        val = result.attributes["mean_degree"][result.items[0]]
        assert isinstance(val, (int, float)) or (isinstance(val, dict) and "mean" not in val)
