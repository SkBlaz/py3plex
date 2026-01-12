"""
Graph ops: Filter and mutate.

Demonstrates:
- Filtering nodes using lambda
- Adding computed columns with mutate
- Dplyr-style chaining
"""

from py3plex.datasets import load_aarhus_cs
from py3plex.graph_ops import nodes

# 1. Load network
network = load_aarhus_cs()

# 2. Filter and mutate
df = (
    nodes(network)
    .filter(lambda n: n["degree"] > 5)
    .mutate(
        degree_squared=lambda n: n["degree"] ** 2,
        importance=lambda n: n["degree"] * 2.5
    )
    .arrange("importance", reverse=True)
    .to_pandas()
)

# 3. Print result
print("Filtered and mutated nodes:")
print(df[['id', 'degree', 'degree_squared', 'importance']].head(10))
