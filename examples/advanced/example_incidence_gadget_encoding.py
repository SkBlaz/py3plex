"""
Example demonstrating incidence gadget encoding for multiplex networks.

This example shows how to transform a multiplex network into a homogeneous
hypergraph using incidence gadget encoding with prime-based layer signatures.

SKIP_CI: external_deps - Requires sympy package
"""

import networkx as nx

from py3plex.core import multinet


def example_basic_encoding():
    """Basic example of encoding and decoding a multiplex network."""
    print("=" * 70)
    print("BASIC INCIDENCE GADGET ENCODING EXAMPLE")
    print("=" * 70)

    # Create a simple multiplex network
    network = multinet.multi_layer_network(directed=False)

    # Add nodes to layers using dict format
    network.add_nodes(
        [
            {"source": "1", "type": "A"},
            {"source": "2", "type": "A"},
            {"source": "3", "type": "A"},
            {"source": "1", "type": "B"},
            {"source": "3", "type": "B"},
            {"source": "2", "type": "C"},
            {"source": "4", "type": "C"},
        ],
        input_type="dict",
    )

    # Add edges using dict format
    network.add_edges(
        [
            {"source": "1", "target": "2", "source_type": "A", "target_type": "A"},
            {"source": "2", "target": "3", "source_type": "A", "target_type": "A"},
            {"source": "1", "target": "3", "source_type": "B", "target_type": "B"},
            {"source": "2", "target": "4", "source_type": "C", "target_type": "C"},
        ],
        input_type="dict",
    )

    print("\nOriginal multiplex network:")
    print(f"  Nodes: {len(list(network.get_nodes()))}")
    print(f"  Edges: {len(list(network.get_edges()))}")

    # Encode to homogeneous hypergraph
    print("\nEncoding to homogeneous hypergraph...")
    H, node_mapping, edge_info = network.to_homogeneous_hypergraph()

    print("\nHomogeneous graph H:")
    print(f"  Nodes: {len(H.nodes())}")
    print(f"  Edges: {len(H.edges())}")

    print("\nNode mapping (original -> vertex-node):")
    for orig, mapped in sorted(node_mapping.items()):
        print(f"  {orig} -> {mapped}")

    print("\nEdge information (edge-node -> (layer, endpoints)):")
    for edge_node, (layer, endpoints) in sorted(edge_info.items()):
        print(f"  {edge_node} -> Layer: {layer}, Endpoints: {endpoints}")

    # Decode back to multiplex
    print("\nDecoding back to multiplex...")
    recovered = network.from_homogeneous_hypergraph(H)

    print("\nRecovered multiplex:")
    for layer, edges in sorted(recovered.items()):
        print(f"  {layer}: {edges}")

    print()


def example_social_network():
    """Example using a social network with multiple relationship types."""
    print("=" * 70)
    print("SOCIAL NETWORK MULTIPLEX EXAMPLE")
    print("=" * 70)

    # Create a multiplex social network
    network = multinet.multi_layer_network(directed=False)

    # Define people and relationship types
    people = ["Alice", "Bob", "Charlie", "Diana"]

    # Friendship layer
    network.add_nodes(
        [{"source": p, "type": "friendship"} for p in people], input_type="dict"
    )
    network.add_edges(
        [
            {
                "source": "Alice",
                "target": "Bob",
                "source_type": "friendship",
                "target_type": "friendship",
            },
            {
                "source": "Bob",
                "target": "Charlie",
                "source_type": "friendship",
                "target_type": "friendship",
            },
            {
                "source": "Charlie",
                "target": "Diana",
                "source_type": "friendship",
                "target_type": "friendship",
            },
        ],
        input_type="dict",
    )

    # Colleague layer
    network.add_nodes(
        [{"source": p, "type": "colleague"} for p in ["Alice", "Bob", "Diana"]],
        input_type="dict",
    )
    network.add_edges(
        [
            {
                "source": "Alice",
                "target": "Bob",
                "source_type": "colleague",
                "target_type": "colleague",
            },
            {
                "source": "Alice",
                "target": "Diana",
                "source_type": "colleague",
                "target_type": "colleague",
            },
        ],
        input_type="dict",
    )

    # Family layer
    network.add_nodes(
        [{"source": p, "type": "family"} for p in ["Alice", "Charlie", "Diana"]],
        input_type="dict",
    )
    network.add_edges(
        [
            {
                "source": "Alice",
                "target": "Charlie",
                "source_type": "family",
                "target_type": "family",
            }
        ],
        input_type="dict",
    )

    print("\nMultiplex social network:")
    print(f"  People: {people}")
    print(f"  Total connections: {len(list(network.get_edges()))}")

    # Encode
    H, node_mapping, edge_info = network.to_homogeneous_hypergraph()

    print("\nEncoded as homogeneous hypergraph:")
    print(f"  Nodes in H: {len(H.nodes())}")
    print(f"  Edges in H: {len(H.edges())}")
    print(f"  Connected components: {nx.number_connected_components(H)}")

    print("\nRelationships encoded:")
    for edge_node, (layer, (u, v)) in sorted(edge_info.items()):
        print(f"  {u} <--> {v} via {layer}")

    # Demonstrate that structure is preserved
    print("\nVerifying structure preservation:")
    recovered = network.from_homogeneous_hypergraph(H)

    original_edges = len(list(network.get_edges()))
    recovered_edges = sum(len(edges) for edges in recovered.values())
    print(f"  Original edges: {original_edges}")
    print(f"  Recovered edges: {recovered_edges}")
    print(f"  Match: {original_edges == recovered_edges}")

    print()


def example_cycle_detection():
    """Example showing how cycle structure encodes layer information."""
    print("=" * 70)
    print("CYCLE STRUCTURE ANALYSIS")
    print("=" * 70)

    # Create a network with 3 layers
    network = multinet.multi_layer_network(directed=False)

    for layer_name in ["Layer1", "Layer2", "Layer3"]:
        network.add_nodes(
            [{"source": "A", "type": layer_name}, {"source": "B", "type": layer_name}],
            input_type="dict",
        )
        network.add_edges(
            [
                {
                    "source": "A",
                    "target": "B",
                    "source_type": layer_name,
                    "target_type": layer_name,
                }
            ],
            input_type="dict",
        )

    print("\nCreated 3 layers, each with one edge A-B")

    H, node_mapping, edge_info = network.to_homogeneous_hypergraph()

    print("\nHomogeneous graph statistics:")
    print(f"  Total nodes: {len(H.nodes())}")
    print(f"  Total edges: {len(H.edges())}")

    print("\nCycle analysis:")
    print("  Each layer is encoded with a unique prime cycle length:")

    from sympy import primerange

    primes = list(primerange(2, 20))
    print(f"  First few primes: {primes[:5]}")

    # Analyze cycles
    all_cycles = nx.cycle_basis(H)
    print(f"\n  Number of cycles found: {len(all_cycles)}")
    print(f"  Cycle lengths: {sorted([len(c) for c in all_cycles])}")

    # Each edge-node should have a cycle through it
    print("\n  Edge-node analysis:")
    for edge_node, (layer, endpoints) in sorted(edge_info.items()):
        # Find cycle containing this edge-node
        cycles_with_edge = [c for c in all_cycles if edge_node in c]
        if cycles_with_edge:
            cycle_len = len(cycles_with_edge[0])
            print(
                f"    {edge_node} (layer {layer}): cycle length = {cycle_len} (prime)"
            )

    print()


def example_network_properties():
    """Example analyzing properties of the encoded hypergraph."""
    print("=" * 70)
    print("NETWORK PROPERTIES COMPARISON")
    print("=" * 70)

    # Create a multiplex network
    network = multinet.multi_layer_network(directed=False)

    # Create a small-world like structure in two layers
    for layer in ["Layer1", "Layer2"]:
        # Add nodes
        network.add_nodes(
            [{"source": str(i), "type": layer} for i in range(6)], input_type="dict"
        )
        # Create a ring
        for i in range(6):
            network.add_edges(
                [
                    {
                        "source": str(i),
                        "target": str((i + 1) % 6),
                        "source_type": layer,
                        "target_type": layer,
                    }
                ],
                input_type="dict",
            )

    print("\nOriginal multiplex network:")
    print("  Nodes per layer: 6")
    print("  Edges per layer: 6 (ring topology)")
    print(f"  Total edges: {len(list(network.get_edges()))}")

    # Encode
    H, node_mapping, edge_info = network.to_homogeneous_hypergraph()

    print("\nHomogeneous hypergraph H:")
    print(f"  Nodes: {len(H.nodes())}")
    print(f"  Edges: {len(H.edges())}")
    print(f"  Average degree: {sum(dict(H.degree()).values()) / len(H.nodes()):.2f}")
    print(f"  Connected components: {nx.number_connected_components(H)}")

    # Analyze node types in H
    vertex_nodes = [n for n in H.nodes() if str(n).startswith("v_")]
    edge_nodes = [n for n in H.nodes() if str(n).startswith("e_")]
    signature_nodes = [
        n
        for n in H.nodes()
        if not str(n).startswith("v_") and not str(n).startswith("e_")
    ]

    print("\n  Node types in H:")
    print(f"    Vertex-nodes (v_*): {len(vertex_nodes)}")
    print(f"    Edge-nodes (e_*): {len(edge_nodes)}")
    print(f"    Signature-nodes (*_s*): {len(signature_nodes)}")

    print()


if __name__ == "__main__":
    # Run all examples
    example_basic_encoding()
    example_social_network()
    example_cycle_detection()
    example_network_properties()

    print("=" * 70)
    print("All examples completed successfully!")
    print("=" * 70)
