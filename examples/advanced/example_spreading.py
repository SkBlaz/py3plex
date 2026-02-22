"""
Dynamics Example: Simple Spreading Process on Multilayer Networks

This example demonstrates how to:
1. Generate a random multilayer network
2. Simulate a spreading/diffusion process (like information or disease spread)
3. Track which layers are visited during the spread
4. Visualize the layer visit distribution

The spreading process uses a breadth-first search (BFS) approach where
information spreads from a seed node to its neighbors across all layers.

Use cases:
- Information diffusion in social networks
- Disease spreading in contact networks
- Influence propagation in multilayer systems

SKIP_CI: external_deps - Requires seaborn
"""

import numpy as np
import queue
import matplotlib.pyplot as plt
import seaborn as sns
from py3plex.core import random_generators

print("=" * 70)
print("MULTILAYER SPREADING PROCESS SIMULATION")
print("=" * 70)

# Generate a random multilayer Erdos-Renyi network
print("\nGenerating multilayer network...")
print("  Nodes: 5000")
print("  Layers: 15")
print("  Edge probability: 0.05")

ER_multilayer = random_generators.random_multilayer_ER(
    5000,     # Number of nodes
    15,       # Number of layers
    0.05,     # Edge probability (fairly dense for spreading)
    directed=False
)

print("Network generated successfully!")

# Prepare for spreading simulation
all_nodes = list(ER_multilayer.get_nodes())
all_nodes_indexed = {x: en for en, x in enumerate(all_nodes)}

print(f"\nTotal node-layer pairs: {len(all_nodes)}")
print("\nSimulating spreading process from 5 random seed nodes...")
print("-" * 70)

# Run multiple spreading simulations from different seed nodes
num_simulations = 5

for simulation_id in range(num_simulations):
    print(f"\nSimulation {simulation_id + 1}/{num_simulations}:")

    # Select a random seed node to start the spread
    random_init = np.random.randint(len(all_nodes))
    random_node = all_nodes[random_init]

    print(f"  Seed node: {random_node}")

    # Track which nodes have been visited (infected/informed)
    # 0 = not visited, 1 = visited
    spread_vector = np.zeros(len(ER_multilayer.core_network))

    # Use a queue for breadth-first spreading
    Q = queue.Queue(maxsize=300000)
    Q.put(random_node)

    # Track the sequence of layer visits
    layer_visit_sequence = []
    node_visit_sequence = []
    iterations = 0

    # Spreading process: BFS traversal
    while True:
        if not Q.empty():
            # Get next node to process
            candidate = Q.get()
            iterations += 1

            # Progress indicator for long-running simulations
            if iterations % 100 == 0:
                print(f"    Iterations: {iterations}")

            # Spread to all neighbors of current node
            for neighbor in ER_multilayer.get_neighbors(
                    candidate[0],  # Node ID
                    candidate[1]   # Layer ID
            ):
                idx = all_nodes_indexed[neighbor]

                # If neighbor hasn't been visited yet
                if spread_vector[idx] != 1:
                    # Record the layer where spread occurred
                    layer_visit_sequence.append(candidate[1])

                    # Record the node and when it was reached
                    node_visit_sequence.append((neighbor, iterations))

                    # Add neighbor to queue for further spreading
                    Q.put(neighbor)

                    # Mark as visited
                    spread_vector[idx] = 1
        else:
            # Queue is empty, spreading complete
            break

    print(f"  Spreading complete!")
    print(f"  Total iterations: {iterations}")
    print(f"  Nodes reached: {int(np.sum(spread_vector))}/{len(spread_vector)}")
    print(f"  Coverage: {100 * np.sum(spread_vector) / len(spread_vector):.1f}%")

    # Visualize layer visit distribution
    if layer_visit_sequence:
        sns.distplot(
            layer_visit_sequence,
            bins=10,
            kde=True,
            label=f"Walker {simulation_id + 1}",
            hist_kws={
                "linewidth": 3,
                "alpha": 0.2
            }
        )

print("\n" + "=" * 70)
print("LAYER VISIT DISTRIBUTION VISUALIZATION")
print("=" * 70)

# Configure plot
plt.xlabel("Layer", fontsize=12)
plt.ylabel("Visit density", fontsize=12)
plt.xlim(0, 14)
plt.title("Distribution of Layer Visits During Spreading", fontsize=14)
plt.legend()
plt.grid(True, alpha=0.3)

print("\nGenerating visualization...")
print("(Close the window to exit)")

plt.show()

print("\n" + "=" * 70)
print("SIMULATION COMPLETE")
print("=" * 70)

print("\nInterpretation:")
print("  - Each curve shows how often each layer was visited during spreading")
print("  - Peaks indicate layers that are more central to the spreading process")
print("  - Differences between simulations show variability in spreading paths")
print("  - More uniform distribution = layers are well-connected")
print("  - Concentrated distribution = some layers dominate the spreading")
