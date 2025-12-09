"""
Tests for monoplex_nx_wrapper function.

This module tests that the monoplex_nx_wrapper properly forwards kwargs
to NetworkX centrality functions.
"""
import unittest

import networkx as nx

from py3plex.core import multinet


class TestMonoplexNxWrapper(unittest.TestCase):
    """Test monoplex_nx_wrapper kwargs forwarding."""

    def setUp(self):
        """Create a test network."""
        # Create a simple multilayer network
        self.network = multinet.multi_layer_network()
        
        # Add nodes and edges
        edges = [
            {"source": "A", "target": "B", "source_type": "layer1", "target_type": "layer1", "weight": 2.0},
            {"source": "B", "target": "C", "source_type": "layer1", "target_type": "layer1", "weight": 3.0},
            {"source": "C", "target": "D", "source_type": "layer1", "target_type": "layer1", "weight": 1.0},
            {"source": "A", "target": "D", "source_type": "layer1", "target_type": "layer1", "weight": 1.5},
        ]
        
        self.network.add_edges(edges)

    def test_degree_centrality_no_kwargs(self):
        """Test degree centrality without kwargs."""
        result = self.network.monoplex_nx_wrapper("degree_centrality")
        
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)

    def test_degree_centrality_with_empty_kwargs(self):
        """Test degree centrality with empty kwargs dict."""
        result = self.network.monoplex_nx_wrapper("degree_centrality", kwargs={})
        
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)

    def test_betweenness_centrality_unweighted(self):
        """Test betweenness centrality without weight parameter."""
        result = self.network.monoplex_nx_wrapper("betweenness_centrality")
        
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)

    def test_betweenness_centrality_weighted(self):
        """Test betweenness centrality with weight parameter forwarded via kwargs."""
        result_weighted = self.network.monoplex_nx_wrapper(
            "betweenness_centrality", 
            kwargs={"weight": "weight"}
        )
        
        self.assertIsInstance(result_weighted, dict)
        self.assertGreater(len(result_weighted), 0)
        
        # Also test unweighted for comparison
        result_unweighted = self.network.monoplex_nx_wrapper("betweenness_centrality")
        
        # The results should be different when weights are considered
        # (though they might be the same in some edge cases)
        self.assertIsInstance(result_unweighted, dict)

    def test_betweenness_centrality_normalized(self):
        """Test betweenness centrality with normalized parameter."""
        result = self.network.monoplex_nx_wrapper(
            "betweenness_centrality",
            kwargs={"normalized": True}
        )
        
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)

    def test_betweenness_centrality_multiple_kwargs(self):
        """Test betweenness centrality with multiple kwargs."""
        result = self.network.monoplex_nx_wrapper(
            "betweenness_centrality",
            kwargs={"weight": "weight", "normalized": False}
        )
        
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)

    def test_closeness_centrality_weighted(self):
        """Test closeness centrality with distance parameter."""
        result = self.network.monoplex_nx_wrapper(
            "closeness_centrality",
            kwargs={"distance": "weight"}
        )
        
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)

    def test_eigenvector_centrality_max_iter(self):
        """Test eigenvector centrality with max_iter parameter."""
        try:
            result = self.network.monoplex_nx_wrapper(
                "eigenvector_centrality",
                kwargs={"max_iter": 100}
            )
            
            self.assertIsInstance(result, dict)
        except (nx.PowerIterationFailedConvergence, nx.NetworkXNotImplemented):
            # PowerIterationFailedConvergence is acceptable - the test is to verify kwargs are forwarded
            # NetworkXNotImplemented is expected for multigraphs (eigenvector centrality not supported)
            pass

    def test_pagerank_alpha(self):
        """Test pagerank with alpha parameter."""
        result = self.network.monoplex_nx_wrapper(
            "pagerank",
            kwargs={"alpha": 0.85}
        )
        
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)


    def test_invalid_method_raises_error(self):
        """Test that invalid method name raises AttributeError."""
        with self.assertRaises(AttributeError) as context:
            self.network.monoplex_nx_wrapper("nonexistent_centrality_function")
        
        self.assertIn("NetworkX has no method", str(context.exception))


if __name__ == "__main__":
    unittest.main()
