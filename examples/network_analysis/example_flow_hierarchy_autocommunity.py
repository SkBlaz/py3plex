#!/usr/bin/env python3
"""
Example: Using flow hierarchy with auto_select_community.

Teaches:
- How to add flow_hierarchical_communities as a custom candidate
- Understanding hierarchical vs flat community detection
- Comparing flow-based with modularity-based algorithms
- Interpreting hierarchical community structure

Prerequisites:
- py3plex with community detection algorithms installed

SKIP_CI: slow - Auto-selection evaluates multiple algorithms
"""

from __future__ import annotations

import sys
from typing import Any, Dict, Tuple

try:
    from py3plex.algorithms.community_detection import (
        auto_select_community,
        flow_hierarchical_communities,
    )
    from py3plex.core import multinet
    from py3plex.selection.community_registry import CandidateSpec
    import numpy as np
except ImportError as exc:  # pragma: no cover - surfaced to user
    auto_select_community = None
    flow_hierarchical_communities = None
    multinet = None
    CandidateSpec = None
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


# ============================================================================
# Wrapper for flow hierarchy to make it compatible with auto_select
# ============================================================================

def flow_hierarchy_wrapper(
    network: Any,
    alpha: float = 0.8,
    approx: str = "mc",
    n_walks: int = 50,
    seed: int = None
) -> Dict[Tuple[Any, Any], int]:
    """
    Wrapper for flow_hierarchical_communities to work with auto_select.
    
    Returns a flat partition (best scale) from the hierarchical result.
    
    Args:
        network: py3plex multi_layer_network object
        alpha: Interlayer coupling (0=full, 1=independent)
        approx: "mc" (Monte Carlo) or "exact"
        n_walks: Number of random walks per node (MC only)
        seed: Random seed for reproducibility
    
    Returns:
        Dictionary mapping (node, layer) tuples to community IDs
    """
    result = flow_hierarchical_communities(
        network,
        alpha=alpha,
        approx=approx,
        n_walks=n_walks,
        seed=seed if seed is not None else 42,
    )
    
    # Return the best partition (maximum stability)
    return result.get_partition()


def example_flow_hierarchy_in_autoselect() -> None:
    """Example: Using flow hierarchy as a candidate in auto_select."""
    _print_header("Flow Hierarchy as AutoCommunity Candidate")
    
    # Create a multilayer network with hierarchical structure
    network = multinet.multi_layer_network(directed=False)
    
    # Layer 1: Two super-communities, each with 2 sub-communities
    # Super-community 1: nodes 0-9 (sub: 0-4, 5-9)
    # Super-community 2: nodes 10-19 (sub: 10-14, 15-19)
    
    print("Creating hierarchical multilayer network...")
    
    # Add nodes
    for i in range(20):
        network.add_nodes([{"source": f"N{i}", "type": "L1"}])
        network.add_nodes([{"source": f"N{i}", "type": "L2"}])
    
    # Build hierarchical structure in Layer 1
    # Sub-community 1a: 0-4 (tight)
    for i in range(5):
        for j in range(i+1, 5):
            network.add_edges([{
                "source": f"N{i}", "target": f"N{j}",
                "source_type": "L1", "target_type": "L1"
            }])
    
    # Sub-community 1b: 5-9 (tight)
    for i in range(5, 10):
        for j in range(i+1, 10):
            network.add_edges([{
                "source": f"N{i}", "target": f"N{j}",
                "source_type": "L1", "target_type": "L1"
            }])
    
    # Weak connection between 1a and 1b (forms super-community 1)
    network.add_edges([{
        "source": "N4", "target": "N5",
        "source_type": "L1", "target_type": "L1"
    }])
    
    # Sub-community 2a: 10-14 (tight)
    for i in range(10, 15):
        for j in range(i+1, 15):
            network.add_edges([{
                "source": f"N{i}", "target": f"N{j}",
                "source_type": "L1", "target_type": "L1"
            }])
    
    # Sub-community 2b: 15-19 (tight)
    for i in range(15, 20):
        for j in range(i+1, 20):
            network.add_edges([{
                "source": f"N{i}", "target": f"N{j}",
                "source_type": "L1", "target_type": "L1"
            }])
    
    # Weak connection between 2a and 2b (forms super-community 2)
    network.add_edges([{
        "source": "N14", "target": "N15",
        "source_type": "L1", "target_type": "L1"
    }])
    
    # Very weak connection between super-communities
    network.add_edges([{
        "source": "N9", "target": "N10",
        "source_type": "L1", "target_type": "L1"
    }])
    
    # Add Layer 2 with different structure
    for i in range(0, 20, 2):
        if i < 18:
            network.add_edges([{
                "source": f"N{i}", "target": f"N{i+2}",
                "source_type": "L2", "target_type": "L2"
            }])
    
    print(f"Network created: {len(list(network.get_nodes()))} node-layer pairs")
    
    # Create custom candidates including flow hierarchy
    custom_candidates = [
        # Flow hierarchy with high alpha (layer-independent)
        CandidateSpec(
            name="flow_hierarchy_alpha09",
            callable=flow_hierarchy_wrapper,
            params={"alpha": 0.9, "approx": "mc", "n_walks": 50},
            supports_multilayer=True,
            seed_param_name="seed",
        ),
        # Flow hierarchy with balanced alpha
        CandidateSpec(
            name="flow_hierarchy_alpha05",
            callable=flow_hierarchy_wrapper,
            params={"alpha": 0.5, "approx": "mc", "n_walks": 50},
            supports_multilayer=True,
            seed_param_name="seed",
        ),
        # Flow hierarchy with low alpha (strong coupling)
        CandidateSpec(
            name="flow_hierarchy_alpha02",
            callable=flow_hierarchy_wrapper,
            params={"alpha": 0.2, "approx": "mc", "n_walks": 50},
            supports_multilayer=True,
            seed_param_name="seed",
        ),
    ]
    
    print("\nRunning auto_select with flow hierarchy candidates...")
    print("(This may take a moment...)")
    
    # Run auto_select with custom candidates
    result = auto_select_community(
        network,
        mode="wins",  # Use wins mode for comparison
        fast=True,
        max_candidates=10,
        seed=DEFAULT_SEED,
        custom_candidates=custom_candidates,
    )
    
    # Display results
    print("\n" + "=" * 70)
    print("Auto-Selection Results")
    print("=" * 70)
    
    print(f"\nWinning algorithm: {result.algorithm['name']}")
    if 'params' in result.algorithm:
        print(f"Parameters: {result.algorithm['params']}")
    
    print(f"\nPartition stats:")
    print(f"  Communities: {len(set(result.partition.values()))}")
    print(f"  Nodes: {len(result.partition)}")
    
    print("\nLeaderboard (top 5):")
    print(result.leaderboard.head(5).to_string())
    
    print("\n" + result.explain())


def example_compare_flow_with_flat() -> None:
    """Example: Compare flow hierarchy with flat algorithms."""
    _print_header("Comparing Flow Hierarchy with Flat Algorithms")
    
    # Create a simple network
    network = multinet.multi_layer_network(directed=False)
    
    # Two clear communities
    for i in range(10):
        network.add_nodes([{"source": f"N{i}", "type": "L1"}])
    
    # Community 1: 0-4 (fully connected)
    for i in range(5):
        for j in range(i+1, 5):
            network.add_edges([{
                "source": f"N{i}", "target": f"N{j}",
                "source_type": "L1", "target_type": "L1"
            }])
    
    # Community 2: 5-9 (fully connected)
    for i in range(5, 10):
        for j in range(i+1, 10):
            network.add_edges([{
                "source": f"N{i}", "target": f"N{j}",
                "source_type": "L1", "target_type": "L1"
            }])
    
    # Bridge
    network.add_edges([{
        "source": "N4", "target": "N5",
        "source_type": "L1", "target_type": "L1"
    }])
    
    print("Running flow hierarchy (full hierarchical output)...")
    
    # Run flow hierarchy to see full hierarchy
    result = flow_hierarchical_communities(
        network,
        approx="mc",
        n_walks=100,
        seed=DEFAULT_SEED
    )
    
    print(result.summary())
    
    print("\nHierarchy exploration:")
    for scale in sorted(result.hierarchy_levels.keys())[:5]:
        partition = result.hierarchy_levels[scale]
        n_comms = len(set(partition.values()))
        stability = result.stability_scores[scale]
        print(f"  Scale {scale:6.1f}: {n_comms:2d} communities (stability={stability:.3f})")
    
    print("\nComparing with flat algorithms via auto_select...")
    
    # Now compare with standard algorithms
    auto_result = auto_select_community(
        network,
        mode="wins",
        fast=True,
        seed=DEFAULT_SEED,
    )
    
    print(f"\nAuto-select winner: {auto_result.algorithm['name']}")
    print(f"Communities found: {len(set(auto_result.partition.values()))}")


def main() -> None:
    """Run all examples."""
    if IMPORT_ERROR is not None:
        print(f"Error: Failed to import required modules: {IMPORT_ERROR}")
        sys.exit(1)
    
    try:
        # Example 1: Flow hierarchy as AutoCommunity candidate
        example_flow_hierarchy_in_autoselect()
        
        # Example 2: Compare flow with flat algorithms
        example_compare_flow_with_flat()
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
