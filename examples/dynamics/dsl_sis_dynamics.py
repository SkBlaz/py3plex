"""
SIS epidemic simulation using DSL builder API.

Demonstrates Q.dynamics() DSL interface for SIS (Susceptible-Infected-Susceptible)
epidemic, where nodes can be reinfected. Shows endemic equilibrium behavior and
parameter sensitivity using the declarative builder pattern.

This complements the traditional SISDynamics class approach shown in
sis_dynamics.py with a more concise DSL-style interface.

Runtime: FAST (<1 second)
"""

from __future__ import annotations

from pathlib import Path

import networkx as nx
from py3plex.core import multinet
from py3plex.dsl import Q, L

try:  # Matplotlib is optional
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


def create_network() -> multinet.multi_layer_network:
    """Create a simple network for SIS demonstration."""
    network = multinet.multi_layer_network(directed=False)

    # Single layer with 20 nodes
    nodes = [{"source": i, "type": "network"} for i in range(20)]
    network.add_nodes(nodes)

    # Create a small-world-like structure
    edges = []
    # Ring
    for i in range(20):
        edges.append(
            {
                "source": i,
                "target": (i + 1) % 20,
                "source_type": "network",
                "target_type": "network",
            }
        )
    # Random shortcuts
    edges.extend(
        [
            {"source": 0, "target": 10, "source_type": "network", "target_type": "network"},
            {"source": 5, "target": 15, "source_type": "network", "target_type": "network"},
            {"source": 3, "target": 17, "source_type": "network", "target_type": "network"},
        ]
    )

    network.add_edges(edges)
    return network


def run_dsl_sis_examples():
    """Run SIS epidemic examples using DSL."""
    print("=" * 70)
    print("DSL-Based SIS Epidemic Simulation")
    print("=" * 70)

    net = create_network()
    nodes = list(net.get_nodes())
    edges = list(net.get_edges())
    print(f"\nNetwork: {len(nodes)} nodes, {len(edges)} edges")

    # Example 1: Sub-critical regime (dies out)
    print("\n--- Example 1: Sub-critical regime (beta/mu < threshold) ---")
    result_sub = (
        Q.dynamics("SIS", beta=0.1, mu=0.2)  # Low infection, high recovery
        .on_layers(L["network"])
        .seed_infections(fraction=0.2)  # Start with 20% infected
        .run(steps=100, replicates=10)
        .execute(net)
    )

    traj_sub = result_sub.trajectories
    final_sub = traj_sub[traj_sub["step"] > 80].groupby("step").mean()
    avg_infected_sub = final_sub["infected"].mean()
    print(f"Endemic equilibrium infected: {avg_infected_sub:.2f} (expected: ~0)")

    # Example 2: Super-critical regime (endemic)
    print("\n--- Example 2: Super-critical regime (beta/mu > threshold) ---")
    result_super = (
        Q.dynamics("SIS", beta=0.4, mu=0.1)  # High infection, low recovery
        .on_layers(L["network"])
        .seed_infections(fraction=0.2)
        .run(steps=100, replicates=10)
        .execute(net)
    )

    traj_super = result_super.trajectories
    final_super = traj_super[traj_super["step"] > 80].groupby("step").mean()
    avg_infected_super = final_super["infected"].mean()
    print(f"Endemic equilibrium infected: {avg_infected_super:.2f} (expected: >0)")

    # Example 3: Critical regime (near threshold)
    print("\n--- Example 3: Near-critical regime ---")
    result_critical = (
        Q.dynamics("SIS", beta=0.25, mu=0.15)
        .on_layers(L["network"])
        .seed_infections(fraction=0.2)
        .run(steps=100, replicates=10)
        .execute(net)
    )

    traj_critical = result_critical.trajectories
    final_critical = traj_critical[traj_critical["step"] > 80].groupby("step").mean()
    avg_infected_critical = final_critical["infected"].mean()
    print(f"Endemic equilibrium infected: {avg_infected_critical:.2f}")

    print("\nKey insight:")
    print("  SIS dynamics reach endemic equilibrium (not extinction like SIR)")
    print("  Critical threshold depends on network structure and beta/mu ratio")

    # Optional: Plot if matplotlib available
    if plt is not None:
        _plot_sis_regimes(traj_sub, traj_super, traj_critical)

    return result_sub, result_super, result_critical


def _plot_sis_regimes(traj_sub, traj_super, traj_critical):
    """Plot SIS dynamics in different regimes."""
    out_dir = _ensure_output_dir()

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    def plot_traj(ax, traj, title, beta, mu):
        df = traj.groupby("step").mean()
        ax.plot(df.index, df["susceptible"], label="Susceptible", color="blue", alpha=0.7)
        ax.plot(df.index, df["infected"], label="Infected", color="red")
        ax.set_xlabel("Time step")
        ax.set_ylabel("Count")
        ax.set_title(f"{title}\n(β={beta}, μ={mu})")
        ax.legend()
        ax.grid(True, alpha=0.3)

    plot_traj(axes[0], traj_sub, "Sub-critical", 0.1, 0.2)
    plot_traj(axes[1], traj_super, "Super-critical", 0.4, 0.1)
    plot_traj(axes[2], traj_critical, "Near-critical", 0.25, 0.15)

    plt.tight_layout()
    output_path = out_dir / "dsl_sis_regimes.png"
    plt.savefig(output_path, dpi=100, bbox_inches="tight")
    print(f"\nPlot saved to: {output_path}")
    plt.close()


def main():
    """Run all DSL SIS examples."""
    try:
        run_dsl_sis_examples()
        print("\n" + "=" * 70)
        print("DSL SIS examples completed successfully!")
        print("=" * 70)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
