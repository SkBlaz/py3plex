"""
DSL v2: Layer algebra.

Demonstrates:
- Layer union operations
- Layer filtering
- Multi-layer queries
"""

from py3plex.datasets import load_aarhus_cs
from py3plex.dsl import Q, L

# 1. Load network
network = load_aarhus_cs()

# 2. Query nodes from multiple layers using union
result = (
    Q.nodes()
    .from_layers(L["lunch"] | L["facebook"])
    .where(degree__gt=3)
    .execute(network)
)

# 3. Print result
print(f"Nodes in lunch OR facebook layers with degree > 3:")
print(f"Found {len(result.nodes)} nodes")
df = result.to_pandas()
print(df[['id', 'layer']].head(10))
