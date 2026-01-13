"""Example: Declarative Dynamics with Q.dynamics() DSL

This example demonstrates the new Q.dynamics() DSL for declaring and running
dynamical processes on multilayer networks. The Q.dynamics() API provides a
first-class, declarative interface for dynamics that integrates seamlessly
with the existing DSL query API.

Key Features:
- Declarative syntax: Q.dynamics("SIS", beta=0.3, mu=0.1)
- Layer selection: .on_layers(L["contacts"] + L["travel"])
- Query-based seeding: .seed(Q.nodes().where(degree__gt=10))
- Per-layer parameters: .parameters_per_layer({"contacts": {"beta": 0.4}})
- Full integration with DSL: uses L[] for layers, Q.nodes() for queries
"""

from py3plex.core import multinet
from py3plex.dsl import Q, L
import numpy as np

print("=" * 80)
print("DECLARATIVE DYNAMICS WITH Q.dynamics() DSL")
print("=" * 80)
print()

# =============================================================================
# Example 1: Basic SIS Epidemic with Q.dynamics()
# =============================================================================
print("[Example 1] Basic SIS Epidemic")
print("-" * 80)

# Create a simple network
network = multinet.multi_layer_network(directed=False)

nodes = [{'source': f'Person{i}', 'type': 'contact'} for i in range(20)]
network.add_nodes(nodes)

# Create connections
edges = []
for i in range(19):
    edges.append({
        'source': f'Person{i}',
        'target': f'Person{i+1}',
        'source_type': 'contact',
        'target_type': 'contact',
        'weight': 1.0
    })

# Add some hub connections
import random
random.seed(42)
for i in [5, 10, 15]:
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

# Run SIS simulation with Q.dynamics()
result = (
    Q.dynamics("SIS", beta=0.3, mu=0.1)
     .seed(0.05)  # Start with 5% infected
     .run(steps=100, replicates=10, track=["prevalence", "incidence"])
     .random_seed(42)
     .execute(network)
)

print(f"Network: {len(list(network.get_nodes()))} nodes, {len(list(network.get_edges()))} edges")
print(f"Process: SIS (β=0.3, μ=0.1)")
print(f"Result shape: {result.data['prevalence'].shape}") # (replicates, steps)
print(f"Mean final prevalence: {result.data['prevalence'][:, -1].mean():.3f}")
print(f"Std final prevalence: {result.data['prevalence'][:, -1].std():.3f}")
print()

# =============================================================================
# Example 2: Multilayer SIR with Layer-Specific Parameters
# =============================================================================
print("[Example 2] Multilayer SIR with Layer-Specific Parameters")
print("-" * 80)

# Create multilayer network
multilayer = multinet.multi_layer_network(directed=False)

people = [f'Person{i}' for i in range(15)]
for person in people:
    multilayer.add_nodes([
        {'source': person, 'type': 'offline'},
        {'source': person, 'type': 'online'}
    ])

# Offline layer: sparse contacts
offline_edges = []
for i in range(14):
    offline_edges.append({
        'source': people[i],
        'target': people[i+1],
        'source_type': 'offline',
        'target_type': 'offline',
        'weight': 1.0
    })

# Online layer: dense random connections
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

# Run SIR with different transmission rates per layer
result_multilayer = (
    Q.dynamics("SIR", beta=0.2, gamma=0.05)
     .on_layers(L["offline"] + L["online"])
     .parameters_per_layer({
         "offline": {"beta": 0.3},  # Higher transmission offline
         "online": {"beta": 0.1}    # Lower transmission online
     })
     .seed(0.1)  # 10% initially infected
     .run(steps=150, replicates=15, track=["prevalence", "state_counts"])
     .random_seed(123)
     .execute(multilayer)
)

print(f"Multilayer network:")
print(f" Offline layer: {len(offline_edges)} edges")
print(f" Online layer: {len(online_edges)} edges")
print(f"Process: SIR with layer-specific transmission")
print(f" Offline β=0.3, Online β=0.1")
print(f"Mean peak prevalence: {result_multilayer.data['prevalence'].max(axis=1).mean():.3f}")
print()

# =============================================================================
# Example 3: Query-Based Seeding (Targeted Intervention)
# =============================================================================
print("[Example 3] Query-Based Seeding (Targeted Intervention)")
print("-" * 80)

# Create network with heterogeneous degree distribution
hetero_net = multinet.multi_layer_network(directed=False)

hetero_nodes = [{'source': f'N{i}', 'type': 'net'} for i in range(30)]
hetero_net.add_nodes(hetero_nodes)

# Create hubs
random.seed(100)
hetero_edges = []
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

# Strategy 1: Random seeding
result_random = (
    Q.dynamics("SIS", beta=0.35, mu=0.12)
     .seed(0.1)  # Random 10%
     .run(steps=100, replicates=10, track=["prevalence"])
     .random_seed(999)
     .execute(hetero_net)
)

# Strategy 2: Target high-degree nodes (hubs)
result_targeted = (
    Q.dynamics("SIS", beta=0.35, mu=0.12)
     .seed(Q.nodes().where(degree__gte=5))  # Seed hubs
     .run(steps=100, replicates=10, track=["prevalence"])
     .random_seed(999)
     .execute(hetero_net)
)

print("Comparing seeding strategies:")
print(f" Random seeding: final prevalence = {result_random.data['prevalence'][:, -1].mean():.3f}")
print(f" Targeted (hubs): final prevalence = {result_targeted.data['prevalence'][:, -1].mean():.3f}")
print(f" Difference: {abs(result_targeted.data['prevalence'][:, -1].mean() - result_random.data['prevalence'][:, -1].mean()):.3f}")
print()

# =============================================================================
# Example 4: Integration with Existing DSL
# =============================================================================
print("[Example 4] Integration with Existing DSL")
print("-" * 80)

# First, use structural DSL to identify important nodes
high_degree_nodes = (
    Q.nodes()
     .from_layers(L["contact"])
     .compute("degree")
     .where(degree__gt=3)
     .execute(network)
)

print(f"Found {len(high_degree_nodes.items)} high-degree nodes (degree > 3)")

# Then use those nodes to seed a dynamics simulation
# (Note: In practice, you'd pass the result to .seed(), but for demo we use fraction)
result_integrated = (
    Q.dynamics("SIS", beta=0.3, mu=0.1)
     .on_layers(L["contact"])
     .seed(0.1)
     .run(steps=50, replicates=5, track=["prevalence"])
     .random_seed(42)
     .execute(network)
)

print(f"Integrated SIS simulation result: {result_integrated.data['prevalence'].shape}")
print()

# =============================================================================
# Summary
# =============================================================================
print("=" * 80)
print("SUMMARY: Q.dynamics() Features Demonstrated")
print("=" * 80)
print("""
1. Declarative syntax: Q.dynamics("SIS", beta=0.3, mu=0.1)
2. Layer selection: .on_layers(L["offline"] + L["online"])
3. Query-based seeding: .seed(Q.nodes().where(degree__gte=5))
4. Per-layer parameters: .parameters_per_layer(...)
5. Multiple measures: track=["prevalence", "incidence", "state_counts"]
6. Reproducibility: .random_seed(42)
7. Integration with structural DSL

Key Advantages:
• First-class DSL feature (not just imperative code)
• Composable with existing Q, L, Param DSL components
• Lazy execution: build query, then .execute()
• Type-safe builder API with method chaining
• Backward compatible: D.process() still works

The dynamics DSL makes complex multilayer simulations concise, readable,
and declarative, following the same design philosophy as the query DSL.
""")

print("For more examples, see:")
print(" - examples/network_analysis/example_dsl_dynamics.py")
print(" - tests/test_dsl_dynamics_integration.py")
print(" - docfiles/how-to/simulate_dynamics.rst")
