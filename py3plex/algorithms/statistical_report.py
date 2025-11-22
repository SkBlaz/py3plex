"""
Graph statistical report generator for multilayer networks.

Auto-generate reports (text/HTML) with:
- Degree statistics
- Layer overlaps
- Clustering coefficients
- Mixing matrices
- Community summaries

Authors: py3plex contributors
Date: 2025
"""

from typing import Any, Dict, List, Optional
import numpy as np
from collections import defaultdict
import json


def generate_statistical_report(
    network: Any,
    output_format: str = "text",
    output_file: Optional[str] = None,
    include_sections: Optional[List[str]] = None
) -> str:
    """Generate comprehensive statistical report for multilayer network.
    
    Args:
        network: Multilayer network object
        output_format: Format for output ('text', 'html', 'json')
        output_file: Optional file path to save report
        include_sections: List of sections to include (None = all):
            - 'basic': Basic statistics
            - 'degree': Degree distribution
            - 'layers': Layer analysis
            - 'clustering': Clustering coefficients
            - 'mixing': Mixing matrices
            - 'communities': Community structure (if available)
            
    Returns:
        Report string in requested format
        
    Example:
        >>> net = load_network(...)
        >>> report = generate_statistical_report(net, 'html', 'report.html')
        >>> print("Report saved to report.html")
    """
    if include_sections is None:
        include_sections = ['basic', 'degree', 'layers', 'clustering', 'mixing']
    
    # Collect statistics
    stats = {}
    
    if 'basic' in include_sections:
        stats['basic'] = _compute_basic_stats(network)
    
    if 'degree' in include_sections:
        stats['degree'] = _compute_degree_stats(network)
    
    if 'layers' in include_sections:
        stats['layers'] = _compute_layer_stats(network)
    
    if 'clustering' in include_sections:
        stats['clustering'] = _compute_clustering_stats(network)
    
    if 'mixing' in include_sections:
        stats['mixing'] = _compute_mixing_matrix(network)
    
    if 'communities' in include_sections:
        stats['communities'] = _compute_community_stats(network)
    
    # Format output
    if output_format == "text":
        report = _format_text_report(stats)
    elif output_format == "html":
        report = _format_html_report(stats)
    elif output_format == "json":
        report = json.dumps(stats, indent=2, default=str)
    else:
        raise ValueError(f"Unknown output format: {output_format}")
    
    # Save to file if requested
    if output_file:
        with open(output_file, 'w') as f:
            f.write(report)
    
    return report


def _compute_basic_stats(network: Any) -> Dict:
    """Compute basic network statistics."""
    if not hasattr(network, 'core_network') or network.core_network is None:
        return {}
    
    G = network.core_network
    
    # Extract layer information
    layers = set()
    for node in G.nodes():
        if isinstance(node, tuple) and len(node) >= 2:
            layers.add(node[1])
    
    stats = {
        'num_nodes': G.number_of_nodes(),
        'num_edges': G.number_of_edges(),
        'num_layers': len(layers),
        'directed': G.is_directed(),
        'density': None,
    }
    
    # Compute density
    try:
        import networkx as nx
        stats['density'] = nx.density(G)
    except:
        pass
    
    return stats


def _compute_degree_stats(network: Any) -> Dict:
    """Compute degree distribution statistics."""
    if not hasattr(network, 'core_network') or network.core_network is None:
        return {}
    
    G = network.core_network
    degrees = [d for n, d in G.degree()]
    
    if not degrees:
        return {}
    
    stats = {
        'mean_degree': np.mean(degrees),
        'median_degree': np.median(degrees),
        'std_degree': np.std(degrees),
        'min_degree': np.min(degrees),
        'max_degree': np.max(degrees),
        'degree_histogram': np.histogram(degrees, bins=20)[0].tolist(),
    }
    
    return stats


def _compute_layer_stats(network: Any) -> Dict:
    """Compute per-layer statistics."""
    if not hasattr(network, 'core_network') or network.core_network is None:
        return {}
    
    G = network.core_network
    
    # Group by layer
    layer_nodes = defaultdict(set)
    layer_edges = defaultdict(int)
    
    for node in G.nodes():
        if isinstance(node, tuple) and len(node) >= 2:
            layer = node[1]
            layer_nodes[layer].add(node)
    
    for u, v in G.edges():
        if isinstance(u, tuple) and isinstance(v, tuple) and len(u) >= 2 and len(v) >= 2:
            if u[1] == v[1]:  # Intra-layer edge
                layer = u[1]
                layer_edges[layer] += 1
    
    # Compute overlap between layers
    layers = list(layer_nodes.keys())
    layer_overlaps = {}
    
    for i, l1 in enumerate(layers):
        for l2 in layers[i+1:]:
            # Node overlap
            nodes1 = {n[0] for n in layer_nodes[l1]}
            nodes2 = {n[0] for n in layer_nodes[l2]}
            overlap = len(nodes1 & nodes2)
            layer_overlaps[f"{l1}-{l2}"] = {
                'overlap': overlap,
                'jaccard': overlap / len(nodes1 | nodes2) if (nodes1 | nodes2) else 0
            }
    
    # Per-layer stats
    layer_stats = {}
    for layer in layers:
        layer_stats[str(layer)] = {
            'num_nodes': len(layer_nodes[layer]),
            'num_edges': layer_edges[layer],
            'density': (2 * layer_edges[layer] / (len(layer_nodes[layer]) * (len(layer_nodes[layer]) - 1))
                       if len(layer_nodes[layer]) > 1 else 0)
        }
    
    return {
        'layer_stats': layer_stats,
        'layer_overlaps': layer_overlaps
    }


def _compute_clustering_stats(network: Any) -> Dict:
    """Compute clustering coefficient statistics."""
    if not hasattr(network, 'core_network') or network.core_network is None:
        return {}
    
    G = network.core_network
    
    try:
        import networkx as nx
        
        # Global clustering
        global_clustering = nx.average_clustering(G.to_undirected())
        
        # Per-node clustering
        clustering = nx.clustering(G.to_undirected())
        clustering_values = list(clustering.values())
        
        stats = {
            'global_clustering': global_clustering,
            'mean_clustering': np.mean(clustering_values) if clustering_values else 0,
            'std_clustering': np.std(clustering_values) if clustering_values else 0,
        }
        
        # Try to compute transitivity
        try:
            stats['transitivity'] = nx.transitivity(G.to_undirected())
        except:
            pass
        
        return stats
    
    except:
        return {}


def _compute_mixing_matrix(network: Any) -> Dict:
    """Compute mixing matrix between layers."""
    if not hasattr(network, 'core_network') or network.core_network is None:
        return {}
    
    G = network.core_network
    
    # Count inter-layer edges
    layers = set()
    for node in G.nodes():
        if isinstance(node, tuple) and len(node) >= 2:
            layers.add(node[1])
    
    layers = sorted(layers)
    n = len(layers)
    
    # Initialize mixing matrix
    mixing = np.zeros((n, n))
    layer_idx = {layer: i for i, layer in enumerate(layers)}
    
    # Count edges between layers
    for u, v in G.edges():
        if isinstance(u, tuple) and isinstance(v, tuple) and len(u) >= 2 and len(v) >= 2:
            l1, l2 = u[1], v[1]
            if l1 in layer_idx and l2 in layer_idx:
                i, j = layer_idx[l1], layer_idx[l2]
                mixing[i, j] += 1
                if not G.is_directed() and i != j:
                    mixing[j, i] += 1
    
    return {
        'mixing_matrix': mixing.tolist(),
        'layer_names': layers,
        'interlayer_edges': int(mixing[np.triu_indices(n, k=1)].sum()),
        'intralayer_edges': int(np.diag(mixing).sum()),
    }


def _compute_community_stats(network: Any) -> Dict:
    """Compute community structure statistics if available."""
    # Check if network has community assignments
    if not hasattr(network, 'ground_truth_communities'):
        return {'available': False}
    
    communities = network.ground_truth_communities
    
    # Count communities
    num_communities = len(set(communities.values()))
    
    # Community sizes
    community_sizes = defaultdict(int)
    for node, comm in communities.items():
        community_sizes[comm] += 1
    
    sizes = list(community_sizes.values())
    
    return {
        'available': True,
        'num_communities': num_communities,
        'mean_community_size': np.mean(sizes),
        'std_community_size': np.std(sizes),
        'min_community_size': np.min(sizes),
        'max_community_size': np.max(sizes),
    }


def _format_text_report(stats: Dict) -> str:
    """Format statistics as plain text report."""
    lines = []
    lines.append("=" * 70)
    lines.append("MULTILAYER NETWORK STATISTICAL REPORT")
    lines.append("=" * 70)
    lines.append("")
    
    # Basic statistics
    if 'basic' in stats:
        lines.append("BASIC STATISTICS")
        lines.append("-" * 70)
        for key, value in stats['basic'].items():
            lines.append(f"  {key}: {value}")
        lines.append("")
    
    # Degree statistics
    if 'degree' in stats:
        lines.append("DEGREE STATISTICS")
        lines.append("-" * 70)
        for key, value in stats['degree'].items():
            if key != 'degree_histogram':
                lines.append(f"  {key}: {value:.4f}" if isinstance(value, float) else f"  {key}: {value}")
        lines.append("")
    
    # Layer statistics
    if 'layers' in stats:
        lines.append("LAYER STATISTICS")
        lines.append("-" * 70)
        if 'layer_stats' in stats['layers']:
            for layer, layer_data in stats['layers']['layer_stats'].items():
                lines.append(f"  Layer {layer}:")
                for key, value in layer_data.items():
                    lines.append(f"    {key}: {value:.4f}" if isinstance(value, float) else f"    {key}: {value}")
        lines.append("")
        
        if 'layer_overlaps' in stats['layers']:
            lines.append("  Layer Overlaps:")
            for pair, overlap_data in stats['layers']['layer_overlaps'].items():
                lines.append(f"    {pair}: overlap={overlap_data['overlap']}, jaccard={overlap_data['jaccard']:.4f}")
        lines.append("")
    
    # Clustering statistics
    if 'clustering' in stats:
        lines.append("CLUSTERING STATISTICS")
        lines.append("-" * 70)
        for key, value in stats['clustering'].items():
            lines.append(f"  {key}: {value:.4f}")
        lines.append("")
    
    # Mixing matrix
    if 'mixing' in stats:
        lines.append("MIXING MATRIX")
        lines.append("-" * 70)
        lines.append(f"  Intralayer edges: {stats['mixing']['intralayer_edges']}")
        lines.append(f"  Interlayer edges: {stats['mixing']['interlayer_edges']}")
        lines.append("")
    
    # Community statistics
    if 'communities' in stats and stats['communities'].get('available'):
        lines.append("COMMUNITY STATISTICS")
        lines.append("-" * 70)
        for key, value in stats['communities'].items():
            if key != 'available':
                lines.append(f"  {key}: {value:.4f}" if isinstance(value, float) else f"  {key}: {value}")
        lines.append("")
    
    lines.append("=" * 70)
    
    return "\n".join(lines)


def _format_html_report(stats: Dict) -> str:
    """Format statistics as HTML report."""
    html = []
    html.append("<!DOCTYPE html>")
    html.append("<html><head>")
    html.append("<title>Multilayer Network Statistical Report</title>")
    html.append("<style>")
    html.append("body { font-family: Arial, sans-serif; margin: 20px; }")
    html.append("h1 { color: #333; }")
    html.append("h2 { color: #666; border-bottom: 2px solid #ddd; padding-bottom: 5px; }")
    html.append("table { border-collapse: collapse; margin: 10px 0; }")
    html.append("td, th { border: 1px solid #ddd; padding: 8px; text-align: left; }")
    html.append("th { background-color: #f2f2f2; }")
    html.append("</style>")
    html.append("</head><body>")
    
    html.append("<h1>Multilayer Network Statistical Report</h1>")
    
    # Basic statistics
    if 'basic' in stats:
        html.append("<h2>Basic Statistics</h2>")
        html.append("<table>")
        for key, value in stats['basic'].items():
            html.append(f"<tr><td><strong>{key}</strong></td><td>{value}</td></tr>")
        html.append("</table>")
    
    # Degree statistics
    if 'degree' in stats:
        html.append("<h2>Degree Statistics</h2>")
        html.append("<table>")
        for key, value in stats['degree'].items():
            if key != 'degree_histogram':
                formatted_value = f"{value:.4f}" if isinstance(value, float) else str(value)
                html.append(f"<tr><td><strong>{key}</strong></td><td>{formatted_value}</td></tr>")
        html.append("</table>")
    
    # Layer statistics
    if 'layers' in stats and 'layer_stats' in stats['layers']:
        html.append("<h2>Layer Statistics</h2>")
        html.append("<table>")
        html.append("<tr><th>Layer</th><th>Nodes</th><th>Edges</th><th>Density</th></tr>")
        for layer, layer_data in stats['layers']['layer_stats'].items():
            html.append(f"<tr>")
            html.append(f"<td>{layer}</td>")
            html.append(f"<td>{layer_data['num_nodes']}</td>")
            html.append(f"<td>{layer_data['num_edges']}</td>")
            html.append(f"<td>{layer_data['density']:.4f}</td>")
            html.append(f"</tr>")
        html.append("</table>")
    
    # Clustering
    if 'clustering' in stats:
        html.append("<h2>Clustering Statistics</h2>")
        html.append("<table>")
        for key, value in stats['clustering'].items():
            html.append(f"<tr><td><strong>{key}</strong></td><td>{value:.4f}</td></tr>")
        html.append("</table>")
    
    # Mixing matrix
    if 'mixing' in stats:
        html.append("<h2>Mixing Matrix</h2>")
        html.append(f"<p><strong>Intralayer edges:</strong> {stats['mixing']['intralayer_edges']}</p>")
        html.append(f"<p><strong>Interlayer edges:</strong> {stats['mixing']['interlayer_edges']}</p>")
    
    html.append("</body></html>")
    
    return "\n".join(html)
