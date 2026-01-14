#!/usr/bin/env python3
"""
Flagship Example: Comprehensive Multilayer Network Analysis

This example demonstrates the full py3plex workflow for analyzing multilayer biological networks:
1. Automated community detection with Pareto-optimal multi-objective selection
2. Uncertainty quantification for robustness assessment
3. Advanced DSL queries for identifying key hub genes across layers
4. Integration of community structure with centrality analysis

Features demonstrated:
- AutoCommunity with multi-objective optimization
- Uncertainty quantification (UQ) for confidence intervals
- Layer-wise analysis with cross-layer coverage filtering
- Composite scoring and interpretability
"""

from py3plex.core import datasets
from py3plex.dsl import Q
from py3plex.algorithms.community_detection import auto_select_community

# 1. Load multilayer biological network
net = datasets.fetch_multilayer("human_ppi_gene_disease_drug")

# 2. Automated community detection with multi-objective selection
best = auto_select_community(
    net,
    mode="pareto",              # Pareto-optimal selection (no single objective)
    fast=False,                 # Full evaluation
    uq=True,                    # Uncertainty quantification enabled
    uq_n_samples=30,           # 30 perturbed runs for robustness
    uq_method="seed",          # Vary random seeds
    seed=42,                   # Reproducibility
)

# Assign discovered communities to network
net.assign_partition(best.partition)

# Set node-level community stability attributes
if hasattr(best, 'community_stats') and best.community_stats.node_confidence:
    for (node, layer), conf in best.community_stats.node_confidence.items():
        net.set_node_attribute(f"{node}_{layer}", "community_stability", conf)
    
    # Set community IDs as node attributes
    for (node, layer), comm_id in best.partition.items():
        net.set_node_attribute(f"{node}_{layer}", "community_id", comm_id)

# 3. Advanced DSL query: Find robust master regulator gene candidates
# Goal: Identify genes that are central hubs in multiple layers with high confidence
res = (
    Q.nodes()
     .node_type("gene")                            # Focus on gene nodes
     .where(degree__gt=3)                          # Filter out peripheral genes (degree > 3)
     .compute("degree_centrality", "betweenness_centrality", "pagerank")
     .uq(method="perturbation", n_samples=100, ci=0.95, seed=42)  # UQ with 100 samples, 95% CI
     .per_layer()                                  # Group analysis by layer
        .top_k(30, "betweenness_centrality__mean") # Top 30 genes per layer by mean betweenness
     .end_grouping()
     .coverage(mode="at_least", k=2)               # Keep only genes that are hubs in ≥2 layers
     .mutate(                                      # Composite influence score
        score=lambda r: (
            0.5 * r.get("betweenness_centrality__mean", 0) +
            0.3 * r.get("pagerank__mean", 0) +
            0.2 * r.get("degree_centrality__mean", 0)
        )
     )
     .sort(by="score", descending=True)
     .limit(20)                                    # Top 20 final candidates
     .explain(neighbors_top=5)                     # Enrich with top 5 interaction partners
     .execute(net)
)

# 4. Display results
df = res.to_pandas(expand_uncertainty=True, expand_explanations=True)
print(df[[
    "id","layer","community_id","community_stability",
    "betweenness_centrality__mean",
    "betweenness_centrality_ci95_low",
    "betweenness_centrality_ci95_high",
    "score","top_neighbors"
]].head(10))

# 5. Bonus: Stochastic Block Model (SBM) Analysis
# SBM provides a principled generative model for community structure
print("\n" + "="*80)
print("Bonus: Stochastic Block Model Analysis")
print("="*80)

sbm_result = auto_select_community(
    net,
    mode="pareto",
    fast=True,              # Fast mode for computationally intensive SBM
    seed=42,
)

print(f"SBM-based algorithm: {sbm_result.algorithm['name']}")
if hasattr(sbm_result, 'community_stats'):
    print(f"Communities found: {sbm_result.community_stats.n_communities}")
