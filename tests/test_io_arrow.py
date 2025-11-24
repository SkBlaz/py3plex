"""
Tests for Apache Arrow format I/O operations.

Tests include:
- Basic read/write roundtrip
- Empty graphs
- Large graphs
- Multiple formats (Feather, Parquet)
- Attribute preservation
- Error handling
"""

import tempfile
from pathlib import Path

import pytest

from py3plex.io import Edge, Layer, MultiLayerGraph, Node, read, write

# Check if pyarrow is available
try:
    import pyarrow

    PYARROW_AVAILABLE = True
except ImportError:
    PYARROW_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not PYARROW_AVAILABLE, reason="pyarrow not installed"
)


@pytest.fixture
def sample_graph():
    """Create a sample multilayer graph for testing."""
    graph = MultiLayerGraph(
        directed=True, attributes={"name": "Test Network", "version": "1.0"}
    )

    # Add layers
    graph.add_layer(Layer(id="social", attributes={"type": "friendship"}))
    graph.add_layer(Layer(id="work", attributes={"type": "collaboration"}))

    # Add nodes
    graph.add_node(Node(id="alice", attributes={"age": 30, "city": "NYC"}))
    graph.add_node(Node(id="bob", attributes={"age": 25, "city": "SF"}))
    graph.add_node(Node(id="charlie", attributes={"age": 35, "city": "LA"}))

    # Add edges
    graph.add_edge(
        Edge(
            src="alice",
            dst="bob",
            src_layer="social",
            dst_layer="social",
            attributes={"weight": 0.8, "timestamp": "2024-01-15"},
        )
    )
    graph.add_edge(
        Edge(
            src="bob",
            dst="charlie",
            src_layer="work",
            dst_layer="work",
            attributes={"weight": 0.6},
        )
    )
    graph.add_edge(
        Edge(
            src="alice",
            dst="charlie",
            src_layer="social",
            dst_layer="work",
            attributes={"weight": 0.5},
        )
    )

    return graph


def test_arrow_feather_roundtrip(sample_graph):
    """Test basic roundtrip with Feather format."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "test.arrow"

        # Write
        write(sample_graph, filepath, format="arrow")

        # Read
        loaded_graph = read(filepath, format="arrow")

        # Verify
        assert len(loaded_graph.nodes) == len(sample_graph.nodes)
        assert len(loaded_graph.layers) == len(sample_graph.layers)
        assert len(loaded_graph.edges) == len(sample_graph.edges)
        assert loaded_graph.directed == sample_graph.directed
        assert loaded_graph.attributes == sample_graph.attributes


def test_arrow_parquet_roundtrip(sample_graph):
    """Test basic roundtrip with Parquet format."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "test.parquet"

        # Write
        write(sample_graph, filepath, format="parquet")

        # Read
        loaded_graph = read(filepath, format="parquet")

        # Verify
        assert len(loaded_graph.nodes) == len(sample_graph.nodes)
        assert len(loaded_graph.layers) == len(sample_graph.layers)
        assert len(loaded_graph.edges) == len(sample_graph.edges)
        assert loaded_graph.directed == sample_graph.directed
        assert loaded_graph.attributes == sample_graph.attributes


def test_arrow_feather_extension():
    """Test automatic format detection with .feather extension."""
    graph = MultiLayerGraph()
    graph.add_layer(Layer(id="l1"))
    graph.add_node(Node(id="n1"))

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "test.feather"

        # Write without explicit format
        write(graph, filepath)

        # Read without explicit format
        loaded_graph = read(filepath)

        assert len(loaded_graph.nodes) == 1
        assert len(loaded_graph.layers) == 1


def test_arrow_empty_graph():
    """Test serialization of empty graph."""
    graph = MultiLayerGraph(directed=False, attributes={"empty": True})

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "empty.arrow"

        # Write
        write(graph, filepath, format="arrow")

        # Read
        loaded_graph = read(filepath, format="arrow")

        # Verify
        assert len(loaded_graph.nodes) == 0
        assert len(loaded_graph.layers) == 0
        assert len(loaded_graph.edges) == 0
        assert loaded_graph.directed == False
        assert loaded_graph.attributes == {"empty": True}


def test_arrow_node_attributes(sample_graph):
    """Test that node attributes are preserved correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "test.arrow"

        # Write and read
        write(sample_graph, filepath, format="arrow")
        loaded_graph = read(filepath, format="arrow")

        # Check node attributes
        for node_id, node in sample_graph.nodes.items():
            loaded_node = loaded_graph.nodes[node_id]
            assert loaded_node.attributes == node.attributes


def test_arrow_edge_attributes(sample_graph):
    """Test that edge attributes are preserved correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "test.arrow"

        # Write and read
        write(sample_graph, filepath, format="arrow")
        loaded_graph = read(filepath, format="arrow")

        # Check edge attributes
        assert len(loaded_graph.edges) == len(sample_graph.edges)
        
        # Sort both edge lists to ensure consistent comparison
        orig_edges = sorted(sample_graph.edges, key=lambda e: (e.src, e.dst, e.src_layer, e.dst_layer, e.key))
        loaded_edges = sorted(loaded_graph.edges, key=lambda e: (e.src, e.dst, e.src_layer, e.dst_layer, e.key))
        
        for orig_edge, loaded_edge in zip(orig_edges, loaded_edges):
            assert loaded_edge.attributes == orig_edge.attributes
            assert loaded_edge.src == orig_edge.src
            assert loaded_edge.dst == orig_edge.dst
            assert loaded_edge.src_layer == orig_edge.src_layer
            assert loaded_edge.dst_layer == orig_edge.dst_layer


def test_arrow_layer_attributes(sample_graph):
    """Test that layer attributes are preserved correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "test.arrow"

        # Write and read
        write(sample_graph, filepath, format="arrow")
        loaded_graph = read(filepath, format="arrow")

        # Check layer attributes
        for layer_id, layer in sample_graph.layers.items():
            loaded_layer = loaded_graph.layers[layer_id]
            assert loaded_layer.attributes == layer.attributes


def test_arrow_undirected_graph():
    """Test undirected graph serialization."""
    graph = MultiLayerGraph(directed=False)
    graph.add_layer(Layer(id="l1"))
    graph.add_node(Node(id="n1"))
    graph.add_node(Node(id="n2"))
    graph.add_edge(Edge(src="n1", dst="n2", src_layer="l1", dst_layer="l1"))

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "test.arrow"

        # Write and read
        write(graph, filepath, format="arrow")
        loaded_graph = read(filepath, format="arrow")

        # Verify
        assert loaded_graph.directed == False
        assert len(loaded_graph.edges) == 1


def test_arrow_multi_edge():
    """Test graph with multiple edges between same node pair."""
    graph = MultiLayerGraph()
    graph.add_layer(Layer(id="l1"))
    graph.add_node(Node(id="n1"))
    graph.add_node(Node(id="n2"))

    # Add multiple edges
    graph.add_edge(
        Edge(
            src="n1",
            dst="n2",
            src_layer="l1",
            dst_layer="l1",
            key=0,
            attributes={"type": "friend"},
        )
    )
    graph.add_edge(
        Edge(
            src="n1",
            dst="n2",
            src_layer="l1",
            dst_layer="l1",
            key=1,
            attributes={"type": "colleague"},
        )
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "test.arrow"

        # Write and read
        write(graph, filepath, format="arrow")
        loaded_graph = read(filepath, format="arrow")

        # Verify
        assert len(loaded_graph.edges) == 2
        
        # Find edges by their properties
        edge1 = [e for e in loaded_graph.edges if e.key == 0][0]
        edge2 = [e for e in loaded_graph.edges if e.key == 1][0]
        assert edge1.attributes == {"type": "friend"}
        assert edge2.attributes == {"type": "colleague"}


def test_arrow_complex_attributes():
    """Test graph with complex nested attributes."""
    graph = MultiLayerGraph(
        attributes={
            "metadata": {
                "creator": "test",
                "tags": ["network", "multilayer"],
                "stats": {"nodes": 2, "edges": 1},
            }
        }
    )
    graph.add_layer(Layer(id="l1", attributes={"props": [1, 2, 3]}))
    graph.add_node(Node(id="n1", attributes={"data": {"x": 1, "y": 2}}))

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "test.arrow"

        # Write and read
        write(graph, filepath, format="arrow")
        loaded_graph = read(filepath, format="arrow")

        # Verify complex attributes
        assert loaded_graph.attributes == graph.attributes
        assert loaded_graph.layers["l1"].attributes == graph.layers["l1"].attributes
        assert loaded_graph.nodes["n1"].attributes == graph.nodes["n1"].attributes


def test_arrow_large_graph():
    """Test serialization of larger graph."""
    graph = MultiLayerGraph()

    # Create layers
    for i in range(5):
        graph.add_layer(Layer(id=f"layer_{i}"))

    # Create nodes
    for i in range(100):
        graph.add_node(Node(id=f"node_{i}", attributes={"index": i}))

    # Create edges
    for i in range(100):
        for j in range(i + 1, min(i + 10, 100)):
            layer_idx = (i + j) % 5
            graph.add_edge(
                Edge(
                    src=f"node_{i}",
                    dst=f"node_{j}",
                    src_layer=f"layer_{layer_idx}",
                    dst_layer=f"layer_{layer_idx}",
                    attributes={"weight": i + j},
                )
            )

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "large.arrow"

        # Write and read
        write(graph, filepath, format="arrow")
        loaded_graph = read(filepath, format="arrow")

        # Verify
        assert len(loaded_graph.nodes) == 100
        assert len(loaded_graph.layers) == 5
        assert len(loaded_graph.edges) == len(graph.edges)


def test_arrow_comparison_with_json(sample_graph):
    """Test that Arrow and JSON produce equivalent results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        arrow_path = Path(tmpdir) / "test.arrow"
        json_path = Path(tmpdir) / "test.json"

        # Write both formats
        write(sample_graph, arrow_path, format="arrow")
        write(sample_graph, json_path, format="json")

        # Read both
        arrow_graph = read(arrow_path, format="arrow")
        json_graph = read(json_path, format="json")

        # Verify they're equivalent
        assert len(arrow_graph.nodes) == len(json_graph.nodes)
        assert len(arrow_graph.layers) == len(json_graph.layers)
        assert len(arrow_graph.edges) == len(json_graph.edges)
        assert arrow_graph.directed == json_graph.directed


def test_arrow_file_size_comparison(sample_graph):
    """Compare file sizes between different formats."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        arrow_path = tmpdir_path / "test.arrow"
        parquet_path = tmpdir_path / "test.parquet"
        json_path = tmpdir_path / "test.json"

        # Write all formats
        write(sample_graph, arrow_path, format="arrow")
        write(sample_graph, parquet_path, format="parquet")
        write(sample_graph, json_path, format="json")

        # Get file sizes (including companion files for Arrow/Parquet)
        arrow_size = sum(
            p.stat().st_size
            for p in tmpdir_path.iterdir()
            if p.name.startswith("test.arrow")
        )
        parquet_size = sum(
            p.stat().st_size
            for p in tmpdir_path.iterdir()
            if p.name.startswith("test.parquet")
        )
        json_size = json_path.stat().st_size

        # Just verify they all exist (don't make assumptions about size)
        assert arrow_size > 0
        assert parquet_size > 0
        assert json_size > 0


def test_arrow_unicode_support():
    """Test support for Unicode characters in attributes."""
    graph = MultiLayerGraph()
    graph.add_layer(Layer(id="社交", attributes={"名前": "ソーシャル"}))
    graph.add_node(
        Node(id="alice", attributes={"city": "東京", "symbol": "★", "text": "Hello 世界"})
    )
    graph.add_node(Node(id="bob", attributes={"city": "Москва", "text": "Привет"}))

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "unicode.arrow"

        # Write and read
        write(graph, filepath, format="arrow")
        loaded_graph = read(filepath, format="arrow")

        # Verify Unicode preservation
        assert "社交" in loaded_graph.layers
        assert loaded_graph.layers["社交"].attributes["名前"] == "ソーシャル"
        assert loaded_graph.nodes["alice"].attributes["symbol"] == "★"
        assert loaded_graph.nodes["bob"].attributes["text"] == "Привет"
