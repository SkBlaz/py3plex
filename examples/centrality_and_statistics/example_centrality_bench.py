#!/usr/bin/env python3
"""
Example: Centrality Benchmark - Comparing Multiple Centrality Algorithms

This example demonstrates:
1. Generating 100 synthetic multilayer networks
2. Computing all centrality measures on each network
3. Comparing centrality rankings using Jaccard similarity at different top-k values
4. Integrating similarity curves to get overall similarity scores
5. Visualizing results as a heatmap showing similarity between different algorithms

The benchmark helps understand how different centrality measures correlate
with each other across various network topologies.

SKIP_CI: slow - This benchmark takes several minutes to complete
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
from tqdm import tqdm

from py3plex.core import random_generators
from py3plex.algorithms.multilayer_algorithms.centrality import compute_all_centralities


def jaccard_similarity(set1, set2):
    """
    Compute Jaccard similarity between two sets.
    
    Args:
        set1: First set
        set2: Second set
        
    Returns:
        float: Jaccard similarity (intersection over union)
    """
    if len(set1) == 0 and len(set2) == 0:
        return 1.0
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union > 0 else 0.0


def get_topk_nodes(centrality_dict, k):
    """
    Get top-k nodes from centrality dictionary.
    
    Args:
        centrality_dict: Dictionary mapping nodes/node-layers to centrality values
        k: Number of top nodes to retrieve
        
    Returns:
        set: Set of top-k nodes (or node-layer tuples)
    """
    sorted_items = sorted(centrality_dict.items(), key=lambda x: x[1], reverse=True)
    return set([item[0] for item in sorted_items[:k]])


def compare_centralities_at_topk(cent1, cent2, max_k=50):
    """
    Compare two centrality measures at different top-k values.
    
    Args:
        cent1: First centrality dictionary
        cent2: Second centrality dictionary
        max_k: Maximum k value to test
        
    Returns:
        list: Jaccard similarities for k=1 to max_k
    """
    # Limit max_k to the size of the smaller centrality dict
    actual_max_k = min(max_k, len(cent1), len(cent2))
    if actual_max_k == 0:
        return [0.0]
    
    similarities = []
    for k in range(1, actual_max_k + 1):
        topk1 = get_topk_nodes(cent1, k)
        topk2 = get_topk_nodes(cent2, k)
        sim = jaccard_similarity(topk1, topk2)
        similarities.append(sim)
    
    return similarities


def integrate_similarity_curve(similarities):
    """
    Integrate the similarity curve using trapezoidal rule.
    
    Args:
        similarities: List of similarity values at different k
        
    Returns:
        float: Integrated area under the curve (normalized by number of points)
    """
    if len(similarities) == 0:
        return 0.0
    # Use trapezoidal rule and normalize by length
    return np.trapz(similarities) / len(similarities)


def generate_synthetic_network(num_nodes=50, num_layers=3, edge_prob=0.15):
    """
    Generate a synthetic multilayer Erdős-Rényi network.
    
    Args:
        num_nodes: Number of nodes in each layer
        num_layers: Number of layers
        edge_prob: Edge probability in each layer
        
    Returns:
        multi_layer_network: Generated network
    """
    return random_generators.random_multilayer_ER(
        num_nodes,
        num_layers,
        edge_prob,
        directed=False
    )


def compute_centralities_safe(network):
    """
    Compute centralities with error handling.
    
    Args:
        network: Multilayer network
        
    Returns:
        dict: Dictionary of centrality measures
    """
    try:
        # Compute only basic measures for speed (no path-based or advanced)
        centralities = compute_all_centralities(
            network,
            include_path_based=False,
            include_advanced=False,
            include_extended=False
        )
        return centralities
    except Exception as e:
        print(f"Warning: Error computing centralities: {e}")
        return {}


def aggregate_node_layer_centrality(centrality_dict):
    """
    Aggregate node-layer centralities to node level by summing.
    
    Args:
        centrality_dict: Dictionary with (node, layer) keys or node keys
        
    Returns:
        dict: Dictionary with node keys
    """
    aggregated = defaultdict(float)
    
    for key, value in centrality_dict.items():
        if isinstance(key, tuple):
            # Extract node from (node, layer) tuple
            node = key[0]
            aggregated[node] += value
        else:
            # Already node-level
            aggregated[key] += value
    
    return dict(aggregated)


def run_centrality_benchmark(num_networks=100, num_nodes=30, num_layers=3, 
                             edge_prob=0.2, max_k=20):
    """
    Run the centrality benchmark on multiple synthetic networks.
    
    Args:
        num_networks: Number of networks to generate
        num_nodes: Number of nodes per network
        num_layers: Number of layers per network
        edge_prob: Edge probability for ER networks
        max_k: Maximum k for top-k comparison
        
    Returns:
        dict: Pairwise similarity matrix between centrality measures
    """
    print(f"Running centrality benchmark on {num_networks} synthetic networks...")
    print(f"Network parameters: {num_nodes} nodes, {num_layers} layers, p={edge_prob}")
    
    # Store integrated similarities for each network
    all_integrated_sims = defaultdict(lambda: defaultdict(list))
    
    # Generate networks and compute centralities
    for i in tqdm(range(num_networks), desc="Processing networks"):
        # Generate network
        network = generate_synthetic_network(num_nodes, num_layers, edge_prob)
        
        # Compute centralities
        centralities = compute_centralities_safe(network)
        
        if not centralities:
            continue
        
        # Aggregate node-layer centralities to node level
        aggregated_centralities = {}
        for cent_name, cent_values in centralities.items():
            aggregated_centralities[cent_name] = aggregate_node_layer_centrality(cent_values)
        
        # Compare all pairs of centrality measures
        cent_names = list(aggregated_centralities.keys())
        for i, cent1_name in enumerate(cent_names):
            for cent2_name in cent_names[i:]:
                cent1 = aggregated_centralities[cent1_name]
                cent2 = aggregated_centralities[cent2_name]
                
                # Compute similarity curve
                similarities = compare_centralities_at_topk(cent1, cent2, max_k)
                
                # Integrate the curve
                integrated_sim = integrate_similarity_curve(similarities)
                
                # Store result
                all_integrated_sims[cent1_name][cent2_name].append(integrated_sim)
                if cent1_name != cent2_name:
                    all_integrated_sims[cent2_name][cent1_name].append(integrated_sim)
    
    # Average the integrated similarities across all networks
    avg_similarity_matrix = {}
    all_cent_names = sorted(all_integrated_sims.keys())
    
    for cent1_name in all_cent_names:
        avg_similarity_matrix[cent1_name] = {}
        for cent2_name in all_cent_names:
            sims = all_integrated_sims[cent1_name].get(cent2_name, [])
            avg_similarity_matrix[cent1_name][cent2_name] = np.mean(sims) if sims else 0.0
    
    return avg_similarity_matrix, all_cent_names


def plot_similarity_heatmap(similarity_matrix, cent_names, output_file=None):
    """
    Plot similarity matrix as a heatmap.
    
    Args:
        similarity_matrix: Dictionary of dictionaries with pairwise similarities
        cent_names: List of centrality measure names
        output_file: Optional output file path to save figure
    """
    # Convert to numpy array for plotting
    n = len(cent_names)
    matrix = np.zeros((n, n))
    
    for i, cent1 in enumerate(cent_names):
        for j, cent2 in enumerate(cent_names):
            matrix[i, j] = similarity_matrix[cent1][cent2]
    
    # Create figure
    plt.figure(figsize=(12, 10))
    
    # Create heatmap
    sns.heatmap(
        matrix,
        xticklabels=cent_names,
        yticklabels=cent_names,
        annot=True,
        fmt='.3f',
        cmap='RdYlGn',
        vmin=0,
        vmax=1,
        cbar_kws={'label': 'Average Integrated Jaccard Similarity'},
        square=True
    )
    
    plt.title('Centrality Algorithm Similarity Matrix\n(Average Integrated Jaccard Similarity across 100 Networks)', 
              fontsize=14, pad=20)
    plt.xlabel('Centrality Measure', fontsize=12)
    plt.ylabel('Centrality Measure', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"\nHeatmap saved to: {output_file}")
    
    # Only show if not in CI mode
    import os
    if os.environ.get('MPLBACKEND') != 'Agg':
        plt.show()
    else:
        plt.close()


def print_summary_statistics(similarity_matrix, cent_names):
    """
    Print summary statistics about the similarity matrix.
    
    Args:
        similarity_matrix: Dictionary of dictionaries with pairwise similarities
        cent_names: List of centrality measure names
    """
    print("\n" + "="*70)
    print("SUMMARY STATISTICS")
    print("="*70)
    
    # Find most similar pairs (excluding diagonal)
    similarities = []
    for i, cent1 in enumerate(cent_names):
        for j, cent2 in enumerate(cent_names):
            if i < j:  # Upper triangle only
                sim = similarity_matrix[cent1][cent2]
                similarities.append((cent1, cent2, sim))
    
    similarities.sort(key=lambda x: x[2], reverse=True)
    
    print("\nTop 5 Most Similar Pairs:")
    for cent1, cent2, sim in similarities[:5]:
        print(f"  {cent1:25} <-> {cent2:25} : {sim:.4f}")
    
    print("\nTop 5 Least Similar Pairs:")
    for cent1, cent2, sim in similarities[-5:]:
        print(f"  {cent1:25} <-> {cent2:25} : {sim:.4f}")
    
    # Average similarity per measure
    print("\nAverage Similarity per Measure (with all others):")
    avg_sims = []
    for cent in cent_names:
        sims = [similarity_matrix[cent][other] 
                for other in cent_names if other != cent]
        avg_sim = np.mean(sims) if sims else 0.0
        avg_sims.append((cent, avg_sim))
    
    avg_sims.sort(key=lambda x: x[1], reverse=True)
    for cent, avg_sim in avg_sims:
        print(f"  {cent:35} : {avg_sim:.4f}")


def main():
    """
    Main function to run the centrality benchmark.
    """
    print("="*70)
    print("CENTRALITY BENCHMARK - Comparing Multiple Algorithms")
    print("="*70)
    
    # Set parameters
    NUM_NETWORKS = 100
    NUM_NODES = 30
    NUM_LAYERS = 3
    EDGE_PROB = 0.2
    MAX_K = 20
    
    print(f"\nBenchmark Configuration:")
    print(f"  Number of synthetic networks: {NUM_NETWORKS}")
    print(f"  Nodes per network: {NUM_NODES}")
    print(f"  Layers per network: {NUM_LAYERS}")
    print(f"  Edge probability: {EDGE_PROB}")
    print(f"  Top-k range: 1-{MAX_K}")
    
    # Run benchmark
    similarity_matrix, cent_names = run_centrality_benchmark(
        num_networks=NUM_NETWORKS,
        num_nodes=NUM_NODES,
        num_layers=NUM_LAYERS,
        edge_prob=EDGE_PROB,
        max_k=MAX_K
    )
    
    print(f"\nComputed {len(cent_names)} centrality measures:")
    for name in cent_names:
        print(f"  - {name}")
    
    # Print summary statistics
    print_summary_statistics(similarity_matrix, cent_names)
    
    # Plot heatmap
    output_file = "/tmp/centrality_similarity_heatmap.png"
    plot_similarity_heatmap(similarity_matrix, cent_names, output_file)
    
    print("\n" + "="*70)
    print("Benchmark completed successfully!")
    print("="*70)


if __name__ == "__main__":
    main()
