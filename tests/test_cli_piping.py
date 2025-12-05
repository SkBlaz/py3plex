"""
Tests for CLI piping functionality.

This module tests the Unix piping support for py3plex CLI commands.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from py3plex import cli
from py3plex.core import multinet


class TestCLIQueryCommand:
    """Test the 'query' command."""

    @pytest.fixture
    def sample_network(self, tmp_path):
        """Create a sample network for testing."""
        network = multinet.multi_layer_network()

        # Add nodes and edges in two layers
        for layer in ["layer1", "layer2"]:
            for i in range(5):
                network.add_nodes([{"source": f"node{i}", "type": layer}], input_type="dict")
            
            for i in range(4):
                network.add_edges([{
                    "source": f"node{i}",
                    "target": f"node{i+1}",
                    "source_type": layer,
                    "target_type": layer,
                }], input_type="dict")

        output_file = tmp_path / "test_network.edgelist"
        network.save_network(str(output_file), output_type="multiedgelist")
        return output_file

    def test_query_basic(self, sample_network, capsys):
        """Test basic query command."""
        result = cli.main([
            "query",
            str(sample_network),
            "SELECT nodes COMPUTE degree",
        ])
        assert result == 0
        
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert "nodes" in output
        assert "count" in output
        assert output["count"] == 10  # 5 nodes * 2 layers

    def test_query_json_format(self, sample_network, capsys):
        """Test query with JSON output format."""
        result = cli.main([
            "query",
            str(sample_network),
            "SELECT nodes COMPUTE degree",
            "--format", "json",
        ])
        assert result == 0
        
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert "computed" in output
        assert "degree" in output["computed"]

    def test_query_csv_format(self, sample_network, capsys):
        """Test query with CSV output format."""
        result = cli.main([
            "query",
            str(sample_network),
            "SELECT nodes COMPUTE degree",
            "--format", "csv",
        ])
        assert result == 0
        
        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        assert len(lines) > 0
        assert "node" in lines[0].lower()

    def test_query_table_format(self, sample_network, capsys):
        """Test query with table output format."""
        result = cli.main([
            "query",
            str(sample_network),
            "SELECT nodes COMPUTE degree",
            "--format", "table",
        ])
        assert result == 0
        
        captured = capsys.readouterr()
        assert "Node" in captured.out
        assert "degree" in captured.out.lower()
        assert "Total:" in captured.out

    def test_query_dsl_builder(self, sample_network, capsys):
        """Test query with Python DSL builder syntax."""
        result = cli.main([
            "query",
            str(sample_network),
            'Q.nodes().compute("degree")',
            "--dsl",
        ])
        assert result == 0
        
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert "nodes" in output
        assert "computed" in output

    def test_query_dsl_with_order_and_limit(self, sample_network, capsys):
        """Test DSL builder with order_by and limit."""
        result = cli.main([
            "query",
            str(sample_network),
            'Q.nodes().compute("degree").order_by("-degree").limit(5)',
            "--dsl",
        ])
        assert result == 0
        
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["count"] == 5

    def test_query_output_file(self, sample_network, tmp_path):
        """Test query with output to file."""
        output_file = tmp_path / "query_output.json"
        result = cli.main([
            "query",
            str(sample_network),
            "SELECT nodes COMPUTE degree",
            "--output", str(output_file),
        ])
        assert result == 0
        assert output_file.exists()
        
        with open(output_file) as f:
            output = json.load(f)
        assert "nodes" in output

    def test_query_no_query_error(self, sample_network, capsys, caplog):
        """Test error when no query provided."""
        result = cli.main([
            "query",
            str(sample_network),
        ])
        assert result == 1


class TestCLIStdinSupport:
    """Test stdin support for CLI commands."""

    @pytest.fixture
    def sample_edgelist_content(self):
        """Create sample edgelist content for stdin testing."""
        return """node0 layer1 node1 layer1 1.0
node1 layer1 node2 layer1 1.0
node0 layer2 node1 layer2 1.0
node1 layer2 node2 layer2 1.0
"""

    @pytest.fixture
    def sample_network_file(self, tmp_path, sample_edgelist_content):
        """Create a sample network file."""
        network_file = tmp_path / "network.edgelist"
        network_file.write_text(sample_edgelist_content)
        return network_file

    def test_load_from_stdin(self, sample_network_file):
        """Test loading network from stdin."""
        # Use subprocess to properly test stdin piping
        result = subprocess.run(
            [sys.executable, "-m", "py3plex", "load", "-", "--info"],
            input=sample_network_file.read_text(),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Nodes:" in result.stderr or "Nodes:" in result.stdout

    def test_query_from_stdin(self, sample_network_file):
        """Test query with stdin input."""
        result = subprocess.run(
            [sys.executable, "-m", "py3plex", "query", "-", "SELECT nodes COMPUTE degree"],
            input=sample_network_file.read_text(),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "nodes" in output

    def test_query_stdin_with_dsl(self, sample_network_file):
        """Test query from stdin with DSL builder syntax."""
        result = subprocess.run(
            [
                sys.executable, "-m", "py3plex", "query", "-",
                'Q.nodes().compute("degree")',
                "--dsl",
            ],
            input=sample_network_file.read_text(),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "nodes" in output


class TestCLIPipingIntegration:
    """Integration tests for CLI piping workflows."""

    def test_create_and_query_workflow(self, tmp_path):
        """Test workflow: create network then query it."""
        network_file = tmp_path / "workflow_network.edgelist"
        
        # Create network
        result = cli.main([
            "create",
            "--nodes", "10",
            "--layers", "2",
            "--probability", "0.3",
            "--seed", "42",
            "--output", str(network_file),
        ])
        assert result == 0
        
        # Query network
        result = cli.main([
            "query",
            str(network_file),
            "SELECT nodes COMPUTE degree",
        ])
        assert result == 0

    def test_query_multiple_measures(self, tmp_path, capsys):
        """Test querying with multiple computed measures."""
        network_file = tmp_path / "multi_measure.edgelist"
        
        # Create network
        cli.main([
            "create",
            "--nodes", "15",
            "--layers", "2",
            "--probability", "0.2",
            "--seed", "123",
            "--output", str(network_file),
        ])
        
        # Query with multiple measures
        result = cli.main([
            "query",
            str(network_file),
            "SELECT nodes COMPUTE degree, clustering, betweenness_centrality",
            "--format", "json",
        ])
        assert result == 0
        
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert "degree" in output["computed"]

    def test_query_layer_filter(self, tmp_path, capsys):
        """Test querying with layer filter."""
        network_file = tmp_path / "layer_filter.edgelist"
        
        # Create network
        cli.main([
            "create",
            "--nodes", "10",
            "--layers", "3",
            "--probability", "0.2",
            "--seed", "456",
            "--output", str(network_file),
        ])
        
        # Query specific layer
        result = cli.main([
            "query",
            str(network_file),
            'SELECT nodes WHERE layer="layer1"',
            "--format", "json",
        ])
        assert result == 0
        
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        # All returned nodes should be in layer1
        for node in output["nodes"]:
            assert "layer1" in node


class TestCLIQueryErrorHandling:
    """Test error handling in query command."""

    def test_query_invalid_file(self, capsys, caplog):
        """Test query with non-existent file."""
        result = cli.main([
            "query",
            "/nonexistent/file.edgelist",
            "SELECT nodes",
        ])
        assert result == 1

    def test_query_invalid_dsl(self, tmp_path, capsys, caplog):
        """Test query with invalid DSL syntax."""
        network_file = tmp_path / "test.edgelist"
        
        # Create minimal network
        cli.main([
            "create",
            "--nodes", "5",
            "--layers", "1",
            "--output", str(network_file),
        ])
        
        result = cli.main([
            "query",
            str(network_file),
            "Q.invalid_method()",
            "--dsl",
        ])
        assert result == 1


class TestLoadStdinInputFormat:
    """Test input format detection for stdin."""

    def test_load_stdin_multiedgelist_format(self):
        """Test loading multiedgelist format from stdin."""
        content = "A layer1 B layer1 1.0\nB layer1 C layer1 1.0\n"
        result = subprocess.run(
            [sys.executable, "-m", "py3plex", "load", "-", "--info", "--input-format", "multiedgelist"],
            input=content,
            capture_output=True,
            text=True,
        )
        # Should complete without error
        assert result.returncode == 0
