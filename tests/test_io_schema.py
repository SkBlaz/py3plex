"""
Tests for the I/O module - Core Schema and Validation (Task Set 1).
"""

import json
import tempfile
import unittest
from pathlib import Path

import pytest

from py3plex.exceptions import Py3plexIOError
from py3plex.io import (
    Edge,
    FormatUnsupportedError,
    Layer,
    MultiLayerGraph,
    Node,
    ReferentialIntegrityError,
    SchemaValidationError,
    read,
    register_reader,
    register_writer,
    supported_formats,
    write,
)

# Check library availability for conditional tests
try:
    import igraph  # noqa: F401
    HAS_IGRAPH = True
except ImportError:
    HAS_IGRAPH = False


class TestNode(unittest.TestCase):
    """Test Node dataclass and validation."""

    def test_node_creation(self):
        """Test basic node creation."""
        node = Node(id="n1", attributes={"label": "Node 1"})
        assert node.id == "n1"
        assert node.attributes == {"label": "Node 1"}

    def test_node_empty_attributes(self):
        """Test node with no attributes."""
        node = Node(id="n1")
        assert node.id == "n1"
        assert node.attributes == {}

    def test_node_json_serializable_attributes(self):
        """Test node with JSON-serializable attributes."""
        node = Node(
            id="n1",
            attributes={
                "name": "test",
                "value": 42,
                "active": True,
                "tags": ["a", "b"],
            },
        )
        # Should not raise
        assert node.attributes["name"] == "test"

    def test_node_non_json_serializable_attributes(self):
        """Test node with non-JSON-serializable attributes raises error."""
        with pytest.raises(SchemaValidationError, match="not JSON-serializable"):
            Node(id="n1", attributes={"func": lambda x: x})

    def test_node_to_dict(self):
        """Test node serialization to dict."""
        node = Node(id="n1", attributes={"label": "Node 1"})
        data = node.to_dict()
        assert data == {"id": "n1", "attributes": {"label": "Node 1"}}

    def test_node_from_dict(self):
        """Test node deserialization from dict."""
        data = {"id": "n1", "attributes": {"label": "Node 1"}}
        node = Node.from_dict(data)
        assert node.id == "n1"
        assert node.attributes == {"label": "Node 1"}


class TestLayer(unittest.TestCase):
    """Test Layer dataclass and validation."""

    def test_layer_creation(self):
        """Test basic layer creation."""
        layer = Layer(id="l1", attributes={"name": "Layer 1"})
        assert layer.id == "l1"
        assert layer.attributes == {"name": "Layer 1"}

    def test_layer_empty_attributes(self):
        """Test layer with no attributes."""
        layer = Layer(id="l1")
        assert layer.id == "l1"
        assert layer.attributes == {}

    def test_layer_non_json_serializable_attributes(self):
        """Test layer with non-JSON-serializable attributes raises error."""
        with pytest.raises(SchemaValidationError, match="not JSON-serializable"):
            Layer(id="l1", attributes={"obj": object()})

    def test_layer_to_dict(self):
        """Test layer serialization to dict."""
        layer = Layer(id="l1", attributes={"name": "Layer 1"})
        data = layer.to_dict()
        assert data == {"id": "l1", "attributes": {"name": "Layer 1"}}

    def test_layer_from_dict(self):
        """Test layer deserialization from dict."""
        data = {"id": "l1", "attributes": {"name": "Layer 1"}}
        layer = Layer.from_dict(data)
        assert layer.id == "l1"
        assert layer.attributes == {"name": "Layer 1"}


class TestEdge(unittest.TestCase):
    """Test Edge dataclass and validation."""

    def test_edge_creation(self):
        """Test basic edge creation."""
        edge = Edge(src="n1", dst="n2", src_layer="l1", dst_layer="l1")
        assert edge.src == "n1"
        assert edge.dst == "n2"
        assert edge.src_layer == "l1"
        assert edge.dst_layer == "l1"
        assert edge.key == 0

    def test_edge_with_key(self):
        """Test edge with custom key."""
        edge = Edge(src="n1", dst="n2", src_layer="l1", dst_layer="l1", key=5)
        assert edge.key == 5

    def test_edge_with_attributes(self):
        """Test edge with attributes."""
        edge = Edge(
            src="n1",
            dst="n2",
            src_layer="l1",
            dst_layer="l1",
            attributes={"weight": 2.5},
        )
        assert edge.attributes == {"weight": 2.5}

    def test_edge_non_json_serializable_attributes(self):
        """Test edge with non-JSON-serializable attributes raises error."""
        with pytest.raises(SchemaValidationError, match="not JSON-serializable"):
            Edge(
                src="n1",
                dst="n2",
                src_layer="l1",
                dst_layer="l1",
                attributes={"set": {1, 2, 3}},
            )

    def test_edge_to_dict(self):
        """Test edge serialization to dict."""
        edge = Edge(
            src="n1",
            dst="n2",
            src_layer="l1",
            dst_layer="l1",
            key=1,
            attributes={"weight": 1.0},
        )
        data = edge.to_dict()
        assert data == {
            "src": "n1",
            "dst": "n2",
            "src_layer": "l1",
            "dst_layer": "l1",
            "key": 1,
            "attributes": {"weight": 1.0},
        }

    def test_edge_from_dict(self):
        """Test edge deserialization from dict."""
        data = {
            "src": "n1",
            "dst": "n2",
            "src_layer": "l1",
            "dst_layer": "l1",
            "key": 1,
            "attributes": {"weight": 1.0},
        }
        edge = Edge.from_dict(data)
        assert edge.src == "n1"
        assert edge.dst == "n2"
        assert edge.key == 1
        assert edge.attributes == {"weight": 1.0}

    def test_edge_tuple(self):
        """Test edge_tuple method."""
        edge = Edge(src="n1", dst="n2", src_layer="l1", dst_layer="l2", key=3)
        assert edge.edge_tuple() == ("n1", "n2", "l1", "l2", 3)


class TestMultiLayerGraph(unittest.TestCase):
    """Test MultiLayerGraph dataclass and validation."""

    def test_empty_graph(self):
        """Test empty graph creation."""
        graph = MultiLayerGraph()
        assert len(graph.nodes) == 0
        assert len(graph.layers) == 0
        assert len(graph.edges) == 0
        assert graph.directed is True

    def test_add_node(self):
        """Test adding nodes to graph."""
        graph = MultiLayerGraph()
        node = Node(id="n1")
        graph.add_node(node)
        assert "n1" in graph.nodes
        assert graph.nodes["n1"] == node

    def test_add_duplicate_node(self):
        """Test adding duplicate node raises error."""
        graph = MultiLayerGraph()
        graph.add_node(Node(id="n1"))
        with pytest.raises(SchemaValidationError, match="already exists"):
            graph.add_node(Node(id="n1"))

    def test_add_layer(self):
        """Test adding layers to graph."""
        graph = MultiLayerGraph()
        layer = Layer(id="l1")
        graph.add_layer(layer)
        assert "l1" in graph.layers
        assert graph.layers["l1"] == layer

    def test_add_duplicate_layer(self):
        """Test adding duplicate layer raises error."""
        graph = MultiLayerGraph()
        graph.add_layer(Layer(id="l1"))
        with pytest.raises(SchemaValidationError, match="already exists"):
            graph.add_layer(Layer(id="l1"))

    def test_add_edge_success(self):
        """Test adding valid edge to graph."""
        graph = MultiLayerGraph()
        graph.add_node(Node(id="n1"))
        graph.add_node(Node(id="n2"))
        graph.add_layer(Layer(id="l1"))

        edge = Edge(src="n1", dst="n2", src_layer="l1", dst_layer="l1")
        graph.add_edge(edge)
        assert len(graph.edges) == 1
        assert graph.edges[0] == edge

    def test_add_edge_missing_source_node(self):
        """Test adding edge with missing source node raises error."""
        graph = MultiLayerGraph()
        graph.add_node(Node(id="n2"))
        graph.add_layer(Layer(id="l1"))

        edge = Edge(src="n1", dst="n2", src_layer="l1", dst_layer="l1")
        with pytest.raises(ReferentialIntegrityError, match="non-existent source node"):
            graph.add_edge(edge)

    def test_add_edge_missing_destination_node(self):
        """Test adding edge with missing destination node raises error."""
        graph = MultiLayerGraph()
        graph.add_node(Node(id="n1"))
        graph.add_layer(Layer(id="l1"))

        edge = Edge(src="n1", dst="n2", src_layer="l1", dst_layer="l1")
        with pytest.raises(
            ReferentialIntegrityError, match="non-existent destination node"
        ):
            graph.add_edge(edge)

    def test_add_edge_missing_source_layer(self):
        """Test adding edge with missing source layer raises error."""
        graph = MultiLayerGraph()
        graph.add_node(Node(id="n1"))
        graph.add_node(Node(id="n2"))
        graph.add_layer(Layer(id="l2"))

        edge = Edge(src="n1", dst="n2", src_layer="l1", dst_layer="l2")
        with pytest.raises(
            ReferentialIntegrityError, match="non-existent source layer"
        ):
            graph.add_edge(edge)

    def test_add_edge_missing_destination_layer(self):
        """Test adding edge with missing destination layer raises error."""
        graph = MultiLayerGraph()
        graph.add_node(Node(id="n1"))
        graph.add_node(Node(id="n2"))
        graph.add_layer(Layer(id="l1"))

        edge = Edge(src="n1", dst="n2", src_layer="l1", dst_layer="l2")
        with pytest.raises(
            ReferentialIntegrityError, match="non-existent destination layer"
        ):
            graph.add_edge(edge)

    def test_add_duplicate_edge(self):
        """Test adding duplicate edge raises error."""
        graph = MultiLayerGraph()
        graph.add_node(Node(id="n1"))
        graph.add_node(Node(id="n2"))
        graph.add_layer(Layer(id="l1"))

        edge1 = Edge(src="n1", dst="n2", src_layer="l1", dst_layer="l1")
        edge2 = Edge(src="n1", dst="n2", src_layer="l1", dst_layer="l1")

        graph.add_edge(edge1)
        with pytest.raises(SchemaValidationError, match="Duplicate edge"):
            graph.add_edge(edge2)

    def test_graph_validation_on_init(self):
        """Test graph validation during initialization."""
        # Create graph with invalid reference
        with pytest.raises(ReferentialIntegrityError):
            MultiLayerGraph(
                nodes={"n1": Node(id="n1")},
                layers={"l1": Layer(id="l1")},
                edges=[Edge(src="n1", dst="n2", src_layer="l1", dst_layer="l1")],
            )

    def test_graph_to_dict(self):
        """Test graph serialization to dict."""
        graph = MultiLayerGraph()
        graph.add_node(Node(id="n1"))
        graph.add_layer(Layer(id="l1"))

        data = graph.to_dict()
        assert "nodes" in data
        assert "layers" in data
        assert "edges" in data
        assert "directed" in data
        assert len(data["nodes"]) == 1
        assert len(data["layers"]) == 1

    def test_graph_from_dict(self):
        """Test graph deserialization from dict."""
        data = {
            "nodes": [{"id": "n1", "attributes": {}}],
            "layers": [{"id": "l1", "attributes": {}}],
            "edges": [
                {
                    "src": "n1",
                    "dst": "n1",
                    "src_layer": "l1",
                    "dst_layer": "l1",
                    "key": 0,
                    "attributes": {},
                }
            ],
            "directed": True,
            "attributes": {},
        }
        graph = MultiLayerGraph.from_dict(data)
        assert len(graph.nodes) == 1
        assert len(graph.layers) == 1
        assert len(graph.edges) == 1
        assert graph.directed is True


class TestAPI(unittest.TestCase):
    """Test I/O API and registry (Task Set 2)."""

    def test_supported_formats(self):
        """Test supported_formats returns registered formats."""
        formats = supported_formats()
        assert "read" in formats
        assert "write" in formats
        assert "json" in formats["read"]
        assert "json" in formats["write"]
        assert "jsonl" in formats["read"]
        assert "jsonl" in formats["write"]

    def test_supported_formats_read_only(self):
        """Test supported_formats with read=True, write=False."""
        formats = supported_formats(read=True, write=False)
        assert "read" in formats
        assert "write" not in formats

    def test_supported_formats_write_only(self):
        """Test supported_formats with read=False, write=True."""
        formats = supported_formats(read=False, write=True)
        assert "read" not in formats
        assert "write" in formats

    def test_register_custom_reader(self):
        """Test registering a custom reader."""

        def custom_reader(filepath, **kwargs):
            return MultiLayerGraph()

        register_reader("custom", custom_reader)
        formats = supported_formats()
        assert "custom" in formats["read"]

    def test_register_custom_writer(self):
        """Test registering a custom writer."""

        def custom_writer(graph, filepath, **kwargs):
            pass

        register_writer("custom", custom_writer)
        formats = supported_formats()
        assert "custom" in formats["write"]

    def test_read_unsupported_format(self):
        """Test reading unsupported format raises error."""
        with tempfile.NamedTemporaryFile(suffix=".xyz") as tmp:
            with pytest.raises(FormatUnsupportedError, match="xyz"):
                read(tmp.name)

    def test_write_unsupported_format(self):
        """Test writing unsupported format raises error."""
        graph = MultiLayerGraph()
        with tempfile.NamedTemporaryFile(suffix=".xyz") as tmp:
            with pytest.raises(FormatUnsupportedError, match="xyz"):
                write(graph, tmp.name)

    def test_read_file_not_found(self):
        """Test reading non-existent file raises error."""
        with pytest.raises(Py3plexIOError):
            read("/nonexistent/file.json")


class TestJSONFormat(unittest.TestCase):
    """Test JSON format implementation (Task Set 3)."""

    def test_json_round_trip(self):
        """Test JSON format round-trip preserves data."""
        # Create a sample graph
        graph = MultiLayerGraph()
        graph.add_node(Node(id="n1", attributes={"label": "Node 1"}))
        graph.add_node(Node(id="n2", attributes={"label": "Node 2"}))
        graph.add_layer(Layer(id="l1", attributes={"name": "Layer 1"}))
        graph.add_edge(
            Edge(
                src="n1",
                dst="n2",
                src_layer="l1",
                dst_layer="l1",
                attributes={"weight": 1.5},
            )
        )

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Write and read back
            write(graph, tmp_path)
            graph2 = read(tmp_path)

            # Verify
            assert len(graph2.nodes) == 2
            assert len(graph2.layers) == 1
            assert len(graph2.edges) == 1
            assert graph2.nodes["n1"].attributes["label"] == "Node 1"
            assert graph2.edges[0].attributes["weight"] == 1.5
        finally:
            Path(tmp_path).unlink()

    def test_json_deterministic_output(self):
        """Test JSON deterministic flag produces consistent output."""
        graph = MultiLayerGraph()
        graph.add_node(Node(id="n2"))
        graph.add_node(Node(id="n1"))
        graph.add_layer(Layer(id="l1"))

        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False
        ) as tmp1, tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp2:
            tmp1_path = tmp1.name
            tmp2_path = tmp2.name

        try:
            # Write twice with deterministic=True
            write(graph, tmp1_path, deterministic=True)
            write(graph, tmp2_path, deterministic=True)

            # Read both files and compare
            with open(tmp1_path) as f1, open(tmp2_path) as f2:
                data1 = json.load(f1)
                data2 = json.load(f2)

            assert data1 == data2
        finally:
            Path(tmp1_path).unlink()
            Path(tmp2_path).unlink()

    def test_jsonl_round_trip(self):
        """Test JSONL format round-trip preserves data."""
        # Create a sample graph
        graph = MultiLayerGraph()
        graph.add_node(Node(id="n1"))
        graph.add_layer(Layer(id="l1"))

        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Write and read back
            write(graph, tmp_path, format="jsonl")
            graph2 = read(tmp_path, format="jsonl")

            # Verify
            assert len(graph2.nodes) == 1
            assert len(graph2.layers) == 1
        finally:
            Path(tmp_path).unlink()

    def test_json_gzip_support(self):
        """Test JSON with gzip compression."""
        graph = MultiLayerGraph()
        graph.add_node(Node(id="n1"))
        graph.add_layer(Layer(id="l1"))

        with tempfile.NamedTemporaryFile(suffix=".json.gz", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Write and read back compressed
            write(graph, tmp_path)
            graph2 = read(tmp_path)

            assert len(graph2.nodes) == 1
        finally:
            Path(tmp_path).unlink()

    def test_jsonl_gzip_support(self):
        """Test JSONL with gzip compression."""
        graph = MultiLayerGraph()
        graph.add_node(Node(id="n1"))
        graph.add_layer(Layer(id="l1"))

        with tempfile.NamedTemporaryFile(suffix=".jsonl.gz", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Write and read back compressed
            write(graph, tmp_path, format="jsonl")
            graph2 = read(tmp_path, format="jsonl")

            assert len(graph2.nodes) == 1
        finally:
            Path(tmp_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


class TestCSVFormat(unittest.TestCase):
    """Test CSV format implementation (Task Set 3, tasks 12-15)."""

    def test_csv_basic_round_trip(self):
        """Test basic CSV format round-trip."""
        # Create a sample graph
        graph = MultiLayerGraph()
        graph.add_node(Node(id="n1"))
        graph.add_node(Node(id="n2"))
        graph.add_layer(Layer(id="l1"))
        graph.add_edge(Edge(src="n1", dst="n2", src_layer="l1", dst_layer="l1"))

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Write and read back
            write(graph, tmp_path, format="csv")
            graph2 = read(tmp_path, format="csv")

            # Verify
            assert len(graph2.nodes) == 2
            assert len(graph2.layers) == 1
            assert len(graph2.edges) == 1
        finally:
            Path(tmp_path).unlink()

    def test_csv_with_edge_attributes(self):
        """Test CSV with edge attributes."""
        graph = MultiLayerGraph()
        graph.add_node(Node(id="n1"))
        graph.add_node(Node(id="n2"))
        graph.add_layer(Layer(id="l1"))
        graph.add_edge(
            Edge(
                src="n1",
                dst="n2",
                src_layer="l1",
                dst_layer="l1",
                attributes={"weight": 2.5, "label": "test"},
            )
        )

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Write and read back
            write(graph, tmp_path, format="csv")
            graph2 = read(tmp_path, format="csv")

            # Verify attributes
            assert len(graph2.edges) == 1
            assert graph2.edges[0].attributes["weight"] == 2.5
            assert graph2.edges[0].attributes["label"] == "test"
        finally:
            Path(tmp_path).unlink()

    def test_csv_with_multiple_edges(self):
        """Test CSV with multiple edges (multigraph)."""
        graph = MultiLayerGraph()
        graph.add_node(Node(id="n1"))
        graph.add_node(Node(id="n2"))
        graph.add_layer(Layer(id="l1"))
        graph.add_edge(Edge(src="n1", dst="n2", src_layer="l1", dst_layer="l1", key=0))
        graph.add_edge(Edge(src="n1", dst="n2", src_layer="l1", dst_layer="l1", key=1))

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Write and read back
            write(graph, tmp_path, format="csv")
            graph2 = read(tmp_path, format="csv")

            # Verify both edges are preserved
            assert len(graph2.edges) == 2
            keys = {e.key for e in graph2.edges}
            assert keys == {0, 1}
        finally:
            Path(tmp_path).unlink()

    def test_csv_sidecar_files(self):
        """Test CSV with sidecar node and layer files."""
        graph = MultiLayerGraph()
        graph.add_node(Node(id="n1", attributes={"name": "Node 1", "value": 10}))
        graph.add_node(Node(id="n2", attributes={"name": "Node 2", "value": 20}))
        graph.add_layer(Layer(id="l1", attributes={"type": "social"}))
        graph.add_edge(Edge(src="n1", dst="n2", src_layer="l1", dst_layer="l1"))

        with tempfile.TemporaryDirectory() as tmpdir:
            edges_path = Path(tmpdir) / "edges.csv"
            nodes_path = Path(tmpdir) / "nodes.csv"
            layers_path = Path(tmpdir) / "layers.csv"

            # Write with sidecars
            write(graph, edges_path, format="csv", write_sidecars=True)

            # Verify sidecar files exist
            assert nodes_path.exists()
            assert layers_path.exists()

            # Read back with sidecars
            graph2 = read(
                edges_path, format="csv", nodes_file=nodes_path, layers_file=layers_path
            )

            # Verify node attributes preserved
            assert graph2.nodes["n1"].attributes["name"] == "Node 1"
            assert graph2.nodes["n1"].attributes["value"] == "10"  # CSV reads as string
            assert graph2.layers["l1"].attributes["type"] == "social"

    def test_csv_missing_required_columns(self):
        """Test CSV with missing required columns raises error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as tmp:
            # Write CSV with missing columns
            tmp.write("src,dst\n")
            tmp.write("n1,n2\n")
            tmp_path = tmp.name

        try:
            with pytest.raises(SchemaValidationError, match="missing required columns"):
                read(tmp_path, format="csv")
        finally:
            Path(tmp_path).unlink()

    def test_csv_deterministic_output(self):
        """Test CSV deterministic flag produces consistent output."""
        graph = MultiLayerGraph()
        graph.add_node(Node(id="n2"))
        graph.add_node(Node(id="n1"))
        graph.add_layer(Layer(id="l1"))
        graph.add_edge(Edge(src="n2", dst="n1", src_layer="l1", dst_layer="l1"))
        graph.add_edge(Edge(src="n1", dst="n2", src_layer="l1", dst_layer="l1"))

        with tempfile.NamedTemporaryFile(
            suffix=".csv", delete=False
        ) as tmp1, tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp2:
            tmp1_path = tmp1.name
            tmp2_path = tmp2.name

        try:
            # Write twice with deterministic=True
            write(graph, tmp1_path, format="csv", deterministic=True)
            write(graph, tmp2_path, format="csv", deterministic=True)

            # Read both files and compare
            with open(tmp1_path) as f1, open(tmp2_path) as f2:
                content1 = f1.read()
                content2 = f2.read()

            assert content1 == content2
        finally:
            Path(tmp1_path).unlink()
            Path(tmp2_path).unlink()


class TestNetworkXConverter(unittest.TestCase):
    """Test NetworkX converter (Task Set 4, task 23)."""

    def test_to_networkx_union_mode(self):
        """Test conversion to NetworkX in union mode."""
        # Skip if NetworkX not available
        try:
            import networkx as nx  # noqa: F401

            from py3plex.io import from_networkx, to_networkx  # noqa: F401
        except ImportError:
            pytest.skip("NetworkX not available")

        # Create a simple multilayer graph
        graph = MultiLayerGraph()
        graph.add_node(Node(id="n1", attributes={"label": "Node 1"}))
        graph.add_node(Node(id="n2", attributes={"label": "Node 2"}))
        graph.add_layer(Layer(id="l1"))
        graph.add_layer(Layer(id="l2"))
        graph.add_edge(Edge(src="n1", dst="n2", src_layer="l1", dst_layer="l1"))
        graph.add_edge(Edge(src="n1", dst="n2", src_layer="l2", dst_layer="l2"))

        # Convert to NetworkX
        G = to_networkx(graph, mode="union")

        # Verify structure
        assert G.number_of_nodes() == 2
        assert G.number_of_edges() == 2  # Both layer edges merged
        assert "n1" in G.nodes()
        assert "n2" in G.nodes()

    def test_to_networkx_multiplex_mode(self):
        """Test conversion to NetworkX in multiplex mode."""
        try:
            import networkx as nx  # noqa: F401

            from py3plex.io import to_networkx
        except ImportError:
            pytest.skip("NetworkX not available")

        # Create a multilayer graph
        graph = MultiLayerGraph()
        graph.add_node(Node(id="n1"))
        graph.add_node(Node(id="n2"))
        graph.add_layer(Layer(id="l1"))
        graph.add_layer(Layer(id="l2"))
        graph.add_edge(Edge(src="n1", dst="n2", src_layer="l1", dst_layer="l1"))

        # Convert to NetworkX with multiplex mode
        G = to_networkx(graph, mode="multiplex")

        # Verify structure - should have (node, layer) tuples
        assert G.number_of_nodes() == 4  # 2 nodes x 2 layers
        assert ("n1", "l1") in G.nodes()
        assert ("n1", "l2") in G.nodes()
        assert ("n2", "l1") in G.nodes()
        assert ("n2", "l2") in G.nodes()

    def test_from_networkx_union_mode(self):
        """Test conversion from NetworkX in union mode."""
        try:
            import networkx as nx

            from py3plex.io import from_networkx
        except ImportError:
            pytest.skip("NetworkX not available")

        # Create a NetworkX graph
        G = nx.MultiDiGraph()
        G.add_node("n1", label="Node 1")
        G.add_node("n2", label="Node 2")
        G.add_edge("n1", "n2", weight=1.5)

        # Convert to MultiLayerGraph
        graph = from_networkx(G, mode="union", default_layer="layer1")

        # Verify structure
        assert len(graph.nodes) == 2
        assert len(graph.layers) == 1
        assert "layer1" in graph.layers
        assert len(graph.edges) == 1
        assert graph.nodes["n1"].attributes["label"] == "Node 1"

    def test_from_networkx_multiplex_mode(self):
        """Test conversion from NetworkX in multiplex mode."""
        try:
            import networkx as nx

            from py3plex.io import from_networkx
        except ImportError:
            pytest.skip("NetworkX not available")

        # Create a NetworkX graph with (node, layer) tuples
        G = nx.MultiDiGraph()
        G.add_node(("n1", "l1"))
        G.add_node(("n2", "l1"))
        G.add_edge(("n1", "l1"), ("n2", "l1"), weight=1.0)

        # Convert to MultiLayerGraph
        graph = from_networkx(G, mode="multiplex")

        # Verify structure
        assert len(graph.nodes) == 2
        assert len(graph.layers) == 1
        assert "l1" in graph.layers
        assert len(graph.edges) == 1

    def test_networkx_round_trip(self):
        """Test round-trip conversion: MLG -> NX -> MLG."""
        try:
            import networkx as nx  # noqa: F401

            from py3plex.io import from_networkx, to_networkx
        except ImportError:
            pytest.skip("NetworkX not available")

        # Create original graph
        graph1 = MultiLayerGraph()
        graph1.add_node(Node(id="n1", attributes={"value": 10}))
        graph1.add_node(Node(id="n2", attributes={"value": 20}))
        graph1.add_layer(Layer(id="l1", attributes={"type": "social"}))
        graph1.add_edge(
            Edge(
                src="n1",
                dst="n2",
                src_layer="l1",
                dst_layer="l1",
                attributes={"weight": 2.5},
            )
        )

        # Convert to NetworkX and back
        G = to_networkx(graph1, mode="multiplex")
        graph2 = from_networkx(G, mode="multiplex")

        # Verify preservation
        assert len(graph2.nodes) == len(graph1.nodes)
        assert len(graph2.layers) == len(graph1.layers)
        assert len(graph2.edges) == len(graph1.edges)
        assert graph2.nodes["n1"].attributes["value"] == 10


class TestIGraphConverter(unittest.TestCase):
    """Test igraph converter (Task Set 4, task 24)."""

    @unittest.skipUnless(HAS_IGRAPH, "igraph not available")
    def test_to_igraph_multiplex_mode(self):
        """Test conversion to igraph in multiplex mode."""
        import igraph as ig  # noqa: F401

        from py3plex.io import to_igraph

        # Create a multilayer graph
        graph = MultiLayerGraph()
        graph.add_node(Node(id="n1", attributes={"label": "Node 1"}))
        graph.add_node(Node(id="n2", attributes={"label": "Node 2"}))
        graph.add_layer(Layer(id="l1"))
        graph.add_edge(Edge(src="n1", dst="n2", src_layer="l1", dst_layer="l1"))

        # Convert to igraph
        g = to_igraph(graph, mode="multiplex")

        # Verify structure
        assert g.vcount() == 2  # 2 nodes x 1 layer
        assert g.ecount() == 1

    @unittest.skipUnless(HAS_IGRAPH, "igraph not available")
    def test_to_igraph_union_mode(self):
        """Test conversion to igraph in union mode."""
        import igraph as ig  # noqa: F401

        from py3plex.io import to_igraph

        # Create a multilayer graph
        graph = MultiLayerGraph()
        graph.add_node(Node(id="n1"))
        graph.add_node(Node(id="n2"))
        graph.add_layer(Layer(id="l1"))
        graph.add_layer(Layer(id="l2"))
        graph.add_edge(Edge(src="n1", dst="n2", src_layer="l1", dst_layer="l1"))
        graph.add_edge(Edge(src="n1", dst="n2", src_layer="l2", dst_layer="l2"))

        # Convert to igraph
        g = to_igraph(graph, mode="union")

        # Verify structure
        assert g.vcount() == 2
        assert g.ecount() == 2  # Both layer edges

    @unittest.skipUnless(HAS_IGRAPH, "igraph not available")
    def test_from_igraph_union_mode(self):
        """Test conversion from igraph in union mode."""
        import igraph as ig

        from py3plex.io import from_igraph

        # Create an igraph graph
        g = ig.Graph(directed=True)
        g.add_vertices(2)
        g.vs[0]["node_id"] = "n1"
        g.vs[1]["node_id"] = "n2"
        g.add_edge(0, 1, weight=1.5)

        # Convert to MultiLayerGraph
        graph = from_igraph(g, mode="union", default_layer="layer1")

        # Verify structure
        assert len(graph.nodes) == 2
        assert len(graph.layers) == 1
        assert len(graph.edges) == 1

    @unittest.skipUnless(HAS_IGRAPH, "igraph not available")
    def test_igraph_round_trip(self):
        """Test round-trip conversion: MLG -> igraph -> MLG."""
        import igraph as ig  # noqa: F401

        from py3plex.io import from_igraph, to_igraph

        # Create original graph
        graph1 = MultiLayerGraph()
        graph1.add_node(Node(id="n1", attributes={"value": 10}))
        graph1.add_node(Node(id="n2", attributes={"value": 20}))
        graph1.add_layer(Layer(id="l1"))
        graph1.add_edge(
            Edge(
                src="n1",
                dst="n2",
                src_layer="l1",
                dst_layer="l1",
                attributes={"weight": 2.5},
            )
        )

        # Convert to igraph and back
        g = to_igraph(graph1, mode="multiplex")
        graph2 = from_igraph(g, mode="multiplex")

        # Verify preservation
        assert len(graph2.nodes) == len(graph1.nodes)
        assert len(graph2.layers) == len(graph1.layers)
        assert len(graph2.edges) == len(graph1.edges)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
