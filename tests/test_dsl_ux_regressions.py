"""Public DSL workflows reproduced during the usability stress test."""

from itertools import product

import pytest

from py3plex.core.multinet import multi_layer_network
from py3plex.core.temporal_multinet import TemporalMultiLayerNetwork
from py3plex.dsl import F, L, Q
from py3plex.dsl.ast import ast_from_json, ast_to_json
from py3plex.dsl.errors import DslExecutionError, UnknownAttributeError, UnknownLayerError


@pytest.fixture
def network():
    net = multi_layer_network(directed=False)
    net.add_edges(
        [
            ["a", "friends", "b", "friends", 4],
            ["a", "friends", "c", "friends", 3],
            ["a", "work", "d", "work", 2],
            ["d", "work", "e", "work", 1],
            ["a", "friends", "a", "work", 5],
        ],
        input_type="list",
    )
    return net


@pytest.mark.parametrize(
    "expression, oracle",
    [
        (lambda a, b, c: a & (b | c), lambda a, b, c: a and (b or c)),
        (lambda a, b, c: (a | b) & c, lambda a, b, c: (a or b) and c),
        (lambda a, b, c: a | (b & c), lambda a, b, c: a or (b and c)),
        (lambda a, b, c: a & ~b, lambda a, b, c: a and not b),
        (lambda a, b, c: ~a | b, lambda a, b, c: not a or b),
        (lambda a, b, c: ~(a | (b & c)), lambda a, b, c: not (a or (b and c))),
    ],
)
def test_boolean_builder_matches_python_truth_table(expression, oracle):
    net = multi_layer_network(directed=False)
    values = list(product((False, True), repeat=3))
    net.add_nodes([{"source": index, "type": "L"} for index in range(len(values))])
    for index, (a, b, c) in enumerate(values):
        net.core_network.nodes[index, "L"].update(a=a, b=b, c=c)

    condition = expression(F.a == True, F.b == True, F.c == True)  # noqa: E712
    query = Q.nodes().where(condition)
    expected = {(index, "L") for index, row in enumerate(values) if oracle(*row)}

    assert set(query.execute(net).items) == expected
    restored = Q.from_ast(ast_from_json(ast_to_json(query.to_ast())))
    assert set(restored.execute(net).items) == expected


def test_where_composes_without_mutating_the_original_expression(network):
    condition = (F.degree == 3) | (F.degree == 2)
    combined = Q.nodes().where(condition).where(layer="work")
    expected = {("a", "work"), ("d", "work")}

    assert set(combined.execute(network).items) == expected
    assert set(Q.nodes().where(condition).execute(network).items) == expected | {("a", "friends")}
    replayable = combined.provenance(mode="replayable", capture="snapshot").execute(network)
    assert set(replayable.replay().items) == expected


def test_where_resolves_computed_alias_before_limit(network):
    result = (
        Q.nodes()
        .compute("degree", alias="deg")
        .where((F.deg > 2) | (F.layer == "work"))
        .order_by("-deg")
        .limit(1)
        .execute(network)
    )
    assert result.items == [("a", "friends")]
    assert result.to_pandas().iloc[0]["deg"] == 3


def test_where_and_grouping_report_unknown_fields(network):
    with pytest.raises(UnknownAttributeError, match="Did you mean 'degree'"):
        Q.nodes().where(degre__gt=0).execute(network)
    with pytest.raises(UnknownAttributeError, match="Did you mean 'layer'"):
        Q.nodes().group_by("layre").top_k(1, "degree").execute(network)


@pytest.mark.parametrize("layers", [L["friends"] | L["freinds"], L["friends | freinds"]])
def test_coverage_reports_a_misspelled_layer(network, layers):
    with pytest.raises(UnknownLayerError, match="Did you mean 'friends'"):
        Q.nodes().from_layers(layers).per_layer().coverage(mode="all").execute(network)


@pytest.mark.parametrize("coverage", [{"mode": "all"}, {"mode": "fraction", "p": 0.75}])
def test_coverage_retains_empty_selected_layers(network, coverage):
    layers = L["friends"] | L["work"]
    query = Q.nodes().from_layers(layers).per_layer()
    assert set(query.coverage(mode="all").execute(network).items) == {("a", "friends"), ("a", "work")}

    query.where(layer="friends").coverage(**coverage)
    assert query.execute(network).items == []


def test_temporal_queries_use_the_network_and_its_time_attribute():
    net = TemporalMultiLayerNetwork(time_attribute="observed_at")
    net.add_edge("a", "friends", "b", "friends", 10)
    net.add_edge("b", "friends", "c", "friends", 11)
    net.add_edge("c", "friends", "d", "friends", 20)

    assert Q.edges().execute(net).count == 3
    result = Q.edges().from_layers(L["friends"]).during(8, 12).execute(net)
    assert set(result.to_pandas()["target"]) == {"b", "c"}
    assert Q.edges().at(10).execute(net).count == 1
    replayable = Q.edges().during(8, 12).provenance(mode="replayable", capture="snapshot")
    assert replayable.execute(net).replay().items == result.items
    with pytest.raises(DslExecutionError, match="start time at or before"):
        Q.edges().during(12, 8).execute(net)


def test_global_top_k_uses_requested_key_as_primary_order(network):
    query = Q.nodes().order_by("degree", "layer").per_layer().coverage(mode="all")
    result = query.top_k_global(1, "degree").execute(network)
    assert result.items == [("a", "friends")]


def test_neighbor_explanation_uses_parallel_edge_weights(network):
    network.add_edges([["a", "friends", "b", "friends", 7]], input_type="list")
    result = (
        Q.nodes().where(id="a", layer="friends")
        .explain(neighbors_top=3)
        .execute(network)
    )
    neighbors = result.to_pandas().iloc[0]["top_neighbors"]
    assert [(neighbor["neighbor_id"], neighbor["edge_weight"]) for neighbor in neighbors] == [
        ("b", 7), ("a", 5), ("c", 3)
    ]


def test_edge_hint_suggests_runnable_edge_operations(network, capsys):
    query = Q.edges().where(weight__gt=1).hint()
    hints = capsys.readouterr().out
    assert '.compute("edge_betweenness_centrality")' in hints
    assert '.per_layer_pair()' in hints
    assert query.compute("edge_betweenness_centrality").execute(network).count == 4


def test_empty_edge_export_keeps_the_result_columns(network):
    result = Q.edges().where(weight__gt=100).execute(network)
    assert result.to_pandas().columns.tolist() == [
        "source", "source_layer", "target", "target_layer", "weight",
    ]
