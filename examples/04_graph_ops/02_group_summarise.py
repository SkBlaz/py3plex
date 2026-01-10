"""
Graph ops: Group by and summarise.

Demonstrates:
- Grouping by layer
- Computing summary statistics
- Aggregation functions
"""

from py3plex.datasets import load_aarhus_cs
from py3plex.graph_ops import nodes

# 1. Load network
network = load_aarhus_cs()

# 2. Group and summarise
df = (
    nodes(network)
    .group_by("layer")
    .summarise(
        count=lambda g: len(g),
        avg_degree=lambda g: sum(n["degree"] for n in g) / len(g),
        max_degree=lambda g: max(n["degree"] for n in g)
    )
    .to_pandas()
)

# 3. Print summary
print("Per-layer summary statistics:")
print(df)
