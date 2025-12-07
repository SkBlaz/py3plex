# Compute many possible network statistics

from operator import itemgetter
from typing import Any, Dict, Optional

import networkx as nx
import numpy as np
import pandas as pd

# Optional formal verification support
try:
    from icontract import ensure, require

    ICONTRACT_AVAILABLE = True
except ImportError:
    # Create no-op decorators when icontract is not available
    def require(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

    def ensure(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

    ICONTRACT_AVAILABLE = False


@require(lambda top_n: top_n > 0, "top_n must be positive")
@ensure(lambda result, top_n: len(result) <= top_n, "result size must not exceed top_n")
@ensure(
    lambda result: all(isinstance(v, int) and v >= 0 for v in result.values()),
    "all degree values must be non-negative integers",
)
def identify_n_hubs(
    G: nx.Graph, top_n: int = 100, node_type: Optional[str] = None
) -> Dict[Any, int]:
    """
    Identify the top N hub nodes in a network based on degree centrality.

    Args:
        G: NetworkX graph to analyze
        top_n: Number of top hubs to return (default: 100)
        node_type: Optional filter for specific node type

    Returns:
        Dictionary mapping node identifiers to their degree values

    Contracts:
        - Precondition: top_n must be positive
        - Postcondition: result has at most top_n entries
        - Postcondition: all degree values are non-negative integers
    """
    if node_type is not None:
        target_nodes = []
        for n in G.nodes(data=True):
            try:
                if n[0][1] == node_type:
                    target_nodes.append(n[0])
            except (IndexError, TypeError, KeyError):
                pass
    else:
        target_nodes = G.nodes()

    degree_dict = {x: G.degree(x) for x in target_nodes}
    top_n_id = {
        x[0]: x[1]
        for e, x in enumerate(
            sorted(degree_dict.items(), key=itemgetter(1), reverse=True)
        )
        if e < top_n
    }
    return top_n_id


def core_network_statistics(
    G: nx.Graph, labels: Optional[Any] = None, name: str = "example"
) -> pd.DataFrame:
    """
    Compute core statistics for a network.

    Args:
        G: NetworkX graph to analyze
        labels: Optional label matrix with shape attribute
        name: Name identifier for the network (default: "example")

    Returns:
        DataFrame containing network statistics
    """
    nodes = len(G.nodes())
    edges = len(G.edges())
    
    # Convert to simple undirected graph for analysis
    # MultiGraphs need to be converted to simple Graphs for some algorithms
    G_undirected = G.to_undirected()
    if isinstance(G_undirected, nx.MultiGraph):
        G_undirected = nx.Graph(G_undirected)
    
    num_components = len(list(nx.connected_components(G_undirected)))

    try:
        clustering = nx.average_clustering(G_undirected)
    except (nx.NetworkXError, ValueError, ZeroDivisionError):
        clustering = None

    try:
        dx = nx.density(G)
    except (nx.NetworkXError, ZeroDivisionError):
        dx = None

    if labels is not None:
        number_of_classes = labels.shape[1]
    else:
        number_of_classes = None

    node_degree_vector = dict(nx.degree(G)).values()
    mean_degree = np.mean(list(node_degree_vector))

    try:
        diameter = nx.diameter(G)
    except (nx.NetworkXError, ValueError):
        diameter = "intractable"

    try:
        flow_hierarchy = nx.flow_hierarchy(G)
    except (nx.NetworkXError, ValueError, AttributeError):
        flow_hierarchy = "intractable"

    point = {
        "Name": name,
        "classes": number_of_classes,
        "nodes": nodes,
        "edges": edges,
        "diameter": diameter,
        "degree": mean_degree,
        "flow hierarchy": flow_hierarchy,
        "connected components": num_components,
        "clustering coefficient": clustering,
        "density": dx,
    }
    
    # Create DataFrame directly from the data point
    rframe = pd.DataFrame([point])
    return rframe
