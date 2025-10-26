"""
Tests for core/supporting module.

This module tests utility functions for network parsing and conversion.
"""
import tempfile
import unittest

import networkx as nx

from py3plex.core.supporting import (
    add_mpx_edges,
    parse_gaf_to_uniprot_GO,
    split_to_layers,
)


class TestSplitToLayers(unittest.TestCase):
    """Test layer splitting functionality."""

    def test_split_simple_multilayer(self):
        """Test splitting a simple multilayer network."""
        G = nx.Graph()
        G.add_node(("A", "layer1"))
        G.add_node(("B", "layer1"))
        G.add_node(("C", "layer2"))
        G.add_node(("D", "layer2"))
        G.add_edge(("A", "layer1"), ("B", "layer1"))
        G.add_edge(("C", "layer2"), ("D", "layer2"))
        
        layers = split_to_layers(G)
        
        self.assertIsInstance(layers, dict)
        self.assertIn("layer1", layers)
        self.assertIn("layer2", layers)
        self.assertEqual(len(layers["layer1"].nodes()), 2)
        self.assertEqual(len(layers["layer2"].nodes()), 2)

    def test_split_single_layer(self):
        """Test splitting network with only one layer."""
        G = nx.Graph()
        G.add_node(("A", "layer1"))
        G.add_node(("B", "layer1"))
        
        layers = split_to_layers(G)
        
        self.assertIsInstance(layers, dict)
        self.assertEqual(len(layers), 1)
        self.assertIn("layer1", layers)

    def test_split_with_attributes(self):
        """Test splitting network where layer info is in node attributes."""
        G = nx.Graph()
        G.add_node("A", type="layer1")
        G.add_node("B", type="layer1")
        G.add_node("C", type="layer2")
        
        layers = split_to_layers(G)
        
        self.assertIsInstance(layers, dict)
        self.assertIn("layer1", layers)
        self.assertIn("layer2", layers)

    def test_split_empty_network(self):
        """Test splitting an empty network."""
        G = nx.Graph()
        
        layers = split_to_layers(G)
        
        self.assertIsInstance(layers, dict)
        self.assertEqual(len(layers), 0)

    def test_split_directed_network(self):
        """Test splitting a directed multilayer network."""
        G = nx.DiGraph()
        G.add_node(("A", "layer1"))
        G.add_node(("B", "layer2"))
        
        layers = split_to_layers(G)
        
        self.assertIsInstance(layers, dict)
        # All values should be NetworkX graphs
        for layer_graph in layers.values():
            self.assertIsInstance(layer_graph, (nx.Graph, nx.DiGraph))

    def test_split_multigraph(self):
        """Test splitting a multigraph."""
        G = nx.MultiGraph()
        G.add_node(("A", "layer1"))
        G.add_node(("B", "layer2"))
        
        layers = split_to_layers(G)
        
        self.assertIsInstance(layers, dict)


class TestAddMpxEdges(unittest.TestCase):
    """Test multiplex edge addition functionality."""

    def test_add_mpx_edges_basic(self):
        """Test adding multiplex edges to a simple network."""
        G = nx.MultiGraph()
        G.add_node(("A", "layer1"))
        G.add_node(("A", "layer2"))
        G.add_node(("B", "layer1"))
        
        result = add_mpx_edges(G)
        
        self.assertIsInstance(result, (nx.Graph, nx.MultiGraph))
        # Node A appears in both layers, so there should be a multiplex edge
        edges = list(result.edges(keys=True))
        mpx_edges = [e for e in edges if len(e) > 2 and e[2] == "mpx"]
        self.assertGreater(len(mpx_edges), 0)

    def test_add_mpx_edges_three_layers(self):
        """Test adding multiplex edges across three layers."""
        G = nx.MultiGraph()
        G.add_node(("A", "layer1"))
        G.add_node(("A", "layer2"))
        G.add_node(("A", "layer3"))
        
        result = add_mpx_edges(G)
        
        self.assertIsInstance(result, (nx.Graph, nx.MultiGraph))
        # Node A appears in three layers, so there should be multiplex edges
        # between all pairs of layers
        edges = list(result.edges(keys=True))
        mpx_edges = [e for e in edges if len(e) > 2 and e[2] == "mpx"]
        # Should have C(3,2) = 3 multiplex edges for node A
        self.assertGreaterEqual(len(mpx_edges), 3)

    def test_add_mpx_edges_no_overlap(self):
        """Test adding multiplex edges when no nodes overlap layers."""
        G = nx.MultiGraph()
        G.add_node(("A", "layer1"))
        G.add_node(("B", "layer2"))
        G.add_node(("C", "layer3"))
        
        result = add_mpx_edges(G)
        
        self.assertIsInstance(result, (nx.Graph, nx.MultiGraph))
        # No nodes overlap, so no multiplex edges should be added
        edges = list(result.edges(keys=True))
        mpx_edges = [e for e in edges if len(e) > 2 and e[2] == "mpx"]
        self.assertEqual(len(mpx_edges), 0)

    def test_add_mpx_edges_directed(self):
        """Test adding multiplex edges to directed network."""
        G = nx.MultiDiGraph()
        G.add_node(("A", "layer1"))
        G.add_node(("A", "layer2"))
        
        result = add_mpx_edges(G)
        
        self.assertIsInstance(result, (nx.DiGraph, nx.MultiDiGraph))

    def test_add_mpx_edges_multiple_nodes(self):
        """Test adding multiplex edges for multiple overlapping nodes."""
        G = nx.MultiGraph()
        # Node A and B both appear in multiple layers
        G.add_node(("A", "layer1"))
        G.add_node(("A", "layer2"))
        G.add_node(("B", "layer1"))
        G.add_node(("B", "layer2"))
        
        result = add_mpx_edges(G)
        
        self.assertIsInstance(result, (nx.Graph, nx.MultiGraph))
        # Should have multiplex edges for both A and B
        edges = list(result.edges(keys=True))
        mpx_edges = [e for e in edges if len(e) > 2 and e[2] == "mpx"]
        self.assertGreaterEqual(len(mpx_edges), 2)


class TestParseGafToUniprotGO(unittest.TestCase):
    """Test GAF file parsing functionality."""

    def setUp(self):
        """Create temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_parse_gaf_basic(self):
        """Test basic GAF file parsing."""
        import os
        gaf_file = os.path.join(self.temp_dir, "test.gaf")
        with open(gaf_file, "w") as f:
            f.write("col1\tP12345\tcol3\tGO:0001\tGO:0002\tcol6\n")
            f.write("col1\tP67890\tcol3\tGO:0003\tGO:0004\tcol6\n")
        
        result = parse_gaf_to_uniprot_GO(gaf_file)
        
        self.assertIsInstance(result, dict)
        self.assertIn("P12345", result)
        self.assertIn("P67890", result)

    def test_parse_gaf_with_filter(self):
        """Test GAF parsing with term filtering."""
        import os
        gaf_file = os.path.join(self.temp_dir, "test.gaf")
        with open(gaf_file, "w") as f:
            # Write multiple lines with repeated GO terms
            for i in range(10):
                f.write(f"col1\tP{i:05d}\tcol3\tGO:0001\tGO:0001\tcol6\n")
            # Less frequent term
            f.write("col1\tP99999\tcol3\tGO:0099\tGO:0099\tcol6\n")
        
        result = parse_gaf_to_uniprot_GO(gaf_file, filter_terms=5)
        
        self.assertIsInstance(result, dict)
        # The top term should be GO:0001 (appears 20 times)
        # The filtering should keep the top 5 terms

    def test_parse_gaf_malformed_lines(self):
        """Test GAF parsing handles malformed lines gracefully."""
        import os
        gaf_file = os.path.join(self.temp_dir, "test.gaf")
        with open(gaf_file, "w") as f:
            # Valid line
            f.write("col1\tP12345\tcol3\tGO:0001\tGO:0002\tcol6\n")
            # Malformed lines (too few columns)
            f.write("col1\tP67890\n")
            f.write("col1\n")
            # Another valid line
            f.write("col1\tP11111\tcol3\tGO:0003\tGO:0004\tcol6\n")
        
        result = parse_gaf_to_uniprot_GO(gaf_file)
        
        self.assertIsInstance(result, dict)
        self.assertIn("P12345", result)
        self.assertIn("P11111", result)
        # Malformed lines should be skipped

    def test_parse_gaf_go_in_column_4(self):
        """Test parsing when GO term is in column 4."""
        import os
        gaf_file = os.path.join(self.temp_dir, "test.gaf")
        with open(gaf_file, "w") as f:
            f.write("col1\tP12345\tcol3\tcol4\tGO:0001\tcol6\n")
        
        result = parse_gaf_to_uniprot_GO(gaf_file)
        
        self.assertIsInstance(result, dict)
        self.assertIn("P12345", result)
        self.assertIn("GO:0001", result["P12345"])

    def test_parse_gaf_go_in_column_3(self):
        """Test parsing when GO term is in column 3."""
        import os
        gaf_file = os.path.join(self.temp_dir, "test.gaf")
        with open(gaf_file, "w") as f:
            f.write("col1\tP12345\tcol3\tGO:0002\tcol5\tcol6\n")
        
        result = parse_gaf_to_uniprot_GO(gaf_file)
        
        self.assertIsInstance(result, dict)
        self.assertIn("P12345", result)
        self.assertIn("GO:0002", result["P12345"])

    def test_parse_gaf_empty_file(self):
        """Test parsing an empty GAF file."""
        import os
        gaf_file = os.path.join(self.temp_dir, "empty.gaf")
        with open(gaf_file, "w") as f:
            pass
        
        result = parse_gaf_to_uniprot_GO(gaf_file)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 0)


if __name__ == "__main__":
    unittest.main()
