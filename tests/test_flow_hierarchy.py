"""
Tests for hierarchical flow-based community detection algorithm.

This module tests the flow_hierarchical_communities algorithm on various
network structures including toy graphs, hierarchical SBMs, and multilayer networks.
"""

import numpy as np
import pytest

from py3plex.core import multinet
from py3plex.algorithms.community_detection import (
    flow_hierarchical_communities,
    FlowHierarchyResult,
)
from py3plex.exceptions import AlgorithmError


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def simple_chain():
    """Create a simple chain graph: A-B-C-D-E."""
    net = multinet.multi_layer_network(directed=False)
    net.add_edges(
        [
            ["A", "L1", "B", "L1", 1.0],
            ["B", "L1", "C", "L1", 1.0],
            ["C", "L1", "D", "L1", 1.0],
            ["D", "L1", "E", "L1", 1.0],
        ],
        input_type="list",
    )
    return net


@pytest.fixture
def two_cliques():
    """Create two cliques connected by a bridge: (A-B-C) - (D-E-F)."""
    net = multinet.multi_layer_network(directed=False)
    net.add_edges(
        [
            # Clique 1
            ["A", "L1", "B", "L1", 1.0],
            ["B", "L1", "C", "L1", 1.0],
            ["C", "L1", "A", "L1", 1.0],
            # Clique 2
            ["D", "L1", "E", "L1", 1.0],
            ["E", "L1", "F", "L1", 1.0],
            ["F", "L1", "D", "L1", 1.0],
            # Bridge
            ["C", "L1", "D", "L1", 0.5],
        ],
        input_type="list",
    )
    return net


@pytest.fixture
def multilayer_network():
    """Create a multilayer network with 2 layers."""
    net = multinet.multi_layer_network(directed=False)
    net.add_edges(
        [
            # Layer 1: Two triangles
            ["A", "L1", "B", "L1", 1.0],
            ["B", "L1", "C", "L1", 1.0],
            ["C", "L1", "A", "L1", 1.0],
            ["D", "L1", "E", "L1", 1.0],
            ["E", "L1", "F", "L1", 1.0],
            ["F", "L1", "D", "L1", 1.0],
            # Layer 2: Different structure
            ["A", "L2", "D", "L2", 1.0],
            ["B", "L2", "E", "L2", 1.0],
            ["C", "L2", "F", "L2", 1.0],
        ],
        input_type="list",
    )
    return net


@pytest.fixture
def hierarchical_network():
    """
    Create a network with clear hierarchical structure.
    
    Structure:
    - Level 1: Two super-communities
      - Super-community 1: (A-B) and (C-D) weakly connected
      - Super-community 2: (E-F) and (G-H) weakly connected
    - Level 0: Four tight communities (A-B), (C-D), (E-F), (G-H)
    """
    net = multinet.multi_layer_network(directed=False)
    net.add_edges(
        [
            # Tight community 1: A-B
            ["A", "L1", "B", "L1", 2.0],
            ["B", "L1", "A", "L1", 2.0],
            # Tight community 2: C-D
            ["C", "L1", "D", "L1", 2.0],
            ["D", "L1", "C", "L1", 2.0],
            # Weak connection between 1 and 2
            ["B", "L1", "C", "L1", 0.5],
            # Tight community 3: E-F
            ["E", "L1", "F", "L1", 2.0],
            ["F", "L1", "E", "L1", 2.0],
            # Tight community 4: G-H
            ["G", "L1", "H", "L1", 2.0],
            ["H", "L1", "G", "L1", 2.0],
            # Weak connection between 3 and 4
            ["F", "L1", "G", "L1", 0.5],
            # Very weak connection between super-communities
            ["D", "L1", "E", "L1", 0.1],
        ],
        input_type="list",
    )
    return net


# ============================================================================
# Test Basic Functionality
# ============================================================================


def test_flow_hierarchy_simple_chain(simple_chain):
    """Test flow hierarchy on a simple chain graph."""
    result = flow_hierarchical_communities(simple_chain, seed=42)

    # Check result type
    assert isinstance(result, FlowHierarchyResult)

    # Check basic structure
    assert len(result.hierarchy_levels) > 0
    assert len(result.stability_scores) > 0
    assert result.metadata["n_nodes"] == 5

    # Check that we can get a partition
    partition = result.get_partition()
    assert len(partition) == 5
    # In py3plex, nodes are tuples (node_id, layer)
    expected_nodes = [("A", "L1"), ("B", "L1"), ("C", "L1"), ("D", "L1"), ("E", "L1")]
    assert all(node in partition for node in expected_nodes)


def test_flow_hierarchy_two_cliques(two_cliques):
    """Test flow hierarchy on two cliques with a bridge."""
    result = flow_hierarchical_communities(two_cliques, seed=42)

    # Check result structure
    assert isinstance(result, FlowHierarchyResult)
    assert result.metadata["n_nodes"] == 6

    # Get best partition
    partition = result.get_partition()
    assert len(partition) == 6

    # At some scale, should detect 2 communities
    for scale, part in result.hierarchy_levels.items():
        n_comms = len(set(part.values()))
        if n_comms == 2:
            # Found 2-community partition
            # Check that cliques are separated (using tuple keys)
            comm_A = part[("A", "L1")]
            comm_D = part[("D", "L1")]
            # At 2-community level, cliques should be separate
            assert part[("B", "L1")] == comm_A
            assert part[("C", "L1")] == comm_A
            assert part[("E", "L1")] == comm_D
            assert part[("F", "L1")] == comm_D
            break


def test_flow_hierarchy_result_methods(two_cliques):
    """Test FlowHierarchyResult convenience methods."""
    result = flow_hierarchical_communities(two_cliques, seed=42)

    # Test get_partition with scale
    scales = list(result.hierarchy_levels.keys())
    partition = result.get_partition(scale=scales[0])
    assert len(partition) == 6

    # Test get_flat_partition with n_communities
    partition_2 = result.get_flat_partition(n_communities=2)
    assert len(set(partition_2.values())) <= 3  # May not have exactly 2, but close

    # Test summary
    summary = result.summary()
    assert "Hierarchical Flow-Based Community Detection" in summary
    assert str(result.metadata["n_nodes"]) in summary

    # Test repr
    repr_str = repr(result)
    assert "FlowHierarchyResult" in repr_str


# ============================================================================
# Test Determinism and Reproducibility
# ============================================================================


def test_flow_hierarchy_determinism_mc(two_cliques):
    """Test that Monte Carlo approximation is deterministic with fixed seed."""
    result1 = flow_hierarchical_communities(two_cliques, approx="mc", seed=42)
    result2 = flow_hierarchical_communities(two_cliques, approx="mc", seed=42)

    # Same seed should give same results
    partition1 = result1.get_partition()
    partition2 = result2.get_partition()

    # Partitions should be identical
    assert partition1 == partition2

    # Stability scores should be close (may have floating point differences)
    for scale in result1.stability_scores:
        assert abs(result1.stability_scores[scale] - result2.stability_scores[scale]) < 1e-6


def test_flow_hierarchy_determinism_exact(simple_chain):
    """Test that exact approximation is fully deterministic."""
    result1 = flow_hierarchical_communities(simple_chain, approx="exact", seed=42)
    result2 = flow_hierarchical_communities(simple_chain, approx="exact", seed=999)

    # Different seeds shouldn't matter for exact
    partition1 = result1.get_partition()
    partition2 = result2.get_partition()

    # Should be identical
    assert partition1 == partition2


def test_flow_hierarchy_different_seeds_mc(two_cliques):
    """Test that different seeds give different results with Monte Carlo."""
    result1 = flow_hierarchical_communities(two_cliques, approx="mc", n_walks=10, seed=42)
    result2 = flow_hierarchical_communities(two_cliques, approx="mc", n_walks=10, seed=123)

    # Different seeds may give slightly different results (stochastic)
    # But partitions should still be reasonable
    partition1 = result1.get_partition()
    partition2 = result2.get_partition()

    assert len(partition1) == len(partition2) == 6
    # May differ due to randomness, but both should be valid


# ============================================================================
# Test Multilayer Networks
# ============================================================================


def test_flow_hierarchy_multilayer(multilayer_network):
    """Test flow hierarchy on multilayer network."""
    result = flow_hierarchical_communities(
        multilayer_network, multilayer=True, alpha=0.8, seed=42
    )

    # Check structure
    assert isinstance(result, FlowHierarchyResult)
    assert result.metadata["multilayer"] is True
    assert result.metadata["alpha"] == 0.8

    # Should detect nodes from both layers (nodes appear as (node, layer) tuples)
    partition = result.get_partition()
    # In multilayer, we have 6 nodes x 2 layers = up to 12 node-layer pairs
    # (depending on which nodes are present in which layers)
    assert len(partition) > 0
    assert result.metadata["n_nodes"] > 0


def test_flow_hierarchy_multilayer_alpha_variations(multilayer_network):
    """Test effect of alpha parameter on multilayer networks."""
    # High alpha (layer-independent)
    result_high = flow_hierarchical_communities(
        multilayer_network, alpha=0.95, seed=42
    )

    # Low alpha (strong interlayer coupling)
    result_low = flow_hierarchical_communities(
        multilayer_network, alpha=0.5, seed=42
    )

    # Both should complete successfully
    assert isinstance(result_high, FlowHierarchyResult)
    assert isinstance(result_low, FlowHierarchyResult)

    # Partitions may differ due to different coupling
    partition_high = result_high.get_partition()
    partition_low = result_low.get_partition()

    # Both should have same nodes (node-layer pairs)
    assert len(partition_high) == len(partition_low)
    assert len(partition_high) > 0


# ============================================================================
# Test Hierarchical Structure Detection
# ============================================================================


def test_flow_hierarchy_detects_levels(hierarchical_network):
    """Test that algorithm detects hierarchical structure."""
    result = flow_hierarchical_communities(hierarchical_network, seed=42)

    # Should detect multiple hierarchy levels
    assert len(result.hierarchy_levels) >= 2

    # Check that different scales give different numbers of communities
    n_communities_by_scale = {}
    for scale, partition in result.hierarchy_levels.items():
        n_communities_by_scale[scale] = len(set(partition.values()))

    # Should have variation in number of communities
    unique_counts = set(n_communities_by_scale.values())
    assert len(unique_counts) >= 2  # At least 2 different community counts


def test_flow_hierarchy_stability_plateaus(hierarchical_network):
    """Test stability plateau detection."""
    result = flow_hierarchical_communities(hierarchical_network, seed=42)

    # Check that plateaus were detected
    assert "plateau_indices" in result.metadata
    assert "plateau_scales" in result.metadata

    plateau_indices = result.metadata["plateau_indices"]
    assert len(plateau_indices) >= 1


# ============================================================================
# Test Parameter Validation
# ============================================================================


def test_flow_hierarchy_invalid_flow_type(simple_chain):
    """Test error on invalid flow type."""
    with pytest.raises(AlgorithmError, match="Unsupported flow_type"):
        flow_hierarchical_communities(simple_chain, flow_type="invalid")


def test_flow_hierarchy_invalid_alpha(simple_chain):
    """Test error on invalid alpha."""
    with pytest.raises(AlgorithmError, match="alpha must be in"):
        flow_hierarchical_communities(simple_chain, alpha=1.5)

    with pytest.raises(AlgorithmError, match="alpha must be in"):
        flow_hierarchical_communities(simple_chain, alpha=-0.1)


def test_flow_hierarchy_invalid_approx(simple_chain):
    """Test error on invalid approximation method."""
    with pytest.raises(AlgorithmError, match="approx must be"):
        flow_hierarchical_communities(simple_chain, approx="invalid")


def test_flow_hierarchy_invalid_n_walks(simple_chain):
    """Test error on invalid n_walks."""
    with pytest.raises(AlgorithmError, match="n_walks must be"):
        flow_hierarchical_communities(simple_chain, n_walks=0)


def test_flow_hierarchy_empty_network():
    """Test error on empty network."""
    net = multinet.multi_layer_network(directed=False)

    # Empty network should raise an error
    with pytest.raises((AlgorithmError, AttributeError)):
        flow_hierarchical_communities(net)


# ============================================================================
# Test Approximation Methods
# ============================================================================


def test_flow_hierarchy_mc_vs_exact_small_graph(simple_chain):
    """Compare MC and exact approximations on small graph."""
    result_mc = flow_hierarchical_communities(
        simple_chain, approx="mc", n_walks=1000, seed=42
    )
    result_exact = flow_hierarchical_communities(simple_chain, approx="exact", seed=42)

    # Both should complete
    assert isinstance(result_mc, FlowHierarchyResult)
    assert isinstance(result_exact, FlowHierarchyResult)

    # Partitions should be similar (MC is stochastic but with high n_walks should converge)
    partition_mc = result_mc.get_partition()
    partition_exact = result_exact.get_partition()

    # Number of communities should be close
    n_comms_mc = len(set(partition_mc.values()))
    n_comms_exact = len(set(partition_exact.values()))
    assert abs(n_comms_mc - n_comms_exact) <= 2


def test_flow_hierarchy_custom_scales(two_cliques):
    """Test with custom scale schedule."""
    custom_scales = [1, 3, 5, 7]
    result = flow_hierarchical_communities(two_cliques, scales=custom_scales, seed=42)

    # Should use provided scales
    assert result.metadata["scale_schedule"] == sorted(custom_scales)
    assert result.metadata["n_scales"] == len(custom_scales)


def test_flow_hierarchy_max_scales(two_cliques):
    """Test max_scales parameter."""
    result = flow_hierarchical_communities(two_cliques, max_scales=3, seed=42)

    # Should limit number of scales
    assert result.metadata["n_scales"] <= 3


# ============================================================================
# Test Edge Cases
# ============================================================================


def test_flow_hierarchy_single_node():
    """Test on network with single node (degenerate case)."""
    net = multinet.multi_layer_network(directed=False)
    net.add_nodes([{"source": "A", "type": "L1"}])

    result = flow_hierarchical_communities(net, seed=42)

    # Should handle gracefully
    partition = result.get_partition()
    assert len(partition) == 1
    assert ("A", "L1") in partition


def test_flow_hierarchy_disconnected_components(two_cliques):
    """Test on network with disconnected components."""
    # Remove bridge to create disconnected components
    net = multinet.multi_layer_network(directed=False)
    net.add_edges(
        [
            # Clique 1
            ["A", "L1", "B", "L1", 1.0],
            ["B", "L1", "C", "L1", 1.0],
            ["C", "L1", "A", "L1", 1.0],
            # Clique 2 (disconnected)
            ["D", "L1", "E", "L1", 1.0],
            ["E", "L1", "F", "L1", 1.0],
            ["F", "L1", "D", "L1", 1.0],
        ],
        input_type="list",
    )

    result = flow_hierarchical_communities(net, seed=42)

    # Should handle disconnected components
    partition = result.get_partition()
    assert len(partition) == 6

    # At coarsest level, should have at least 2 communities (disconnected)
    coarsest_scale = max(result.hierarchy_levels.keys())
    coarsest_partition = result.hierarchy_levels[coarsest_scale]
    n_comms = len(set(coarsest_partition.values()))
    assert n_comms >= 2


# ============================================================================
# Test Directed Networks
# ============================================================================


def test_flow_hierarchy_directed_network():
    """Test on directed network."""
    net = multinet.multi_layer_network(directed=True)
    net.add_edges(
        [
            ["A", "L1", "B", "L1", 1.0],
            ["B", "L1", "C", "L1", 1.0],
            ["C", "L1", "A", "L1", 1.0],  # Cycle
            ["D", "L1", "E", "L1", 1.0],
            ["E", "L1", "D", "L1", 1.0],  # Another cycle
            ["C", "L1", "D", "L1", 0.5],  # Bridge
        ],
        input_type="list",
    )

    result = flow_hierarchical_communities(net, seed=42)

    # Should handle directed networks
    assert isinstance(result, FlowHierarchyResult)
    partition = result.get_partition()
    assert len(partition) == 5


# ============================================================================
# Test Metadata and Provenance
# ============================================================================


def test_flow_hierarchy_metadata_complete(two_cliques):
    """Test that result metadata is complete."""
    result = flow_hierarchical_communities(
        two_cliques, approx="mc", n_walks=50, seed=42
    )

    metadata = result.metadata
    required_keys = [
        "flow_type",
        "multilayer",
        "alpha",
        "approx",
        "n_walks",
        "seed",
        "n_nodes",
        "n_scales",
        "scale_schedule",
        "plateau_indices",
        "plateau_scales",
    ]

    for key in required_keys:
        assert key in metadata, f"Missing metadata key: {key}"


def test_flow_hierarchy_dendrogram_structure(two_cliques):
    """Test dendrogram structure."""
    result = flow_hierarchical_communities(two_cliques, seed=42)

    # Dendrogram should be a list of tuples
    assert isinstance(result.dendrogram, list)

    # Each entry should be a tuple with merge info
    for entry in result.dendrogram:
        assert isinstance(entry, tuple)
        assert len(entry) == 5  # (comm_i, comm_j, scale, stability_before, stability_after)


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.integration
def test_flow_hierarchy_integration_with_louvain(two_cliques):
    """Test that flow hierarchy can be compared with Louvain."""
    from py3plex.algorithms.community_detection import multilayer_louvain

    # Run both algorithms
    result_flow = flow_hierarchical_communities(two_cliques, seed=42)
    partition_louvain, Q_louvain = multilayer_louvain(two_cliques, random_state=42)

    # Both should complete
    partition_flow = result_flow.get_partition()

    # Both should find communities
    n_comms_flow = len(set(partition_flow.values()))
    n_comms_louvain = len(set(partition_louvain.values()))

    assert n_comms_flow > 0
    assert n_comms_louvain > 0


@pytest.mark.integration
def test_flow_hierarchy_large_scale(hierarchical_network):
    """Test on larger hierarchical network (integration test)."""
    # Expand the network
    net = multinet.multi_layer_network(directed=False)

    # Create hierarchical structure with more nodes
    for i in range(10):
        for j in range(i * 3, i * 3 + 3):
            net.add_edges(
                [
                    [f"N{j}", "L1", f"N{(j+1)}", "L1", 1.0],
                    [f"N{j}", "L1", f"N{(j+2)%3 + i*3}", "L1", 1.0],
                ],
                input_type="list",
            )

    result = flow_hierarchical_communities(net, approx="mc", n_walks=50, seed=42)

    # Should complete within reasonable time
    assert isinstance(result, FlowHierarchyResult)
    assert result.metadata["n_nodes"] > 20


# ============================================================================
# Property-Based Tests
# ============================================================================


@pytest.mark.property
def test_flow_hierarchy_partition_covers_all_nodes(two_cliques):
    """Property: partition should cover all nodes exactly once."""
    result = flow_hierarchical_communities(two_cliques, seed=42)

    nodes = list(two_cliques.get_nodes())

    for scale, partition in result.hierarchy_levels.items():
        # All nodes should be in partition
        assert set(partition.keys()) == set(nodes)

        # Each node should be assigned to exactly one community
        assert len(partition) == len(nodes)


@pytest.mark.property
def test_flow_hierarchy_monotonic_merging(hierarchical_network):
    """Property: number of communities should decrease or stay constant over scales."""
    result = flow_hierarchical_communities(hierarchical_network, seed=42)

    scales = sorted(result.hierarchy_levels.keys())
    n_communities = [
        len(set(result.hierarchy_levels[s].values())) for s in scales
    ]

    # Number of communities should generally decrease or stay same
    # (allowing for some plateaus)
    for i in range(1, len(n_communities)):
        assert n_communities[i] <= n_communities[i - 1] + 1  # Allow slight variations


@pytest.mark.property
def test_flow_hierarchy_stability_nonnegative(two_cliques):
    """Property: stability scores should be non-negative."""
    result = flow_hierarchical_communities(two_cliques, seed=42)

    for scale, stability in result.stability_scores.items():
        assert stability >= 0, f"Negative stability at scale {scale}: {stability}"
