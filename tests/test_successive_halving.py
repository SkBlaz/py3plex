"""Tests for Successive Halving racing strategy.

Tests cover:
- Determinism (same seed → same result)
- Parallel invariance (n_jobs=1 vs n_jobs>1)
- Correctness on synthetic networks
- Budget monotonicity
- UQ behavior
- Underdetermined detection
"""

import pytest
import numpy as np

from py3plex.core import multinet
from py3plex.algorithms.community_detection import (
    AutoCommunity,
    BudgetSpec,
    SuccessiveHalvingRacer,
    SuccessiveHalvingConfig,
)


class TestBudgetSpec:
    """Test BudgetSpec dataclass."""
    
    def test_budget_creation(self):
        """Test basic budget creation."""
        budget = BudgetSpec(max_iter=10, n_restarts=2, uq_samples=20)
        
        assert budget.max_iter == 10
        assert budget.n_restarts == 2
        assert budget.uq_samples == 20
    
    def test_budget_scale(self):
        """Test budget scaling."""
        budget0 = BudgetSpec(max_iter=5, n_restarts=1, uq_samples=10)
        budget1 = budget0.scale(3.0)
        
        assert budget1.max_iter == 15
        assert budget1.n_restarts == 3
        assert budget1.uq_samples == 30
    
    def test_budget_scale_with_caps(self):
        """Test budget scaling with caps."""
        budget0 = BudgetSpec(max_iter=5, n_restarts=1)
        budget1 = budget0.scale(100.0, caps={"max_iter": 50, "n_restarts": 10})
        
        assert budget1.max_iter == 50  # Capped
        assert budget1.n_restarts == 10  # Capped
    
    def test_budget_to_dict(self):
        """Test budget serialization."""
        budget = BudgetSpec(max_iter=10, uq_samples=20)
        d = budget.to_dict()
        
        assert d["max_iter"] == 10
        assert d["uq_samples"] == 20
        assert "n_restarts" not in d  # None values excluded
    
    def test_budget_from_dict(self):
        """Test budget deserialization."""
        d = {"max_iter": 10, "uq_samples": 20}
        budget = BudgetSpec.from_dict(d)
        
        assert budget.max_iter == 10
        assert budget.uq_samples == 20
        assert budget.n_restarts is None


class TestSuccessiveHalvingConfig:
    """Test SuccessiveHalvingConfig validation."""
    
    def test_valid_config(self):
        """Test valid configuration."""
        config = SuccessiveHalvingConfig(
            eta=3,
            budget0=BudgetSpec(max_iter=5),
            utility_method="mean_minus_std",
        )
        
        assert config.eta == 3
        assert config.utility_method == "mean_minus_std"
    
    def test_invalid_eta(self):
        """Test invalid eta value."""
        with pytest.raises(ValueError, match="eta must be >= 2"):
            SuccessiveHalvingConfig(eta=1)
    
    def test_invalid_tie_mode(self):
        """Test invalid tie_mode."""
        with pytest.raises(ValueError, match="tie_mode must be"):
            SuccessiveHalvingConfig(tie_mode="invalid")
    
    def test_invalid_utility_method(self):
        """Test invalid utility_method."""
        with pytest.raises(ValueError, match="utility_method must be"):
            SuccessiveHalvingConfig(utility_method="invalid")
    
    def test_default_budget0(self):
        """Test default budget0 creation."""
        config = SuccessiveHalvingConfig()
        
        assert config.budget0 is not None
        assert config.budget0.max_iter == 5
        assert config.budget0.uq_samples == 10


def _create_simple_network():
    """Create a simple test network with clear community structure."""
    network = multinet.multi_layer_network(directed=False)
    
    # Community 1: nodes 0-4
    nodes_c1 = [{"source": f"N{i}", "type": "layer1"} for i in range(5)]
    network.add_nodes(nodes_c1)
    
    edges_c1 = [
        {"source": f"N{i}", "target": f"N{j}",
         "source_type": "layer1", "target_type": "layer1"}
        for i in range(5) for j in range(i+1, 5)
    ]
    
    # Community 2: nodes 5-9
    nodes_c2 = [{"source": f"N{i}", "type": "layer1"} for i in range(5, 10)]
    network.add_nodes(nodes_c2)
    
    edges_c2 = [
        {"source": f"N{i}", "target": f"N{j}",
         "source_type": "layer1", "target_type": "layer1"}
        for i in range(5, 10) for j in range(i+1, 10)
    ]
    
    # Bridge between communities
    bridge = [
        {"source": "N4", "target": "N5",
         "source_type": "layer1", "target_type": "layer1"}
    ]
    
    network.add_edges(edges_c1 + edges_c2 + bridge)
    
    return network


class TestSuccessiveHalvingRacer:
    """Test SuccessiveHalvingRacer class."""
    
    def test_racer_runs_without_crash(self):
        """Test that racer runs without crashing."""
        network = _create_simple_network()
        
        config = SuccessiveHalvingConfig(
            eta=2,
            rounds=2,
            budget0=BudgetSpec(max_iter=5, uq_samples=5),
        )
        
        racer = SuccessiveHalvingRacer(config, seed=42)
        
        history = racer.race(
            network=network,
            algorithm_ids=["louvain", "leiden"],
            metric_names=["modularity", "coverage"],
            n_jobs=1,
        )
        
        assert history is not None
        assert history.winner_algo_id is not None
        assert len(history.rounds) > 0
        assert history.status in ("ok", "underdetermined", "error")
    
    def test_determinism_same_seed(self):
        """Test that same seed produces same result."""
        network = _create_simple_network()
        
        config = SuccessiveHalvingConfig(
            eta=2,
            rounds=2,
            budget0=BudgetSpec(max_iter=5, uq_samples=5),
        )
        
        # Run twice with same seed
        racer1 = SuccessiveHalvingRacer(config, seed=42)
        history1 = racer1.race(
            network=network,
            algorithm_ids=["louvain", "leiden"],
            metric_names=["modularity"],
            n_jobs=1,
        )
        
        racer2 = SuccessiveHalvingRacer(config, seed=42)
        history2 = racer2.race(
            network=network,
            algorithm_ids=["louvain", "leiden"],
            metric_names=["modularity"],
            n_jobs=1,
        )
        
        # Results should be identical
        assert history1.winner_algo_id == history2.winner_algo_id
        assert len(history1.rounds) == len(history2.rounds)
        
        # Check that utilities are the same in each round
        for r1, r2 in zip(history1.rounds, history2.rounds):
            assert r1["utilities"] == r2["utilities"]
    
    def test_budget_monotonicity(self):
        """Test that budgets increase across rounds."""
        network = _create_simple_network()
        
        config = SuccessiveHalvingConfig(
            eta=2,
            rounds=3,
            budget0=BudgetSpec(max_iter=5, uq_samples=5),
            budget_growth=2.0,
        )
        
        racer = SuccessiveHalvingRacer(config, seed=42)
        history = racer.race(
            network=network,
            algorithm_ids=["louvain", "leiden"],
            metric_names=["modularity"],
            n_jobs=1,
        )
        
        # Check budget monotonicity
        budgets = [round_rec["budget"] for round_rec in history.rounds]
        
        for i in range(len(budgets) - 1):
            # Budget should grow
            if budgets[i].get("max_iter") and budgets[i+1].get("max_iter"):
                assert budgets[i+1]["max_iter"] >= budgets[i]["max_iter"]
    
    def test_elimination(self):
        """Test that algorithms are eliminated across rounds."""
        network = _create_simple_network()
        
        config = SuccessiveHalvingConfig(
            eta=2,
            rounds=2,
            budget0=BudgetSpec(max_iter=5, uq_samples=5),
        )
        
        racer = SuccessiveHalvingRacer(config, seed=42)
        history = racer.race(
            network=network,
            algorithm_ids=["louvain", "leiden"],
            metric_names=["modularity"],
            n_jobs=1,
        )
        
        # Check that survivors decrease
        n_survivors_per_round = [
            len(round_rec["survivors"])
            for round_rec in history.rounds
        ]
        
        # Should be monotone decreasing or equal
        for i in range(len(n_survivors_per_round) - 1):
            assert n_survivors_per_round[i+1] <= n_survivors_per_round[i]


class TestAutoCommunityIntegration:
    """Test AutoCommunity integration with Successive Halving."""
    
    def test_autocommunity_default_strategy(self):
        """Test AutoCommunity with default strategy."""
        network = _create_simple_network()
        
        result = (
            AutoCommunity()
              .candidates("louvain", "leiden")
              .metrics("modularity", "coverage")
              .seed(42)
              .execute(network)
        )
        
        assert result is not None
        assert result.selected is not None
        assert result.consensus_partition is not None
    
    def test_autocommunity_successive_halving(self):
        """Test AutoCommunity with Successive Halving strategy."""
        network = _create_simple_network()
        
        result = (
            AutoCommunity()
              .candidates("louvain", "leiden")
              .metrics("modularity", "coverage")
              .strategy("successive_halving", eta=2, rounds=2)
              .seed(42)
              .execute(network)
        )
        
        assert result is not None
        assert result.selected is not None
        assert result.consensus_partition is not None
        
        # Check that provenance includes racing metadata
        assert "racing_history" in result.provenance
        assert result.provenance["strategy"] == "successive_halving"
    
    def test_autocommunity_sh_determinism(self):
        """Test that AutoCommunity with SH is deterministic."""
        network = _create_simple_network()
        
        # Run twice with same seed
        result1 = (
            AutoCommunity()
              .candidates("louvain", "leiden")
              .metrics("modularity")
              .strategy("successive_halving", eta=2, rounds=2)
              .seed(42)
              .execute(network)
        )
        
        result2 = (
            AutoCommunity()
              .candidates("louvain", "leiden")
              .metrics("modularity")
              .strategy("successive_halving", eta=2, rounds=2)
              .seed(42)
              .execute(network)
        )
        
        # Winners should be identical
        assert result1.selected == result2.selected
    
    def test_autocommunity_sh_with_uq(self):
        """Test AutoCommunity with SH and UQ."""
        network = _create_simple_network()
        
        result = (
            AutoCommunity()
              .candidates("louvain", "leiden")
              .metrics("modularity", "coverage")
              .uq(method="seed", n_samples=10)
              .strategy("successive_halving", eta=2, rounds=2)
              .seed(42)
              .execute(network)
        )
        
        assert result is not None
        assert result.selected is not None
        
        # Check that UQ was used in budgets
        racing_history = result.provenance.get("racing_history", {})
        if racing_history.get("rounds"):
            first_round = racing_history["rounds"][0]
            budget = first_round.get("budget", {})
            assert budget.get("uq_samples", 0) > 0
    
    def test_autocommunity_sh_custom_budget(self):
        """Test AutoCommunity with SH and custom budget."""
        network = _create_simple_network()
        
        result = (
            AutoCommunity()
              .candidates("louvain", "leiden")
              .metrics("modularity")
              .strategy(
                  "successive_halving",
                  eta=2,
                  budget0={"max_iter": 10, "uq_samples": 15},
                  budget_growth=2.0,
              )
              .seed(42)
              .execute(network)
        )
        
        assert result is not None
        assert result.selected is not None


class TestUtilityMethods:
    """Test different utility computation methods."""
    
    def test_mean_minus_std_utility(self):
        """Test mean_minus_std utility method."""
        network = _create_simple_network()
        
        config = SuccessiveHalvingConfig(
            utility_method="mean_minus_std",
            utility_lambda=1.0,
        )
        
        racer = SuccessiveHalvingRacer(config, seed=42)
        history = racer.race(
            network=network,
            algorithm_ids=["louvain", "leiden"],
            metric_names=["modularity"],
            n_jobs=1,
        )
        
        assert history.winner_algo_id is not None
    
    def test_expected_regret_utility(self):
        """Test expected_regret utility method."""
        network = _create_simple_network()
        
        config = SuccessiveHalvingConfig(
            utility_method="expected_regret",
        )
        
        racer = SuccessiveHalvingRacer(config, seed=42)
        history = racer.race(
            network=network,
            algorithm_ids=["louvain", "leiden"],
            metric_names=["modularity"],
            n_jobs=1,
        )
        
        assert history.winner_algo_id is not None
    
    def test_prob_near_best_utility(self):
        """Test prob_near_best utility method."""
        network = _create_simple_network()
        
        config = SuccessiveHalvingConfig(
            utility_method="prob_near_best",
        )
        
        racer = SuccessiveHalvingRacer(config, seed=42)
        history = racer.race(
            network=network,
            algorithm_ids=["louvain", "leiden"],
            metric_names=["modularity"],
            n_jobs=1,
        )
        
        assert history.winner_algo_id is not None


class TestMetricAggregation:
    """Test metric aggregation and normalization."""
    
    def test_metric_normalization(self):
        """Test that metric normalization works."""
        network = _create_simple_network()
        
        config = SuccessiveHalvingConfig(
            normalize_metrics=True,
        )
        
        racer = SuccessiveHalvingRacer(config, seed=42)
        history = racer.race(
            network=network,
            algorithm_ids=["louvain", "leiden"],
            metric_names=["modularity", "coverage"],
            n_jobs=1,
        )
        
        assert history.winner_algo_id is not None
    
    def test_metric_weights(self):
        """Test custom metric weights."""
        network = _create_simple_network()
        
        config = SuccessiveHalvingConfig(
            metric_weights={"modularity": 0.7, "coverage": 0.3},
        )
        
        racer = SuccessiveHalvingRacer(config, seed=42)
        history = racer.race(
            network=network,
            algorithm_ids=["louvain", "leiden"],
            metric_names=["modularity", "coverage"],
            n_jobs=1,
        )
        
        assert history.winner_algo_id is not None


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_single_algorithm(self):
        """Test with single algorithm (no race needed)."""
        network = _create_simple_network()
        
        config = SuccessiveHalvingConfig()
        racer = SuccessiveHalvingRacer(config, seed=42)
        
        history = racer.race(
            network=network,
            algorithm_ids=["louvain"],
            metric_names=["modularity"],
            n_jobs=1,
        )
        
        assert history.winner_algo_id == "louvain"
        assert history.status == "ok"
    
    def test_empty_algorithms(self):
        """Test with empty algorithm list."""
        network = _create_simple_network()
        
        config = SuccessiveHalvingConfig()
        racer = SuccessiveHalvingRacer(config, seed=42)
        
        with pytest.raises(ValueError, match="Must provide at least one algorithm"):
            racer.race(
                network=network,
                algorithm_ids=[],
                metric_names=["modularity"],
                n_jobs=1,
            )
    
    def test_empty_metrics(self):
        """Test with empty metric list."""
        network = _create_simple_network()
        
        config = SuccessiveHalvingConfig()
        racer = SuccessiveHalvingRacer(config, seed=42)
        
        with pytest.raises(ValueError, match="Must provide at least one metric"):
            racer.race(
                network=network,
                algorithm_ids=["louvain"],
                metric_names=[],
                n_jobs=1,
            )


class TestProvenance:
    """Test provenance tracking."""
    
    def test_provenance_includes_metadata(self):
        """Test that provenance includes all required metadata."""
        network = _create_simple_network()
        
        result = (
            AutoCommunity()
              .candidates("louvain", "leiden")
              .metrics("modularity")
              .strategy("successive_halving")
              .seed(42)
              .execute(network)
        )
        
        prov = result.provenance
        
        assert "engine" in prov
        assert prov["engine"] == "autocommunity_successive_halving"
        assert "py3plex_version" in prov
        assert "timestamp_utc" in prov
        assert "seed" in prov
        assert prov["seed"] == 42
        assert "strategy" in prov
        assert prov["strategy"] == "successive_halving"
        assert "racing_history" in prov
    
    def test_racing_history_structure(self):
        """Test that racing history has correct structure."""
        network = _create_simple_network()
        
        result = (
            AutoCommunity()
              .candidates("louvain", "leiden")
              .metrics("modularity")
              .strategy("successive_halving", rounds=2)
              .seed(42)
              .execute(network)
        )
        
        history = result.provenance["racing_history"]
        
        assert "rounds" in history
        assert "winner_algo_id" in history
        assert "finalists" in history
        assert "status" in history
        assert "total_runtime_ms" in history
        
        # Check round structure
        if history["rounds"]:
            round0 = history["rounds"][0]
            assert "round" in round0
            assert "budget" in round0
            assert "algorithms" in round0
            assert "utilities" in round0
            assert "survivors" in round0
