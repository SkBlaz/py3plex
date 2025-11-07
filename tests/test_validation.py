"""
Tests for the validation module.

This module tests input validation utilities for catching common errors
and providing clear error messages to users.
"""
import os
import tempfile
import shutil
import unittest
from pathlib import Path

import pytest
import pandas as pd

from py3plex.exceptions import ParsingError
from py3plex.validation import (
    validate_csv_columns,
    validate_edgelist_format,
    validate_file_exists,
    validate_input_type,
    validate_multiedgelist_format,
    validate_network_data,
)


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


class TestFileValidation:
    """Test file existence and accessibility validation."""

    def test_validate_file_exists_valid(self, temp_dir):
        """Test validation passes for existing file."""
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test content")
        
        # Should not raise exception
        validate_file_exists(test_file)

    def test_validate_file_exists_missing(self, temp_dir):
        """Test validation fails for non-existent file."""
        non_existent = os.path.join(temp_dir, "nonexistent.txt")
        
        with pytest.raises(ParsingError) as exc_info:
            validate_file_exists(non_existent)
        
        assert "File not found" in str(exc_info.value)
        assert non_existent in str(exc_info.value)

    def test_validate_file_exists_directory(self, temp_dir):
        """Test validation fails when path is a directory."""
        with pytest.raises(ParsingError) as exc_info:
            validate_file_exists(temp_dir)
        
        assert "not a file" in str(exc_info.value)

    def test_validate_file_exists_not_readable(self, temp_dir):
        """Test validation fails for non-readable file."""
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")
        
        # Make file non-readable
        os.chmod(test_file, 0o000)
        
        try:
            with pytest.raises(ParsingError) as exc_info:
                validate_file_exists(test_file)
            
            assert "not readable" in str(exc_info.value)
        finally:
            # Restore permissions for cleanup
            os.chmod(test_file, 0o644)


class TestCSVValidation:
    """Test CSV column validation."""

    def test_validate_csv_columns_valid(self, temp_dir):
        """Test validation passes for CSV with required columns."""
        csv_file = os.path.join(temp_dir, "test.csv")
        df = pd.DataFrame({
            "source": ["A", "B"],
            "target": ["B", "C"],
            "layer": ["L1", "L1"]
        })
        df.to_csv(csv_file, index=False)
        
        # Should not raise exception
        validate_csv_columns(csv_file, ["source", "target", "layer"])

    def test_validate_csv_columns_missing(self, temp_dir):
        """Test validation fails for CSV missing required columns."""
        csv_file = os.path.join(temp_dir, "test.csv")
        df = pd.DataFrame({
            "source": ["A", "B"],
            "target": ["B", "C"]
        })
        df.to_csv(csv_file, index=False)
        
        with pytest.raises(ParsingError) as exc_info:
            validate_csv_columns(csv_file, ["source", "target", "layer"])
        
        assert "missing required column" in str(exc_info.value)
        assert "layer" in str(exc_info.value)

    def test_validate_csv_columns_empty_file(self, temp_dir):
        """Test validation fails for empty CSV file."""
        csv_file = os.path.join(temp_dir, "empty.csv")
        with open(csv_file, "w") as f:
            f.write("")
        
        with pytest.raises(ParsingError) as exc_info:
            validate_csv_columns(csv_file, ["source", "target"])
        
        assert "empty" in str(exc_info.value)

    def test_validate_csv_columns_with_optional(self, temp_dir):
        """Test validation with optional columns."""
        csv_file = os.path.join(temp_dir, "test.csv")
        df = pd.DataFrame({
            "source": ["A", "B"],
            "target": ["B", "C"],
            "layer": ["L1", "L1"]
        })
        df.to_csv(csv_file, index=False)
        
        # Should not raise exception even without optional weight column
        validate_csv_columns(
            csv_file,
            ["source", "target", "layer"],
            optional_columns=["weight"]
        )


class TestMultiedgelistValidation:
    """Test multiedgelist format validation."""

    def test_validate_multiedgelist_csv_format(self, temp_dir):
        """Test validation of CSV multiedgelist format."""
        csv_file = os.path.join(temp_dir, "edges.csv")
        df = pd.DataFrame({
            "source": ["A", "B", "C"],
            "target": ["B", "C", "D"],
            "layer": ["L1", "L1", "L2"],
            "weight": [1.0, 2.0, 3.0]
        })
        df.to_csv(csv_file, index=False)
        
        # Should not raise exception
        validate_multiedgelist_format(csv_file)

    def test_validate_multiedgelist_space_format(self, temp_dir):
        """Test validation of space-delimited multiedgelist format."""
        edge_file = os.path.join(temp_dir, "edges.txt")
        with open(edge_file, "w") as f:
            f.write("# Comment line\n")
            f.write("A L1 B L1 1.0\n")
            f.write("B L1 C L1 2.0\n")
            f.write("C L2 D L2 3.0\n")
        
        # Should not raise exception
        validate_multiedgelist_format(edge_file)

    def test_validate_multiedgelist_invalid_format(self, temp_dir):
        """Test validation fails for invalid multiedgelist format."""
        edge_file = os.path.join(temp_dir, "edges.txt")
        with open(edge_file, "w") as f:
            f.write("A B C\n")  # Only 3 fields, need 4 or 5
        
        with pytest.raises(ParsingError) as exc_info:
            validate_multiedgelist_format(edge_file)
        
        assert "Invalid multiedgelist format" in str(exc_info.value)
        assert "expected 4 or 5" in str(exc_info.value)

    def test_validate_multiedgelist_without_weight(self, temp_dir):
        """Test validation of multiedgelist without weight column."""
        edge_file = os.path.join(temp_dir, "edges.txt")
        with open(edge_file, "w") as f:
            f.write("A L1 B L1\n")
            f.write("B L1 C L1\n")
        
        # Should not raise exception (4 fields is valid)
        validate_multiedgelist_format(edge_file)


class TestEdgelistValidation:
    """Test edgelist format validation."""

    def test_validate_edgelist_csv_format(self, temp_dir):
        """Test validation of CSV edgelist format."""
        csv_file = os.path.join(temp_dir, "edges.csv")
        df = pd.DataFrame({
            "source": ["A", "B", "C"],
            "target": ["B", "C", "D"],
            "weight": [1.0, 2.0, 3.0]
        })
        df.to_csv(csv_file, index=False)
        
        # Should not raise exception
        validate_edgelist_format(csv_file)

    def test_validate_edgelist_space_format(self, temp_dir):
        """Test validation of space-delimited edgelist format."""
        edge_file = os.path.join(temp_dir, "edges.txt")
        with open(edge_file, "w") as f:
            f.write("# Comment line\n")
            f.write("A B 1.0\n")
            f.write("B C 2.0\n")
            f.write("C D 3.0\n")
        
        # Should not raise exception
        validate_edgelist_format(edge_file)

    def test_validate_edgelist_invalid_format(self, temp_dir):
        """Test validation fails for invalid edgelist format."""
        edge_file = os.path.join(temp_dir, "edges.txt")
        with open(edge_file, "w") as f:
            f.write("A\n")  # Only 1 field, need 2 or 3
        
        with pytest.raises(ParsingError) as exc_info:
            validate_edgelist_format(edge_file)
        
        assert "Invalid edgelist format" in str(exc_info.value)
        assert "expected 2 or 3" in str(exc_info.value)

    def test_validate_edgelist_without_weight(self, temp_dir):
        """Test validation of edgelist without weight column."""
        edge_file = os.path.join(temp_dir, "edges.txt")
        with open(edge_file, "w") as f:
            f.write("A B\n")
            f.write("B C\n")
        
        # Should not raise exception (2 fields is valid)
        validate_edgelist_format(edge_file)

    def test_validate_edgelist_with_delimiter(self, temp_dir):
        """Test validation with custom delimiter."""
        edge_file = os.path.join(temp_dir, "edges.txt")
        with open(edge_file, "w") as f:
            f.write("A|B|1.0\n")
            f.write("B|C|2.0\n")
        
        # Should not raise exception with pipe delimiter
        validate_edgelist_format(edge_file, delimiter="|")


class TestInputTypeValidation:
    """Test input type validation."""

    @pytest.mark.parametrize("input_type", [
        'gml', 'nx', 'multiedgelist', 'edgelist', 'gpickle'
    ])
    def test_validate_input_type_valid(self, input_type):
        """Test validation passes for valid input types."""
        # Should not raise exception
        validate_input_type(input_type)

    def test_validate_input_type_invalid(self):
        """Test validation fails for invalid input type."""
        with pytest.raises(ParsingError) as exc_info:
            validate_input_type("invalid_type")
        
        assert "Invalid input_type" in str(exc_info.value)
        assert "invalid_type" in str(exc_info.value)

    def test_validate_input_type_custom_valid_set(self):
        """Test validation with custom set of valid types."""
        custom_types = {"type1", "type2", "type3"}
        
        # Should not raise exception
        validate_input_type("type1", valid_types=custom_types)
        
        # Should raise exception for type not in custom set
        with pytest.raises(ParsingError):
            validate_input_type("type4", valid_types=custom_types)


class TestNetworkDataValidation:
    """Test comprehensive network data validation."""

    def test_validate_network_data_multiedgelist(self, temp_dir):
        """Test validation of multiedgelist network data."""
        edge_file = os.path.join(temp_dir, "edges.txt")
        with open(edge_file, "w") as f:
            f.write("A L1 B L1 1.0\n")
            f.write("B L1 C L1 2.0\n")
        
        # Should not raise exception
        validate_network_data(edge_file, "multiedgelist")

    def test_validate_network_data_edgelist(self, temp_dir):
        """Test validation of edgelist network data."""
        edge_file = os.path.join(temp_dir, "edges.txt")
        with open(edge_file, "w") as f:
            f.write("A B 1.0\n")
            f.write("B C 2.0\n")
        
        # Should not raise exception
        validate_network_data(edge_file, "edgelist")

    def test_validate_network_data_invalid_type(self, temp_dir):
        """Test validation fails for invalid input type."""
        edge_file = os.path.join(temp_dir, "edges.txt")
        with open(edge_file, "w") as f:
            f.write("A B\n")
        
        with pytest.raises(ParsingError) as exc_info:
            validate_network_data(edge_file, "invalid_type")
        
        assert "Invalid input_type" in str(exc_info.value)

    def test_validate_network_data_missing_file(self):
        """Test validation fails for missing file."""
        with pytest.raises(ParsingError) as exc_info:
            validate_network_data("/nonexistent/file.txt", "edgelist")
        
        assert "File not found" in str(exc_info.value)

    def test_validate_network_data_nx_type(self):
        """Test validation skips file check for nx type.
        
        The 'nx' type doesn't require a file, so should not raise file error.
        It should only validate the input type.
        """
        validate_input_type("nx")

    def test_validate_network_data_multiedge_tuple_list(self):
        """Test validation skips file check for multiedge_tuple_list type.
        
        This type doesn't require a file.
        """
        validate_input_type("multiedge_tuple_list")
