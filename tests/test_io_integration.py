"""
Integration test for I/O system with realistic multilayer network data.

This test creates a more complex multilayer social network and verifies
that the I/O system handles it correctly.
"""

import tempfile
from pathlib import Path

import pytest

from py3plex.io import Edge, Layer, MultiLayerGraph, Node, read, write


def create_social_network():
    """Create a realistic multilayer social network."""
    graph = MultiLayerGraph(
        directed=True,
        attributes={
            "name": "Multi-platform Social Network",
            "description": "User interactions across Facebook, Twitter, and LinkedIn",
            "created": "2024-01-01",
        },
    )

    # Add layers
    graph.add_layer(
        Layer(
            id="facebook",
            attributes={
                "platform": "Facebook",
                "type": "social",
                "founded": 2004,
                "users_millions": 2900,
            },
        )
    )
    graph.add_layer(
        Layer(
            id="twitter",
            attributes={
                "platform": "Twitter",
                "type": "microblogging",
                "founded": 2006,
                "users_millions": 450,
            },
        )
    )
    graph.add_layer(
        Layer(
            id="linkedin",
            attributes={
                "platform": "LinkedIn",
                "type": "professional",
                "founded": 2003,
                "users_millions": 875,
            },
        )
    )

    # Add nodes (users)
    users = [
        ("alice", {"age": 28, "occupation": "Engineer", "city": "San Francisco"}),
        ("bob", {"age": 32, "occupation": "Designer", "city": "New York"}),
        ("charlie", {"age": 35, "occupation": "Manager", "city": "Seattle"}),
        ("diana", {"age": 29, "occupation": "Scientist", "city": "Boston"}),
        ("eve", {"age": 31, "occupation": "Writer", "city": "Austin"}),
    ]

    for user_id, attrs in users:
        graph.add_node(Node(id=user_id, attributes=attrs))

    # Add intra-layer edges (connections within same platform)
    # Facebook friendships
    facebook_edges = [
        ("alice", "bob", 0.9, "2023-01-15"),
        ("alice", "charlie", 0.8, "2023-02-20"),
        ("bob", "charlie", 0.7, "2023-03-10"),
        ("charlie", "diana", 0.85, "2023-04-05"),
        ("diana", "eve", 0.75, "2023-05-12"),
    ]

    for src, dst, weight, timestamp in facebook_edges:
        graph.add_edge(
            Edge(
                src=src,
                dst=dst,
                src_layer="facebook",
                dst_layer="facebook",
                attributes={
                    "weight": weight,
                    "timestamp": timestamp,
                    "interaction_type": "friend",
                },
            )
        )

    # Twitter follows
    twitter_edges = [
        ("alice", "charlie", 0.6, "follow"),
        ("bob", "alice", 0.7, "follow"),
        ("charlie", "diana", 0.8, "follow"),
        ("diana", "alice", 0.65, "follow"),
        ("eve", "bob", 0.7, "follow"),
    ]

    for src, dst, weight, interaction in twitter_edges:
        graph.add_edge(
            Edge(
                src=src,
                dst=dst,
                src_layer="twitter",
                dst_layer="twitter",
                attributes={"weight": weight, "interaction_type": interaction},
            )
        )

    # LinkedIn connections
    linkedin_edges = [
        ("alice", "diana", 0.9, True),
        ("bob", "charlie", 0.85, True),
        ("charlie", "eve", 0.8, False),
    ]

    for src, dst, weight, endorsed in linkedin_edges:
        graph.add_edge(
            Edge(
                src=src,
                dst=dst,
                src_layer="linkedin",
                dst_layer="linkedin",
                attributes={
                    "weight": weight,
                    "endorsed": endorsed,
                    "interaction_type": "connection",
                },
            )
        )

    # Add inter-layer edges (cross-platform relationships)
    # User links same person across platforms
    inter_layer_edges = [
        ("alice", "alice", "facebook", "twitter"),
        ("alice", "alice", "twitter", "linkedin"),
        ("bob", "bob", "facebook", "twitter"),
        ("charlie", "charlie", "facebook", "linkedin"),
    ]

    for src, dst, src_layer, dst_layer in inter_layer_edges:
        graph.add_edge(
            Edge(
                src=src,
                dst=dst,
                src_layer=src_layer,
                dst_layer=dst_layer,
                attributes={"weight": 1.0, "type": "identity"},
            )
        )

    return graph


def test_social_network_json_round_trip():
    """Test JSON round-trip with realistic data."""
    graph = create_social_network()

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Write
        write(graph, tmp_path, deterministic=True)

        # Read
        graph2 = read(tmp_path)

        # Verify structure
        assert len(graph2.nodes) == 5
        assert len(graph2.layers) == 3
        assert len(graph2.edges) == 17  # 5 + 5 + 3 + 4

        # Verify graph attributes
        assert graph2.attributes["name"] == "Multi-platform Social Network"

        # Verify layer attributes
        assert graph2.layers["facebook"].attributes["founded"] == 2004
        assert graph2.layers["twitter"].attributes["users_millions"] == 450

        # Verify node attributes
        assert graph2.nodes["alice"].attributes["occupation"] == "Engineer"
        assert graph2.nodes["charlie"].attributes["city"] == "Seattle"

        # Verify edge attributes
        facebook_edges = [
            e
            for e in graph2.edges
            if e.src_layer == "facebook" and e.dst_layer == "facebook"
        ]
        assert len(facebook_edges) == 5

        # Find specific edge
        alice_bob = [e for e in facebook_edges if e.src == "alice" and e.dst == "bob"][
            0
        ]
        assert alice_bob.attributes["weight"] == 0.9
        assert alice_bob.attributes["timestamp"] == "2023-01-15"

    finally:
        Path(tmp_path).unlink()


def test_social_network_csv_with_sidecars():
    """Test CSV format with sidecar files."""
    graph = create_social_network()

    with tempfile.TemporaryDirectory() as tmpdir:
        edges_path = Path(tmpdir) / "edges.csv"

        # Write with sidecars
        write(graph, edges_path, format="csv", write_sidecars=True, deterministic=True)

        # Verify files exist
        assert edges_path.exists()
        assert (Path(tmpdir) / "nodes.csv").exists()
        assert (Path(tmpdir) / "layers.csv").exists()

        # Read back
        graph2 = read(
            edges_path,
            format="csv",
            nodes_file=Path(tmpdir) / "nodes.csv",
            layers_file=Path(tmpdir) / "layers.csv",
        )

        # Verify structure
        assert len(graph2.nodes) == 5
        assert len(graph2.layers) == 3
        assert len(graph2.edges) == 17


def test_social_network_jsonl_streaming():
    """Test JSONL streaming format."""
    graph = create_social_network()

    with tempfile.NamedTemporaryFile(suffix=".jsonl.gz", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Write compressed JSONL
        write(graph, tmp_path, format="jsonl", deterministic=True)

        # Read back
        graph2 = read(tmp_path, format="jsonl")

        # Verify structure
        assert len(graph2.nodes) == 5
        assert len(graph2.layers) == 3
        assert len(graph2.edges) == 17

    finally:
        Path(tmp_path).unlink()


def test_social_network_statistics():
    """Test computing statistics on the loaded graph."""
    graph = create_social_network()

    # Count edges by layer
    edge_counts = {}
    for edge in graph.edges:
        layer_pair = (edge.src_layer, edge.dst_layer)
        edge_counts[layer_pair] = edge_counts.get(layer_pair, 0) + 1

    # Intra-layer counts
    assert edge_counts[("facebook", "facebook")] == 5
    assert edge_counts[("twitter", "twitter")] == 5
    assert edge_counts[("linkedin", "linkedin")] == 3

    # Inter-layer counts
    inter_layer_total = sum(
        count for (src_l, dst_l), count in edge_counts.items() if src_l != dst_l
    )
    assert inter_layer_total == 4

    # Node degree (total connections)
    node_degrees = {}
    for edge in graph.edges:
        node_degrees[edge.src] = node_degrees.get(edge.src, 0) + 1
        if not graph.directed:
            node_degrees[edge.dst] = node_degrees.get(edge.dst, 0) + 1

    # Alice should have highest degree (most active)
    assert "alice" in node_degrees
    assert node_degrees["alice"] >= 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
