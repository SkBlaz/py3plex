#!/usr/bin/env python3
"""
Example: Automatic community detection with Uncertainty Quantification.

Teaches:
- How to enable UQ for stability analysis in auto_select_community
- Understanding UQ methods: seed, perturbation, bootstrap
- Interpreting stability metrics in the leaderboard
- Using UQ to gate wins by significance

Prerequisites:
- py3plex with community detection and UQ modules installed

SKIP_CI: slow - UQ requires multiple runs and is computationally intensive
"""

from __future__ import annotations

import sys
from typing import Dict

try:
    from py3plex.algorithms.community_detection import auto_select_community
    from py3plex.core import multinet, random_generators
    import numpy as np
except ImportError as exc:  # pragma: no cover - surfaced to user
    auto_select_community = None
    multinet = None
    random_generators = None
    np = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None

DEFAULT_SEED = 42


def _print_header(title: str) -> None:
    """Pretty header for individual sections."""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def example_uq_basic() -> None:
    """Example 1: Basic UQ with seed-based variation."""
    _print_header("Example 1: Auto-select with UQ (seed-based)")
    
    # Create a network with moderate community structure
    network = multinet.multi_layer_network(directed=False)
    
    # Create 3 communities with different densities
    for comm_idx in range(3):
        start = comm_idx * 5
        end = start + 5
        
        nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(start, end)]
        network.add_nodes(nodes)
        
        # Dense intra-community edges
        edges = [
            {"source": f"N{i}", "target": f"N{j}", 
             "source_type": "layer1", "target_type": "layer1"}
            for i in range(start, end) for j in range(i+1, end)
            if (i + j) % 3 != 0  # Some sparsity
        ]
        network.add_edges(edges)
    
    # Add some inter-community edges
    bridge_edges = [
        {"source": "N4", "target": "N5", "source_type": "layer1", "target_type": "layer1"},
        {"source": "N9", "target": "N10", "source_type": "layer1", "target_type": "layer1"},
    ]
    network.add_edges(bridge_edges)
    
    print(f"Network: {len(list(network.get_nodes()))} nodes, "
          f"{network.edge_count} edges")
    
    # Run auto-select with UQ
    print("\nRunning auto-select with UQ (10 samples)...")
    print("This will take longer as algorithms are run multiple times...")
    
    result = auto_select_community(
        network,
        fast=True,
        max_candidates=2,
        uq=True,
        uq_n_samples=10,
        uq_method="seed",
        seed=DEFAULT_SEED
    )
    
    # Show results
    print("\n" + result.explain())
    
    # Show leaderboard with stability metrics
    print("\n--- Leaderboard with Stability Metrics ---")
    print(result.leaderboard.to_string(index=False))
    
    # Highlight stability information
    print("\n--- Stability Analysis ---")
    print("Higher stability values indicate more consistent partitions")
    print("across different random seeds/perturbations.")


def example_uq_comparison() -> None:
    """Example 2: Comparing algorithms with different stability profiles."""
    _print_header("Example 2: Stability comparison across algorithms")
    
    # Create a more challenging network with overlapping communities
    np.random.seed(DEFAULT_SEED)
    network = random_generators.random_multilayer_ER(
        n=25,
        l=2,
        p=0.15,
        directed=False,
    )
    
    print(f"Network: {len(list(network.get_nodes()))} node-layer pairs")
    
    # Run with UQ to assess stability
    print("\nRunning auto-select with UQ to compare stability...")
    print("Using seed-based method for robustness testing...")
    
    result = auto_select_community(
        network,
        fast=True,
        max_candidates=3,
        uq=True,
        uq_n_samples=15,
        uq_method="seed",  # seed is faster than bootstrap for examples
        seed=DEFAULT_SEED
    )
    
    # Show results
    print("\n" + result.explain())
    
    # Detailed stability analysis
    print("\n--- Detailed Stability Comparison ---")
    leaderboard = result.leaderboard
    
    # Check if stability columns exist
    stability_cols = [col for col in leaderboard.columns if 'stability' in col.lower()]
    
    if stability_cols:
        print("\nStability metrics found:")
        for col in stability_cols:
            print(f"  - {col}")
        
        print("\nTop 3 by stability:")
        if 'stability' in leaderboard.columns:
            stable_sorted = leaderboard.sort_values('stability', ascending=False)
            print(stable_sorted.head(3)[['rank', 'algorithm', 'stability']].to_string(index=False))
    else:
        print("Note: Stability metrics may require specific UQ configuration")
    
    # Show provenance
    print("\n--- UQ Configuration ---")
    config = result.provenance['selection_config']
    print(f"UQ enabled: {config['uq_enabled']}")
    print(f"UQ samples: {config['uq_n_samples']}")
    print(f"UQ method: {config['uq_method']}")


def example_uq_parameter_robustness() -> None:
    """Example 3: Using UQ to assess parameter sensitivity."""
    _print_header("Example 3: Parameter robustness with UQ")
    
    # Create a network with clear structure
    network = multinet.multi_layer_network(directed=False)
    
    # Two tight communities
    for comm_idx in range(2):
        start = comm_idx * 6
        end = start + 6
        
        nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(start, end)]
        network.add_nodes(nodes)
        
        # Very dense intra-community edges
        edges = [
            {"source": f"N{i}", "target": f"N{j}", 
             "source_type": "layer1", "target_type": "layer1"}
            for i in range(start, end) for j in range(i+1, end)
        ]
        network.add_edges(edges)
    
    # Weak bridge
    network.add_edges([
        {"source": "N5", "target": "N6", "source_type": "layer1", "target_type": "layer1"}
    ])
    
    print(f"Network: {len(list(network.get_nodes()))} nodes (2 communities)")
    
    # Run with smaller UQ sample for demonstration
    print("\nRunning auto-select with UQ (5 samples for speed)...")
    
    result = auto_select_community(
        network,
        fast=True,
        max_candidates=2,
        uq=True,
        uq_n_samples=5,
        uq_method="seed",
        seed=DEFAULT_SEED
    )
    
    # Show results
    print("\n" + result.explain())
    
    print("\n--- Key Insights with UQ ---")
    print("1. The winner is selected based on 'most wins' across metrics")
    print("2. UQ helps identify algorithms that produce stable results")
    print("3. Consider both quality (metrics) and stability (UQ) in final choice")
    
    # Show report summary
    print("\n--- Report Summary ---")
    report = result.report
    print(f"Total contestants: {report['n_contestants']}")
    print(f"Total metrics: {report['n_metrics']}")
    
    print("\nMetrics by bucket:")
    for bucket, metrics in report['metrics_by_bucket'].items():
        if metrics:
            print(f"  {bucket}: {len(metrics)} metrics")


def main() -> int:
    """Run all UQ examples."""
    if IMPORT_ERROR:
        print(f"Import error: {IMPORT_ERROR}", file=sys.stderr)
        print("Please ensure py3plex with UQ support is installed.", file=sys.stderr)
        return 1
    
    print("=" * 70)
    print("Auto-Select with Uncertainty Quantification (UQ)")
    print("=" * 70)
    print("\nUQ provides stability analysis for community detection,")
    print("helping identify algorithms that produce robust results.")
    print("\nNote: UQ examples take longer as they run multiple iterations.")
    
    try:
        example_uq_basic()
        example_uq_comparison()
        example_uq_parameter_robustness()
        
        print("\n" + "=" * 70)
        print("✓ All UQ examples completed successfully!")
        print("=" * 70)
        print("\nKey Takeaways:")
        print("- UQ helps assess partition stability")
        print("- Seed method: varies random seeds")
        print("- Bootstrap method: resamples network edges")
        print("- Perturbation method: adds noise to network")
        print("- Higher stability = more reliable communities")
        
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
