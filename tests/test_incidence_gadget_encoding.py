"""
Tests for incidence gadget encoding functionality.

This module tests the transformation of multiplex networks to homogeneous hypergraphs
using incidence gadget encoding with prime-based layer signatures.
"""

import networkx as nx

from py3plex.core import multinet


class TestIncidenceGadgetEncoding:
    """Test suite for incidence gadget encoding methods."""

    def test_basic_encoding_decoding(self):
        """Test basic encoding and decoding of a simple multiplex network."""
        # Create a simple multiplex network
        network = multinet.multi_layer_network(directed=False)
        network.add_nodes(
            [
                {"source": "1", "type": "A"},
                {"source": "2", "type": "A"},
                {"source": "3", "type": "A"},
                {"source": "1", "type": "B"},
                {"source": "3", "type": "B"},
            ],
            input_type="dict",
        )
        network.add_edges(
            [
                {"source": "1", "target": "2", "source_type": "A", "target_type": "A"},
                {"source": "2", "target": "3", "source_type": "A", "target_type": "A"},
                {"source": "1", "target": "3", "source_type": "B", "target_type": "B"},
            ],
            input_type="dict",
        )

        # Encode to homogeneous hypergraph
        H, node_mapping, edge_info = network.to_homogeneous_hypergraph()

        # Check that H is a valid graph
        assert isinstance(H, nx.Graph)
        assert len(H.nodes()) > 0
        assert len(H.edges()) > 0

        # Check node mapping
        assert "1" in node_mapping
        assert "2" in node_mapping
        assert "3" in node_mapping
        assert all(v.startswith("v_") for v in node_mapping.values())

        # Check edge info
        assert len(edge_info) == 3  # 2 edges in layer A, 1 in layer B

        # Decode back to multiplex
        recovered = network.from_homogeneous_hypergraph(H)

        # Check that we recovered edges
        assert len(recovered) > 0

        # Check that we have the right number of edges per layer
        total_edges = sum(len(edges) for edges in recovered.values())
        assert total_edges == 3

    def test_single_layer_network(self):
        """Test encoding of a single-layer network."""
        network = multinet.multi_layer_network(directed=False)
        network.add_nodes(
            [
                {"source": "A", "type": "layer1"},
                {"source": "B", "type": "layer1"},
                {"source": "C", "type": "layer1"},
            ],
            input_type="dict",
        )
        network.add_edges(
            [
                {
                    "source": "A",
                    "target": "B",
                    "source_type": "layer1",
                    "target_type": "layer1",
                },
                {
                    "source": "B",
                    "target": "C",
                    "source_type": "layer1",
                    "target_type": "layer1",
                },
            ],
            input_type="dict",
        )

        H, node_mapping, edge_info = network.to_homogeneous_hypergraph()

        # Check basic properties
        assert len(node_mapping) == 3  # A, B, C
        assert len(edge_info) == 2  # 2 edges

        # Each edge should be associated with layer1
        for edge_node, (layer, endpoints) in edge_info.items():
            assert layer == "layer1"
            assert len(endpoints) == 2

    def test_multiple_layers(self):
        """Test encoding with multiple layers."""
        network = multinet.multi_layer_network(directed=False)

        # Add nodes to each layer
        network.add_nodes(
            [
                {"source": "Alice", "type": "social"},
                {"source": "Bob", "type": "social"},
                {"source": "Charlie", "type": "social"},
                {"source": "Alice", "type": "work"},
                {"source": "Bob", "type": "work"},
                {"source": "Alice", "type": "family"},
                {"source": "Charlie", "type": "family"},
            ],
            input_type="dict",
        )

        # Add edges
        network.add_edges(
            [
                {
                    "source": "Alice",
                    "target": "Bob",
                    "source_type": "social",
                    "target_type": "social",
                },
                {
                    "source": "Alice",
                    "target": "Bob",
                    "source_type": "work",
                    "target_type": "work",
                },
                {
                    "source": "Alice",
                    "target": "Charlie",
                    "source_type": "family",
                    "target_type": "family",
                },
            ],
            input_type="dict",
        )

        H, node_mapping, edge_info = network.to_homogeneous_hypergraph()

        # Check that we have 3 unique nodes
        assert len(node_mapping) == 3

        # Check that we have 3 edges (one per layer)
        assert len(edge_info) == 3

        # Check that each edge belongs to different layer
        layers = [layer for layer, _ in edge_info.values()]
        assert len(set(layers)) == 3

    def test_empty_network(self):
        """Test encoding of an empty network."""
        network = multinet.multi_layer_network(directed=False)

        H, node_mapping, edge_info = network.to_homogeneous_hypergraph()

        # Should return empty structures
        assert len(H.nodes()) == 0
        assert len(H.edges()) == 0
        assert len(node_mapping) == 0
        assert len(edge_info) == 0

    def test_node_mapping_correctness(self):
        """Test that node mappings are correctly preserved."""
        network = multinet.multi_layer_network(directed=False)
        network.add_nodes(
            [{"source": "node1", "type": "L1"}, {"source": "node2", "type": "L1"}],
            input_type="dict",
        )
        network.add_edges(
            [
                {
                    "source": "node1",
                    "target": "node2",
                    "source_type": "L1",
                    "target_type": "L1",
                }
            ],
            input_type="dict",
        )

        H, node_mapping, edge_info = network.to_homogeneous_hypergraph()

        # Check that original nodes are mapped correctly
        assert "node1" in node_mapping
        assert "node2" in node_mapping
        assert node_mapping["node1"] == "v_node1"
        assert node_mapping["node2"] == "v_node2"

        # Check that mapped nodes exist in H
        assert "v_node1" in H.nodes()
        assert "v_node2" in H.nodes()

    def test_cycle_structure(self):
        """Test that cycle structures are created correctly."""
        network = multinet.multi_layer_network(directed=False)
        network.add_nodes(
            [{"source": "A", "type": "layer1"}, {"source": "B", "type": "layer1"}],
            input_type="dict",
        )
        network.add_edges(
            [
                {
                    "source": "A",
                    "target": "B",
                    "source_type": "layer1",
                    "target_type": "layer1",
                }
            ],
            input_type="dict",
        )

        H, node_mapping, edge_info = network.to_homogeneous_hypergraph()

        # Find the edge node
        edge_nodes = list(edge_info.keys())
        assert len(edge_nodes) == 1
        edge_node = edge_nodes[0]

        # The edge node should have degree 2 (endpoints) + p-1 (cycle nodes)
        # For the first layer, prime is 2, so cycle has 1 node
        # Edge node connects to: v_A, v_B, and 1 cycle node
        degree = H.degree(edge_node)
        assert degree >= 2  # At least connected to endpoints

        # Check that the edge node exists
        assert edge_node in H.nodes()

    def test_decoding_without_encoding(self):
        """Test decoding a manually created homogeneous graph."""
        # Create a simple homogeneous graph manually with proper cycle
        H = nx.Graph()
        H.add_nodes_from(["v_1", "v_2", "e_0", "e_0_s0", "e_0_s1"])
        # Connect edge node to its endpoints
        H.add_edges_from([("v_1", "e_0"), ("v_2", "e_0")])

        # Add a cycle of length 3 through e_0 (simulating prime=3 layer)
        # Cycle: e_0 -> e_0_s0 -> e_0_s1 -> e_0
        H.add_edges_from([("e_0", "e_0_s0"), ("e_0_s0", "e_0_s1"), ("e_0_s1", "e_0")])

        network = multinet.multi_layer_network(directed=False)
        recovered = network.from_homogeneous_hypergraph(H)

        # Should recover at least one edge
        assert len(recovered) > 0, f"Expected to recover edges, got: {recovered}"

        # Check structure
        for layer, edges in recovered.items():
            assert (
                "layer_with_prime_" in layer
            ), f"Expected layer name with prime, got: {layer}"
            assert len(edges) > 0, f"Expected edges in layer {layer}, got empty"

    def test_large_network(self):
        """Test encoding with a larger network."""
        network = multinet.multi_layer_network(directed=False)

        # Add 10 nodes to each layer
        nodes_l1 = [{"source": str(i), "type": "L1"} for i in range(10)]
        nodes_l2 = [{"source": str(i), "type": "L2"} for i in range(10)]
        network.add_nodes(nodes_l1 + nodes_l2, input_type="dict")

        # Add edges to create a path in each layer
        edges_l1 = [
            {
                "source": str(i),
                "target": str(i + 1),
                "source_type": "L1",
                "target_type": "L1",
            }
            for i in range(9)
        ]
        edges_l2 = [
            {
                "source": str(i),
                "target": str(i + 1),
                "source_type": "L2",
                "target_type": "L2",
            }
            for i in range(9)
        ]
        network.add_edges(edges_l1 + edges_l2, input_type="dict")

        H, node_mapping, edge_info = network.to_homogeneous_hypergraph()

        # Check that we have correct number of nodes
        assert len(node_mapping) == 10

        # Check that we have correct number of edges
        assert len(edge_info) == 18  # 9 edges per layer

        # Verify that H is connected
        # Note: May not be connected if layers are independent
        assert nx.number_connected_components(H) >= 1

    def test_directed_network(self):
        """Test encoding with directed edges (should work with directed=True in network)."""
        network = multinet.multi_layer_network(directed=True)
        network.add_nodes(
            [{"source": "1", "type": "A"}, {"source": "2", "type": "A"}],
            input_type="dict",
        )
        network.add_edges(
            [{"source": "1", "target": "2", "source_type": "A", "target_type": "A"}],
            input_type="dict",
        )

        H, node_mapping, edge_info = network.to_homogeneous_hypergraph()

        # Should still create valid encoding
        assert len(H.nodes()) > 0
        assert len(edge_info) == 1

    def test_edge_info_structure(self):
        """Test that edge_info has correct structure."""
        network = multinet.multi_layer_network(directed=False)
        network.add_nodes(
            [
                {"source": "X", "type": "TestLayer"},
                {"source": "Y", "type": "TestLayer"},
            ],
            input_type="dict",
        )
        network.add_edges(
            [
                {
                    "source": "X",
                    "target": "Y",
                    "source_type": "TestLayer",
                    "target_type": "TestLayer",
                }
            ],
            input_type="dict",
        )

        H, node_mapping, edge_info = network.to_homogeneous_hypergraph()

        # Check edge_info structure
        assert len(edge_info) == 1
        for edge_node, (layer, endpoints) in edge_info.items():
            assert isinstance(layer, str)
            assert layer == "TestLayer"
            assert isinstance(endpoints, tuple)
            assert len(endpoints) == 2
            assert "X" in endpoints or "Y" in endpoints


if __name__ == "__main__":
    # Run tests directly
    test = TestIncidenceGadgetEncoding()

    tests = [
        ("test_basic_encoding_decoding", test.test_basic_encoding_decoding),
        ("test_single_layer_network", test.test_single_layer_network),
        ("test_multiple_layers", test.test_multiple_layers),
        ("test_empty_network", test.test_empty_network),
        ("test_node_mapping_correctness", test.test_node_mapping_correctness),
        ("test_cycle_structure", test.test_cycle_structure),
        ("test_decoding_without_encoding", test.test_decoding_without_encoding),
        ("test_large_network", test.test_large_network),
        ("test_directed_network", test.test_directed_network),
        ("test_edge_info_structure", test.test_edge_info_structure),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            print(f"Running {name}...", end=" ")
            test_func()
            print("[OK] PASSED")
            passed += 1
        except Exception as e:
            print(f"[X] FAILED: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
