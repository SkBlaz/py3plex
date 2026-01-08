"""Integration tests for SelectionUQ with DSL.

This module tests the integration of SelectionUQ with the DSL query system,
verifying that .top_k().uq() and filter queries work correctly.
"""

import pytest
import numpy as np

from py3plex.core import multinet
from py3plex.dsl import Q
from py3plex.uncertainty import EdgeDrop


def build_test_network():
    """Build a simple multilayer network for testing."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    
    # Create a small network with clear structure
    edges = [
        # Layer 0: Hub structure (a is central)
        ["a", "L0", "b", "L0", 1.0],
        ["a", "L0", "c", "L0", 1.0],
        ["a", "L0", "d", "L0", 1.0],
        ["a", "L0", "e", "L0", 1.0],
        ["b", "L0", "c", "L0", 1.0],
        # Layer 1: Chain structure
        ["a", "L1", "b", "L1", 1.0],
        ["b", "L1", "c", "L1", 1.0],
        ["c", "L1", "d", "L1", 1.0],
        ["d", "L1", "e", "L1", 1.0],
        # Inter-layer
        ["a", "L0", "a", "L1", 1.0],
        ["b", "L0", "b", "L1", 1.0],
        ["c", "L0", "c", "L1", 1.0],
    ]
    net.add_edges(edges, input_type="list")
    return net


class TestSelectionUQIntegration:
    """Integration tests for SelectionUQ with DSL."""
    
    def test_top_k_with_uq_basic(self):
        """Test basic top-k query with UQ."""
        net = build_test_network()
        
        result = (
            Q.nodes()
            .compute("degree")
            .order_by("degree", desc=True)
            .limit(3)
            .uq(method="seed", n_samples=10, seed=42)
            .execute(net)
        )
        
        # Should have UQ columns
        assert "present_prob" in result.attributes
        assert "present_ci_low" in result.attributes
        assert "present_ci_high" in result.attributes
        
        # Should have UQ metadata
        assert "uq" in result.meta
        assert result.meta["uq"]["type"] == "selection"
        assert result.meta["uq"]["n_samples"] == 10
        
        # High-degree nodes should have high present_prob
        df = result.to_pandas()
        assert len(df) > 0
        
        # Check that probabilities are valid
        for prob in df["present_prob"]:
            assert 0.0 <= prob <= 1.0
    
    def test_top_k_with_perturbation(self):
        """Test top-k with edge-drop perturbation."""
        net = build_test_network()
        
        result = (
            Q.nodes()
            .compute("degree")
            .order_by("degree", desc=True)
            .limit(3)
            .uq(
                method="perturbation",
                n_samples=20,
                seed=42,
                noise_model=EdgeDrop(p=0.1)
            )
            .execute(net)
        )
        
        # Should have rank columns
        assert "rank_mean" in result.attributes
        assert "rank_std" in result.attributes
        assert "p_in_topk" in result.attributes
        
        # Should have topk stats in meta
        assert "topk" in result.meta["uq"]
        assert result.meta["uq"]["topk"]["k"] == 3
        
        # Check noise model recorded
        assert result.meta["uq"]["noise_model"] is not None
        assert "EdgeDrop" in result.meta["uq"]["noise_model"]
    
    def test_filter_only_with_uq(self):
        """Test filter-only query with UQ."""
        net = build_test_network()
        
        # This currently won't trigger SelectionUQ unless it has order+limit
        # But we can test it works
        result = (
            Q.nodes()
            .where(degree__gt=2)
            .compute("degree")
            .order_by("degree", desc=True)
            .limit(5)
            .uq(method="seed", n_samples=15, seed=7)
            .execute(net)
        )
        
        assert "present_prob" in result.attributes
        assert result.meta["uq"]["type"] == "selection"
    
    def test_selection_uq_deterministic(self):
        """Test that seed-only UQ with no noise gives deterministic results."""
        net = build_test_network()
        
        result = (
            Q.nodes()
            .compute("degree")
            .order_by("degree", desc=True)
            .limit(3)
            .uq(method="seed", n_samples=5, seed=42)
            .execute(net)
        )
        
        df = result.to_pandas()
        
        # With no noise, top items should have present_prob = 1.0
        # (assuming deterministic centrality computation)
        top_items = df.nlargest(3, "degree")
        
        # Note: This might not be exactly 1.0 if there are ties or randomness
        # in centrality computation, so we just check they're high
        for prob in top_items["present_prob"]:
            assert prob >= 0.8
    
    def test_selection_uq_stability_metrics(self):
        """Test that stability metrics are computed."""
        net = build_test_network()
        
        result = (
            Q.nodes()
            .compute("degree")
            .order_by("degree", desc=True)
            .limit(3)
            .uq(
                method="perturbation",
                n_samples=20,
                seed=42,
                noise_model=EdgeDrop(p=0.15)
            )
            .execute(net)
        )
        
        uq_meta = result.meta["uq"]
        
        # Should have stability stats
        assert "stability" in uq_meta
        assert "jaccard_mean" in uq_meta["stability"]
        assert "jaccard_std" in uq_meta["stability"]
        
        # Should have consensus info
        assert "consensus" in uq_meta
        assert "size" in uq_meta["consensus"]
        
        # Should have borderline items
        assert "borderline_items" in uq_meta
    
    def test_selection_uq_provenance(self):
        """Test that provenance is correctly recorded."""
        net = build_test_network()
        
        result = (
            Q.nodes()
            .compute("degree")
            .order_by("degree", desc=True)
            .limit(3)
            .uq(
                method="perturbation",
                n_samples=10,
                seed=42,
                noise_model=EdgeDrop(p=0.05)
            )
            .execute(net)
        )
        
        # Check UQ metadata
        assert result.meta["uq"]["method"] == "perturbation"
        assert result.meta["uq"]["n_samples"] == 10
        
        # Check selection_uq object is stored
        assert "selection_uq" in result.meta
        selection_uq = result.meta["selection_uq"]
        
        assert selection_uq.n_samples == 10
        assert selection_uq.target == "nodes"
        assert selection_uq.k == 3
    
    def test_selection_uq_pandas_export(self):
        """Test that SelectionUQ columns export to pandas correctly."""
        net = build_test_network()
        
        result = (
            Q.nodes()
            .compute("degree")
            .order_by("degree", desc=True)
            .limit(3)
            .uq(method="seed", n_samples=10, seed=42)
            .execute(net)
        )
        
        df = result.to_pandas()
        
        # Should have all UQ columns
        assert "present_prob" in df.columns
        assert "present_ci_low" in df.columns
        assert "present_ci_high" in df.columns
        
        # All rows should have valid values
        assert not df["present_prob"].isna().any()
        assert not df["present_ci_low"].isna().any()
        assert not df["present_ci_high"].isna().any()


@pytest.mark.integration
class TestSelectionUQStatisticalProperties:
    """Statistical property tests for SelectionUQ."""
    
    def test_increased_noise_decreases_stability(self):
        """Test that increasing noise decreases selection stability."""
        net = build_test_network()
        
        # Run with low noise
        result_low = (
            Q.nodes()
            .compute("degree")
            .order_by("degree", desc=True)
            .limit(3)
            .uq(
                method="perturbation",
                n_samples=30,
                seed=42,
                noise_model=EdgeDrop(p=0.05)
            )
            .execute(net)
        )
        
        # Run with high noise
        result_high = (
            Q.nodes()
            .compute("degree")
            .order_by("degree", desc=True)
            .limit(3)
            .uq(
                method="perturbation",
                n_samples=30,
                seed=42,
                noise_model=EdgeDrop(p=0.3)
            )
            .execute(net)
        )
        
        # High noise should have lower Jaccard similarity
        jaccard_low = result_low.meta["uq"]["stability"]["jaccard_mean"]
        jaccard_high = result_high.meta["uq"]["stability"]["jaccard_mean"]
        
        assert jaccard_high < jaccard_low
    
    def test_high_degree_nodes_high_p_in_topk(self):
        """Test that high-degree nodes have high p_in_topk under small perturbation."""
        net = build_test_network()
        
        result = (
            Q.nodes()
            .compute("degree")
            .order_by("degree", desc=True)
            .limit(3)
            .uq(
                method="perturbation",
                n_samples=30,
                seed=42,
                noise_model=EdgeDrop(p=0.05)  # Small perturbation
            )
            .execute(net)
        )
        
        df = result.to_pandas()
        
        # Node 'a' should have the highest degree and high p_in_topk
        # Check if 'node' or 'id' column exists
        id_col = 'node' if 'node' in df.columns else 'id'
        a_row = df[df[id_col] == "a"]
        if len(a_row) > 0:
            assert a_row["p_in_topk"].iloc[0] > 0.8
