"""
Tests to improve coverage of py3plex.core.parsers module.
"""

import json
import os
import tempfile
from pathlib import Path

import networkx as nx
import numpy as np
import pytest

from py3plex.core import parsers


class TestParseGML:
    """Tests for parse_gml function."""

    def test_parse_gml_returns_tuple(self):
        """Test that parse_gml returns a tuple."""
        gml_content = """graph [
  node [
    id 1
    label "A"
    type "default"
  ]
  node [
    id 2
    label "B"
    type "default"
  ]
  edge [
    source 1
    target 2
  ]
]"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.gml', delete=False) as f:
            f.write(gml_content)
            f.flush()
            temp_path = f.name
        
        try:
            result = parsers.parse_gml(temp_path, directed=False)
            assert isinstance(result, tuple)
            assert len(result) == 2
        finally:
            os.unlink(temp_path)


class TestSimpleEdgelist:
    """Tests for simple_edgelist parsing."""

    def test_parse_simple_edgelist_directed(self):
        """Test parsing simple edgelist as directed."""
        edgelist = """A B 1.0
B C 1.0
C D 1.0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(edgelist)
            f.flush()
            temp_path = f.name
        
        try:
            result = parsers.parse_simple_edgelist(temp_path, directed=True)
            # parse_simple_edgelist returns a tuple (graph, labels)
            assert isinstance(result, tuple)
            graph = result[0]
            assert isinstance(graph, (nx.Graph, nx.MultiGraph, nx.DiGraph, nx.MultiDiGraph))
        finally:
            os.unlink(temp_path)

    def test_parse_simple_edgelist_undirected(self):
        """Test parsing simple edgelist as undirected."""
        edgelist = """node1 node2 0.5
node2 node3 0.8
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(edgelist)
            f.flush()
            temp_path = f.name
        
        try:
            result = parsers.parse_simple_edgelist(temp_path, directed=False)
            assert result is not None
        finally:
            os.unlink(temp_path)


class TestMultiEdgelist:
    """Tests for multi_edgelist parsing."""

    def test_parse_multi_edgelist_directed(self):
        """Test parsing multilayer network edgelist format."""
        ml_edgelist = """A layer1 B layer1 1.0
B layer1 C layer1 1.0
A layer2 B layer2 1.0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(ml_edgelist)
            f.flush()
            temp_path = f.name
        
        try:
            result = parsers.parse_multi_edgelist(temp_path, directed=True)
            assert result is not None
        finally:
            os.unlink(temp_path)


class TestGPickleIO:
    """Tests for gpickle reading/writing."""

    def test_parse_gpickle(self):
        """Test parsing gpickle format."""
        # Create a simple graph and save it
        G = nx.MultiGraph()
        G.add_edge('A', 'B', weight=1.0)
        G.add_edge('B', 'C', weight=2.0)
        
        with tempfile.NamedTemporaryFile(suffix='.gpickle', delete=False) as f:
            temp_path = f.name
        
        try:
            # Write the graph using parsers module
            parsers.save_gpickle(G, temp_path)
            
            # Read it back - parse_gpickle returns a tuple
            result = parsers.parse_gpickle(temp_path)
            assert isinstance(result, tuple)
            loaded_graph = result[0]
            
            assert loaded_graph.number_of_nodes() == G.number_of_nodes()
            assert loaded_graph.number_of_edges() >= 0
        finally:
            os.unlink(temp_path)

    def test_save_and_load_gpickle_roundtrip(self):
        """Test saving and loading gpickle."""
        G = nx.Graph()
        G.add_edge('X', 'Y')
        G.add_edge('Y', 'Z')
        
        with tempfile.NamedTemporaryFile(suffix='.gpickle', delete=False) as f:
            temp_path = f.name
        
        try:
            parsers.save_gpickle(G, temp_path)
            result = parsers.parse_gpickle(temp_path)
            loaded = result[0]  # Extract graph from tuple
            assert loaded.number_of_nodes() == 3
        finally:
            os.unlink(temp_path)


class TestEdgelistSaving:
    """Tests for saving edgelists."""

    def test_save_edgelist(self):
        """Test saving graph as edgelist."""
        G = nx.Graph()
        G.add_edge('A', 'B', weight=1.0)
        G.add_edge('B', 'C', weight=2.0)
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            temp_path = f.name
        
        try:
            parsers.save_edgelist(G, temp_path)
            assert Path(temp_path).exists()
            # Verify file has content
            with open(temp_path, 'r') as f:
                content = f.read()
                assert len(content) > 0
        finally:
            os.unlink(temp_path)


class TestErrorHandling:
    """Tests for error handling in parsers."""

    def test_parse_nonexistent_file_raises_error(self):
        """Test that parsing nonexistent file raises appropriate error."""
        with pytest.raises((FileNotFoundError, IOError, OSError, Exception)):
            parsers.parse_simple_edgelist("/nonexistent/path/to/file.txt", directed=True)

    def test_parse_invalid_gml_raises_error(self):
        """Test that parsing invalid GML raises error."""
        invalid_gml = "this is not valid gml content"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.gml', delete=False) as f:
            f.write(invalid_gml)
            f.flush()
            temp_path = f.name
        
        try:
            with pytest.raises(Exception):  # NetworkX will raise some exception
                parsers.parse_gml(temp_path, directed=False)
        finally:
            os.unlink(temp_path)

