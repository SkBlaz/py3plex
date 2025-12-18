"""Execution-focused tests for temporal predicates in DSL WHERE clauses."""

import pytest

from py3plex.core import multinet
from py3plex.dsl import Q


def _timestamped_network():
    """Build a small multilayer network with timestamped edges."""
    net = multinet.multi_layer_network(directed=False)
    nodes = [
        {"source": "A", "type": "L"},
        {"source": "B", "type": "L"},
        {"source": "C", "type": "L"},
        {"source": "D", "type": "L"},
    ]
    net.add_nodes(nodes)

    edges = [
        {"source": "A", "target": "B", "source_type": "L", "target_type": "L", "t": 5.0},
        {"source": "B", "target": "C", "source_type": "L", "target_type": "L", "t": 15.0},
        {"source": "C", "target": "D", "source_type": "L", "target_type": "L", "t": 30.0},
        # Edge without timestamp should be excluded by temporal predicates
        {"source": "D", "target": "A", "source_type": "L", "target_type": "L"},
    ]
    net.add_edges(edges)
    return net


def _edge_times(edges):
    """Extract timestamp attribute from edge tuples returned by the executor."""
    times = []
    for edge in edges:
        if len(edge) >= 3 and isinstance(edge[2], dict):
            times.append(edge[2].get("t"))
    return times


def test_t_between_filters_edges_by_timestamp():
    """t__between should include only edges whose t lies within the closed interval."""
    net = _timestamped_network()

    result = Q.edges().where(t__between=(0.0, 20.0)).execute(net)
    times = [t for t in _edge_times(result.edges) if t is not None]

    assert len(result.edges) == 2
    assert set(times) == {5.0, 15.0}


def test_t_between_excludes_edges_without_timestamp():
    """Edges missing a t attribute should not satisfy the temporal predicate."""
    net = _timestamped_network()

    result = Q.edges().where(t__between=(0.0, 10.0)).execute(net)
    times = _edge_times(result.edges)

    assert times == [5.0]  # only the edge with explicit t inside the window


def test_t_between_invalid_argument_raises():
    """Invalid t__between payload should surface as a builder error."""
    with pytest.raises(ValueError):
        Q.edges().where(t__between=100.0)


try:
    from hypothesis import given, settings, strategies as st
except ImportError:  # pragma: no cover - optional dependency
    given = None


if given:

    def _network_from_times(times):
        net = multinet.multi_layer_network(directed=False)
        for idx, t in enumerate(times):
            src = f"u{idx}"
            dst = f"v{idx}"
            net.add_nodes(
                [{"source": src, "type": "L"}, {"source": dst, "type": "L"}]
            )
            net.add_edges(
                [
                    {
                        "source": src,
                        "target": dst,
                        "source_type": "L",
                        "target_type": "L",
                        "t": float(t),
                    }
                ]
            )
        return net

    @given(
        times=st.lists(
            st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=5,
        ),
        bounds=st.tuples(
            st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
            st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        ),
    )
    @settings(max_examples=25)
    def test_t_between_matches_gte_lte(times, bounds):
        """t__between should behave like combining t__gte and t__lte filters."""
        low, high = sorted(bounds)
        net = _network_from_times(times)

        between_result = Q.edges().where(t__between=(low, high)).execute(net)
        bounded_result = Q.edges().where(t__gte=low, t__lte=high).execute(net)

        assert set(_edge_times(between_result.edges)) == set(
            _edge_times(bounded_result.edges)
        )

else:

    def test_t_between_matches_gte_lte():
        pytest.skip("hypothesis not installed")
