"""
Basic queries: Filter by degree.

Demonstrates:
- Filtering nodes by degree
- Using comparison operators
"""

from py3plex.datasets import load_aarhus_cs
from py3plex.dsl import Q

# 1. Load network
network = load_aarhus_cs()

# 2. Filter high-degree nodes
result = (
    Q.nodes()
    .where(degree__gt=10)
    .execute(network)
)

# 3. Print result
print(f"High-degree nodes: {len(result.nodes)}")
df = result.to_pandas()
print(df[['id', 'layer']].head())
