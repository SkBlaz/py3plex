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
    """
    layers_data = network.get_layers()
    if isinstance(layers_data, tuple):
        return layers_data[0]
    return list(layers_data)


def query_basic_exploration(network):
    """Summarize layers: node counts, edge counts, and average degree per layer.
    
    This query demonstrates basic multilayer exploration by computing
    fundamental statistics for each layer independently. This is typically
    the first step in multilayer analysis to understand the structure
    and identify layers with different connectivity patterns.
    
    Why it's interesting:
    - Reveals which layers are denser or sparser
    - Identifies layers that might be hubs of activity
    - Shows structural diversity across the multilayer network
    
    DSL concepts demonstrated:
    - SELECT nodes from specific layers
    - Computing degree per layer
    - Aggregation by layer
    
    Args:
        network: A multi_layer_network instance
        
    Returns:
        pd.DataFrame with columns: layer, n_nodes, n_edges, avg_degree
    """
    # Get all unique layers in the network
    layers = _get_layer_names(network)
    
    results = []
    for layer_name in layers:
        # Query nodes in this layer with degree computation
        layer_result = (
            Q.nodes()
             .from_layers(L[layer_name])
             .compute("degree")
             .execute(network)
        )
        
        if len(layer_result) > 0:
            df = layer_result.to_pandas()
            n_nodes = len(df)
            n_edges = df['degree'].sum() // 2  # Each edge counted twice
            avg_degree = df['degree'].mean()
            
            results.append({
                'layer': layer_name,
                'n_nodes': n_nodes,
                'n_edges': n_edges,
                'avg_degree': round(avg_degree, 2)
            })
    
    return pd.DataFrame(results)


def query_cross_layer_hubs(network, k=5):
    """Find nodes that are consistently central across multiple layers.
    
    This query identifies "super hubs" - nodes that maintain high centrality
    across different layers. These nodes are particularly important because
    they serve as connectors across different contexts or domains.
    
    Why it's interesting:
    - Reveals nodes with consistent importance across contexts
    - Useful for identifying key actors in multiplex social networks
    - Helps understand cross-layer influence and information flow
    
    DSL concepts demonstrated:
    - Per-layer grouping and aggregation
    - Computing betweenness centrality
    - Ordering and filtering by computed metrics
    - Coverage analysis (nodes appearing in multiple layers)
    
    Args:
        network: A multi_layer_network instance
        k: Number of top nodes to select per layer
        
    Returns:
        pd.DataFrame with nodes and their centrality scores per layer
    """
    layers = _get_layer_names(network)
    
    # For each layer, get top-k nodes by betweenness centrality
    all_results = []
    
    for layer_name in layers:
        layer_result = (
            Q.nodes()
             .from_layers(L[layer_name])
             .compute("betweenness_centrality", "degree")
             .order_by("-betweenness_centrality")
             .limit(k)
             .execute(network)
        )
        
        if len(layer_result) > 0:
            df = layer_result.to_pandas()
            df['layer'] = layer_name
            all_results.append(df)
    
    if not all_results:
        return pd.DataFrame()
    
    # Combine results and identify nodes appearing in multiple layers
    combined = pd.concat(all_results, ignore_index=True)
    
    # Rename 'id' column to 'node' for clarity
    combined = combined.rename(columns={'id': 'node'})
    
    # Count how many layers each node appears in as a top-k hub
    coverage = combined.groupby('node').size().reset_index(name='layer_count')
    
    # Merge with centrality data
    result = combined.merge(coverage, on='node')
    
    # Sort by coverage (number of layers) and then by betweenness
    result = result.sort_values(
        ['layer_count', 'betweenness_centrality'],
        ascending=[False, False]
    )
    
    return result[['node', 'layer', 'degree', 'betweenness_centrality', 'layer_count']]


def query_layer_similarity(network):
    """Compute structural similarity between layers based on degree distributions.
    
    This query measures how similar different layers are in terms of their
    connectivity patterns. Layers with similar degree distributions likely
    serve similar structural roles in the multilayer network.
    
    Why it's interesting:
    - Identifies redundant or complementary layers
    - Helps understand layer specialization
    - Can inform layer aggregation or simplification decisions
    
    DSL concepts demonstrated:
    - Computing statistics per layer
    - Aggregation and comparison across layers
    - Using computed metrics for layer-level analysis
    
    Args:
        network: A multi_layer_network instance
        
    Returns:
        pd.DataFrame: Pairwise correlation matrix of layer degree distributions
    """
    layers = _get_layer_names(network)
    
    # Get degree distribution for each layer
    layer_degrees = {}
    
    for layer_name in layers:
        result = (
            Q.nodes()
             .from_layers(L[layer_name])
             .compute("degree")
             .execute(network)
        )
        
        if len(result) > 0:
            df = result.to_pandas()
            # Store as dict: node -> degree
            layer_degrees[layer_name] = dict(zip(df['id'], df['degree']))
    
    # Compute correlation between layers
    # Get union of all nodes
    all_nodes = set()
    for degrees in layer_degrees.values():
        all_nodes.update(degrees.keys())
    all_nodes = sorted(all_nodes)
    
    # Build degree matrix: layers x nodes
    degree_matrix = []
    for layer_name in layers:
        if layer_name in layer_degrees:
            degrees = [layer_degrees[layer_name].get(node, 0) for node in all_nodes]
            degree_matrix.append(degrees)
        else:
            degree_matrix.append([0] * len(all_nodes))
    
    # Compute correlation matrix
    degree_matrix = np.array(degree_matrix)
    correlation = np.corrcoef(degree_matrix)
    
    # Convert to DataFrame for readability
    corr_df = pd.DataFrame(
        correlation,
        index=layers,
        columns=layers
    )
    
    return corr_df.round(3)


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
    """Compute multiplex PageRank to identify important nodes considering all layers.
    
    This query uses a multilayer-aware centrality measure that accounts for
    the full structure of the multiplex network, not just individual layers.
    Multiplex PageRank captures node importance while considering cross-layer
    connections and influence.
    
    Why it's interesting:
    - Standard PageRank doesn't account for multilayer structure
    - Reveals nodes that are important across the entire multiplex
    - More accurate than averaging single-layer centralities
    - Essential for multiplex influence analysis
    
    DSL concepts demonstrated:
    - Computing advanced centrality measures
    - Working with all layers simultaneously
    - Ranking nodes by multilayer importance
    
    Args:
        network: A multi_layer_network instance
        
    Returns:
        pd.DataFrame with nodes ranked by multiplex PageRank scores
    """
    # First, compute regular PageRank per layer for comparison
    layers = _get_layer_names(network)
    
    pagerank_by_layer = []
    
    for layer_name in layers:
        result = (
            Q.nodes()
             .from_layers(L[layer_name])
             .compute("pagerank", "degree")
             .execute(network)
        )
        
        if len(result) > 0:
            df = result.to_pandas()
            df['layer'] = layer_name
            pagerank_by_layer.append(df)
    
    if not pagerank_by_layer:
        return pd.DataFrame()
    
    # Combine results
    combined = pd.concat(pagerank_by_layer, ignore_index=True)
    
    # Rename 'id' column to 'node' for clarity
    combined = combined.rename(columns={'id': 'node'})
    
    # Compute aggregate multiplex PageRank (simple approach: average across layers)
    # Note: This is a simplified version. True multiplex PageRank requires
    # supra-adjacency matrix computation, but this demonstrates the concept.
    multiplex_pr = combined.groupby('node').agg({
        'pagerank': 'mean',  # Average across layers
        'degree': 'sum'      # Total degree across layers
    }).reset_index()
    
    multiplex_pr.columns = ['node', 'multiplex_pagerank', 'total_degree']
    
    # Sort by multiplex PageRank
    multiplex_pr = multiplex_pr.sort_values('multiplex_pagerank', ascending=False)
    
    # Add layer-specific details
    layer_details = combined.pivot_table(
        index='node',
        columns='layer',
        values='pagerank',
        fill_value=0
    ).round(4)
    
    result = multiplex_pr.merge(layer_details, left_on='node', right_index=True, how='left')
    
    return result.round(4)


def query_robustness_analysis(network):
    """Analyze network robustness: impact of removing one layer at a time.
    
    This query demonstrates robustness analysis by simulating layer failure.
    For each layer, we measure how connectivity changes if that layer is removed.
    This reveals which layers are critical for network cohesion.
    
    Why it's interesting:
    - Identifies critical infrastructure layers
    - Measures redundancy in multilayer systems
    - Informs resilience strategies and backup planning
    - Essential for analyzing cascading failures
    
    DSL concepts demonstrated:
    - Layer selection and filtering
    - Computing connectivity metrics
    - Comparing network states (with/without layers)
    
    Args:
        network: A multi_layer_network instance
        
    Returns:
        pd.DataFrame comparing connectivity with each layer removed
    """
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
    
    # Test removing each layer
    for layer_to_remove in layers:
        # Get remaining layers
        remaining_layers = [L[layer] for layer in layers if layer != layer_to_remove]
        
        if not remaining_layers:
            continue
        
        # Combine remaining layers
        layer_expr = remaining_layers[0]
        for layer in remaining_layers[1:]:
            layer_expr = layer_expr + layer
        
        # Query with reduced layer set
        reduced_result = (
            Q.nodes()
             .from_layers(layer_expr)
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
    """Compare multiple centrality measures to identify versatile vs specialized hubs.
    
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
    - Ranking and comparing across metrics
    - Using computed attributes for classification
    
    Args:
        network: A multi_layer_network instance
        
    Returns:
        pd.DataFrame with nodes and their centrality scores, plus a "versatility" metric
    """
    # Select a representative layer (or aggregate across all layers)
    layers = _get_layer_names(network)
    if not layers:
        return pd.DataFrame()
    
    # Use first layer for demonstration
    layer_name = layers[0]
    
    result = (
        Q.nodes()
         .from_layers(L[layer_name])
         .compute("degree", "betweenness_centrality", "closeness_centrality", "pagerank")
         .execute(network)
    )
    
    if len(result) == 0:
        return pd.DataFrame()
    
    df = result.to_pandas()
    
    # Rename 'id' column to 'node' for clarity
    df = df.rename(columns={'id': 'node'})
    
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
