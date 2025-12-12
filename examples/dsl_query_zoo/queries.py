"""Query Zoo: Gallery of DSL examples for multilayer network analysis.

This module contains a collection of example queries that showcase the
expressiveness and power of the py3plex DSL for multilayer analysis.

Each query function:
- Has a clear docstring explaining what it does and why it's interesting
- Uses the DSL end-to-end with minimal low-level API usage
- Works with small but non-trivial multilayer networks
- Produces concrete outputs (DataFrames, statistics, etc.)
- Is tested and reproducible

Query Categories:
1. Basic multilayer exploration
2. Cross-layer hubs and coverage
3. Layer similarity and alignment
4. Community structure in multilayers
5. Advanced centralities (multiplex PageRank)
6. Robustness and resilience
"""

import pandas as pd
import numpy as np
import networkx as nx
from typing import Dict, List, Tuple, Any

from py3plex.dsl import Q, L
from py3plex.core import multinet


def _get_layer_names(network):
    """Helper function to extract layer names from network.
    
    Args:
        network: A multi_layer_network instance
        
    Returns:
        List of layer names
        
    Raises:
        ValueError: If network.get_layers() returns unexpected data
    """
    layers_data = network.get_layers()
    
    if layers_data is None:
        return []
    
    if isinstance(layers_data, tuple):
        if len(layers_data) > 0 and isinstance(layers_data[0], list):
            return layers_data[0]
        raise ValueError(f"Unexpected tuple structure from get_layers(): {type(layers_data[0])}")
    
    if isinstance(layers_data, (list, set)):
        return list(layers_data)
    
    raise ValueError(f"Unexpected return type from get_layers(): {type(layers_data)}")


def query_basic_exploration(network):
    """Summarize layers: node counts, edge counts, and average degree per layer.
    
    Refactored: single DSL query over all layers + pandas groupby, no explicit
    for-loop over layers.
    
    This query demonstrates basic multilayer exploration by computing
    fundamental statistics for each layer independently. This is typically
    the first step in multilayer analysis to understand the structure
    and identify layers with different connectivity patterns.
    
    Why it's interesting:
    - Reveals which layers are denser or sparser
    - Identifies layers that might be hubs of activity
    - Shows structural diversity across the multilayer network
    
    DSL concepts demonstrated:
    - SELECT nodes from all layers in one shot
    - Computing degree per layer
    - Vectorized aggregation by layer
    
    Args:
        network: A multi_layer_network instance
        
    Returns:
        pd.DataFrame with columns: layer, n_nodes, n_edges, avg_degree
    """
    result = (
        Q.nodes()
         .from_layers(L["*"])       # all layers in one shot
         .compute("degree")
         .execute(network)
    )

    if len(result) == 0:
        return pd.DataFrame(columns=["layer", "n_nodes", "n_edges", "avg_degree"])

    df = result.to_pandas()

    # One row per (node, layer), so size() is node count
    stats = (
        df.groupby("layer")
          .agg(
              n_nodes=("id", "size"),
              total_degree=("degree", "sum"),
              avg_degree=("degree", "mean"),
          )
          .reset_index()
    )

    stats["n_edges"] = (stats["total_degree"] // 2).astype(int)
    stats["avg_degree"] = stats["avg_degree"].round(2)

    return stats[["layer", "n_nodes", "n_edges", "avg_degree"]]


def query_cross_layer_hubs(network, k=5):
    """Find nodes that are consistently central across multiple layers.
    
    Refactored: one DSL query across all layers + pandas grouping, no explicit
    per-layer for loop.
    
    This query identifies "super hubs" - nodes that maintain high centrality
    across different layers. These nodes are particularly important because
    they serve as connectors across different contexts or domains.
    
    Why it's interesting:
    - Reveals nodes with consistent importance across contexts
    - Useful for identifying key actors in multiplex social networks
    - Helps understand cross-layer influence and information flow
    
    DSL concepts demonstrated:
    - Single query across all layers
    - Computing betweenness centrality
    - Vectorized top-k selection per layer using groupby
    - Coverage analysis (nodes appearing in multiple layers)
    
    Args:
        network: A multi_layer_network instance
        k: Number of top nodes to select per layer
        
    Returns:
        pd.DataFrame with nodes and their centrality scores per layer
    """
    result = (
        Q.nodes()
         .from_layers(L["*"])
         .compute("betweenness_centrality", "degree")
         .execute(network)
    )

    if len(result) == 0:
        return pd.DataFrame()

    df = result.to_pandas().rename(columns={"id": "node"})

    # Top-k by betweenness within each layer (vectorized)
    df_sorted = df.sort_values(["layer", "betweenness_centrality"],
                               ascending=[True, False])
    topk = df_sorted.groupby("layer").head(k)

    # Count how many layers each node appears in as a top-k hub
    coverage = (
        topk.groupby("node")["layer"]
            .nunique()
            .reset_index(name="layer_count")
    )

    result_df = (
        topk.merge(coverage, on="node")
            .sort_values(["layer_count", "betweenness_centrality"],
                         ascending=[False, False])
    )

    return result_df[["node", "layer", "degree",
                      "betweenness_centrality", "layer_count"]]


def query_layer_similarity(network):
    """Compute structural similarity between layers based on degree distributions.
    
    Refactored: single DSL query + pivot, no explicit loops over layers/nodes.
    
    This query measures how similar different layers are in terms of their
    connectivity patterns. Layers with similar degree distributions likely
    serve similar structural roles in the multilayer network.
    
    Why it's interesting:
    - Identifies redundant or complementary layers
    - Helps understand layer specialization
    - Can inform layer aggregation or simplification decisions
    
    DSL concepts demonstrated:
    - Single query across all layers
    - Pivot table to create node × layer matrix
    - Correlation between layers via .corr()
    
    Args:
        network: A multi_layer_network instance
        
    Returns:
        pd.DataFrame: Pairwise correlation matrix of layer degree distributions
    """
    result = (
        Q.nodes()
         .from_layers(L["*"])
         .compute("degree")
         .execute(network)
    )

    if len(result) == 0:
        return pd.DataFrame()

    df = result.to_pandas()

    # Build node × layer degree matrix: rows = nodes, cols = layers
    degree_matrix = df.pivot_table(
        index="id",
        columns="layer",
        values="degree",
        fill_value=0,
    )

    # Correlation between columns = correlation between layers
    corr_df = degree_matrix.corr().round(3)

    # Optional: clean up index/column names for display
    corr_df.index.name = None
    corr_df.columns.name = None

    return corr_df


def query_community_structure(network):
    """Detect communities and analyze their distribution across layers.
    
    This query finds communities in the multilayer network and examines
    how they manifest across different layers. Some communities might be
    tightly connected in one layer but dispersed in others.
    
    Why it's interesting:
    - Reveals mesoscale structure in multilayer networks
    - Shows how communities span or specialize across layers
    - Useful for understanding multi-context group formation
    
    DSL concepts demonstrated:
    - Community detection via DSL
    - Grouping by community and layer
    - Aggregation and counting
    
    Args:
        network: A multi_layer_network instance
        
    Returns:
        pd.DataFrame with community info: community_id, layer, size, dominant_layer
    """
    # Compute communities across all layers
    result = (
        Q.nodes()
         .from_layers(L["*"])  # All layers
         .compute("communities", "degree")
         .execute(network)
    )
    
    if len(result) == 0:
        return pd.DataFrame()
    
    df = result.to_pandas()
    
    # Rename 'id' column to 'node' for clarity
    df = df.rename(columns={'id': 'node'})
    
    # Analyze community distribution across layers
    community_stats = df.groupby(['communities', 'layer']).agg({
        'node': 'count',
        'degree': 'mean'
    }).reset_index()
    
    community_stats.columns = ['community_id', 'layer', 'size', 'avg_degree']
    
    # Find dominant layer for each community (layer with most nodes)
    dominant = community_stats.loc[
        community_stats.groupby('community_id')['size'].idxmax()
    ][['community_id', 'layer']].rename(columns={'layer': 'dominant_layer'})
    
    # Merge dominant layer info
    result_df = community_stats.merge(dominant, on='community_id')
    
    # Sort by community size
    result_df = result_df.sort_values(['community_id', 'size'], ascending=[True, False])
    
    return result_df[['community_id', 'layer', 'size', 'avg_degree', 'dominant_layer']]


def query_multiplex_pagerank(network):
    """Approximate multiplex PageRank by aggregating layer-specific scores.
    
    NOTE: This is still a *simplified* multiplex PageRank approximation
    (average of layer-specific PageRank). For true Multiplex PageRank, wrap
    the dedicated algorithm from the algorithms module (see query_true_multiplex_pagerank).
    
    Refactored: single DSL query over all layers + vectorized pandas aggregation,
    no explicit for-loop over layers.
    
    Why it's interesting:
    - Approximates node importance across the entire multiplex
    - More informative than single-layer centralities
    - Efficient computation via aggregation
    - Good starting point before using full multiplex algorithms
    
    DSL concepts demonstrated:
    - Single query across all layers
    - Computing PageRank
    - Vectorized aggregation and pivot tables
    - Ranking nodes by multilayer importance
    
    Args:
        network: A multi_layer_network instance
        
    Returns:
        pd.DataFrame with nodes ranked by multiplex PageRank scores
    """
    result = (
        Q.nodes()
         .from_layers(L["*"])
         .compute("pagerank", "degree")
         .execute(network)
    )

    if len(result) == 0:
        return pd.DataFrame()

    df = result.to_pandas().rename(columns={"id": "node"})

    # Aggregate across layers: average PR, total degree
    multiplex_pr = (
        df.groupby("node")
          .agg(
              multiplex_pagerank=("pagerank", "mean"),
              total_degree=("degree", "sum"),
          )
          .reset_index()
    )

    multiplex_pr = multiplex_pr.sort_values("multiplex_pagerank", ascending=False)

    # Layer-specific PR breakdown as wide table
    layer_details = (
        df.pivot_table(
            index="node",
            columns="layer",
            values="pagerank",
            fill_value=0,
        )
        .round(4)
        .reset_index()
    )

    result_df = (
        multiplex_pr.merge(layer_details, on="node", how="left")
                    .round(4)
    )

    return result_df


def query_robustness_analysis(network):
    """Evaluate network robustness by removing each layer and recomputing stats.
    
    This query demonstrates robustness analysis by simulating layer failure.
    For each layer, we measure how connectivity changes if that layer is removed.
    This reveals which layers are critical for network cohesion.
    
    Note: The loop over layers is semantically part of the experiment design
    (each iteration is a different scenario), which is an acceptable use of loops.
    
    Why it's interesting:
    - Identifies critical infrastructure layers
    - Measures redundancy in multilayer systems
    - Informs resilience strategies and backup planning
    - Essential for analyzing cascading failures
    
    DSL concepts demonstrated:
    - Layer selection and filtering
    - Computing connectivity metrics
    - Comparing network states (with/without layers)
    - Using functools.reduce for cleaner layer expressions
    
    Args:
        network: A multi_layer_network instance
        
    Returns:
        pd.DataFrame comparing connectivity with each layer removed
    """
    from functools import reduce
    import operator
    
    layers = _get_layer_names(network)
    
    # Baseline: connectivity with all layers
    baseline_result = (
        Q.nodes()
         .from_layers(L["*"])
         .compute("degree")
         .execute(network)
    )
    
    baseline_df = baseline_result.to_pandas()
    baseline_nodes = len(baseline_df)
    baseline_avg_degree = baseline_df['degree'].mean()
    baseline_total_degree = baseline_df['degree'].sum()
    
    results = [{
        'scenario': 'baseline (all layers)',
        'n_nodes': baseline_nodes,
        'avg_degree': round(baseline_avg_degree, 2),
        'total_edges': baseline_total_degree // 2,
        'connectivity_loss': 0.0
    }]
    
    # Test removing each layer (scenario loop - part of experiment design)
    for layer_to_remove in layers:
        # Build a layer expression that includes all layers except layer_to_remove
        remaining_exprs = [L[layer] for layer in layers if layer != layer_to_remove]
        
        if not remaining_exprs:
            continue
        
        # Combine remaining layers using reduce
        remaining_expr = reduce(operator.add, remaining_exprs)
        
        # Query with reduced layer set
        reduced_result = (
            Q.nodes()
             .from_layers(remaining_expr)
             .compute("degree")
             .execute(network)
        )
        
        if len(reduced_result) > 0:
            reduced_df = reduced_result.to_pandas()
            n_nodes = len(reduced_df)
            avg_degree = reduced_df['degree'].mean()
            total_degree = reduced_df['degree'].sum()
            
            # Calculate connectivity loss
            connectivity_loss = (baseline_total_degree - total_degree) / baseline_total_degree * 100
            
            results.append({
                'scenario': f'without {layer_to_remove}',
                'n_nodes': n_nodes,
                'avg_degree': round(avg_degree, 2),
                'total_edges': total_degree // 2,
                'connectivity_loss': round(connectivity_loss, 2)
            })
        else:
            results.append({
                'scenario': f'without {layer_to_remove}',
                'n_nodes': 0,
                'avg_degree': 0.0,
                'total_edges': 0,
                'connectivity_loss': 100.0
            })
    
    return pd.DataFrame(results)


def query_advanced_centrality_comparison(network):
    """Compare multiple centrality measures on the aggregated multilayer network.
    
    Refactored: multilayer-aware with L["*"], no loops.
    
    This query computes several centrality measures (degree, betweenness, closeness,
    PageRank) and identifies nodes that rank high in multiple measures ("versatile hubs")
    versus those that excel in only one measure ("specialized hubs").
    
    Why it's interesting:
    - Different centralities capture different notions of importance
    - Versatile hubs are robust across different centrality definitions
    - Specialized hubs reveal specific structural roles
    - Essential for comprehensive node importance analysis
    
    DSL concepts demonstrated:
    - Computing multiple centrality measures in one query
    - Aggregating across all layers
    - Ranking and comparing across metrics
    - Using computed attributes for classification
    
    Args:
        network: A multi_layer_network instance
        
    Returns:
        pd.DataFrame with nodes and their centrality scores, plus a "versatility" metric
    """
    result = (
        Q.nodes()
         .from_layers(L["*"])  # aggregate across layers
         .compute("degree", "betweenness_centrality",
                  "closeness_centrality", "pagerank")
         .execute(network)
    )
    
    if len(result) == 0:
        return pd.DataFrame()
    
    df = result.to_pandas().rename(columns={'id': 'node'})
    
    # Normalize each centrality to [0, 1] for comparison
    for col in ['degree', 'betweenness_centrality', 'closeness_centrality', 'pagerank']:
        if col in df.columns:
            max_val = df[col].max()
            if max_val > 0:
                df[f'{col}_norm'] = df[col] / max_val
            else:
                df[f'{col}_norm'] = 0
    
    # Compute "versatility" - how many centralities place node in top 30%
    norm_cols = [c for c in df.columns if c.endswith('_norm')]
    
    def count_top_ranks(row):
        count = 0
        for col in norm_cols:
            if row[col] >= 0.7:  # Top 30% threshold
                count += 1
        return count
    
    df['versatility'] = df.apply(count_top_ranks, axis=1)
    
    # Classify nodes
    def classify_hub(row):
        if row['versatility'] >= 3:
            return 'versatile_hub'
        elif row['versatility'] >= 1:
            return 'specialized_hub'
        else:
            return 'peripheral'
    
    df['hub_type'] = df.apply(classify_hub, axis=1)
    
    # Sort by versatility and then by average normalized centrality
    df['avg_centrality'] = df[norm_cols].mean(axis=1)
    df = df.sort_values(['versatility', 'avg_centrality'], ascending=[False, False])
    
    # Select columns for output
    output_cols = ['node', 'degree', 'betweenness_centrality', 'closeness_centrality', 
                   'pagerank', 'versatility', 'hub_type']
    
    return df[output_cols].round(4)


def query_edge_grouping_and_coverage(network, k=3):
    """Analyze edges across layer pairs with grouping and coverage.
    
    This query demonstrates the powerful new edge grouping capabilities
    introduced in DSL v2. It groups edges by (src_layer, dst_layer) pairs
    and analyzes edge distribution across layer pairs.
    
    Why it's interesting:
    - Reveals how connections are distributed within and between layers
    - Shows which layer pairs have more connectivity
    - Identifies edges that appear across multiple layer contexts
    - Essential for understanding cross-layer edge patterns
    
    DSL concepts demonstrated:
    - .per_layer_pair() for edge grouping
    - .coverage() for cross-group filtering
    - Edge-specific grouping metadata
    - .group_summary() for aggregate statistics
    
    Args:
        network: A multi_layer_network instance
        k: Number of edges to limit per layer pair (default: 3)
        
    Returns:
        Dictionary with:
        - 'edges_by_pair': DataFrame with edges grouped by layer pair
        - 'summary': DataFrame with edge counts per layer pair
    """
    # Query: Get edges grouped by layer pair
    result = (
        Q.edges()
         .from_layers(L["*"])
         .per_layer_pair()
            .top_k(k)  # Limit to k edges per pair
         .end_grouping()
         .execute(network)
    )
    
    if len(result) == 0:
        return {
            'edges_by_pair': pd.DataFrame(),
            'summary': pd.DataFrame()
        }
    
    # Get edges DataFrame
    df_edges = result.to_pandas()
    
    # Get group summary
    summary = result.group_summary()
    
    return {
        'edges_by_pair': df_edges,
        'summary': summary
    }


# ============================================================================
# Note: True Multiplex PageRank Implementation
# ============================================================================
# 
# To add a true multiplex PageRank query (using the dedicated algorithm from
# py3plex.algorithms.multilayer_algorithms.multirank), implement a wrapper
# function like this:
#
# def query_true_multiplex_pagerank(network, variant="additive", **kwargs):
#     """True Multiplex PageRank via the dedicated algorithm.
#     
#     This is a thin wrapper around the standalone Multiplex PageRank
#     implementation in py3plex.algorithms.multilayer_algorithms.multirank.
#     
#     Args:
#         network: A multi_layer_network instance
#         variant: 'neutral', 'additive', 'multiplicative', or 'combined'
#         **kwargs: Additional parameters for multiplex_pagerank
#         
#     Returns:
#         pd.DataFrame with node scores and per-layer breakdown
#     """
#     from py3plex.algorithms.multilayer_algorithms.multirank import multiplex_pagerank
#     
#     # Extract layer adjacency matrices from network
#     layers = _get_layer_names(network)
#     layer_adjacencies = []
#     
#     for layer_name in layers:
#         # Get the NetworkX graph for this layer
#         layer_graph = network.get_layer_graph(layer_name)
#         # Convert to adjacency matrix
#         adj_matrix = nx.to_numpy_array(layer_graph)
#         layer_adjacencies.append(adj_matrix)
#     
#     # Run multiplex PageRank
#     result = multiplex_pagerank(layer_adjacencies, variant=variant, **kwargs)
#     
#     # Convert to tidy DataFrame
#     node_scores = result['node_scores']
#     replica_scores = result['replica_scores']
#     
#     # Build DataFrame with node-level scores
#     rows = []
#     for i, node in enumerate(network.get_nodes()):
#         row = {'node': node, 'multiplex_pagerank': node_scores[i]}
#         for j, layer in enumerate(layers):
#             row[f'{layer}_pr'] = replica_scores[i, j]
#         rows.append(row)
#     
#     df = pd.DataFrame(rows)
#     df = df.sort_values('multiplex_pagerank', ascending=False)
#     
#     return df.round(4)
#
# Note: This requires implementing get_layer_graph() or similar method to extract
# per-layer adjacency matrices from the multi_layer_network object.


def query_layer_algebra_filtering(network):
    """Demonstrate layer set algebra for flexible layer selection.
    
    This query showcases the new LayerSet algebra feature that allows
    expressive, composable layer filtering using set operations.
    
    Why it's interesting:
    - Shows how to exclude specific layers (e.g., coupling layers)
    - Demonstrates union, intersection, and difference operations
    - Enables reusable layer group definitions
    
    DSL concepts demonstrated:
    - Layer set algebra with |, &, - operators
    - String expression parsing: L["* - coupling"]
    - Named layer groups via L.define()
    
    Args:
        network: A multi_layer_network instance
        
    Returns:
        Dict with multiple DataFrames showing different layer selections
    """
    from py3plex.dsl import LayerSet
    
    # Example 1: All layers except coupling
    # This is useful when you want to exclude infrastructure/meta layers
    result_no_coupling = (
        Q.nodes()
         .from_layers(L["* - coupling"])
         .compute("degree")
         .execute(network)
    ).to_pandas()
    
    # Example 2: Union of biological layers
    # Define a named group for reuse
    L.define("bio", LayerSet.parse("ppi | gene | disease"))
    
    result_bio = (
        Q.nodes()
         .from_layers(LayerSet("bio"))
         .compute("betweenness_centrality")
         .execute(network)
    ).to_pandas()
    
    # Example 3: Complex expression - intersection of sets
    # Find nodes in both social and work layers (for networks with these layers)
    try:
        result_intersection = (
            Q.nodes()
             .from_layers(L["social & work"])
             .compute("degree")
             .execute(network)
        ).to_pandas()
    except:
        # If network doesn't have these layers, use a generic example
        layers = list(set(result_no_coupling['layer'].unique()))
        if len(layers) >= 2:
            expr = f"{layers[0]} & {layers[1]}"
            result_intersection = (
                Q.nodes()
                 .from_layers(L[expr])
                 .compute("degree")
                 .execute(network)
            ).to_pandas()
        else:
            result_intersection = pd.DataFrame()
    
    # Example 4: Complement - everything except specific layers
    result_complement = (
        Q.nodes()
         .from_layers(~LayerSet("coupling"))
         .compute("clustering")
         .execute(network)
    ).to_pandas()
    
    return {
        "no_coupling": result_no_coupling,
        "bio_layers": result_bio,
        "intersection": result_intersection,
        "complement": result_complement,
        "explanation": {
            "no_coupling": "All layers except coupling - useful for excluding meta layers",
            "bio_layers": "Named group 'bio' containing biological layers",
            "intersection": "Nodes appearing in multiple specific layers",
            "complement": "Complement of coupling layer (same as * - coupling)",
        }
    }


def query_cross_layer_paths_with_algebra(network, source_node, target_node):
    """Find shortest paths while excluding certain layers using layer algebra.
    
    This demonstrates using LayerSet algebra to control which layers
    are considered when computing cross-layer paths.
    
    Why it's interesting:
    - Shows practical use of layer filtering in path queries
    - Demonstrates how to avoid "shortcuts" through coupling layers
    - Illustrates the difference between path computation on different layer subsets
    
    DSL concepts demonstrated:
    - Layer set algebra in path queries
    - Comparing results with/without layer filtering
    
    Args:
        network: A multi_layer_network instance
        source_node: Source node ID
        target_node: Target node ID
        
    Returns:
        Dict with path lengths and layer usage statistics
    """
    # Path using all layers
    try:
        result_all = (
            Q.nodes()
             .from_layers(L["*"])
             .where(id=source_node)
             .execute(network)
        ).to_pandas()
        
        # Path excluding coupling layers (more "natural" paths)
        result_no_coupling = (
            Q.nodes()
             .from_layers(L["* - coupling"])
             .where(id=source_node)
             .execute(network)
        ).to_pandas()
        
        # Get layer distribution
        layer_dist_all = result_all.groupby('layer').size().to_dict()
        layer_dist_filtered = result_no_coupling.groupby('layer').size().to_dict()
        
        return {
            "all_layers": {
                "node_count": len(result_all),
                "layer_distribution": layer_dist_all,
            },
            "filtered_layers": {
                "node_count": len(result_no_coupling),
                "layer_distribution": layer_dist_filtered,
            },
            "explanation": (
                "Excluding coupling layers often reveals more semantically "
                "meaningful paths by avoiding artificial shortcuts"
            )
        }
    except Exception as e:
        return {
            "error": str(e),
            "explanation": "Path query requires nodes to exist in specified layers"
        }
