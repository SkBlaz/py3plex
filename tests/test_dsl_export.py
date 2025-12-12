"""Tests for DSL export functionality.

Tests cover:
- ExportSpec dataclass
- File export to CSV
- File export to JSON
- File export with column selection
- Fluent API (.export(), .export_csv(), .export_json())
- Export with no specification (should not write files)
- Error handling for invalid formats and paths
"""

import json
import pytest

from py3plex.core import multinet
from py3plex.dsl import (
    Q,
    L,
    ExportSpec,
    QueryResult,
    execute_ast,
    Query,
    SelectStmt,
    Target,
    DslExecutionError,
    export_result,
)


@pytest.fixture
def sample_network():
    """Create a sample multilayer network for testing."""
    network = multinet.multi_layer_network(directed=False)

    nodes = [
        {'source': 'A', 'type': 'social'},
        {'source': 'B', 'type': 'social'},
        {'source': 'C', 'type': 'social'},
        {'source': 'D', 'type': 'work'},
        {'source': 'E', 'type': 'work'},
    ]
    network.add_nodes(nodes)

    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'B', 'target': 'C', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'A', 'target': 'C', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'D', 'target': 'E', 'source_type': 'work', 'target_type': 'work', 'weight': 1.0},
    ]
    network.add_edges(edges)

    return network


class TestExportSpec:
    """Test ExportSpec dataclass."""

    def test_export_spec_basic(self):
        """Test basic ExportSpec creation."""
        spec = ExportSpec(path="output.csv", fmt="csv")
        assert spec.path == "output.csv"
        assert spec.fmt == "csv"
        assert spec.columns is None
        assert spec.options == {}

    def test_export_spec_with_columns(self):
        """Test ExportSpec with column selection."""
        spec = ExportSpec(
            path="output.csv",
            fmt="csv",
            columns=["node", "degree"],
        )
        assert spec.columns == ["node", "degree"]

    def test_export_spec_with_options(self):
        """Test ExportSpec with format options."""
        spec = ExportSpec(
            path="output.json",
            fmt="json",
            options={"orient": "records", "indent": 4},
        )
        assert spec.options == {"orient": "records", "indent": 4}


class TestFileExportCSV:
    """Test CSV file export functionality."""

    def test_export_degree_to_csv(self, sample_network, tmp_path):
        """Test exporting degree centrality to CSV."""
        output_file = tmp_path / "degree.csv"

        q = (
            Q.nodes()
            .from_layers(L["social"])
            .compute("degree")
            .export_csv(str(output_file))
        )
        result = q.execute(sample_network)

        # Verify result is still returned
        assert isinstance(result, QueryResult)
        assert len(result.items) == 3  # A, B, C in social layer

        # Verify file was created
        assert output_file.exists()

        # Read and verify CSV content
        content = output_file.read_text()
        lines = content.strip().split('\n')
        assert len(lines) >= 2  # Header + at least one row
        assert "id" in lines[0]  # Check for header

    def test_export_with_column_selection(self, sample_network, tmp_path):
        """Test exporting with specific columns."""
        output_file = tmp_path / "selected.csv"

        q = (
            Q.nodes()
            .from_layers(L["social"])
            .compute("degree")
            .export_csv(str(output_file), columns=["id", "degree"])
        )
        q.execute(sample_network)

        # Verify file was created
        assert output_file.exists()

        # Read and verify columns
        content = output_file.read_text()
        header = content.split('\n')[0]
        assert "id" in header
        assert "degree" in header

    def test_export_with_custom_delimiter(self, sample_network, tmp_path):
        """Test exporting CSV with custom delimiter."""
        output_file = tmp_path / "custom_delim.csv"

        q = (
            Q.nodes()
            .from_layers(L["social"])
            .compute("degree")
            .export_csv(str(output_file), delimiter=";")
        )
        q.execute(sample_network)

        # Verify file uses semicolon delimiter
        content = output_file.read_text()
        assert ";" in content


class TestFileExportJSON:
    """Test JSON file export functionality."""

    def test_export_degree_to_json(self, sample_network, tmp_path):
        """Test exporting degree centrality to JSON."""
        output_file = tmp_path / "degree.json"

        q = (
            Q.nodes()
            .from_layers(L["social"])
            .compute("degree")
            .export_json(str(output_file))
        )
        result = q.execute(sample_network)

        # Verify result is still returned
        assert isinstance(result, QueryResult)

        # Verify file was created
        assert output_file.exists()

        # Read and verify JSON content
        with open(output_file) as f:
            data = json.load(f)

        assert isinstance(data, list)  # Default orient is 'records'
        assert len(data) == 3  # A, B, C in social layer

    def test_export_json_orient_columns(self, sample_network, tmp_path):
        """Test exporting JSON with 'columns' orientation."""
        output_file = tmp_path / "degree_columns.json"

        q = (
            Q.nodes()
            .from_layers(L["social"])
            .compute("degree")
            .export_json(str(output_file), orient="columns")
        )
        q.execute(sample_network)

        # Verify JSON structure
        with open(output_file) as f:
            data = json.load(f)

        assert isinstance(data, dict)
        assert "id" in data
        assert "degree" in data

    def test_export_json_orient_split(self, sample_network, tmp_path):
        """Test exporting JSON with 'split' orientation."""
        output_file = tmp_path / "degree_split.json"

        q = (
            Q.nodes()
            .from_layers(L["social"])
            .compute("degree")
            .export_json(str(output_file), orient="split")
        )
        q.execute(sample_network)

        # Verify JSON structure
        with open(output_file) as f:
            data = json.load(f)

        assert isinstance(data, dict)
        assert "columns" in data
        assert "index" in data
        assert "data" in data


class TestFluentExportAPI:
    """Test fluent API for exports."""

    def test_export_method(self, sample_network, tmp_path):
        """Test generic .export() method."""
        output_file = tmp_path / "export.csv"

        q = (
            Q.nodes()
            .from_layers(L["social"])
            .compute("degree")
            .export(str(output_file), fmt="csv", columns=["id", "degree"])
        )
        result = q.execute(sample_network)

        assert isinstance(result, QueryResult)
        assert output_file.exists()
    
    def test_export_to_dsl_string(self, tmp_path):
        """Test that export is serialized to DSL string."""
        output_file = tmp_path / "export.csv"

        q = (
            Q.nodes()
            .from_layers(L["social"])
            .compute("degree")
            .export_csv(str(output_file), columns=["id", "degree"])
        )
        
        dsl_str = q.to_dsl()
        
        # Verify DSL string contains EXPORT clause
        assert "EXPORT TO" in dsl_str
        assert str(output_file) in dsl_str
        assert "FORMAT CSV" in dsl_str
        assert "COLUMNS (id, degree)" in dsl_str

    def test_export_tsv(self, sample_network, tmp_path):
        """Test TSV export (CSV with tab delimiter)."""
        output_file = tmp_path / "data.tsv"

        q = (
            Q.nodes()
            .from_layers(L["social"])
            .compute("degree")
            .export(str(output_file), fmt="tsv")
        )
        q.execute(sample_network)

        # Verify file uses tab delimiter
        content = output_file.read_text()
        assert "\t" in content

    def test_chaining_with_order_and_limit(self, sample_network, tmp_path):
        """Test export with ORDER BY and LIMIT."""
        output_file = tmp_path / "top_nodes.csv"

        q = (
            Q.nodes()
            .from_layers(L["social"])
            .compute("degree")
            .order_by("degree", desc=True)
            .limit(2)
            .export_csv(str(output_file))
        )
        result = q.execute(sample_network)

        # Verify only 2 results
        assert len(result.items) == 2

        # Verify file contains 2 data rows + header
        content = output_file.read_text()
        lines = content.strip().split('\n')
        assert len(lines) == 3  # Header + 2 rows


class TestExportWithoutSpec:
    """Test that queries without export specs don't write files."""

    def test_no_export_no_file(self, sample_network, tmp_path):
        """Test that no file is written without export spec."""
        q = (
            Q.nodes()
            .from_layers(L["social"])
            .compute("degree")
        )
        result = q.execute(sample_network)

        # Verify result is returned
        assert isinstance(result, QueryResult)

        # Verify no CSV/JSON files were created in tmp_path
        csv_files = list(tmp_path.glob("*.csv"))
        json_files = list(tmp_path.glob("*.json"))
        assert len(csv_files) == 0
        assert len(json_files) == 0


class TestExportErrorHandling:
    """Test error handling for export operations."""

    def test_invalid_format_raises_error_at_build_time(self):
        """Test that invalid format is caught at builder time."""
        output_file = "data.xyz"

        with pytest.raises(ValueError) as exc_info:
            q = (
                Q.nodes()
                .compute("degree")
                .export(output_file, fmt="invalid_format")
            )

        assert "Unsupported export format" in str(exc_info.value)
        assert "invalid_format" in str(exc_info.value)
        assert "csv, json, tsv" in str(exc_info.value)

    def test_export_creates_parent_directories(self, sample_network, tmp_path):
        """Test that export creates parent directories if needed."""
        output_file = tmp_path / "nested" / "dir" / "output.csv"

        q = (
            Q.nodes()
            .from_layers(L["social"])
            .compute("degree")
            .export_csv(str(output_file))
        )
        q.execute(sample_network)

        # Verify file was created in nested directory
        assert output_file.exists()
        assert output_file.parent.exists()


class TestExportMultipleFormats:
    """Test exporting to multiple formats in sequence."""

    def test_export_csv_and_json(self, sample_network, tmp_path):
        """Test that we can export to both CSV and JSON."""
        csv_file = tmp_path / "data.csv"
        json_file = tmp_path / "data.json"

        # Build query once
        q_base = Q.nodes().from_layers(L["social"]).compute("degree")

        # Export to CSV
        q_csv = q_base.export_csv(str(csv_file))
        result1 = q_csv.execute(sample_network)

        # Export to JSON (need to rebuild query since export is terminal)
        q_json = Q.nodes().from_layers(L["social"]).compute("degree").export_json(str(json_file))
        result2 = q_json.execute(sample_network)

        # Verify both files exist
        assert csv_file.exists()
        assert json_file.exists()

        # Verify both results are equivalent
        assert len(result1.items) == len(result2.items)


class TestExportEmptyResults:
    """Test exporting empty results."""

    def test_export_empty_to_csv(self, sample_network, tmp_path):
        """Test exporting empty results to CSV."""
        output_file = tmp_path / "empty.csv"

        # Query that returns no results
        q = (
            Q.nodes()
            .from_layers(L["nonexistent"])
            .export_csv(str(output_file))
        )
        result = q.execute(sample_network)

        # Verify empty result
        assert len(result.items) == 0

        # Verify file still created with header
        assert output_file.exists()
        content = output_file.read_text()
        assert len(content.strip()) > 0  # Has at least header

    def test_export_empty_to_json(self, sample_network, tmp_path):
        """Test exporting empty results to JSON."""
        output_file = tmp_path / "empty.json"

        # Query that returns no results
        q = (
            Q.nodes()
            .from_layers(L["nonexistent"])
            .export_json(str(output_file))
        )
        result = q.execute(sample_network)

        # Verify empty result
        assert len(result.items) == 0

        # Verify file created with empty array
        with open(output_file) as f:
            data = json.load(f)
        assert data == []


class TestExportNormalizationVariants:
    """Test normalization paths that feed export_result()."""

    def test_export_dict_with_tuple_keys(self, tmp_path):
        """Dict with (node, layer) keys should expand to node/layer/score columns."""
        tuple_dict = {("A", "social"): 0.5, ("B", "work"): 1.2}
        output_file = tmp_path / "tuple_keys.csv"

        export_result(tuple_dict, ExportSpec(path=str(output_file), fmt="csv"))

        lines = output_file.read_text().strip().split("\n")
        assert "node,layer,score" in lines[0]
        assert any("A" in line and "social" in line for line in lines[1:])
        assert any("B" in line and "work" in line for line in lines[1:])

    def test_export_list_of_dicts_tsv_with_column_hint(self, tmp_path):
        """List-of-dicts path should respect column hints and TSV delimiter."""
        rows = [
            {"name": "A", "score": 1, "extra": "x"},
            {"name": "B", "score": 2, "extra": "y"},
        ]
        output_file = tmp_path / "rows.tsv"

        export_result(
            rows,
            ExportSpec(path=str(output_file), fmt="tsv", columns=["name", "score"]),
        )

        content = output_file.read_text().strip().split("\n")
        # Header only includes hinted columns and uses tab delimiter
        assert content[0] == "name\tscore"
        assert content[1].startswith("A\t1")

    def test_export_dataframe_respects_columns_hint(self, tmp_path):
        """DataFrame export path should drop non-hinted columns."""
        pd = pytest.importorskip("pandas")
        df = pd.DataFrame([{"id": "A", "degree": 2, "ignore": 99}])
        output_file = tmp_path / "df.json"

        export_result(df, ExportSpec(path=str(output_file), fmt="json", columns=["id"]))

        with open(output_file) as f:
            data = json.load(f)

        # Only the hinted column should be present
        assert data == [{"id": "A"}]

    def test_export_unsupported_type_raises(self, tmp_path):
        """Unsupported result types should raise DslExecutionError."""
        output_file = tmp_path / "bad.csv"

        with pytest.raises(DslExecutionError):
            export_result({1, 2, 3}, ExportSpec(path=str(output_file), fmt="csv"))

    def test_export_unsupported_format_raises(self, tmp_path):
        """Unknown formats should be rejected with a clear DSL error."""
        output_file = tmp_path / "data.unknown"

        with pytest.raises(DslExecutionError):
            export_result({"A": 1}, ExportSpec(path=str(output_file), fmt="parquet"))
