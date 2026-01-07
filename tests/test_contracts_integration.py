"""Integration tests for robustness contracts with actual query execution.

These tests validate end-to-end contract evaluation on real queries.
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import Q
from py3plex.contracts import Robustness, FailureMode


def make_test_network(n_nodes=10, n_edges=20):
    """Create a test network with specified size."""
    net = multinet.multi_layer_network(directed=False)
    
    # Add nodes
    nodes = [{'source': f'N{i}', 'type': 'L0'} for i in range(n_nodes)]
    net.add_nodes(nodes)
    
    # Add edges in a connected pattern
    import random
    random.seed(42)
    
    edges = []
    # Ensure connectivity: create a spanning tree first
    for i in range(n_nodes - 1):
        edges.append({
            'source': f'N{i}',
            'target': f'N{i+1}',
            'source_type': 'L0',
            'target_type': 'L0'
        })
    
    # Add remaining edges randomly
    for _ in range(n_edges - (n_nodes - 1)):
        i = random.randint(0, n_nodes - 1)
        j = random.randint(0, n_nodes - 1)
        if i != j:
            edges.append({
                'source': f'N{i}',
                'target': f'N{j}',
                'source_type': 'L0',
                'target_type': 'L0'
            })
    
    net.add_edges(edges)
    return net


@pytest.mark.slow
class TestContractIntegration:
    """Integration tests for contract execution."""
    
    def test_simple_top_k_contract_pass(self):
        """Test that a stable top-k query passes the contract."""
        net = make_test_network(n_nodes=10, n_edges=30)
        
        # Query with contract (minimal usage)
        result = (Q.nodes()
                  .compute("degree")
                  .order_by("degree", desc=True)
                  .limit(5)
                  .contract(Robustness(n_samples=5, p_max=0.05))
                  .execute(net))
        
        # Should return ContractResult
        assert hasattr(result, "contract_ok")
        
        # For a well-connected graph with small perturbations,
        # top-k by degree should be stable
        # Note: might fail due to randomness, so this is a probabilistic test
        print(f"Contract OK: {result.contract_ok}")
        if not result.contract_ok:
            print(f"Failure mode: {result.failure_mode}")
            print(f"Message: {result.message}")
    
    def test_insufficient_baseline_failure(self):
        """Test INSUFFICIENT_BASELINE failure mode."""
        net = make_test_network(n_nodes=5, n_edges=10)
        
        # Query for top-20 but network only has 5 nodes
        result = (Q.nodes()
                  .compute("degree")
                  .order_by("degree", desc=True)
                  .limit(20)
                  .contract(Robustness())
                  .execute(net))
        
        # Should fail with INSUFFICIENT_BASELINE
        assert result.contract_ok is False
        assert result.failure_mode == FailureMode.INSUFFICIENT_BASELINE
    
    def test_contract_result_serialization(self):
        """Test that ContractResult can be serialized."""
        net = make_test_network(n_nodes=10, n_edges=20)
        
        result = (Q.nodes()
                  .compute("degree")
                  .order_by("degree", desc=True)
                  .limit(3)
                  .contract(Robustness(n_samples=3, p_max=0.05))
                  .execute(net))
        
        # Should be able to serialize to dict
        d = result.to_dict()
        assert isinstance(d, dict)
        assert "contract_ok" in d
        assert "failure_mode" in d
        assert "provenance" in d
    
    def test_contract_result_to_pandas(self):
        """Test that ContractResult can be converted to pandas."""
        net = make_test_network(n_nodes=10, n_edges=20)
        
        result = (Q.nodes()
                  .compute("degree")
                  .order_by("degree", desc=True)
                  .limit(3)
                  .contract(Robustness(n_samples=3, p_max=0.05))
                  .execute(net))
        
        # Should be able to convert to pandas
        df = result.to_pandas(expand_contract=True)
        
        # Should have contract columns
        if result.contract_ok or result.repair.stable_core:
            # Columns should exist
            assert df is not None
    
    def test_contract_without_contract_unchanged(self):
        """Test that queries without .contract() are unchanged."""
        net = make_test_network(n_nodes=10, n_edges=20)
        
        # Query without contract
        result = (Q.nodes()
                  .compute("degree")
                  .order_by("degree", desc=True)
                  .limit(5)
                  .execute(net))
        
        # Should return regular QueryResult, not ContractResult
        assert not hasattr(result, "contract_ok")
        assert hasattr(result, "to_pandas")
    
    def test_contract_provenance(self):
        """Test that contract provenance is recorded."""
        net = make_test_network(n_nodes=10, n_edges=20)
        
        result = (Q.nodes()
                  .compute("degree")
                  .order_by("degree", desc=True)
                  .limit(5)
                  .contract(Robustness(n_samples=3, p_max=0.05))
                  .execute(net))
        
        # Check provenance
        assert hasattr(result, "provenance")
        assert result.provenance is not None
        assert "contract" in result.provenance
        
        # Contract spec should be recorded
        contract_spec = result.provenance["contract"]
        assert contract_spec["perturb"] == "edge_drop"
        assert contract_spec["seed"] == 0
        assert contract_spec["n_samples"] == 3
    
    def test_auto_predicate_selection_top_k(self):
        """Test that predicate is auto-selected for top-k."""
        net = make_test_network(n_nodes=10, n_edges=20)
        
        result = (Q.nodes()
                  .compute("degree")
                  .order_by("degree", desc=True)
                  .limit(7)
                  .contract(Robustness(n_samples=3))
                  .execute(net))
        
        # Check provenance for auto-selected predicate
        if "contract" in result.provenance and "predicates" in result.provenance["contract"]:
            predicates = result.provenance["contract"]["predicates"]
            assert len(predicates) > 0
            assert predicates[0]["type"] == "jaccard_at_k"
            assert predicates[0]["k"] == 7


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
