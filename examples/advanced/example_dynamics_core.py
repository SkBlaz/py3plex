"""
Example: Using the new dynamics core classes in py3plex

This example demonstrates the new OOP-style dynamics classes that complement
the existing high-level DSL/builder API.

The new classes provide:
1. DynamicsProcess - Base class for discrete-time dynamics
2. ContinuousTimeProcess - Base class for continuous-time (Gillespie) dynamics
3. Specific models: RandomWalk, SIS, SIR, SEIR, Adaptive SIS
4. Temporal network support
5. Config-based dynamics specification
"""

import networkx as nx
import matplotlib.pyplot as plt
from py3plex.dynamics import (
    RandomWalkDynamics,
    MultiRandomWalkDynamics,
    SISDynamics,
    AdaptiveSISDynamics,
    SIRDynamics,
    SEIRDynamics,
    SISContinuousTime,
    TemporalGraph,
    TemporalRandomWalk,
    build_dynamics_from_config,
)


def example_random_walk():
    """Example 1: Single-walker random walk on Karate Club graph."""
    print("\n" + "="*70)
    print("Example 1: Random Walk on Karate Club Network")
    print("="*70)
    
    # Create graph
    G = nx.karate_club_graph()
    
    # Create random walk dynamics
    walk = RandomWalkDynamics(
        G,
        seed=42,
        start_node=0,
        lazy_probability=0.1
    )
    
    # Run simulation
    trajectory = walk.run(steps=100)
    
    # Analyze visit counts
    counts = walk.visit_counts(trajectory)
    
    print(f"Walker started at node: {trajectory[0]}")
    print(f"Total steps: {len(trajectory) - 1}")
    print(f"Unique nodes visited: {len(counts)}")
    print(f"Most visited nodes: {sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]}")


def example_multi_walker():
    """Example 2: Multiple walkers with absorbing states."""
    print("\n" + "="*70)
    print("Example 2: Multiple Walkers with Absorbing States")
    print("="*70)
    
    # Create a small graph
    G = nx.karate_club_graph()
    
    # Create multi-walker dynamics with absorbing nodes
    walk = MultiRandomWalkDynamics(
        G,
        seed=42,
        n_walkers=5,
        absorbing_nodes={0, 33},  # Club leaders as absorbing states
    )
    
    # Run simulation
    trajectory = walk.run(steps=200)
    
    # Compute hitting time statistics
    stats = walk.hitting_time_statistics(trajectory)
    
    print(f"Number of walkers: 5")
    print(f"Absorbing nodes: {0, 33}")
    print(f"Walkers absorbed: {stats['absorbed_count']}/5")
    if stats['mean'] is not None:
        print(f"Mean hitting time: {stats['mean']:.2f} steps")
        print(f"Std hitting time: {stats['std']:.2f} steps")


def example_sis_epidemic():
    """Example 3: SIS epidemic dynamics."""
    print("\n" + "="*70)
    print("Example 3: SIS Epidemic Model")
    print("="*70)
    
    # Create graph
    G = nx.karate_club_graph()
    
    # Create SIS dynamics
    sis = SISDynamics(
        G,
        seed=42,
        beta=0.3,      # Infection probability
        mu=0.1,        # Recovery probability
        initial_infected=0.1,  # 10% initially infected
        backend='python'  # Can also use 'numpy' or 'torch'
    )
    
    # Run and get prevalence time series
    prevalence = sis.run_with_prevalence(steps=100)
    
    print(f"Initial prevalence: {prevalence[0]:.3f}")
    print(f"Final prevalence: {prevalence[-1]:.3f}")
    print(f"Peak prevalence: {max(prevalence):.3f}")
    print(f"Equilibrium reached: {abs(prevalence[-1] - prevalence[-10]) < 0.01}")


def example_adaptive_sis():
    """Example 4: Adaptive SIS with edge rewiring."""
    print("\n" + "="*70)
    print("Example 4: Adaptive SIS (Co-evolution)")
    print("="*70)
    
    # Create graph (must be mutable NetworkX graph)
    G = nx.karate_club_graph()
    initial_edges = G.number_of_edges()
    
    # Create adaptive SIS dynamics
    adaptive = AdaptiveSISDynamics(
        G,
        seed=42,
        beta=0.3,
        mu=0.1,
        w=0.1,  # Rewiring probability
        initial_infected=0.3
    )
    
    # Run simulation
    trajectory = adaptive.run(steps=50)
    
    # Analyze final state
    final_state = trajectory[-1]
    edge_counts = adaptive.edge_type_counts(final_state)
    
    print(f"Initial edges: {initial_edges}")
    print(f"Final edges: {G.number_of_edges()}")
    print(f"Edge types - S-S: {edge_counts['S-S']}, S-I: {edge_counts['S-I']}, I-I: {edge_counts['I-I']}")
    print(f"Prevalence: {adaptive.prevalence(final_state):.3f}")


def example_sir_dynamics():
    """Example 5: SIR compartmental model."""
    print("\n" + "="*70)
    print("Example 5: SIR Compartmental Model")
    print("="*70)
    
    # Create graph
    G = nx.karate_club_graph()
    
    # Create SIR dynamics
    sir = SIRDynamics(
        G,
        seed=42,
        beta=0.3,
        gamma=0.1,
        initial_infected=0.1
    )
    
    # Run simulation
    trajectory = sir.run(steps=100)
    
    # Analyze compartment evolution
    print("\nCompartment evolution:")
    for t in [0, 25, 50, 75, 100]:
        counts = sir.compartment_counts(trajectory[t])
        total = sum(counts.values())
        print(f"t={t:3d}: S={counts['S']:2d} ({counts['S']/total*100:5.1f}%), "
              f"I={counts['I']:2d} ({counts['I']/total*100:5.1f}%), "
              f"R={counts['R']:2d} ({counts['R']/total*100:5.1f}%)")


def example_continuous_time():
    """Example 6: Continuous-time SIS with Gillespie algorithm."""
    print("\n" + "="*70)
    print("Example 6: Continuous-Time SIS (Gillespie)")
    print("="*70)
    
    # Create small graph for visualization
    G = nx.karate_club_graph()
    
    # Create continuous-time SIS
    sis = SISContinuousTime(
        G,
        seed=42,
        beta=0.5,   # Infection rate
        mu=0.2,     # Recovery rate
        initial_infected=0.2
    )
    
    # Run until time 10
    trajectory, times = sis.run(t_max=10.0)
    
    print(f"Number of events: {len(trajectory)}")
    print(f"Simulation time: {times[-1]:.3f}")
    print(f"Initial prevalence: {sis.prevalence(trajectory[0]):.3f}")
    print(f"Final prevalence: {sis.prevalence(trajectory[-1]):.3f}")
    
    # Show some event times
    print(f"\nFirst 10 event times: {[f'{t:.3f}' for t in times[:10]]}")


def example_temporal_network():
    """Example 7: Random walk on temporal network."""
    print("\n" + "="*70)
    print("Example 7: Temporal Network Dynamics")
    print("="*70)
    
    # Create temporal graph snapshots
    snapshots = [
        nx.erdos_renyi_graph(10, 0.3, seed=i) for i in range(10)
    ]
    temporal = TemporalGraph(snapshots=snapshots)
    
    # Create temporal random walk
    walk = TemporalRandomWalk(
        temporal,
        seed=42,
        start_node=0
    )
    
    # Run for 9 steps (one less than number of snapshots)
    trajectory = walk.run(steps=9)
    
    print(f"Number of snapshots: {len(temporal)}")
    print(f"Starting node: {trajectory[0]}")
    print(f"Trajectory: {trajectory}")
    print(f"Note: Walker can only traverse edges present at each time step")


def example_config_based():
    """Example 8: Config-based dynamics specification."""
    print("\n" + "="*70)
    print("Example 8: Config-Based Dynamics")
    print("="*70)
    
    # Create graph
    G = nx.karate_club_graph()
    
    # Define SIS-like model via config
    config = {
        "type": "compartmental",
        "compartments": ["S", "I"],
        "parameters": {
            "beta": 0.3,
            "mu": 0.1
        },
        "rules": {
            "S": "infected_neighbors > 0 ? p=1-(1-beta)**infected_neighbors -> I : stay",
            "I": "p=mu -> S"  # With probability mu, recover to S (else stay)
        },
        "initial": {
            "I": 0.1
        }
    }
    
    # Build dynamics from config
    dynamics = build_dynamics_from_config(G, config)
    dynamics.set_seed(42)  # Set seed using the new method
    
    # Run simulation
    trajectory = dynamics.run(steps=50)
    
    initial_I = sum(1 for v in trajectory[0].values() if v == 'I')
    final_I = sum(1 for v in trajectory[-1].values() if v == 'I')
    
    print("Config-based SIS model:")
    print(f"  Initial infected: {initial_I}/{len(trajectory[0])}")
    print(f"  Final infected: {final_I}/{len(trajectory[-1])}")
    print(f"  Compartments: {config['compartments']}")
    print(f"  Parameters: {config['parameters']}")


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("PY3PLEX DYNAMICS CORE - EXAMPLES")
    print("="*70)
    print("\nThese examples demonstrate the new OOP-style dynamics classes")
    print("that complement the existing high-level DSL/builder API.\n")
    
    # Run all examples
    example_random_walk()
    example_multi_walker()
    example_sis_epidemic()
    example_adaptive_sis()
    example_sir_dynamics()
    example_continuous_time()
    example_temporal_network()
    example_config_based()
    
    print("\n" + "="*70)
    print("All examples completed!")
    print("="*70)


if __name__ == "__main__":
    main()
