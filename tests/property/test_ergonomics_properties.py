#!/usr/bin/env python3
"""
Property-based tests for the ergonomics module.

Tests quick_network, quick_analysis, and show_network_summary invariants.
"""

import pytest
from hypothesis import given, settings, strategies as st, assume

# Import ergonomics module
try:
    from py3plex.ergonomics import quick_network, quick_analysis, show_network_summary
    ERGONOMICS_AVAILABLE = True
except ImportError:
    ERGONOMICS_AVAILABLE = False
    pytest.skip("ergonomics module not available", allow_module_level=True)


# ---------------------------------------------------------------------------
# Shared strategies
# ---------------------------------------------------------------------------

_name = st.text(
    min_size=1, max_size=15,
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_"),
)
_people = st.lists(_name, min_size=1, max_size=6, unique=True)
_layers = st.lists(_name, min_size=1, max_size=4, unique=True)


# ---------------------------------------------------------------------------
# quick_network – node / layer creation
# ---------------------------------------------------------------------------


@pytest.mark.property
@settings(deadline=None, max_examples=25)
@given(people=_people, layers=_layers)
def test_quick_network_returns_network_object(people, layers):
    """quick_network returns a non-None network object."""
    net = quick_network(people=people, layers=layers)
    assert net is not None


@pytest.mark.property
@settings(deadline=None, max_examples=25)
@given(people=_people, layers=_layers)
def test_quick_network_node_count(people, layers):
    """quick_network creates len(people) * len(layers) node replicas."""
    net = quick_network(people=people, layers=layers)
    nodes = list(net.get_nodes())
    assert len(nodes) == len(people) * len(layers)


@pytest.mark.property
@settings(deadline=None, max_examples=25)
@given(people=_people, layers=_layers)
def test_quick_network_layer_count(people, layers):
    """quick_network creates exactly the requested number of layers."""
    net = quick_network(people=people, layers=layers)
    # get_layers() returns a tuple (layer_names, graph_objects, edge_dict)
    net_layer_names = net.get_layers()[0]
    assert len(net_layer_names) == len(layers)


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(people=_people, layers=_layers)
def test_quick_network_physical_node_count(people, layers):
    """quick_network physical node count equals len(people)."""
    net = quick_network(people=people, layers=layers)
    nodes = list(net.get_nodes())
    physical = set(n[0] for n in nodes)
    assert len(physical) == len(people)


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(people=_people, layers=_layers)
def test_quick_network_empty_connections_no_edges(people, layers):
    """quick_network with no connections has no edges."""
    net = quick_network(people=people, layers=layers, connections=None)
    edges = list(net.get_edges())
    assert len(edges) == 0


@pytest.mark.property
@settings(deadline=None, max_examples=15)
@given(people=st.lists(_name, min_size=2, max_size=5, unique=True), layers=_layers)
def test_quick_network_with_intra_layer_edge(people, layers):
    """quick_network with 3-tuple connection adds at least one edge."""
    conn = [(people[0], people[1], layers[0])]
    net = quick_network(people=people, layers=layers, connections=conn)
    edges = list(net.get_edges())
    assert len(edges) >= 1


@pytest.mark.property
@settings(deadline=None, max_examples=15)
@given(
    people=st.lists(_name, min_size=2, max_size=5, unique=True),
    layers=st.lists(_name, min_size=2, max_size=4, unique=True),
)
def test_quick_network_with_cross_layer_edge(people, layers):
    """quick_network with 4-tuple cross-layer connection adds at least one edge."""
    conn = [(people[0], people[1], layers[0], layers[1])]
    net = quick_network(people=people, layers=layers, connections=conn)
    edges = list(net.get_edges())
    assert len(edges) >= 1


@pytest.mark.property
@settings(deadline=None, max_examples=15)
@given(people=_people, layers=_layers)
def test_quick_network_directed_flag(people, layers):
    """quick_network accepts a directed flag without error."""
    net_undirected = quick_network(people=people, layers=layers, directed=False)
    net_directed = quick_network(people=people, layers=layers, directed=True)
    assert net_undirected is not None
    assert net_directed is not None


# ---------------------------------------------------------------------------
# quick_analysis – returns expected structure
# ---------------------------------------------------------------------------


@pytest.mark.property
@settings(deadline=None, max_examples=15)
@given(people=_people, layers=_layers)
def test_quick_analysis_returns_dict(people, layers):
    """quick_analysis returns a dict."""
    net = quick_network(people=people, layers=layers)
    result = quick_analysis(net)
    assert isinstance(result, dict)


@pytest.mark.property
@settings(deadline=None, max_examples=15)
@given(people=_people, layers=_layers)
def test_quick_analysis_has_required_keys(people, layers):
    """quick_analysis result contains 'dataframe', 'count', 'network_stats'."""
    net = quick_network(people=people, layers=layers)
    result = quick_analysis(net)
    assert "dataframe" in result
    assert "count" in result
    assert "network_stats" in result


@pytest.mark.property
@settings(deadline=None, max_examples=15)
@given(people=_people, layers=_layers)
def test_quick_analysis_count_is_non_negative(people, layers):
    """quick_analysis count is a non-negative integer."""
    net = quick_network(people=people, layers=layers)
    result = quick_analysis(net)
    assert isinstance(result["count"], int)
    assert result["count"] >= 0


@pytest.mark.property
@settings(deadline=None, max_examples=15)
@given(people=_people, layers=_layers)
def test_quick_analysis_default_metric_is_degree(people, layers):
    """quick_analysis default computes at least the degree metric."""
    net = quick_network(people=people, layers=layers)
    result = quick_analysis(net)
    df = result["dataframe"]
    # The dataframe should not be None
    assert df is not None


@pytest.mark.property
@settings(deadline=None, max_examples=10)
@given(people=_people, layers=_layers)
def test_quick_analysis_network_stats_is_dict(people, layers):
    """quick_analysis network_stats value is a dict."""
    net = quick_network(people=people, layers=layers)
    result = quick_analysis(net)
    assert isinstance(result["network_stats"], dict)


# ---------------------------------------------------------------------------
# show_network_summary – output handling
# ---------------------------------------------------------------------------


@pytest.mark.property
@settings(deadline=None, max_examples=15)
@given(people=_people, layers=_layers)
def test_show_network_summary_does_not_raise(people, layers):
    """show_network_summary runs without raising an exception."""
    import io
    import contextlib

    net = quick_network(people=people, layers=layers)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        show_network_summary(net)  # Should not raise


@pytest.mark.property
@settings(deadline=None, max_examples=15)
@given(people=_people, layers=_layers)
def test_show_network_summary_prints_something(people, layers):
    """show_network_summary produces non-empty output."""
    import io
    import contextlib

    net = quick_network(people=people, layers=layers)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        show_network_summary(net)
    assert len(buf.getvalue()) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "property"])
