"""Tests for AutoCommunity selection.

Tests cover:
- Capabilities scanner
- Selection logic (most wins)
- Bucket caps
- Tie-breaker rules
- DSL integration
- Functional API
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch

from py3plex.core import multinet
from py3plex.selection.capabilities import CapabilitiesScanner, scan_capabilities
from py3plex.selection.result import AutoCommunityResult, ContestantResult
from py3plex.selection.metric_registry import MetricRegistry, MetricSpec
from py3plex.selection.community_registry import CommunityRegistry, CandidateSpec
from py3plex.selection.wins import compute_pairwise_wins, select_winner
from py3plex.selection.evaluate import _derive_contestant_seed


class TestCapabilitiesScanner:
    """Test capabilities detection."""
    
    def test_scanner_runs_without_crash(self):
        """Scanner should run without crashing."""
        scanner = CapabilitiesScanner()
        report = scanner.scan()
        
        assert report is not None
        assert isinstance(report.algorithms_found, dict)
        assert isinstance(report.metrics_found, dict)
        assert isinstance(report.uq_available, bool)
    
    def test_scanner_finds_algorithms(self):
        """Scanner should find at least one algorithm."""
        report = scan_capabilities()
        
        # Should find at least one multilayer algorithm
        assert len(report.algorithms_found) > 0
        
        # Check that at least one algorithm supports multilayer
        multilayer_algos = [
            a for a in report.algorithms_found.values()
            if a.supports_multilayer
        ]
        assert len(multilayer_algos) > 0
    
    def test_scanner_stable_output(self):
        """Scanner should produce consistent output."""
        report1 = scan_capabilities()
        report2 = scan_capabilities()
        
        # Same algorithms detected
        assert set(report1.algorithms_found.keys()) == set(report2.algorithms_found.keys())
        assert report1.uq_available == report2.uq_available


class TestMostWinsLogic:
    """Test most-wins decision engine."""
    
    def test_simple_winner(self):
        """Test simple case where one contestant dominates."""
        # Create mock contestants
        contestants = [
            ContestantResult(
                contestant_id="A",
                algo_name="algo_a",
                params={},
                partition={},
                metrics={"metric1": 10.0, "metric2": 20.0},
                runtime_ms=100.0,
            ),
            ContestantResult(
                contestant_id="B",
                algo_name="algo_b",
                params={},
                partition={},
                metrics={"metric1": 5.0, "metric2": 15.0},
                runtime_ms=200.0,
            ),
        ]
        
        # Create metrics (both max direction)
        metrics = [
            MetricSpec(
                name="metric1",
                callable=lambda p, n, c: p,
                direction="max",
                bucket="objective",
            ),
            MetricSpec(
                name="metric2",
                callable=lambda p, n, c: p,
                direction="max",
                bucket="structure",
            ),
        ]
        
        total_wins, wins_by_bucket, leaderboard = compute_pairwise_wins(
            contestants=contestants,
            metrics=metrics,
        )
        
        # A should win both metrics (1 pairwise comparison each)
        assert total_wins["A"] == 2.0
        assert total_wins["B"] == 0.0
        
        winner = select_winner(contestants, total_wins, wins_by_bucket)
        assert winner.contestant_id == "A"
    
    def test_tie_handling(self):
        """Test tie handling (0.5 points each)."""
        contestants = [
            ContestantResult(
                contestant_id="A",
                algo_name="algo_a",
                params={},
                partition={},
                metrics={"metric1": 10.0},
                runtime_ms=100.0,
            ),
            ContestantResult(
                contestant_id="B",
                algo_name="algo_b",
                params={},
                partition={},
                metrics={"metric1": 10.0},  # Same value = tie
                runtime_ms=200.0,
            ),
        ]
        
        metrics = [
            MetricSpec(
                name="metric1",
                callable=lambda p, n, c: p,
                direction="max",
                bucket="objective",
            ),
        ]
        
        total_wins, wins_by_bucket, leaderboard = compute_pairwise_wins(
            contestants=contestants,
            metrics=metrics,
        )
        
        # Each should get 0.5 for the tie
        assert total_wins["A"] == 0.5
        assert total_wins["B"] == 0.5
    
    def test_min_direction(self):
        """Test metrics with min direction."""
        contestants = [
            ContestantResult(
                contestant_id="A",
                algo_name="algo_a",
                params={},
                partition={},
                metrics={"metric1": 5.0},  # Lower is better
                runtime_ms=100.0,
            ),
            ContestantResult(
                contestant_id="B",
                algo_name="algo_b",
                params={},
                partition={},
                metrics={"metric1": 10.0},
                runtime_ms=200.0,
            ),
        ]
        
        metrics = [
            MetricSpec(
                name="metric1",
                callable=lambda p, n, c: p,
                direction="min",
                bucket="runtime",
            ),
        ]
        
        total_wins, wins_by_bucket, leaderboard = compute_pairwise_wins(
            contestants=contestants,
            metrics=metrics,
        )
        
        # A should win (lower value)
        assert total_wins["A"] == 1.0
        assert total_wins["B"] == 0.0


class TestBucketCaps:
    """Test bucket capping logic."""
    
    def test_bucket_caps_applied(self):
        """Test that bucket caps prevent domination."""
        # Create contestants where one would win many times in one bucket
        contestants = [
            ContestantResult(
                contestant_id="A",
                algo_name="algo_a",
                params={},
                partition={},
                metrics={f"metric{i}": 10.0 for i in range(10)},  # Wins 10 metrics
                runtime_ms=100.0,
            ),
            ContestantResult(
                contestant_id="B",
                algo_name="algo_b",
                params={},
                partition={},
                metrics={f"metric{i}": 5.0 for i in range(10)},
                runtime_ms=200.0,
            ),
        ]
        
        # All metrics in same bucket (objective)
        metrics = [
            MetricSpec(
                name=f"metric{i}",
                callable=lambda p, n, c: p,
                direction="max",
                bucket="objective",
            )
            for i in range(10)
        ]
        
        # Set cap to 5
        bucket_caps = {"objective": 5.0, "structure": 30, "sanity": 30, "stability": 30, "runtime": 10, "predictive": 30}
        
        total_wins, wins_by_bucket, leaderboard = compute_pairwise_wins(
            contestants=contestants,
            metrics=metrics,
            bucket_caps=bucket_caps,
        )
        
        # A should win 10 pairwise comparisons, but capped at 5
        assert wins_by_bucket["A"]["objective"] == 5.0
        assert total_wins["A"] == 5.0


class TestTieBreakers:
    """Test deterministic tie-breaking."""
    
    def test_tie_breaker_by_runtime(self):
        """When wins are tied, lower runtime wins."""
        contestants = [
            ContestantResult(
                contestant_id="A",
                algo_name="algo_a",
                params={},
                partition={},
                metrics={},
                runtime_ms=200.0,  # Slower
            ),
            ContestantResult(
                contestant_id="B",
                algo_name="algo_b",
                params={},
                partition={},
                metrics={},
                runtime_ms=100.0,  # Faster
            ),
        ]
        
        total_wins = {"A": 5.0, "B": 5.0}  # Tied
        wins_by_bucket = {
            "A": {"objective": 5.0, "structure": 0, "sanity": 0, "stability": 0, "runtime": 0, "predictive": 0},
            "B": {"objective": 5.0, "structure": 0, "sanity": 0, "stability": 0, "runtime": 0, "predictive": 0},
        }
        
        winner = select_winner(contestants, total_wins, wins_by_bucket)
        assert winner.contestant_id == "B"  # Faster runtime
    
    def test_tie_breaker_by_id(self):
        """When everything is tied, use contestant_id."""
        contestants = [
            ContestantResult(
                contestant_id="Z",
                algo_name="algo_a",
                params={},
                partition={},
                metrics={},
                runtime_ms=100.0,
            ),
            ContestantResult(
                contestant_id="A",
                algo_name="algo_b",
                params={},
                partition={},
                metrics={},
                runtime_ms=100.0,
            ),
        ]
        
        total_wins = {"Z": 0.0, "A": 0.0}
        wins_by_bucket = {
            "Z": {"objective": 0, "structure": 0, "sanity": 0, "stability": 0, "runtime": 0, "predictive": 0},
            "A": {"objective": 0, "structure": 0, "sanity": 0, "stability": 0, "runtime": 0, "predictive": 0},
        }
        
        winner = select_winner(contestants, total_wins, wins_by_bucket)
        assert winner.contestant_id == "A"  # Lexicographically first


class TestSeedDeterminism:
    """Test deterministic seed derivation."""
    
    def test_seed_derivation_deterministic(self):
        """Derived seeds should be deterministic."""
        seed1 = _derive_contestant_seed(42, "contestant_a")
        seed2 = _derive_contestant_seed(42, "contestant_a")
        
        assert seed1 == seed2
    
    def test_seed_derivation_different_contestants(self):
        """Different contestants get different seeds."""
        seed1 = _derive_contestant_seed(42, "contestant_a")
        seed2 = _derive_contestant_seed(42, "contestant_b")
        
        assert seed1 != seed2
    
    def test_seed_derivation_different_masters(self):
        """Different master seeds give different derived seeds."""
        seed1 = _derive_contestant_seed(42, "contestant_a")
        seed2 = _derive_contestant_seed(99, "contestant_a")
        
        assert seed1 != seed2


class TestMetricRegistry:
    """Test metric registry."""
    
    def test_registry_has_defaults(self):
        """Registry should have default metrics."""
        registry = MetricRegistry()
        
        assert len(registry.metrics) > 0
        
        # Should have metrics in different buckets
        buckets = {m.bucket for m in registry.metrics.values()}
        assert "objective" in buckets or "structure" in buckets
    
    def test_get_default_metrics(self):
        """Get default metrics should work."""
        registry = MetricRegistry()
        
        defaults = registry.get_default_metrics(uq_enabled=False)
        assert len(defaults) > 0
        
        # Should not include UQ metrics when disabled
        for metric in defaults:
            assert not metric.requires_uq
    
    def test_get_default_metrics_with_uq(self):
        """Get default metrics should include UQ metrics when enabled."""
        registry = MetricRegistry()
        
        defaults_without_uq = registry.get_default_metrics(uq_enabled=False)
        defaults_with_uq = registry.get_default_metrics(uq_enabled=True)
        
        # With UQ should have at least as many (or more if UQ metrics exist)
        assert len(defaults_with_uq) >= len(defaults_without_uq)


class TestCommunityRegistry:
    """Test community registry."""
    
    def test_registry_builds_candidates(self):
        """Registry should build candidates from capabilities."""
        from py3plex.selection.capabilities import AlgorithmInfo, CapabilitiesReport
        
        # Create mock capabilities
        capabilities = CapabilitiesReport(
            algorithms_found={
                "leiden": AlgorithmInfo(
                    name="leiden",
                    callable=lambda: None,
                    module_path="test",
                    supports_multilayer=True,
                    params=["network", "gamma"],
                    accepts_seed=True,
                    seed_param_name="random_state",
                )
            },
            metrics_found={},
            uq_available=False,
        )
        
        registry = CommunityRegistry(capabilities)
        candidates = registry.build_candidate_set(is_multilayer=True, fast_mode=True)
        
        assert len(candidates) > 0
        assert all(isinstance(c, CandidateSpec) for c in candidates)


class TestFunctionalAPI:
    """Test functional API (auto_select_community)."""
    
    @pytest.mark.slow
    def test_auto_select_runs(self):
        """Auto-select should run on a simple network."""
        # Create simple network
        network = multinet.multi_layer_network(directed=False)
        
        nodes = [
            {"source": "A", "type": "layer1"},
            {"source": "B", "type": "layer1"},
            {"source": "C", "type": "layer1"},
            {"source": "D", "type": "layer1"},
        ]
        network.add_nodes(nodes)
        
        edges = [
            {"source": "A", "target": "B", "source_type": "layer1", "target_type": "layer1"},
            {"source": "B", "target": "C", "source_type": "layer1", "target_type": "layer1"},
            {"source": "C", "target": "D", "source_type": "layer1", "target_type": "layer1"},
        ]
        network.add_edges(edges)
        
        # Run auto-select
        from py3plex.algorithms.community_detection import auto_select_community
        
        result = auto_select_community(network, fast=True, max_candidates=2, seed=42)
        
        assert isinstance(result, AutoCommunityResult)
        assert result.partition is not None
        assert len(result.partition) > 0
        assert result.leaderboard is not None
        assert len(result.leaderboard) > 0
    
    @pytest.mark.slow
    def test_auto_select_deterministic(self):
        """Auto-select should be deterministic with same seed."""
        network = multinet.multi_layer_network(directed=False)
        
        nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(10)]
        network.add_nodes(nodes)
        
        edges = [
            {"source": f"N{i}", "target": f"N{i+1}", "source_type": "layer1", "target_type": "layer1"}
            for i in range(9)
        ]
        network.add_edges(edges)
        
        from py3plex.algorithms.community_detection import auto_select_community
        
        result1 = auto_select_community(network, fast=True, max_candidates=2, seed=42)
        result2 = auto_select_community(network, fast=True, max_candidates=2, seed=42)
        
        # Same winner
        assert result1.algorithm["name"] == result2.algorithm["name"]
        assert result1.algorithm["contestant_id"] == result2.algorithm["contestant_id"]


class TestDSLIntegration:
    """Test DSL integration."""
    
    def test_dsl_auto_select_exists(self):
        """Q.community().auto_select() should exist."""
        from py3plex.dsl import Q
        
        builder = Q.communities().auto_select()
        
        assert builder is not None
        assert hasattr(builder._select, "auto_select_config")
        assert builder._select.auto_select_config["enabled"] is True
    
    @pytest.mark.slow
    def test_dsl_auto_select_executes(self):
        """Q.community().auto_select().execute() should work."""
        from py3plex.dsl import Q
        
        # Create simple network
        network = multinet.multi_layer_network(directed=False)
        
        nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(6)]
        network.add_nodes(nodes)
        
        edges = [
            {"source": "N0", "target": "N1", "source_type": "layer1", "target_type": "layer1"},
            {"source": "N1", "target": "N2", "source_type": "layer1", "target_type": "layer1"},
            {"source": "N3", "target": "N4", "source_type": "layer1", "target_type": "layer1"},
            {"source": "N4", "target": "N5", "source_type": "layer1", "target_type": "layer1"},
        ]
        network.add_edges(edges)
        
        result = Q.communities().auto_select(fast=True, max_candidates=2, seed=42).execute(network)
        
        assert isinstance(result, AutoCommunityResult)
        assert result.partition is not None


class TestAutoResult:
    """Test AutoCommunityResult."""
    
    def test_explain_method(self):
        """Test explain() method."""
        contestant = ContestantResult(
            contestant_id="leiden:default",  # Use algorithm name in ID
            algo_name="leiden",
            params={"gamma": 1.0},
            partition={},
            metrics={"modularity": 0.5},
            runtime_ms=100.0,
        )
        
        result = AutoCommunityResult(
            chosen=contestant,
            partition={},
            algorithm={"name": "leiden", "params": {}},
            leaderboard=pd.DataFrame(),
            report={},
            provenance={"wins_by_bucket": {"objective": 10, "structure": 5}},
        )
        
        explanation = result.explain()
        
        assert isinstance(explanation, str)
        assert len(explanation) > 0
        assert "leiden" in explanation.lower()
    
    def test_to_dict(self):
        """Test to_dict() serialization."""
        contestant = ContestantResult(
            contestant_id="test",
            algo_name="leiden",
            params={},
            partition={("A", "layer1"): 0},
            metrics={},
            runtime_ms=100.0,
        )
        
        result = AutoCommunityResult(
            chosen=contestant,
            partition={("A", "layer1"): 0},
            algorithm={"name": "leiden"},
            leaderboard=pd.DataFrame([{"rank": 1, "algorithm": "leiden"}]),
            report={},
            provenance={},
        )
        
        d = result.to_dict()
        
        assert isinstance(d, dict)
        assert "algorithm" in d
        assert "partition" in d
        assert "leaderboard" in d


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
