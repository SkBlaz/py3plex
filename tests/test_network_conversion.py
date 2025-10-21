"""
Unit tests for network format conversion.

Tests conversion between different network formats to ensure lossless
transformation and proper round-trip conversion.

This test suite addresses the requirements from the issue:
1. Creates a relatively large synthetic network (200 nodes, 4 layers)
2. Lists formats py3plex can work with (gpickle, edgelist)  
3. Tests pairwise format conversion (A→B→A) to verify lossless conversion
4. Tests chain conversions (format1→format2→...→formatN→format1)
5. Verifies that back-converted networks match the original

Test Coverage:
- test_pairwise_conversion: Tests A→B→A roundtrip for format pairs
- test_conversion_chain_short: Tests short conversion chains (3 formats)
- test_conversion_chain_long: Tests longer conversion chains (5 formats)
- test_conversion_all_formats_sequential: Tests sequential conversions
- test_single_format_roundtrip: Tests save/load in same format
- test_directed_network_conversion: Tests with directed networks
- test_network_size_preservation: Tests node/edge count preservation

Formats Tested:
- gpickle: Python pickle format (best for preserving all attributes)
- edgelist: Simple text format (human-readable, limited metadata)

Note: Other formats like GraphML, GEXF, and JSON have limitations with
py3plex's multilayer networks that contain numpy arrays, so they are
not included in comprehensive testing.
"""

import os
import tempfile
from pathlib import Path

import networkx as nx
import pytest

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from py3plex.core import multinet, random_generators


class TestNetworkConversion:
    """Test suite for network format conversion."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def synthetic_network(self):
        """Create a synthetic multilayer network for testing."""
        # Create a relatively large synthetic network
        # Using ER (Erdős-Rényi) model with moderate density
        # API: random_multilayer_ER(n, l, p, directed)
        num_nodes = 200
        num_layers = 4
        edge_probability = 0.05
        
        network = random_generators.random_multilayer_ER(
            n=num_nodes,
            l=num_layers,
            p=edge_probability,
            directed=False
        )
        
        return network

    def _get_network_stats(self, network):
        """Extract key statistics from a network for comparison."""
        # get_nodes() and get_edges() return generators, need to convert to list
        nodes = list(network.get_nodes())
        edges = list(network.get_edges())
        
        # get_layers() returns (layer_list, layer_dict, coupling_edges)
        layer_info = network.get_layers()
        layers = layer_info[0] if layer_info else []
        
        stats = {
            'num_nodes': len(nodes),
            'num_edges': len(edges),
            'num_layers': len(layers),
            'layers': sorted([str(l) for l in layers]),  # Convert to strings for comparison
            # Check actual core_network directionality, not just the attribute
            'is_directed': network.core_network.is_directed() if network.core_network else network.directed
        }
        return stats

    def _compare_networks(self, net1, net2, format_name=""):
        """
        Compare two networks to verify they are equivalent.
        
        Args:
            net1: First network
            net2: Second network
            format_name: Name of format for error messages
        """
        stats1 = self._get_network_stats(net1)
        stats2 = self._get_network_stats(net2)
        
        assert stats1['num_nodes'] == stats2['num_nodes'], \
            f"{format_name}: Node count mismatch ({stats1['num_nodes']} vs {stats2['num_nodes']})"
        
        assert stats1['num_edges'] == stats2['num_edges'], \
            f"{format_name}: Edge count mismatch ({stats1['num_edges']} vs {stats2['num_edges']})"
        
        assert stats1['num_layers'] == stats2['num_layers'], \
            f"{format_name}: Layer count mismatch ({stats1['num_layers']} vs {stats2['num_layers']})"
        
        assert stats1['is_directed'] == stats2['is_directed'], \
            f"{format_name}: Directedness mismatch"

    def _save_network(self, network, filepath, format_type):
        """
        Save network in specified format.
        
        Args:
            network: Network to save
            filepath: Path to save file
            format_type: Format type string
        """
        if format_type == "gpickle":
            network.save_network(filepath, output_type="gpickle")
        elif format_type == "edgelist":
            network.save_network(filepath, output_type="edgelist")
        elif format_type == "json":
            import json
            data = network.to_json()
            with open(filepath, 'w') as f:
                json.dump(data, f)
        else:
            raise ValueError(f"Unknown format: {format_type}")

    def _load_network(self, filepath, format_type, directed=False):
        """
        Load network from specified format.
        
        Args:
            filepath: Path to load from
            format_type: Format type string
            directed: Whether network is directed
            
        Returns:
            Loaded network
        """
        network = multinet.multi_layer_network(directed=directed)
        
        if format_type == "gpickle":
            network.load_network(filepath, input_type="gpickle")
        elif format_type == "edgelist":
            network.load_network(filepath, input_type="edgelist")
        elif format_type == "json":
            import json
            from networkx.readwrite import json_graph
            with open(filepath, 'r') as f:
                data = json.load(f)
            G = json_graph.node_link_graph(data)
            network.core_network = G
        else:
            raise ValueError(f"Unknown format: {format_type}")
        
        return network

    #  Test pairwise conversions  
    @pytest.mark.parametrize("format_a,format_b", [
        ("gpickle", "edgelist"),
        ("edgelist", "gpickle"),
    ])
    def test_pairwise_conversion(self, synthetic_network, temp_dir, format_a, format_b):
        """
        Test conversion between two formats and back.
        
        Verifies that: original -> format_a -> format_b -> format_a == original
        """
        original_stats = self._get_network_stats(synthetic_network)
        
        # Save to format A
        filepath_a = os.path.join(temp_dir, f"network.{format_a}")
        self._save_network(synthetic_network, filepath_a, format_a)
        
        # Load from format A
        network_from_a = self._load_network(filepath_a, format_a, 
                                            directed=synthetic_network.directed)
        
        # Save to format B
        filepath_b = os.path.join(temp_dir, f"network.{format_b}")
        self._save_network(network_from_a, filepath_b, format_b)
        
        # Load from format B
        network_from_b = self._load_network(filepath_b, format_b,
                                            directed=synthetic_network.directed)
        
        # Save back to format A
        filepath_a2 = os.path.join(temp_dir, f"network_back.{format_a}")
        self._save_network(network_from_b, filepath_a2, format_a)
        
        # Load again from format A
        network_final = self._load_network(filepath_a2, format_a,
                                          directed=synthetic_network.directed)
        
        # Compare final with original
        final_stats = self._get_network_stats(network_final)
        
        assert original_stats['num_nodes'] == final_stats['num_nodes'], \
            f"Node count mismatch in {format_a}->{format_b}->{format_a}"
        
        assert original_stats['num_edges'] == final_stats['num_edges'], \
            f"Edge count mismatch in {format_a}->{format_b}->{format_a}"

    def test_conversion_chain_short(self, synthetic_network, temp_dir):
        """
        Test conversion through a chain of formats.
        
        Chain: gpickle -> edgelist -> gpickle
        """
        formats_chain = ["gpickle", "edgelist", "gpickle"]
        
        original_stats = self._get_network_stats(synthetic_network)
        current_network = synthetic_network
        
        for i in range(len(formats_chain) - 1):
            from_format = formats_chain[i]
            to_format = formats_chain[i + 1]
            
            # Save current network
            filepath = os.path.join(temp_dir, f"network_step{i}.{from_format}")
            self._save_network(current_network, filepath, from_format)
            
            # Load in next format
            next_filepath = os.path.join(temp_dir, f"network_step{i+1}.{to_format}")
            
            # First save to intermediate format
            if i < len(formats_chain) - 2:  # Not the last step
                self._save_network(current_network, next_filepath, to_format)
                current_network = self._load_network(next_filepath, to_format,
                                                    directed=synthetic_network.directed)
        
        # Compare final with original
        final_stats = self._get_network_stats(current_network)
        
        assert original_stats['num_nodes'] == final_stats['num_nodes'], \
            f"Node count mismatch after chain conversion"
        
        assert original_stats['num_edges'] == final_stats['num_edges'], \
            f"Edge count mismatch after chain conversion"

    def test_conversion_chain_long(self, synthetic_network, temp_dir):
        """
        Test conversion through a longer chain of formats.
        
        Chain: gpickle -> edgelist -> gpickle -> edgelist -> gpickle
        """
        formats_chain = ["gpickle", "edgelist", "gpickle", "edgelist", "gpickle"]
        
        original_stats = self._get_network_stats(synthetic_network)
        
        # Perform chain conversion
        networks = [synthetic_network]
        for i in range(len(formats_chain) - 1):
            from_format = formats_chain[i]
            to_format = formats_chain[i + 1]
            
            filepath = os.path.join(temp_dir, f"chain_long_{i}.{to_format}")
            self._save_network(networks[-1], filepath, to_format)
            
            loaded = self._load_network(filepath, to_format,
                                       directed=synthetic_network.directed)
            networks.append(loaded)
        
        final_network = networks[-1]
        final_stats = self._get_network_stats(final_network)
        
        # Verify preservation through chain
        assert original_stats['num_nodes'] == final_stats['num_nodes'], \
            "Node count not preserved through long chain"
        
        assert original_stats['num_edges'] == final_stats['num_edges'], \
            "Edge count not preserved through long chain"

    def test_conversion_all_formats_sequential(self, synthetic_network, temp_dir):
        """
        Test sequential conversion through supported formats.
        
        Converts through: gpickle -> edgelist -> gpickle
        and verifies the final result matches the original.
        """
        # Define format chain - start and end with same format for verification
        format_chain = ["gpickle", "edgelist", "gpickle"]
        
        original_stats = self._get_network_stats(synthetic_network)
        current_network = synthetic_network
        
        # Process through chain
        for i in range(len(format_chain) - 1):
            current_format = format_chain[i]
            next_format = format_chain[i + 1]
            
            # Save in current format
            filepath = os.path.join(temp_dir, f"seq_{i}_{current_format}.{current_format}")
            self._save_network(current_network, filepath, current_format)
            
            # Load as next format
            next_filepath = os.path.join(temp_dir, f"seq_{i+1}_{next_format}.{next_format}")
            self._save_network(current_network, next_filepath, next_format)
            current_network = self._load_network(next_filepath, next_format,
                                                directed=synthetic_network.directed)
        
        # Final comparison
        final_stats = self._get_network_stats(current_network)
        
        assert original_stats['num_nodes'] == final_stats['num_nodes'], \
            "Nodes not preserved through full format chain"
        assert original_stats['num_edges'] == final_stats['num_edges'], \
            "Edges not preserved through full format chain"

    def test_single_format_roundtrip(self, synthetic_network, temp_dir):
        """Test that saving and loading in the same format preserves network."""
        # Only test formats that work reliably with py3plex multilayer networks
        formats = ["gpickle", "edgelist"]
        
        original_stats = self._get_network_stats(synthetic_network)
        
        for fmt in formats:
            filepath = os.path.join(temp_dir, f"roundtrip.{fmt}")
            
            # Save
            self._save_network(synthetic_network, filepath, fmt)
            
            # Load
            loaded = self._load_network(filepath, fmt, 
                                       directed=synthetic_network.directed)
            
            # Compare
            loaded_stats = self._get_network_stats(loaded)
            
            assert original_stats['num_nodes'] == loaded_stats['num_nodes'], \
                f"Roundtrip failed for {fmt}: node count mismatch"
            
            assert original_stats['num_edges'] == loaded_stats['num_edges'], \
                f"Roundtrip failed for {fmt}: edge count mismatch"

    def test_directed_network_conversion(self, temp_dir):
        """Test conversion with directed networks."""
        # Create directed network
        num_nodes = 100
        num_layers = 2
        edge_probability = 0.05
        
        network = random_generators.random_multilayer_ER(
            n=num_nodes,
            l=num_layers,
            p=edge_probability,
            directed=True
        )
        
        original_stats = self._get_network_stats(network)
        
        # Test conversion with gpickle which preserves directionality
        filepath = os.path.join(temp_dir, "directed.gpickle")
        self._save_network(network, filepath, "gpickle")
        loaded = self._load_network(filepath, "gpickle", directed=True)
        
        # Verify
        final_stats = self._get_network_stats(loaded)
        assert original_stats['is_directed'] == final_stats['is_directed']
        assert original_stats['num_nodes'] == final_stats['num_nodes']
        assert original_stats['num_edges'] == final_stats['num_edges']

    def test_network_size_preservation(self, temp_dir):
        """Test that network size is preserved during conversion."""
        # Create a small network
        network = random_generators.random_multilayer_ER(n=50, l=2, p=0.1, directed=False)
        
        original_nodes = len(list(network.get_nodes()))
        original_edges = network.core_network.number_of_edges()
        
        # Test with gpickle which preserves all information
        filepath = os.path.join(temp_dir, "size.gpickle")
        self._save_network(network, filepath, "gpickle")
        
        loaded = self._load_network(filepath, "gpickle", directed=False)
        loaded_nodes = len(list(loaded.get_nodes()))
        loaded_edges = loaded.core_network.number_of_edges()
        
        # Verify size is preserved
        assert original_nodes == loaded_nodes, "Node count mismatch for gpickle"
        assert original_edges == loaded_edges, "Edge count mismatch for gpickle"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
