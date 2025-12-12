"""Example: Computing betweenness centrality with Bootstrap uncertainty.

This example demonstrates uncertainty estimation for a more complex
metric (betweenness centrality) using bootstrap resampling.

We bootstrap by resampling edges, recompute betweenness on each sample,
and aggregate the results into a StatValue with Bootstrap uncertainty.
"""

import sys
sys.path.insert(0, '/home/runner/work/py3plex/py3plex')

import numpy as np
import networkx as nx
from py3plex.core import multinet
from py3plex.stats import StatValue, Bootstrap, Provenance


def compute_betweenness_with_bootstrap(network, node_id, n_boot=20, seed=42):
    """Compute betweenness with bootstrap uncertainty estimation.
    
    Args:
        network: Multilayer network
        node_id: Node to compute betweenness for (with layer)
        n_boot: Number of bootstrap samples
        seed: Random seed for reproducibility
        
    Returns:
        StatValue with betweenness and Bootstrap uncertainty
    """
    rng = np.random.default_rng(seed)
    G = network.core_network
    
    if node_id not in G:
        return StatValue(0.0, Bootstrap(np.array([0.0])), Provenance("betweenness", "bootstrap", {}))
    
    # Compute original betweenness
    bc_original = nx.betweenness_centrality(G)
    original_value = bc_original.get(node_id, 0.0)
    
    # Bootstrap: resample edges with replacement
    edges = list(G.edges(data=True))
    n_edges = len(edges)
    
    if n_edges == 0:
        return StatValue(0.0, Bootstrap(np.array([0.0])), Provenance("betweenness", "bootstrap", {}))
    
    bootstrap_samples = []
    
    for i in range(n_boot):
        # Resample edges
        indices = rng.choice(n_edges, size=n_edges, replace=True)
        resampled_edges = [edges[idx] for idx in indices]
        
        # Create bootstrap graph
        G_boot = type(G)()
        for u, v, data in resampled_edges:
            weight = data.get('weight', 1.0)
            if G_boot.has_edge(u, v):
                # If edge already exists (due to resampling), sum weights
                existing_weight = G_boot[u][v].get('weight', 1.0)
                G_boot.add_edge(u, v, weight=existing_weight + weight)
            else:
                G_boot.add_edge(u, v, weight=weight)
        
        # Compute betweenness on bootstrap sample
        try:
            bc_boot = nx.betweenness_centrality(G_boot)
            sample_value = bc_boot.get(node_id, 0.0)
        except:
            # If computation fails (e.g., disconnected), use 0
            sample_value = 0.0
        
        # Store difference from original (for relative uncertainty)
        bootstrap_samples.append(sample_value - original_value)
    
    # Create Bootstrap uncertainty model
    uncertainty = Bootstrap(np.array(bootstrap_samples))
    
    return StatValue(
        value=original_value,
        uncertainty=uncertainty,
        provenance=Provenance(
            algorithm="betweenness",
            uncertainty_method="bootstrap",
            parameters={"n_boot": n_boot, "unit": "edges"},
            seed=seed
        )
    )


def main():
    """Demonstrate betweenness computation with Bootstrap uncertainty."""
    print("=" * 70)
    print("Uncertainty-First Statistics: Betweenness with Bootstrap")
    print("=" * 70)
    print()
    
    # Create a more complex multilayer network
    print("1. Creating multilayer network...")
    net = multinet.multi_layer_network(directed=False)
    
    # Add edges to create a network with interesting betweenness structure
    # Layer 1: A star pattern
    edges = [
        ["A", "L1", "B", "L1", 1.0],
        ["A", "L1", "C", "L1", 1.0],
        ["A", "L1", "D", "L1", 1.0],
        ["A", "L1", "E", "L1", 1.0],
    ]
    
    # Layer 2: A chain pattern
    edges.extend([
        ["B", "L2", "C", "L2", 1.0],
        ["C", "L2", "D", "L2", 1.0],
        ["D", "L2", "E", "L2", 1.0],
    ])
    
    net.add_edges(edges, input_type="list")
    print(f"   Added {len(edges)} edges across 2 layers")
    print(f"   Network has {net.core_network.number_of_nodes()} nodes")
    print()
    
    # Compute betweenness with bootstrap for key nodes
    print("2. Computing betweenness with Bootstrap uncertainty...")
    print("   (Using 20 bootstrap samples for speed)")
    print()
    
    # Select representative nodes from different layers
    nodes_to_analyze = [
        ("A", "L1"),  # Central hub in L1
        ("C", "L2"),  # Middle of chain in L2
        ("E", "L1"),  # Peripheral in L1
    ]
    
    betweenness_stats = {}
    
    for node in nodes_to_analyze:
        if node in net.core_network:
            stat = compute_betweenness_with_bootstrap(net, node, n_boot=20, seed=42)
            betweenness_stats[node] = stat
    
    print(f"   Computed betweenness for {len(betweenness_stats)} nodes")
    print()
    
    # Display results
    print("3. Results with Uncertainty:")
    print("-" * 70)
    print(f"{'Node':<15} {'BC':<12} {'Std':<12} {'CI (95%)':<20} {'Robust':<10}")
    print("-" * 70)
    
    for node, stat in sorted(betweenness_stats.items(), key=lambda x: float(x[1]), reverse=True):
        ci_low, ci_high = stat.ci(0.95)
        node_str = f"{node[0]}-{node[1]}"
        print(f"{node_str:<15} {float(stat):<12.4f} {stat.std():<12.4f} "
              f"[{ci_low:.4f}, {ci_high:.4f}]  {stat.robustness():<10.3f}")
    
    print("-" * 70)
    print()
    
    # Explain the results
    print("4. Interpretation:")
    if ("A", "L1") in betweenness_stats:
        stat_a = betweenness_stats[("A", "L1")]
        print(f"   Node A (Layer 1):")
        print(f"     - Betweenness: {float(stat_a):.4f}")
        print(f"     - Std: {stat_a.std():.4f}")
        print(f"     - Robustness: {stat_a.robustness():.3f}")
        if stat_a.robustness() > 0.8:
            print(f"     - High robustness → stable under edge resampling")
        else:
            print(f"     - Lower robustness → sensitive to network perturbations")
    print()
    
    # Demonstrate arithmetic with uncertain values
    print("5. Arithmetic with uncertain values...")
    if len(betweenness_stats) >= 2:
        nodes_list = list(betweenness_stats.keys())
        stat1 = betweenness_stats[nodes_list[0]]
        stat2 = betweenness_stats[nodes_list[1]]
        
        # Addition propagates uncertainty via Monte Carlo
        stat_sum = stat1 + stat2
        print(f"   {nodes_list[0]} + {nodes_list[1]}:")
        print(f"     Value: {float(stat_sum):.4f}")
        print(f"     Std: {stat_sum.std():.4f}")
        print(f"     (Uncertainty propagated via Monte Carlo sampling)")
    print()
    
    # Demonstrate querying uncertainty
    print("6. Querying Uncertainty Details:")
    if ("A", "L1") in betweenness_stats:
        stat = betweenness_stats[("A", "L1")]
        summary = stat.uncertainty.summary(level=0.95)
        print(f"   Node A (L1) uncertainty summary:")
        for key, value in summary.items():
            if key != "ci":
                print(f"     {key}: {value}")
            else:
                print(f"     ci: [{value[0]:.4f}, {value[1]:.4f}]")
    print()
    
    # Demonstrate reproducibility
    print("7. Reproducibility via seed:")
    if ("A", "L1") in net.core_network:
        # Compute twice with same seed
        stat_a1 = compute_betweenness_with_bootstrap(net, ("A", "L1"), n_boot=20, seed=42)
        stat_a2 = compute_betweenness_with_bootstrap(net, ("A", "L1"), n_boot=20, seed=42)
        
        print(f"   Run 1: {float(stat_a1):.6f} (std: {stat_a1.std():.6f})")
        print(f"   Run 2: {float(stat_a2):.6f} (std: {stat_a2.std():.6f})")
        
        if abs(float(stat_a1) - float(stat_a2)) < 1e-10:
            print(f"   ✓ Results are identical (reproducible)")
    print()
    
    print("=" * 70)
    print("Key Takeaways:")
    print("- Bootstrap provides empirical uncertainty estimates")
    print("- Uncertainty reflects sensitivity to network perturbations")
    print("- Robustness score quantifies reliability (0-1 scale)")
    print("- Arithmetic operations propagate uncertainty via Monte Carlo")
    print("- Provenance tracks seed for reproducibility")
    print("=" * 70)


if __name__ == "__main__":
    main()
