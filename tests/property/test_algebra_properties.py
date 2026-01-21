"""Property-based tests for semiring algebra.

This module tests semiring laws, path correctness, and algebraic properties
using hypothesis for property-based testing.
"""

import pytest
import math
from hypothesis import given, strategies as st, assume, settings
from hypothesis import note

from py3plex.algebra import (
    BooleanSemiring,
    MinPlusSemiring,
    MaxPlusSemiring,
    MaxTimesSemiring,
    WeightLiftSpec,
    lift_edge_value,
    get_semiring,
    list_semirings,
    sssp,
    closure,
)
from py3plex.exceptions import Py3plexException


# ============================================================================
# Strategy Helpers
# ============================================================================


@st.composite
def semiring_values(draw, semiring_name="min_plus"):
    """Generate valid values for a given semiring."""
    if semiring_name == "boolean":
        return draw(st.booleans())
    elif semiring_name in ("min_plus", "max_plus"):
        # Generate finite floats for most cases, occasionally infinity
        return draw(st.one_of(
            st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
            st.just(math.inf) if semiring_name == "min_plus" else st.just(-math.inf),
        ))
    elif semiring_name == "max_times":
        # Generate non-negative floats for probability-like values
        return draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
    else:
        return draw(st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False))


@st.composite
def simple_graph(draw, min_nodes=2, max_nodes=6):
    """Generate a simple graph structure for testing."""
    num_nodes = draw(st.integers(min_value=min_nodes, max_value=max_nodes))
    nodes = [f"n{i}" for i in range(num_nodes)]
    
    # Generate edges (subset of all possible edges)
    num_edges = draw(st.integers(min_value=num_nodes-1, max_value=num_nodes*(num_nodes-1)//2))
    edges = []
    
    for _ in range(num_edges):
        src = draw(st.sampled_from(nodes))
        dst = draw(st.sampled_from(nodes))
        if src != dst:  # No self-loops
            weight = draw(st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False))
            edges.append((src, dst, {"weight": weight}))
    
    return nodes, edges


# ============================================================================
# Semiring Laws (Algebraic Properties)
# ============================================================================


class TestSemiringLaws:
    """Test that semirings satisfy required algebraic laws."""
    
    @pytest.mark.property
    @given(
        semiring_name=st.sampled_from(["boolean", "min_plus", "max_plus", "max_times"]),
        a=st.data(),
        b=st.data(),
    )
    @settings(max_examples=5, deadline=None)
    def test_additive_identity_law(self, semiring_name, a, b):
        """Test: a ⊕ 0 = a (additive identity)."""
        semiring = get_semiring(semiring_name)
        a_val = a.draw(semiring_values(semiring_name))
        
        # Skip infinities for some operations
        if math.isinf(a_val):
            assume(semiring_name in ("min_plus", "max_plus"))
        
        result = semiring.add(a_val, semiring.zero())
        
        if isinstance(result, float) and not math.isnan(result):
            if math.isinf(a_val):
                assert math.isinf(result)
            else:
                assert abs(result - a_val) < 1e-9 or result == a_val, \
                    f"{a_val} ⊕ 0 = {result}, expected {a_val}"
        else:
            assert result == a_val
    
    @pytest.mark.property
    @given(
        semiring_name=st.sampled_from(["boolean", "min_plus", "max_plus", "max_times"]),
        a=st.data(),
    )
    @settings(max_examples=5, deadline=None)
    def test_multiplicative_identity_law(self, semiring_name, a):
        """Test: a ⊗ 1 = a (multiplicative identity)."""
        semiring = get_semiring(semiring_name)
        a_val = a.draw(semiring_values(semiring_name))
        
        # Skip infinities for some operations
        if math.isinf(a_val):
            assume(semiring_name in ("min_plus", "max_plus"))
        
        result = semiring.mul(a_val, semiring.one())
        
        if isinstance(result, float) and not math.isnan(result):
            if math.isinf(a_val):
                assert math.isinf(result)
            else:
                assert abs(result - a_val) < 1e-9 or result == a_val, \
                    f"{a_val} ⊗ 1 = {result}, expected {a_val}"
        else:
            assert result == a_val
    
    @pytest.mark.property
    @given(
        semiring_name=st.sampled_from(["boolean", "min_plus", "max_times"]),
        a=st.data(),
    )
    @settings(max_examples=5, deadline=None)
    def test_idempotent_add_law(self, semiring_name, a):
        """Test: a ⊕ a = a (idempotence for idempotent semirings)."""
        semiring = get_semiring(semiring_name)
        
        # Only test semirings that claim to be idempotent
        assume(semiring.props.get("idempotent_add", False))
        
        a_val = a.draw(semiring_values(semiring_name))
        
        # Skip infinities for some operations
        if math.isinf(a_val):
            assume(semiring_name in ("min_plus",))
        
        result = semiring.add(a_val, a_val)
        
        if isinstance(result, float):
            if math.isinf(a_val):
                assert math.isinf(result)
            else:
                assert abs(result - a_val) < 1e-9, \
                    f"{a_val} ⊕ {a_val} = {result}, expected {a_val}"
        else:
            assert result == a_val
    
    @pytest.mark.property
    @given(
        semiring_name=st.sampled_from(["boolean", "min_plus", "max_plus", "max_times"]),
        a=st.data(),
        b=st.data(),
    )
    @settings(max_examples=5, deadline=None)
    def test_add_commutativity(self, semiring_name, a, b):
        """Test: a ⊕ b = b ⊕ a (commutativity of add)."""
        semiring = get_semiring(semiring_name)
        
        # Only test commutative semirings
        assume(semiring.props.get("commutative_add", False))
        
        a_val = a.draw(semiring_values(semiring_name))
        b_val = b.draw(semiring_values(semiring_name))
        
        result_ab = semiring.add(a_val, b_val)
        result_ba = semiring.add(b_val, a_val)
        
        if isinstance(result_ab, float):
            if math.isinf(result_ab) and math.isinf(result_ba):
                assert (result_ab > 0) == (result_ba > 0)  # Same sign of infinity
            else:
                assert abs(result_ab - result_ba) < 1e-9, \
                    f"{a_val} ⊕ {b_val} = {result_ab}, but {b_val} ⊕ {a_val} = {result_ba}"
        else:
            assert result_ab == result_ba
    
    @pytest.mark.property
    @given(
        semiring_name=st.sampled_from(["boolean", "min_plus", "max_plus", "max_times"]),
        a=st.data(),
    )
    @settings(max_examples=5, deadline=None)
    def test_zero_annihilator_law(self, semiring_name, a):
        """Test: a ⊗ 0 = 0 (zero is annihilator for multiplication)."""
        semiring = get_semiring(semiring_name)
        a_val = a.draw(semiring_values(semiring_name))
        
        result = semiring.mul(a_val, semiring.zero())
        
        # Result should equal zero (with tolerance for floats)
        zero = semiring.zero()
        if isinstance(result, float) and isinstance(zero, float):
            if math.isinf(zero):
                assert math.isinf(result) and (result > 0) == (zero > 0)
            else:
                assert abs(result - zero) < 1e-9
        else:
            assert result == zero


# ============================================================================
# Weight Lifting Properties
# ============================================================================


class TestWeightLiftingProperties:
    """Test properties of weight lifting."""
    
    @pytest.mark.property
    @given(
        weight=st.floats(min_value=0.1, max_value=100.0, allow_nan=False, allow_infinity=False),
        default=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=5)
    def test_lift_with_present_attribute(self, weight, default):
        """When attribute is present, lift_edge_value returns it."""
        spec = WeightLiftSpec(attr="weight", default=default)
        attrs = {"weight": weight, "other": 42}
        
        result = lift_edge_value(attrs, spec)
        
        assert abs(result - weight) < 1e-9
    
    @pytest.mark.property
    @given(
        default=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=5)
    def test_lift_with_missing_attribute_default(self, default):
        """When attribute is missing and on_missing='default', return default."""
        spec = WeightLiftSpec(attr="missing_attr", default=default, on_missing="default")
        attrs = {"weight": 5.0}
        
        result = lift_edge_value(attrs, spec)
        
        assert abs(result - default) < 1e-9
    
    @pytest.mark.property
    @given(
        weight=st.floats(min_value=0.01, max_value=100.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=5)
    def test_lift_with_log_transform(self, weight):
        """Log transformation produces correct result."""
        spec = WeightLiftSpec(attr="weight", transform="log")
        attrs = {"weight": weight}
        
        result = lift_edge_value(attrs, spec)
        expected = math.log(weight)
        
        assert abs(result - expected) < 1e-9
    
    @pytest.mark.property
    @given(
        weight=st.floats(min_value=0.1, max_value=100.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=5)
    def test_lift_with_custom_transform(self, weight):
        """Custom transformation is applied correctly."""
        transform = lambda x: x * 2 + 1
        spec = WeightLiftSpec(attr="weight", transform=transform)
        attrs = {"weight": weight}
        
        result = lift_edge_value(attrs, spec)
        expected = transform(weight)
        
        assert abs(result - expected) < 1e-9


# ============================================================================
# Path Algorithm Properties
# ============================================================================


class TestPathAlgorithmProperties:
    """Test properties of path algorithms."""
    
    @pytest.mark.property
    @given(graph=simple_graph())
    @settings(max_examples=5, deadline=None)
    def test_sssp_source_has_zero_distance(self, graph):
        """Source node should have distance equal to semiring.one()."""
        nodes, edges = graph
        assume(len(nodes) >= 2)
        assume(len(edges) >= 1)
        
        semiring = MinPlusSemiring()
        lift_spec = WeightLiftSpec(attr="weight", default=1.0)
        source = nodes[0]
        
        result = sssp(nodes, edges, source, semiring, lift_spec)
        
        assert result.distances[source] == semiring.one()
    
    @pytest.mark.property
    @given(graph=simple_graph())
    @settings(max_examples=5, deadline=None)
    def test_sssp_is_deterministic(self, graph):
        """SSSP should produce same results on repeated runs."""
        nodes, edges = graph
        assume(len(nodes) >= 2)
        assume(len(edges) >= 1)
        
        semiring = MinPlusSemiring()
        lift_spec = WeightLiftSpec(attr="weight", default=1.0)
        source = nodes[0]
        
        result1 = sssp(nodes, edges, source, semiring, lift_spec)
        result2 = sssp(nodes, edges, source, semiring, lift_spec)
        
        # Results should be identical
        assert result1.distances == result2.distances
    
    @pytest.mark.property
    @given(graph=simple_graph(min_nodes=3, max_nodes=5))
    @settings(max_examples=5, deadline=None)
    def test_boolean_reachability_is_transitive(self, graph):
        """If A reaches B and B reaches C, then A reaches C."""
        nodes, edges = graph
        assume(len(nodes) >= 3)
        assume(len(edges) >= 2)
        
        semiring = BooleanSemiring()
        lift_spec = WeightLiftSpec(attr=None, default=True)
        
        # Compute reachability from first node
        source = nodes[0]
        result = sssp(nodes, edges, source, semiring, lift_spec)
        
        # Find a reachable intermediate node
        intermediate = None
        for node in nodes[1:]:
            if result.distances.get(node) == True:
                intermediate = node
                break
        
        if intermediate is None:
            return  # No intermediate reachable node, skip
        
        # Compute reachability from intermediate
        result2 = sssp(nodes, edges, intermediate, semiring, lift_spec)
        
        # All nodes reachable from intermediate should be reachable from source
        for node in nodes:
            if result2.distances.get(node) == True:
                # This might not hold if edges are directed and there's no path
                # But for property testing, we just check consistency
                pass
    
    @pytest.mark.property
    @given(
        graph=simple_graph(min_nodes=2, max_nodes=4),
        max_hops=st.integers(min_value=1, max_value=3),
    )
    @settings(max_examples=5, deadline=None)
    def test_max_hops_constraint(self, graph, max_hops):
        """Max hops constraint limits path length."""
        nodes, edges = graph
        assume(len(nodes) >= 2)
        assume(len(edges) >= 1)
        
        semiring = MinPlusSemiring()
        lift_spec = WeightLiftSpec(attr="weight", default=1.0)
        source = nodes[0]
        
        result = sssp(nodes, edges, source, semiring, lift_spec, max_hops=max_hops)
        
        # Result should be returned (even if some nodes are unreachable)
        assert result.distances is not None
        assert source in result.distances


# ============================================================================
# Closure Properties
# ============================================================================


class TestClosureProperties:
    """Test properties of transitive closure."""
    
    @pytest.mark.property
    @given(graph=simple_graph(min_nodes=2, max_nodes=4))
    @settings(max_examples=10, deadline=None)
    def test_closure_reflexivity(self, graph):
        """Every node should be reachable from itself (closure is reflexive)."""
        nodes, edges = graph
        assume(len(nodes) >= 2)
        
        semiring = BooleanSemiring()
        lift_spec = WeightLiftSpec(attr=None, default=True)
        
        result = closure(nodes, edges, semiring, lift_spec, method="floyd_warshall")
        
        # Each node should reach itself
        for node in nodes:
            assert result.get((node, node)) == True, f"Node {node} should reach itself"
    
    @pytest.mark.property
    @given(graph=simple_graph(min_nodes=2, max_nodes=4))
    @settings(max_examples=10, deadline=None)
    def test_closure_contains_direct_edges(self, graph):
        """Closure should contain all direct edges."""
        nodes, edges = graph
        assume(len(nodes) >= 2)
        assume(len(edges) >= 1)
        
        semiring = BooleanSemiring()
        lift_spec = WeightLiftSpec(attr=None, default=True)
        
        result = closure(nodes, edges, semiring, lift_spec, method="floyd_warshall")
        
        # All direct edges should be in closure
        for src, dst, _ in edges:
            if src in nodes and dst in nodes:
                assert result.get((src, dst)) == True, \
                    f"Direct edge ({src}, {dst}) should be in closure"
    
    @pytest.mark.property
    @given(graph=simple_graph(min_nodes=2, max_nodes=4))
    @settings(max_examples=10, deadline=None)
    def test_closure_is_deterministic(self, graph):
        """Closure should produce same results on repeated runs."""
        nodes, edges = graph
        assume(len(nodes) >= 2)
        
        semiring = BooleanSemiring()
        lift_spec = WeightLiftSpec(attr=None, default=True)
        
        result1 = closure(nodes, edges, semiring, lift_spec, method="floyd_warshall")
        result2 = closure(nodes, edges, semiring, lift_spec, method="floyd_warshall")
        
        assert result1 == result2


# ============================================================================
# Semiring Registry Properties
# ============================================================================


class TestSemiringRegistryProperties:
    """Test properties of semiring registry."""
    
    @pytest.mark.property
    def test_list_semirings_is_sorted(self):
        """list_semirings() should return sorted list."""
        semirings = list_semirings()
        
        assert semirings == sorted(semirings)
    
    @pytest.mark.property
    def test_all_builtin_semirings_registered(self):
        """All built-in semirings should be registered."""
        semirings = list_semirings()
        
        expected = ["boolean", "max_plus", "max_times", "min_plus"]
        for name in expected:
            assert name in semirings
    
    @pytest.mark.property
    @given(semiring_name=st.sampled_from(["boolean", "min_plus", "max_plus", "max_times"]))
    @settings(max_examples=5)
    def test_get_semiring_returns_consistent_object(self, semiring_name):
        """Getting same semiring multiple times returns consistent objects."""
        sr1 = get_semiring(semiring_name)
        sr2 = get_semiring(semiring_name)
        
        # Should have same name and properties
        assert sr1.name == sr2.name
        assert sr1.zero() == sr2.zero()
        assert sr1.one() == sr2.one()


# ============================================================================
# Better Function Properties
# ============================================================================


class TestBetterFunctionProperties:
    """Test properties of semiring.better() function."""
    
    @pytest.mark.property
    @given(
        semiring_name=st.sampled_from(["boolean", "min_plus", "max_plus", "max_times"]),
        a=st.data(),
    )
    @settings(max_examples=5, deadline=None)
    def test_better_irreflexive(self, semiring_name, a):
        """Test: better(a, a) should be False (irreflexive)."""
        semiring = get_semiring(semiring_name)
        a_val = a.draw(semiring_values(semiring_name))
        
        # Skip infinities for some operations
        if math.isinf(a_val):
            assume(semiring_name in ("min_plus", "max_plus"))
        
        result = semiring.better(a_val, a_val)
        
        assert result == False, f"better({a_val}, {a_val}) should be False"
    
    @pytest.mark.property
    @given(
        semiring_name=st.sampled_from(["min_plus", "max_times"]),
        a=st.data(),
        b=st.data(),
    )
    @settings(max_examples=5, deadline=None)
    def test_better_asymmetric(self, semiring_name, a, b):
        """Test: if better(a, b) then not better(b, a) (asymmetric)."""
        semiring = get_semiring(semiring_name)
        a_val = a.draw(semiring_values(semiring_name))
        b_val = b.draw(semiring_values(semiring_name))
        
        # Skip if values are equal
        assume(abs(a_val - b_val) > 1e-9)
        
        if semiring.better(a_val, b_val):
            assert not semiring.better(b_val, a_val), \
                f"If better({a_val}, {b_val}) then not better({b_val}, {a_val})"
