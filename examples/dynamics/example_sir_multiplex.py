"""
Example: SIR Epidemic Simulation on Multiplex Networks

This example demonstrates the use of the SIR epidemic simulator
on multiplex networks with multiple interaction layers.
"""

import numpy as np
import scipy.sparse
from py3plex.algorithms.sir_multiplex import (
    simulate_sir_multiplex_discrete,
    simulate_sir_multiplex_gillespie,
    basic_reproduction_number,
    summarize
)

def create_multiplex_network(N, seed=42):
    """Create a simple two-layer multiplex network."""
    np.random.seed(seed)
    
    # Layer 1: Ring network (local contacts)
    edges1 = [(i, (i+1) % N) for i in range(N)]
    edges1 += [((i+1) % N, i) for i in range(N)]  # Make symmetric
    row1, col1 = zip(*edges1)
    A1 = scipy.sparse.csr_matrix((np.ones(len(edges1)), (row1, col1)), shape=(N, N))
    
    # Layer 2: Random network (distant contacts)
    edges2 = [(i, j) for i in range(N) for j in range(N) 
              if i != j and np.random.random() < 0.1]
    if edges2:
        row2, col2 = zip(*edges2)
        A2 = scipy.sparse.csr_matrix((np.ones(len(edges2)), (row2, col2)), shape=(N, N))
    else:
        A2 = scipy.sparse.csr_matrix((N, N))
    
    return [A1, A2]

def main():
    print("=" * 70)
    print("SIR Epidemic Simulation on Multiplex Networks")
    print("=" * 70)
    
    # Create network
    N = 50
    A_layers = create_multiplex_network(N)
    
    print(f"\nNetwork: N={N} nodes, L={len(A_layers)} layers")
    for i, A in enumerate(A_layers):
        print(f"  Layer {i}: {A.nnz} edges")
    
    # Parameters
    beta = np.array([0.3, 0.15])  # Transmission rates per layer
    gamma = 0.2  # Recovery rate
    layer_weights = np.array([1.0, 0.5])  # Layer importance
    
    print(f"\nParameters:")
    print(f"  β (transmission): {beta}")
    print(f"  γ (recovery): {gamma}")
    print(f"  Layer weights: {layer_weights}")
    
    # Compute R0
    R0 = basic_reproduction_number(A_layers, beta, gamma, layer_weights)
    print(f"\nBasic reproduction number R₀ ≈ {R0:.3f}")
    
    # Discrete-time simulation
    print("\n" + "=" * 70)
    print("Discrete-Time Simulation")
    print("=" * 70)
    
    result_discrete = simulate_sir_multiplex_discrete(
        A_layers=A_layers,
        beta=beta,
        gamma=gamma,
        layer_weights=layer_weights,
        dt=0.5,
        steps=100,
        rng_seed=42,
        return_layer_incidence=True
    )
    
    summary_discrete = summarize(result_discrete)
    print(f"\nResults:")
    print(f"  Peak prevalence: {summary_discrete['peak_prevalence']} at t={summary_discrete['peak_time']:.1f}")
    print(f"  Attack rate: {summary_discrete['attack_rate']:.1%}")
    print(f"  Total infections: {summary_discrete['total_infections']}")
    
    if summary_discrete.get('layer_contributions'):
        print(f"  Layer contributions:")
        for i, contrib in enumerate(summary_discrete['layer_contributions']):
            print(f"    Layer {i}: {contrib:.1%}")
    
    # Gillespie simulation
    print("\n" + "=" * 70)
    print("Gillespie (Continuous-Time) Simulation")
    print("=" * 70)
    
    result_gillespie = simulate_sir_multiplex_gillespie(
        A_layers=A_layers,
        beta=beta,
        gamma=gamma,
        layer_weights=layer_weights,
        t_max=50.0,
        rng_seed=42,
        return_event_log=True,
        return_layer_incidence=True
    )
    
    summary_gillespie = summarize(result_gillespie)
    print(f"\nResults:")
    print(f"  Peak prevalence: {summary_gillespie['peak_prevalence']} at t={summary_gillespie['peak_time']:.1f}")
    print(f"  Attack rate: {summary_gillespie['attack_rate']:.1%}")
    print(f"  Total infections: {summary_gillespie['total_infections']}")
    print(f"  Total events: {len(result_gillespie.events)}")
    
    if summary_gillespie.get('layer_contributions'):
        print(f"  Layer contributions:")
        for i, contrib in enumerate(summary_gillespie['layer_contributions']):
            print(f"    Layer {i}: {contrib:.1%}")
    
    print("\n  Sample events:")
    for i, (t, event_type, node, layer) in enumerate(result_gillespie.events[:5]):
        layer_str = f"layer {layer}" if layer is not None else "N/A"
        print(f"    t={t:6.2f}: {event_type:10s} node={node:2d} ({layer_str})")
    
    # Comparison of importation scenarios
    print("\n" + "=" * 70)
    print("Effect of Exogenous Importations")
    print("=" * 70)
    
    # With imports
    result_with_import = simulate_sir_multiplex_discrete(
        A_layers=A_layers,
        beta=beta * 0.5,  # Lower transmission
        gamma=gamma,
        layer_weights=layer_weights,
        dt=0.5,
        steps=100,
        import_rate=0.01,  # Small import rate
        rng_seed=42
    )
    
    # Without imports
    result_no_import = simulate_sir_multiplex_discrete(
        A_layers=A_layers,
        beta=beta * 0.5,
        gamma=gamma,
        layer_weights=layer_weights,
        dt=0.5,
        steps=100,
        import_rate=0.0,
        rng_seed=42
    )
    
    print(f"\nWith low transmission (β/2):")
    print(f"  Without imports: {result_no_import.R[-1]}/{N} infected ({result_no_import.R[-1]/N:.1%})")
    print(f"  With imports:    {result_with_import.R[-1]}/{N} infected ({result_with_import.R[-1]/N:.1%})")
    
    print("\n" + "=" * 70)
    print("Simulation completed successfully!")
    print("=" * 70)

if __name__ == "__main__":
    main()
