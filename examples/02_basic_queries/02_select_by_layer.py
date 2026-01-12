"""
Basic queries: Select nodes by layer.

Demonstrates:
- Querying nodes in a specific layer
- Using DSL v2 builder API
"""

from py3plex.datasets import load_aarhus_cs
from py3plex.dsl import Q, L

# 1. Load network
network = load_aarhus_cs()

# 2. Query nodes in specific layer
result = (
    Q.nodes()
    .from_layers(L["lunch"])
    .execute(network)
)

# 3. Print result
print(f"Nodes in 'lunch' layer: {len(result.nodes)}")
df = result.to_pandas()
print(df.head())
