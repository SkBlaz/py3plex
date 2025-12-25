"""
Node-attribute correlation tools for multilayer networks.

Test correlations between metadata and structural metrics across layers.
Helps identify relationships between node properties and network position.

Authors: py3plex contributors
Date: 2025
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from collections import defaultdict

from py3plex.exceptions import AlgorithmError, NetworkConstructionError

try:
    from scipy.stats import pearsonr, spearmanr, kendalltau
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


def correlate_attributes_with_centrality(
    network: Any,
    attribute_name: str,
    centrality_type: str = "degree",
    correlation_method: str = "pearson",
    by_layer: bool = True
) -> Dict[Any, Tuple[float, float]]:
    """Correlate node attributes with centrality measures.
    
    Args:
        network: Multilayer network object
        attribute_name: Name of node attribute to correlate
        centrality_type: Type of centrality ('degree', 'betweenness', 'closeness', 'eigenvector')
        correlation_method: Correlation method ('pearson', 'spearman', 'kendall')
        by_layer: If True, compute correlations separately per layer
        
    Returns:
        Dictionary mapping layers (or 'global') to (correlation, p-value) tuples
        
    Example:
        >>> net = load_network(...)
        >>> correlations = correlate_attributes_with_centrality(
        ...     net, 'weight', centrality_type='degree'
        ... )
        >>> for layer, (corr, pval) in correlations.items():
        ...     print(f"{layer}: r={corr:.3f}, p={pval:.3f}")
        
    References:
        - Newman, M. E. (2002). "Assortative mixing in networks."
          Physical Review Letters, 89(20), 208701.
    """
    if not SCIPY_AVAILABLE:
        raise ImportError("scipy is required for correlation analysis")
    
    if not hasattr(network, 'core_network') or network.core_network is None:
        raise NetworkConstructionError(
            "Network object has no core_network attribute",
            suggestions=[
                "Ensure the network has been properly initialized",
                "Add edges to the network before computing correlations",
                "Check that the network object is a valid multilayer network"
            ]
        )
    
    import networkx as nx
    
    G = network.core_network
    
    # Compute centrality
    valid_centrality_types = ["degree", "betweenness", "closeness", "eigenvector"]
    if centrality_type == "degree":
        centrality = dict(G.degree())
    elif centrality_type == "betweenness":
        centrality = nx.betweenness_centrality(G)
    elif centrality_type == "closeness":
        centrality = nx.closeness_centrality(G)
    elif centrality_type == "eigenvector":
        try:
            centrality = nx.eigenvector_centrality(G, max_iter=1000)
        except:
            centrality = dict(G.degree())  # Fallback
    else:
        from py3plex.errors import find_similar
        did_you_mean = find_similar(centrality_type, valid_centrality_types)
        raise AlgorithmError(
            f"Centrality type '{centrality_type}' is not recognized",
            algorithm_name=centrality_type,
            valid_algorithms=valid_centrality_types,
            suggestions=[
                f"Valid centrality types: {', '.join(valid_centrality_types)}",
                "Use 'degree' for node connectivity",
                "Use 'betweenness' for bridge nodes",
                "Use 'closeness' for central nodes"
            ],
            did_you_mean=did_you_mean
        )
    
    # Extract node attributes
    node_attrs = nx.get_node_attributes(G, attribute_name)
    
    if by_layer:
        # Group by layer
        layer_data = defaultdict(lambda: {'attrs': [], 'centrality': []})
        
        for node in G.nodes():
            if node in node_attrs and node in centrality:
                if isinstance(node, tuple) and len(node) >= 2:
                    layer = node[1]
                else:
                    layer = 'default'
                
                layer_data[layer]['attrs'].append(node_attrs[node])
                layer_data[layer]['centrality'].append(centrality[node])
        
        # Compute correlations per layer
        results = {}
        for layer, data in layer_data.items():
            attrs = np.array(data['attrs'])
            cent = np.array(data['centrality'])
            
            if len(attrs) > 1:
                corr, pval = _compute_correlation(attrs, cent, correlation_method)
                results[layer] = (corr, pval)
        
        return results
    
    else:
        # Global correlation
        attrs = []
        cent = []
        
        for node in G.nodes():
            if node in node_attrs and node in centrality:
                attrs.append(node_attrs[node])
                cent.append(centrality[node])
        
        if len(attrs) > 1:
            corr, pval = _compute_correlation(np.array(attrs), np.array(cent), correlation_method)
            return {'global': (corr, pval)}
        
        return {'global': (0.0, 1.0)}


def correlate_attributes_across_layers(
    network: Any,
    attribute_name: str,
    correlation_method: str = "pearson"
) -> Dict[Tuple[Any, Any], Tuple[float, float]]:
    """Correlate node attribute values across layers.
    
    Tests whether nodes with high attribute values in one layer
    also have high values in other layers.
    
    Args:
        network: Multilayer network object
        attribute_name: Name of node attribute
        correlation_method: Correlation method ('pearson', 'spearman', 'kendall')
        
    Returns:
        Dictionary mapping layer pairs to (correlation, p-value)
        
    Example:
        >>> net = load_network(...)
        >>> correlations = correlate_attributes_across_layers(net, 'importance')
        >>> for (l1, l2), (corr, pval) in correlations.items():
        ...     print(f"{l1}-{l2}: r={corr:.3f}")
    """
    if not SCIPY_AVAILABLE:
        raise ImportError("scipy is required for correlation analysis")
    
    if not hasattr(network, 'core_network') or network.core_network is None:
        raise NetworkConstructionError(
            "Network object has no core_network attribute",
            suggestions=[
                "Ensure the network has been properly initialized",
                "Add edges to the network before analysis"
            ]
        )
    
    import networkx as nx
    
    G = network.core_network
    node_attrs = nx.get_node_attributes(G, attribute_name)
    
    # Group attributes by layer and node_id
    layer_attrs = defaultdict(dict)
    
    for node, value in node_attrs.items():
        if isinstance(node, tuple) and len(node) >= 2:
            node_id, layer = node[0], node[1]
            layer_attrs[layer][node_id] = value
    
    # Compute pairwise correlations between layers
    results = {}
    layers = list(layer_attrs.keys())
    
    for i, l1 in enumerate(layers):
        for l2 in layers[i+1:]:
            # Find common nodes
            common_nodes = set(layer_attrs[l1].keys()) & set(layer_attrs[l2].keys())
            
            if len(common_nodes) > 1:
                vals1 = np.array([layer_attrs[l1][node] for node in sorted(common_nodes)])
                vals2 = np.array([layer_attrs[l2][node] for node in sorted(common_nodes)])
                
                corr, pval = _compute_correlation(vals1, vals2, correlation_method)
                results[(l1, l2)] = (corr, pval)
    
    return results


def attribute_structural_contingency(
    network: Any,
    attribute_name: str,
    structural_property: str = "degree",
    bins: int = 5
) -> Dict[str, np.ndarray]:
    """Create contingency table of attribute vs. structural property.
    
    Discretizes both attribute and structural property into bins
    and computes a contingency table showing their joint distribution.
    
    Args:
        network: Multilayer network object
        attribute_name: Name of node attribute
        structural_property: Structural property ('degree', 'betweenness', etc.)
        bins: Number of bins for discretization
        
    Returns:
        Dictionary with 'contingency_table', 'chi2', 'p_value'
        
    Example:
        >>> net = load_network(...)
        >>> result = attribute_structural_contingency(net, 'age', 'degree')
        >>> print(result['contingency_table'])
        >>> print(f"Chi-square: {result['chi2']}, p-value: {result['p_value']}")
    """
    if not hasattr(network, 'core_network') or network.core_network is None:
        raise NetworkConstructionError(
            "Network object has no core_network attribute",
            suggestions=[
                "Ensure the network has been properly initialized",
                "Add edges to the network before analysis"
            ]
        )
    
    import networkx as nx
    
    G = network.core_network
    
    # Get structural property
    valid_properties = ["degree", "betweenness", "closeness"]
    if structural_property == "degree":
        struct_values = dict(G.degree())
    elif structural_property == "betweenness":
        struct_values = nx.betweenness_centrality(G)
    elif structural_property == "closeness":
        struct_values = nx.closeness_centrality(G)
    else:
        from py3plex.errors import find_similar
        did_you_mean = find_similar(structural_property, valid_properties)
        raise AlgorithmError(
            f"Structural property '{structural_property}' is not recognized",
            algorithm_name=structural_property,
            valid_algorithms=valid_properties,
            did_you_mean=did_you_mean
        )
    
    # Get node attributes
    node_attrs = nx.get_node_attributes(G, attribute_name)
    
    # Collect paired values
    attr_vals = []
    struct_vals = []
    
    for node in G.nodes():
        if node in node_attrs and node in struct_values:
            attr_vals.append(node_attrs[node])
            struct_vals.append(struct_values[node])
    
    if len(attr_vals) < 2:
        return {'contingency_table': np.array([[0]]), 'chi2': 0, 'p_value': 1}
    
    # Discretize into bins
    attr_bins = np.linspace(min(attr_vals), max(attr_vals), bins + 1)
    struct_bins = np.linspace(min(struct_vals), max(struct_vals), bins + 1)
    
    attr_binned = np.digitize(attr_vals, attr_bins[:-1]) - 1
    struct_binned = np.digitize(struct_vals, struct_bins[:-1]) - 1
    
    # Clamp to valid range
    attr_binned = np.clip(attr_binned, 0, bins - 1)
    struct_binned = np.clip(struct_binned, 0, bins - 1)
    
    # Create contingency table
    contingency = np.zeros((bins, bins))
    for a, s in zip(attr_binned, struct_binned):
        contingency[a, s] += 1
    
    # Compute chi-square test
    try:
        from scipy.stats import chi2_contingency
        chi2, p_value, _, _ = chi2_contingency(contingency)
    except:
        chi2, p_value = 0, 1
    
    return {
        'contingency_table': contingency,
        'chi2': chi2,
        'p_value': p_value,
        'attribute_bins': attr_bins,
        'structural_bins': struct_bins
    }


def _compute_correlation(x: np.ndarray, y: np.ndarray, method: str) -> Tuple[float, float]:
    """Compute correlation between two arrays.
    
    Args:
        x: First array
        y: Second array
        method: Correlation method
        
    Returns:
        Tuple of (correlation, p-value)
    """
    valid_methods = ["pearson", "spearman", "kendall"]
    if method == "pearson":
        return pearsonr(x, y)
    elif method == "spearman":
        return spearmanr(x, y)
    elif method == "kendall":
        return kendalltau(x, y)
    else:
        from py3plex.errors import find_similar
        did_you_mean = find_similar(method, valid_methods)
        raise AlgorithmError(
            f"Correlation method '{method}' is not recognized",
            algorithm_name=method,
            valid_algorithms=valid_methods,
            suggestions=[
                "Use 'pearson' for linear correlations",
                "Use 'spearman' for monotonic correlations",
                "Use 'kendall' for rank correlations"
            ],
            did_you_mean=did_you_mean
        )


def multilayer_assortativity(
    network: Any,
    attribute_name: Optional[str] = None,
    by_layer: bool = True
) -> Dict[Any, float]:
    """Compute assortativity coefficient for multilayer network.
    
    Measures tendency of nodes to connect to similar nodes (homophily).
    
    Args:
        network: Multilayer network object
        attribute_name: Node attribute for assortativity (None for degree assortativity)
        by_layer: Compute per layer or globally
        
    Returns:
        Dictionary mapping layers to assortativity coefficients
        
    References:
        - Newman, M. E. (2002). "Assortative mixing in networks."
          Physical Review Letters, 89(20), 208701.
    """
    if not hasattr(network, 'core_network') or network.core_network is None:
        raise NetworkConstructionError(
            "Network object has no core_network attribute",
            suggestions=[
                "Ensure the network has been properly initialized",
                "Add edges to the network before analysis"
            ]
        )
    
    import networkx as nx
    
    G = network.core_network
    
    if by_layer:
        # Extract layers
        layers = defaultdict(list)
        for node in G.nodes():
            if isinstance(node, tuple) and len(node) >= 2:
                layer = node[1]
                layers[layer].append(node)
        
        results = {}
        for layer, nodes in layers.items():
            subgraph = G.subgraph(nodes)
            
            try:
                if attribute_name is None:
                    # Degree assortativity
                    assortativity = nx.degree_assortativity_coefficient(subgraph)
                else:
                    # Attribute assortativity
                    assortativity = nx.attribute_assortativity_coefficient(
                        subgraph, attribute_name
                    )
                results[layer] = assortativity
            except:
                results[layer] = 0.0
        
        return results
    
    else:
        # Global assortativity
        try:
            if attribute_name is None:
                assortativity = nx.degree_assortativity_coefficient(G)
            else:
                assortativity = nx.attribute_assortativity_coefficient(G, attribute_name)
            return {'global': assortativity}
        except:
            return {'global': 0.0}
