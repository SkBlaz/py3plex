"""
Tests for CLI ergonomics fixes.

This module tests the specific fixes made for the CLI ergonomics issue:
- Statistics computation without "too many values to unpack" errors
- Visualization without "Input is not a known data type" errors
- Proper layer name extraction
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from py3plex import cli
from py3plex.core import multinet


class TestLayerNameExtraction:
    """Test the _get_layer_names helper function."""

    def test_get_layer_names_basic(self):
        """Test basic layer name extraction."""
        # Create a simple multilayer network
        network = multinet.multi_layer_network()
        network.add_nodes([
            {"source": "node1", "type": "layer1"},
            {"source": "node2", "type": "layer1"},
            {"source": "node3", "type": "layer2"},
        ], input_type="dict")
        
        layers = cli._get_layer_names(network)
        assert isinstance(layers, list)
        assert len(layers) == 2
        assert "layer1" in layers
        assert "layer2" in layers

    def test_get_layer_names_empty_network(self):
        """Test layer name extraction on empty network."""
        network = multinet.multi_layer_network()
        layers = cli._get_layer_names(network)
        assert isinstance(layers, list)
        assert len(layers) == 0

    def test_get_layer_names_single_layer(self):
        """Test layer name extraction with single layer."""
        network = multinet.multi_layer_network()
        network.add_nodes([
            {"source": "node1", "type": "layer1"},
            {"source": "node2", "type": "layer1"},
        ], input_type="dict")
        
        layers = cli._get_layer_names(network)
        assert len(layers) == 1
        assert layers[0] == "layer1"


class TestCLIStatsCommand:
    """Test the stats command fixes."""

    @patch('py3plex.cli.logger')
    @patch('py3plex.cli._load_network')
    @patch('py3plex.algorithms.statistics.multilayer_statistics.layer_density')
    def test_stats_command_no_unpacking_error(self, mock_density, mock_load, mock_logger):
        """Test that stats command doesn't raise 'too many values to unpack' error."""
        # Setup mock network
        mock_network = MagicMock(spec=multinet.multi_layer_network)
        mock_network.core_network = MagicMock()
        mock_network.core_network.to_undirected.return_value = MagicMock()
        mock_network.core_network.nodes.return_value = [
            (('node1', 'layer1'), {}),
            (('node2', 'layer1'), {}),
        ]
        mock_network.get_nodes.return_value = [
            ('node1', 'layer1'),
            ('node2', 'layer1'),
        ]
        mock_load.return_value = mock_network
        mock_density.return_value = 0.5
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix='.edgelist', delete=False) as f:
            temp_file = f.name
        
        try:
            # This should not raise "too many values to unpack" error
            args = cli.create_parser().parse_args(['stats', temp_file, '--measure', 'density'])
            result = cli.cmd_stats(args)
            
            # Verify it completed successfully
            assert result == 0
            mock_load.assert_called_once()
        finally:
            Path(temp_file).unlink(missing_ok=True)


class TestCLILoadCommand:
    """Test the load command fixes."""

    @patch('py3plex.cli.logger')
    @patch('py3plex.cli._load_network')
    def test_load_with_stats_no_unpacking_error(self, mock_load, mock_logger):
        """Test that load --stats doesn't raise 'too many values to unpack' error."""
        # Setup mock network
        mock_network = MagicMock(spec=multinet.multi_layer_network)
        mock_network.core_network = MagicMock()
        mock_network.core_network.number_of_nodes.return_value = 10
        mock_network.core_network.number_of_edges.return_value = 20
        mock_network.core_network.to_undirected.return_value = MagicMock()
        mock_network.core_network.degree.return_value = [(('node1', 'layer1'), 3)]
        mock_network.directed = False
        mock_network.get_nodes.return_value = [
            ('node1', 'layer1'),
            ('node2', 'layer1'),
        ]
        mock_load.return_value = mock_network
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix='.edgelist', delete=False) as f:
            temp_file = f.name
        
        try:
            # This should not raise "too many values to unpack" error
            args = cli.create_parser().parse_args(['load', temp_file, '--stats'])
            result = cli.cmd_load(args)
            
            # Verify it completed successfully
            assert result == 0
            mock_load.assert_called_once()
        finally:
            Path(temp_file).unlink(missing_ok=True)


class TestCLIVisualizeCommand:
    """Test the visualize command fixes."""

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    @patch('matplotlib.pyplot.figure')
    @patch('py3plex.cli.logger')
    @patch('py3plex.cli._load_network')
    def test_visualize_multilayer_no_conversion_error(
        self, mock_load, mock_logger, mock_figure, mock_close, mock_savefig
    ):
        """Test that visualize command with multilayer layout works correctly."""
        # Setup mock network
        mock_network = MagicMock(spec=multinet.multi_layer_network)
        mock_network.core_network = MagicMock()
        
        # Mock get_layers to return the expected tuple
        mock_graph1 = MagicMock()
        mock_graph2 = MagicMock()
        mock_network.get_layers.return_value = (
            ['layer1', 'layer2'],  # layer_names
            {'layer1': mock_graph1, 'layer2': mock_graph2},  # layer_graphs
            []  # multiedges
        )
        
        mock_load.return_value = mock_network
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix='.edgelist', delete=False) as f:
            temp_input = f.name
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_output = f.name
        
        try:
            # Mock the multilayer visualization module
            with patch('py3plex.visualization.multilayer.draw_multilayer_default') as mock_draw:
                # This should not raise "Input is not a known data type" error
                args = cli.create_parser().parse_args([
                    'visualize', temp_input, '--output', temp_output, '--layout', 'multilayer'
                ])
                result = cli.cmd_visualize(args)
                
                # Verify it completed successfully
                assert result == 0
                mock_load.assert_called_once()
                mock_network.get_layers.assert_called_once()
                
                # Verify draw_multilayer_default was called with list of graphs, not network object
                mock_draw.assert_called_once()
                call_args = mock_draw.call_args
                assert call_args is not None
                # First argument should be a list
                assert isinstance(call_args[0][0], list)
        finally:
            Path(temp_input).unlink(missing_ok=True)
            Path(temp_output).unlink(missing_ok=True)


class TestCLIConvertCommand:
    """Test the convert command fixes."""

    @patch('py3plex.cli.logger')
    @patch('py3plex.cli._load_network')
    def test_convert_to_json_no_unpacking_error(self, mock_load, mock_logger):
        """Test that convert to JSON doesn't raise 'too many values to unpack' error."""
        # Setup mock network
        mock_network = MagicMock(spec=multinet.multi_layer_network)
        mock_network.core_network = MagicMock()
        mock_network.core_network.nodes.return_value = [('node1', 'layer1')]
        mock_network.core_network.edges.return_value = []
        mock_network.directed = False
        mock_network.get_nodes.return_value = [
            ('node1', 'layer1'),
        ]
        mock_load.return_value = mock_network
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix='.edgelist', delete=False) as f:
            temp_input = f.name
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_output = f.name
        
        try:
            # This should not raise "too many values to unpack" error
            args = cli.create_parser().parse_args(['convert', temp_input, '--output', temp_output])
            result = cli.cmd_convert(args)
            
            # Verify it completed successfully
            assert result == 0
            mock_load.assert_called_once()
        finally:
            Path(temp_input).unlink(missing_ok=True)
            Path(temp_output).unlink(missing_ok=True)


class TestCLIDocumentation:
    """Test that CLI documentation is comprehensive."""

    def test_help_shows_examples(self, capsys):
        """Test that --help shows comprehensive examples."""
        with pytest.raises(SystemExit):
            cli.main(["--help"])
        
        captured = capsys.readouterr()
        help_text = captured.out
        
        # Check for key examples
        assert "py3plex create" in help_text
        assert "py3plex stats" in help_text
        assert "py3plex visualize" in help_text
        assert "py3plex load" in help_text
        assert "edgelist" in help_text or ".edgelist" in help_text

    def test_create_help_mentions_edgelist(self, capsys):
        """Test that create command help mentions edgelist format."""
        with pytest.raises(SystemExit):
            cli.main(["create", "--help"])
        
        captured = capsys.readouterr()
        help_text = captured.out
        
        # Check that edgelist is mentioned as a recommended format
        assert "edgelist" in help_text.lower() or ".txt" in help_text.lower()
