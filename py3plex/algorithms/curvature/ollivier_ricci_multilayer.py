"""
Ollivier-Ricci Curvature and Ricci Flow for Multilayer Networks.

This module provides a wrapper around the GraphRicciCurvature library to compute
Ollivier-Ricci curvature and perform Ricci flow on graphs. It is designed to work
seamlessly with py3plex's multilayer network structures.

The module handles the optional dependency on GraphRicciCurvature gracefully,
raising clear error messages when it is not installed.

References:
    - Ni, C. C., Lin, Y. Y., Gao, J., Gu, X. D., & Saucan, E. (2015).
      Ricci curvature of the Internet topology. In 2015 IEEE Conference on
      Computer Communications (INFOCOM) (pp. 2758-2766). IEEE.
    - Ni, C. C., Lin, Y. Y., Luo, F., & Gao, J. (2019).
      Community detection on networks with Ricci flow. Scientific reports, 9(1), 9984.
"""

from typing import Any, Dict, Optional

from py3plex.exceptions import AlgorithmError


class RicciBackendNotAvailable(AlgorithmError):
    """Exception raised when GraphRicciCurvature is not installed.

    This exception provides clear installation instructions for the user.
    """

    def __init__(self, message: Optional[str] = None):
        if message is None:
            message = (
                "GraphRicciCurvature is required for Ollivier-Ricci curvature and Ricci flow. "
                "Install it via: pip install GraphRicciCurvature"
            )
        super().__init__(message)


# Try to import GraphRicciCurvature
try:
    from GraphRicciCurvature.OllivierRicci import OllivierRicci
    GRAPHRICCICURVATURE_AVAILABLE = True
except ImportError:
    GRAPHRICCICURVATURE_AVAILABLE = False
    OllivierRicci = None


def _check_backend_availability():
    """Check if GraphRicciCurvature is available, raise exception if not."""
    if not GRAPHRICCICURVATURE_AVAILABLE:
        raise RicciBackendNotAvailable()


def compute_ollivier_ricci_single_graph(
    G,
    alpha: float = 0.5,
    weight_attr: str = "weight",
    curvature_attr: str = "ricciCurvature",
    verbose: str = "ERROR",
    backend_kwargs: Optional[Dict[str, Any]] = None,
):
    """Compute Ollivier-Ricci curvature for a single graph.

    This function wraps GraphRicciCurvature's OllivierRicci class to compute
    Ollivier-Ricci curvature on all edges of the input graph. The curvature
    values are stored as edge attributes.

    Note: If the input is a MultiGraph or MultiDiGraph, it will be converted
    to a simple Graph/DiGraph by aggregating parallel edges (summing weights).

    Args:
        G: NetworkX graph (Graph, DiGraph, MultiGraph, or MultiDiGraph).
        alpha: Ollivier-Ricci parameter in [0, 1] controlling the mass
            distribution. alpha=0 uses pure neighbors, alpha=0.5 is standard.
        weight_attr: Name of the edge attribute containing edge weights.
            Defaults to "weight".
        curvature_attr: Name of the edge attribute to store computed curvature
            values. Defaults to "ricciCurvature".
        verbose: Verbosity level for GraphRicciCurvature. Options: "INFO",
            "DEBUG", "ERROR". Defaults to "ERROR".
        backend_kwargs: Optional dictionary of additional keyword arguments to
            pass to the OllivierRicci constructor.

    Returns:
        NetworkX graph: The input graph (or converted simple graph) with edge
            curvatures computed and stored in the curvature_attr attribute.

    Raises:
        RicciBackendNotAvailable: If GraphRicciCurvature is not installed.

    Examples:
        >>> import networkx as nx
        >>> from py3plex.algorithms.curvature import compute_ollivier_ricci_single_graph
        >>> G = nx.karate_club_graph()
        >>> G_curved = compute_ollivier_ricci_single_graph(G, alpha=0.5)
        >>> # Edge curvatures are now available in G_curved
        >>> edge = list(G_curved.edges())[0]
        >>> curvature = G_curved[edge[0]][edge[1]]['ricciCurvature']
    """
    _check_backend_availability()

    if backend_kwargs is None:
        backend_kwargs = {}

    # Import NetworkX here to avoid circular imports
    import networkx as nx

    # Convert MultiGraph to simple Graph if necessary
    # GraphRicciCurvature/networkit doesn't handle MultiGraphs well
    is_directed = G.is_directed()
    is_multigraph = isinstance(G, (nx.MultiGraph, nx.MultiDiGraph))

    if is_multigraph:
        # Convert to simple graph by aggregating parallel edges
        if is_directed:
            G_simple = nx.DiGraph()
        else:
            G_simple = nx.Graph()

        G_simple.add_nodes_from(G.nodes(data=True))

        # Aggregate parallel edges - sum weights
        for u, v, data in G.edges(data=True):
            if G_simple.has_edge(u, v):
                # Edge already exists, add to weight
                G_simple[u][v][weight_attr] = (
                    G_simple[u][v].get(weight_attr, 0) + data.get(weight_attr, 1.0)
                )
            else:
                # New edge
                G_simple.add_edge(u, v, **{weight_attr: data.get(weight_attr, 1.0)})

        G_to_process = G_simple
    else:
        G_to_process = G.copy()

    # Ensure all edges have the weight attribute
    for u, v in G_to_process.edges():
        if weight_attr not in G_to_process[u][v]:
            G_to_process[u][v][weight_attr] = 1.0

    # Initialize OllivierRicci
    orc = OllivierRicci(
        G_to_process,
        alpha=alpha,
        weight=weight_attr,
        verbose=verbose,
        **backend_kwargs
    )

    # Compute Ricci curvature
    orc.compute_ricci_curvature()

    # Get the graph with curvature values
    G_curved = orc.G

    # Ensure curvature is stored in the requested attribute name
    # GraphRicciCurvature stores it as 'ricciCurvature' by default
    if curvature_attr != "ricciCurvature":
        for u, v, data in G_curved.edges(data=True):
            if "ricciCurvature" in data:
                data[curvature_attr] = data["ricciCurvature"]

    return G_curved


def compute_ollivier_ricci_flow_single_graph(
    G,
    alpha: float = 0.5,
    iterations: int = 10,
    method: str = "OTD",
    weight_attr: str = "weight",
    curvature_attr: str = "ricciCurvature",
    verbose: str = "ERROR",
    backend_kwargs: Optional[Dict[str, Any]] = None,
):
    """Compute Ollivier-Ricci flow for a single graph.

    This function performs Ricci flow on the input graph by iteratively
    adjusting edge weights based on their Ricci curvature. After Ricci flow,
    edges with negative curvature (indicating community boundaries) will have
    reduced weights, while edges with positive curvature will have increased
    weights.

    Note: If the input is a MultiGraph or MultiDiGraph, it will be converted
    to a simple Graph/DiGraph by aggregating parallel edges (summing weights).

    Args:
        G: NetworkX graph (Graph, DiGraph, MultiGraph, or MultiDiGraph).
        alpha: Ollivier-Ricci parameter in [0, 1] controlling the mass
            distribution. alpha=0 uses pure neighbors, alpha=0.5 is standard.
        iterations: Number of Ricci flow iterations to perform. More iterations
            lead to stronger effects but take longer to compute.
        method: Method for Ricci flow computation. Options: "OTD" (Optimal
            Transport Distance, recommended), "ATD" (Average Transport Distance).
        weight_attr: Name of the edge attribute containing edge weights.
            After Ricci flow, these weights will be updated to reflect the
            Ricci flow metric.
        curvature_attr: Name of the edge attribute to store computed curvature
            values. Defaults to "ricciCurvature".
        verbose: Verbosity level for GraphRicciCurvature. Options: "INFO",
            "DEBUG", "ERROR". Defaults to "ERROR".
        backend_kwargs: Optional dictionary of additional keyword arguments to
            pass to the OllivierRicci constructor.

    Returns:
        NetworkX graph: The input graph (or converted simple graph) with Ricci
            flow applied. Edge weights in weight_attr are updated according to
            the Ricci flow metric, and curvature values are available in
            curvature_attr.

    Raises:
        RicciBackendNotAvailable: If GraphRicciCurvature is not installed.

    Examples:
        >>> import networkx as nx
        >>> from py3plex.algorithms.curvature import compute_ollivier_ricci_flow_single_graph
        >>> G = nx.karate_club_graph()
        >>> G_flow = compute_ollivier_ricci_flow_single_graph(
        ...     G, alpha=0.5, iterations=20, method="OTD"
        ... )
        >>> # Edge weights now reflect Ricci flow
    """
    _check_backend_availability()

    if backend_kwargs is None:
        backend_kwargs = {}

    # Import NetworkX here to avoid circular imports
    import networkx as nx

    # Convert MultiGraph to simple Graph if necessary
    is_directed = G.is_directed()
    is_multigraph = isinstance(G, (nx.MultiGraph, nx.MultiDiGraph))

    if is_multigraph:
        # Convert to simple graph by aggregating parallel edges
        if is_directed:
            G_simple = nx.DiGraph()
        else:
            G_simple = nx.Graph()

        G_simple.add_nodes_from(G.nodes(data=True))

        # Aggregate parallel edges - sum weights
        for u, v, data in G.edges(data=True):
            if G_simple.has_edge(u, v):
                # Edge already exists, add to weight
                G_simple[u][v][weight_attr] = (
                    G_simple[u][v].get(weight_attr, 0) + data.get(weight_attr, 1.0)
                )
            else:
                # New edge
                G_simple.add_edge(u, v, **{weight_attr: data.get(weight_attr, 1.0)})

        G_to_process = G_simple
    else:
        G_to_process = G.copy()

    # Ensure all edges have the weight attribute
    for u, v in G_to_process.edges():
        if weight_attr not in G_to_process[u][v]:
            G_to_process[u][v][weight_attr] = 1.0

    # Initialize OllivierRicci
    orc = OllivierRicci(
        G_to_process,
        alpha=alpha,
        weight=weight_attr,
        method=method,
        verbose=verbose,
        **backend_kwargs
    )

    # Compute Ricci curvature first (required before flow)
    orc.compute_ricci_curvature()

    # Perform Ricci flow
    orc.compute_ricci_flow(iterations=iterations)

    # Get the graph with updated weights and curvature
    G_flow = orc.G

    # Ensure curvature is stored in the requested attribute name
    if curvature_attr != "ricciCurvature":
        for u, v, data in G_flow.edges(data=True):
            if "ricciCurvature" in data:
                data[curvature_attr] = data["ricciCurvature"]

    return G_flow
