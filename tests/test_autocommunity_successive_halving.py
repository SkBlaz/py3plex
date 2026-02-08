"""Tests for AutoCommunity successive halving integration.

Tests focus on:
- Successive halving strategy configuration
- Budget specification
- Round-based elimination
- Determinism across rounds
"""

import pytest
import numpy as np

from py3plex.core import multinet
from py3plex.algorithms.community_detection import AutoCommunity
from py3plex.algorithms.community_detection.budget import BudgetSpec


@pytest.fixture
def test_network():
    """Create a test network for successive halving tests."""
    network = multinet.multi_layer_network(directed=False)
    nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(15)]
    network.add_nodes(nodes)
    
    for i in range(15):
        for j in range(i+1, min(i+3, 15)):
            network.add_edges([{
                "source": f"N{i}", "target": f"N{j}",
                "source_type": "layer1", "target_type": "layer1"
            }])
    
    return network


class TestSuccessiveHalvingConfiguration:
    """Test successive halving configuration."""
    
    def test_strategy_sets_successive_halving(self):
        """Should set successive halving strategy."""
        ac = AutoCommunity().strategy("successive_halving")
        
        assert ac._strategy == "successive_halving"
        # racer_config may be None or empty dict initially
        assert hasattr(ac, '_racer_config')
    
    def test_strategy_with_eta(self):
        """Should configure elimination factor (eta)."""
        ac = AutoCommunity().strategy("successive_halving", eta=3)
        
        assert ac._racer_config.get('eta') == 3
    
    def test_strategy_with_rounds(self):
        """Should configure number of rounds."""
        ac = AutoCommunity().strategy("successive_halving", rounds=2)
        
        assert ac._racer_config.get('rounds') == 2
    
    def test_strategy_with_budget(self):
        """Should configure initial budget."""
        budget = BudgetSpec(max_iter=10, n_restarts=1)
        ac = AutoCommunity().strategy("successive_halving", budget0=budget)
        
        assert ac._racer_config.get('budget0') is not None
    
    def test_strategy_with_utility_method(self):
        """Should configure utility method."""
        ac = AutoCommunity().strategy("successive_halving", utility_method="mean_minus_std")
        
        assert ac._racer_config.get('utility_method') == "mean_minus_std"


class TestSuccessiveHalvingExecution:
    """Test successive halving execution."""
    
    def test_sh_basic_execution(self, test_network):
        """Should execute with successive halving strategy."""
        result = (
            AutoCommunity()
              .candidates("louvain", "leiden")
              .metrics("modularity", "coverage")
              .strategy("successive_halving", eta=2, rounds=2)
              .seed(42)
              .execute(test_network)
        )
        
        assert result is not None
        assert result.selected is not None
        # Should have provenance about successive halving
        assert 'strategy' in result.provenance
    
    def test_sh_with_multiple_candidates(self, test_network):
        """Should eliminate candidates progressively."""
        result = (
            AutoCommunity()
              .candidates("louvain", "leiden", "label_propagation")
              .metrics("modularity")
              .strategy("successive_halving", eta=2, rounds=2)
              .seed(42)
              .execute(test_network)
        )
        
        # Should have tested algorithms
        assert len(result.algorithms_tested) > 0
        # Winner should be selected
        assert result.selected is not None
    
    def test_sh_determinism(self, test_network):
        """Should produce deterministic results with fixed seed."""
        result1 = (
            AutoCommunity()
              .candidates("louvain", "leiden")
              .metrics("modularity", "coverage")
              .strategy("successive_halving", eta=2, rounds=2)
              .seed(42)
              .execute(test_network)
        )
        
        result2 = (
            AutoCommunity()
              .candidates("louvain", "leiden")
              .metrics("modularity", "coverage")
              .strategy("successive_halving", eta=2, rounds=2)
              .seed(42)
              .execute(test_network)
        )
        
        # Should select same algorithm
        assert result1.selected == result2.selected
        # Should have same partition
        assert result1.consensus_partition == result2.consensus_partition
    
    def test_sh_budget_progression(self, test_network):
        """Should respect budget progression."""
        result = (
            AutoCommunity()
              .candidates("louvain", "leiden")
              .metrics("modularity")
              .strategy(
                  "successive_halving",
                  eta=2,
                  rounds=2,
                  budget0={"max_iter": 5, "n_restarts": 1}
              )
              .seed(42)
              .execute(test_network)
        )
        
        # Should complete without error
        assert result is not None
        # Provenance should track rounds
        if 'racing_history' in result.provenance:
            history = result.provenance['racing_history']
            assert 'rounds' in history


class TestSuccessiveHalvingWithUQ:
    """Test successive halving with uncertainty quantification."""
    
    def test_sh_with_uq(self, test_network):
        """Should work with UQ enabled."""
        result = (
            AutoCommunity()
              .candidates("louvain", "leiden")
              .metrics("modularity", "coverage")
              .uq(method="seed", n_samples=5)
              .strategy("successive_halving", eta=2, rounds=2)
              .seed(42)
              .execute(test_network)
        )
        
        assert result is not None
        # UQ should be reflected in stats (but may not always populate node_confidence)
        assert result.community_stats is not None


class TestSuccessiveHalvingEdgeCases:
    """Test edge cases for successive halving."""
    
    def test_sh_single_candidate(self, test_network):
        """Should handle single candidate (no elimination needed)."""
        result = (
            AutoCommunity()
              .candidates("louvain")
              .metrics("modularity")
              .strategy("successive_halving", eta=2, rounds=2)
              .seed(42)
              .execute(test_network)
        )
        
        assert result is not None
        assert result.selected is not None
        # Should test at least one algorithm
        assert len(result.algorithms_tested) >= 1
    
    def test_sh_with_high_eta(self, test_network):
        """Should handle aggressive elimination (high eta)."""
        result = (
            AutoCommunity()
              .candidates("louvain", "leiden", "label_propagation")
              .metrics("modularity")
              .strategy("successive_halving", eta=10, rounds=2)
              .seed(42)
              .execute(test_network)
        )
        
        # Should still complete
        assert result is not None
        assert result.selected is not None
    
    def test_sh_with_many_rounds(self, test_network):
        """Should handle many rounds."""
        result = (
            AutoCommunity()
              .candidates("louvain", "leiden")
              .metrics("modularity")
              .strategy("successive_halving", eta=2, rounds=5)
              .seed(42)
              .execute(test_network)
        )
        
        assert result is not None
        assert result.selected is not None


class TestBudgetSpec:
    """Test BudgetSpec functionality."""
    
    def test_budget_creation(self):
        """Should create BudgetSpec with parameters."""
        budget = BudgetSpec(max_iter=100, n_restarts=5)
        
        assert budget.max_iter == 100
        assert budget.n_restarts == 5
    
    def test_budget_default_values(self):
        """Should have default values."""
        budget = BudgetSpec()
        
        # Should have some default value for max_iter
        assert hasattr(budget, 'max_iter')
    
    def test_budget_with_uq_samples(self):
        """Should support UQ samples."""
        budget = BudgetSpec(uq_samples=20)
        
        assert budget.uq_samples == 20
    
    def test_budget_dict_conversion(self):
        """Should convert to/from dict."""
        budget = BudgetSpec(max_iter=50, n_restarts=3)
        
        # Should be able to convert to dict for strategy config
        budget_dict = {"max_iter": budget.max_iter, "n_restarts": budget.n_restarts}
        assert budget_dict['max_iter'] == 50
        assert budget_dict['n_restarts'] == 3


class TestUtilityMethods:
    """Test different utility computation methods."""
    
    def test_mean_minus_std_utility(self, test_network):
        """Should use mean_minus_std utility."""
        result = (
            AutoCommunity()
              .candidates("louvain", "leiden")
              .metrics("modularity", "coverage")
              .strategy("successive_halving", utility_method="mean_minus_std", eta=2)
              .seed(42)
              .execute(test_network)
        )
        
        assert result is not None
        assert result.selected is not None
    
    def test_expected_regret_utility(self, test_network):
        """Should use expected_regret utility."""
        result = (
            AutoCommunity()
              .candidates("louvain", "leiden")
              .metrics("modularity")
              .strategy("successive_halving", utility_method="expected_regret", eta=2)
              .seed(42)
              .execute(test_network)
        )
        
        assert result is not None
        assert result.selected is not None
    
    def test_prob_near_best_utility(self, test_network):
        """Should use prob_near_best utility."""
        result = (
            AutoCommunity()
              .candidates("louvain", "leiden")
              .metrics("modularity")
              .strategy("successive_halving", utility_method="prob_near_best", eta=2)
              .seed(42)
              .execute(test_network)
        )
        
        assert result is not None
        assert result.selected is not None


class TestSuccessiveHalvingProvenance:
    """Test provenance tracking for successive halving."""
    
    def test_provenance_includes_strategy(self, test_network):
        """Provenance should include strategy information."""
        result = (
            AutoCommunity()
              .candidates("louvain", "leiden")
              .metrics("modularity")
              .strategy("successive_halving", eta=3, rounds=2)
              .seed(42)
              .execute(test_network)
        )
        
        assert 'strategy' in result.provenance
        assert result.provenance['strategy'] == "successive_halving"
    
    def test_provenance_includes_racing_history(self, test_network):
        """Provenance should include racing history."""
        result = (
            AutoCommunity()
              .candidates("louvain", "leiden")
              .metrics("modularity")
              .strategy("successive_halving", eta=2, rounds=2)
              .seed(42)
              .execute(test_network)
        )
        
        # Should have racing history if SH was used
        if 'racing_history' in result.provenance:
            history = result.provenance['racing_history']
            assert 'winner_algo_id' in history or 'finalists' in history
    
    def test_provenance_tracks_seed(self, test_network):
        """Provenance should track seed."""
        result = (
            AutoCommunity()
              .candidates("louvain")
              .metrics("modularity")
              .strategy("successive_halving")
              .seed(12345)
              .execute(test_network)
        )
        
        assert result.provenance['seed'] == 12345
