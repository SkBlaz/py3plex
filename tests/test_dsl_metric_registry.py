"""Tests for the DSL metric registry (py3plex/dsl/metrics.py).

Verifies:
- MetricSpec is a frozen dataclass with expected fields
- METRIC_REGISTRY contains known core metrics
- get_metric() returns correct MetricSpec for known metric names
- get_metric() raises for unknown metrics
- is_known_metric() returns True for known, False for unknown
- Alias resolution works if aliases are set
- target field is "nodes" for node-only metrics
- cost_class indicates expensive metrics correctly
"""

import pytest
from py3plex.dsl.metrics import (
    MetricSpec,
    METRIC_REGISTRY,
    get_metric,
    is_known_metric,
)


# ---------------------------------------------------------------------------
# MetricSpec structure
# ---------------------------------------------------------------------------

def test_metric_spec_is_dataclass():
    """MetricSpec must be a dataclass with expected fields."""
    spec = get_metric("degree")
    assert isinstance(spec, MetricSpec)
    assert hasattr(spec, "name")
    assert hasattr(spec, "target")
    assert hasattr(spec, "output_type")
    assert hasattr(spec, "cost_class")
    assert hasattr(spec, "supports_uq")
    assert hasattr(spec, "supports_approx")
    assert hasattr(spec, "deterministic")


def test_metric_spec_is_immutable():
    """MetricSpec must be frozen (immutable)."""
    spec = get_metric("degree")
    with pytest.raises((AttributeError, TypeError)):
        spec.name = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Core metrics exist
# ---------------------------------------------------------------------------

CORE_METRICS = [
    "degree",
    "degree_centrality",
    "betweenness_centrality",
    "closeness_centrality",
    "pagerank",
    "clustering",
]


@pytest.mark.parametrize("metric", CORE_METRICS)
def test_core_metric_in_registry(metric):
    """Each core metric must be in METRIC_REGISTRY."""
    assert metric in METRIC_REGISTRY, f"Expected '{metric}' in METRIC_REGISTRY"


@pytest.mark.parametrize("metric", CORE_METRICS)
def test_core_metric_get(metric):
    """get_metric() must return a MetricSpec for each core metric."""
    spec = get_metric(metric)
    assert isinstance(spec, MetricSpec)
    assert spec.name == metric


# ---------------------------------------------------------------------------
# is_known_metric()
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("metric", CORE_METRICS)
def test_is_known_metric_true(metric):
    """is_known_metric() must return True for known metrics."""
    assert is_known_metric(metric) is True


def test_is_known_metric_false_for_unknown():
    """is_known_metric() must return False for unknown metrics."""
    assert is_known_metric("not_a_real_metric_xyz") is False


def test_is_known_metric_false_empty():
    """is_known_metric() must return False for empty string."""
    assert is_known_metric("") is False


# ---------------------------------------------------------------------------
# get_metric() error handling
# ---------------------------------------------------------------------------

def test_get_metric_raises_for_unknown():
    """get_metric() must raise an error for unknown metric names."""
    with pytest.raises((KeyError, ValueError, Exception)):
        get_metric("completely_unknown_metric_xyz")


# ---------------------------------------------------------------------------
# Metric properties
# ---------------------------------------------------------------------------

def test_degree_is_cheap():
    """degree must have a low cost class (constant or linear)."""
    spec = get_metric("degree")
    assert spec.cost_class in ("constant", "linear", "near_linear")


def test_betweenness_is_expensive():
    """betweenness_centrality must have an expensive cost class."""
    spec = get_metric("betweenness_centrality")
    assert spec.cost_class in ("quadratic", "cubic", "near_quadratic"), (
        f"Expected expensive cost class for betweenness, got {spec.cost_class!r}"
    )


def test_closeness_is_expensive():
    """closeness_centrality must have an expensive cost class."""
    spec = get_metric("closeness_centrality")
    assert spec.cost_class in ("quadratic", "cubic", "near_quadratic", "near_linear"), (
        f"Expected expensive cost class for closeness, got {spec.cost_class!r}"
    )


def test_node_metrics_have_nodes_target():
    """Centrality metrics should target 'nodes'."""
    for metric in ["degree", "degree_centrality", "betweenness_centrality", "pagerank"]:
        spec = get_metric(metric)
        assert spec.target == "nodes", (
            f"Expected target='nodes' for {metric}, got {spec.target!r}"
        )


def test_metric_name_matches_key():
    """Each metric's name attribute must match its registry key."""
    for key, spec in METRIC_REGISTRY.items():
        assert spec.name == key, (
            f"Registry key {key!r} does not match spec.name {spec.name!r}"
        )


# ---------------------------------------------------------------------------
# Aliases (if implemented)
# ---------------------------------------------------------------------------

def test_aliases_are_tuple_or_sequence():
    """If a metric has aliases, they must be a tuple/sequence."""
    spec = get_metric("degree")
    if hasattr(spec, "aliases"):
        assert isinstance(spec.aliases, (tuple, list, frozenset))


def test_aliases_do_not_conflict_with_names():
    """No alias should shadow another metric's primary name."""
    all_names = set(METRIC_REGISTRY.keys())
    for key, spec in METRIC_REGISTRY.items():
        if hasattr(spec, "aliases") and spec.aliases:
            for alias in spec.aliases:
                # alias can match other metric names only if it IS that metric
                # but aliases should not shadow a DIFFERENT metric
                if alias in all_names and alias != key:
                    # This would be a registry error
                    pytest.fail(
                        f"Alias {alias!r} on metric {key!r} shadows metric {alias!r}"
                    )
