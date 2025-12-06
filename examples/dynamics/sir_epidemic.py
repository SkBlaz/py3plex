"""
Example: SIR Epidemic Simulation using OOP-style Dynamics

This example demonstrates the use of the SIRDynamics class from the
py3plex.dynamics module, as described in the Practical Multilayer Network
Analysis with Py3plex book.

The example shows:
- Creating a multilayer network
- Setting up SIR dynamics with beta (infection) and gamma (recovery) parameters
- Running the simulation with a specific seed for reproducibility
- Extracting measures like prevalence and state counts
- Plotting the epidemic curve
"""

import networkx as nx
import matplotlib.pyplot as plt
from py3plex.core import multinet
from py3plex.dynamics import SIRDynamics


def create_simple_multilayer_network():
    """Create a simple two-layer network for demonstration.
    
    Returns:
        py3plex multi_layer_network object
    """
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
    rng = np.random.default_rng(42)
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


def run_sir_example():
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
    sir.set_seed(42)
    
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


def plot_epidemic_curve(prevalence, state_counts):
    """Plot the epidemic curve showing S, I, R over time.
    
    Args:
        prevalence: Array of prevalence values over time
        state_counts: Dictionary of state -> count arrays
    """
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
    plt.savefig('/tmp/sir_epidemic_example.png', dpi=150, bbox_inches='tight')
    print(f"\n✓ Plot saved to /tmp/sir_epidemic_example.png")
    
    # Try to display if in interactive mode
    try:
        plt.show()
    except:
        pass


def run_comparison_with_different_parameters():
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
    
    plt.figure(figsize=(12, 8))
    
    for params in param_sets:
        sir = SIRDynamics(G, beta=params['beta'], gamma=params['gamma'], initial_infected=0.1)
        sir.set_seed(42)
        results = sir.run(steps=50)
        
        prevalence = results.get_measure("prevalence")
        plt.plot(prevalence, label=params['label'], linewidth=2)
    
    plt.xlabel('Time step', fontsize=12)
    plt.ylabel('Prevalence', fontsize=12)
    plt.title('SIR Dynamics with Different Parameters', fontsize=14, fontweight='bold')
    plt.legend(fontsize=11)
    plt.grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('/tmp/sir_parameter_comparison.png', dpi=150, bbox_inches='tight')
    print(f"✓ Comparison plot saved to /tmp/sir_parameter_comparison.png")


if __name__ == "__main__":
    # Run main example
    results = run_sir_example()
    
    # Run parameter comparison
    run_comparison_with_different_parameters()
    
    print("\n" + "=" * 70)
    print("Example complete!")
    print("=" * 70)
