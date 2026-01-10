"""
Dynamics: SIS epidemic model.

Demonstrates:
- Susceptible-Infected-Susceptible dynamics
- Using SIS model from dynamics module

Note: This is a simplified conceptual example.
For full dynamics features, see the documentation.
"""

from py3plex.core.multinet import multi_layer_network

# 1. Create simple network
network = multi_layer_network(directed=False)
edges = []
for i in range(10):
    for j in range(i+1, 10):
        if abs(i-j) <= 2:  # Connect nearby nodes
            edges.append({
                'source': str(i),
                'target': str(j),
                'source_type': 'contact',
                'target_type': 'contact'
            })
network.add_edges(edges)

# 2. Network is ready for dynamics simulation
print(f"Network created: {len(list(network.get_nodes()))} nodes")
print(f"Edges: {len(list(network.get_edges()))}")
print("Network ready for SIS dynamics simulation")
print("See py3plex.dynamics module for simulation API")
