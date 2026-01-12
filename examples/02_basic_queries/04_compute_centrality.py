"""
Basic queries: Compute centrality metric.

Demonstrates:
- Computing a single centrality metric
- Accessing metric values
"""

from py3plex.datasets import load_aarhus_cs
from py3plex.dsl import Q

# 1. Load network
network = load_aarhus_cs()

# 2. Compute betweenness centrality
result = (
    Q.nodes()
    .compute("betweenness_centrality")
    .sort(by="betweenness_centrality", descending=True)
    .limit(10)
    .execute(network)
)

# 3. Print top nodes
print("Top 10 nodes by betweenness:")
df = result.to_pandas()
print(df[['id', 'layer', 'betweenness_centrality']].head(10))
