"""
DSL v2: Grouping and aggregation.

Demonstrates:
- Grouping by layer
- Computing per-group metrics
- Top-k selection per group
"""

from py3plex.datasets import load_aarhus_cs
from py3plex.dsl import Q

# 1. Load network
network = load_aarhus_cs()

# 2. Query with grouping
result = (
    Q.nodes()
    .per_layer()
    .compute("degree_centrality")
    .top_k(5, "degree_centrality")
    .end_grouping()
    .execute(network)
)

# 3. Print result
print("Top 5 nodes per layer by degree centrality:")
df = result.to_pandas()
print(df[['id', 'layer', 'degree_centrality']])
