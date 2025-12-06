"""Example: DSL-Based Dynamics Simulation on Multilayer Networks

This example demonstrates the declarative DSL for dynamics simulations on
multilayer networks. The DSL provides a composable, type-safe API for:

1. Specifying dynamical processes (SIS, SIR, RandomWalk)
2. Configuring initial conditions
3. Running simulations with replicates
4. Measuring epidemic/dynamics properties
5. Integrating with the query DSL for layer selection

The dynamics DSL follows the same design philosophy as the query DSL:
declarative, chainable, and type-safe.

Mathematical Formalism:
-----------------------

SIS Model (Susceptible-Infected-Susceptible):
    States: S (susceptible), I (infected)
    Update rules:
        - S → I with probability λ_i = 1 - ∏_j (1 - β)^(A_ij · I_j)
        - I → S with probability μ
    Parameters:
        - β: transmission probability per contact
        - μ: recovery probability

SIR Model (Susceptible-Infected-Recovered):
    States: S (susceptible), I (infected), R (recovered)
    Update rules:
        - S → I with probability λ_i = 1 - ∏_j (1 - β)^(A_ij · I_j)
        - I → R with probability γ
    Parameters:
        - β: transmission probability per contact
        - γ: recovery probability

Random Walk:
    State: Current node position
    Update rule:
        - Move to neighbor j with probability 1/degree(i)
        - Stay at i with probability p_lazy (if lazy walk)
"""

from py3plex.core import multinet
from py3plex.dynamics import D, SIS, SIR, RandomWalk
from py3plex.dsl import Q, L
import networkx as nx

print("=" * 80)
print("DSL-BASED DYNAMICS SIMULATION")
print("=" * 80)
print("\nThis example demonstrates the declarative DSL for dynamics on")
print("multilayer networks, including SIS, SIR, and Random Walk models.\n")


# =============================================================================
# Example 1: Basic SIS Epidemic Simulation
# =============================================================================
print("\n" + "=" * 80)
print("[1] Basic SIS Epidemic Simulation")
print("-" * 80)

# Create a simple network
network = multinet.multi_layer_network(directed=False)

# Add nodes and edges for a contact network
nodes = [{'source': f'Person{i}', 'type': 'contact'} for i in range(20)]
network.add_nodes(nodes)

# Create a scale-free-like structure
edges = []
for i in range(19):
    edges.append({
        'source': f'Person{i}',
        'target': f'Person{i+1}',
        'source_type': 'contact',
        'target_type': 'contact',
        'weight': 1.0
    })

# Add some random connections for hubs
import random
random.seed(42)
for i in [5, 10, 15]:  # Create hubs
    for _ in range(3):
        j = random.randint(0, 19)
        if i != j:
            edges.append({
                'source': f'Person{i}',
                'target': f'Person{j}',
                'source_type': 'contact',
                'target_type': 'contact',
                'weight': 1.0
            })

network.add_edges(edges)

print(f"Network: {len(list(network.get_nodes()))} nodes, {len(list(network.get_edges()))} edges")

# Define SIS simulation using DSL
sim = (
    D.process(SIS(beta=0.3, mu=0.1))  # Transmission rate 0.3, recovery rate 0.1
     .initial(infected=0.05)           # Start with 5% infected
     .steps(100)                       # Run for 100 time steps
     .measure("prevalence", "incidence")  # Track prevalence and incidence
     .replicates(10)                   # Run 10 independent simulations
     .seed(42)                         # For reproducibility
)

print("\nSimulation configuration:")
print(f"  Process: SIS")
print(f"  Parameters: β=0.3, μ=0.1")
print(f"  Initial infected: 5%")
print(f"  Time steps: 100")
print(f"  Replicates: 10")

# Run simulation
result = sim.run(network)

print(f"\nSimulation complete!")
print(f"  Result shape: {result.data['prevalence'].shape}")  # (replicates, steps)
print(f"  Mean final prevalence: {result.data['prevalence'][:, -1].mean():.3f}")
print(f"  Std final prevalence: {result.data['prevalence'][:, -1].std():.3f}")

# Convert to pandas for analysis
df_dict = result.to_pandas()  # Returns dict of DataFrames
print(f"\nResult DataFrames available: {list(df_dict.keys())}")
print(f"\nPrevalence DataFrame (first 10 rows):")
print(df_dict['prevalence'].head(10))


# =============================================================================
# Example 2: SIR Epidemic with Recovered Tracking
# =============================================================================
print("\n" + "=" * 80)
print("[2] SIR Epidemic with Recovered Tracking")
print("-" * 80)

# SIR model: infections are permanent (recovery means immunity)
sim_sir = (
    D.process(SIR(beta=0.4, gamma=0.15))  # Higher transmission, slower recovery
     .initial(infected=0.1)                # Start with 10% infected
     .steps(150)
     .measure("prevalence", "state_counts")  # Track all compartments
     .replicates(20)
     .seed(123)
)

print("\nSIR Simulation configuration:")
print(f"  Process: SIR")
print(f"  Parameters: β=0.4, γ=0.15")
print(f"  Initial infected: 10%")
print(f"  Time steps: 150")
print(f"  Replicates: 20")

result_sir = sim_sir.run(network)

# Analyze final outbreak size (final recovered)
# state_counts returns counts for each state (S=0, I=1, R=2)
print(f"\nSIR Results:")
print(f"  Mean peak prevalence: {result_sir.data['prevalence'].max(axis=1).mean():.3f}")
print(f"  Attack rate (final R/N): Variable per replicate")


# =============================================================================
# Example 3: Multilayer SIS with Layer Selection
# =============================================================================
print("\n" + "=" * 80)
print("[3] Multilayer SIS with Layer Selection")
print("-" * 80)

# Create a multilayer network with online and offline layers
multilayer = multinet.multi_layer_network(directed=False)

# Add nodes to both layers
people = [f'Person{i}' for i in range(15)]
for person in people:
    multilayer.add_nodes([
        {'source': person, 'type': 'offline'},
        {'source': person, 'type': 'online'}
    ])

# Offline layer: sparse, localized contacts
offline_edges = []
for i in range(14):
    offline_edges.append({
        'source': people[i],
        'target': people[i+1],
        'source_type': 'offline',
        'target_type': 'offline',
        'weight': 1.0
    })

# Online layer: more random, denser connections
random.seed(42)
online_edges = []
for _ in range(25):
    i, j = random.sample(range(15), 2)
    online_edges.append({
        'source': people[i],
        'target': people[j],
        'source_type': 'online',
        'target_type': 'online',
        'weight': 1.0
    })

multilayer.add_edges(offline_edges + online_edges)

print(f"\nMultilayer network created:")
print(f"  Offline layer: {len(offline_edges)} edges")
print(f"  Online layer: {len(online_edges)} edges")

# Run SIS on BOTH layers (node states shared across layers)
sim_multi = (
    D.process(SIS(beta=0.25, mu=0.08))
     .on_layers(L["offline"] + L["online"])  # Simulate on both layers
     .coupling(node_replicas="strong")       # Nodes share states across layers
     .initial(infected=0.1)
     .steps(120)
     .measure("prevalence", "prevalence_by_layer")  # Track per-layer prevalence
     .replicates(15)
     .seed(456)
)

print("\nMultilayer SIS configuration:")
print(f"  Layers: offline + online")
print(f"  Coupling: strong (shared node states)")
print(f"  Parameters: β=0.25, μ=0.08")

result_multi = sim_multi.run(multilayer)

print(f"\nMultilayer SIS complete!")
print(f"  Overall prevalence tracked")
print(f"  Per-layer prevalence available in result")


# =============================================================================
# Example 4: Random Walk Dynamics
# =============================================================================
print("\n" + "=" * 80)
print("[4] Random Walk on Network")
print("-" * 80)

# Create a small directed graph for random walk
walk_net = multinet.multi_layer_network(directed=True)

# Create a simple path with branches
walk_nodes = [{'source': f'Node{i}', 'type': 'graph'} for i in range(8)]
walk_net.add_nodes(walk_nodes)

walk_edges = [
    # Main path
    {'source': 'Node0', 'target': 'Node1', 'source_type': 'graph', 'target_type': 'graph'},
    {'source': 'Node1', 'target': 'Node2', 'source_type': 'graph', 'target_type': 'graph'},
    {'source': 'Node2', 'target': 'Node3', 'source_type': 'graph', 'target_type': 'graph'},
    # Branch from Node2
    {'source': 'Node2', 'target': 'Node4', 'source_type': 'graph', 'target_type': 'graph'},
    {'source': 'Node4', 'target': 'Node5', 'source_type': 'graph', 'target_type': 'graph'},
    # Branch from Node1
    {'source': 'Node1', 'target': 'Node6', 'source_type': 'graph', 'target_type': 'graph'},
    {'source': 'Node6', 'target': 'Node7', 'source_type': 'graph', 'target_type': 'graph'},
]

walk_net.add_edges(walk_edges)

# Random walk simulation
sim_walk = (
    D.process(RandomWalk())
     .initial(start_node=('Node0', 'graph'))  # Start at Node0
     .steps(50)
     .measure("visit_frequency")  # Track visit frequency
     .replicates(100)  # Many replicates for statistics
     .seed(789)
)

print("\nRandom Walk configuration:")
print(f"  Start node: Node0")
print(f"  Steps: 50")
print(f"  Replicates: 100")

result_walk = sim_walk.run(walk_net)

print(f"\nRandom Walk complete!")
print(f"  Visit frequency statistics collected across replicates")


# =============================================================================
# Example 5: DSL Integration - Query-based Initial Conditions
# =============================================================================
print("\n" + "=" * 80)
print("[5] DSL Integration: Query-Based Initial Conditions")
print("-" * 80)

# Create network with varying node degrees
hetero_net = multinet.multi_layer_network(directed=False)

# Add nodes
hetero_nodes = [{'source': f'N{i}', 'type': 'net'} for i in range(30)]
hetero_net.add_nodes(hetero_nodes)

# Create heterogeneous degree distribution
random.seed(100)
hetero_edges = []

# Hub nodes (high degree)
hubs = ['N5', 'N15', 'N25']
for hub in hubs:
    for _ in range(8):
        target = f'N{random.randint(0, 29)}'
        if target != hub:
            hetero_edges.append({
                'source': hub,
                'target': target,
                'source_type': 'net',
                'target_type': 'net',
                'weight': 1.0
            })

# Regular connections
for i in range(29):
    hetero_edges.append({
        'source': f'N{i}',
        'target': f'N{i+1}',
        'source_type': 'net',
        'target_type': 'net',
        'weight': 1.0
    })

hetero_net.add_edges(hetero_edges)

print("\nNetwork with hubs created")
print(f"  Hub nodes: {hubs}")

# Use query DSL to select high-degree nodes as initial infected
# This demonstrates integration between query DSL and dynamics DSL
sim_targeted = (
    D.process(SIS(beta=0.35, mu=0.12))
     .initial(
         # Instead of a fraction, use a query to select specific nodes
         infected=Q.nodes().where(degree__gte=5)  # Start infection at hubs
     )
     .steps(100)
     .measure("prevalence", "incidence")
     .replicates(10)
     .seed(999)
)

print("\nTargeted initial infection configuration:")
print(f"  Initial infected: Nodes with degree >= 5 (hubs)")
print(f"  This uses query DSL (Q.nodes()) within dynamics DSL")

result_targeted = sim_targeted.run(hetero_net)

print(f"\nTargeted SIS complete!")
print(f"  Mean final prevalence: {result_targeted.data['prevalence'][:, -1].mean():.3f}")


# =============================================================================
# Example 6: Parameter Comparison Using Multiple Simulations
# =============================================================================
print("\n" + "=" * 80)
print("[6] Parameter Comparison: Varying Transmission Rates")
print("-" * 80)

# Compare epidemic dynamics under different transmission rates
beta_values = [0.2, 0.3, 0.4, 0.5]
comparison_results = {}

print("\nRunning SIS simulations with varying β:")
for beta in beta_values:
    sim_param = (
        D.process(SIS(beta=beta, mu=0.1))
         .initial(infected=0.05)
         .steps(80)
         .measure("prevalence")
         .replicates(20)
         .seed(42)
    )

    result_param = sim_param.run(network)
    mean_final = result_param.data['prevalence'][:, -1].mean()
    comparison_results[beta] = mean_final

    print(f"  β={beta:.1f}: mean final prevalence = {mean_final:.3f}")

# Summary
print("\n" + "=" * 80)
print("SUMMARY: DSL Dynamics Features Demonstrated")
print("=" * 80)
print("""
1. ✓ Basic SIS epidemic with prevalence tracking
2. ✓ SIR model with compartment tracking
3. ✓ Multilayer dynamics with layer coupling
4. ✓ Random walk dynamics
5. ✓ Integration with query DSL for initial conditions
6. ✓ Parameter comparison across simulations

Key DSL Capabilities:
  • Declarative simulation specification
  • Type-safe builder API with method chaining
  • Integration with query DSL (L[] for layers, Q for queries)
  • Automatic replication management
  • Built-in measures (prevalence, incidence, state_counts, etc.)
  • Pandas export for analysis

The dynamics DSL makes complex multilayer simulations concise and readable,
following the same design philosophy as the query DSL.
""")

print("\nFor more details on dynamics models, see:")
print("  - examples/advanced/example_dynamics_core.py")
print("  - docfiles/sir_epidemic_simulator.rst")
print("  - py3plex.dynamics module documentation")
