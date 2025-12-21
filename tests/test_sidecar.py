"""
Tests for sidecar bundle functionality.

These tests verify that sidecar bundles correctly preserve graph data
for lossless roundtrip conversion.
"""

import json
import tempfile
from pathlib import Path

import pytest
import pandas as pd

from py3plex.compat.sidecar import export_sidecar, import_sidecar
from py3plex.compat.ir import GraphIR, NodeTable, EdgeTable, GraphMeta, to_ir
from py3plex.io.schema import MultiLayerGraph, Node, Layer, Edge


@pytest.fixture
def sample_ir():
    """Create a sample GraphIR for testing."""
    nodes = NodeTable(
        node_id=["A", "B", "C"],
        node_order=[0, 1, 2],
        attrs=pd.DataFrame({
            "type": ["hub", "leaf", "leaf"],
            "value": [1.0, 2.0, 3.0],
        }),
    )
    
    edges = EdgeTable(
        edge_id=["e0", "e1"],
        src=["A", "B"],
        dst=["B", "C"],
        edge_order=[0, 1],
        attrs=pd.DataFrame({
            "weight": [1.0, 0.5],
            "color": ["red", "blue"],
        }),
        src_layer=["L1", "L1"],
        dst_layer=["L1", "L1"],
    )
    
    meta = GraphMeta(
        directed=False,
        multi=False,
        name="test_graph",
        layers=["L1"],
        global_attrs={"description": "A test graph"},
    )
    
    return GraphIR(nodes=nodes, edges=edges, meta=meta)


class TestSidecarExport:
    """Test sidecar export functionality."""
    
    def test_export_creates_directory(self, sample_ir):
        """Test that export creates bundle directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle_path = Path(tmpdir) / "test_bundle"
            
            export_sidecar(sample_ir, str(bundle_path))
            
            assert bundle_path.exists()
            assert bundle_path.is_dir()
    
    def test_export_creates_meta_json(self, sample_ir):
        """Test that meta.json is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle_path = Path(tmpdir) / "test_bundle"
            
            export_sidecar(sample_ir, str(bundle_path))
            
            meta_path = bundle_path / "meta.json"
            assert meta_path.exists()
            
            # Verify JSON content
            with open(meta_path) as f:
                meta_data = json.load(f)
            
            assert meta_data["directed"] == False
            assert meta_data["multi"] == False
            assert meta_data["name"] == "test_graph"
            assert meta_data["layers"] == ["L1"]
    
    def test_export_csv_format(self, sample_ir):
        """Test export with CSV format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle_path = Path(tmpdir) / "test_bundle"
            
            export_sidecar(sample_ir, str(bundle_path), format="json+csv")
            
            assert (bundle_path / "nodes.csv").exists()
            assert (bundle_path / "edges.csv").exists()
            assert (bundle_path / "format.txt").exists()
            
            # Check format marker
            with open(bundle_path / "format.txt") as f:
                assert f.read().strip() == "csv"
    
    def test_export_parquet_format_fallback(self, sample_ir):
        """Test that parquet falls back to CSV if pyarrow unavailable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle_path = Path(tmpdir) / "test_bundle"
            
            # Try parquet format (may fall back to CSV)
            export_sidecar(sample_ir, str(bundle_path), format="json+parquet")
            
            # Check that at least one format exists
            assert (bundle_path / "nodes.csv").exists() or (bundle_path / "nodes.parquet").exists()
            assert (bundle_path / "edges.csv").exists() or (bundle_path / "edges.parquet").exists()


class TestSidecarImport:
    """Test sidecar import functionality."""
    
    def test_import_roundtrip_csv(self, sample_ir):
        """Test roundtrip with CSV format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle_path = Path(tmpdir) / "test_bundle"
            
            # Export
            export_sidecar(sample_ir, str(bundle_path), format="json+csv")
            
            # Import
            result_ir = import_sidecar(str(bundle_path))
            
            # Verify nodes
            assert result_ir.nodes.node_id == sample_ir.nodes.node_id
            assert result_ir.nodes.node_order == sample_ir.nodes.node_order
            
            # Verify edges
            assert result_ir.edges.edge_id == sample_ir.edges.edge_id
            assert result_ir.edges.src == sample_ir.edges.src
            assert result_ir.edges.dst == sample_ir.edges.dst
            
            # Verify metadata
            assert result_ir.meta.directed == sample_ir.meta.directed
            assert result_ir.meta.name == sample_ir.meta.name
            assert result_ir.meta.layers == sample_ir.meta.layers
    
    def test_import_nonexistent_raises(self):
        """Test that importing nonexistent bundle raises error."""
        with pytest.raises(FileNotFoundError):
            import_sidecar("/nonexistent/path")
    
    def test_import_missing_meta_raises(self):
        """Test that missing meta.json raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle_path = Path(tmpdir) / "incomplete_bundle"
            bundle_path.mkdir()
            
            with pytest.raises(FileNotFoundError) as exc_info:
                import_sidecar(str(bundle_path))
            
            assert "meta.json" in str(exc_info.value)
    
    def test_import_preserves_node_attributes(self, sample_ir):
        """Test that node attributes are preserved in roundtrip."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle_path = Path(tmpdir) / "test_bundle"
            
            export_sidecar(sample_ir, str(bundle_path))
            result_ir = import_sidecar(str(bundle_path))
            
            # Check node attributes
            assert "type" in result_ir.nodes.attrs.columns
            assert "value" in result_ir.nodes.attrs.columns
            
            # Check values
            assert list(result_ir.nodes.attrs["type"]) == ["hub", "leaf", "leaf"]
            assert list(result_ir.nodes.attrs["value"]) == [1.0, 2.0, 3.0]
    
    def test_import_preserves_edge_attributes(self, sample_ir):
        """Test that edge attributes are preserved in roundtrip."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle_path = Path(tmpdir) / "test_bundle"
            
            export_sidecar(sample_ir, str(bundle_path))
            result_ir = import_sidecar(str(bundle_path))
            
            # Check edge attributes
            assert "weight" in result_ir.edges.attrs.columns
            assert "color" in result_ir.edges.attrs.columns
            
            # Check values
            assert list(result_ir.edges.attrs["weight"]) == [1.0, 0.5]
            assert list(result_ir.edges.attrs["color"]) == ["red", "blue"]
    
    def test_import_preserves_layer_info(self, sample_ir):
        """Test that layer information is preserved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle_path = Path(tmpdir) / "test_bundle"
            
            export_sidecar(sample_ir, str(bundle_path))
            result_ir = import_sidecar(str(bundle_path))
            
            assert result_ir.edges.src_layer == sample_ir.edges.src_layer
            assert result_ir.edges.dst_layer == sample_ir.edges.dst_layer


class TestSidecarWithMultilayerGraph:
    """Test sidecar with real MultiLayerGraph objects."""
    
    def test_full_roundtrip_with_graph(self):
        """Test full roundtrip from graph through sidecar."""
        # Create graph
        graph = MultiLayerGraph(directed=False)
        graph.add_layer(Layer(id="layer1"))
        graph.add_node(Node(id="A", attributes={"type": "hub"}))
        graph.add_node(Node(id="B", attributes={"type": "leaf"}))
        graph.add_edge(Edge(
            src="A", dst="B",
            src_layer="layer1", dst_layer="layer1",
            attributes={"weight": 1.5}
        ))
        
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle_path = Path(tmpdir) / "graph_bundle"
            
            # Convert to IR and export
            ir = to_ir(graph)
            export_sidecar(ir, str(bundle_path))
            
            # Import and convert back
            restored_ir = import_sidecar(str(bundle_path))
            
            # Verify structure preserved
            assert len(restored_ir.nodes.node_id) == 2
            assert len(restored_ir.edges.edge_id) == 1
            assert not restored_ir.meta.directed


class TestSidecarEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_graph_export_import(self):
        """Test sidecar with empty graph."""
        nodes = NodeTable(node_id=[], node_order=[], attrs=None)
        edges = EdgeTable(edge_id=[], src=[], dst=[], edge_order=[], attrs=None)
        meta = GraphMeta(directed=False, name="empty")
        
        empty_ir = GraphIR(nodes=nodes, edges=edges, meta=meta)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle_path = Path(tmpdir) / "empty_bundle"
            
            export_sidecar(empty_ir, str(bundle_path))
            result_ir = import_sidecar(str(bundle_path))
            
            assert len(result_ir.nodes.node_id) == 0
            assert len(result_ir.edges.edge_id) == 0
    
    def test_graph_without_attributes(self):
        """Test sidecar with graph without attributes."""
        nodes = NodeTable(
            node_id=["A", "B"],
            node_order=[0, 1],
            attrs=None,
        )
        edges = EdgeTable(
            edge_id=["e0"],
            src=["A"],
            dst=["B"],
            edge_order=[0],
            attrs=None,
        )
        meta = GraphMeta(directed=True)
        
        ir = GraphIR(nodes=nodes, edges=edges, meta=meta)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle_path = Path(tmpdir) / "no_attrs_bundle"
            
            export_sidecar(ir, str(bundle_path))
            result_ir = import_sidecar(str(bundle_path))
            
            assert result_ir.nodes.attrs is None or len(result_ir.nodes.attrs.columns) == 0
            assert result_ir.edges.attrs is None or len(result_ir.edges.attrs.columns) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
