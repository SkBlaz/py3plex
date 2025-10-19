"""
Tests for the py3plex CLI tool.

This module tests all CLI commands and their functionality.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import networkx as nx
import pytest

from py3plex import cli
from py3plex.core import multinet


class TestCLIBasic:
    """Test basic CLI functionality."""

    def test_cli_help(self):
        """Test that --help works."""
        result = cli.main(["--help"])
        assert result == 0

    def test_cli_version(self, capsys):
        """Test that --version works."""
        with pytest.raises(SystemExit) as exc_info:
            cli.main(["--version"])
        assert exc_info.value.code == 0

    def test_cli_no_command(self):
        """Test CLI with no command shows help."""
        result = cli.main([])
        assert result == 0

    def test_cli_invalid_command(self, capsys):
        """Test CLI with invalid command."""
        result = cli.main(["invalid_command"])
        assert result != 0


class TestCLICreate:
    """Test the 'create' command."""

    def test_create_simple_network(self, tmp_path):
        """Test creating a simple network."""
        output_file = tmp_path / "network.graphml"
        result = cli.main(
            [
                "create",
                "--nodes",
                "10",
                "--layers",
                "2",
                "--output",
                str(output_file),
                "--seed",
                "42",
            ]
        )
        assert result == 0
        assert output_file.exists()

        # Load and verify
        G = nx.read_graphml(str(output_file))
        assert G.number_of_nodes() > 0

    def test_create_er_network(self, tmp_path):
        """Test creating Erdős-Rényi network."""
        output_file = tmp_path / "er_network.graphml"
        result = cli.main(
            [
                "create",
                "--nodes",
                "20",
                "--layers",
                "2",
                "--type",
                "er",
                "--probability",
                "0.2",
                "--output",
                str(output_file),
                "--seed",
                "42",
            ]
        )
        assert result == 0
        assert output_file.exists()

    def test_create_ba_network(self, tmp_path):
        """Test creating Barabási-Albert network."""
        output_file = tmp_path / "ba_network.graphml"
        result = cli.main(
            [
                "create",
                "--nodes",
                "20",
                "--layers",
                "2",
                "--type",
                "ba",
                "--probability",
                "0.1",
                "--output",
                str(output_file),
                "--seed",
                "42",
            ]
        )
        assert result == 0
        assert output_file.exists()

    def test_create_ws_network(self, tmp_path):
        """Test creating Watts-Strogatz network."""
        output_file = tmp_path / "ws_network.graphml"
        result = cli.main(
            [
                "create",
                "--nodes",
                "20",
                "--layers",
                "2",
                "--type",
                "ws",
                "--probability",
                "0.2",
                "--output",
                str(output_file),
                "--seed",
                "42",
            ]
        )
        assert result == 0
        assert output_file.exists()

    def test_create_gexf_format(self, tmp_path):
        """Test creating network in GEXF format."""
        output_file = tmp_path / "network.gexf"
        result = cli.main(
            [
                "create",
                "--nodes",
                "10",
                "--layers",
                "2",
                "--output",
                str(output_file),
                "--seed",
                "42",
            ]
        )
        assert result == 0
        assert output_file.exists()

    def test_create_gpickle_format(self, tmp_path):
        """Test creating network in gpickle format."""
        output_file = tmp_path / "network.gpickle"
        result = cli.main(
            [
                "create",
                "--nodes",
                "10",
                "--layers",
                "2",
                "--output",
                str(output_file),
                "--seed",
                "42",
            ]
        )
        assert result == 0
        assert output_file.exists()


class TestCLILoad:
    """Test the 'load' command."""

    @pytest.fixture
    def sample_network(self, tmp_path):
        """Create a sample network for testing."""
        network = multinet.multi_layer_network()

        # Add nodes using dict format
        for layer in ["layer1", "layer2"]:
            nodes_dict = [{"source": f"node{i}", "type": layer} for i in range(5)]
            network.add_nodes(nodes_dict, input_type="dict")

        # Add some edges
        for layer in ["layer1", "layer2"]:
            edges_dict = [
                {
                    "source": f"node{i}",
                    "target": f"node{i+1}",
                    "source_type": layer,
                    "target_type": layer,
                }
                for i in range(4)
            ]
            network.add_edges(edges_dict, input_type="dict")

        output_file = tmp_path / "test_network.graphml"
        nx.write_graphml(network.core_network, str(output_file))
        return output_file

    def test_load_info(self, sample_network):
        """Test loading and displaying network info."""
        result = cli.main(["load", str(sample_network), "--info"])
        assert result == 0

    def test_load_stats(self, sample_network):
        """Test loading and displaying network stats."""
        result = cli.main(["load", str(sample_network), "--stats"])
        assert result == 0

    def test_load_with_output(self, sample_network, tmp_path):
        """Test loading and saving output to JSON."""
        output_file = tmp_path / "load_output.json"
        result = cli.main(
            ["load", str(sample_network), "--info", "--output", str(output_file)]
        )
        assert result == 0
        assert output_file.exists()

        # Verify JSON structure
        with open(output_file) as f:
            data = json.load(f)
            assert "info" in data
            assert "nodes" in data["info"]
            assert "edges" in data["info"]
            assert "layers" in data["info"]


class TestCLICommunity:
    """Test the 'community' command."""

    @pytest.fixture
    def sample_network(self, tmp_path):
        """Create a sample network for community detection testing."""
        network = multinet.multi_layer_network()

        # Add nodes using dict format
        nodes_dict = [{"source": f"node{i}", "type": "layer1"} for i in range(10)]
        network.add_nodes(nodes_dict, input_type="dict")

        # First community (0-4)
        edges_dict = []
        for i in range(4):
            for j in range(i + 1, 5):
                edges_dict.append({
                    "source": f"node{i}",
                    "target": f"node{j}",
                    "source_type": "layer1",
                    "target_type": "layer1",
                })

        # Second community (5-9)
        for i in range(5, 9):
            for j in range(i + 1, 10):
                edges_dict.append({
                    "source": f"node{i}",
                    "target": f"node{j}",
                    "source_type": "layer1",
                    "target_type": "layer1",
                })

        network.add_edges(edges_dict, input_type="dict")

        output_file = tmp_path / "community_test.graphml"
        nx.write_graphml(network.core_network, str(output_file))
        return output_file

    def test_community_louvain(self, sample_network):
        """Test Louvain community detection."""
        result = cli.main(["community", str(sample_network), "--algorithm", "louvain"])
        assert result == 0

    def test_community_label_prop(self, sample_network):
        """Test label propagation community detection."""
        result = cli.main(
            ["community", str(sample_network), "--algorithm", "label_prop"]
        )
        assert result == 0

    def test_community_with_output(self, sample_network, tmp_path):
        """Test community detection with JSON output."""
        output_file = tmp_path / "communities.json"
        result = cli.main(
            [
                "community",
                str(sample_network),
                "--algorithm",
                "louvain",
                "--output",
                str(output_file),
            ]
        )
        assert result == 0
        assert output_file.exists()

        # Verify JSON structure
        with open(output_file) as f:
            data = json.load(f)
            assert "algorithm" in data
            assert "num_communities" in data
            assert "communities" in data
            assert data["num_communities"] > 0

    def test_community_with_resolution(self, sample_network, tmp_path):
        """Test community detection with custom resolution."""
        result = cli.main(
            [
                "community",
                str(sample_network),
                "--algorithm",
                "louvain",
                "--resolution",
                "0.5",
            ]
        )
        assert result == 0


class TestCLICentrality:
    """Test the 'centrality' command."""

    @pytest.fixture
    def sample_network(self, tmp_path):
        """Create a sample network for centrality testing."""
        network = multinet.multi_layer_network()

        # Add nodes using dict format
        nodes_dict = [{"source": f"node{i}", "type": "layer1"} for i in range(10)]
        network.add_nodes(nodes_dict, input_type="dict")

        # Create a star topology (node0 is hub)
        edges_dict = [
            {
                "source": "node0",
                "target": f"node{i}",
                "source_type": "layer1",
                "target_type": "layer1",
            }
            for i in range(1, 10)
        ]
        network.add_edges(edges_dict, input_type="dict")

        output_file = tmp_path / "centrality_test.graphml"
        nx.write_graphml(network.core_network, str(output_file))
        return output_file

    def test_centrality_degree(self, sample_network):
        """Test degree centrality."""
        result = cli.main(["centrality", str(sample_network), "--measure", "degree"])
        assert result == 0

    def test_centrality_betweenness(self, sample_network):
        """Test betweenness centrality."""
        result = cli.main(
            ["centrality", str(sample_network), "--measure", "betweenness"]
        )
        assert result == 0

    def test_centrality_closeness(self, sample_network):
        """Test closeness centrality."""
        result = cli.main(
            ["centrality", str(sample_network), "--measure", "closeness"]
        )
        assert result == 0

    def test_centrality_eigenvector(self, sample_network):
        """Test eigenvector centrality."""
        result = cli.main(
            ["centrality", str(sample_network), "--measure", "eigenvector"]
        )
        assert result == 0

    def test_centrality_pagerank(self, sample_network):
        """Test PageRank centrality."""
        result = cli.main(
            ["centrality", str(sample_network), "--measure", "pagerank"]
        )
        assert result == 0

    def test_centrality_with_output(self, sample_network, tmp_path):
        """Test centrality with JSON output."""
        output_file = tmp_path / "centrality.json"
        result = cli.main(
            [
                "centrality",
                str(sample_network),
                "--measure",
                "degree",
                "--output",
                str(output_file),
            ]
        )
        assert result == 0
        assert output_file.exists()

        # Verify JSON structure
        with open(output_file) as f:
            data = json.load(f)
            assert "measure" in data
            assert "centrality" in data
            assert "top_nodes" in data

    def test_centrality_top_n(self, sample_network):
        """Test centrality with top N filter."""
        result = cli.main(
            [
                "centrality",
                str(sample_network),
                "--measure",
                "degree",
                "--top",
                "5",
            ]
        )
        assert result == 0


class TestCLIStats:
    """Test the 'stats' command."""

    @pytest.fixture
    def sample_network(self, tmp_path):
        """Create a sample network for statistics testing."""
        network = multinet.multi_layer_network()

        # Add nodes using dict format
        for layer in ["layer1", "layer2"]:
            nodes_dict = [{"source": f"node{i}", "type": layer} for i in range(8)]
            network.add_nodes(nodes_dict, input_type="dict")

            # Create some edges
            edges_dict = [
                {
                    "source": f"node{i}",
                    "target": f"node{i+1}",
                    "source_type": layer,
                    "target_type": layer,
                }
                for i in range(7)
            ]
            network.add_edges(edges_dict, input_type="dict")

        output_file = tmp_path / "stats_test.graphml"
        nx.write_graphml(network.core_network, str(output_file))
        return output_file

        output_file = tmp_path / "stats_test.graphml"
        nx.write_graphml(network.core_network, str(output_file))
        return output_file

    def test_stats_all(self, sample_network):
        """Test computing all statistics."""
        result = cli.main(["stats", str(sample_network), "--measure", "all"])
        assert result == 0

    def test_stats_density(self, sample_network):
        """Test computing density statistics."""
        result = cli.main(["stats", str(sample_network), "--measure", "density"])
        assert result == 0

    def test_stats_clustering(self, sample_network):
        """Test computing clustering statistics."""
        result = cli.main(["stats", str(sample_network), "--measure", "clustering"])
        assert result == 0

    def test_stats_layer_density(self, sample_network):
        """Test computing layer density."""
        result = cli.main(
            ["stats", str(sample_network), "--measure", "layer_density"]
        )
        assert result == 0

    def test_stats_with_output(self, sample_network, tmp_path):
        """Test statistics with JSON output."""
        output_file = tmp_path / "stats.json"
        result = cli.main(
            [
                "stats",
                str(sample_network),
                "--measure",
                "all",
                "--output",
                str(output_file),
            ]
        )
        assert result == 0
        assert output_file.exists()

        # Verify JSON structure
        with open(output_file) as f:
            data = json.load(f)
            assert isinstance(data, dict)


class TestCLIVisualize:
    """Test the 'visualize' command."""

    @pytest.fixture
    def sample_network(self, tmp_path):
        """Create a sample network for visualization testing."""
        network = multinet.multi_layer_network()

        # Add nodes using dict format
        nodes_dict = [{"source": f"node{i}", "type": "layer1"} for i in range(8)]
        network.add_nodes(nodes_dict, input_type="dict")

        # Create edges
        edges_dict = [
            {
                "source": f"node{i}",
                "target": f"node{i+1}",
                "source_type": "layer1",
                "target_type": "layer1",
            }
            for i in range(7)
        ]
        network.add_edges(edges_dict, input_type="dict")

        output_file = tmp_path / "viz_test.graphml"
        nx.write_graphml(network.core_network, str(output_file))
        return output_file

    def test_visualize_multilayer(self, sample_network, tmp_path):
        """Test multilayer visualization."""
        output_file = tmp_path / "viz_multilayer.png"
        result = cli.main(
            [
                "visualize",
                str(sample_network),
                "--layout",
                "multilayer",
                "--output",
                str(output_file),
            ]
        )
        assert result == 0
        assert output_file.exists()

    def test_visualize_spring(self, sample_network, tmp_path):
        """Test spring layout visualization."""
        output_file = tmp_path / "viz_spring.png"
        result = cli.main(
            [
                "visualize",
                str(sample_network),
                "--layout",
                "spring",
                "--output",
                str(output_file),
            ]
        )
        assert result == 0
        assert output_file.exists()

    def test_visualize_circular(self, sample_network, tmp_path):
        """Test circular layout visualization."""
        output_file = tmp_path / "viz_circular.png"
        result = cli.main(
            [
                "visualize",
                str(sample_network),
                "--layout",
                "circular",
                "--output",
                str(output_file),
            ]
        )
        assert result == 0
        assert output_file.exists()

    def test_visualize_custom_size(self, sample_network, tmp_path):
        """Test visualization with custom figure size."""
        output_file = tmp_path / "viz_custom.png"
        result = cli.main(
            [
                "visualize",
                str(sample_network),
                "--layout",
                "spring",
                "--width",
                "10",
                "--height",
                "6",
                "--output",
                str(output_file),
            ]
        )
        assert result == 0
        assert output_file.exists()


class TestCLIAggregate:
    """Test the 'aggregate' command."""

    @pytest.fixture
    def sample_network(self, tmp_path):
        """Create a sample multilayer network for aggregation testing."""
        network = multinet.multi_layer_network()

        # Add nodes using dict format
        for layer in ["layer1", "layer2"]:
            nodes_dict = [{"source": f"node{i}", "type": layer} for i in range(5)]
            network.add_nodes(nodes_dict, input_type="dict")

            # Create edges
            edges_dict = [
                {
                    "source": f"node{i}",
                    "target": f"node{i+1}",
                    "source_type": layer,
                    "target_type": layer,
                }
                for i in range(4)
            ]
            network.add_edges(edges_dict, input_type="dict")

        output_file = tmp_path / "aggregate_test.graphml"
        nx.write_graphml(network.core_network, str(output_file))
        return output_file

    def test_aggregate_sum(self, sample_network, tmp_path):
        """Test aggregation with sum method."""
        output_file = tmp_path / "aggregated_sum.graphml"
        result = cli.main(
            [
                "aggregate",
                str(sample_network),
                "--method",
                "sum",
                "--output",
                str(output_file),
            ]
        )
        assert result == 0
        assert output_file.exists()

    def test_aggregate_mean(self, sample_network, tmp_path):
        """Test aggregation with mean method."""
        output_file = tmp_path / "aggregated_mean.graphml"
        result = cli.main(
            [
                "aggregate",
                str(sample_network),
                "--method",
                "mean",
                "--output",
                str(output_file),
            ]
        )
        assert result == 0
        assert output_file.exists()


class TestCLIConvert:
    """Test the 'convert' command."""

    @pytest.fixture
    def sample_network(self, tmp_path):
        """Create a sample network for conversion testing."""
        network = multinet.multi_layer_network()

        # Add nodes using dict format
        nodes_dict = [{"source": f"node{i}", "type": "layer1"} for i in range(5)]
        network.add_nodes(nodes_dict, input_type="dict")

        # Create edges
        edges_dict = [
            {
                "source": f"node{i}",
                "target": f"node{i+1}",
                "source_type": "layer1",
                "target_type": "layer1",
            }
            for i in range(4)
        ]
        network.add_edges(edges_dict, input_type="dict")

        output_file = tmp_path / "convert_test.graphml"
        nx.write_graphml(network.core_network, str(output_file))
        return output_file

    def test_convert_to_gexf(self, sample_network, tmp_path):
        """Test conversion to GEXF format."""
        output_file = tmp_path / "converted.gexf"
        result = cli.main(
            ["convert", str(sample_network), "--output", str(output_file)]
        )
        assert result == 0
        assert output_file.exists()

    def test_convert_to_gpickle(self, sample_network, tmp_path):
        """Test conversion to gpickle format."""
        output_file = tmp_path / "converted.gpickle"
        result = cli.main(
            ["convert", str(sample_network), "--output", str(output_file)]
        )
        assert result == 0
        assert output_file.exists()

    def test_convert_to_json(self, sample_network, tmp_path):
        """Test conversion to JSON format."""
        output_file = tmp_path / "converted.json"
        result = cli.main(
            ["convert", str(sample_network), "--output", str(output_file)]
        )
        assert result == 0
        assert output_file.exists()

        # Verify JSON structure
        with open(output_file) as f:
            data = json.load(f)
            assert "nodes" in data
            assert "edges" in data
            assert "layers" in data


class TestCLIIntegration:
    """Integration tests for CLI workflows."""

    def test_create_load_community_workflow(self, tmp_path):
        """Test complete workflow: create -> load -> community detection."""
        # Create network
        network_file = tmp_path / "workflow.graphml"
        result = cli.main(
            [
                "create",
                "--nodes",
                "20",
                "--layers",
                "2",
                "--type",
                "er",
                "--probability",
                "0.3",
                "--output",
                str(network_file),
                "--seed",
                "42",
            ]
        )
        assert result == 0

        # Load and inspect
        result = cli.main(["load", str(network_file), "--info"])
        assert result == 0

        # Detect communities
        comm_file = tmp_path / "communities.json"
        result = cli.main(
            [
                "community",
                str(network_file),
                "--algorithm",
                "louvain",
                "--output",
                str(comm_file),
            ]
        )
        assert result == 0
        assert comm_file.exists()

    def test_create_stats_visualize_workflow(self, tmp_path):
        """Test complete workflow: create -> stats -> visualize."""
        # Create network
        network_file = tmp_path / "workflow2.graphml"
        result = cli.main(
            [
                "create",
                "--nodes",
                "15",
                "--layers",
                "2",
                "--output",
                str(network_file),
                "--seed",
                "42",
            ]
        )
        assert result == 0

        # Compute statistics
        stats_file = tmp_path / "stats.json"
        result = cli.main(
            [
                "stats",
                str(network_file),
                "--measure",
                "all",
                "--output",
                str(stats_file),
            ]
        )
        assert result == 0

        # Visualize
        viz_file = tmp_path / "network.png"
        result = cli.main(
            [
                "visualize",
                str(network_file),
                "--layout",
                "spring",
                "--output",
                str(viz_file),
            ]
        )
        assert result == 0
        assert viz_file.exists()
