"""
DSL v2: Query explanation.

Demonstrates:
- Using explain() to understand query execution
- Getting metadata about nodes
- Inspecting neighbors
"""

from py3plex.datasets import load_aarhus_cs
from py3plex.dsl import Q

# 1. Load network
network = load_aarhus_cs()

# 2. Query with explanation
result = (
    Q.nodes()
    .where(degree__gt=8)
    .compute("betweenness_centrality")
    .explain(neighbors_top=3)
    .limit(5)
    .execute(network)
)

# 3. Print explained results
df = result.to_pandas(expand_explanations=True)
print("Top 5 nodes with neighbor information:")
cols_to_show = [c for c in ['id', 'layer', 'betweenness_centrality', 'top_neighbors'] if c in df.columns]
print(df[cols_to_show].head())
