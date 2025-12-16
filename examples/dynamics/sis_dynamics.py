"""
SIS epidemic simulation with py3plex dynamics.

Highlights the difference from SIR (no lasting immunity), explores endemic
behavior, and compares parameter regimes. Prerequisites: py3plex installed
with dynamics extras, plus networkx; matplotlib is optional for plots (Agg
backend).
"""

from __future__ import annotations

from pathlib import Path

import networkx as nx
from py3plex.dynamics import SISDynamics

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


def run_sis_example() -> SISDynamics:
    """Run SIS epidemic simulation example."""
    print("=" * 70)
    print("SIS Epidemic Simulation Example")
    print("=" * 70)
    
    # Create a small-world network (realistic for many epidemics)
    G = nx.watts_strogatz_graph(n=100, k=6, p=0.1, seed=42)
    
    print(f"\nNetwork: Watts-Strogatz small-world")
    print(f"  Nodes: {G.number_of_nodes()}")
    print(f"  Edges: {G.number_of_edges()}")
    print(f"  Average degree: {2 * G.number_of_edges() / G.number_of_nodes():.2f}")
    
    # Create SIS dynamics
    sis = SISDynamics(
        G,
        beta=0.3,      # Infection rate
        gamma=0.1,     # Recovery rate
        initial_infected=0.05
    )
    
    print(f"\nSIS Parameters:")
    print(f"  β (beta): 0.3")
    print(f"  γ (gamma): 0.1")
    print(f"  Initial infected: 5%")
    print(f"  R₀ estimate: β/γ * <k> = {0.3/0.1 * 6:.2f}")
    
    # Set seed and run
    sis.set_seed(DEFAULT_SEED)
    print(f"\nRunning simulation for 200 steps...")
    results = sis.run(steps=200)
    
    # Extract measures
    prevalence = results.get_measure("prevalence")
    state_counts = results.get_measure("state_counts")
    
    print(f"\nSimulation complete!")
    print(f"  Mean prevalence (last 50 steps): {prevalence[-50:].mean():.2%}")
    print(f"  Std prevalence (last 50 steps): {prevalence[-50:].std():.2%}")
    
    # Plot results
    plot_sis_dynamics(prevalence, state_counts)
    
    return results


def plot_sis_dynamics(prevalence, state_counts) -> None:
    """Plot SIS epidemic dynamics (if matplotlib available)."""
    if plt is None:
        print(f"⚠️  Skipping plot: matplotlib not installed ({MATPLOTLIB_ERROR})")
        return

    output_dir = _ensure_output_dir()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Plot state counts
    steps = range(len(state_counts['S']))
    ax1.plot(steps, state_counts['S'], label='Susceptible', color='blue', linewidth=2)
    ax1.plot(steps, state_counts['I'], label='Infected', color='red', linewidth=2)
    ax1.set_xlabel('Time step', fontsize=12)
    ax1.set_ylabel('Number of nodes', fontsize=12)
    ax1.set_title('SIS Epidemic Dynamics', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=11)
    ax1.grid(alpha=0.3)
    
    # Plot prevalence with endemic equilibrium
    ax2.plot(steps, prevalence, color='red', linewidth=2, alpha=0.7)
    # Add horizontal line at mean endemic level (last 50 steps)
    endemic_level = prevalence[-50:].mean()
    ax2.axhline(endemic_level, color='green', linestyle='--', linewidth=2,
                label=f'Endemic equilibrium: {endemic_level:.2%}')
    ax2.fill_between(steps, 0, prevalence, alpha=0.3, color='red')
    ax2.set_xlabel('Time step', fontsize=12)
    ax2.set_ylabel('Prevalence (fraction infected)', fontsize=12)
    ax2.set_title('Infection Prevalence Over Time', fontsize=14, fontweight='bold')
    ax2.legend(fontsize=11)
    ax2.grid(alpha=0.3)
    
    plt.tight_layout()
    filepath = output_dir / "sis_dynamics_example.png"
    plt.savefig(filepath, dpi=150, bbox_inches="tight")
    print(f"✓ Plot saved to {filepath}")


def compare_sis_vs_sir() -> None:
    """Compare SIS and SIR dynamics on the same network."""
    print("\n" + "=" * 70)
    print("SIS vs SIR Comparison")
    print("=" * 70)
    
    from py3plex.dynamics import SIRDynamics
    
    # Use same network for fair comparison
    G = nx.karate_club_graph()
    
    # SIS dynamics
    sis = SISDynamics(G, beta=0.3, gamma=0.1, initial_infected=0.1)
    sis.set_seed(DEFAULT_SEED)
    sis_results = sis.run(steps=100)
    sis_prevalence = sis_results.get_measure("prevalence")
    
    # SIR dynamics
    sir = SIRDynamics(G, beta=0.3, gamma=0.1, initial_infected=0.1)
    sir.set_seed(DEFAULT_SEED)
    sir_results = sir.run(steps=100)
    sir_prevalence = sir_results.get_measure("prevalence")
    
    # Plot comparison
    if plt is None:
        print(f"⚠️  Skipping plot: matplotlib not installed ({MATPLOTLIB_ERROR})")
        return

    _ensure_output_dir()
    plt.figure(figsize=(10, 6))
    plt.plot(sis_prevalence, label='SIS (no immunity)', color='red', linewidth=2)
    plt.plot(sir_prevalence, label='SIR (with immunity)', color='blue', linewidth=2)
    plt.xlabel('Time step', fontsize=12)
    plt.ylabel('Prevalence', fontsize=12)
    plt.title('SIS vs SIR Epidemic Dynamics', fontsize=14, fontweight='bold')
    plt.legend(fontsize=11)
    plt.grid(alpha=0.3)
    
    plt.tight_layout()
    filepath = OUTPUT_DIR / "sis_vs_sir_comparison.png"
    plt.savefig(filepath, dpi=150, bbox_inches="tight")
    print(f"✓ Comparison plot saved to {filepath}")
    
    print(f"\nKey differences:")
    print(f"  SIS reaches endemic equilibrium: {sis_prevalence[-1]:.2%}")
    print(f"  SIR dies out: {sir_prevalence[-1]:.2%}")


def analyze_endemic_threshold() -> None:
    """Analyze the epidemic threshold for SIS dynamics."""
    print("\n" + "=" * 70)
    print("Endemic Threshold Analysis")
    print("=" * 70)
    
    G = nx.karate_club_graph()
    avg_degree = 2 * G.number_of_edges() / G.number_of_nodes()
    
    # Theory: endemic state exists when β/γ > 1/<k>
    # Or equivalently: R₀ = β/γ * <k> > 1
    
    gamma = 0.1
    beta_values = [0.01, 0.02, 0.03, 0.05, 0.1, 0.2, 0.3]
    
    final_prevalence = []
    
    for beta in beta_values:
        sis = SISDynamics(G, beta=beta, gamma=gamma, initial_infected=0.1)
        sis.set_seed(DEFAULT_SEED)
        results = sis.run(steps=200)
        prevalence = results.get_measure("prevalence")
        # Take mean of last 50 steps as endemic level
        final_prevalence.append(prevalence[-50:].mean())
    
    # Calculate R0 for each beta
    R0_values = [beta / gamma * avg_degree for beta in beta_values]
    
    # Plot
    if plt is None:
        print(f"⚠️  Skipping plot: matplotlib not installed ({MATPLOTLIB_ERROR})")
        return

    _ensure_output_dir()
    plt.figure(figsize=(10, 6))
    plt.plot(R0_values, final_prevalence, 'o-', linewidth=2, markersize=8)
    plt.axvline(1.0, color='red', linestyle='--', linewidth=2, label='Epidemic threshold (R₀=1)')
    plt.axhline(0.0, color='gray', linestyle=':', alpha=0.5)
    plt.xlabel('R₀ (basic reproduction number)', fontsize=12)
    plt.ylabel('Endemic prevalence', fontsize=12)
    plt.title('Endemic Threshold in SIS Dynamics', fontsize=14, fontweight='bold')
    plt.legend(fontsize=11)
    plt.grid(alpha=0.3)
    
    plt.tight_layout()
    filepath = OUTPUT_DIR / "sis_threshold_analysis.png"
    plt.savefig(filepath, dpi=150, bbox_inches="tight")
    print(f"✓ Threshold plot saved to {filepath}")
    
    print(f"\nResults:")
    for beta, R0, prev in zip(beta_values, R0_values, final_prevalence):
        status = "endemic" if prev > 0.01 else "extinct"
        print(f"  β={beta:.2f}, R₀={R0:.2f}: prevalence={prev:.2%} ({status})")


def main() -> int:
    """Execute all SIS demonstrations."""
    run_sis_example()
    compare_sis_vs_sir()
    analyze_endemic_threshold()

    print("\n" + "=" * 70)
    print("Example complete!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
