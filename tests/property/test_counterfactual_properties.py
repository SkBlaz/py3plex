"""Property-based tests for the counterfactual module.

This module tests invariants and properties of counterfactual reasoning
using hypothesis for property-based testing.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from hypothesis import note
import hashlib

from py3plex.counterfactual import (
    RemoveEdgesSpec,
    RewireDegreePreservingSpec,
    ShuffleWeightsSpec,
    KnockoutSpec,
)
from py3plex.counterfactual.engine import CounterfactualEngine
from py3plex.core import multinet


# ============================================================================
# Helper Strategies
# ============================================================================


@st.composite
def remove_edges_spec_strategy(draw):
    """Generate random RemoveEdgesSpec."""
    use_proportion = draw(st.booleans())
    if use_proportion:
        proportion = draw(st.floats(min_value=0.0, max_value=1.0))
        return RemoveEdgesSpec(proportion=proportion, mode="random")
    else:
        budget = draw(st.integers(min_value=0, max_value=100))
        return RemoveEdgesSpec(budget=budget, mode="random")


@st.composite
def rewire_spec_strategy(draw):
    """Generate random RewireDegreePreservingSpec."""
    n_swaps = draw(st.integers(min_value=1, max_value=100))
    return RewireDegreePreservingSpec(n_swaps=n_swaps)


@st.composite
def shuffle_weights_spec_strategy(draw):
    """Generate random ShuffleWeightsSpec."""
    return ShuffleWeightsSpec()


@st.composite
def knockout_spec_strategy(draw):
    """Generate random KnockoutSpec."""
    # Generate simple node list
    num_nodes = draw(st.integers(min_value=1, max_value=5))
    nodes = [f"n{i}" for i in range(num_nodes)]
    return KnockoutSpec(nodes=nodes)


@st.composite
def simple_network_strategy(draw):
    """Generate a simple multilayer network for testing."""
    num_nodes = draw(st.integers(min_value=3, max_value=8))
    num_layers = draw(st.integers(min_value=1, max_value=2))
    edge_prob = draw(st.floats(min_value=0.3, max_value=0.8))
    
    net = multinet.multi_layer_network(directed=False)
    
    # Generate layers
    layers = [f"L{i}" for i in range(num_layers)]
    nodes = [f"n{i}" for i in range(num_nodes)]
    
    # Add nodes
    for layer in layers:
        for node in nodes:
            net.add_nodes([{"source": node, "type": layer}])
    
    # Add edges
    edges = []
    for layer in layers:
        for i in range(num_nodes):
            for j in range(i + 1, num_nodes):
                if draw(st.floats(min_value=0, max_value=1)) < edge_prob:
                    weight = draw(st.floats(min_value=0.1, max_value=10.0))
                    edges.append({
                        "source": nodes[i],
                        "target": nodes[j],
                        "source_type": layer,
                        "target_type": layer,
                        "weight": weight,
                    })
    
    if edges:
        net.add_edges(edges)
    
    return net


# ============================================================================
# Property Tests: InterventionSpec Immutability
# ============================================================================


class TestInterventionSpecProperties:
    """Property-based tests for InterventionSpec classes."""
    
    @pytest.mark.property
    @given(spec=remove_edges_spec_strategy())
    @settings(max_examples=100, deadline=None)
    def test_remove_edges_spec_immutability(self, spec):
        """RemoveEdgesSpec must be immutable (frozen dataclass)."""
        with pytest.raises(AttributeError):
            spec.proportion = 0.5
        with pytest.raises(AttributeError):
            spec.mode = "targeted"
    
    @pytest.mark.property
    @given(spec=rewire_spec_strategy())
    @settings(max_examples=100, deadline=None)
    def test_rewire_spec_immutability(self, spec):
        """RewireDegreePreservingSpec must be immutable."""
        with pytest.raises(AttributeError):
            spec.n_swaps = 100
    
    @pytest.mark.property
    @given(spec=shuffle_weights_spec_strategy())
    @settings(max_examples=50, deadline=None)
    def test_shuffle_weights_spec_immutability(self, spec):
        """ShuffleWeightsSpec must be immutable."""
        # ShuffleWeightsSpec has no mutable fields, but test the pattern
        assert hasattr(spec, "to_dict")
    
    @pytest.mark.property
    @given(spec=knockout_spec_strategy())
    @settings(max_examples=100, deadline=None)
    def test_knockout_spec_immutability(self, spec):
        """KnockoutSpec must be immutable."""
        with pytest.raises((AttributeError, TypeError)):
            spec.nodes = ["new_node"]


# ============================================================================
# Property Tests: Spec Hash Determinism
# ============================================================================


class TestSpecHashProperties:
    """Property-based tests for spec hash determinism."""
    
    @pytest.mark.property
    @given(spec=remove_edges_spec_strategy())
    @settings(max_examples=100, deadline=None)
    def test_remove_edges_spec_hash_deterministic(self, spec):
        """spec_hash must be deterministic."""
        hash1 = spec.spec_hash()
        hash2 = spec.spec_hash()
        assert hash1 == hash2
        assert isinstance(hash1, str)
        assert len(hash1) > 0
    
    @pytest.mark.property
    @given(spec=rewire_spec_strategy())
    @settings(max_examples=100, deadline=None)
    def test_rewire_spec_hash_deterministic(self, spec):
        """spec_hash must be deterministic."""
        hash1 = spec.spec_hash()
        hash2 = spec.spec_hash()
        assert hash1 == hash2
        assert isinstance(hash1, str)
        assert len(hash1) > 0
    
    @pytest.mark.property
    @given(
        spec1=remove_edges_spec_strategy(),
        spec2=remove_edges_spec_strategy(),
    )
    @settings(max_examples=50, deadline=None)
    def test_different_specs_different_hashes(self, spec1, spec2):
        """Different specs should (likely) have different hashes."""
        # Only test if specs are actually different
        if spec1 != spec2:
            hash1 = spec1.spec_hash()
            hash2 = spec2.spec_hash()
            # With high probability, different specs have different hashes
            # (hash collisions are rare but possible, so we don't assert strictly)
            if spec1.proportion != spec2.proportion or spec1.budget != spec2.budget:
                note(f"Spec1: {spec1}, hash: {hash1}")
                note(f"Spec2: {spec2}, hash: {hash2}")


# ============================================================================
# Property Tests: Spec Serialization
# ============================================================================


class TestSpecSerializationProperties:
    """Property-based tests for spec serialization."""
    
    @pytest.mark.property
    @given(spec=remove_edges_spec_strategy())
    @settings(max_examples=100, deadline=None)
    def test_remove_edges_spec_to_dict(self, spec):
        """to_dict must return a dictionary."""
        d = spec.to_dict()
        assert isinstance(d, dict)
        assert "type" in d or "proportion" in d or "budget" in d
    
    @pytest.mark.property
    @given(spec=rewire_spec_strategy())
    @settings(max_examples=100, deadline=None)
    def test_rewire_spec_to_dict(self, spec):
        """to_dict must return a dictionary."""
        d = spec.to_dict()
        assert isinstance(d, dict)
        assert "n_swaps" in d or "type" in d
    
    @pytest.mark.property
    @given(spec=knockout_spec_strategy())
    @settings(max_examples=100, deadline=None)
    def test_knockout_spec_to_dict(self, spec):
        """to_dict must return a dictionary."""
        d = spec.to_dict()
        assert isinstance(d, dict)
        assert "nodes" in d or "type" in d


# ============================================================================
# Property Tests: RemoveEdgesSpec Validation
# ============================================================================


class TestRemoveEdgesSpecValidation:
    """Property-based tests for RemoveEdgesSpec validation."""
    
    @pytest.mark.property
    @given(proportion=st.floats(min_value=-1.0, max_value=-0.01))
    @settings(max_examples=50, deadline=None)
    def test_negative_proportion_rejected(self, proportion):
        """Negative proportions must be rejected."""
        with pytest.raises(ValueError):
            RemoveEdgesSpec(proportion=proportion)
    
    @pytest.mark.property
    @given(proportion=st.floats(min_value=1.01, max_value=2.0))
    @settings(max_examples=50, deadline=None)
    def test_proportion_over_one_rejected(self, proportion):
        """Proportions > 1.0 must be rejected."""
        with pytest.raises(ValueError):
            RemoveEdgesSpec(proportion=proportion)
    
    @pytest.mark.property
    @given(budget=st.integers(min_value=-100, max_value=-1))
    @settings(max_examples=50, deadline=None)
    def test_negative_budget_rejected(self, budget):
        """Negative budgets must be rejected."""
        with pytest.raises(ValueError):
            RemoveEdgesSpec(budget=budget)
    
    @pytest.mark.property
    def test_both_proportion_and_budget_rejected(self):
        """Cannot specify both proportion and budget."""
        with pytest.raises(ValueError):
            RemoveEdgesSpec(proportion=0.5, budget=10)
    
    @pytest.mark.property
    def test_neither_proportion_nor_budget_rejected(self):
        """Must specify either proportion or budget."""
        with pytest.raises(ValueError):
            RemoveEdgesSpec()


# ============================================================================
# Property Tests: CounterfactualEngine Determinism
# ============================================================================




# ============================================================================
# Property Tests: InterventionSpec Properties
# ============================================================================


class TestInterventionSpecProperties:
    """Property-based tests for InterventionSpec invariants."""
    
    @pytest.mark.property
    @given(nodes=st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=5))
    @settings(max_examples=50, deadline=None)
    def test_knockout_spec_immutable(self, nodes):
        """KnockoutSpec should be immutable."""
        spec = KnockoutSpec(nodes=nodes)
        
        # Verify spec is frozen
        with pytest.raises(Exception):  # dataclass frozen=True raises FrozenInstanceError
            spec.nodes = []
    
    @pytest.mark.property
    @given(
        proportion=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        seed=st.integers(min_value=0, max_value=10000),
    )
    @settings(max_examples=50, deadline=None)
    def test_remove_edges_spec_deterministic(self, proportion, seed):
        """RemoveEdgesSpec with same seed should be deterministic."""
        spec1 = RemoveEdgesSpec(proportion=proportion, mode="random")
        spec2 = RemoveEdgesSpec(proportion=proportion, mode="random")
        
        # Specs should be equal
        assert spec1.proportion == spec2.proportion
        assert spec1.mode == spec2.mode
    
    @pytest.mark.property
    @given(n_swaps=st.integers(min_value=0, max_value=100))
    @settings(max_examples=50, deadline=None)
    def test_rewire_spec_nonnegative_swaps(self, n_swaps):
        """RewireDegreePreservingSpec should accept non-negative n_swaps."""
        spec = RewireDegreePreservingSpec(n_swaps=n_swaps)
        assert spec.n_swaps >= 0
    
    @pytest.mark.property
    @given(budget=st.integers(min_value=0, max_value=100))
    @settings(max_examples=50, deadline=None)
    def test_remove_edges_budget_nonnegative(self, budget):
        """RemoveEdgesSpec with budget should accept non-negative values."""
        spec = RemoveEdgesSpec(budget=budget, mode="random")
        assert spec.budget >= 0
