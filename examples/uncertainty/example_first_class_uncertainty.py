"""
Example: First-Class Uncertainty in py3plex

This example demonstrates the new first-class uncertainty support in py3plex.
The key idea is that statistics now return StatSeries objects that can carry
uncertainty information (mean, std, quantiles), making uncertainty "native"
rather than an add-on.
"""

import numpy as np
from py3plex.core import multinet
from py3plex.algorithms.centrality_toolkit import multilayer_pagerank
from py3plex.uncertainty import (
    StatSeries,
    uncertainty_enabled,
    ResamplingStrategy,
)


def create_example_network():
    """Create a simple multilayer network for demonstration."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    
    # Add edges to create a simple structure
    edges = [
        # Layer 0: Triangle
        ["A", "L0", "B", "L0", 1.0],
        ["B", "L0", "C", "L0", 1.0],
        ["C", "L0", "A", "L0", 1.0],
        # Layer 1: Chain
        ["A", "L1", "B", "L1", 1.0],
        ["B", "L1", "C", "L1", 1.0],
        # Inter-layer connections
        ["A", "L0", "A", "L1", 1.0],
        ["B", "L0", "B", "L1", 1.0],
        ["C", "L0", "C", "L1", 1.0],
    ]
    net.add_edges(edges, input_type="list")
    
    return net


def example_1_deterministic():
    """Example 1: Deterministic computation (default behavior)."""
    print("\n" + "="*70)
    print("Example 1: Deterministic PageRank")
    print("="*70)
    
    net = create_example_network()
    
    # Compute PageRank without uncertainty
    result = multilayer_pagerank(net, uncertainty=False)
    
    print(f"\nResult type: {type(result).__name__}")
    print(f"Is deterministic: {result.is_deterministic}")
    print(f"Certainty: {result.certainty}")
    print(f"\nNumber of nodes: {len(result)}")
    
    # Access values in different ways
    print("\n--- Accessing values ---")
    print(f"As array (backward compat): {np.array(result)[:3]}...")
    
    if len(result.index) > 0:
        node = result.index[0]
        print(f"Dict-like access for node {node}: {result[node]}")
    
    print("\nTop 3 nodes by PageRank:")
    sorted_indices = np.argsort(result.mean)[::-1][:3]
    for i in sorted_indices:
        node = result.index[i]
        score = result.mean[i]
        print(f"  {node}: {score:.4f}")


def example_2_uncertainty():
    """Example 2: Uncertainty estimation via perturbations."""
    print("\n" + "="*70)
    print("Example 2: PageRank with Uncertainty")
    print("="*70)
    
    net = create_example_network()
    
    # Compute PageRank with uncertainty
    result = multilayer_pagerank(
        net,
        uncertainty=True,
        n_runs=30,
        resampling=ResamplingStrategy.PERTURBATION,
        random_seed=42
    )
    
    print(f"\nResult type: {type(result).__name__}")
    print(f"Is deterministic: {result.is_deterministic}")
    print(f"Certainty: {result.certainty}")
    
    print("\n--- Uncertainty information ---")
    print(f"Has std: {result.std is not None}")
    print(f"Has quantiles: {result.quantiles is not None}")
    print(f"Number of samples: {result.meta.get('n_samples')}")
    
    # Show values with uncertainty
    print("\nTop 3 nodes with confidence intervals:")
    sorted_indices = np.argsort(result.mean)[::-1][:3]
    for i in sorted_indices:
        node = result.index[i]
        mean = result.mean[i]
        std = result.std[i] if result.std is not None else 0
        ci_low = result.quantiles[0.025][i] if result.quantiles else mean
        ci_high = result.quantiles[0.975][i] if result.quantiles else mean
        
        print(f"  {node}:")
        print(f"    Mean: {mean:.4f}")
        print(f"    Std:  {std:.4f}")
        print(f"    95% CI: [{ci_low:.4f}, {ci_high:.4f}]")


def example_3_context_manager():
    """Example 3: Using uncertainty_enabled context manager."""
    print("\n" + "="*70)
    print("Example 3: Global Uncertainty Context")
    print("="*70)
    
    net = create_example_network()
    
    # Without context: deterministic
    result_default = multilayer_pagerank(net)
    print(f"\nDefault mode:")
    print(f"  Is deterministic: {result_default.is_deterministic}")
    
    # With context: all computations have uncertainty
    with uncertainty_enabled(n_runs=20):
        result_uncertain = multilayer_pagerank(
            net,
            resampling=ResamplingStrategy.PERTURBATION
        )
        
        print(f"\nWith uncertainty_enabled context:")
        print(f"  Is deterministic: {result_uncertain.is_deterministic}")
        print(f"  Has std: {result_uncertain.std is not None}")
    
    # After context: back to deterministic
    result_after = multilayer_pagerank(net)
    print(f"\nAfter context:")
    print(f"  Is deterministic: {result_after.is_deterministic}")


def example_4_to_dict():
    """Example 4: Converting to dictionary for serialization."""
    print("\n" + "="*70)
    print("Example 4: Converting to Dictionary")
    print("="*70)
    
    net = create_example_network()
    
    result = multilayer_pagerank(
        net,
        uncertainty=True,
        n_runs=10,
        resampling=ResamplingStrategy.PERTURBATION,
        random_seed=42
    )
    
    # Convert to dictionary
    result_dict = result.to_dict()
    
    print(f"\nResult as dictionary (first 2 nodes):")
    for i, (node, stats) in enumerate(result_dict.items()):
        if i >= 2:
            break
        print(f"\n  {node}:")
        for key, value in stats.items():
            if key == 'quantiles':
                print(f"    {key}:")
                for q, v in value.items():
                    print(f"      {q}: {v:.4f}")
            else:
                print(f"    {key}: {value:.4f}")


def example_5_comparison():
    """Example 5: Comparing deterministic and uncertain results."""
    print("\n" + "="*70)
    print("Example 5: Deterministic vs Uncertain Results")
    print("="*70)
    
    net = create_example_network()
    
    # Deterministic
    result_det = multilayer_pagerank(net, uncertainty=False)
    
    # With uncertainty
    result_unc = multilayer_pagerank(
        net,
        uncertainty=True,
        n_runs=50,
        resampling=ResamplingStrategy.PERTURBATION,
        random_seed=42
    )
    
    print("\nComparison (first 3 nodes):")
    print(f"{'Node':<15} {'Deterministic':<15} {'Mean±Std':<20}")
    print("-" * 50)
    
    for i in range(min(3, len(result_det))):
        node = result_det.index[i]
        det_val = result_det.mean[i]
        
        # Find corresponding node in uncertain result
        if node in result_unc.index:
            unc_idx = result_unc.index.index(node)
            mean_val = result_unc.mean[unc_idx]
            std_val = result_unc.std[unc_idx] if result_unc.std is not None else 0
            print(f"{str(node):<15} {det_val:<15.4f} {mean_val:.4f}±{std_val:.4f}")


def main():
    """Run all examples."""
    print("\n" + "#"*70)
    print("# First-Class Uncertainty Examples")
    print("#"*70)
    
    example_1_deterministic()
    example_2_uncertainty()
    example_3_context_manager()
    example_4_to_dict()
    example_5_comparison()
    
    print("\n" + "#"*70)
    print("# All examples completed successfully!")
    print("#"*70 + "\n")


if __name__ == "__main__":
    main()
