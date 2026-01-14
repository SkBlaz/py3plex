"""
Example: Using Stochastic Block Model (SBM) with AutoCommunity

This example demonstrates:
1. Direct SBM usage via runner
2. SBM integration with AutoCommunity
3. Model selection and UQ
"""

import numpy as np
from py3plex.core import multinet
from py3plex.algorithms.community_detection import AutoCommunity
from py3plex.algorithms.community_detection.runner import run_community_algorithm
from py3plex.algorithms.community_detection.budget import BudgetSpec


def create_example_network(n_nodes=50, seed=42):
    """Create a simple example network with community structure."""
    rng = np.random.RandomState(seed)
    
    net = multinet.multi_layer_network(directed=False)
    
    # Create two communities
    community_size = n_nodes // 2
    
    # Within-community edges (higher probability)
    for i in range(community_size):
        for j in range(i + 1, community_size):
            if rng.rand() < 0.3:
                net.add_edges([{
                    'source': i,
                    'target': j,
                    'source_type': 'social',
                    'target_type': 'social'
                }])
    
    for i in range(community_size, n_nodes):
        for j in range(i + 1, n_nodes):
            if rng.rand() < 0.3:
                net.add_edges([{
                    'source': i,
                    'target': j,
                    'source_type': 'social',
                    'target_type': 'social'
                }])
    
    # Between-community edges (lower probability)
    for i in range(community_size):
        for j in range(community_size, n_nodes):
            if rng.rand() < 0.05:
                net.add_edges([{
                    'source': i,
                    'target': j,
                    'source_type': 'social',
                    'target_type': 'social'
                }])
    
    return net


def example_1_direct_sbm():
    """Example 1: Direct SBM usage via runner."""
    print("=" * 70)
    print("Example 1: Direct DC-SBM usage")
    print("=" * 70)
    
    # Create network
    net = create_example_network(n_nodes=40)
    
    # Define budget
    budget = BudgetSpec(
        max_iter=100,      # EM iterations
        n_restarts=5,      # Random initializations
        uq_samples=None    # No UQ for this example
    )
    
    # Run DC-SBM with model selection
    result = run_community_algorithm(
        algorithm_id="dc_sbm",
        network=net,
        budget=budget,
        seed=42,
        K_range=[2, 3, 4, 5]  # Try these K values
    )
    
    # Access results
    print(f"\nResults:")
    print(f"  Selected K: {result.meta['K_selected']}")
    print(f"  Log-likelihood: {result.meta['log_likelihood']:.2f}")
    print(f"  MDL: {result.meta['mdl']:.2f}")
    print(f"  Converged: {result.meta['converged']}")
    print(f"  Iterations: {result.meta['n_iter']}")
    print(f"  Communities found: {len(set(result.partition.values()))}")
    print()


def example_2_sbm_with_uq():
    """Example 2: SBM with uncertainty quantification."""
    print("=" * 70)
    print("Example 2: DC-SBM with UQ")
    print("=" * 70)
    
    # Create network
    net = create_example_network(n_nodes=40)
    
    # Define budget with UQ
    budget = BudgetSpec(
        max_iter=50,
        n_restarts=2,
        uq_samples=10  # 10 bootstrap samples
    )
    
    # Run DC-SBM with UQ
    result = run_community_algorithm(
        algorithm_id="dc_sbm",
        network=net,
        budget=budget,
        seed=42,
        K_range=[2, 3, 4]
    )
    
    # Access results
    print(f"\nResults with UQ:")
    print(f"  Selected K: {result.meta['K_selected']}")
    print(f"  Log-likelihood: {result.meta['log_likelihood']:.2f} ± {result.meta['log_likelihood_std']:.2f}")
    print(f"  MDL: {result.meta['mdl']:.2f} ± {result.meta['mdl_std']:.2f}")
    print(f"  UQ samples: {result.meta['n_samples']}")
    print()


def example_3_autocommunity():
    """Example 3: SBM with AutoCommunity."""
    print("=" * 70)
    print("Example 3: AutoCommunity with SBM")
    print("=" * 70)
    
    # Create network
    net = create_example_network(n_nodes=40)
    
    # Run AutoCommunity with multiple algorithms
    result = (
        AutoCommunity()
        .candidates("louvain", "dc_sbm")
        .metrics("modularity")
        .seed(42)
        .execute(net)
    )
    
    # Access results
    print(f"\nAutoCommunity Results:")
    print(f"  Selected algorithm: {result.selected}")
    print(f"  Algorithms tested: {result.algorithms_tested}")
    print(f"  Communities found: {result.community_stats.n_communities}")
    print(f"  Coverage: {result.community_stats.coverage:.3f}")
    print()
    
    # Show evaluation matrix
    print("Evaluation matrix:")
    print(result.evaluation_matrix)
    print()


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("SBM (Stochastic Block Model) Examples")
    print("=" * 70 + "\n")
    
    # Run examples
    example_1_direct_sbm()
    example_2_sbm_with_uq()
    example_3_autocommunity()
    
    print("=" * 70)
    print("All examples completed successfully!")
    print("=" * 70)
