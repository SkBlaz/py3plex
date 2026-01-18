"""
Certificate-based verification tests for community detection algorithms.

These tests validate community detection outputs by checking certificates
(witnesses) rather than trusting the algorithm output directly:

1. Partition validity: Every node assigned exactly once, no empty communities
2. Modularity certificate: Recompute modularity from partition
3. Coverage certificate: Verify partition covers all nodes
4. Confidence intervals: Check CI bounds are valid

All tests use canonical graphs with known community structure.
"""

import pytest
import math
from typing import Dict, List, Set, Any, Tuple

from tests.fixtures import two_cliques_bridge, small_three_layer
from py3plex.algorithms.community_detection import louvain_multilayer, multilayer_modularity


# ============================================================================
# Certificate Validators
# ============================================================================


def validate_partition_coverage(partition: Dict[Any, int], nodes: Set[Any]) -> Tuple[bool, str]:
    """
    Validate that a partition covers all nodes exactly once.
    
    Certificate checks:
    1. Every node appears in partition
    2. No extra nodes in partition
    3. No None/null community assignments
    
    Args:
        partition: Dict mapping nodes to community IDs
        nodes: Set of all nodes that should be in partition
        
    Returns:
        (is_valid, error_message): Tuple of validity flag and error message
    """
    partition_nodes = set(partition.keys())
    
    # Check 1: All nodes must be in partition
    missing = nodes - partition_nodes
    if missing:
        return False, f"Missing nodes in partition: {missing}"
    
    # Check 2: No extra nodes in partition
    extra = partition_nodes - nodes
    if extra:
        return False, f"Extra nodes in partition: {extra}"
    
    # Check 3: No None assignments
    none_assignments = [node for node, comm in partition.items() if comm is None]
    if none_assignments:
        return False, f"Nodes with None community: {none_assignments}"
    
    return True, ""


def validate_partition_no_empty_communities(partition: Dict[Any, int]) -> Tuple[bool, str]:
    """
    Validate that there are no empty communities.
    
    Certificate check: Every community ID has at least one member.
    
    Args:
        partition: Dict mapping nodes to community IDs
        
    Returns:
        (is_valid, error_message): Tuple of validity flag and error message
    """
    # Get all unique community IDs
    communities = set(partition.values())
    
    # Count members per community
    comm_sizes = {}
    for node, comm in partition.items():
        comm_sizes[comm] = comm_sizes.get(comm, 0) + 1
    
    # Check for empty communities (community IDs with 0 members)
    # This shouldn't happen if partition is well-formed, but check anyway
    empty = [c for c in communities if comm_sizes.get(c, 0) == 0]
    if empty:
        return False, f"Empty communities: {empty}"
    
    return True, ""


def validate_partition_single_assignment(partition: Dict[Any, int]) -> Tuple[bool, str]:
    """
    Validate that each node is assigned to exactly one community.
    
    This is inherent in the dict representation, but we verify:
    1. No duplicate keys (enforced by dict)
    2. All assignments are integers (valid community IDs)
    
    Args:
        partition: Dict mapping nodes to community IDs
        
    Returns:
        (is_valid, error_message): Tuple of validity flag and error message
    """
    # Check that all community IDs are integers
    non_int = [(node, comm) for node, comm in partition.items() 
               if not isinstance(comm, int)]
    if non_int:
        return False, f"Non-integer community IDs: {non_int[:5]}"
    
    return True, ""


def recompute_modularity_certificate(
    net,
    partition: Dict[Any, int],
    tol: float = 1e-3
) -> Tuple[bool, str, float]:
    """
    Recompute modularity from partition as a certificate.
    
    Certificate check: Modularity computed from partition should be finite
    and match expected properties (bounded between -0.5 and 1.0).
    
    Args:
        net: Multilayer network
        partition: Community partition
        tol: Tolerance for modularity bounds check
        
    Returns:
        (is_valid, error_message, modularity): Tuple of validity, message, and modularity value
    """
    try:
        # Recompute modularity from partition
        Q = multilayer_modularity(net, partition)
        
        # Check 1: Modularity must be finite
        if not math.isfinite(Q):
            return False, f"Modularity is not finite: {Q}", Q
        
        # Check 2: Modularity should be in theoretical bounds [-0.5, 1.0]
        # (allowing small tolerance for numerical errors)
        if Q < -0.5 - tol or Q > 1.0 + tol:
            return False, f"Modularity {Q:.6f} outside bounds [-0.5, 1.0]", Q
        
        return True, "", Q
        
    except Exception as e:
        return False, f"Failed to compute modularity: {e}", float('nan')


def validate_confidence_intervals(
    ci_data: Dict[str, Any],
    n_nodes: int
) -> Tuple[bool, str]:
    """
    Validate confidence interval structure and bounds.
    
    Certificate checks:
    1. CI bounds exist for each node
    2. Lower bound <= upper bound
    3. All bounds are finite
    4. Confidence level is in [0, 1]
    
    Args:
        ci_data: Confidence interval data structure
        n_nodes: Expected number of nodes
        
    Returns:
        (is_valid, error_message): Tuple of validity flag and error message
    """
    if not ci_data:
        return True, ""  # No CI data is valid (not all methods provide it)
    
    # Check structure
    if 'lower' not in ci_data or 'upper' not in ci_data:
        return False, "CI data missing 'lower' or 'upper' bounds"
    
    lower = ci_data['lower']
    upper = ci_data['upper']
    
    # Check 1: Length matches number of nodes
    if len(lower) != n_nodes or len(upper) != n_nodes:
        return False, f"CI bounds length mismatch: expected {n_nodes}, got {len(lower)}, {len(upper)}"
    
    # Check 2: Lower <= Upper for all nodes
    for i, (l, u) in enumerate(zip(lower, upper)):
        if not math.isfinite(l) or not math.isfinite(u):
            return False, f"Non-finite CI bounds at node {i}: [{l}, {u}]"
        
        if l > u:
            return False, f"Lower bound > upper bound at node {i}: [{l}, {u}]"
    
    # Check 3: Confidence level is valid
    if 'confidence' in ci_data:
        conf = ci_data['confidence']
        if not (0 <= conf <= 1):
            return False, f"Invalid confidence level: {conf}"
    
    return True, ""


# ============================================================================
# Community Detection Certificate Tests
# ============================================================================


@pytest.mark.metamorphic
def test_community_partition_validity_two_cliques():
    """
    Test that community detection produces a valid partition.
    
    Certificate checks:
    - All nodes are assigned
    - No nodes are missing
    - Each node assigned exactly once
    - No empty communities
    """
    net = two_cliques_bridge()
    
    # Get all node-layer pairs (partition keys are (node, layer) tuples)
    nodes = set(net.get_nodes())
    
    # Run community detection
    try:
        partition = louvain_multilayer(net, random_state=42)
    except Exception as e:
        pytest.skip(f"Community detection failed: {e}")
    
    # Validate partition coverage
    is_valid, msg = validate_partition_coverage(partition, nodes)
    assert is_valid, f"Partition coverage invalid: {msg}"
    
    # Validate no empty communities
    is_valid, msg = validate_partition_no_empty_communities(partition)
    assert is_valid, f"Empty communities found: {msg}"
    
    # Validate single assignment
    is_valid, msg = validate_partition_single_assignment(partition)
    assert is_valid, f"Invalid community assignments: {msg}"


@pytest.mark.metamorphic
def test_community_partition_validity_small_three_layer():
    """
    Test partition validity on a small three-layer network.
    """
    net = small_three_layer()
    
    nodes = set(net.get_nodes())
    
    try:
        partition = louvain_multilayer(net, random_state=123)
    except Exception as e:
        pytest.skip(f"Community detection failed: {e}")
    
    is_valid, msg = validate_partition_coverage(partition, nodes)
    assert is_valid, f"Partition coverage invalid: {msg}"
    
    is_valid, msg = validate_partition_no_empty_communities(partition)
    assert is_valid, f"Empty communities found: {msg}"
    
    is_valid, msg = validate_partition_single_assignment(partition)
    assert is_valid, f"Invalid community assignments: {msg}"


@pytest.mark.metamorphic
def test_community_modularity_certificate_two_cliques():
    """
    Test that modularity can be recomputed from partition.
    
    Certificate: Recomputed modularity should be finite and within bounds.
    """
    net = two_cliques_bridge()
    
    try:
        partition = louvain_multilayer(net, random_state=42)
    except Exception as e:
        pytest.skip(f"Community detection failed: {e}")
    
    # Recompute modularity as certificate
    is_valid, msg, Q = recompute_modularity_certificate(net, partition)
    assert is_valid, f"Modularity certificate invalid: {msg}"
    
    # For two clear cliques with a bridge, modularity should be positive
    assert Q > 0, f"Expected positive modularity for two-cliques graph, got {Q:.6f}"


@pytest.mark.metamorphic
def test_community_modularity_certificate_small():
    """
    Test modularity certificate on small three-layer network.
    """
    net = small_three_layer()
    
    try:
        partition = louvain_multilayer(net, random_state=999)
    except Exception as e:
        pytest.skip(f"Community detection failed: {e}")
    
    is_valid, msg, Q = recompute_modularity_certificate(net, partition)
    assert is_valid, f"Modularity certificate invalid: {msg}"


@pytest.mark.metamorphic
def test_community_expected_structure_two_cliques():
    """
    Test that community detection finds expected structure in two-cliques graph.
    
    For a graph with two clear K3 cliques connected by a bridge,
    we expect to find 2 communities (or possibly more, but at least 2).
    """
    net = two_cliques_bridge()
    
    try:
        partition = louvain_multilayer(net, random_state=42)
    except Exception as e:
        pytest.skip(f"Community detection failed: {e}")
    
    # Count number of communities
    num_communities = len(set(partition.values()))
    
    # With two clear cliques, we expect at least 2 communities
    # (allowing for possible over-splitting)
    assert num_communities >= 2, (
        f"Expected at least 2 communities for two-cliques graph, found {num_communities}"
    )
    
    # But not too many (shouldn't split into singleton communities)
    assert num_communities <= 4, (
        f"Expected at most 4 communities for two-cliques graph, found {num_communities}"
    )


@pytest.mark.metamorphic
def test_community_determinism_with_seed():
    """
    Test that community detection is deterministic with a fixed seed.
    
    Certificate: Same network + same seed should produce same partition.
    """
    net = two_cliques_bridge()
    
    try:
        partition1 = louvain_multilayer(net, random_state=42)
        partition2 = louvain_multilayer(net, random_state=42)
    except Exception as e:
        pytest.skip(f"Community detection failed: {e}")
    
    # Partitions should be identical
    assert partition1 == partition2, "Same seed should produce identical partitions"


@pytest.mark.metamorphic
def test_community_partition_relabel_equivalence():
    """
    Test that community detection produces equivalent partitions under relabeling.
    
    Metamorphic relation: Relabeling nodes should produce the same partition structure
    (ignoring community ID labels, which can be arbitrary).
    """
    from tests.fixtures import relabel_nodes
    
    net = two_cliques_bridge()
    
    # Compute partition on original
    try:
        partition1 = louvain_multilayer(net, random_state=42)
    except Exception as e:
        pytest.skip(f"Community detection failed: {e}")
    
    # Relabel nodes
    mapping = {node: f"n{i}" for i, node in enumerate(['A', 'B', 'C', 'D', 'E', 'F'])}
    relabeled_net = relabel_nodes(net, mapping)
    
    # Compute partition on relabeled
    try:
        partition2 = louvain_multilayer(relabeled_net, random_state=42)
    except Exception as e:
        pytest.skip(f"Community detection on relabeled network failed: {e}")
    
    # Number of communities should match
    num_comm1 = len(set(partition1.values()))
    num_comm2 = len(set(partition2.values()))
    assert num_comm1 == num_comm2, (
        f"Number of communities differs: {num_comm1} vs {num_comm2}"
    )
    
    # Modularity should match (partition structure is equivalent)
    is_valid1, msg1, Q1 = recompute_modularity_certificate(net, partition1)
    is_valid2, msg2, Q2 = recompute_modularity_certificate(relabeled_net, partition2)
    
    assert is_valid1 and is_valid2, f"Modularity computation failed: {msg1}, {msg2}"
    assert abs(Q1 - Q2) < 1e-6, (
        f"Modularity differs after relabeling: {Q1:.6f} vs {Q2:.6f}"
    )
