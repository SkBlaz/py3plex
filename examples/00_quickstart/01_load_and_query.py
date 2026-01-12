"""
Quickstart: Load dataset and run a simple query.

Demonstrates:
- Loading a built-in dataset
- Running a basic DSL query
- Printing results
"""

from py3plex.datasets import load_aarhus_cs
from py3plex.dsl import Q

# 1. Load network
network = load_aarhus_cs()

# 2. Run query - find nodes with degree > 5
result = (
    Q.nodes()
    .where(degree__gt=5)
    .compute("degree_centrality")
    .execute(network)
)

# 3. Inspect result
print(f"Found {len(result.nodes)} high-degree nodes")
df = result.to_pandas()
print(df.head())
