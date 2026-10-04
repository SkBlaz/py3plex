"""End-to-end coverage for optimizer behavior through the DSL API."""

import pytest

from py3plex.core import multinet
from py3plex.dsl import L, Param, Q
from py3plex.dsl.errors import ParameterMissingError
from py3plex.optimizer.logical_plan import LogicalPlanBuilder
from py3plex.optimizer.rules import render_logical_plan


@pytest.fixture
def multilayer_network():
    network = multinet.multi_layer_network(directed=False)
    network.add_edges(
        [
            {
                "source": "a",
                "target": "b",
                "source_type": "social",
                "target_type": "social",
                "weight": 1.0,
            },
            {
                "source": "a",
                "target": "c",
                "source_type": "social",
                "target_type": "social",
                "weight": 2.0,
            },
            {
                "source": "b",
                "target": "c",
                "source_type": "work",
                "target_type": "work",
                "weight": 3.0,
            },
            {
                "source": "c",
                "target": "d",
                "source_type": "work",
                "target_type": "work",
                "weight": 4.0,
            },
        ]
    )
    return network


def test_dsl_execution_explain_and_provenance_integrate_rewrites(
    multilayer_network,
):
    query = (
        Q.nodes()
        .from_layers(L["social"] + L["work"])
        .where(degree__gte=1)
        .compute("degree", "degree")
        .order_by("degree", desc=True)
        .limit(3)
    )

    baseline = query.execute(
        multilayer_network, optimize=False, progress=False
    )
    optimized = query.execute(
        multilayer_network, optimize=True, progress=False
    )

    assert optimized.items == baseline.items
    assert optimized.attributes == baseline.attributes
    assert optimized.meta["optimizer"]["enabled"] is True
    assert "R006" in optimized.meta["optimizer"]["rule_ids_applied"]
    assert (
        optimized.meta["optimizer"]["original_plan_hash"]
        != optimized.meta["optimizer"]["optimized_plan_hash"]
    )
    assert (
        optimized.meta["provenance"]["optimizer"]["optimized_plan_hash"]
        == optimized.meta["optimizer"]["optimized_plan_hash"]
    )

    explanation = query.execute(
        multilayer_network, explain_plan=True, progress=False
    ).explain_plan()
    assert "layers=['social', 'work']" in explanation["original_logical_plan"]
    assert "Compute[" in explanation["original_logical_plan"]
    assert "R006" in explanation["optimization_trace"]["rules_applied"]
    assert (
        explanation["optimized_logical_plan"]
        != explanation["original_logical_plan"]
    )


def test_parameterized_limit_executes_with_and_without_optimizer(
    multilayer_network,
):
    query = Q.nodes().compute("degree").order_by("degree", desc=True).limit(
        Param.int("count")
    )

    baseline = query.execute(
        multilayer_network, count=2, optimize=False, progress=False
    )
    optimized = query.execute(
        multilayer_network, count=2, optimize=True, progress=False
    )

    assert optimized.items == baseline.items
    assert optimized.attributes == baseline.attributes
    with pytest.raises(ParameterMissingError, match="count"):
        query.execute(multilayer_network, optimize=True, progress=False)


def test_edge_query_optimizer_mode_preserves_public_results(multilayer_network):
    query = Q.edges().from_layers(L["social"]).limit(1)

    baseline = query.execute(
        multilayer_network, optimize=False, progress=False
    )
    optimized = query.execute(
        multilayer_network, optimize=True, progress=False
    )

    assert optimized.items == baseline.items
    assert optimized.attributes == baseline.attributes


def test_wildcard_layer_is_not_misrepresented_as_a_literal_layer():
    plan = LogicalPlanBuilder(Q.nodes().from_layers(L["*"]).to_ast()).build()

    assert render_logical_plan(plan) == "Scan[nodes]"
