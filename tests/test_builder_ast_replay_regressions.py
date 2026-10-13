"""Builder reconstruction must retain summary, ranking and selection stages."""

import networkx as nx
import pandas as pd
import pytest

from py3plex.core.multinet import multi_layer_network
from py3plex.dsl import Q


BUILDERS = [
    pytest.param(lambda: Q.nodes().compute("degree").summarize(total="sum(degree)"), id="summary"),
    pytest.param(lambda: Q.nodes().compute("degree").rank_by("degree"), id="rank"),
    pytest.param(lambda: Q.nodes().compute("degree").zscore("degree"), id="zscore"),
    pytest.param(lambda: Q.nodes().compute("degree").tail(1), id="selection"),
    pytest.param(lambda: Q.nodes().embed(dim=2, seed=42, cache=False), id="embedding"),
]


@pytest.mark.parametrize("build", BUILDERS)
def test_builder_roundtrip_preserves_all_select_fields(build):
    ast = build().to_ast()
    restored = Q.from_ast(ast).to_ast()
    assert restored.select == ast.select


@pytest.mark.parametrize("build", BUILDERS)
def test_reconstructed_builder_has_identical_results(build):
    network = multi_layer_network(directed=False)
    network.core_network = nx.path_graph([("a", "L"), ("b", "L"), ("c", "L")])
    original = build()
    replayed = Q.from_ast(original.to_ast())
    expected = original.execute(network)
    actual = replayed.execute(network)
    print(expected)
    print(actual)
    pd.testing.assert_frame_equal(actual.to_pandas(), expected.to_pandas())
