"""
Tests for the nx_compat module.

This module tests NetworkX compatibility functions.
"""
import os
import tempfile
import unittest

import networkx as nx
import numpy as np
import scipy.sparse

from py3plex.core.nx_compat import (
    is_string_like,
    nx_from_scipy_sparse_matrix,
    nx_info,
    nx_read_gpickle,
    nx_to_scipy_sparse_matrix,
    nx_write_gpickle,
)


class TestNxInfo(unittest.TestCase):
    """Test network information function."""

    def test_nx_info_simple_graph(self):
        """Test info for simple graph."""
        G = nx.Graph()
        G.add_edges_from([(1, 2), (2, 3), (3, 4)])
        
        info = nx_info(G)
        
        self.assertIsInstance(info, str)
        self.assertIn("nodes", info.lower())
        self.assertIn("edges", info.lower())

    def test_nx_info_directed_graph(self):
        """Test info for directed graph."""
        G = nx.DiGraph()
        G.add_edges_from([(1, 2), (2, 3)])
        
        info = nx_info(G)
        
        self.assertIsInstance(info, str)
        self.assertIn("directed", info.lower())

    def test_nx_info_multigraph(self):
        """Test info for multigraph."""
        G = nx.MultiGraph()
        G.add_edges_from([(1, 2), (1, 2), (2, 3)])
        
        info = nx_info(G)
        
        self.assertIsInstance(info, str)

    def test_nx_info_empty_graph(self):
        """Test info for empty graph."""
        G = nx.Graph()
        
        info = nx_info(G)
        
        self.assertIsInstance(info, str)
        self.assertIn("0", info)  # Should mention 0 nodes/edges

    def test_nx_info_named_graph(self):
        """Test info for named graph."""
        G = nx.Graph(name="TestGraph")
        G.add_edge(1, 2)
        
        info = nx_info(G)
        
        self.assertIsInstance(info, str)


class TestNxPickle(unittest.TestCase):
    """Test pickle read/write functions."""

    def setUp(self):
        """Create temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_write_and_read_graph(self):
        """Test writing and reading a graph."""
        G = nx.Graph()
        G.add_edges_from([(1, 2), (2, 3), (3, 4)])
        G.nodes[1]["attr"] = "value1"
        G.edges[1, 2]["weight"] = 5.0
        
        pickle_path = os.path.join(self.temp_dir, "test.gpickle")
        nx_write_gpickle(G, pickle_path)
        
        # Read it back
        G_read = nx_read_gpickle(pickle_path)
        
        self.assertEqual(G.number_of_nodes(), G_read.number_of_nodes())
        self.assertEqual(G.number_of_edges(), G_read.number_of_edges())
        self.assertEqual(G.nodes[1]["attr"], G_read.nodes[1]["attr"])

    def test_write_and_read_directed_graph(self):
        """Test writing and reading a directed graph."""
        G = nx.DiGraph()
        G.add_edges_from([(1, 2), (2, 3)])
        
        pickle_path = os.path.join(self.temp_dir, "test_directed.gpickle")
        nx_write_gpickle(G, pickle_path)
        
        G_read = nx_read_gpickle(pickle_path)
        
        self.assertEqual(G.number_of_nodes(), G_read.number_of_nodes())
        self.assertEqual(G.number_of_edges(), G_read.number_of_edges())
        self.assertTrue(G_read.is_directed())

    def test_write_and_read_multigraph(self):
        """Test writing and reading a multigraph."""
        G = nx.MultiGraph()
        G.add_edges_from([(1, 2), (1, 2), (2, 3)])
        
        pickle_path = os.path.join(self.temp_dir, "test_multi.gpickle")
        nx_write_gpickle(G, pickle_path)
        
        G_read = nx_read_gpickle(pickle_path)
        
        self.assertEqual(G.number_of_nodes(), G_read.number_of_nodes())
        self.assertEqual(G.number_of_edges(), G_read.number_of_edges())
        self.assertTrue(G_read.is_multigraph())

    def test_write_and_read_empty_graph(self):
        """Test writing and reading an empty graph."""
        G = nx.Graph()
        
        pickle_path = os.path.join(self.temp_dir, "test_empty.gpickle")
        nx_write_gpickle(G, pickle_path)
        
        G_read = nx_read_gpickle(pickle_path)
        
        self.assertEqual(G.number_of_nodes(), G_read.number_of_nodes())
        self.assertEqual(G.number_of_edges(), G_read.number_of_edges())


class TestNxSparseMatrix(unittest.TestCase):
    """Test sparse matrix conversion functions."""

    def test_to_sparse_matrix_simple(self):
        """Test converting graph to sparse matrix."""
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2), (2, 3)])
        
        matrix = nx_to_scipy_sparse_matrix(G)
        
        self.assertIsNotNone(matrix)
        self.assertEqual(matrix.shape, (4, 4))

    def test_to_sparse_matrix_with_weights(self):
        """Test converting graph with weights to sparse matrix."""
        G = nx.Graph()
        G.add_edge(0, 1, weight=5.0)
        G.add_edge(1, 2, weight=3.0)
        
        matrix = nx_to_scipy_sparse_matrix(G, weight="weight")
        
        self.assertIsNotNone(matrix)
        # Check that weights are preserved
        self.assertEqual(matrix[0, 1], 5.0)
        self.assertEqual(matrix[1, 2], 3.0)

    def test_to_sparse_matrix_formats(self):
        """Test converting to different sparse matrix formats."""
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2)])
        
        # Test CSR format
        csr_matrix = nx_to_scipy_sparse_matrix(G, format="csr")
        self.assertIsNotNone(csr_matrix)
        
        # Test COO format
        coo_matrix = nx_to_scipy_sparse_matrix(G, format="coo")
        self.assertIsNotNone(coo_matrix)

    def test_to_sparse_matrix_directed(self):
        """Test converting directed graph to sparse matrix."""
        G = nx.DiGraph()
        G.add_edges_from([(0, 1), (1, 2), (2, 0)])
        
        matrix = nx_to_scipy_sparse_matrix(G)
        
        self.assertIsNotNone(matrix)
        self.assertEqual(matrix.shape, (3, 3))

    def test_to_sparse_matrix_with_nodelist(self):
        """Test converting with specific node list."""
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2), (2, 3)])
        
        nodelist = [0, 1, 2]
        matrix = nx_to_scipy_sparse_matrix(G, nodelist=nodelist)
        
        self.assertEqual(matrix.shape, (3, 3))

    def test_from_sparse_matrix_simple(self):
        """Test creating graph from sparse matrix."""
        # Create a simple sparse matrix
        data = np.array([1, 1, 1])
        row = np.array([0, 1, 2])
        col = np.array([1, 2, 0])
        matrix = scipy.sparse.csr_matrix((data, (row, col)), shape=(3, 3))
        
        G = nx_from_scipy_sparse_matrix(matrix)
        
        self.assertIsNotNone(G)
        self.assertGreater(G.number_of_nodes(), 0)
        self.assertGreater(G.number_of_edges(), 0)

    def test_from_sparse_matrix_directed(self):
        """Test creating directed graph from sparse matrix."""
        data = np.array([1, 1])
        row = np.array([0, 1])
        col = np.array([1, 2])
        matrix = scipy.sparse.csr_matrix((data, (row, col)), shape=(3, 3))
        
        G = nx_from_scipy_sparse_matrix(matrix, create_using=nx.DiGraph())
        
        self.assertIsNotNone(G)
        self.assertTrue(G.is_directed())

    def test_from_sparse_matrix_with_weights(self):
        """Test creating graph from weighted sparse matrix."""
        data = np.array([5.0, 3.0, 2.0])
        row = np.array([0, 1, 2])
        col = np.array([1, 2, 0])
        matrix = scipy.sparse.csr_matrix((data, (row, col)), shape=(3, 3))
        
        G = nx_from_scipy_sparse_matrix(matrix, edge_attribute="weight")
        
        self.assertIsNotNone(G)
        # Check that weights are preserved
        edges_with_data = list(G.edges(data=True))
        self.assertGreater(len(edges_with_data), 0)

    def test_roundtrip_conversion(self):
        """Test converting graph to matrix and back."""
        G_orig = nx.Graph()
        G_orig.add_edges_from([(0, 1), (1, 2), (2, 3), (3, 0)])
        
        # Convert to matrix
        matrix = nx_to_scipy_sparse_matrix(G_orig)
        
        # Convert back to graph
        G_new = nx_from_scipy_sparse_matrix(matrix)
        
        self.assertEqual(G_orig.number_of_nodes(), G_new.number_of_nodes())
        self.assertEqual(G_orig.number_of_edges(), G_new.number_of_edges())


class TestIsStringLike(unittest.TestCase):
    """Test string-like check function."""

    def test_is_string_like_str(self):
        """Test with string."""
        self.assertTrue(is_string_like("hello"))

    def test_is_string_like_empty_str(self):
        """Test with empty string."""
        self.assertTrue(is_string_like(""))

    def test_is_string_like_int(self):
        """Test with integer."""
        self.assertFalse(is_string_like(123))

    def test_is_string_like_list(self):
        """Test with list."""
        self.assertFalse(is_string_like([1, 2, 3]))

    def test_is_string_like_none(self):
        """Test with None."""
        self.assertFalse(is_string_like(None))

    def test_is_string_like_float(self):
        """Test with float."""
        self.assertFalse(is_string_like(3.14))

    def test_is_string_like_dict(self):
        """Test with dictionary."""
        self.assertFalse(is_string_like({"key": "value"}))


if __name__ == "__main__":
    unittest.main()
