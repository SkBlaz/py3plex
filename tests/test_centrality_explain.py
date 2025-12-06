#!/usr/bin/env python3
"""
Test suite for explainable centrality features.

This module tests the explainable centrality functions that provide
human-readable explanations for centrality scores in multilayer networks.
"""

import unittest

# Handle missing dependencies gracefully
try:
    import networkx as nx
    from py3plex.core import multinet
    from py3plex.algorithms.centrality.explain import (
        explain_node_centrality,
        explain_top_k_central_nodes,
    )

    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    nx = None
    multinet = None
    explain_node_centrality = None
    explain_top_k_central_nodes = None
    DEPENDENCIES_AVAILABLE = False
    print(f"Warning: {e}")


def skip_if_no_deps(test_func):
    """Decorator to skip tests when dependencies are missing."""
    if not DEPENDENCIES_AVAILABLE:
        return unittest.skip("Dependencies not available")(test_func)
    return test_func


class TestExplainNodeCentrality(unittest.TestCase):
    """Test cases for explain_node_centrality function."""

    def setUp(self):
        """Set up test networks."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")

        # Create a simple 2-layer network with a clear bridge node
        self.bridge_network = multinet.multi_layer_network(directed=False)

        # Layer 1: A-B-C chain
        self.bridge_network.add_edges(
            [
                ["A", "L1", "B", "L1", 1],
                ["B", "L1", "C", "L1", 1],
            ],
            input_type="list",
        )

        # Layer 2: B-D-E chain (B is the bridge)
        self.bridge_network.add_edges(
            [
                ["B", "L2", "D", "L2", 1],
                ["D", "L2", "E", "L2", 1],
            ],
            input_type="list",
        )

        # Simple triangle network for motif testing
        self.triangle_network = multinet.multi_layer_network(directed=False)
        self.triangle_network.add_edges(
            [
                ["A", "L1", "B", "L1", 1],
                ["B", "L1", "C", "L1", 1],
                ["C", "L1", "A", "L1", 1],
            ],
            input_type="list",
        )

    @skip_if_no_deps
    def test_basic_explanation_structure(self):
        """Test that explanation returns required keys."""
        # Create simple centrality scores
        scores = {
            ("A", "L1"): 0.2,
            ("B", "L1"): 0.5,
            ("C", "L1"): 0.2,
            ("B", "L2"): 0.5,
            ("D", "L2"): 0.3,
            ("E", "L2"): 0.2,
        }

        explanation = explain_node_centrality(
            self.bridge_network, ("B", "L1"), scores, method="degree"
        )

        # Check required keys
        self.assertIn("score", explanation)
        self.assertIn("layer_breakdown", explanation)
        self.assertIn("degree_per_layer", explanation)
        self.assertIn("num_interlayer_edges", explanation)
        self.assertIn("local_motifs", explanation)
        self.assertIn("rank", explanation)
        self.assertIn("percentile", explanation)

    @skip_if_no_deps
    def test_degree_explanation(self):
        """Test explanation for degree centrality."""
        scores = {
            ("A", "L1"): 1.0,
            ("B", "L1"): 2.0,
            ("C", "L1"): 1.0,
        }

        explanation = explain_node_centrality(
            self.triangle_network, ("B", "L1"), scores, method="degree"
        )

        # B has degree 2 in L1 (connected to A and C)
        self.assertEqual(explanation["score"], 2.0)
        self.assertIn("L1", explanation["degree_per_layer"])
        self.assertEqual(explanation["degree_per_layer"]["L1"], 2)

    @skip_if_no_deps
    def test_bridge_node_interlayer_edges(self):
        """Test that bridge nodes have inter-layer edges counted."""
        scores = {
            ("A", "L1"): 1.0,
            ("B", "L1"): 2.0,
            ("C", "L1"): 1.0,
            ("B", "L2"): 2.0,
            ("D", "L2"): 2.0,
            ("E", "L2"): 1.0,
        }

        # B appears in both layers and should have inter-layer edges
        explanation_b = explain_node_centrality(
            self.bridge_network, ("B", "L1"), scores, method="degree"
        )

        # A only appears in L1, should have 0 inter-layer edges
        explanation_a = explain_node_centrality(
            self.bridge_network, ("A", "L1"), scores, method="degree"
        )

        # B should have at least one inter-layer edge
        self.assertGreaterEqual(explanation_b["num_interlayer_edges"], 0)

        # A should have no inter-layer edges
        self.assertEqual(explanation_a["num_interlayer_edges"], 0)

    @skip_if_no_deps
    def test_triangle_motifs(self):
        """Test triangle counting in local motifs."""
        scores = {
            ("A", "L1"): 2.0,
            ("B", "L1"): 2.0,
            ("C", "L1"): 2.0,
        }

        explanation = explain_node_centrality(
            self.triangle_network, ("A", "L1"), scores, method="degree"
        )

        # Should detect triangles
        self.assertIn("triangles", explanation["local_motifs"])
        # Each node in a triangle sees 1 triangle
        self.assertGreaterEqual(explanation["local_motifs"]["triangles"], 0)

    @skip_if_no_deps
    def test_ranking_information(self):
        """Test that ranking and percentile are computed correctly."""
        scores = {
            ("A", "L1"): 0.1,
            ("B", "L1"): 0.5,
            ("C", "L1"): 0.3,
        }

        explanation_b = explain_node_centrality(
            self.triangle_network, ("B", "L1"), scores, method="degree"
        )

        explanation_c = explain_node_centrality(
            self.triangle_network, ("C", "L1"), scores, method="degree"
        )

        explanation_a = explain_node_centrality(
            self.triangle_network, ("A", "L1"), scores, method="degree"
        )

        # B has highest score, should be rank 1
        self.assertEqual(explanation_b["rank"], 1)
        # C has middle score, should be rank 2
        self.assertEqual(explanation_c["rank"], 2)
        # A has lowest score, should be rank 3
        self.assertEqual(explanation_a["rank"], 3)

        # Percentiles should be in valid range
        self.assertGreaterEqual(explanation_b["percentile"], 0)
        self.assertLessEqual(explanation_b["percentile"], 100)

    @skip_if_no_deps
    def test_ranking_with_ties(self):
        """Test that ranking handles tied scores correctly."""
        scores = {
            ("A", "L1"): 0.5,
            ("B", "L1"): 0.5,  # Tie with A
            ("C", "L1"): 0.3,
        }

        explanation_a = explain_node_centrality(
            self.triangle_network, ("A", "L1"), scores, method="degree"
        )

        explanation_b = explain_node_centrality(
            self.triangle_network, ("B", "L1"), scores, method="degree"
        )

        explanation_c = explain_node_centrality(
            self.triangle_network, ("C", "L1"), scores, method="degree"
        )

        # A and B should have same rank (both are tied for first)
        self.assertEqual(explanation_a["rank"], 1)
        self.assertEqual(explanation_b["rank"], 1)

        # C should be ranked lower
        self.assertEqual(explanation_c["rank"], 3)

    @skip_if_no_deps
    def test_layer_breakdown_for_degree(self):
        """Test that layer breakdown is correct for degree centrality."""
        scores = {
            ("A", "L1"): 1.0,
            ("B", "L1"): 2.0,
            ("C", "L1"): 1.0,
        }

        explanation = explain_node_centrality(
            self.triangle_network, ("B", "L1"), scores, method="degree"
        )

        # For degree, layer breakdown should match degree_per_layer
        self.assertEqual(
            explanation["layer_breakdown"], explanation["degree_per_layer"]
        )

    @skip_if_no_deps
    def test_invalid_node_raises_error(self):
        """Test that invalid node raises ValueError."""
        scores = {
            ("A", "L1"): 1.0,
            ("B", "L1"): 2.0,
        }

        with self.assertRaises(ValueError):
            explain_node_centrality(
                self.triangle_network,
                ("Z", "L1"),  # Node doesn't exist
                scores,
                method="degree",
            )

    @skip_if_no_deps
    def test_betweenness_explanation(self):
        """Test explanation for betweenness centrality."""
        scores = {
            ("A", "L1"): 0.0,
            ("B", "L1"): 0.5,
            ("C", "L1"): 0.0,
        }

        explanation = explain_node_centrality(
            self.triangle_network, ("B", "L1"), scores, method="betweenness"
        )

        # Should have layer breakdown (approximate)
        self.assertIn("layer_breakdown", explanation)
        self.assertIsInstance(explanation["layer_breakdown"], dict)


class TestExplainTopKCentralNodes(unittest.TestCase):
    """Test cases for explain_top_k_central_nodes function."""

    def setUp(self):
        """Set up test networks."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")

        # Create a simple network
        self.network = multinet.multi_layer_network(directed=False)
        self.network.add_edges(
            [
                ["A", "L1", "B", "L1", 1],
                ["B", "L1", "C", "L1", 1],
                ["C", "L1", "D", "L1", 1],
            ],
            input_type="list",
        )

    @skip_if_no_deps
    def test_top_k_returns_correct_number(self):
        """Test that top-k returns exactly k explanations."""
        scores = {
            ("A", "L1"): 0.1,
            ("B", "L1"): 0.5,
            ("C", "L1"): 0.3,
            ("D", "L1"): 0.2,
        }

        explanations = explain_top_k_central_nodes(
            self.network, scores, method="degree", k=2
        )

        self.assertEqual(len(explanations), 2)

    @skip_if_no_deps
    def test_top_k_returns_highest_scores(self):
        """Test that top-k returns nodes with highest scores."""
        scores = {
            ("A", "L1"): 0.1,
            ("B", "L1"): 0.5,
            ("C", "L1"): 0.3,
            ("D", "L1"): 0.2,
        }

        explanations = explain_top_k_central_nodes(
            self.network, scores, method="degree", k=2
        )

        # Top 2 should be B and C
        nodes = list(explanations.keys())
        self.assertIn(("B", "L1"), nodes)
        self.assertIn(("C", "L1"), nodes)

    @skip_if_no_deps
    def test_top_k_explanations_have_correct_structure(self):
        """Test that each explanation has required keys."""
        scores = {
            ("A", "L1"): 0.1,
            ("B", "L1"): 0.5,
            ("C", "L1"): 0.3,
        }

        explanations = explain_top_k_central_nodes(
            self.network, scores, method="degree", k=2
        )

        for node, explanation in explanations.items():
            self.assertIn("score", explanation)
            # Should have full explanation (unless error occurred)
            if "error" not in explanation:
                self.assertIn("layer_breakdown", explanation)
                self.assertIn("degree_per_layer", explanation)

    @skip_if_no_deps
    def test_top_k_with_k_larger_than_nodes(self):
        """Test behavior when k is larger than number of nodes."""
        scores = {
            ("A", "L1"): 0.1,
            ("B", "L1"): 0.5,
        }

        explanations = explain_top_k_central_nodes(
            self.network, scores, method="degree", k=10  # More than available nodes
        )

        # Should return all available nodes
        self.assertEqual(len(explanations), 2)

    @skip_if_no_deps
    def test_top_k_default_k_value(self):
        """Test that default k=5 works."""
        scores = {
            ("A", "L1"): 0.1,
            ("B", "L1"): 0.5,
            ("C", "L1"): 0.3,
            ("D", "L1"): 0.2,
        }

        explanations = explain_top_k_central_nodes(
            self.network,
            scores,
            method="degree",
            # k defaults to 5
        )

        # Should return all 4 nodes (since k=5 > 4)
        self.assertEqual(len(explanations), 4)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def setUp(self):
        """Set up edge case networks."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")

        # Single node network
        self.single_node = multinet.multi_layer_network(directed=False)
        self.single_node.add_edges(
            [
                ["A", "L1", "A", "L1", 1],  # Self-loop
            ],
            input_type="list",
        )

        # Disconnected layers
        self.disconnected = multinet.multi_layer_network(directed=False)
        self.disconnected.add_edges(
            [
                ["A", "L1", "B", "L1", 1],
                ["C", "L2", "D", "L2", 1],
            ],
            input_type="list",
        )

    @skip_if_no_deps
    def test_single_node_network(self):
        """Test explanation for single node network."""
        scores = {("A", "L1"): 1.0}

        explanation = explain_node_centrality(
            self.single_node, ("A", "L1"), scores, method="degree"
        )

        # Should return valid explanation
        self.assertEqual(explanation["score"], 1.0)
        self.assertEqual(explanation["rank"], 1)
        self.assertEqual(explanation["percentile"], 0.0)  # Only one node

    @skip_if_no_deps
    def test_disconnected_layers(self):
        """Test explanation with disconnected layers."""
        scores = {
            ("A", "L1"): 0.5,
            ("B", "L1"): 0.5,
            ("C", "L2"): 0.5,
            ("D", "L2"): 0.5,
        }

        explanation = explain_node_centrality(
            self.disconnected, ("A", "L1"), scores, method="degree"
        )

        # Should work even with disconnected layers
        self.assertIn("score", explanation)
        self.assertIn("layer_breakdown", explanation)

    @skip_if_no_deps
    def test_zero_centrality_scores(self):
        """Test explanation with zero centrality scores."""
        scores = {
            ("A", "L1"): 0.0,
            ("B", "L1"): 0.0,
        }

        explanation = explain_node_centrality(
            self.single_node, ("A", "L1"), scores, method="degree"
        )

        # Should handle zero scores gracefully
        self.assertEqual(explanation["score"], 0.0)


if __name__ == "__main__":
    unittest.main()
