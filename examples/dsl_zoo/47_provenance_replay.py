"""Example 47: Provenance tracking and replay

Demonstrates provenance tracking for reproducibility and query replay
from provenance metadata.

Runtime: FAST (~0.1s)
"""

from py3plex.core import multinet
from py3plex.dsl import Q, L

# Create sample network
net = multinet.multi_layer_network(directed=False)
net.add_nodes([
    {'source': 'Alice', 'type': 'social'},
    {'source': 'Bob', 'type': 'social'},
    {'source': 'Carol', 'type': 'social'},
    {'source': 'Alice', 'type': 'work'},
    {'source': 'Bob', 'type': 'work'},
])
net.add_edges([
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Bob', 'target': 'Carol', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'work', 'target_type': 'work'},
])

print("=" * 60)
print("Example 1: Basic provenance tracking")
print("=" * 60)

result = (
    Q.nodes()
     .compute("degree", "betweenness_centrality")
     .where(degree__gt=1)
     .execute(net)
)

# Access provenance
prov = result.meta.get('provenance', {})
print(f"\nEngine: {prov.get('engine', 'N/A')}")
print(f"py3plex version: {prov.get('py3plex_version', 'N/A')}")
print(f"Timestamp: {prov.get('timestamp_utc', 'N/A')}")

# Network fingerprint
fp = prov.get('network_fingerprint', {})
print(f"\nNetwork fingerprint:")
print(f"  Nodes: {fp.get('node_count', 'N/A')}")
print(f"  Edges: {fp.get('edge_count', 'N/A')}")
print(f"  Layers: {fp.get('layer_count', 'N/A')}")

# Query AST
query_info = prov.get('query', {})
print(f"\nQuery AST hash: {query_info.get('ast_hash', 'N/A')}")

# Performance
perf = prov.get('performance', {})
print(f"\nExecution time: {perf.get('total_ms', 'N/A')}ms")

print("\n" + "=" * 60)
print("Example 2: Provenance with randomness")
print("=" * 60)

result_uq = (
    Q.nodes()
     .compute("degree")
     .uq(method="bootstrap", n_samples=10, seed=42)
     .execute(net)
)

prov_uq = result_uq.meta.get('provenance', {})
randomness = prov_uq.get('randomness', {})
print(f"\nRandomness tracking:")
print(f"  Method: {randomness.get('method', 'N/A')}")
print(f"  Seed: {randomness.get('seed', 'N/A')}")
print(f"  Samples: {randomness.get('n_samples', 'N/A')}")

print("\n" + "=" * 60)
print("Example 3: AST hash for reproducibility")
print("=" * 60)

# Same query twice - should have same AST hash
result1 = Q.nodes().compute("degree").execute(net)
result2 = Q.nodes().compute("degree").execute(net)

hash1 = result1.meta.get('provenance', {}).get('query', {}).get('ast_hash')
hash2 = result2.meta.get('provenance', {}).get('query', {}).get('ast_hash')

print(f"\nFirst query AST hash:  {hash1}")
print(f"Second query AST hash: {hash2}")
print(f"Hashes match: {hash1 == hash2}")

# Different query - different hash
result3 = Q.nodes().compute("betweenness_centrality").execute(net)
hash3 = result3.meta.get('provenance', {}).get('query', {}).get('ast_hash')
print(f"\nDifferent query AST hash: {hash3}")
print(f"Different from first: {hash1 != hash3}")

print("\n[TIP] Provenance enables reproducibility and auditability")
print("[TIP] AST hash uniquely identifies query structure")
print("[TIP] Track seeds for stochastic operations")
print("[TIP] Network fingerprint detects data changes")
