"""Example: Community Detection for Multilayer Networks (Legacy DSL)

This example demonstrates community detection in multilayer networks using 
legacy DSL convenience functions. These are maintained for backward compatibility.

LEGACY PATTERNS (shown here):
    result = execute_query(network, 'SELECT nodes COMPUTE communities')
    communities = detect_communities(network)

PREFERRED PATTERN (DSL v2):
    from py3plex.algorithms.community_detection import leiden_multilayer
    partition = leiden_multilayer(network, random_state=42)
    # OR use AutoCommunity for automatic algorithm selection

This example covers:
1. Basic community detection via legacy string DSL
2. Using legacy convenience functions for backward compatibility
3. Analyzing community statistics (biggest, smallest, distribution)
4. Combining community detection with centrality measures

Note: For new code using DSL v2, see:
- examples/network_analysis/flagship_example.py for modern patterns
- AGENTS.md for Golden Paths documentation
- Direct algorithm functions: leiden_multilayer, label_propagation_*
"""

from py3plex.core import multinet
from py3plex.dsl import (
    execute_query,  # Legacy string DSL
    format_result,
    detect_communities,  # Legacy convenience function
    get_community_partition,
    get_biggest_community,
    get_smallest_community,
    get_num_communities,
    get_community_sizes,
    get_community_size_distribution,
)

print("=" * 80)
print("COMMUNITY DETECTION FOR MULTILAYER NETWORKS (Legacy DSL)")
print("=" * 80)
print("\nThis example demonstrates legacy DSL patterns for backward compatibility.")
print("For modern DSL v2 patterns, see examples/network_analysis/flagship_example.py")
print("and AGENTS.md documentation.")
print()

# ═══════════════════════════════════════════════════════════════════════════════
# Create a sample network with clear community structure
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[1] Creating sample network with community structure...")
print("-" * 80)

network = multinet.multi_layer_network(directed=False)

# Add nodes organized into 3 potential communities
nodes = [
    # Community 1: Social group A (Alice, Bob, Charlie)
    {'source': 'Alice', 'type': 'social'},
    {'source': 'Bob', 'type': 'social'},
    {'source': 'Charlie', 'type': 'social'},

    # Community 2: Social group B (David, Eve, Frank, Grace)
    {'source': 'David', 'type': 'social'},
    {'source': 'Eve', 'type': 'social'},
    {'source': 'Frank', 'type': 'social'},
    {'source': 'Grace', 'type': 'social'},

    # Community 3: Social group C (Henry, Ivy)
    {'source': 'Henry', 'type': 'social'},
    {'source': 'Ivy', 'type': 'social'},
]

network.add_nodes(nodes)

# Add edges to form communities with weak inter-community connections
edges = [
    # Community 1: Alice, Bob, Charlie (densely connected)
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
    {'source': 'Alice', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
    {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},

    # Community 2: David, Eve, Frank, Grace (densely connected)
    {'source': 'David', 'target': 'Eve', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
    {'source': 'David', 'target': 'Frank', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
    {'source': 'David', 'target': 'Grace', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
    {'source': 'Eve', 'target': 'Frank', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
    {'source': 'Eve', 'target': 'Grace', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
    {'source': 'Frank', 'target': 'Grace', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},

    # Community 3: Henry, Ivy
    {'source': 'Henry', 'target': 'Ivy', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},

    # Bridge connections between communities (weak ties)
    {'source': 'Charlie', 'target': 'David', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
    {'source': 'Grace', 'target': 'Henry', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
]

network.add_edges(edges)

print(f"Network created: {len(list(network.get_nodes()))} nodes, {len(list(network.get_edges()))} edges")

# ═══════════════════════════════════════════════════════════════════════════════
# Example 1: Basic community detection via legacy string DSL
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("[2] Example 1: Basic Community Detection via Legacy String DSL")
print("-" * 80)
print("Query: SELECT nodes COMPUTE communities")
print()

result = execute_query(network, 'SELECT nodes COMPUTE communities')

print(f"Total nodes: {result['count']}")
print(f"Community assignments:")
for node, community_id in sorted(result['computed']['communities'].items()):
    print(f"  {node}: Community {community_id}")

# ═══════════════════════════════════════════════════════════════════════════════
# Example 2: Full community analysis with convenience function
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("[3] Example 2: Full Community Analysis with Convenience Function")
print("-" * 80)

communities = detect_communities(network)

print(f"Number of communities: {communities['num_communities']}")
print(f"Community sizes: {communities['community_sizes']}")
print(f"Size distribution: {communities['size_distribution']}")
print(f"Biggest community: ID={communities['biggest_community'][0]}, Size={communities['biggest_community'][1]}")
print(f"Smallest community: ID={communities['smallest_community'][0]}, Size={communities['smallest_community'][1]}")

# ═══════════════════════════════════════════════════════════════════════════════
# Example 3: Get the biggest community
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("[4] Example 3: Biggest Community Details")
print("-" * 80)

community_id, size, nodes = get_biggest_community(network)
print(f"Biggest community: ID={community_id}")
print(f"Size: {size} nodes")
print(f"Members:")
for node in nodes:
    print(f"  - {node}")

# ═══════════════════════════════════════════════════════════════════════════════
# Example 4: Get the smallest community
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("[5] Example 4: Smallest Community Details")
print("-" * 80)

community_id, size, nodes = get_smallest_community(network)
print(f"Smallest community: ID={community_id}")
print(f"Size: {size} nodes")
print(f"Members:")
for node in nodes:
    print(f"  - {node}")

# ═══════════════════════════════════════════════════════════════════════════════
# Example 5: Community size distribution analysis
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("[6] Example 5: Community Size Distribution Analysis")
print("-" * 80)

sizes = get_community_size_distribution(network)
num_communities = get_num_communities(network)

print(f"Number of communities: {num_communities}")
print(f"Size distribution (sorted descending): {sizes}")
print(f"Average community size: {sum(sizes) / len(sizes):.2f}")
print(f"Largest community: {max(sizes)} nodes")
print(f"Smallest community: {min(sizes)} nodes")

# ═══════════════════════════════════════════════════════════════════════════════
# Example 6: Working with the full partition
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("[7] Example 6: Working with Community Partition")
print("-" * 80)

partition = get_community_partition(network)

# Group nodes by community
from collections import defaultdict
communities_grouped = defaultdict(list)
for node, community_id in partition.items():
    communities_grouped[community_id].append(node)

print("Nodes grouped by community:")
for community_id, members in sorted(communities_grouped.items()):
    member_names = [str(m[0]) for m in members]  # Extract node names
    print(f"  Community {community_id}: {', '.join(sorted(member_names))}")

# ═══════════════════════════════════════════════════════════════════════════════
# Example 7: Combining community detection with other DSL features
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("[8] Example 7: Community Detection with Other Measures")
print("-" * 80)
print("Query: SELECT nodes COMPUTE communities degree betweenness_centrality")
print()

result = execute_query(network, 'SELECT nodes COMPUTE communities degree betweenness_centrality')

print("Node Analysis (Communities + Centrality):")
print(f"{'Node':<15} {'Community':<12} {'Degree':<10} {'Betweenness':<12}")
print("-" * 50)

for node in sorted(result['nodes']):
    comm = result['computed']['communities'].get(node, -1)
    deg = result['computed']['degree'].get(node, 0)
    btw = result['computed']['betweenness_centrality'].get(node, 0)
    print(f"{str(node[0]):<15} {comm:<12} {deg:<10} {btw:<12.4f}")

# ═══════════════════════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("LEGACY DSL COMMUNITY DETECTION EXAMPLES COMPLETE")
print("=" * 80)
print("\nLegacy string DSL syntax (backward compatibility):")
print("  SELECT nodes COMPUTE communities")
print("  SELECT nodes COMPUTE community  # alias")
print("  SELECT nodes WHERE layer=\"name\" COMPUTE communities")
print()
print("Legacy convenience functions:")
print("  detect_communities(network) - Full analysis with all statistics")
print("  get_community_partition(network) - Node to community mapping")
print("  get_biggest_community(network) - Returns (id, size, nodes)")
print("  get_smallest_community(network) - Returns (id, size, nodes)")
print("  get_num_communities(network) - Number of communities")
print("  get_community_sizes(network) - Dict of community sizes")
print("  get_community_size_distribution(network) - Sorted size list")
print()
print("PREFERRED PATTERNS (for new code):")
print("  Use algorithm functions directly:")
print("    from py3plex.algorithms.community_detection import leiden_multilayer")
print("    partition = leiden_multilayer(network, random_state=42)")
print()
print("  Or use AutoCommunity for automatic algorithm selection:")
print("    from py3plex.algorithms.community_detection import AutoCommunity")
print("    result = AutoCommunity().candidates('leiden', 'louvain').execute(network)")
print()
print("For more information:")
print("  - AGENTS.md: Section on Community Detection")
print("  - examples/network_analysis/flagship_example.py: Modern patterns")
print("  - docfiles/user_guide/community_detection.rst: Full documentation")
