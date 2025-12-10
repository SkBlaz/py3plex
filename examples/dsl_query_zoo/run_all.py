"""Run all Query Zoo examples and generate outputs.

This script executes all query functions and saves their outputs to the
outputs/ directory. Outputs include:
- CSV files with query results
- Summary statistics
- Small plots where appropriate

All examples use fixed random seeds for reproducibility.
"""

import os
import sys
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns

# Add parent directory to path to import query zoo modules
sys.path.insert(0, str(Path(__file__).parent))

from datasets import get_dataset
from queries import (
    query_basic_exploration,
    query_cross_layer_hubs,
    query_layer_similarity,
    query_community_structure,
    query_multiplex_pagerank,
    query_robustness_analysis,
    query_advanced_centrality_comparison,
)


def setup_output_dir():
    """Create output directory if it doesn't exist."""
    output_dir = Path(__file__).parent / "outputs"
    output_dir.mkdir(exist_ok=True)
    return output_dir


def save_dataframe(df, filename, output_dir):
    """Save DataFrame to CSV."""
    filepath = output_dir / filename
    df.to_csv(filepath, index=False)
    print(f"  Saved: {filename}")
    return filepath


def plot_layer_stats(df, output_dir):
    """Create a bar plot of layer statistics."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    
    # Plot 1: Number of nodes per layer
    axes[0].bar(df['layer'], df['n_nodes'], color='skyblue')
    axes[0].set_title('Nodes per Layer')
    axes[0].set_xlabel('Layer')
    axes[0].set_ylabel('Number of Nodes')
    axes[0].tick_params(axis='x', rotation=45)
    
    # Plot 2: Number of edges per layer
    axes[1].bar(df['layer'], df['n_edges'], color='lightcoral')
    axes[1].set_title('Edges per Layer')
    axes[1].set_xlabel('Layer')
    axes[1].set_ylabel('Number of Edges')
    axes[1].tick_params(axis='x', rotation=45)
    
    # Plot 3: Average degree per layer
    axes[2].bar(df['layer'], df['avg_degree'], color='lightgreen')
    axes[2].set_title('Average Degree per Layer')
    axes[2].set_xlabel('Layer')
    axes[2].set_ylabel('Average Degree')
    axes[2].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    filepath = output_dir / 'basic_exploration_plot.png'
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: basic_exploration_plot.png")
    return filepath


def plot_layer_similarity(df, output_dir):
    """Create a heatmap of layer similarity."""
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(df, annot=True, fmt='.2f', cmap='coolwarm', center=0,
                square=True, ax=ax, cbar_kws={'label': 'Correlation'})
    ax.set_title('Layer Similarity (Degree Distribution Correlation)')
    
    plt.tight_layout()
    filepath = output_dir / 'layer_similarity_heatmap.png'
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: layer_similarity_heatmap.png")
    return filepath


def plot_robustness(df, output_dir):
    """Create a plot showing connectivity loss when layers are removed."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    scenarios = df['scenario'].tolist()
    connectivity_loss = df['connectivity_loss'].tolist()
    
    colors = ['green' if loss == 0 else 'orange' if loss < 50 else 'red' 
              for loss in connectivity_loss]
    
    ax.barh(scenarios, connectivity_loss, color=colors, alpha=0.7)
    ax.set_xlabel('Connectivity Loss (%)')
    ax.set_title('Network Robustness: Impact of Layer Removal')
    ax.axvline(x=0, color='black', linewidth=0.5)
    ax.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    filepath = output_dir / 'robustness_analysis_plot.png'
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: robustness_analysis_plot.png")
    return filepath


def run_all_queries():
    """Execute all queries and save outputs."""
    print("=" * 80)
    print("DSL QUERY ZOO: Running All Examples")
    print("=" * 80)
    
    output_dir = setup_output_dir()
    print(f"\nOutput directory: {output_dir}\n")
    
    # Load datasets
    print("Loading datasets...")
    social_work_net = get_dataset('social_work', seed=42)
    communication_net = get_dataset('communication', seed=42)
    transport_net = get_dataset('transport', seed=42)
    print("  ✓ Datasets loaded\n")
    
    # Query 1: Basic Exploration
    print("[1/7] Running: Basic Multilayer Exploration")
    try:
        result = query_basic_exploration(social_work_net)
        save_dataframe(result, 'basic_exploration.csv', output_dir)
        plot_layer_stats(result, output_dir)
        print(f"  Result preview:\n{result.to_string(index=False)}\n")
    except Exception as e:
        print(f"  ERROR: {e}\n")
    
    # Query 2: Cross-Layer Hubs
    print("[2/7] Running: Cross-Layer Hubs")
    try:
        result = query_cross_layer_hubs(social_work_net, k=5)
        save_dataframe(result, 'cross_layer_hubs.csv', output_dir)
        print(f"  Result preview (first 10 rows):\n{result.head(10).to_string(index=False)}\n")
    except Exception as e:
        print(f"  ERROR: {e}\n")
    
    # Query 3: Layer Similarity
    print("[3/7] Running: Layer Similarity Analysis")
    try:
        result = query_layer_similarity(social_work_net)
        save_dataframe(result, 'layer_similarity.csv', output_dir)
        plot_layer_similarity(result, output_dir)
        print(f"  Result:\n{result.to_string()}\n")
    except Exception as e:
        print(f"  ERROR: {e}\n")
    
    # Query 4: Community Structure
    print("[4/7] Running: Community Structure Analysis")
    try:
        result = query_community_structure(communication_net)
        save_dataframe(result, 'community_structure.csv', output_dir)
        print(f"  Result preview (first 10 rows):\n{result.head(10).to_string(index=False)}\n")
    except Exception as e:
        print(f"  ERROR: {e}\n")
    
    # Query 5: Multiplex PageRank
    print("[5/7] Running: Multiplex PageRank")
    try:
        result = query_multiplex_pagerank(transport_net)
        save_dataframe(result, 'multiplex_pagerank.csv', output_dir)
        print(f"  Result preview (top 10 nodes):\n{result.head(10).to_string(index=False)}\n")
    except Exception as e:
        print(f"  ERROR: {e}\n")
    
    # Query 6: Robustness Analysis
    print("[6/7] Running: Robustness Analysis")
    try:
        result = query_robustness_analysis(transport_net)
        save_dataframe(result, 'robustness_analysis.csv', output_dir)
        plot_robustness(result, output_dir)
        print(f"  Result:\n{result.to_string(index=False)}\n")
    except Exception as e:
        print(f"  ERROR: {e}\n")
    
    # Query 7: Advanced Centrality Comparison
    print("[7/7] Running: Advanced Centrality Comparison")
    try:
        result = query_advanced_centrality_comparison(communication_net)
        save_dataframe(result, 'centrality_comparison.csv', output_dir)
        print(f"  Result preview (top 10 nodes):\n{result.head(10).to_string(index=False)}\n")
    except Exception as e:
        print(f"  ERROR: {e}\n")
    
    print("=" * 80)
    print("QUERY ZOO EXECUTION COMPLETE")
    print("=" * 80)
    print(f"\nAll outputs saved to: {output_dir}")
    print("\nGenerated files:")
    for file in sorted(output_dir.glob('*')):
        print(f"  - {file.name}")


if __name__ == '__main__':
    run_all_queries()
