"""Arrow schema round trips preserve scalar identity and legacy string IDs."""

import json

import pytest

pa = pytest.importorskip("pyarrow")

from py3plex.io import Edge, Layer, MultiLayerGraph, Node, read, write
from py3plex.io.formats.arrow_format import _arrow_tables_to_graph


@pytest.mark.parametrize(
    "identifiers",
    [(1, "1"), (False, "False"), (1.25, "1.25"), (None, "null"), ("[1,2]", '{"x":1}')],
)
@pytest.mark.parametrize("format_name", ["arrow", "parquet"])
def test_arrow_preserves_scalar_node_and_layer_identity(
    tmp_path, identifiers, format_name
):
    graph = MultiLayerGraph(directed=True, attributes={"seed": 42})
    for index, identifier in enumerate(identifiers):
        graph.add_layer(Layer(id=identifier, attributes={"index": index}))
        graph.add_node(Node(id=identifier, attributes={"index": index}))
    graph.add_edge(
        Edge(
            src=identifiers[0],
            dst=identifiers[1],
            src_layer=identifiers[0],
            dst_layer=identifiers[1],
            key=0,
            attributes={"weight": 2.5},
        )
    )
    path = tmp_path / ("ids." + format_name)
    write(graph, path, format=format_name)
    restored = read(path, format=format_name)
    assert restored == graph
    assert [type(identifier) for identifier in restored.nodes] == [
        type(identifier) for identifier in identifiers
    ]
    assert [type(identifier) for identifier in restored.layers] == [
        type(identifier) for identifier in identifiers
    ]


def test_legacy_arrow_tables_keep_literal_string_ids():
    # Legacy exports did not declare an identifier encoding; JSON-looking IDs
    # in such files are literal strings, including "null" and numeric names.
    tables = {
        "metadata": pa.table({"directed": [True], "attributes": ["{}"]}),
        "nodes": pa.table({"id": ["null", "1"], "attributes": ["{}", "{}"]}),
        "layers": pa.table({"id": ["true", "1"], "attributes": ["{}", "{}"]}),
        "edges": pa.table(
            {
                "src": ["null"],
                "dst": ["1"],
                "src_layer": ["true"],
                "dst_layer": ["1"],
                "key": [0],
                "attributes": [json.dumps({"weight": 2})],
            }
        ),
    }
    restored = _arrow_tables_to_graph(tables)
    assert set(restored.nodes) == {"null", "1"}
    assert set(restored.layers) == {"true", "1"}
    edge = restored.edges[0]
    assert (edge.src, edge.dst, edge.src_layer, edge.dst_layer) == (
        "null",
        "1",
        "true",
        "1",
    )
    assert edge.attributes == {"weight": 2}
