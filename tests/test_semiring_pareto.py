"""Tests for Pareto frontier utilities in py3plex.semiring.pareto."""

from py3plex.semiring.pareto import ParetoSet, pareto_semiring_spec


class TestParetoSet:
    """Test Pareto set behavior and dominance logic."""

    def test_add_rejects_dominated_vector(self):
        """Adding a dominated vector should not change the frontier."""
        frontier = ParetoSet()
        frontier.add((1.0, 1.0))
        frontier.add((2.0, 2.0))  # Dominated by (1, 1)

        assert frontier.to_list() == [(1.0, 1.0)]

    def test_add_removes_vectors_dominated_by_new_vector(self):
        """A new dominating vector should prune dominated existing vectors."""
        frontier = ParetoSet()
        frontier.add((3.0, 3.0))
        frontier.add((2.0, 2.0))
        frontier.add((1.0, 1.0))

        assert frontier.to_list() == [(1.0, 1.0)]

    def test_add_prunes_by_max_size_with_deterministic_order(self):
        """Exceeding max_size should keep lexicographically smallest vectors."""
        frontier = ParetoSet(max_size=2)
        frontier.add((2.0, 1.0))
        frontier.add((1.0, 2.0))
        frontier.add((0.0, 3.0))

        assert frontier.to_list() == [(0.0, 3.0), (1.0, 2.0)]

    def test_dominates_returns_false_for_dimension_mismatch(self):
        """Dominance comparison across different dimensions should be False."""
        frontier = ParetoSet()

        assert frontier._dominates((1.0, 2.0), (1.0, 2.0, 3.0)) is False

    def test_dominates_uses_epsilon_tolerance(self):
        """Small numerical differences within epsilon are not strict dominance."""
        frontier = ParetoSet(epsilon=1e-6)

        assert frontier._dominates((1.0, 1.0), (1.0 + 5e-7, 1.0 + 5e-7)) is False

    def test_union_combines_frontiers_and_prunes_dominated_points(self):
        """Union should merge frontiers and remove dominated vectors."""
        left = ParetoSet()
        right = ParetoSet()
        left.add((1.0, 2.0))
        left.add((2.0, 1.0))
        right.add((1.0, 2.0))  # Duplicate point
        right.add((3.0, 3.0))  # Dominated by both left points

        merged = left.union(right)

        # Equality does not imply dominance in this implementation, so duplicates
        # may remain while strictly dominated vectors are removed.
        assert merged.to_list() == [(1.0, 2.0), (1.0, 2.0), (2.0, 1.0)]

    def test_cartesian_combine_adds_componentwise_and_prunes(self):
        """Cartesian combine should perform componentwise addition for each pair."""
        left = ParetoSet()
        right = ParetoSet()
        left.add((1.0, 0.0))
        left.add((0.0, 1.0))
        right.add((1.0, 1.0))
        right.add((2.0, 2.0))  # Dominated in result by combinations with (1, 1)

        combined = left.cartesian_combine(right)

        assert combined.to_list() == [(1.0, 2.0), (2.0, 1.0)]

    def test_repr_reports_number_of_vectors(self):
        """__repr__ should include deterministic vector count."""
        frontier = ParetoSet()
        frontier.add((1.0, 1.0))

        assert repr(frontier) == "ParetoSet(1 vectors)"


class TestParetoSemiringSpec:
    """Test helper that builds Pareto semiring specifications."""

    def test_spec_has_expected_identity_and_zero(self):
        """pareto_semiring_spec should create expected empty and identity sets."""
        spec = pareto_semiring_spec(dim=3, max_size=10)

        assert spec.name == "pareto_3d"
        assert spec.zero.to_list() == []
        assert spec.one.to_list() == [(0.0, 0.0, 0.0)]

    def test_spec_plus_and_times_delegate_to_pareto_operations(self):
        """Spec operators should preserve Pareto frontier semantics."""
        spec = pareto_semiring_spec(dim=2, max_size=10)
        a = ParetoSet()
        b = ParetoSet()
        a.add((1.0, 2.0))
        b.add((2.0, 1.0))

        plus_result = spec.plus(a, b)
        times_result = spec.times(a, b)

        assert plus_result.to_list() == [(1.0, 2.0), (2.0, 1.0)]
        assert times_result.to_list() == [(3.0, 3.0)]
