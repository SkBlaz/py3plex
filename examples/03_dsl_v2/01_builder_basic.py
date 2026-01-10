"""
DSL v2: Minimal builder query.

Demonstrates:
- Basic Q.nodes() builder pattern
- Chaining operations
- Converting to pandas
"""

from py3plex.datasets import load_aarhus_cs
from py3plex.dsl import Q

# 1. Load network
network = load_aarhus_cs()

# 2. Build and execute query
result = (
    Q.nodes()
    .where(degree__gte=5)
    .compute("degree_centrality")
    .sort(by="degree_centrality", descending=True)
    .limit(15)
    .execute(network)
)

# 3. Convert to dataframe
df = result.to_pandas()
print(f"Top 15 nodes by degree centrality:")
print(df[['id', 'layer', 'degree_centrality']].head())
