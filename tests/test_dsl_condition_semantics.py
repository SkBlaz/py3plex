"""Correctness tests for DSL v2 WHERE semantics.

Focus:
- Numeric equality should behave numerically (int vs float).
- Boolean operator precedence: AND binds tighter than OR.
- Layer wildcard algebra behaves as set algebra.
"""

import pytest

from py3plex.core import multinet
from py3plex.dsl import F, L, Q, UnknownMeasureError


@pytest.fixture
def small_two_layer_network():
    net = multinet.multi_layer_network(directed=False)

    net.add_nodes(
        [
            {"source": "A", "type": "social"},
            {"source": "B", "type": "social"},
            {"source": "C", "type": "social"},
            {"source": "D", "type": "work"},
            {"source": "E", "type": "work"},
        ]
    )

    net.add_edges(
        [
            # Social triangle: degree(A)=degree(B)=degree(C)=2
            {"source": "A", "target": "B", "source_type": "social", "target_type": "social"},
            {"source": "B", "target": "C", "source_type": "social", "target_type": "social"},
            {"source": "A", "target": "C", "source_type": "social", "target_type": "social"},
            # Work single edge: degree(D)=degree(E)=1
            {"source": "D", "target": "E", "source_type": "work", "target_type": "work"},
        ]
    )
    return net


def test_where_numeric_equality_treats_int_and_float_equal(small_two_layer_network):
    result = Q.nodes().where(F.degree == 2.0).execute(small_two_layer_network)
    assert set(result.nodes) == {("A", "social"), ("B", "social"), ("C", "social")}


def test_where_numeric_equality_from_kwargs_treats_int_and_float_equal(small_two_layer_network):
    result = Q.nodes().where(degree__eq=2.0).execute(small_two_layer_network)
    assert set(result.nodes) == {("A", "social"), ("B", "social"), ("C", "social")}


def test_where_and_or_precedence_and_binds_tighter_than_or(small_two_layer_network):
    # Intended meaning (matching Python precedence): A OR (B AND C)
    # A: social layer; B: work layer; C: degree==1
    expr = (F.layer == "social") | ((F.layer == "work") & (F.degree == 1))
    result = Q.nodes().where(expr).execute(small_two_layer_network)
    assert set(result.nodes) == {
        ("A", "social"),
        ("B", "social"),
        ("C", "social"),
        ("D", "work"),
        ("E", "work"),
    }


def test_from_layers_wildcard_difference_filters_nodes(small_two_layer_network):
    # All layers except work should be the social layer.
    result = Q.nodes().from_layers(L["*"] - L["work"]).execute(small_two_layer_network)
    assert set(result.nodes) == {("A", "social"), ("B", "social"), ("C", "social")}


def test_compute_unknown_measure_raises(small_two_layer_network):
    with pytest.raises(UnknownMeasureError):
        Q.nodes().compute("definitely_not_a_measure").execute(small_two_layer_network)


def test_property_numeric_equality_matches_float_cast_for_node_attributes():
    hypothesis = pytest.importorskip("hypothesis")
    strategies = pytest.importorskip("hypothesis.strategies")

    @hypothesis.given(
        value=strategies.one_of(
            strategies.integers(min_value=-10, max_value=10),
            strategies.floats(
                min_value=-10.0,
                max_value=10.0,
                allow_nan=False,
                allow_infinity=False,
            ),
        )
    )
    @hypothesis.settings(max_examples=50)
    def check(value):
        net = multinet.multi_layer_network(directed=False)
        net.add_nodes([{"source": "X", "type": "L"}])
        node = ("X", "L")
        net.core_network.nodes[node]["score"] = value

        # Equality should behave numerically across int/float/stringy numeric values.
        result_eq = Q.nodes().where(F.score == float(value)).execute(net)
        assert set(result_eq.nodes) == {node}

        result_ne = Q.nodes().where(F.score != float(value)).execute(net)
        assert set(result_ne.nodes) == set()

    check()
