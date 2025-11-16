"""
Multilayer Network Fingerprint Example

This example demonstrates the use of the get_fingerprint() method to obtain
a comprehensive statistical characterization of a multilayer network.

The fingerprint provides a "signature" of the network structure that includes:
- Basic metrics (nodes, edges, layers)
- Layer-specific statistics
- Inter-layer coupling
- Network-wide properties
- Centrality and structural measures

This is useful for:
- Network comparison and classification
- Quick diagnostics of network properties
- Feature extraction for machine learning
- Documentation and reporting
"""

from py3plex.core import multinet
import pandas as pd

print("=" * 80)
print("MULTILAYER NETWORK FINGERPRINT DEMONSTRATION")
print("=" * 80)

# ═════════════════════════════════════════════════════════════════════════════
# Example 1: Simple Multiplex Network
# ═════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("EXAMPLE 1: Simple Multiplex Network")
print("=" * 80)

# Create a simple multiplex network with 2 layers
net = multinet.multi_layer_network(directed=False, verbose=False)

# Add edges in layer 1 (social network)
net.add_edges([
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Charlie', 'target': 'Alice', 'source_type': 'social', 'target_type': 'social'},
])

# Add edges in layer 2 (professional network)
net.add_edges([
    {'source': 'Alice', 'target': 'Charlie', 'source_type': 'professional', 'target_type': 'professional'},
    {'source': 'Bob', 'target': 'Charlie', 'source_type': 'professional', 'target_type': 'professional'},
])

# Add inter-layer edges
net.add_edges([
    {'source': 'Alice', 'target': 'Alice', 'source_type': 'social', 'target_type': 'professional'},
    {'source': 'Bob', 'target': 'Bob', 'source_type': 'social', 'target_type': 'professional'},
    {'source': 'Charlie', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'professional'},
])

print("\nNetwork created with 3 nodes in 2 layers")
print("Computing fingerprint...")

# Get the fingerprint
fingerprint = net.get_fingerprint()

print("\nNetwork Fingerprint:")
print("-" * 80)
# Display the fingerprint nicely
pd.set_option('display.max_rows', None)
pd.set_option('display.max_colwidth', 60)
pd.set_option('display.width', 120)
print(fingerprint.to_string(index=False))

# ═════════════════════════════════════════════════════════════════════════════
# Example 2: Larger Random Multilayer Network
# ═════════════════════════════════════════════════════════════════════════════

print("\n\n" + "=" * 80)
print("EXAMPLE 2: Larger Random Multilayer Network")
print("=" * 80)

# Create a larger random network
net2 = multinet.multi_layer_network(directed=False, verbose=False)

# Generate random edges across 3 layers
import random
random.seed(42)

nodes = [f'N{i}' for i in range(1, 21)]  # 20 nodes
layers = ['Layer1', 'Layer2', 'Layer3']

print(f"\nCreating network with {len(nodes)} nodes and {len(layers)} layers")

# Add intra-layer edges
for layer in layers:
    num_edges = random.randint(15, 25)
    for _ in range(num_edges):
        n1, n2 = random.sample(nodes, 2)
        net2.add_edges([{
            'source': n1, 'target': n2,
            'source_type': layer, 'target_type': layer
        }])

# Add some inter-layer edges
for _ in range(10):
    node = random.choice(nodes)
    l1, l2 = random.sample(layers, 2)
    net2.add_edges([{
        'source': node, 'target': node,
        'source_type': l1, 'target_type': l2
    }])

print("Computing fingerprint (without detailed layer stats for speed)...")

# Get fingerprint without detailed layer stats for larger networks
fingerprint2 = net2.get_fingerprint(include_layer_stats=True)

print("\nNetwork Fingerprint:")
print("-" * 80)
print(fingerprint2.to_string(index=False))

# ═════════════════════════════════════════════════════════════════════════════
# Example 3: Comparing Network Fingerprints
# ═════════════════════════════════════════════════════════════════════════════

print("\n\n" + "=" * 80)
print("EXAMPLE 3: Comparing Network Fingerprints")
print("=" * 80)

print("\nComparing basic statistics between the two networks:")
print("-" * 80)

# Extract key metrics for comparison
metrics_to_compare = [
    'total_node_layer_pairs',
    'unique_nodes',
    'total_edges',
    'num_layers',
    'overall_density',
    'intra_layer_edges',
    'inter_layer_edges'
]

comparison_data = []
for metric in metrics_to_compare:
    val1 = fingerprint[fingerprint['statistic'] == metric]['value'].values
    val2 = fingerprint2[fingerprint2['statistic'] == metric]['value'].values
    
    if len(val1) > 0 and len(val2) > 0:
        comparison_data.append({
            'Metric': metric,
            'Network 1': val1[0],
            'Network 2': val2[0]
        })

comparison_df = pd.DataFrame(comparison_data)
print(comparison_df.to_string(index=False))

# ═════════════════════════════════════════════════════════════════════════════
# Example 4: Exporting Fingerprint
# ═════════════════════════════════════════════════════════════════════════════

print("\n\n" + "=" * 80)
print("EXAMPLE 4: Exporting Fingerprint")
print("=" * 80)

# Save fingerprint to CSV
output_file = '/tmp/network_fingerprint.csv'
fingerprint.to_csv(output_file, index=False)
print(f"\nFingerprint saved to: {output_file}")

# You can also convert to dictionary for JSON export
fingerprint_dict = fingerprint.to_dict('records')
print("\nFingerprint as dictionary (first 5 entries):")
for entry in fingerprint_dict[:5]:
    print(f"  {entry['statistic']}: {entry['value']}")

print("\n" + "=" * 80)
print("FINGERPRINT DEMONSTRATION COMPLETE")
print("=" * 80)
print("\nKey Takeaways:")
print("- get_fingerprint() provides comprehensive network statistics")
print("- Returns pandas DataFrame for easy manipulation and export")
print("- Use include_layer_stats=False for large networks to improve speed")
print("- Fingerprints enable network comparison and classification")
print("- Useful for documentation, reporting, and machine learning features")
