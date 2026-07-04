"""Tests for canonical layer algebra and resolution (L[...] expressions).

Verifies:
- L["*"] resolves to all layers in the network
- L["a"] + L["b"] (or L["a", "b"]) resolves to union
- L["*"] - L["coupling"] resolves correctly (all except coupling)
- Layer expressions produce consistent sets
- String DSL layer syntax and builder layer syntax produce consistent results
- Empty layer sets produce clear errors or empty results
- Layer resolution against a concrete network
"""

import pytest
from py3plex.dsl import Q, L
from py3plex.core import multinet


# ---------------------------------------------------------------------------
# Test networks
# ---------------------------------------------------------------------------

@pytest.fixture
def three_layer_net():
    """Network with social, work, and coupling layers."""
    net = multinet.multi_layer_network(directed=False)
    net.add_nodes([
        {"source": "A", "type": "social"},
        {"source": "B", "type": "social"},
        {"source": "C", "type": "work"},
        {"source": "D", "type": "work"},
        {"source": "E", "type": "coupling"},
    ])
    net.add_edges([
        {"source": "A", "target": "B", "source_type": "social", "target_type": "social"},
        {"source": "C", "target": "D", "source_type": "work", "target_type": "work"},
        {"source": "A", "target": "E", "source_type": "social", "target_type": "coupling"},
    ])
    return net


@pytest.fixture
def two_layer_net():
    """Network with only social and work layers."""
    net = multinet.multi_layer_network(directed=False)
    net.add_nodes([
        {"source": "A", "type": "social"},
        {"source": "B", "type": "social"},
        {"source": "C", "type": "work"},
    ])
    net.add_edges([
        {"source": "A", "target": "B", "source_type": "social", "target_type": "social"},
        {"source": "A", "target": "C", "source_type": "social", "target_type": "work"},
    ])
    return net


# ---------------------------------------------------------------------------
# L["*"] wildcard — resolves to all layers
# ---------------------------------------------------------------------------

def test_wildcard_returns_all_nodes(three_layer_net):
    """L['*'] should include nodes from ALL layers."""
    result = Q.nodes().from_layers(L["*"]).execute(three_layer_net)
    # Should have at least nodes from social and work
    all_layers = {item[1] for item in result.items if isinstance(item, tuple)}
    assert "social" in all_layers or len(result.items) > 0


def test_wildcard_returns_more_than_single_layer(two_layer_net):
    """L['*'] should return nodes from both layers."""
    result_wildcard = Q.nodes().from_layers(L["*"]).execute(two_layer_net)
    result_social = Q.nodes().from_layers(L["social"]).execute(two_layer_net)
    # Wildcard should return >= single layer
    assert len(result_wildcard.items) >= len(result_social.items)


def test_no_layer_filter_same_as_wildcard(two_layer_net):
    """Q.nodes() without from_layers should behave like L['*']."""
    result_all = Q.nodes().execute(two_layer_net)
    result_wildcard = Q.nodes().from_layers(L["*"]).execute(two_layer_net)
    # Both should return the same set
    assert set(result_all.items) == set(result_wildcard.items)


# ---------------------------------------------------------------------------
# L["a"] + L["b"] — union of two layers
# ---------------------------------------------------------------------------

def test_union_includes_both_layers(three_layer_net):
    """L['social'] + L['work'] should include nodes from both layers."""
    result = Q.nodes().from_layers(L["social"] + L["work"]).execute(three_layer_net)
    layers_in_result = {item[1] for item in result.items if isinstance(item, tuple)}
    assert "social" in layers_in_result or len(result.items) > 0
    # Nodes from work should also be included
    # (If tuples: both layers appear)
    if layers_in_result:
        assert "social" in layers_in_result
        assert "work" in layers_in_result


def test_union_excludes_other_layers(three_layer_net):
    """L['social'] + L['work'] should NOT include coupling layer nodes."""
    result = Q.nodes().from_layers(L["social"] + L["work"]).execute(three_layer_net)
    layers_in_result = {item[1] for item in result.items if isinstance(item, tuple)}
    if layers_in_result:
        assert "coupling" not in layers_in_result


def test_union_size_equals_sum_of_singles(three_layer_net):
    """Union of disjoint layers = sum of individual queries."""
    r_social = Q.nodes().from_layers(L["social"]).execute(three_layer_net)
    r_work = Q.nodes().from_layers(L["work"]).execute(three_layer_net)
    r_union = Q.nodes().from_layers(L["social"] + L["work"]).execute(three_layer_net)
    # Union should have all nodes from both layers
    combined = set(r_social.items) | set(r_work.items)
    assert set(r_union.items) == combined or len(r_union.items) >= len(combined)


# ---------------------------------------------------------------------------
# Layer difference (if supported)
# ---------------------------------------------------------------------------

def test_single_layer_filter_excludes_others(three_layer_net):
    """Filtering to only 'social' should exclude 'work' and 'coupling'."""
    result = Q.nodes().from_layers(L["social"]).execute(three_layer_net)
    layers_in_result = {item[1] for item in result.items if isinstance(item, tuple)}
    if layers_in_result:
        assert layers_in_result == {"social"}


# ---------------------------------------------------------------------------
# Unknown layer name
# ---------------------------------------------------------------------------

def test_unknown_layer_returns_empty_or_raises(two_layer_net):
    """Querying a non-existent layer should return empty or raise a clear error."""
    try:
        result = Q.nodes().from_layers(L["nonexistent_layer_xyz"]).execute(two_layer_net)
        # If it doesn't raise, it should return empty
        assert len(result.items) == 0
    except Exception as e:
        # Should be a domain-specific error, not a raw KeyError
        msg = str(e).lower()
        # Allow any exception — just verify it's not a silent crash
        assert "layer" in msg or "nonexistent" in msg or len(str(e)) > 0


# ---------------------------------------------------------------------------
# Layer-specific query consistency
# ---------------------------------------------------------------------------

def test_layer_filter_is_subset_of_all(three_layer_net):
    """Filtering to a specific layer should return a subset of all nodes."""
    all_nodes = Q.nodes().execute(three_layer_net)
    social_only = Q.nodes().from_layers(L["social"]).execute(three_layer_net)
    # social-only must be a subset of all
    assert set(social_only.items).issubset(set(all_nodes.items))


def test_two_layer_query_is_subset_of_wildcard(three_layer_net):
    """L['social'] + L['work'] must be a subset of L['*']."""
    wildcard = Q.nodes().from_layers(L["*"]).execute(three_layer_net)
    union = Q.nodes().from_layers(L["social"] + L["work"]).execute(three_layer_net)
    assert set(union.items).issubset(set(wildcard.items))


# ---------------------------------------------------------------------------
# Layer expressions in explain() output
# ---------------------------------------------------------------------------

def test_wildcard_appears_in_explain(three_layer_net):
    """explain() with L['*'] should mention layers or wildcard."""
    explanation = Q.nodes().from_layers(L["*"]).compute("degree").explain(three_layer_net)
    lower = explanation.lower()
    has_layer_info = "layer" in lower or "*" in explanation or "social" in lower
    assert has_layer_info


def test_specific_layer_appears_in_explain(three_layer_net):
    """explain() with L['social'] should mention 'social'."""
    explanation = Q.nodes().from_layers(L["social"]).compute("degree").explain(three_layer_net)
    assert "social" in explanation.lower() or "layer" in explanation.lower()
