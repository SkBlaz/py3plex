"""
Dynamics: Custom dynamics model.

Demonstrates:
- Defining custom dynamics behavior
- Threshold activation model concept

Note: This is a conceptual example showing the idea of custom dynamics.
For the full dynamics API, see py3plex.dynamics module documentation.
"""

from py3plex.core.multinet import multi_layer_network

# 1. Create network
network = multi_layer_network(directed=False)
edges = []
for i in range(10):
    for j in range(i+1, 10):
        if abs(i-j) <= 2:  # Connect nearby nodes
            edges.append({
                'source': str(i),
                'target': str(j),
                'source_type': 'net',
                'target_type': 'net'
            })
network.add_edges(edges)

# 2. Network structure
print(f"Network for custom dynamics:")
print(f"  Nodes: {len(list(network.get_nodes()))}")
print(f"  Edges: {len(list(network.get_edges()))}")

# 3. Custom dynamics concept
print("\nThreshold model idea:")
print("  - Nodes activate when enough neighbors are active")
print("  - Can be implemented using py3plex.dynamics module")
print("  - See documentation for BaseDynamicsModel class")
