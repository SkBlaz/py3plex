"""Example demonstrating stratified perturbation for variance-reduced UQ.

This example shows how stratified resampling reduces estimator variance
compared to naive perturbation, achieving the same accuracy with fewer samples.
"""

from py3plex.core import multinet
from py3plex.uncertainty import estimate_uncertainty, ResamplingStrategy
import numpy as np
import networkx as nx


def build_heterogeneous_network():
    """Build a multilayer network with heterogeneous degree distribution."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    
    # Layer 0: Star network (one hub, many spokes)
    edges_l0 = [["hub", "L0", f"node{i}", "L0", 1.0] for i in range(1, 11)]
    
    # Layer 1: Regular chain
    edges_l1 = [[f"node{i}", "L1", f"node{i+1}", "L1", 1.0] for i in range(1, 10)]
    
    # Inter-layer connections
    edges_inter = [[f"node{i}", "L0", f"node{i}", "L1", 1.0] for i in range(1, 11)]
    
    all_edges = edges_l0 + edges_l1 + edges_inter
    net.add_edges(all_edges, input_type="list")
    
    return net


def betweenness_metric(network):
    """Compute betweenness centrality."""
    return dict(nx.betweenness_centrality(network.core_network))


def main():
    print("=" * 70)
    print("Stratified Perturbation Demo: Variance-Reduced UQ")
    print("=" * 70)
    
    # Build test network
    net = build_heterogeneous_network()
    print(f"\nNetwork: {net.core_network.number_of_nodes()} nodes, "
          f"{net.core_network.number_of_edges()} edges")
    
    # Regular perturbation with 50 samples
    print("\n" + "-" * 70)
    print("1. Regular Perturbation (50 samples)")
    print("-" * 70)
    
    result_regular = estimate_uncertainty(
        net,
        betweenness_metric,
        n_runs=50,
        resampling=ResamplingStrategy.PERTURBATION,
        random_seed=42,
        perturbation_params={"edge_drop_p": 0.1}
    )
    
    print(f"Mean betweenness std: {np.mean(result_regular.std):.6f}")
    
    # Stratified perturbation with 50 samples (auto-strata)
    print("\n" + "-" * 70)
    print("2. Stratified Perturbation (50 samples, auto-strata)")
    print("-" * 70)
    
    result_stratified = estimate_uncertainty(
        net,
        betweenness_metric,
        n_runs=50,
        resampling=ResamplingStrategy.STRATIFIED_PERTURBATION,
        random_seed=42,
        perturbation_params={"edge_drop_p": 0.1}
    )
    
    print(f"Mean betweenness std: {np.mean(result_stratified.std):.6f}")
    print(f"Stratification metadata: {result_stratified.meta.get('stratification', {})}")
    print(f"Number of strata: {result_stratified.meta.get('n_strata', 'N/A')}")
    
    # Stratified perturbation with explicit strata
    print("\n" + "-" * 70)
    print("3. Stratified Perturbation (50 samples, degree bins=3)")
    print("-" * 70)
    
    result_stratified_explicit = estimate_uncertainty(
        net,
        betweenness_metric,
        n_runs=50,
        resampling=ResamplingStrategy.STRATIFIED_PERTURBATION,
        random_seed=42,
        perturbation_params={
            "edge_drop_p": 0.1,
            "strata": ["degree"],
            "bins": {"degree": 3}
        }
    )
    
    print(f"Mean betweenness std: {np.mean(result_stratified_explicit.std):.6f}")
    
    # Summary
    print("\n" + "=" * 70)
    print("Summary: Variance Reduction")
    print("=" * 70)
    
    variance_regular = np.mean(result_regular.std ** 2)
    variance_stratified = np.mean(result_stratified.std ** 2)
    reduction = (variance_regular - variance_stratified) / variance_regular * 100
    
    print(f"Regular perturbation variance:     {variance_regular:.8f}")
    print(f"Stratified perturbation variance:  {variance_stratified:.8f}")
    print(f"Variance reduction:                {reduction:.2f}%")
    
    if reduction > 0:
        print("\nOK Stratified perturbation achieved lower variance with same sample count!")
    else:
        print("\nNote: Variance reduction depends on network heterogeneity.")
        print("     For this small network, differences may be minimal.")
    
    # Determinism check
    print("\n" + "=" * 70)
    print("Determinism Check")
    print("=" * 70)
    
    result_check1 = estimate_uncertainty(
        net,
        betweenness_metric,
        n_runs=20,
        resampling=ResamplingStrategy.STRATIFIED_PERTURBATION,
        random_seed=42,
        perturbation_params={"edge_drop_p": 0.1}
    )
    
    result_check2 = estimate_uncertainty(
        net,
        betweenness_metric,
        n_runs=20,
        resampling=ResamplingStrategy.STRATIFIED_PERTURBATION,
        random_seed=42,  # Same seed
        perturbation_params={"edge_drop_p": 0.1}
    )
    
    if np.allclose(result_check1.mean, result_check2.mean):
        print("OK Stratified perturbation is deterministic with same seed!")
    else:
        print("FAIL Results differ (non-deterministic)")
    
    print("\n" + "=" * 70)
    print("Example completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
