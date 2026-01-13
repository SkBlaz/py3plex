"""
Network Manipulation and Basic Operations Tutorial

Teaches:
- Add single and multiple nodes/edges with attributes
- Use dictionary-based and list-based input formats
- Create and manipulate multiplex networks (shared node sets)
- Subset networks by layers, nodes, or node-layer tuples
- Work with coupled edges in multiplex networks
- Remove nodes and edges

Prerequisites:
- py3plex installed (no external datasets required)

Runtime: FAST (< 5 seconds) - Standalone example suitable for CI
"""

from py3plex.core import multinet
from py3plex.core import random_generators

print("=" * 70)
print("NETWORK MANIPULATION AND BASIC OPERATIONS")
print("=" * 70)

# ═══════════════════════════════════════════════════════════════════════════════
# Example 1: Adding single nodes and edges
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[1] Adding single nodes and edges with attributes...")
print("-" * 70)

# An example general multilayer network
A = multinet.multi_layer_network()

# Add a single node with type (layer)
simple_node = {"source": "node1", "type": "t1"}
A.add_nodes(simple_node)
A.monitor("Added a single node.")
print("Nodes:", list(A.get_nodes(data=True)))

# ═══════════════════════════════════════════════════════════════════════════════
# Example 2: Adding edges with attributes
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[2] Adding edges with custom attributes...")
print("-" * 70)

# Add a single edge with type and custom attributes
simple_edge = {
    "source": "node1",
    "target": "node2",
    "type": "mention",
    "source_type": "t1",
    "weight": 2,  # add arbitrary attributes!
    "target_type": "t2"
}

A.add_edges(simple_edge)
A.monitor("Added a single edge with weight attribute.")
print("Edges:", list(A.get_edges(data=True)))

# ═══════════════════════════════════════════════════════════════════════════════
# Example 3: Adding multiple edges at once
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[3] Adding multiple edges at once...")
print("-" * 70)

# Multiple edges are added by packing them into a list
simple_attributed_edges = [{
    "source": "node1",
    "target": "node6",
    "type": "mention",
    "source_type": "t1",
    "target_type": "t5"
}, {
    "source": "node3",
    "target": "node2",
    "type": "mention",
    "source_type": "t1",
    "target_type": "t3"
}]
A.add_edges(simple_attributed_edges)
A.monitor("Added multiple edges using list of dictionaries.")
print(f"Total edges: {len(list(A.get_edges()))}")

# ═══════════════════════════════════════════════════════════════════════════════
# Example 4: Using list-based input format
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[4] Using list-based input format: [source, source_layer, target, target_layer, weight]...")
print("-" * 70)

# Edges can also be added as lists: [source, source_layer, target, target_layer, weight]
example_list_edge = [["node3", "t2", "node2", "t6", 1],
                     ["node3", "t2", "node2", "t6", 1]]

# Specify that input is list format - Py3plex automatically handles it!
A.add_edges(example_list_edge, input_type="list")
print(f"Total edges after list additions: {len(list(A.get_edges()))}")

# ═══════════════════════════════════════════════════════════════════════════════
# Example 5: Generate random multilayer network
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[5] Generating random Erdős-Rényi multilayer network...")
print("-" * 70)

A.monitor("Generating random ER multilayer graph...")
ER_multilayer = random_generators.random_multilayer_ER(300,
                                                       6,
                                                       0.05,
                                                       directed=False)
print(f"Generated network: 300 nodes, 6 layers, edge probability 0.05")
# Visualization: ER_multilayer.visualize_network(show=True)

# ═══════════════════════════════════════════════════════════════════════════════
# Example 6: Working with multiplex networks (shared node sets)
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[6] Creating and manipulating multiplex networks...")
print("-" * 70)
print("Note: network_type='multiplex' is used when:")
print("  - All layers share the same set of nodes")
print("  - Automatic coupling edges connect node copies across layers")
print("  - Edges represent different relationship types between same entities")
print("For heterogeneous networks (different node sets), use network_type='multilayer'")
print()
B = multinet.multi_layer_network(network_type="multiplex")
B.add_edges(
    [[1, 1, 2, 1, 1], [1, 2, 3, 2, 1], [1, 2, 3, 1, 1], [2, 1, 3, 2, 1]],
    input_type="list")
print("Multiplex network created with shared nodes across layers")

# ═══════════════════════════════════════════════════════════════════════════════
# Example 7: Subsetting networks
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[7] Subsetting networks by layers, nodes, and node-layer tuples...")
print("-" * 70)
# Subset by layers
C = B.subnetwork([2], subset_by="layers")
print(f"Nodes in layer 2: {list(C.get_nodes())}")

# Subset by node names (gets all layers for specified nodes)
C = B.subnetwork([2], subset_by="node_names")
print(f"All instances of node 2: {list(C.get_nodes())}")

# Subset by specific node-layer tuples
C = B.subnetwork([(1, 1), (1, 2)], subset_by="node_layer_names")
print(f"Specific node-layer tuples: {list(C.get_nodes())}")

# ═══════════════════════════════════════════════════════════════════════════════
# Example 8: Coupled vs non-coupled edges in multiplex networks
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[8] Working with coupled edges in multiplex networks...")
print("-" * 70)
# Coupled edges (inter-layer connections between same node)
coupled_edges = list(B.get_edges(multiplex_edges=True))
B.monitor(f"Coupled edges (inter-layer): {len(coupled_edges)} edges")

# Non-coupled edges (intra-layer connections)
non_coupled_edges = list(B.get_edges(multiplex_edges=False))
B.monitor(f"Non-coupled edges (intra-layer): {len(non_coupled_edges)} edges")

# Visualization: B.visualize_network(show=True, resolution=0.01)

# ═══════════════════════════════════════════════════════════════════════════════
# Example 9: Removing edges and nodes
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[9] Removing edges and nodes...")
print("-" * 70)
# Remove edges using list format
B.remove_edges(
    [[1, 1, 2, 1, 1], [1, 2, 3, 2, 1], [1, 2, 3, 1, 1], [2, 1, 3, 2, 1]],
    input_type="list")
print(f"Edges after removal: {len(list(B.get_edges()))}")

# Remove nodes using list format (node-layer tuples)
B.remove_nodes([(1, 1), (3, 1)], input_type="list")
print(f"Nodes after removal: {list(B.get_nodes())}")

# Remove nodes using dictionary format
B.remove_nodes({"source": 2, "type": 1}, input_type="dict")
print(f"Final nodes: {list(B.get_nodes())}")

print("\n" + "=" * 70)
print("NETWORK MANIPULATION EXAMPLES COMPLETE")
print("=" * 70)
print("\nKey takeaways:")
print("  [OK] Dictionary and list formats both supported for nodes/edges")
print("  [OK] Multiplex networks enforce shared node sets across layers")
print("  [OK] Subnetworks can be extracted by layers, nodes, or tuples")
print("  [OK] Coupled edges automatically connect nodes across layers")
print("  [OK] Random network generators available for testing")

