"""Additional correctness tests for py3plex.io contracts and algorithms."""

import networkx as nx
import pytest

from py3plex.io.api import _detect_format
from py3plex.io.converters import to_networkx
from py3plex.io.exceptions import SchemaValidationError
from py3plex.io.api import read, write
from py3plex.io.formats.csv_format import read_csv, write_csv
from py3plex.io.schema import Edge, Layer, MultiLayerGraph, Node


def _simple_graph_with_layers() -> MultiLayerGraph:
    graph = MultiLayerGraph()
    graph.add_layer(Layer(id="l1"))
    graph.add_layer(Layer(id="l2"))
    graph.add_node(Node(id="A"))
    graph.add_node(Node(id="B"))
    return graph


def test_detect_format_handles_compressed_and_parquet_extensions(tmp_path):
    """_detect_format should map compressed and parquet extensions correctly."""
    compressed = tmp_path / "graph.csv.gz"
    compressed.touch()
    parquet = tmp_path / "graph.parquet"
    parquet.touch()

    assert _detect_format(compressed) == "csv"
    assert _detect_format(parquet) == "parquet"


def test_to_networkx_intersection_only_keeps_edges_present_in_all_layers():
    """Intersection mode should keep only intra-layer edges appearing in every layer."""
    graph = _simple_graph_with_layers()

    # Edge present in both layers
    graph.add_edge(Edge(src="A", dst="B", src_layer="l1", dst_layer="l1"))
    graph.add_edge(Edge(src="A", dst="B", src_layer="l2", dst_layer="l2"))
    # Edge only in one layer should be discarded
    graph.add_edge(Edge(src="B", dst="A", src_layer="l1", dst_layer="l1"))
    # Inter-layer edge should be ignored for intersection
    graph.add_edge(Edge(src="A", dst="A", src_layer="l1", dst_layer="l2"))

    G = to_networkx(graph, mode="intersection")

    assert isinstance(G, (nx.MultiGraph, nx.MultiDiGraph))
    assert G.number_of_edges() == 1
    assert ("A", "B") in {(u, v) for u, v in G.edges()}


def test_to_networkx_union_undirected_does_not_drop_reversed_edges():
    """Union mode should not drop edges if the same undirected pair is (u,v) vs (v,u)."""
    graph = MultiLayerGraph(directed=False)
    graph.add_layer(Layer(id="l1"))
    graph.add_layer(Layer(id="l2"))
    graph.add_node(Node(id="A"))
    graph.add_node(Node(id="B"))
    graph.add_edge(Edge(src="A", dst="B", src_layer="l1", dst_layer="l1"))
    graph.add_edge(Edge(src="B", dst="A", src_layer="l2", dst_layer="l2"))

    G = to_networkx(graph, mode="union")

    assert isinstance(G, nx.MultiGraph)
    assert G.number_of_edges() == 2
    assert {(u, v) for u, v, _k in G.edges(keys=True)} == {("A", "B")}
    assert {k for _u, _v, k in G.edges(keys=True)} == {0, 1}


def test_to_networkx_intersection_undirected_treats_reversed_edges_as_same():
    """Intersection mode should treat (u,v) and (v,u) as the same edge for undirected graphs."""
    graph = MultiLayerGraph(directed=False)
    graph.add_layer(Layer(id="l1"))
    graph.add_layer(Layer(id="l2"))
    graph.add_node(Node(id="A"))
    graph.add_node(Node(id="B"))

    graph.add_edge(Edge(src="A", dst="B", src_layer="l1", dst_layer="l1"))
    graph.add_edge(Edge(src="B", dst="A", src_layer="l2", dst_layer="l2"))

    G = to_networkx(graph, mode="intersection")

    assert isinstance(G, nx.MultiGraph)
    assert G.number_of_edges() == 1
    assert ("A", "B") in {(u, v) for u, v in G.edges()}


def test_csv_gzip_roundtrip_via_api(tmp_path):
    """`.csv.gz` should be treated as gzip-compressed CSV by the CSV format implementation."""
    graph = MultiLayerGraph()
    graph.add_layer(Layer(id="l1"))
    graph.add_node(Node(id="A"))
    graph.add_node(Node(id="B"))
    graph.add_edge(Edge(src="A", dst="B", src_layer="l1", dst_layer="l1", attributes={"weight": 1.25}))

    path = tmp_path / "graph.csv.gz"
    write(graph, path)
    loaded = read(path)

    assert len(loaded.nodes) == 2
    assert len(loaded.layers) == 1
    assert len(loaded.edges) == 1
    assert loaded.edges[0].attributes["weight"] == pytest.approx(1.25)


def test_csv_roundtrip_numeric_attributes_and_sidecars(tmp_path):
    """Numeric edge attributes should survive CSV round-trip with deterministic ordering."""
    graph = _simple_graph_with_layers()
    graph.nodes["A"].attributes["label"] = "alpha"
    graph.layers["l1"].attributes["kind"] = "base"
    graph.add_edge(
        Edge(
            src="A",
            dst="B",
            src_layer="l1",
            dst_layer="l1",
            attributes={"weight": 1.5, "count": 2},
        )
    )

    edge_path = tmp_path / "graph.csv"
    write_csv(
        graph,
        edge_path,
        deterministic=True,
        write_sidecars=True,
    )

    loaded = read_csv(
        edge_path,
        nodes_file=edge_path.parent / "nodes.csv",
        layers_file=edge_path.parent / "layers.csv",
    )

    assert loaded.edges[0].attributes["weight"] == pytest.approx(1.5)
    assert loaded.edges[0].attributes["count"] == 2
    assert (edge_path.parent / "nodes.csv").exists()
    assert (edge_path.parent / "layers.csv").exists()


def test_csv_missing_required_columns_raises_validation_error(tmp_path):
    """CSV reader should reject files without required headers."""
    bad_path = tmp_path / "bad.csv"
    bad_path.write_text("src,dst\nA,B\n")

    with pytest.raises(SchemaValidationError, match="required columns"):
        read_csv(bad_path)


def test_from_dict_rejects_duplicate_edges():
    """Duplicate edges in serialized data should raise during reconstruction."""
    data = {
        "nodes": [{"id": "A", "attributes": {}}, {"id": "B", "attributes": {}}],
        "layers": [{"id": "l1", "attributes": {}}],
        "edges": [
            {
                "src": "A",
                "dst": "B",
                "src_layer": "l1",
                "dst_layer": "l1",
                "key": 0,
                "attributes": {},
            },
            {
                "src": "A",
                "dst": "B",
                "src_layer": "l1",
                "dst_layer": "l1",
                "key": 0,
                "attributes": {},
            },
        ],
        "directed": True,
        "attributes": {},
    }

    with pytest.raises(SchemaValidationError, match="Duplicate edge"):
        MultiLayerGraph.from_dict(data)


def test_property_union_projection_never_drops_edges():
    """Property: union projection returns exactly as many edges as the source graph."""
    hypothesis = pytest.importorskip("hypothesis")
    st = pytest.importorskip("hypothesis.strategies")

    @hypothesis.given(
        directed=st.booleans(),
        n_nodes=st.integers(min_value=1, max_value=4),
        n_layers=st.integers(min_value=1, max_value=3),
        edge_specs=st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=3),
                st.integers(min_value=0, max_value=3),
                st.integers(min_value=0, max_value=2),
                st.integers(min_value=0, max_value=2),
            ),
            min_size=0,
            max_size=12,
        ),
    )
    @hypothesis.settings(max_examples=50)
    def check(directed, n_nodes, n_layers, edge_specs):
        graph = MultiLayerGraph(directed=directed)
        for node_id in range(n_nodes):
            graph.add_node(Node(id=node_id))
        for layer_id in range(n_layers):
            graph.add_layer(Layer(id=layer_id))

        seen = set()
        for src, dst, src_layer, dst_layer in edge_specs:
            if src >= n_nodes or dst >= n_nodes or src_layer >= n_layers or dst_layer >= n_layers:
                continue
            edge = Edge(
                src=src,
                dst=dst,
                src_layer=src_layer,
                dst_layer=dst_layer,
                key=0,
                attributes={},
            )
            if edge.edge_tuple() in seen:
                continue
            graph.add_edge(edge)
            seen.add(edge.edge_tuple())

        G = to_networkx(graph, mode="union")
        assert G.number_of_edges() == len(graph.edges)

    check()
