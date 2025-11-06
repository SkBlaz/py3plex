#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for visualize_matrix generator/len() fix.

This module tests that the fix for the generator/len() incompatibility
in get_supra_adjacency_matrix works correctly.
"""

import unittest

from py3plex.core import random_generators


class TestGeneratorLenFix(unittest.TestCase):
    """Test cases for generator/len() fix in visualize_matrix."""

    def test_get_nodes_is_generator(self):
        """Verify that get_nodes() returns a generator."""
        net = random_generators.random_multilayer_ER(10, 2, 0.3, directed=False)
        
        # get_nodes() should return a generator
        nodes = net.get_nodes()
        self.assertTrue(hasattr(nodes, '__iter__'))
        self.assertTrue(hasattr(nodes, '__next__'))
        
    def test_get_edges_is_generator(self):
        """Verify that get_edges() returns a generator."""
        net = random_generators.random_multilayer_ER(10, 2, 0.3, directed=False)
        
        # get_edges() should return a generator
        edges = net.get_edges()
        self.assertTrue(hasattr(edges, '__iter__'))
        self.assertTrue(hasattr(edges, '__next__'))

    def test_supra_adjacency_matrix_sparse(self):
        """Test that get_supra_adjacency_matrix works with sparse format."""
        net = random_generators.random_multilayer_ER(10, 2, 0.3, directed=False)
        
        # Should work without error
        matrix = net.get_supra_adjacency_matrix(mtype="sparse")
        self.assertIsNotNone(matrix)

    def test_supra_adjacency_matrix_dense_small(self):
        """Test that get_supra_adjacency_matrix works with dense format on small networks.
        
        This test specifically exercises the code path that was broken:
        the len() call on generators in the memory warning section.
        """
        # Use a small network to avoid memory issues
        net = random_generators.random_multilayer_ER(5, 2, 0.3, directed=False)
        
        # This should work now - previously failed with:
        # TypeError: object of type 'generator' has no len()
        matrix = net.get_supra_adjacency_matrix(mtype="dense")
        self.assertIsNotNone(matrix)
        
        # Verify the matrix has the expected shape
        # For 5 nodes and 2 layers, supra matrix should be 10x10 (or smaller if not all nodes in all layers)
        self.assertEqual(len(matrix.shape), 2)
        self.assertEqual(matrix.shape[0], matrix.shape[1])

    def test_get_nodes_can_be_listed(self):
        """Test that get_nodes() can be converted to a list."""
        net = random_generators.random_multilayer_ER(10, 2, 0.3, directed=False)
        
        nodes_list = list(net.get_nodes())
        self.assertIsInstance(nodes_list, list)
        self.assertGreater(len(nodes_list), 0)

    def test_get_edges_can_be_listed(self):
        """Test that get_edges() can be converted to a list."""
        net = random_generators.random_multilayer_ER(10, 2, 0.3, directed=False)
        
        edges_list = list(net.get_edges())
        self.assertIsInstance(edges_list, list)

    def test_layer_counting_from_nodes(self):
        """Test that layer counting from nodes works correctly."""
        net = random_generators.random_multilayer_ER(20, 3, 0.2, directed=False)
        
        # This should work - using set comprehension on generator
        num_layers = len({x[1] for x in net.get_nodes()})
        
        # Should have at most 3 layers (as specified)
        self.assertGreaterEqual(num_layers, 1)
        self.assertLessEqual(num_layers, 3)


if __name__ == "__main__":
    unittest.main()
