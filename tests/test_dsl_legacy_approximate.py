"""Focused legacy DSL tests for APPROXIMATE parsing and execution paths."""

from __future__ import annotations

import pytest

from py3plex.core import multinet
from py3plex.dsl_legacy import DSLSyntaxError, _parse_approx_kwargs, execute_query


@pytest.fixture
def tiny_network():
    network = multinet.multi_layer_network(directed=False)
    network.add_edges(
        [
            {
                "source": "A",
                "target": "B",
                "source_type": "social",
                "target_type": "social",
                "weight": 1.0,
            },
            {
                "source": "B",
                "target": "C",
                "source_type": "social",
                "target_type": "social",
                "weight": 2.0,
            },
            {
                "source": "A",
                "target": "C",
                "source_type": "social",
                "target_type": "social",
                "weight": 1.5,
            },
        ]
    )
    return network


def test_parse_approx_kwargs_parses_numbers_and_strings() -> None:
    tokens = [
        "method",
        "=",
        '"sampling"',
        ",",
        "n_samples",
        "=",
        "128",
        ",",
        "tol",
        "=",
        "1e-6",
    ]

    parsed = _parse_approx_kwargs(tokens)

    assert parsed["method"] == "sampling"
    assert parsed["n_samples"] == 128
    assert parsed["tol"] == pytest.approx(1e-6)


def test_execute_query_supports_approximate_keyword_without_kwargs(
    tiny_network,
) -> None:
    result = execute_query(
        tiny_network,
        "SELECT nodes COMPUTE betweenness_centrality APPROXIMATE",
    )
    assert result["target"] == "nodes"
    assert "computed" in result
    assert "betweenness_centrality" in result["computed"]
    assert len(result["computed"]["betweenness_centrality"]) > 0


def test_execute_query_supports_approximate_kwargs(tiny_network) -> None:
    result = execute_query(
        tiny_network,
        (
            'SELECT nodes COMPUTE betweenness_centrality '
            'APPROXIMATE(method="sampling", n_samples=16, seed=42)'
        ),
    )
    assert result["target"] == "nodes"
    assert "computed" in result
    assert "betweenness_centrality" in result["computed"]
    assert len(result["computed"]["betweenness_centrality"]) > 0


def test_execute_query_passes_approximate_params_to_compute(
    tiny_network, monkeypatch
) -> None:
    captured = {}

    def _capture_compute_measure(network, measure, nodes=None, approx_spec=None):
        captured["measure"] = measure
        captured["approx_spec"] = approx_spec
        if nodes is None:
            nodes = []
        return {node: 0.0 for node in nodes}

    monkeypatch.setattr(
        "py3plex.dsl_legacy._compute_measure",
        _capture_compute_measure,
    )

    execute_query(
        tiny_network,
        (
            'SELECT nodes COMPUTE degree '
            'APPROXIMATE(method="sampling", n_samples=16, seed=42)'
        ),
    )

    assert captured["measure"] == "degree"
    assert captured["approx_spec"]["enabled"] is True
    assert captured["approx_spec"]["method"] == "sampling"
    assert captured["approx_spec"]["params"]["n_samples"] == 16
    assert captured["approx_spec"]["params"]["seed"] == 42


def test_execute_query_rejects_too_short_query(tiny_network) -> None:
    with pytest.raises(DSLSyntaxError, match="requires a target"):
        execute_query(tiny_network, "SELECT")
