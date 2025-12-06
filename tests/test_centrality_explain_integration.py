#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration tests for explainable centrality with real centrality computations.

Tests that explanations work correctly with actual centrality algorithms
from the py3plex toolkit.
"""

import unittest

# Handle missing dependencies gracefully
try:
    from py3plex.core import multinet
    from py3plex.algorithms.centrality.explain import (
        explain_node_centrality,
        explain_top_k_central_nodes,
    )
    from py3plex.algorithms.centrality_toolkit import (
        multiplex_degree_centrality,
    )
    from py3plex.algorithms.multilayer_algorithms.centrality import (
        MultilayerCentrality,
    )

    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    multinet = None
    explain_node_centrality = None
    explain_top_k_central_nodes = None
    multiplex_degree_centrality = None
    MultilayerCentrality = None
    DEPENDENCIES_AVAILABLE = False
    print(f"Warning: {e}")


def skip_if_no_deps(test_func):
    """Decorator to skip tests when dependencies are missing."""
    if not DEPENDENCIES_AVAILABLE:
        return unittest.skip("Dependencies not available")(test_func)
    return test_func


class TestExplainabilityWithRealCentrality(unittest.TestCase):
    """Test explainability with actual centrality computations."""

    def setUp(self):
        """Set up test networks."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")

        # Create a typical multilayer network
        self.network = multinet.multi_layer_network(directed=False)

        # Layer 1: Social network
        self.network.add_edges(
            [
                ["A", "social", "B", "social", 1],
                ["B", "social", "C", "social", 1],
                ["C", "social", "D", "social", 1],
            ],
            input_type="list",
        )

        # Layer 2: Collaboration network
        self.network.add_edges(
            [
                ["B", "collab", "C", "collab", 1],
                ["C", "collab", "E", "collab", 1],
            ],
            input_type="list",
        )

    @skip_if_no_deps
    def test_explain_with_degree_centrality(self):
        """Test explanations with real degree centrality."""
        # Compute degree centrality
        centrality = multiplex_degree_centrality(self.network, normalized=False)

        # Get explanations for top nodes
        explanations = explain_top_k_central_nodes(
            self.network, centrality, method="degree", k=3
        )

        # Should return explanations
        self.assertGreater(len(explanations), 0)

        # Each explanation should have required fields
        for node, explanation in explanations.items():
            self.assertIn("score", explanation)
            self.assertIn("layer_breakdown", explanation)
            self.assertIn("degree_per_layer", explanation)

    @skip_if_no_deps
    def test_explain_bridge_node_with_multilayer_centrality(self):
        """Test that bridge nodes are correctly identified."""
        # Compute degree centrality
        centrality = multiplex_degree_centrality(self.network, normalized=False)

        # Node C appears in both layers and should have high centrality
        c_nodes = [n for n in centrality.keys() if isinstance(n, tuple) and n[0] == "C"]

        if c_nodes:
            # Explain node C in first layer
            explanation = explain_node_centrality(
                self.network, c_nodes[0], centrality, method="degree"
            )

            # C should have contributions from multiple layers
            self.assertGreater(len(explanation["degree_per_layer"]), 0)

            # C should have reasonable rank
            self.assertGreater(explanation["rank"], 0)

    @skip_if_no_deps
    def test_consistency_of_explanations(self):
        """Test that explanations are consistent with actual scores."""
        # Compute degree centrality
        centrality = multiplex_degree_centrality(self.network, normalized=False)

        # Get all explanations
        for node, score in centrality.items():
            explanation = explain_node_centrality(
                self.network, node, centrality, method="degree"
            )

            # Explanation score should match input score
            self.assertEqual(explanation["score"], score)

            # Rank should be valid
            self.assertGreater(explanation["rank"], 0)
            self.assertLessEqual(explanation["rank"], len(centrality))

    @skip_if_no_deps
    def test_layer_breakdown_sums_correctly(self):
        """Test that layer breakdown makes sense."""
        # Compute degree centrality
        centrality = multiplex_degree_centrality(self.network, normalized=False)

        # Pick a node with known structure
        node = ("B", "social")
        if node in centrality:
            explanation = explain_node_centrality(
                self.network, node, centrality, method="degree"
            )

            # For degree, layer breakdown should match degree_per_layer
            self.assertEqual(
                explanation["layer_breakdown"], explanation["degree_per_layer"]
            )


class TestExplainabilityEdgeCasesWithRealNetworks(unittest.TestCase):
    """Test edge cases with real network structures."""

    def setUp(self):
        """Set up edge case networks."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")

    @skip_if_no_deps
    def test_star_network(self):
        """Test explanation on a star network."""
        # Create star network
        net = multinet.multi_layer_network(directed=False)
        net.add_edges(
            [
                ["center", "L1", "A", "L1", 1],
                ["center", "L1", "B", "L1", 1],
                ["center", "L1", "C", "L1", 1],
                ["center", "L1", "D", "L1", 1],
            ],
            input_type="list",
        )

        centrality = multiplex_degree_centrality(net, normalized=False)

        # Center should have highest centrality
        explanations = explain_top_k_central_nodes(net, centrality, method="degree", k=1)

        self.assertEqual(len(explanations), 1)
        top_node = list(explanations.keys())[0]

        # Should identify center
        self.assertEqual(top_node[0], "center")

    @skip_if_no_deps
    def test_complete_graph(self):
        """Test explanation on a complete graph."""
        # Create complete graph (all nodes connected)
        net = multinet.multi_layer_network(directed=False)
        nodes = ["A", "B", "C"]

        for i, n1 in enumerate(nodes):
            for n2 in nodes[i + 1 :]:
                net.add_edges([[n1, "L1", n2, "L1", 1]], input_type="list")

        centrality = multiplex_degree_centrality(net, normalized=False)

        # All nodes should have same centrality
        explanations = explain_top_k_central_nodes(net, centrality, method="degree", k=3)

        scores = [exp["score"] for exp in explanations.values()]

        # All scores should be equal (complete graph)
        self.assertEqual(len(set(scores)), 1)


if __name__ == "__main__":
    unittest.main()
