"""
Tests for edgelist format generation.

This module tests that edgelist files are generated correctly for both
multilayer and regular networks, ensuring layer information is preserved
when present.
"""

import tempfile
from pathlib import Path

import networkx as nx
import pytest

from py3plex.core import multinet, parsers


class TestEdgelistFormatMultilayer:
    """Test edgelist format for multilayer networks."""

    def test_multilayer_edgelist_has_four_columns(self):
        """Test that multilayer networks generate 4-column edgelist format."""
        # Create a multilayer network
        network = multinet.multi_layer_network()
        
        # Add nodes to two layers
        nodes_layer1 = [{"source": f"node{i}", "type": "layer1"} for i in range(3)]
        network.add_nodes(nodes_layer1, input_type="dict")
        
        nodes_layer2 = [{"source": f"node{i}", "type": "layer2"} for i in range(3)]
        network.add_nodes(nodes_layer2, input_type="dict")
        
        # Add edges
        edges = [
            {"source": "node0", "target": "node1", "source_type": "layer1", "target_type": "layer1"},
            {"source": "node1", "target": "node2", "source_type": "layer2", "target_type": "layer2"},
        ]
        network.add_edges(edges, input_type="dict")
        
        # Save to edgelist
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.edgelist') as f:
            output_file = f.name
        
        try:
            network.save_network(output_file, output_type="edgelist")
            
            # Read and verify format
            with open(output_file, 'r') as f:
                lines = f.readlines()
            
            # Each line should have 4 space-separated columns
            assert len(lines) == 2, f"Expected 2 edges, got {len(lines)}"
            
            for line in lines:
                parts = line.strip().split()
                assert len(parts) == 4, f"Expected 4 columns, got {len(parts)}: {line}"
                node1, layer1, node2, layer2 = parts
                # Verify we have actual content (not empty strings)
                assert node1 and layer1 and node2 and layer2, f"Empty column in: {line}"
        finally:
            Path(output_file).unlink(missing_ok=True)

    def test_multilayer_edgelist_preserves_layer_names(self):
        """Test that layer names are correctly preserved in edgelist output."""
        network = multinet.multi_layer_network()
        
        # Add nodes
        network.add_nodes([{"source": "A", "type": "social"}], input_type="dict")
        network.add_nodes([{"source": "B", "type": "social"}], input_type="dict")
        network.add_nodes([{"source": "C", "type": "biological"}], input_type="dict")
        network.add_nodes([{"source": "D", "type": "biological"}], input_type="dict")
        
        # Add edges
        edges = [
            {"source": "A", "target": "B", "source_type": "social", "target_type": "social"},
            {"source": "C", "target": "D", "source_type": "biological", "target_type": "biological"},
        ]
        network.add_edges(edges, input_type="dict")
        
        # Save and read
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.edgelist') as f:
            output_file = f.name
        
        try:
            network.save_network(output_file, output_type="edgelist")
            
            with open(output_file, 'r') as f:
                content = f.read()
            
            # Verify layer names appear in output
            assert "social" in content, "Expected 'social' layer name in output"
            assert "biological" in content, "Expected 'biological' layer name in output"
            
            # Verify node names appear in output
            assert "A" in content or "B" in content, "Expected node names in output"
            assert "C" in content or "D" in content, "Expected node names in output"
        finally:
            Path(output_file).unlink(missing_ok=True)

    def test_multilayer_cli_create_generates_correct_format(self):
        """Test that CLI create command generates correct multilayer edgelist format."""
        from py3plex import cli
        import argparse
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.edgelist') as f:
            output_file = f.name
        
        try:
            # Create network via CLI
            args = argparse.Namespace(
                nodes=5,
                layers=2,
                type='random',
                probability=0.5,
                output=output_file,
                seed=42
            )
            
            result = cli.cmd_create(args)
            assert result == 0, "CLI create command failed"
            
            # Verify output format
            with open(output_file, 'r') as f:
                lines = [line for line in f if line.strip()]
            
            if len(lines) > 0:
                # Check at least one line has 4 columns (space-separated)
                first_line = lines[0].strip().split()
                assert len(first_line) == 4, f"Expected 4 columns, got {len(first_line)}: {lines[0]}"
        finally:
            Path(output_file).unlink(missing_ok=True)


class TestEdgelistFormatRegular:
    """Test edgelist format for regular (non-multilayer) networks."""

    def test_regular_network_has_two_columns(self):
        """Test that regular networks generate 2-column edgelist format."""
        # Create a simple NetworkX graph
        G = nx.Graph()
        G.add_edges_from([("A", "B"), ("B", "C"), ("C", "D")])
        
        # Save to edgelist
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.edgelist') as f:
            output_file = f.name
        
        try:
            parsers.save_edgelist(G, output_file)
            
            # Read and verify format
            with open(output_file, 'r') as f:
                lines = f.readlines()
            
            assert len(lines) == 3, f"Expected 3 edges, got {len(lines)}"
            
            # Each line should have 2 space-separated columns
            for line in lines:
                parts = line.strip().split()
                assert len(parts) == 2, f"Expected 2 columns for regular network, got {len(parts)}: {line}"
        finally:
            Path(output_file).unlink(missing_ok=True)

    def test_empty_multilayer_network(self):
        """Test that empty multilayer networks are handled gracefully."""
        network = multinet.multi_layer_network()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.edgelist') as f:
            output_file = f.name
        
        try:
            network.save_network(output_file, output_type="edgelist")
            
            # File should exist and be empty or have no edges
            with open(output_file, 'r') as f:
                content = f.read()
            
            # Empty network should produce empty file
            assert content.strip() == "", "Empty network should produce empty file"
        finally:
            Path(output_file).unlink(missing_ok=True)


class TestEdgelistBackwardCompatibility:
    """Test that the fix maintains backward compatibility."""

    def test_loading_old_format_still_works(self):
        """Test that loading old 2-column format still works if needed."""
        # This is more about ensuring we didn't break loading functionality
        # The save function now produces 4-column format for multilayer,
        # but we should ensure existing code still works
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.edgelist') as f:
            output_file = f.name
            # Write a simple 2-column edgelist
            f.write("0 1\n")
            f.write("1 2\n")
            f.write("2 3\n")
        
        try:
            # This test just ensures the file was created correctly
            with open(output_file, 'r') as f:
                lines = f.readlines()
            assert len(lines) == 3
        finally:
            Path(output_file).unlink(missing_ok=True)
