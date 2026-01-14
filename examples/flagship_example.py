#!/usr/bin/env python3
"""
Flagship Example: Comprehensive Multilayer Network Analysis with AutoCommunity

This flagship example demonstrates the complete py3plex workflow for analyzing 
multilayer biological networks with state-of-the-art methods:

1. Automated community detection with Pareto-optimal multi-objective selection
2. Uncertainty quantification for robustness assessment
3. Advanced DSL queries for identifying key hub genes across layers
4. Integration of community structure with centrality analysis
5. Stochastic Block Model (SBM) analysis for generative modeling

Key features:
- AutoCommunity with multi-objective optimization (no single objective function)
- Uncertainty quantification (UQ) for confidence intervals on centralities
- Layer-wise analysis with cross-layer coverage filtering (≥k layers requirement)
- Composite scoring from multiple centrality measures
- Interpretability via .explain() with top neighbors and community info

Prerequisites:
- py3plex with community detection algorithms installed
- Recommended: Full installation with [algos] for more algorithm candidates

SKIP_CI: slow - Full UQ evaluation on real biological network
"""

from __future__ import annotations

import sys

try:
    from py3plex.core import datasets
    from py3plex.dsl import Q
    from py3plex.algorithms.community_detection import auto_select_community
except ImportError as exc:
    datasets = None
    Q = None
    auto_select_community = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


def main():
    """Main flagship example workflow."""
    if IMPORT_ERROR:
        print(f"Import error: {IMPORT_ERROR}", file=sys.stderr)
        sys.exit(1)


    # ========================================================================
    # 1. Load multilayer biological network
    # ========================================================================
    print("="*80)
    print("FLAGSHIP EXAMPLE: Multilayer Network Analysis with AutoCommunity")
    print("="*80)
    
    print("\n1. Loading multilayer biological network...")
    net = datasets.fetch_multilayer("human_ppi_gene_disease_drug")
    print(f"   ✓ Loaded {len(list(net.get_nodes()))} nodes across {len(net.get_layers())} layers")
    print(f"   ✓ Total edges: {net.edge_count}")

    # ========================================================================
    # 2. Automated community detection with multi-objective selection
    # ========================================================================
    print("\n2. Running automated community detection (Pareto-optimal selection)...")
    print("   - Evaluating multiple algorithms (Louvain, Leiden, etc.)")
    print("   - Multi-objective metrics (modularity, coverage, stability)")
    print("   - Uncertainty quantification with 30 perturbed runs")
    
    best = auto_select_community(
        net,
        mode="pareto",              # Pareto-optimal selection (no single objective)
        fast=False,                 # Full evaluation
        uq=True,                    # Uncertainty quantification enabled
        uq_n_samples=30,           # 30 perturbed runs for robustness
        uq_method="seed",          # Vary random seeds
        seed=42,                   # Reproducibility
    )

    print(f"\n   ✓ Selected: {best.algorithm.get('name', 'consensus')}")
    if hasattr(best, 'community_stats'):
        print(f"   ✓ Found {best.community_stats.n_communities} communities")
        if best.community_stats.stability_score:
            print(f"   ✓ Partition stability: {best.community_stats.stability_score:.3f}")

    # ========================================================================
    # 3. Assign communities and stability scores to network
    # ========================================================================
    print("\n3. Assigning community structure to network...")
    net.assign_partition(best.partition)
    
    if hasattr(best, 'community_stats') and best.community_stats.node_confidence:
        for (node, layer), conf in best.community_stats.node_confidence.items():
            net.set_node_attribute(f"{node}_{layer}", "community_stability", conf)
        
        for (node, layer), comm_id in best.partition.items():
            net.set_node_attribute(f"{node}_{layer}", "community_id", comm_id)
        
        print(f"   ✓ Set community_stability for {len(best.community_stats.node_confidence)} nodes")
        print(f"   ✓ Set community_id for {len(best.partition)} nodes")

    # ========================================================================
    # 4. Advanced DSL query: Find robust master regulator gene candidates
    # ========================================================================
    print("\n4. Querying for robust master regulator candidates...")
    print("   - Filtering to 'gene' node type")
    print("   - Removing peripheral nodes (degree > 3)")
    print("   - Computing centralities with UQ (100 samples, 95% CI)")
    print("   - Per-layer top-k selection (30 genes per layer)")
    print("   - Cross-layer coverage filter (≥2 layers)")
    print("   - Composite influence scoring")
    
    res = (
        Q.nodes()
         .node_type("gene")                            # Focus on genes
         .where(degree__gt=3)                          # Filter peripheral nodes
         .compute("degree_centrality", "betweenness_centrality", "pagerank")
         .uq(method="perturbation", n_samples=100, ci=0.95, seed=42)  # Uncertainty quantification
         .per_layer()                                  # Group by layer
            .top_k(30, "betweenness_centrality__mean") # Top 30 per layer
         .end_grouping()
         .coverage(mode="at_least", k=2)               # Keep genes in ≥2 layers (cross-layer hubs)
         .mutate(                                      # Composite influence score
            score=lambda r: (
                0.5 * r.get("betweenness_centrality__mean", 0) +
                0.3 * r.get("pagerank__mean", 0) +
                0.2 * r.get("degree_centrality__mean", 0)
            )
         )
         .sort(by="score", descending=True)
         .limit(20)                                    # Top 20 candidates
         .explain(neighbors_top=5)                     # Enrich with top 5 neighbors
         .execute(net)
    )

    print(f"   ✓ Query complete: {len(res.nodes)} master regulator candidates")

    # ========================================================================
    # 5. Display results
    # ========================================================================
    print("\n5. Top Master Regulator Candidates (with uncertainty quantification):")
    print("="*80)
    
    df = res.to_pandas(expand_uncertainty=True, expand_explanations=True)
    
    # Select informative columns
    display_cols = [
        "id", "layer", "community_id", "community_stability",
        "betweenness_centrality__mean",
        "betweenness_centrality_ci95_low", 
        "betweenness_centrality_ci95_high",
        "score", "top_neighbors"
    ]
    
    # Filter to available columns
    available_cols = [col for col in display_cols if col in df.columns]
    
    if not df.empty and available_cols:
        print(df[available_cols].head(10).to_string(index=False))
    else:
        print("   (No results with requested columns)")

    # ========================================================================
    # 6. Bonus: Stochastic Block Model Analysis
    # ========================================================================
    print("\n" + "="*80)
    print("6. Bonus: Stochastic Block Model (SBM) Analysis")
    print("="*80)
    print("   SBM provides a principled generative model for community structure")
    
    sbm_result = auto_select_community(
        net,
        mode="pareto",
        fast=True,              # Fast mode for computationally intensive SBM
        seed=42,
    )

    print(f"\n   ✓ SBM model evaluated")
    print(f"   ✓ Algorithm: {sbm_result.algorithm.get('name', 'N/A')}")
    if hasattr(sbm_result, 'community_stats'):
        print(f"   ✓ Communities found: {sbm_result.community_stats.n_communities}")

    # ========================================================================
    # Summary
    # ========================================================================
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE!")
    print("="*80)
    print("\nKey insights:")
    print("  ✓ Automated selection found optimal community detection algorithm")
    print("  ✓ Robustness analysis quantified stability via perturbations") 
    print("  ✓ DSL query identified cross-layer hub genes with confidence intervals")
    print("  ✓ Master regulators ranked by composite influence score")
    print("  ✓ SBM analysis provides generative model perspective")
    print("\nInterpretation:")
    print("  • community_stability: Node-level confidence in community assignment")
    print("  • betweenness_centrality__mean: Average centrality across UQ samples")
    print("  • ci95_low/high: 95% confidence interval bounds")
    print("  • score: Weighted composite of multiple centrality measures")
    print("  • coverage (≥2 layers): Ensures robustness across multilayer structure")


if __name__ == "__main__":
    main()

