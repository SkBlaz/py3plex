"""
SIR epidemic simulation using DSL builder API.

Demonstrates the Q.dynamics() DSL interface for running epidemic simulations
with minimal boilerplate. Shows how to configure SIR dynamics, seed infections,
run replicates, and extract results using the builder pattern.

This complements the traditional SIRDynamics class approach shown in
sir_epidemic.py with a more declarative DSL-style interface.

Runtime: FAST (<1 second)
"""

from __future__ import annotations

from pathlib import Path

import networkx as nx
from py3plex.core import multinet
from py3plex.dsl import Q, L

try:  # Matplotlib is optional; skip plots if missing.
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError as exc:  # pragma: no cover
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


def create_simple_network() -> multinet.multi_layer_network:
    """Create a simple two-layer network for epidemic simulation."""
    network = multinet.multi_layer_network(directed=False)

    # Add nodes to both layers
    nodes = []
    for i in range(15):
        nodes.append({"source": i, "type": "contact"})
        nodes.append({"source": i, "type": "social"})

    network.add_nodes(nodes)

    # Contact layer: ring structure (close physical contact)
    edges = []
    for i in range(15):
        edges.append(
            {
                "source": i,
                "target": (i + 1) % 15,
                "source_type": "contact",
                "target_type": "contact",
            }
        )

    # Social layer: more connected (casual interactions)
    for i in range(15):
        for j in range(i + 1, min(i + 4, 15)):
            edges.append(
                {
                    "source": i,
                    "target": j,
                    "source_type": "social",
                    "target_type": "social",
                }
            )

    network.add_edges(edges)
    return network


def run_dsl_sir_example():
    """Run SIR epidemic using DSL builder API."""
    print("=" * 70)
    print("DSL-Based SIR Epidemic Simulation")
    print("=" * 70)

    # Create network
    net = create_simple_network()
    nodes = list(net.get_nodes())
    edges = list(net.get_edges())
    print(f"\nNetwork: {len(nodes)} nodes, {len(edges)} edges")
    print(f"Layers: {net.get_layers()}")

    # Example 1: Basic SIR on contact layer
    print("\n--- Example 1: SIR on contact layer ---")
    result = (
        Q.dynamics("SIR", beta=0.3, gamma=0.1)
        .on_layers(L["contact"])
        .seed_infections(fraction=0.1)  # 10% initially infected
        .run(steps=50, replicates=5)
        .execute(net)
    )

    # Extract trajectories
    trajectories = result.trajectories
    print(f"Simulation completed: {len(trajectories)} timesteps")
    print(f"Final state (mean across replicates):")
    final = trajectories.groupby("step").mean().iloc[-1]
    print(f"  Susceptible: {final['susceptible']:.1f}")
    print(f"  Infected: {final['infected']:.1f}")
    print(f"  Recovered: {final['recovered']:.1f}")

    # Example 2: SIR on both layers (multilayer dynamics)
    print("\n--- Example 2: SIR on both layers ---")
    result_multi = (
        Q.dynamics("SIR", beta=0.25, gamma=0.15)
        .on_layers(L["contact"] + L["social"])  # Both layers
        .seed_infections(nodes=[(0, "contact"), (7, "social")])  # Specific nodes
        .run(steps=50, replicates=5)
        .execute(net)
    )

    trajectories_multi = result_multi.trajectories
    final_multi = trajectories_multi.groupby("step").mean().iloc[-1]
    print(f"Final state (multilayer):")
    print(f"  Susceptible: {final_multi['susceptible']:.1f}")
    print(f"  Infected: {final_multi['infected']:.1f}")
    print(f"  Recovered: {final_multi['recovered']:.1f}")

    # Example 3: Compare contact vs social layer dynamics
    print("\n--- Example 3: Layer comparison ---")
    result_social = (
        Q.dynamics("SIR", beta=0.3, gamma=0.1)
        .on_layers(L["social"])
        .seed_infections(fraction=0.1)
        .run(steps=50, replicates=5)
        .execute(net)
    )

    traj_social = result_social.trajectories
    final_social = traj_social.groupby("step").mean().iloc[-1]

    print("Contact layer (ring):")
    print(f"  Final recovered: {final['recovered']:.1f}")
    print("Social layer (more connected):")
    print(f"  Final recovered: {final_social['recovered']:.1f}")
    print(
        "\nNote: More connected social layer leads to faster/larger epidemic spread"
    )

    # Optional: Plot results if matplotlib available
    if plt is not None:
        _plot_comparison(trajectories, trajectories_multi, traj_social)

    return result, result_multi, result_social


def _plot_comparison(traj_contact, traj_multi, traj_social):
    """Plot epidemic curves for comparison."""
    out_dir = _ensure_output_dir()

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    # Helper to plot trajectory
    def plot_traj(ax, traj, title):
        df = traj.groupby("step").mean()
        ax.plot(df.index, df["susceptible"], label="Susceptible", color="blue")
        ax.plot(df.index, df["infected"], label="Infected", color="red")
        ax.plot(df.index, df["recovered"], label="Recovered", color="green")
        ax.set_xlabel("Time step")
        ax.set_ylabel("Count")
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=0.3)

    plot_traj(axes[0], traj_contact, "Contact Layer")
    plot_traj(axes[1], traj_multi, "Both Layers")
    plot_traj(axes[2], traj_social, "Social Layer")

    plt.tight_layout()
    output_path = out_dir / "dsl_sir_comparison.png"
    plt.savefig(output_path, dpi=100, bbox_inches="tight")
    print(f"\nPlot saved to: {output_path}")
    plt.close()


def main():
    """Run all DSL SIR examples."""
    try:
        run_dsl_sir_example()
        print("\n" + "=" * 70)
        print("DSL SIR examples completed successfully!")
        print("=" * 70)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
