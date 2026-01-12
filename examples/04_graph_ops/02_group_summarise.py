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
        count=("id", len),
        avg_degree=("degree", lambda degrees: sum(degrees) / len(degrees)),
        max_degree=("degree", max)
    )
    .to_pandas()
)

# 3. Print summary
print("Per-layer summary statistics:")
print(df)
