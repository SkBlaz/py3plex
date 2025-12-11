"""
Tests for py3plex.validation module.

This module tests input validation utilities.
"""

import pytest
import os
import tempfile
from pathlib import Path

from py3plex.validation import (
    validate_file_exists,
    validate_csv_columns,
    validate_multiedgelist_format,
)
from py3plex.exceptions import ParsingError


class TestValidateFileExists:
    """Test the validate_file_exists function."""

    def test_valid_file(self, tmp_path):
        """Test validation passes for existing file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        # Should not raise
        validate_file_exists(str(test_file))

    def test_nonexistent_file(self, tmp_path):
        """Test validation fails for nonexistent file."""
        nonexistent = tmp_path / "nonexistent.txt"
        
        with pytest.raises(ParsingError, match="File not found"):
            validate_file_exists(str(nonexistent))

    def test_directory_not_file(self, tmp_path):
        """Test validation fails when path is a directory."""
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()
        
        with pytest.raises(ParsingError, match="not a file"):
            validate_file_exists(str(test_dir))

    def test_unreadable_file(self, tmp_path):
        """Test validation fails for unreadable file."""
        test_file = tmp_path / "unreadable.txt"
        test_file.write_text("test")
        
        # Make file unreadable (only works on Unix-like systems)
        if os.name != 'nt':  # Skip on Windows
            os.chmod(test_file, 0o000)
            
            try:
                with pytest.raises(ParsingError, match="not readable"):
                    validate_file_exists(str(test_file))
            finally:
                # Restore permissions for cleanup
                os.chmod(test_file, 0o644)


class TestValidateCSVColumns:
    """Test the validate_csv_columns function."""

    def test_valid_csv_with_required_columns(self, tmp_path):
        """Test validation passes for CSV with all required columns."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("source,target,layer,weight\nA,B,L1,1.0\n")
        
        validate_csv_columns(
            str(csv_file),
            required_columns=["source", "target", "layer"]
        )

    def test_csv_missing_required_columns(self, tmp_path):
        """Test validation fails when required columns are missing."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("source,target\nA,B\n")
        
        with pytest.raises(ParsingError, match="missing required column"):
            validate_csv_columns(
                str(csv_file),
                required_columns=["source", "target", "layer"]
            )

    def test_csv_with_optional_columns(self, tmp_path):
        """Test validation with optional columns."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("source,target,layer\nA,B,L1\n")
        
        # Should pass even without optional column
        validate_csv_columns(
            str(csv_file),
            required_columns=["source", "target", "layer"],
            optional_columns=["weight"]
        )

    def test_empty_csv_file(self, tmp_path):
        """Test validation fails for empty CSV file."""
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("")
        
        with pytest.raises(ParsingError, match="empty"):
            validate_csv_columns(
                str(csv_file),
                required_columns=["source", "target"]
            )

    def test_malformed_csv(self, tmp_path):
        """Test validation fails for malformed CSV."""
        csv_file = tmp_path / "malformed.csv"
        csv_file.write_text('source,target\n"A,B\nC,D\n')  # Unclosed quote
        
        with pytest.raises(ParsingError, match="Failed to parse"):
            validate_csv_columns(
                str(csv_file),
                required_columns=["source", "target"]
            )


class TestValidateMultiedgelistFormat:
    """Test the validate_multiedgelist_format function."""

    def test_valid_space_delimited_format(self, tmp_path):
        """Test validation passes for valid space-delimited format."""
        edge_file = tmp_path / "edges.txt"
        edge_file.write_text(
            "A B layer1 1.0\n"
            "B C layer1 1.0\n"
            "C D layer2 2.0\n"
        )
        
        validate_multiedgelist_format(str(edge_file))

    def test_valid_csv_format(self, tmp_path):
        """Test validation passes for CSV format."""
        edge_file = tmp_path / "edges.csv"
        edge_file.write_text(
            "source,target,layer,weight\n"
            "A,B,layer1,1.0\n"
            "B,C,layer1,1.0\n"
        )
        
        validate_multiedgelist_format(str(edge_file))

    def test_space_delimited_with_comments(self, tmp_path):
        """Test validation ignores comment lines."""
        edge_file = tmp_path / "edges.txt"
        edge_file.write_text(
            "# This is a comment\n"
            "A B layer1 1.0\n"
            "# Another comment\n"
            "B C layer1 1.0\n"
        )
        
        validate_multiedgelist_format(str(edge_file))

    def test_invalid_column_count(self, tmp_path):
        """Test validation fails for wrong number of columns."""
        edge_file = tmp_path / "edges.txt"
        edge_file.write_text(
            "A B\n"  # Only 2 columns, need at least 4
            "C D layer1 1.0\n"
        )
        
        with pytest.raises(ParsingError, match="expected 4 or 5"):
            validate_multiedgelist_format(str(edge_file))

    def test_nonexistent_file(self, tmp_path):
        """Test validation fails for nonexistent file."""
        nonexistent = tmp_path / "nonexistent.txt"
        
        with pytest.raises(ParsingError, match="File not found"):
            validate_multiedgelist_format(str(nonexistent))

    def test_empty_lines_ignored(self, tmp_path):
        """Test that empty lines are properly ignored."""
        edge_file = tmp_path / "edges.txt"
        edge_file.write_text(
            "A B layer1 1.0\n"
            "\n"
            "B C layer1 1.0\n"
            "\n"
        )
        
        validate_multiedgelist_format(str(edge_file))

    def test_custom_delimiter(self, tmp_path):
        """Test validation with custom delimiter."""
        edge_file = tmp_path / "edges.txt"
        edge_file.write_text(
            "A|B|layer1|1.0\n"
            "B|C|layer1|1.0\n"
        )
        
        validate_multiedgelist_format(str(edge_file), delimiter="|")

    def test_five_column_format(self, tmp_path):
        """Test validation accepts 5-column format (with extra metadata)."""
        edge_file = tmp_path / "edges.txt"
        edge_file.write_text(
            "A B layer1 1.0 extra\n"
            "B C layer1 1.0 extra\n"
        )
        
        validate_multiedgelist_format(str(edge_file))
