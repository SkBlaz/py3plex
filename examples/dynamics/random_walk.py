"""
Random walk dynamics on multilayer networks.

Teaches how to build a small multilayer network, run py3plex's
`RandomWalkDynamics`, and analyze trajectories (visit counts, layer switching,
lazy walks, hitting times). Prerequisites: py3plex installed with dynamics
extras, plus numpy, networkx; matplotlib is optional for plots (Agg backend).
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Hashable, Tuple

import networkx as nx
import numpy as np
from py3plex.core import multinet
from py3plex.dynamics import RandomWalkDynamics

try:  # Matplotlib is optional; skip plots if missing.
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError as exc:  # pragma: no cover - surfaced to users running examples
    plt = None
    MATPLOTLIB_ERROR = exc
else:
    MATPLOTLIB_ERROR = None

DEFAULT_SEED = 42
OUTPUT_DIR = Path(__file__).parent / "outputs"


def _ensure_output_dir() -> Path:
    """Create output directory for plots if needed."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    return OUTPUT_DIR


def create_two_layer_network() -> multinet.multi_layer_network:
    """Create a two-layer network with ring vs star structures."""
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes to both layers
    n = 15
    nodes = []
    for i in range(n):
        nodes.append({'source': i, 'type': 'ring'})
        nodes.append({'source': i, 'type': 'star'})
    
    network.add_nodes(nodes)
    
    # Layer 1: Ring topology
    for i in range(n):
        network.add_edges([{
            'source': i,
            'target': (i + 1) % n,
            'source_type': 'ring',
            'target_type': 'ring'
        }])
    
    # Layer 2: Star topology (node 0 is hub)
    for i in range(1, n):
        network.add_edges([{
            'source': 0,
            'target': i,
            'source_type': 'star',
            'target_type': 'star'
        }])
    
    # Add inter-layer connections (node replicas)
    for i in range(n):
        network.add_edges([{
            'source': i,
            'target': i,
            'source_type': 'ring',
            'target_type': 'star'
        }])
    
    return network


def run_random_walk_example() -> RandomWalkDynamics:
    """Run random walk simulation example."""
    print("=" * 70)
    print("Random Walk on Multilayer Network")
    print("=" * 70)
    
    # Create network
    network = create_two_layer_network()
    
    print(f"\nNetwork created:")
    print(f"  Nodes: {network.core_network.number_of_nodes()}")
    print(f"  Edges: {network.core_network.number_of_edges()}")
    
    # Create random walk
    walk = RandomWalkDynamics(
        network,
        start_node=(0, 'ring'),  # Start at node 0 in ring layer
        lazy_probability=0.1      # 10% chance to stay in place
    )
    
    print(f"\nRandom Walk Parameters:")
    print(f"  Start: (0, 'ring')")
    print(f"  Lazy probability: 0.1")
    
    # Set seed and run
    walk.set_seed(DEFAULT_SEED)
    print(f"\nRunning walk for 1000 steps...")
    results = walk.run(steps=1000)
    
    # Get trajectory
    trajectory = results.get_measure("trajectory")
    
    print(f"Walk complete!")
    print(f"  Trajectory length: {len(trajectory)}")
    
    # Analyze visit counts
    visit_counts = walk.visit_counts(trajectory)
    
    # Separate by layer
    ring_visits = {k: v for k, v in visit_counts.items() if k[1] == 'ring'}
    star_visits = {k: v for k, v in visit_counts.items() if k[1] == 'star'}
    
    print(f"\nVisit statistics:")
    print(f"  Ring layer total visits: {sum(ring_visits.values())}")
    print(f"  Star layer total visits: {sum(star_visits.values())}")
    print(f"  Most visited in ring: {max(ring_visits.items(), key=lambda x: x[1])}")
    print(f"  Most visited in star: {max(star_visits.items(), key=lambda x: x[1])}")
    
    # Plot results
    plot_visit_distribution(ring_visits, star_visits)
    
    return results


def plot_visit_distribution(
    ring_visits: Dict[Tuple[Hashable, str], int],
    star_visits: Dict[Tuple[Hashable, str], int],
) -> None:
    """Plot visit count distribution across layers (if matplotlib available)."""
    if plt is None:
        print(f"⚠️  Skipping plot: matplotlib not installed ({MATPLOTLIB_ERROR})")
        return

    output_dir = _ensure_output_dir()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Ring layer
    nodes_ring = sorted([k[0] for k in ring_visits.keys()])
    counts_ring = [ring_visits[(n, 'ring')] for n in nodes_ring]
    ax1.bar(nodes_ring, counts_ring, color='skyblue', edgecolor='black')
    ax1.set_xlabel('Node ID', fontsize=12)
    ax1.set_ylabel('Visit count', fontsize=12)
    ax1.set_title('Ring Layer Visit Distribution', fontsize=14, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)
    
    # Star layer
    nodes_star = sorted([k[0] for k in star_visits.keys()])
    counts_star = [star_visits[(n, 'star')] for n in nodes_star]
    ax2.bar(nodes_star, counts_star, color='lightcoral', edgecolor='black')
    ax2.set_xlabel('Node ID', fontsize=12)
    ax2.set_ylabel('Visit count', fontsize=12)
    ax2.set_title('Star Layer Visit Distribution', fontsize=14, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    filepath = output_dir / "random_walk_visits.png"
    plt.savefig(filepath, dpi=150, bbox_inches="tight")
    print(f"✓ Plot saved to {filepath}")


def analyze_layer_switching() -> None:
    """Analyze how often random walk switches between layers."""
    print("\n" + "=" * 70)
    print("Layer Switching Analysis")
    print("=" * 70)
    
    network = create_two_layer_network()
    
    # Run walk
    walk = RandomWalkDynamics(network, start_node=(0, 'ring'))
    walk.set_seed(DEFAULT_SEED)
    results = walk.run(steps=1000)
    trajectory = results.get_measure("trajectory")
    
    # Count layer switches
    switches = 0
    ring_time = 0
    star_time = 0
    
    for i in range(len(trajectory) - 1):
        current_layer = trajectory[i][1]
        next_layer = trajectory[i + 1][1]
        
        if current_layer == 'ring':
            ring_time += 1
        else:
            star_time += 1
        
        if current_layer != next_layer:
            switches += 1
    
    print(f"\nLayer switching statistics:")
    print(f"  Total switches: {switches}")
    print(f"  Switch rate: {switches / len(trajectory):.2%}")
    print(f"  Time in ring layer: {ring_time / len(trajectory):.2%}")
    print(f"  Time in star layer: {star_time / len(trajectory):.2%}")


def compare_lazy_probabilities() -> None:
    """Compare random walks with different lazy probabilities."""
    print("\n" + "=" * 70)
    print("Lazy Probability Comparison")
    print("=" * 70)
    
    # Use simple chain graph
    G = nx.path_graph(20)
    
    lazy_probs = [0.0, 0.2, 0.5, 0.8]
    
    if plt is None:
        print(f"⚠️  Skipping plot: matplotlib not installed ({MATPLOTLIB_ERROR})")
        return

    _ensure_output_dir()
    plt.figure(figsize=(12, 8))
    
    for lazy_p in lazy_probs:
        walk = RandomWalkDynamics(G, start_node=10, lazy_probability=lazy_p)
        walk.set_seed(DEFAULT_SEED)
        results = walk.run(steps=100)
        trajectory = results.get_measure("trajectory")
        
        plt.plot(trajectory, label=f'Lazy p={lazy_p}', linewidth=2, alpha=0.7)
    
    plt.xlabel('Time step', fontsize=12)
    plt.ylabel('Node position', fontsize=12)
    plt.title('Random Walk Trajectories with Different Lazy Probabilities',
              fontsize=14, fontweight='bold')
    plt.legend(fontsize=11)
    plt.grid(alpha=0.3)
    
    plt.tight_layout()
    filepath = OUTPUT_DIR / "lazy_walk_comparison.png"
    plt.savefig(filepath, dpi=150, bbox_inches="tight")
    print(f"✓ Comparison plot saved to {filepath}")


def estimate_hitting_times() -> None:
    """Estimate hitting times between nodes."""
    print("\n" + "=" * 70)
    print("Hitting Time Estimation")
    print("=" * 70)
    
    G = nx.karate_club_graph()
    
    # Estimate hitting time from node 0 to node 33
    source = 0
    target = 33
    n_trials = 100
    hitting_times = []
    
    for trial in range(n_trials):
        walk = RandomWalkDynamics(G, start_node=source)
        walk.set_seed(trial)
        
        # Run until we hit target (with max steps as safety)
        max_steps = 1000
        for step in range(max_steps):
            state = walk.step(source if step == 0 else state, step)
            if state == target:
                hitting_times.append(step + 1)
                break
        else:
            hitting_times.append(max_steps)  # Didn't hit within max_steps
    
    print(f"\nHitting time from node {source} to node {target}:")
    print(f"  Mean: {np.mean(hitting_times):.1f} steps")
    print(f"  Median: {np.median(hitting_times):.1f} steps")
    print(f"  Std: {np.std(hitting_times):.1f} steps")
    
    # Plot distribution
    if plt is None:
        print(f"⚠️  Skipping plot: matplotlib not installed ({MATPLOTLIB_ERROR})")
        return

    _ensure_output_dir()
    plt.figure(figsize=(10, 6))
    plt.hist(hitting_times, bins=30, edgecolor='black', alpha=0.7)
    plt.axvline(np.mean(hitting_times), color='red', linestyle='--',
                linewidth=2, label=f'Mean: {np.mean(hitting_times):.1f}')
    plt.xlabel('Hitting time (steps)', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.title(f'Hitting Time Distribution: Node {source} → Node {target}',
              fontsize=14, fontweight='bold')
    plt.legend(fontsize=11)
    plt.grid(alpha=0.3)
    
    plt.tight_layout()
    filepath = OUTPUT_DIR / "hitting_time_distribution.png"
    plt.savefig(filepath, dpi=150, bbox_inches="tight")
    print(f"✓ Distribution plot saved to {filepath}")


def main() -> int:
    """Execute all random walk demonstrations."""
    run_random_walk_example()
    analyze_layer_switching()
    compare_lazy_probabilities()
    estimate_hitting_times()

    print("\n" + "=" * 70)
    print("Example complete!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
