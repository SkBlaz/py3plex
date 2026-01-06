"""Basic tests for robustness contracts.

These tests validate the core contract functionality with minimal network examples.
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import Q
from py3plex.contracts import Robustness, FailureMode, JaccardAtK


def make_small_network():
    """Create a small test network."""
    net = multinet.multi_layer_network(directed=False)
    
    nodes = [
        {'source': 'A', 'type': 'L0'},
        {'source': 'B', 'type': 'L0'},
        {'source': 'C', 'type': 'L0'},
        {'source': 'D', 'type': 'L0'},
        {'source': 'E', 'type': 'L0'},
    ]
    net.add_nodes(nodes)
    
    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'L0', 'target_type': 'L0'},
        {'source': 'B', 'target': 'C', 'source_type': 'L0', 'target_type': 'L0'},
        {'source': 'C', 'target': 'D', 'source_type': 'L0', 'target_type': 'L0'},
        {'source': 'D', 'target': 'E', 'source_type': 'L0', 'target_type': 'L0'},
        {'source': 'A', 'target': 'C', 'source_type': 'L0', 'target_type': 'L0'},
    ]
    net.add_edges(edges)
    
    return net


class TestBasicContract:
    """Test basic contract functionality."""
    
    def test_contract_imports(self):
        """Test that contract modules can be imported."""
        from py3plex.contracts import (
            Robustness,
            ContractResult,
            FailureMode,
            JaccardAtK,
            KendallTau,
            PartitionVI,
            PartitionARI,
        )
        
        assert Robustness is not None
        assert ContractResult is not None
        assert FailureMode is not None
    
    def test_robustness_defaults(self):
        """Test that Robustness has sensible defaults."""
        contract = Robustness()
        
        assert contract.perturb == "edge_drop"
        assert contract.seed == 0
        assert contract.mode == "soft"
        assert contract.repair is True
        assert contract.tie_policy == "break"
        assert contract.allow_nondeterminism is False
    
    def test_robustness_resolve_defaults_small_graph(self):
        """Test default resolution for small graph."""
        net = make_small_network()
        contract = Robustness()
        
        resolved = contract.resolve_defaults(
            network=net,
            conclusion_type="top_k",
            top_k=3,
            metric="degree",
        )
        
        # Small graph: should cap p_max at 0.05
        assert resolved.p_max == 0.05
        assert 0.0 in resolved.grid
        assert resolved.p_max in resolved.grid
        
        # Small graph: should bump n_samples
        assert resolved.n_samples == 50
        
        # Should auto-select JaccardAtK predicate
        assert len(resolved.predicates) == 1
        assert isinstance(resolved.predicates[0], JaccardAtK)
        assert resolved.predicates[0].k == 3
    
    def test_robustness_with_explicit_predicates(self):
        """Test contract with explicit predicates."""
        contract = Robustness(
            predicates=[JaccardAtK(k=5, threshold=0.9)]
        )
        
        assert len(contract.predicates) == 1
        assert contract.predicates[0].k == 5
        assert contract.predicates[0].threshold == 0.9
    
    def test_robustness_validation_seed_nondeterminism(self):
        """Test that seed=None requires allow_nondeterminism=True."""
        with pytest.raises(ValueError, match="seed cannot be None"):
            Robustness(seed=None, allow_nondeterminism=False)
        
        # Should work with allow_nondeterminism=True
        contract = Robustness(seed=None, allow_nondeterminism=True)
        assert contract.seed is None
    
    def test_robustness_validation_invalid_mode(self):
        """Test validation of mode parameter."""
        with pytest.raises(ValueError, match="mode must be"):
            Robustness(mode="invalid")
    
    def test_robustness_validation_invalid_perturb(self):
        """Test validation of perturb parameter."""
        with pytest.raises(ValueError, match="perturb must be"):
            Robustness(perturb="invalid")
    
    def test_contract_method_exists(self):
        """Test that .contract() method exists on QueryBuilder."""
        q = Q.nodes().compute("degree")
        
        # Should have contract method
        assert hasattr(q, "contract")
        
        # Should return QueryBuilder for chaining
        q2 = q.contract(Robustness())
        assert q2 is q  # Chaining returns self


class TestPredicates:
    """Test predicate classes."""
    
    def test_jaccard_at_k_to_dict(self):
        """Test JaccardAtK serialization."""
        pred = JaccardAtK(k=10, threshold=0.85, metric="pagerank")
        
        d = pred.to_dict()
        assert d["type"] == "jaccard_at_k"
        assert d["k"] == 10
        assert d["threshold"] == 0.85
        assert d["metric"] == "pagerank"
    
    def test_jaccard_at_k_validation(self):
        """Test JaccardAtK parameter validation."""
        with pytest.raises(ValueError, match="k must be positive"):
            JaccardAtK(k=0)
        
        with pytest.raises(ValueError, match="threshold must be in"):
            JaccardAtK(k=10, threshold=1.5)
    
    def test_predicate_get_name(self):
        """Test predicate name generation."""
        pred = JaccardAtK(k=10, threshold=0.85)
        name = pred.get_name()
        
        assert "Jaccard" in name
        assert "10" in name
        assert "0.85" in name


class TestFailureModes:
    """Test failure mode enum."""
    
    def test_failure_mode_enum_values(self):
        """Test that all failure modes are defined."""
        expected_modes = [
            "INSUFFICIENT_BASELINE",
            "NONDETERMINISM_LEAK",
            "PERTURBATION_INVALID",
            "METRIC_UNDEFINED",
            "CONTRACT_VIOLATION",
            "REPAIR_IMPOSSIBLE",
            "RESOURCE_LIMIT",
            "EXECUTION_ERROR",
        ]
        
        for mode_name in expected_modes:
            assert hasattr(FailureMode, mode_name)
            mode = getattr(FailureMode, mode_name)
            assert mode.value is not None


class TestContractResult:
    """Test ContractResult class."""
    
    def test_contract_result_pass(self):
        """Test ContractResult for passed contract."""
        from py3plex.contracts.result import ContractResult, Evidence
        
        result = ContractResult(
            baseline_result=None,
            contract_ok=True,
            message="Test passed",
            evidence=Evidence(),
        )
        
        assert result.contract_ok is True
        assert result.failure_mode is None
        assert "PASS" in str(result)
    
    def test_contract_result_fail(self):
        """Test ContractResult for failed contract."""
        from py3plex.contracts.result import ContractResult, Evidence
        
        result = ContractResult(
            baseline_result=None,
            contract_ok=False,
            failure_mode=FailureMode.CONTRACT_VIOLATION,
            message="Test failed",
            evidence=Evidence(),
        )
        
        assert result.contract_ok is False
        assert result.failure_mode == FailureMode.CONTRACT_VIOLATION
        assert "FAIL" in str(result)
    
    def test_contract_result_to_dict(self):
        """Test ContractResult serialization."""
        from py3plex.contracts.result import ContractResult, Evidence
        
        result = ContractResult(
            baseline_result=None,
            contract_ok=False,
            failure_mode=FailureMode.INSUFFICIENT_BASELINE,
            message="Not enough data",
            details={"baseline_size": 0},
            evidence=Evidence(),
        )
        
        d = result.to_dict()
        assert d["contract_ok"] is False
        assert d["failure_mode"] == "insufficient_baseline"
        assert d["message"] == "Not enough data"
        assert "details" in d


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
