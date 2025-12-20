"""
SIR epidemic simulation with py3plex dynamics.

Shows how to create a small multilayer network, configure `SIRDynamics`, run a
reproducible simulation, and visualize prevalence curves. Prerequisites:
py3plex installed with dynamics extras, plus numpy, networkx; matplotlib is
optional for plots (Agg backend).

Quickstart (from repo root):
- python -m pip install -e ".[dev]"        # install py3plex + dependencies
- python docs/_downloads/b240507cb6a9f6e0b9fc5d743f73d786/sir_epidemic.py
"""

from __future__ import annotations

from pathlib import Path

import networkx as nx
import numpy as np
from py3plex.core import multinet
from py3plex.dynamics import SIRDynamics

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


def create_simple_multilayer_network() -> multinet.multi_layer_network:
    """Create a simple two-layer network for demonstration."""
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes to both layers
    nodes = []
    for i in range(20):
        nodes.append({'source': i, 'type': 'physical'})
        nodes.append({'source': i, 'type': 'digital'})
    
    network.add_nodes(nodes)
    
    # Physical layer: local ring structure
    for i in range(20):
        network.add_edges([{
            'source': i,
            'target': (i + 1) % 20,
            'source_type': 'physical',
            'target_type': 'physical'
        }])
    
    # Digital layer: random connections
    rng = np.random.default_rng(DEFAULT_SEED)
    for i in range(30):  # Add 30 random edges
        source = rng.integers(0, 20)
        target = rng.integers(0, 20)
        if source != target:
            network.add_edges([{
                'source': source,
                'target': target,
                'source_type': 'digital',
                'target_type': 'digital'
            }])
    
    return network


def run_sir_example() -> SIRDynamics:
    """Run SIR epidemic simulation example."""
    print("=" * 70)
    print("SIR Epidemic Simulation Example")
    print("=" * 70)
    
    # Create network
    network = create_simple_multilayer_network()
    
    print(f"\nNetwork created:")
    print(f"  Nodes: {network.core_network.number_of_nodes()}")
    print(f"  Edges: {network.core_network.number_of_edges()}")
    
    # Create SIR dynamics
    # beta: infection probability per contact
    # gamma: recovery probability
    # initial_infected: fraction of nodes initially infected
    sir = SIRDynamics(
        network,
        beta=0.3,
        gamma=0.1,
        initial_infected=0.05
    )
    
    print(f"\nSIR Parameters:")
    print(f"  β (beta): 0.3")
    print(f"  γ (gamma): 0.1")
    print(f"  Initial infected: 5%")
    
    # Set seed for reproducibility
    sir.set_seed(DEFAULT_SEED)
    
    # Run simulation
    print(f"\nRunning simulation for 100 steps...")
    results = sir.run(steps=100)
    
    print(f"Simulation complete!")
    print(f"  Result type: {type(results).__name__}")
    print(f"  Trajectory length: {len(results)}")
    
    # Extract measures using the book-style API
    prevalence = results.get_measure("prevalence")
    state_counts = results.get_measure("state_counts")
    
    print(f"\nEpidemic statistics:")
    print(f"  Peak prevalence: {prevalence.max():.2%} at step {prevalence.argmax()}")
    print(f"  Final recovered: {state_counts['R'][-1]} nodes")
    print(f"  Attack rate: {state_counts['R'][-1] / network.core_network.number_of_nodes():.2%}")
    
    # Plot results
    plot_epidemic_curve(prevalence, state_counts)
    
    return results


def plot_epidemic_curve(prevalence, state_counts) -> None:
    """Plot the epidemic curve showing S, I, R over time (if matplotlib available)."""
    if plt is None:
        print(f"⚠️  Skipping plot: matplotlib not installed ({MATPLOTLIB_ERROR})")
        return

    output_dir = _ensure_output_dir()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Plot state counts
    steps = range(len(state_counts['S']))
    ax1.plot(steps, state_counts['S'], label='Susceptible', color='blue', linewidth=2)
    ax1.plot(steps, state_counts['I'], label='Infected', color='red', linewidth=2)
    ax1.plot(steps, state_counts['R'], label='Recovered', color='green', linewidth=2)
    ax1.set_xlabel('Time step', fontsize=12)
    ax1.set_ylabel('Number of nodes', fontsize=12)
    ax1.set_title('SIR Epidemic Dynamics', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=11)
    ax1.grid(alpha=0.3)
    
    # Plot prevalence
    ax2.plot(steps, prevalence, color='red', linewidth=2)
    ax2.fill_between(steps, 0, prevalence, alpha=0.3, color='red')
    ax2.set_xlabel('Time step', fontsize=12)
    ax2.set_ylabel('Prevalence (fraction infected)', fontsize=12)
    ax2.set_title('Infection Prevalence Over Time', fontsize=14, fontweight='bold')
    ax2.grid(alpha=0.3)
    
    plt.tight_layout()
    filepath = output_dir / "sir_epidemic_example.png"
    plt.savefig(filepath, dpi=150, bbox_inches="tight")
    print(f"\n✓ Plot saved to {filepath}")


def run_comparison_with_different_parameters() -> None:
    """Compare SIR dynamics with different parameter settings."""
    print("\n" + "=" * 70)
    print("Parameter Comparison")
    print("=" * 70)
    
    # Use a simple network for quick comparison
    G = nx.karate_club_graph()
    
    # Test different parameter combinations
    param_sets = [
        {'beta': 0.2, 'gamma': 0.1, 'label': 'Low transmission'},
        {'beta': 0.4, 'gamma': 0.1, 'label': 'High transmission'},
        {'beta': 0.3, 'gamma': 0.05, 'label': 'Slow recovery'},
        {'beta': 0.3, 'gamma': 0.2, 'label': 'Fast recovery'},
    ]
    
    if plt is None:
        print(f"⚠️  Skipping plot: matplotlib not installed ({MATPLOTLIB_ERROR})")
        return

    _ensure_output_dir()
    plt.figure(figsize=(12, 8))
    
    for params in param_sets:
        sir = SIRDynamics(G, beta=params['beta'], gamma=params['gamma'], initial_infected=0.1)
        sir.set_seed(DEFAULT_SEED)
        results = sir.run(steps=50)
        
        prevalence = results.get_measure("prevalence")
        plt.plot(prevalence, label=params['label'], linewidth=2)
    
    plt.xlabel('Time step', fontsize=12)
    plt.ylabel('Prevalence', fontsize=12)
    plt.title('SIR Dynamics with Different Parameters', fontsize=14, fontweight='bold')
    plt.legend(fontsize=11)
    plt.grid(alpha=0.3)
    
    plt.tight_layout()
    filepath = OUTPUT_DIR / "sir_parameter_comparison.png"
    plt.savefig(filepath, dpi=150, bbox_inches="tight")
    print(f"✓ Comparison plot saved to {filepath}")


def main() -> int:
    """Execute all SIR demonstrations."""
    run_sir_example()
    run_comparison_with_different_parameters()

    print("\n" + "=" * 70)
    print("Example complete!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
