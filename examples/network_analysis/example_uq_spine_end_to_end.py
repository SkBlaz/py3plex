"""End-to-end demonstration of UQ spine and PartitionUQ.

This example demonstrates the complete uncertainty quantification pipeline:
1. Direct UQ spine usage
2. DSL integration with .community().uq()
3. Accessing and interpreting UQ results
"""

from py3plex.core import multinet
from py3plex.dsl import Q
from py3plex.uncertainty import (
    UQPlan,
    run_uq,
    NoNoise,
    EdgeDrop,
    PartitionOutput,
    NodeMarginalReducer,
    PartitionUQ,
)


def create_test_network():
    """Create a test network with clear community structure."""
    net = multinet.multi_layer_network(directed=False)
    
    # Community 1: Alice, Bob, Charlie
    # Community 2: David, Eve, Frank
    nodes = [
        {'source': 'Alice', 'type': 'social'},
        {'source': 'Bob', 'type': 'social'},
        {'source': 'Charlie', 'type': 'social'},
        {'source': 'David', 'type': 'social'},
        {'source': 'Eve', 'type': 'social'},
        {'source': 'Frank', 'type': 'social'},
    ]
    net.add_nodes(nodes)
    
    # Strong intra-community edges
    edges = [
        # Community 1
        {'source': 'Alice', 'target': 'Bob', 
         'source_type': 'social', 'target_type': 'social'},
        {'source': 'Alice', 'target': 'Charlie', 
         'source_type': 'social', 'target_type': 'social'},
        {'source': 'Bob', 'target': 'Charlie', 
         'source_type': 'social', 'target_type': 'social'},
        # Community 2
        {'source': 'David', 'target': 'Eve', 
         'source_type': 'social', 'target_type': 'social'},
        {'source': 'David', 'target': 'Frank', 
         'source_type': 'social', 'target_type': 'social'},
        {'source': 'Eve', 'target': 'Frank', 
         'source_type': 'social', 'target_type': 'social'},
        # Weak bridge
        {'source': 'Charlie', 'target': 'David', 
         'source_type': 'social', 'target_type': 'social'},
    ]
    net.add_edges(edges)
    
    return net


def simple_community_detection(network, rng):
    """Simple community detection for demonstration.
    
    In practice, use real algorithms like Leiden or Louvain.
    This assigns nodes based on lexicographic ordering for testing.
    """
    nodes = sorted(network.get_nodes())
    n = len(nodes)
    
    # Simple assignment: first half to community 0, second half to community 1
    labels = {}
    for i, node in enumerate(nodes):
        labels[node] = 0 if i < n // 2 else 1
    
    return PartitionOutput(labels=labels)


# ============================================================================
# Example 1: Direct UQ Spine Usage
# ============================================================================

print("=" * 80)
print("EXAMPLE 1: Direct UQ Spine Usage")
print("=" * 80)
print()

net = create_test_network()
node_ids = sorted(net.get_nodes())
n_nodes = len(node_ids)

print(f"Network: {n_nodes} nodes")
print()

# Create UQ plan
marginal_reducer = NodeMarginalReducer(n_nodes=n_nodes, node_ids=node_ids)

plan = UQPlan(
    base_callable=simple_community_detection,
    strategy="seed",
    noise_model=NoNoise(),
    n_samples=20,
    seed=42,
    reducers=[marginal_reducer],
    storage_mode="sketch",
    backend="python"
)

print("Executing UQ plan...")
uq_result = run_uq(plan, net)

print(f"✓ Executed {uq_result.n_samples} samples")
print(f"✓ Reducers: {list(uq_result.reducer_outputs.keys())}")
print()

# Create PartitionUQ from result
partition_uq = PartitionUQ.from_uq_result(uq_result, node_ids)

print("PartitionUQ Results:")
print(f"  Communities: {partition_uq.n_communities}")
print(f"  Storage mode: {partition_uq.store_mode}")
print()

print("Node-level statistics:")
for i, node_id in enumerate(node_ids):
    print(f"  {str(node_id):20s}: "
          f"community={partition_uq.consensus_partition[i]}, "
          f"entropy={partition_uq.membership_entropy[i]:.3f}, "
          f"confidence={partition_uq.p_max_membership[i]:.3f}")
print()

print("Stability metrics:")
print(f"  VI:  {partition_uq.vi_mean:.3f} ± {partition_uq.vi_std:.3f}")
print(f"  NMI: {partition_uq.nmi_mean:.3f} ± {partition_uq.nmi_std:.3f}")
print()


# ============================================================================
# Example 2: DSL Integration
# ============================================================================

print("=" * 80)
print("EXAMPLE 2: DSL Integration with .community().uq()")
print("=" * 80)
print()

# Note: This example uses a simple mock. In real usage, use Leiden/Louvain.
print("DSL Query:")
print("  Q.nodes()")
print("   .community(method='leiden')")
print("   .uq(method='seed', n_samples=20, seed=42)")
print("   .execute(net)")
print()

# For testing, we'll use the execute_community_with_uq function directly
# In real usage, the DSL executor handles this automatically
from py3plex.dsl.community_uq import execute_community_with_uq

consensus, partition_uq_dsl = execute_community_with_uq(
    network=net,
    method="leiden",
    uq_method="seed",
    n_samples=20,
    seed=42,
    store="sketch",
    progress=False,
    gamma=1.0,
    omega=1.0,
)

print("DSL Result:")
print(f"  Communities: {partition_uq_dsl.n_communities}")
print(f"  Consensus partition: {len(consensus)} nodes")
print()

print("Boundary nodes (high uncertainty):")
boundary = partition_uq_dsl.boundary_nodes(threshold=0.5, metric="confidence")
if boundary:
    for node in boundary[:5]:  # Show first 5
        idx = partition_uq_dsl.node_ids.index(node)
        print(f"  {node}: confidence={partition_uq_dsl.p_max_membership[idx]:.3f}")
else:
    print("  (none - all nodes have high confidence)")
print()


# ============================================================================
# Example 3: Perturbation-Based UQ
# ============================================================================

print("=" * 80)
print("EXAMPLE 3: Perturbation-Based UQ with EdgeDrop")
print("=" * 80)
print()

# Create plan with edge dropping
marginal_reducer_pert = NodeMarginalReducer(n_nodes=n_nodes, node_ids=node_ids)

plan_pert = UQPlan(
    base_callable=simple_community_detection,
    strategy="perturbation",
    noise_model=EdgeDrop(p=0.2),  # Drop 20% of edges
    n_samples=30,
    seed=42,
    reducers=[marginal_reducer_pert],
    storage_mode="sketch"
)

print("Executing UQ with EdgeDrop(p=0.2)...")
uq_result_pert = run_uq(plan_pert, net)

partition_uq_pert = PartitionUQ.from_uq_result(uq_result_pert, node_ids)

print(f"✓ Executed {partition_uq_pert.n_samples} samples with edge perturbations")
print()

print("Comparing seed vs perturbation uncertainty:")
print(f"  Seed UQ:         mean entropy = {partition_uq.membership_entropy.mean():.3f}")
print(f"  Perturbation UQ: mean entropy = {partition_uq_pert.membership_entropy.mean():.3f}")
print()

print("Provenance (from perturbation run):")
prov = partition_uq_pert.meta.get('provenance', {})
if 'randomness' in prov:
    rand_info = prov['randomness']
    print(f"  Strategy: {rand_info.get('strategy')}")
    print(f"  Seed: {rand_info.get('seed')}")
    print(f"  Noise model: {rand_info.get('noise_model')}")
print()


# ============================================================================
# Example 4: Summary and Interpretation
# ============================================================================

print("=" * 80)
print("SUMMARY: Interpreting UQ Results")
print("=" * 80)
print()

print("Key Metrics:")
print()

print("1. Node-level uncertainty:")
print("   - Entropy: H(node) = -Σ p_c log(p_c)")
print("     Higher entropy = node assignment is more uncertain")
print()

print("2. Node confidence:")
print("   - Confidence = max_c p(node, c)")
print("     Higher confidence = node consistently in same community")
print()

print("3. Stability metrics:")
print("   - VI (Variation of Information): distance between partitions")
print("     Lower VI = more stable partitions across samples")
print("   - NMI (Normalized Mutual Information): similarity")
print("     Higher NMI = more similar partitions across samples")
print()

print("Best Practices:")
print("  • Use seed UQ for algorithmic uncertainty (randomness in algorithm)")
print("  • Use perturbation UQ for structural uncertainty (network noise)")
print("  • Check boundary nodes for communities that may need refinement")
print("  • Compare VI/NMI across different parameter settings")
print()

print("=" * 80)
print("End of demonstration")
print("=" * 80)
