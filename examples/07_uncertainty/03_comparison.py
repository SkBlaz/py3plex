"""
Uncertainty: Comparison with deterministic result.

Demonstrates:
- Comparing UQ vs deterministic
- Understanding uncertainty impact
- Identifying robust vs fragile nodes
"""

from py3plex.datasets import load_aarhus_cs
from py3plex.dsl import Q

# 1. Load network
network = load_aarhus_cs()

# 2. Deterministic query
deterministic = (
    Q.nodes()
    .compute("degree_centrality")
    .sort(by="degree_centrality", descending=True)
    .limit(10)
    .execute(network)
)

# 3. UQ-enabled query
with_uq = (
    Q.nodes()
    .uq(method="perturbation", n_samples=30, seed=42)
    .compute("degree_centrality")
    .sort(by="degree_centrality", descending=True)
    .limit(10)
    .execute(network)
)

# 4. Compare results
print("Deterministic top 10:")
print(deterministic.to_pandas()[['id', 'degree_centrality']].head())
print("\nWith uncertainty (std shows robustness):")
df_uq = with_uq.to_pandas(expand_uncertainty=True)
print(df_uq[['id', 'degree_centrality', 'degree_centrality_std']].head())
