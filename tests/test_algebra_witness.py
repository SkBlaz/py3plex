"""
Tests for py3plex.algebra.witness module.

Tests witness tracking structures for path reconstruction.
"""

import pytest
from py3plex.algebra.witness import WitnessSpec, PathWitness, KBestWitnesses


class TestWitnessSpec:
    """Test the WitnessSpec class."""

    def test_default_witness_spec(self):
        """Test default WitnessSpec creation."""
        spec = WitnessSpec()
        
        assert spec.enabled is False
        assert spec.mode == "single"
        assert spec.compress is False
        assert spec.k == 1

    def test_witness_spec_enabled(self):
        """Test WitnessSpec with enabled=True."""
        spec = WitnessSpec(enabled=True)
        
        assert spec.enabled is True

    def test_witness_spec_k_best_mode(self):
        """Test WitnessSpec with k_best mode."""
        spec = WitnessSpec(mode="k_best", k=5)
        
        assert spec.mode == "k_best"
        assert spec.k == 5

    def test_witness_spec_invalid_mode(self):
        """Test that invalid mode raises ValueError."""
        with pytest.raises(ValueError, match="Invalid witness mode"):
            WitnessSpec(mode="invalid_mode")

    def test_witness_spec_invalid_k_negative(self):
        """Test that negative k raises ValueError."""
        with pytest.raises(ValueError, match="k must be >= 1"):
            WitnessSpec(k=0)

    def test_witness_spec_invalid_k_negative_value(self):
        """Test that negative k value raises ValueError."""
        with pytest.raises(ValueError, match="k must be >= 1"):
            WitnessSpec(k=-1)

    def test_witness_spec_compress_enabled(self):
        """Test WitnessSpec with compression."""
        spec = WitnessSpec(compress=True)
        
        assert spec.compress is True

    def test_witness_spec_all_fields(self):
        """Test WitnessSpec with all fields set."""
        spec = WitnessSpec(
            enabled=True,
            mode="k_best",
            compress=True,
            k=10
        )
        
        assert spec.enabled is True
        assert spec.mode == "k_best"
        assert spec.compress is True
        assert spec.k == 10

    def test_witness_spec_single_mode_valid(self):
        """Test that 'single' mode is valid."""
        spec = WitnessSpec(mode="single")
        assert spec.mode == "single"

    def test_witness_spec_k_best_mode_valid(self):
        """Test that 'k_best' mode is valid."""
        spec = WitnessSpec(mode="k_best")
        assert spec.mode == "k_best"


class TestPathWitness:
    """Test the PathWitness class."""

    def test_basic_path_witness(self):
        """Test basic PathWitness creation."""
        witness = PathWitness(value=10.5)
        
        assert witness.value == 10.5
        assert witness.predecessor is None
        assert witness.edge_data is None

    def test_path_witness_with_predecessor(self):
        """Test PathWitness with predecessor."""
        witness = PathWitness(value=5, predecessor="node_a")
        
        assert witness.value == 5
        assert witness.predecessor == "node_a"

    def test_path_witness_with_edge_data(self):
        """Test PathWitness with edge metadata."""
        edge_data = {"weight": 1.5, "layer": "social"}
        witness = PathWitness(value=10, edge_data=edge_data)
        
        assert witness.value == 10
        assert witness.edge_data == edge_data
        assert witness.edge_data["weight"] == 1.5

    def test_path_witness_all_fields(self):
        """Test PathWitness with all fields."""
        edge_data = {"weight": 2.0}
        witness = PathWitness(
            value=42,
            predecessor="prev_node",
            edge_data=edge_data
        )
        
        assert witness.value == 42
        assert witness.predecessor == "prev_node"
        assert witness.edge_data == edge_data

    def test_path_witness_value_types(self):
        """Test PathWitness with different value types."""
        # Integer
        w1 = PathWitness(value=10)
        assert w1.value == 10
        
        # Float
        w2 = PathWitness(value=3.14)
        assert w2.value == 3.14
        
        # String (for some semirings)
        w3 = PathWitness(value="path_value")
        assert w3.value == "path_value"


class TestKBestWitnesses:
    """Test the KBestWitnesses class."""

    def test_default_k_best_witnesses(self):
        """Test default KBestWitnesses creation."""
        container = KBestWitnesses()
        
        assert container.witnesses == []
        assert container.max_k == 1

    def test_k_best_witnesses_with_max_k(self):
        """Test KBestWitnesses with custom max_k."""
        container = KBestWitnesses(max_k=5)
        
        assert container.max_k == 5
        assert len(container.witnesses) == 0

    def test_add_single_witness(self):
        """Test adding a single witness."""
        container = KBestWitnesses(max_k=3)
        witness = PathWitness(value=10)
        
        def better_fn(a, b):
            return a < b
        
        container.add(witness, better_fn)
        
        assert len(container.witnesses) == 1
        assert container.witnesses[0] == witness

    def test_add_multiple_witnesses_sorted(self):
        """Test that witnesses are kept sorted."""
        container = KBestWitnesses(max_k=5)
        
        def better_fn(a, b):
            return a < b
        
        # Add witnesses with different values
        container.add(PathWitness(value=30), better_fn)
        container.add(PathWitness(value=10), better_fn)
        container.add(PathWitness(value=20), better_fn)
        
        # Should be sorted by value
        assert len(container.witnesses) == 3
        assert container.witnesses[0].value == 10
        assert container.witnesses[1].value == 20
        assert container.witnesses[2].value == 30

    def test_keeps_only_k_best(self):
        """Test that only k best witnesses are kept."""
        container = KBestWitnesses(max_k=2)
        
        def better_fn(a, b):
            return a < b
        
        # Add 4 witnesses
        container.add(PathWitness(value=40), better_fn)
        container.add(PathWitness(value=10), better_fn)
        container.add(PathWitness(value=30), better_fn)
        container.add(PathWitness(value=20), better_fn)
        
        # Should keep only top 2 (smallest values)
        assert len(container.witnesses) == 2
        assert container.witnesses[0].value == 10
        assert container.witnesses[1].value == 20

    def test_best_returns_top_witness(self):
        """Test that best() returns the top witness."""
        container = KBestWitnesses(max_k=5)
        
        def better_fn(a, b):
            return a < b
        
        container.add(PathWitness(value=30), better_fn)
        container.add(PathWitness(value=10), better_fn)
        container.add(PathWitness(value=20), better_fn)
        
        best_witness = container.best()
        assert best_witness is not None
        assert best_witness.value == 10

    def test_best_returns_none_when_empty(self):
        """Test that best() returns None when no witnesses."""
        container = KBestWitnesses(max_k=3)
        
        best_witness = container.best()
        assert best_witness is None

    def test_witnesses_with_predecessors(self):
        """Test witnesses with predecessor information."""
        container = KBestWitnesses(max_k=3)
        
        def better_fn(a, b):
            return a < b
        
        w1 = PathWitness(value=10, predecessor="A")
        w2 = PathWitness(value=20, predecessor="B")
        w3 = PathWitness(value=15, predecessor="C")
        
        container.add(w1, better_fn)
        container.add(w2, better_fn)
        container.add(w3, better_fn)
        
        assert len(container.witnesses) == 3
        assert container.witnesses[0].predecessor == "A"  # value=10
        assert container.witnesses[1].predecessor == "C"  # value=15
        assert container.witnesses[2].predecessor == "B"  # value=20

    def test_max_k_equals_one(self):
        """Test with max_k=1 (single best path)."""
        container = KBestWitnesses(max_k=1)
        
        def better_fn(a, b):
            return a < b
        
        container.add(PathWitness(value=30), better_fn)
        container.add(PathWitness(value=10), better_fn)
        container.add(PathWitness(value=20), better_fn)
        
        # Should keep only the best one
        assert len(container.witnesses) == 1
        assert container.witnesses[0].value == 10

    def test_large_k_value(self):
        """Test with large max_k value."""
        container = KBestWitnesses(max_k=100)
        
        def better_fn(a, b):
            return a < b
        
        # Add only 5 witnesses
        for i in range(5):
            container.add(PathWitness(value=i * 10), better_fn)
        
        # Should keep all 5 (less than max_k)
        assert len(container.witnesses) == 5

    def test_duplicate_values(self):
        """Test with duplicate witness values."""
        container = KBestWitnesses(max_k=5)
        
        def better_fn(a, b):
            return a < b
        
        container.add(PathWitness(value=10, predecessor="A"), better_fn)
        container.add(PathWitness(value=10, predecessor="B"), better_fn)
        container.add(PathWitness(value=20), better_fn)
        
        assert len(container.witnesses) == 3
        # Both value=10 witnesses should be kept
        assert container.witnesses[0].value == 10
        assert container.witnesses[1].value == 10
        assert container.witnesses[2].value == 20
