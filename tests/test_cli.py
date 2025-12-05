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

    def test_cli_help(self, capsys):
        """Test that --help works."""
        with pytest.raises(SystemExit) as exc_info:
            cli.main(["--help"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Py3plex" in captured.out

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
        with pytest.raises(SystemExit) as exc_info:
            cli.main(["invalid_command"])
        assert exc_info.value.code == 2  # argparse error code
        captured = capsys.readouterr()
        assert "invalid choice" in captured.err


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


class TestCLIGraphMLStatistics:
    """Test statistics computation for GraphML-loaded networks (issue fix)."""

    @pytest.fixture
    def graphml_network(self, tmp_path):
        """Create a network, save as GraphML, and return the file path."""
        network = multinet.multi_layer_network()

        # Add nodes in multiple layers
        for layer in ["layer1", "layer2", "layer3"]:
            nodes_dict = [{"source": f"node{i}", "type": layer} for i in range(10)]
            network.add_nodes(nodes_dict, input_type="dict")

            # Add edges
            edges_dict = []
            for i in range(8):
                edges_dict.append({
                    "source": f"node{i}",
                    "target": f"node{i+1}",
                    "source_type": layer,
                    "target_type": layer,
                })
            network.add_edges(edges_dict, input_type="dict")

        output_file = tmp_path / "graphml_stats_test.graphml"
        nx.write_graphml(network.core_network, str(output_file))
        return output_file

    def test_load_graphml_stats_no_error(self, graphml_network):
        """Test that loading GraphML and computing stats doesn't error (regression test)."""
        # This was the bug: stats computation failed with "too many values to unpack"
        result = cli.main(["load", str(graphml_network), "--stats"])
        assert result == 0

    def test_load_graphml_stats_computes_layer_densities(self, graphml_network, capsys, caplog):
        """Test that layer densities are computed correctly for GraphML networks."""
        result = cli.main(["load", str(graphml_network), "--stats"])
        assert result == 0
        
        # Check logs for layer density information
        log_output = caplog.text
        # Should show layer densities for all layers
        assert "layer1:" in log_output
        assert "layer2:" in log_output
        assert "layer3:" in log_output

    def test_load_graphml_stats_computes_all_metrics(self, graphml_network, capsys, caplog):
        """Test that all basic statistics are computed for GraphML networks."""
        result = cli.main(["load", str(graphml_network), "--stats"])
        assert result == 0
        
        # Check logs for statistics
        log_output = caplog.text
        # Check all statistics are present
        assert "Layer Densities:" in log_output
        assert "Avg Clustering:" in log_output
        assert "Avg Degree:" in log_output
        assert "Max Degree:" in log_output
        
    def test_load_graphml_stats_to_json(self, graphml_network, tmp_path):
        """Test that statistics from GraphML networks can be saved to JSON."""
        output_file = tmp_path / "graphml_stats.json"
        result = cli.main(
            ["load", str(graphml_network), "--stats", "--output", str(output_file)]
        )
        assert result == 0
        assert output_file.exists()

        # Verify JSON structure
        with open(output_file) as f:
            data = json.load(f)
            assert "statistics" in data
            stats = data["statistics"]
            assert "layer_densities" in stats
            assert "clustering_coefficient" in stats
            assert "avg_degree" in stats
            assert "max_degree" in stats
            # Check that we have all three layers
            assert len(stats["layer_densities"]) == 3

    def test_create_graphml_load_stats_workflow(self, tmp_path):
        """Test full workflow: create network and save as edgelist, convert to graphml, load and compute stats."""
        # Create network as edgelist
        network_file = tmp_path / "workflow.edgelist"
        result = cli.main(
            [
                "create",
                "--nodes",
                "50",
                "--layers",
                "3",
                "--probability",
                "0.1",
                "--output",
                str(network_file),
                "--seed",
                "42",
            ]
        )
        assert result == 0

        # Convert to graphml
        graphml_file = tmp_path / "workflow.graphml"
        result = cli.main(
            ["convert", str(network_file), "--output", str(graphml_file)]
        )
        assert result == 0

        # Load graphml and compute stats (this would fail before the fix)
        result = cli.main(["load", str(graphml_file), "--stats"])
        assert result == 0


class TestCLISelftest:
    """Test the 'selftest' command."""

    def test_selftest_basic(self, capsys):
        """Test that selftest runs successfully."""
        result = cli.main(["selftest"])
        assert result == 0
        captured = capsys.readouterr()
        assert "[py3plex::selftest]" in captured.out
        assert "All tests completed successfully" in captured.out

    def test_selftest_verbose(self, capsys):
        """Test selftest with verbose flag."""
        result = cli.main(["selftest", "--verbose"])
        assert result == 0
        captured = capsys.readouterr()
        assert "[py3plex::selftest]" in captured.out
        assert "numpy:" in captured.out
        assert "networkx:" in captured.out

    def test_selftest_checks_dependencies(self, capsys):
        """Test that selftest checks core dependencies."""
        result = cli.main(["selftest"])
        assert result == 0
        captured = capsys.readouterr()
        assert "Core dependencies" in captured.out
        assert "[OK]" in captured.out

    def test_selftest_checks_graph_creation(self, capsys):
        """Test that selftest checks graph creation."""
        result = cli.main(["selftest"])
        assert result == 0
        captured = capsys.readouterr()
        assert "Graph creation" in captured.out

    def test_selftest_checks_visualization(self, capsys):
        """Test that selftest checks visualization module."""
        result = cli.main(["selftest"])
        assert result == 0
        captured = capsys.readouterr()
        assert "Visualization module" in captured.out

    def test_selftest_checks_multilayer(self, capsys):
        """Test that selftest checks multilayer network creation."""
        result = cli.main(["selftest"])
        assert result == 0
        captured = capsys.readouterr()
        assert "multilayer" in captured.out.lower()

    def test_selftest_checks_community(self, capsys):
        """Test that selftest checks community detection."""
        result = cli.main(["selftest"])
        assert result == 0
        captured = capsys.readouterr()
        assert "Community detection" in captured.out

    def test_selftest_checks_io(self, capsys):
        """Test that selftest checks file I/O."""
        result = cli.main(["selftest"])
        assert result == 0
        captured = capsys.readouterr()
        assert "File I/O" in captured.out

    def test_selftest_summary(self, capsys):
        """Test that selftest provides summary."""
        result = cli.main(["selftest"])
        assert result == 0
        captured = capsys.readouterr()
        assert "TEST SUMMARY" in captured.out
        assert "Tests passed:" in captured.out
        assert "Time elapsed:" in captured.out

    def test_selftest_checks_random_generators(self, capsys):
        """Test that selftest checks random generators."""
        result = cli.main(["selftest"])
        assert result == 0
        captured = capsys.readouterr()
        assert "Random generators" in captured.out or "Random ER" in captured.out

    def test_selftest_checks_nx_wrapper(self, capsys):
        """Test that selftest checks NetworkX wrapper."""
        result = cli.main(["selftest"])
        assert result == 0
        captured = capsys.readouterr()
        assert "NetworkX wrapper" in captured.out

    def test_selftest_checks_new_io(self, capsys):
        """Test that selftest checks new I/O system."""
        result = cli.main(["selftest"])
        assert result == 0
        captured = capsys.readouterr()
        assert "New I/O system" in captured.out

    def test_selftest_checks_advanced_stats(self, capsys):
        """Test that selftest checks advanced multilayer statistics."""
        result = cli.main(["selftest"])
        assert result == 0
        captured = capsys.readouterr()
        assert "Advanced multilayer statistics" in captured.out

    def test_selftest_all_pass(self, capsys):
        """Test that all selftest checks pass."""
        result = cli.main(["selftest"])
        assert result == 0
        captured = capsys.readouterr()
        # Should have 12 tests now (was 8)
        assert "Tests passed: 12/12" in captured.out


class TestCLIQuickstart:
    """Test the 'quickstart' command."""

    def test_quickstart_basic(self, capsys):
        """Test that quickstart runs successfully."""
        result = cli.main(["quickstart"])
        assert result == 0
        captured = capsys.readouterr()
        assert "[py3plex::quickstart]" in captured.out
        assert "Welcome to py3plex" in captured.out
        assert "Quickstart completed successfully" in captured.out

    def test_quickstart_creates_files(self, tmp_path, capsys):
        """Test that quickstart creates the expected files."""
        result = cli.main(
            ["quickstart", "--keep-files", "--output-dir", str(tmp_path)]
        )
        assert result == 0

        # Check that files were created
        assert (tmp_path / "demo_network.graphml").exists()
        assert (tmp_path / "demo_visualization.png").exists()

        captured = capsys.readouterr()
        assert "Network created" in captured.out
        assert "Visualization saved" in captured.out

    def test_quickstart_keep_files(self, tmp_path, capsys):
        """Test that --keep-files preserves files."""
        result = cli.main(
            ["quickstart", "--keep-files", "--output-dir", str(tmp_path)]
        )
        assert result == 0

        # Files should exist after command completes
        assert (tmp_path / "demo_network.graphml").exists()

        captured = capsys.readouterr()
        assert "Files kept in:" in captured.out

    def test_quickstart_shows_next_steps(self, capsys):
        """Test that quickstart shows next steps."""
        result = cli.main(["quickstart"])
        assert result == 0
        captured = capsys.readouterr()
        assert "Next steps:" in captured.out
        assert "py3plex create" in captured.out
        assert "py3plex load" in captured.out
        assert "py3plex visualize" in captured.out

    def test_quickstart_shows_documentation_links(self, capsys):
        """Test that quickstart shows documentation links."""
        result = cli.main(["quickstart"])
        assert result == 0
        captured = capsys.readouterr()
        assert "Documentation:" in captured.out
        assert "GitHub:" in captured.out
        assert "https://skblaz.github.io/py3plex/" in captured.out

    def test_quickstart_network_structure(self, tmp_path):
        """Test that the generated network has expected structure."""
        result = cli.main(
            ["quickstart", "--keep-files", "--output-dir", str(tmp_path)]
        )
        assert result == 0

        # Load and verify the network
        network_file = tmp_path / "demo_network.graphml"
        assert network_file.exists()

        G = nx.read_graphml(str(network_file))
        # Should have nodes from 2 layers
        assert G.number_of_nodes() == 20  # 10 nodes per layer * 2 layers
        assert G.number_of_edges() > 0  # Should have some edges

    def test_quickstart_cleanup_by_default(self, capsys):
        """Test that quickstart cleans up by default."""
        result = cli.main(["quickstart"])
        assert result == 0
        captured = capsys.readouterr()
        # Should mention cleanup
        assert "Cleaning up" in captured.out or "temporary" in captured.out.lower()


class TestCLITutorial:
    """Test the 'tutorial' command."""

    def test_tutorial_basic(self, capsys):
        """Test that tutorial runs successfully in non-interactive mode."""
        result = cli.main(["tutorial", "--non-interactive"])
        assert result == 0
        captured = capsys.readouterr()
        assert "PY3PLEX INTERACTIVE TUTORIAL" in captured.out
        assert "TUTORIAL COMPLETE!" in captured.out
        assert "Steps completed: 6/6" in captured.out

    def test_tutorial_specific_step(self, capsys):
        """Test running a specific tutorial step."""
        result = cli.main(["tutorial", "--step", "1", "--non-interactive"])
        assert result == 0
        captured = capsys.readouterr()
        assert "STEP 1: Understanding Multilayer Networks" in captured.out
        assert "Steps completed: 1/6" in captured.out
        # Step 2 should not be present
        assert "STEP 2:" not in captured.out

    def test_tutorial_step_2(self, capsys):
        """Test tutorial step 2 creates network."""
        result = cli.main(["tutorial", "--step", "2", "--non-interactive"])
        assert result == 0
        captured = capsys.readouterr()
        assert "STEP 2: Creating Your First Network" in captured.out
        assert "Network created and saved to:" in captured.out
        assert "Total nodes: 6" in captured.out
        assert "Total edges: 5" in captured.out

    def test_tutorial_step_3(self, capsys):
        """Test tutorial step 3 explores structure."""
        result = cli.main(["tutorial", "--step", "3", "--non-interactive"])
        assert result == 0
        captured = capsys.readouterr()
        assert "STEP 3: Exploring Network Structure" in captured.out
        assert "Getting all nodes:" in captured.out
        assert "Getting all edges:" in captured.out
        assert "Getting layers:" in captured.out

    def test_tutorial_step_4(self, capsys):
        """Test tutorial step 4 computes statistics."""
        result = cli.main(["tutorial", "--step", "4", "--non-interactive"])
        assert result == 0
        captured = capsys.readouterr()
        assert "STEP 4: Computing Network Statistics" in captured.out
        assert "Layer Density" in captured.out
        assert "Node Activity" in captured.out
        assert "Edge Overlap" in captured.out

    def test_tutorial_step_5(self, capsys):
        """Test tutorial step 5 detects communities."""
        result = cli.main(["tutorial", "--step", "5", "--non-interactive"])
        assert result == 0
        captured = capsys.readouterr()
        assert "STEP 5: Detecting Communities" in captured.out
        assert "Found" in captured.out and "communities!" in captured.out
        assert "Community assignments:" in captured.out

    def test_tutorial_step_6(self, capsys):
        """Test tutorial step 6 creates visualization."""
        result = cli.main(["tutorial", "--step", "6", "--non-interactive"])
        assert result == 0
        captured = capsys.readouterr()
        assert "STEP 6: Visualizing Networks" in captured.out
        assert "Visualization saved to:" in captured.out

    def test_tutorial_creates_files(self, tmp_path, capsys):
        """Test that tutorial creates the expected files when run fully."""
        result = cli.main(
            ["tutorial", "--non-interactive", "--keep-files", "--output-dir", str(tmp_path)]
        )
        assert result == 0

        # Check that files were created
        assert (tmp_path / "tutorial_network.edgelist").exists()
        assert (tmp_path / "tutorial_communities.json").exists()
        assert (tmp_path / "tutorial_visualization.png").exists()

    def test_tutorial_keep_files(self, tmp_path, capsys):
        """Test that --keep-files preserves files."""
        result = cli.main(
            ["tutorial", "--non-interactive", "--keep-files", "--output-dir", str(tmp_path)]
        )
        assert result == 0

        # Files should exist after command completes
        assert (tmp_path / "tutorial_network.edgelist").exists()

        captured = capsys.readouterr()
        assert "Generated files saved in:" in captured.out

    def test_tutorial_cleanup_by_default(self, capsys):
        """Test that tutorial cleans up by default."""
        result = cli.main(["tutorial", "--non-interactive"])
        assert result == 0
        captured = capsys.readouterr()
        # Should mention cleanup
        assert "Cleaning up" in captured.out

    def test_tutorial_shows_next_steps(self, capsys):
        """Test that tutorial shows next steps."""
        result = cli.main(["tutorial", "--non-interactive"])
        assert result == 0
        captured = capsys.readouterr()
        assert "Next steps:" in captured.out
        assert "py3plex --help" in captured.out
        assert "py3plex selftest" in captured.out
        assert "py3plex quickstart" in captured.out

    def test_tutorial_shows_all_steps_in_intro(self, capsys):
        """Test that tutorial shows all available steps in introduction."""
        result = cli.main(["tutorial", "--step", "1", "--non-interactive"])
        assert result == 0
        captured = capsys.readouterr()
        assert "Step 1: Understanding Multilayer Networks" in captured.out
        assert "Step 2: Creating Your First Network" in captured.out
        assert "Step 3: Exploring Network Structure" in captured.out
        assert "Step 4: Computing Network Statistics" in captured.out
        assert "Step 5: Detecting Communities" in captured.out
        assert "Step 6: Visualizing Networks" in captured.out

    def test_tutorial_includes_code_examples(self, capsys):
        """Test that tutorial includes code examples."""
        result = cli.main(["tutorial", "--step", "2", "--non-interactive"])
        assert result == 0
        captured = capsys.readouterr()
        # Should include code snippets
        assert "from py3plex.core import multinet" in captured.out
        assert "network.add_edges" in captured.out

