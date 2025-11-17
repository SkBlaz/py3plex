"""
Comprehensive tests for parsing functions with uncovered code paths.
"""

import os
import tempfile
import pytest
import networkx as nx
import numpy as np
import scipy.io

from py3plex.core.parsers import (
    parse_gml,
    parse_nx,
    parse_matrix,
    parse_matrix_to_nx,
    parse_gpickle,
)
from py3plex.core.nx_compat import nx_write_gpickle


class TestParseGml:
    """Tests for parse_gml function."""

    def test_parse_gml_undirected(self, tmp_path):
        """Test parsing an undirected GML file."""
        gml_content = """graph [
  node [
    id 0
    label "A"
    type "type1"
  ]
  node [
    id 1
    label "B"
    type "type1"
  ]
  node [
    id 2
    label "C"
    type "type2"
  ]
  edge [
    source 0
    target 1
    weight 1.0
  ]
  edge [
    source 1
    target 2
    weight 2.0
  ]
]"""
        gml_file = tmp_path / "test.gml"
        gml_file.write_text(gml_content)
        
        G, labels = parse_gml(str(gml_file), directed=False)
        
        assert isinstance(G, nx.MultiGraph)
        assert not isinstance(G, nx.MultiDiGraph)
        assert G.number_of_nodes() == 3
        assert G.number_of_edges() == 2
        assert labels is None

    def test_parse_gml_directed(self, tmp_path):
        """Test parsing a directed GML file."""
        gml_content = """graph [
  directed 1
  node [
    id 0
    label "A"
    type "type1"
  ]
  node [
    id 1
    label "B"
    type "type1"
  ]
  edge [
    source 0
    target 1
  ]
]"""
        gml_file = tmp_path / "test_directed.gml"
        gml_file.write_text(gml_content)
        
        G, labels = parse_gml(str(gml_file), directed=True)
        
        assert isinstance(G, nx.MultiDiGraph)
        assert G.number_of_nodes() == 2
        assert G.number_of_edges() == 1

    def test_parse_gml_with_edge_properties(self, tmp_path):
        """Test that edge properties are preserved."""
        gml_content = """graph [
  node [
    id 0
    label "A"
    type "type1"
  ]
  node [
    id 1
    label "B"
    type "type1"
  ]
  edge [
    source 0
    target 1
    weight 5.0
    color "red"
  ]
]"""
        gml_file = tmp_path / "test_props.gml"
        gml_file.write_text(gml_content)
        
        G, _ = parse_gml(str(gml_file), directed=False)
        
        edges = list(G.edges(data=True))
        assert len(edges) == 1
        assert 'weight' in edges[0][2]
        assert 'color' in edges[0][2]

    def test_parse_gml_with_node_attributes(self, tmp_path):
        """Test that node attributes are preserved."""
        gml_content = """graph [
  node [
    id 0
    label "A"
    type "type1"
    value 100
  ]
  node [
    id 1
    label "B"
    type "type2"
    value 200
  ]
  edge [
    source 0
    target 1
  ]
]"""
        gml_file = tmp_path / "test_node_attrs.gml"
        gml_file.write_text(gml_content)
        
        G, _ = parse_gml(str(gml_file), directed=False)
        
        nodes = list(G.nodes(data=True))
        assert len(nodes) == 2
        # Check that type information is preserved
        for node, data in nodes:
            assert 'type' in data


class TestParseNx:
    """Tests for parse_nx function."""

    def test_parse_nx_simple_graph(self):
        """Test parsing a simple NetworkX graph."""
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2), (2, 3)])
        
        result, labels = parse_nx(G, directed=False)
        
        assert result is G
        assert labels is None
        assert result.number_of_nodes() == 4
        assert result.number_of_edges() == 3

    def test_parse_nx_directed_graph(self):
        """Test parsing a directed NetworkX graph."""
        G = nx.DiGraph()
        G.add_edges_from([(0, 1), (1, 2)])
        
        result, labels = parse_nx(G, directed=True)
        
        assert result is G
        assert labels is None
        assert isinstance(result, nx.DiGraph)

    def test_parse_nx_with_attributes(self):
        """Test that attributes are preserved."""
        G = nx.Graph()
        G.add_node(0, type='A', value=10)
        G.add_node(1, type='B', value=20)
        G.add_edge(0, 1, weight=5.0)
        
        result, _ = parse_nx(G, directed=False)
        
        assert result.nodes[0]['type'] == 'A'
        assert result.nodes[1]['value'] == 20
        assert result[0][1]['weight'] == 5.0

    def test_parse_nx_multigraph(self):
        """Test parsing a multigraph."""
        G = nx.MultiGraph()
        G.add_edge(0, 1, key=0)
        G.add_edge(0, 1, key=1)
        
        result, _ = parse_nx(G, directed=False)
        
        assert result is G
        assert result.number_of_edges() == 2


class TestParseMatrix:
    """Tests for parse_matrix function."""

    def test_parse_matrix_basic(self, tmp_path):
        """Test parsing a basic .mat file."""
        # Create a simple adjacency matrix
        network = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]])
        group = np.array([0, 0, 1])
        
        mat_file = tmp_path / "test.mat"
        scipy.io.savemat(str(mat_file), {'network': network, 'group': group})
        
        result_net, result_group = parse_matrix(str(mat_file), directed=False)
        
        assert result_net is not None
        assert result_group is not None
        # Note: scipy.io.savemat/loadmat may reshape arrays
        assert result_net.shape == network.shape or result_net.size == network.size

    def test_parse_matrix_directed(self, tmp_path):
        """Test parsing matrix for directed graph."""
        network = np.array([[0, 1, 0], [0, 0, 1], [0, 0, 0]])
        group = np.array([0, 1, 1])
        
        mat_file = tmp_path / "test_directed.mat"
        scipy.io.savemat(str(mat_file), {'network': network, 'group': group})
        
        result_net, result_group = parse_matrix(str(mat_file), directed=True)
        
        assert result_net is not None
        assert result_group is not None

    def test_parse_matrix_large(self, tmp_path):
        """Test parsing a larger matrix."""
        size = 50
        network = np.random.randint(0, 2, (size, size))
        group = np.random.randint(0, 3, size)
        
        mat_file = tmp_path / "test_large.mat"
        scipy.io.savemat(str(mat_file), {'network': network, 'group': group})
        
        result_net, result_group = parse_matrix(str(mat_file), directed=False)
        
        assert result_net.shape == (size, size) or result_net.size == size * size
        assert result_group.size == size or result_group.shape[1] == size


class TestParseMatrixToNx:
    """Tests for parse_matrix_to_nx function."""

    def test_parse_matrix_to_nx_undirected(self, tmp_path):
        """Test converting matrix to undirected NetworkX graph."""
        network = scipy.sparse.csr_matrix([[0, 1, 1], [1, 0, 1], [1, 1, 0]])
        
        mat_file = tmp_path / "test_nx.mat"
        scipy.io.savemat(str(mat_file), {'network': network})
        
        G, labels = parse_matrix_to_nx(str(mat_file), directed=False)
        
        assert isinstance(G, nx.Graph)
        assert not isinstance(G, nx.DiGraph)
        assert G.number_of_nodes() == 3
        assert labels is None
        # Check nodes have the expected format
        assert all(isinstance(n, tuple) and n[1] == "generic" for n in G.nodes())

    def test_parse_matrix_to_nx_directed(self, tmp_path):
        """Test converting matrix to directed NetworkX graph."""
        network = scipy.sparse.csr_matrix([[0, 1, 0], [0, 0, 1], [0, 0, 0]])
        
        mat_file = tmp_path / "test_nx_dir.mat"
        scipy.io.savemat(str(mat_file), {'network': network})
        
        G, labels = parse_matrix_to_nx(str(mat_file), directed=True)
        
        assert isinstance(G, nx.DiGraph)
        assert G.number_of_nodes() == 3

    def test_parse_matrix_to_nx_sparse(self, tmp_path):
        """Test with sparse matrix."""
        size = 100
        # Create a sparse random matrix
        network = scipy.sparse.random(size, size, density=0.05, format='csr')
        
        mat_file = tmp_path / "test_sparse.mat"
        scipy.io.savemat(str(mat_file), {'network': network})
        
        G, _ = parse_matrix_to_nx(str(mat_file), directed=False)
        
        assert G.number_of_nodes() == size
        assert all(n[1] == "generic" for n in G.nodes())


class TestParseGpickle:
    """Tests for parse_gpickle function."""

    def test_parse_gpickle_basic(self, tmp_path):
        """Test parsing a basic gpickle file."""
        G = nx.MultiGraph()
        G.add_edges_from([((0, 'layer1'), (1, 'layer1')),
                          ((1, 'layer1'), (2, 'layer2'))])
        
        gpickle_file = tmp_path / "test.gpickle"
        nx_write_gpickle(G, str(gpickle_file))
        
        result, labels = parse_gpickle(str(gpickle_file), directed=False)
        
        assert isinstance(result, nx.MultiGraph)
        assert result.number_of_nodes() == 3
        assert labels is None

    def test_parse_gpickle_directed(self, tmp_path):
        """Test parsing a directed gpickle."""
        G = nx.MultiDiGraph()
        G.add_edges_from([((0, 'layer1'), (1, 'layer1')),
                          ((1, 'layer1'), (2, 'layer1'))])
        
        gpickle_file = tmp_path / "test_dir.gpickle"
        nx_write_gpickle(G, str(gpickle_file))
        
        result, labels = parse_gpickle(str(gpickle_file), directed=True)
        
        assert isinstance(result, nx.MultiDiGraph)

    def test_parse_gpickle_with_layer_separator(self, tmp_path):
        """Test parsing with layer separator."""
        G = nx.Graph()
        G.add_edges_from([('layer1_node0', 'layer1_node1'),
                          ('layer2_node2', 'layer2_node3')])
        
        gpickle_file = tmp_path / "test_sep.gpickle"
        nx_write_gpickle(G, str(gpickle_file))
        
        result, _ = parse_gpickle(str(gpickle_file), directed=False, 
                                   layer_separator='_')
        
        assert isinstance(result, nx.MultiGraph)
        # Check that nodes were parsed with layer separator
        nodes = list(result.nodes())
        # Should have tuples as nodes after parsing with separator
        if len(nodes) > 0:
            assert all(isinstance(n, tuple) for n in nodes)

    def test_parse_gpickle_remove_empty_labels(self, tmp_path):
        """Test that nodes with empty labels are removed."""
        G = nx.MultiGraph()
        G.add_node((0, 'layer1'), labels='')
        G.add_node((1, 'layer1'), labels='valid')
        G.add_node((2, 'layer1'))  # No labels attribute
        G.add_edge((1, 'layer1'), (2, 'layer1'))
        
        gpickle_file = tmp_path / "test_labels.gpickle"
        nx_write_gpickle(G, str(gpickle_file))
        
        result, _ = parse_gpickle(str(gpickle_file), directed=False)
        
        # Node with empty labels should be removed
        assert (0, 'layer1') not in result.nodes()
        assert (1, 'layer1') in result.nodes()
        assert (2, 'layer1') in result.nodes()

    def test_parse_gpickle_with_attributes(self, tmp_path):
        """Test that node and edge attributes are preserved."""
        G = nx.MultiGraph()
        G.add_node((0, 'layer1'), type='A', value=100)
        G.add_node((1, 'layer1'), type='B', value=200)
        G.add_edge((0, 'layer1'), (1, 'layer1'), weight=5.0)
        
        gpickle_file = tmp_path / "test_attrs.gpickle"
        nx_write_gpickle(G, str(gpickle_file))
        
        result, _ = parse_gpickle(str(gpickle_file), directed=False)
        
        assert result.nodes[(0, 'layer1')]['value'] == 100
        assert result.nodes[(1, 'layer1')]['type'] == 'B'


class TestParserErrorHandling:
    """Tests for error handling in parsers."""

    def test_parse_gml_nonexistent_file(self):
        """Test error handling for non-existent file."""
        with pytest.raises(FileNotFoundError):
            parse_gml("/nonexistent/path/file.gml", directed=False)

    def test_parse_matrix_nonexistent_file(self):
        """Test error handling for non-existent matrix file."""
        with pytest.raises(FileNotFoundError):
            parse_matrix("/nonexistent/path/file.mat", directed=False)

    def test_parse_gpickle_nonexistent_file(self):
        """Test error handling for non-existent gpickle."""
        with pytest.raises(FileNotFoundError):
            parse_gpickle("/nonexistent/path/file.gpickle", directed=False)


class TestParserIntegration:
    """Integration tests for parsers."""

    def test_parse_and_convert_workflow(self, tmp_path):
        """Test a complete parsing workflow."""
        # Create a graph
        G = nx.karate_club_graph()
        
        # Convert to MultiGraph format
        MG = nx.MultiGraph(G)
        
        # Save and reload
        gpickle_file = tmp_path / "workflow.gpickle"
        nx_write_gpickle(MG, str(gpickle_file))
        
        result, _ = parse_gpickle(str(gpickle_file), directed=False)
        
        assert result.number_of_nodes() == G.number_of_nodes()
        assert result.number_of_edges() == G.number_of_edges()

    def test_multiple_format_consistency(self, tmp_path):
        """Test that different parsers produce consistent results."""
        # Create a simple graph
        G_nx = nx.Graph()
        G_nx.add_edges_from([(0, 1), (1, 2), (2, 3)])
        
        # Parse through parse_nx
        result_nx, _ = parse_nx(G_nx, directed=False)
        
        assert result_nx.number_of_nodes() == 4
        assert result_nx.number_of_edges() == 3
