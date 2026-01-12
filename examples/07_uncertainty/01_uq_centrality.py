"""
Uncertainty: UQ-enabled centrality computation.

Demonstrates:
- Uncertainty quantification for centrality
- Confidence intervals
- Bootstrapping
"""

from py3plex.datasets import load_aarhus_cs
from py3plex.dsl import Q

# 1. Load network
network = load_aarhus_cs()

# 2. Query with uncertainty quantification
result = (
    Q.nodes()
    .where(degree__gt=5)
    .uq(method="bootstrap", n_samples=50, ci=0.95, seed=42)
    .compute("betweenness_centrality")
    .limit(10)
    .execute(network)
)

# 3. Print with confidence intervals
df = result.to_pandas(expand_uncertainty=True)
print("Top 10 nodes with uncertainty:")
print(df[['id', 'betweenness_centrality', 'betweenness_centrality_std',
          'betweenness_centrality_ci95_low', 'betweenness_centrality_ci95_high']].head())
