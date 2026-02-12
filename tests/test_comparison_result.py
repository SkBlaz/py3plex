"""
Tests for ComparisonResult class.

This module tests the ComparisonResult container for network comparison operations.
"""
import pytest
import json
from py3plex.comparison.result import ComparisonResult


class TestComparisonResultBasics:
    """Test basic ComparisonResult functionality."""

    def test_create_minimal_comparison_result(self):
        """Test creating a minimal ComparisonResult."""
        result = ComparisonResult(
            metric_name="jaccard",
            network_a_name="net1",
            network_b_name="net2"
        )
        
        assert result.metric_name == "jaccard"
        assert result.network_a_name == "net1"
        assert result.network_b_name == "net2"
        assert result.global_distance is None
        assert result.layerwise_distance == {}
        assert result.per_node_difference == {}
        assert result.meta == {}

    def test_create_comparison_result_with_global_distance(self):
        """Test creating ComparisonResult with global distance."""
        result = ComparisonResult(
            metric_name="edit_distance",
            network_a_name="baseline",
            network_b_name="treatment",
            global_distance=0.35
        )
        
        assert result.global_distance == 0.35

    def test_create_comparison_result_with_layerwise_distance(self):
        """Test creating ComparisonResult with layerwise distances."""
        layerwise = {"layer1": 0.2, "layer2": 0.5, "layer3": 0.1}
        result = ComparisonResult(
            metric_name="hamming",
            network_a_name="net_a",
            network_b_name="net_b",
            layerwise_distance=layerwise
        )
        
        assert result.layerwise_distance == layerwise

    def test_create_comparison_result_with_per_node_difference(self):
        """Test creating ComparisonResult with per-node differences."""
        node_diff = {"A": 0.1, "B": 0.3, "C": 0.5}
        result = ComparisonResult(
            metric_name="structural_distance",
            network_a_name="net1",
            network_b_name="net2",
            per_node_difference=node_diff
        )
        
        assert result.per_node_difference == node_diff

    def test_create_comparison_result_with_metadata(self):
        """Test creating ComparisonResult with metadata."""
        meta = {
            "algorithm": "fast_comparison",
            "runtime_ms": 120.5,
            "version": "2.0"
        }
        result = ComparisonResult(
            metric_name="multiplex_jaccard",
            network_a_name="baseline",
            network_b_name="perturbed",
            global_distance=0.87,
            meta=meta
        )
        
        assert result.meta == meta
        assert result.meta["algorithm"] == "fast_comparison"


class TestComparisonResultExportBasic:
    """Test basic ComparisonResult export functionality."""

    def test_to_pandas(self):
        """Test exporting to pandas DataFrame."""
        pytest.importorskip("pandas")
        
        result = ComparisonResult(
            metric_name="jaccard",
            network_a_name="net1",
            network_b_name="net2",
            global_distance=0.75
        )
        
        df = result.to_pandas()
        
        assert len(df) == 1
        assert list(df.columns) == ["metric", "network_a", "network_b", "global_distance"]
        assert df["metric"].iloc[0] == "jaccard"
        assert df["network_a"].iloc[0] == "net1"
        assert df["network_b"].iloc[0] == "net2"
        assert df["global_distance"].iloc[0] == 0.75

    def test_to_pandas_without_global_distance(self):
        """Test to_pandas with no global distance."""
        pytest.importorskip("pandas")
        
        result = ComparisonResult(
            metric_name="custom",
            network_a_name="a",
            network_b_name="b"
        )
        
        df = result.to_pandas()
        
        assert len(df) == 1
        assert df["global_distance"].iloc[0] is None

    def test_to_pandas_layerwise(self):
        """Test exporting layerwise distances to pandas."""
        pytest.importorskip("pandas")
        
        layerwise = {"social": 0.2, "work": 0.5, "family": 0.1}
        result = ComparisonResult(
            metric_name="hamming",
            network_a_name="net1",
            network_b_name="net2",
            layerwise_distance=layerwise
        )
        
        df = result.to_pandas_layerwise()
        
        assert len(df) == 3
        assert list(df.columns) == ["layer", "distance"]
        assert set(df["layer"]) == {"social", "work", "family"}
        assert df.set_index("layer")["distance"].to_dict() == layerwise

    def test_to_pandas_layerwise_empty(self):
        """Test to_pandas_layerwise with no layerwise data."""
        pytest.importorskip("pandas")
        
        result = ComparisonResult(
            metric_name="jaccard",
            network_a_name="net1",
            network_b_name="net2"
        )
        
        df = result.to_pandas_layerwise()
        
        assert len(df) == 0
        assert list(df.columns) == ["layer", "distance"]

    def test_to_pandas_nodes(self):
        """Test exporting per-node differences to pandas."""
        pytest.importorskip("pandas")
        
        node_diff = {"node1": 0.1, "node2": 0.3, "node3": 0.5}
        result = ComparisonResult(
            metric_name="node_difference",
            network_a_name="net1",
            network_b_name="net2",
            per_node_difference=node_diff
        )
        
        df = result.to_pandas_nodes()
        
        assert len(df) == 3
        assert list(df.columns) == ["node", "difference"]
        assert set(df["node"]) == {"node1", "node2", "node3"}
        assert df.set_index("node")["difference"].to_dict() == node_diff

    def test_to_pandas_nodes_empty(self):
        """Test to_pandas_nodes with no per-node data."""
        pytest.importorskip("pandas")
        
        result = ComparisonResult(
            metric_name="jaccard",
            network_a_name="net1",
            network_b_name="net2"
        )
        
        df = result.to_pandas_nodes()
        
        assert len(df) == 0
        assert list(df.columns) == ["node", "difference"]


class TestComparisonResultToDictAndJson:
    """Test ComparisonResult to_dict and to_json methods."""

    def test_to_dict(self):
        """Test exporting to dictionary."""
        layerwise = {"layer1": 0.3}
        node_diff = {"A": 0.1}
        meta = {"notes": "test"}
        
        result = ComparisonResult(
            metric_name="jaccard",
            network_a_name="net1",
            network_b_name="net2",
            global_distance=0.5,
            layerwise_distance=layerwise,
            per_node_difference=node_diff,
            meta=meta
        )
        
        d = result.to_dict()
        
        assert d["metric_name"] == "jaccard"
        assert d["network_a"] == "net1"
        assert d["network_b"] == "net2"
        assert d["global_distance"] == 0.5
        assert d["layerwise_distance"] == layerwise
        assert d["per_node_difference"] == node_diff
        assert d["meta"] == meta

    def test_to_dict_minimal(self):
        """Test to_dict with minimal data."""
        result = ComparisonResult(
            metric_name="test",
            network_a_name="a",
            network_b_name="b"
        )
        
        d = result.to_dict()
        
        assert d["metric_name"] == "test"
        assert d["network_a"] == "a"
        assert d["network_b"] == "b"
        assert d["global_distance"] is None
        assert d["layerwise_distance"] == {}
        assert d["per_node_difference"] == {}
        assert d["meta"] == {}

    def test_to_json(self):
        """Test exporting to JSON string."""
        result = ComparisonResult(
            metric_name="jaccard",
            network_a_name="net1",
            network_b_name="net2",
            global_distance=0.75
        )
        
        json_str = result.to_json()
        parsed = json.loads(json_str)
        
        assert parsed["metric_name"] == "jaccard"
        assert parsed["network_a"] == "net1"
        assert parsed["network_b"] == "net2"
        assert parsed["global_distance"] == 0.75

    def test_to_json_converts_node_keys_to_strings(self):
        """Test that to_json converts node keys to strings."""
        node_diff = {1: 0.1, 2: 0.3, ("A", "layer1"): 0.5}
        result = ComparisonResult(
            metric_name="node_diff",
            network_a_name="net1",
            network_b_name="net2",
            per_node_difference=node_diff
        )
        
        json_str = result.to_json()
        parsed = json.loads(json_str)
        
        # All keys should be strings in JSON
        assert "1" in parsed["per_node_difference"]
        assert "2" in parsed["per_node_difference"]
        assert parsed["per_node_difference"]["1"] == 0.1
        assert parsed["per_node_difference"]["2"] == 0.3

    def test_to_json_formatted(self):
        """Test that to_json produces formatted output."""
        result = ComparisonResult(
            metric_name="test",
            network_a_name="a",
            network_b_name="b",
            global_distance=0.5
        )
        
        json_str = result.to_json()
        
        # Should be indented
        assert "\n" in json_str
        assert "  " in json_str  # 2-space indent


class TestComparisonResultRepr:
    """Test ComparisonResult string representation."""

    def test_repr(self):
        """Test repr output."""
        result = ComparisonResult(
            metric_name="jaccard",
            network_a_name="baseline",
            network_b_name="treatment",
            global_distance=0.82
        )
        
        repr_str = repr(result)
        
        assert "ComparisonResult" in repr_str
        assert "jaccard" in repr_str
        assert "baseline" in repr_str
        assert "treatment" in repr_str
        assert "0.82" in repr_str

    def test_repr_without_global_distance(self):
        """Test repr without global distance."""
        result = ComparisonResult(
            metric_name="custom",
            network_a_name="net1",
            network_b_name="net2"
        )
        
        repr_str = repr(result)
        
        assert "ComparisonResult" in repr_str
        assert "custom" in repr_str
        assert "None" in repr_str


class TestComparisonResultEdgeCases:
    """Test edge cases and error handling."""

    def test_pandas_import_error_to_pandas(self):
        """Test to_pandas raises ImportError when pandas not available."""
        result = ComparisonResult(
            metric_name="test",
            network_a_name="a",
            network_b_name="b"
        )
        
        # Mock pandas as not available
        import sys
        pandas_backup = sys.modules.get("pandas")
        if pandas_backup:
            sys.modules["pandas"] = None
        
        try:
            with pytest.raises(ImportError, match="pandas is required"):
                result.to_pandas()
        finally:
            if pandas_backup:
                sys.modules["pandas"] = pandas_backup

    def test_pandas_import_error_to_pandas_layerwise(self):
        """Test to_pandas_layerwise raises ImportError when pandas not available."""
        result = ComparisonResult(
            metric_name="test",
            network_a_name="a",
            network_b_name="b",
            layerwise_distance={"layer1": 0.5}
        )
        
        # Mock pandas as not available
        import sys
        pandas_backup = sys.modules.get("pandas")
        if pandas_backup:
            sys.modules["pandas"] = None
        
        try:
            with pytest.raises(ImportError, match="pandas is required"):
                result.to_pandas_layerwise()
        finally:
            if pandas_backup:
                sys.modules["pandas"] = pandas_backup

    def test_pandas_import_error_to_pandas_nodes(self):
        """Test to_pandas_nodes raises ImportError when pandas not available."""
        result = ComparisonResult(
            metric_name="test",
            network_a_name="a",
            network_b_name="b",
            per_node_difference={"node1": 0.5}
        )
        
        # Mock pandas as not available
        import sys
        pandas_backup = sys.modules.get("pandas")
        if pandas_backup:
            sys.modules["pandas"] = None
        
        try:
            with pytest.raises(ImportError, match="pandas is required"):
                result.to_pandas_nodes()
        finally:
            if pandas_backup:
                sys.modules["pandas"] = pandas_backup

    def test_numeric_node_keys(self):
        """Test with numeric node keys."""
        node_diff = {1: 0.1, 2: 0.3, 3: 0.5}
        result = ComparisonResult(
            metric_name="node_distance",
            network_a_name="net1",
            network_b_name="net2",
            per_node_difference=node_diff
        )
        
        assert result.per_node_difference == node_diff
        d = result.to_dict()
        assert d["per_node_difference"] == node_diff

    def test_tuple_node_keys(self):
        """Test with tuple node keys (multilayer)."""
        node_diff = {
            ("A", "layer1"): 0.1,
            ("B", "layer2"): 0.3
        }
        result = ComparisonResult(
            metric_name="multilayer_distance",
            network_a_name="net1",
            network_b_name="net2",
            per_node_difference=node_diff
        )
        
        assert result.per_node_difference == node_diff
        # Should be convertible to JSON (keys as strings)
        json_str = result.to_json()
        assert json_str is not None

    def test_zero_global_distance(self):
        """Test with zero global distance (identical networks)."""
        result = ComparisonResult(
            metric_name="jaccard",
            network_a_name="net1",
            network_b_name="net1_copy",
            global_distance=0.0
        )
        
        assert result.global_distance == 0.0

    def test_large_global_distance(self):
        """Test with large global distance."""
        result = ComparisonResult(
            metric_name="edit_distance",
            network_a_name="small_net",
            network_b_name="large_net",
            global_distance=999999.0
        )
        
        assert result.global_distance == 999999.0

    def test_negative_distances(self):
        """Test with negative distance values (similarity metrics)."""
        # Some metrics may use negative values
        result = ComparisonResult(
            metric_name="correlation",
            network_a_name="net1",
            network_b_name="net2",
            global_distance=-0.5,
            layerwise_distance={"layer1": -0.3, "layer2": -0.7}
        )
        
        assert result.global_distance == -0.5
        assert result.layerwise_distance["layer1"] == -0.3

    def test_many_layers(self):
        """Test with many layers."""
        layerwise = {f"layer_{i}": i * 0.01 for i in range(100)}
        result = ComparisonResult(
            metric_name="jaccard",
            network_a_name="net1",
            network_b_name="net2",
            layerwise_distance=layerwise
        )
        
        assert len(result.layerwise_distance) == 100

    def test_many_nodes(self):
        """Test with many nodes."""
        node_diff = {f"node_{i}": i * 0.001 for i in range(1000)}
        result = ComparisonResult(
            metric_name="node_distance",
            network_a_name="net1",
            network_b_name="net2",
            per_node_difference=node_diff
        )
        
        assert len(result.per_node_difference) == 1000


class TestComparisonResultIntegration:
    """Test realistic comparison scenarios."""

    def test_complete_comparison_workflow(self):
        """Test a complete comparison workflow."""
        pytest.importorskip("pandas")
        
        # Create a realistic comparison result
        result = ComparisonResult(
            metric_name="multiplex_jaccard",
            network_a_name="baseline_network",
            network_b_name="perturbed_network",
            global_distance=0.73,
            layerwise_distance={
                "social": 0.65,
                "work": 0.80,
                "family": 0.75
            },
            per_node_difference={
                "Alice": 0.12,
                "Bob": 0.25,
                "Carol": 0.08
            },
            meta={
                "algorithm": "fast_jaccard",
                "runtime_ms": 250.3,
                "parameters": {"weighted": True}
            }
        )
        
        # Export to different formats
        df_main = result.to_pandas()
        df_layers = result.to_pandas_layerwise()
        df_nodes = result.to_pandas_nodes()
        d = result.to_dict()
        json_str = result.to_json()
        
        # Verify all exports work
        assert len(df_main) == 1
        assert len(df_layers) == 3
        assert len(df_nodes) == 3
        assert d["metric_name"] == "multiplex_jaccard"
        assert "multiplex_jaccard" in json_str
        
        # Verify repr
        repr_str = repr(result)
        assert "0.73" in repr_str
