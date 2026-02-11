"""
Tests for PathResult class.

This module tests the PathResult container for path query operations.
"""
import pytest
from py3plex.paths.result import PathResult


class TestPathResultBasics:
    """Test basic PathResult functionality."""

    def test_create_empty_path_result(self):
        """Test creating an empty PathResult."""
        result = PathResult(path_type="shortest", source="A")
        
        assert result.path_type == "shortest"
        assert result.source == "A"
        assert result.target is None
        assert result.paths == []
        assert result.visit_frequency == {}
        assert result.flow_values == {}
        assert result.meta == {}
        assert result.num_paths == 0
        assert result.shortest_path_length is None

    def test_create_path_result_with_paths(self):
        """Test creating PathResult with paths."""
        paths = [["A", "B", "C"], ["A", "D", "C"]]
        result = PathResult(
            path_type="shortest",
            source="A",
            target="C",
            paths=paths
        )
        
        assert result.paths == paths
        assert result.num_paths == 2
        assert result.shortest_path_length == 2  # Number of edges
        assert result.target == "C"

    def test_create_path_result_with_visit_frequency(self):
        """Test creating PathResult with visit frequency data."""
        visit_freq = {"A": 10, "B": 5, "C": 8}
        result = PathResult(
            path_type="random_walk",
            source="A",
            visit_frequency=visit_freq
        )
        
        assert result.visit_frequency == visit_freq

    def test_create_path_result_with_flow_values(self):
        """Test creating PathResult with flow values."""
        flow = {("A", "B"): 5.0, ("B", "C"): 3.0}
        result = PathResult(
            path_type="max_flow",
            source="A",
            target="C",
            flow_values=flow
        )
        
        assert result.flow_values == flow

    def test_create_path_result_with_meta(self):
        """Test creating PathResult with metadata."""
        meta = {"algorithm": "dijkstra", "weight": "distance"}
        result = PathResult(
            path_type="shortest",
            source="A",
            target="B",
            meta=meta
        )
        
        assert result.meta == meta
        assert result.meta["algorithm"] == "dijkstra"


class TestPathResultProperties:
    """Test PathResult properties and computed values."""

    def test_num_paths_property(self):
        """Test num_paths property."""
        result = PathResult(
            path_type="k_shortest",
            source="A",
            target="D",
            paths=[
                ["A", "B", "D"],
                ["A", "C", "D"],
                ["A", "E", "F", "D"]
            ]
        )
        
        assert result.num_paths == 3
        assert len(result) == 3  # __len__ should match

    def test_shortest_path_length(self):
        """Test shortest_path_length property."""
        result = PathResult(
            path_type="k_shortest",
            source="A",
            target="D",
            paths=[
                ["A", "B", "D"],  # Length 2
                ["A", "C", "D"],  # Length 2
                ["A", "E", "F", "G", "D"]  # Length 4
            ]
        )
        
        assert result.shortest_path_length == 2

    def test_shortest_path_length_single_node_path(self):
        """Test shortest_path_length with single node path."""
        result = PathResult(
            path_type="shortest",
            source="A",
            target="A",
            paths=[["A"]]  # Self-loop
        )
        
        assert result.shortest_path_length == 0

    def test_shortest_path_length_empty(self):
        """Test shortest_path_length with no paths."""
        result = PathResult(path_type="shortest", source="A")
        
        assert result.shortest_path_length is None


class TestPathResultIteratorProtocol:
    """Test PathResult iterator and indexing."""

    def test_iteration(self):
        """Test iterating over PathResult."""
        paths = [["A", "B"], ["A", "C"], ["A", "D"]]
        result = PathResult(
            path_type="all_simple",
            source="A",
            paths=paths
        )
        
        collected = list(result)
        assert collected == paths

    def test_indexing(self):
        """Test indexing PathResult."""
        paths = [["A", "B"], ["A", "C"], ["A", "D"]]
        result = PathResult(
            path_type="k_shortest",
            source="A",
            paths=paths
        )
        
        assert result[0] == ["A", "B"]
        assert result[1] == ["A", "C"]
        assert result[2] == ["A", "D"]
        assert result[-1] == ["A", "D"]

    def test_index_out_of_range(self):
        """Test indexing beyond available paths."""
        result = PathResult(
            path_type="shortest",
            source="A",
            paths=[["A", "B"]]
        )
        
        with pytest.raises(IndexError):
            _ = result[5]


class TestPathResultExport:
    """Test PathResult export functionality."""

    def test_to_pandas(self):
        """Test exporting paths to pandas DataFrame."""
        pytest.importorskip("pandas")
        
        paths = [
            ["A", "B", "C"],
            ["A", "D", "E", "C"],
            ["A", "F", "C"]
        ]
        result = PathResult(
            path_type="k_shortest",
            source="A",
            target="C",
            paths=paths
        )
        
        df = result.to_pandas()
        
        assert len(df) == 3
        assert list(df.columns) == ["path_id", "path_length", "path"]
        assert df["path_id"].tolist() == [0, 1, 2]
        assert df["path_length"].tolist() == [2, 3, 2]
        assert df["path"].tolist() == [
            "A -> B -> C",
            "A -> D -> E -> C",
            "A -> F -> C"
        ]

    def test_to_pandas_empty(self):
        """Test exporting empty paths to pandas."""
        pytest.importorskip("pandas")
        
        result = PathResult(path_type="shortest", source="A")
        df = result.to_pandas()
        
        assert len(df) == 0
        assert list(df.columns) == ["path_id", "path_length", "path"]

    def test_to_pandas_visit_frequency(self):
        """Test exporting visit frequency to pandas."""
        pytest.importorskip("pandas")
        
        visit_freq = {"A": 100, "B": 50, "C": 75}
        result = PathResult(
            path_type="random_walk",
            source="A",
            visit_frequency=visit_freq
        )
        
        df = result.to_pandas_visit_frequency()
        
        assert len(df) == 3
        assert list(df.columns) == ["node", "frequency"]
        assert set(df["node"]) == {"A", "B", "C"}
        assert df.set_index("node")["frequency"].to_dict() == visit_freq

    def test_to_pandas_visit_frequency_empty(self):
        """Test exporting empty visit frequency."""
        pytest.importorskip("pandas")
        
        result = PathResult(path_type="random_walk", source="A")
        df = result.to_pandas_visit_frequency()
        
        assert len(df) == 0
        assert list(df.columns) == ["node", "frequency"]

    def test_to_dict(self):
        """Test exporting to dictionary."""
        paths = [["A", "B"], ["A", "C"]]
        visit_freq = {"A": 10, "B": 5}
        meta = {"algorithm": "bfs"}
        
        result = PathResult(
            path_type="all_simple",
            source="A",
            target="B",
            paths=paths,
            visit_frequency=visit_freq,
            meta=meta
        )
        
        d = result.to_dict()
        
        assert d["path_type"] == "all_simple"
        assert d["source"] == "A"
        assert d["target"] == "B"
        assert d["num_paths"] == 2
        assert d["shortest_path_length"] == 1
        assert d["paths"] == [["A", "B"], ["A", "C"]]
        assert d["visit_frequency"] == {"A": 10, "B": 5}
        assert d["meta"] == meta

    def test_to_dict_with_numeric_nodes(self):
        """Test to_dict converts numeric nodes to strings."""
        paths = [[1, 2, 3], [1, 4, 3]]
        visit_freq = {1: 10, 2: 5, 3: 8}
        
        result = PathResult(
            path_type="shortest",
            source=1,
            target=3,
            paths=paths,
            visit_frequency=visit_freq
        )
        
        d = result.to_dict()
        
        assert d["paths"] == [["1", "2", "3"], ["1", "4", "3"]]
        assert d["visit_frequency"] == {"1": 10, "2": 5, "3": 8}


class TestPathResultRepr:
    """Test PathResult string representation."""

    def test_repr_without_target(self):
        """Test repr for result without target."""
        result = PathResult(
            path_type="random_walk",
            source="A",
            paths=[["A", "B"], ["A", "C"]]
        )
        
        repr_str = repr(result)
        assert "PathResult" in repr_str
        assert "random_walk" in repr_str
        assert "source=A" in repr_str
        assert "num_paths=2" in repr_str

    def test_repr_with_target(self):
        """Test repr for result with target."""
        result = PathResult(
            path_type="shortest",
            source="A",
            target="Z",
            paths=[["A", "B", "Z"]]
        )
        
        repr_str = repr(result)
        assert "PathResult" in repr_str
        assert "shortest" in repr_str
        assert "source=A" in repr_str
        assert "-> Z" in repr_str
        assert "num_paths=1" in repr_str

    def test_repr_empty(self):
        """Test repr for empty result."""
        result = PathResult(path_type="shortest", source="A", target="B")
        
        repr_str = repr(result)
        assert "num_paths=0" in repr_str


class TestPathResultEdgeCases:
    """Test edge cases and error handling."""

    def test_pandas_import_error_to_pandas(self):
        """Test to_pandas raises ImportError when pandas not available."""
        result = PathResult(
            path_type="shortest",
            source="A",
            paths=[["A", "B"]]
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

    def test_pandas_import_error_to_pandas_visit_frequency(self):
        """Test to_pandas_visit_frequency raises ImportError when pandas not available."""
        result = PathResult(
            path_type="random_walk",
            source="A",
            visit_frequency={"A": 10}
        )
        
        # Mock pandas as not available
        import sys
        pandas_backup = sys.modules.get("pandas")
        if pandas_backup:
            sys.modules["pandas"] = None
        
        try:
            with pytest.raises(ImportError, match="pandas is required"):
                result.to_pandas_visit_frequency()
        finally:
            if pandas_backup:
                sys.modules["pandas"] = pandas_backup

    def test_empty_paths_list(self):
        """Test with explicitly empty paths list."""
        result = PathResult(
            path_type="shortest",
            source="A",
            target="B",
            paths=[]
        )
        
        assert result.num_paths == 0
        assert len(result) == 0
        assert result.shortest_path_length is None

    def test_different_node_types(self):
        """Test with different node types (strings, integers, tuples)."""
        # String nodes
        result1 = PathResult(
            path_type="shortest",
            source="A",
            paths=[["A", "B", "C"]]
        )
        assert result1.num_paths == 1
        
        # Integer nodes
        result2 = PathResult(
            path_type="shortest",
            source=1,
            paths=[[1, 2, 3]]
        )
        assert result2.num_paths == 1
        
        # Tuple nodes (multilayer)
        result3 = PathResult(
            path_type="shortest",
            source=("A", "layer1"),
            paths=[[("A", "layer1"), ("B", "layer1"), ("C", "layer2")]]
        )
        assert result3.num_paths == 1

    def test_single_node_path(self):
        """Test path with a single node."""
        result = PathResult(
            path_type="shortest",
            source="A",
            target="A",
            paths=[["A"]]
        )
        
        assert result.num_paths == 1
        assert result.shortest_path_length == 0
        assert result[0] == ["A"]

    def test_very_long_path(self):
        """Test with a very long path."""
        long_path = [f"node_{i}" for i in range(1000)]
        result = PathResult(
            path_type="longest",
            source="node_0",
            target="node_999",
            paths=[long_path]
        )
        
        assert result.num_paths == 1
        assert result.shortest_path_length == 999
        assert len(result[0]) == 1000
