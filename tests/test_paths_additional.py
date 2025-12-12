"""Additional tests for py3plex.paths."""

import networkx as nx
import pytest

from py3plex.core import multinet
from py3plex.paths import find_paths
from py3plex.paths.algorithms import (
    _find_all_nodes_by_name,
    _find_node_by_name,
    random_walk,
)
from py3plex.paths.result import PathResult


@pytest.fixture
def simple_network():
    """Tiny multilayer network reused across tests."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_edges(
        [
            ["n1", "L1", "n2", "L1", 1.0],
            ["n2", "L1", "n3", "L1", 1.0],
        ],
        input_type="list",
    )
    return net


def test_find_paths_captures_algorithm_error(simple_network):
    """Errors from algorithms should be propagated into PathResult.meta."""
    result = find_paths(
        simple_network,
        source="missing",
        target="n1",
        path_type="shortest",
    )

    assert result.paths == []
    assert "error" in result.meta
    assert "Source node 'missing'" in result.meta["error"]


def test_random_walk_blocks_cross_layer_moves():
    """When cross_layer=False and layers specified, neighbors outside layers are ignored."""
    G = nx.Graph()
    source = ("A", "L1")
    other = ("B", "L2")
    G.add_edge(source, other)

    result = random_walk(
        G,
        source="A",
        steps=8,
        layers=["L1"],
        cross_layer=False,
        seed=123,
    )

    assert set(result["visit_frequency"]) == {source}
    # Walk path should never leave the allowed layer
    assert set(result["paths"][0]) == {source}


def test_find_node_helpers_support_layered_and_plain_nodes():
    """_find_node_by_name should locate tuple nodes and plain nodes."""
    G = nx.Graph()
    layered = ("x", "L1")
    plain = "x"
    G.add_nodes_from([layered, plain, ("y", "L2")])

    first_match = _find_node_by_name(G, "x")
    all_matches = _find_all_nodes_by_name(G, "x")

    assert first_match in {layered, plain}
    assert set(all_matches) == {layered, plain}


def test_path_result_to_pandas_formats_paths():
    """to_pandas should produce readable path strings."""
    paths = [["a", "b", "c"]]
    result = PathResult(
        path_type="all",
        source="a",
        target="c",
        paths=paths,
    )

    df = result.to_pandas()

    assert list(df.columns) == ["path_id", "path_length", "path"]
    assert df.loc[0, "path_length"] == 2
    assert df.loc[0, "path"] == "a -> b -> c"


def test_path_result_to_pandas_visit_frequency_handles_values():
    """to_pandas_visit_frequency should emit rows for stored frequencies."""
    result = PathResult(
        path_type="random_walk",
        source="s",
        visit_frequency={("n1", "L1"): 0.6, ("n2", "L2"): 0.4},
    )

    df = result.to_pandas_visit_frequency()

    assert set(df.columns) == {"node", "frequency"}
    assert set(df["node"]) == {("n1", "L1"), ("n2", "L2")}
    assert pytest.approx(df["frequency"].sum()) == 1.0
