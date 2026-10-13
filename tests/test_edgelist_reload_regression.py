"""Regression coverage for reloading the public edge-list export."""

import gzip

import pytest

from py3plex.core import multinet, parsers


@pytest.mark.parametrize("directed", [False, True])
def test_public_edgelist_export_reload(tmp_path, directed):
    network = multinet.multi_layer_network(directed=directed)
    network.add_edges([
        ["a", "social", "b", "social", 1],
        ["a", "work", "c", "work", 1],
        ["a", "social", "a", "work", 1],
        ["b", "social", "b", "social", 1],
    ], input_type="list")
    path = tmp_path / "network.edgelist"
    network.save_network(str(path), output_type="edgelist")
    restored = multinet.multi_layer_network(directed=directed)
    restored.load_network(str(path), input_type="edgelist", directed=directed)
    assert set(restored.core_network) == set(network.core_network)
    expected = {(u, v) if directed else frozenset((u, v))
                for u, v in network.core_network.edges()}
    actual = {(u, v) if directed else frozenset((u, v))
              for u, v in restored.core_network.edges()}
    assert actual == expected
    assert restored.core_network.is_directed() == directed
    assert all(data["type"] == layer
               for (_, layer), data in restored.core_network.nodes(data=True))


@pytest.mark.parametrize("compressed", [False, True])
@pytest.mark.parametrize("directed", [False, True])
def test_mixed_legacy_and_multilayer_rows(tmp_path, compressed, directed):
    text = "# comment\n\na b\nb c 2.5\nx L1 y L2\ny L2 z L2 -3.5\nz L2 z L2 0\n"
    path = tmp_path / ("edges.gz" if compressed else "edges.txt")
    if compressed:
        with gzip.open(path, "wt") as handle:
            handle.write(text)
    else:
        path.write_text(text)
    graph, labels = parsers.parse_simple_edgelist(str(path), directed)
    expected = {
        (("a", "null"), ("b", "null")): 1.0,
        (("b", "null"), ("c", "null")): 2.5,
        (("x", "L1"), ("y", "L2")): 1.0,
        (("y", "L2"), ("z", "L2")): -3.5,
        (("z", "L2"), ("z", "L2")): 0.0,
    }
    assert graph.number_of_edges() == len(expected)
    for (u, v), weight in expected.items():
        assert graph[u][v]["weight"] == weight
        if directed and u != v:
            assert not graph.has_edge(v, u)
    assert graph.is_directed() == directed
    assert labels is None
    assert all(data["type"] == layer for (_, layer), data in graph.nodes(data=True))
