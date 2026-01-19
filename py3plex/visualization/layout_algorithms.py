# set of layout wrappers and algorithms used for visualization.

import itertools
from typing import Any, Dict, Optional

import networkx as nx
import numpy as np

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

from py3plex.core.nx_compat import nx_info

from ..logging_config import get_logger

logger = get_logger(__name__)

try:
    from .fa2.forceatlas2 import ForceAtlas2

    forceImport = True
except ImportError:
    forceImport = False


@require(lambda g: g is not None, "graph must not be None")
@require(lambda g: isinstance(g, nx.Graph), "g must be a NetworkX graph")
@require(lambda g: g.number_of_nodes() > 0, "graph must have at least one node")
@require(lambda gravity: gravity >= 0, "gravity must be non-negative")
@require(lambda scalingRatio: scalingRatio > 0, "scalingRatio must be positive")
@ensure(lambda result: isinstance(result, dict), "result must be a dictionary")
@ensure(
    lambda g, result: len(result) == g.number_of_nodes(),
    "result must have positions for all nodes",
)
def compute_force_directed_layout(
    g: nx.Graph,
    layout_parameters: Optional[Dict[str, Any]] = None,
    verbose: bool = True,
    gravity: float = 0.2,
    strongGravityMode: bool = False,
    barnesHutTheta: float = 1.2,
    edgeWeightInfluence: float = 1,
    scalingRatio: float = 2.0,
    forceImport: bool = True,
    seed: Optional[int] = None,
) -> Dict[Any, np.ndarray]:
    """
    Compute force-directed layout for a graph using ForceAtlas2 or NetworkX spring layout.

    Args:
        g: NetworkX graph to layout
        layout_parameters: Optional parameters to pass to layout algorithm
        verbose: Whether to print progress information
        gravity: Attraction force towards the center (must be non-negative)
        strongGravityMode: Use strong gravity mode
        barnesHutTheta: Barnes-Hut approximation parameter
        edgeWeightInfluence: Influence of edge weights on layout
        scalingRatio: Scaling factor for the layout (must be positive)
        forceImport: Whether to use ForceAtlas2 (if available)
        seed: Random seed for reproducibility in fallback spring layout

    Returns:
        Dictionary mapping nodes to 2D position arrays

    Note:
        For large networks (>1000 nodes), this may be slow. Consider using
        faster layouts (circular, random, spectral) or matrix visualization.

    Contracts:
        - Precondition: graph must not be None and be a NetworkX graph
        - Precondition: graph must have at least one node
        - Precondition: gravity must be non-negative
        - Precondition: scalingRatio must be positive
        - Postcondition: result is a dictionary
        - Postcondition: result has positions for all nodes
    """

    num_nodes = len(g.nodes())

    # Warn about performance for large networks
    if num_nodes > 10000:
        logger.warning(
            "Force-directed layout requested for %d nodes. "
            "This may take a very long time and consume significant memory. "
            "Consider using faster layout algorithms (circular, random, spectral) "
            "or visualizing the adjacency matrix instead.",
            num_nodes,
        )
    elif num_nodes > 5000:
        logger.warning(
            "Force-directed layout requested for %d nodes. "
            "This may take several minutes. Consider reducing iterations or using a faster layout.",
            num_nodes,
        )
    elif num_nodes > 1000 and verbose:
        logger.info(
            "Computing force-directed layout for %d nodes. This may take 10-60 seconds.",
            num_nodes,
        )

    if forceImport:
        try:
            forceatlas2 = ForceAtlas2(
                # Behavior alternatives
                outboundAttractionDistribution=False,  # Dissuade hubs
                linLogMode=False,  # NOT IMPLEMENTED
                adjustSizes=False,  # Prevent overlap (NOT IMPLEMENTED)
                edgeWeightInfluence=edgeWeightInfluence,
                # Performance
                jitterTolerance=1.0,  # Tolerance
                barnesHutOptimize=True,
                barnesHutTheta=barnesHutTheta,
                multiThreaded=False,  # NOT IMPLEMENTED
                # Tuning
                scalingRatio=scalingRatio,
                strongGravityMode=False,
                gravity=gravity,
                # Log
                verbose=verbose,
            )

            if layout_parameters is not None:
                logger.info("Using custom init positions!")
                pos = forceatlas2.forceatlas2_networkx_layout(g, **layout_parameters)
            else:
                pos = forceatlas2.forceatlas2_networkx_layout(g)

            norm: float = np.max(
                [np.abs(x) for x in itertools.chain(zip(*pos.values()))]
            )
            pos_pairs = [np.array([(a / norm), (b / norm)]) for a, b in pos.values()]
            pos = dict(zip(pos.keys(), pos_pairs))

        except Exception as e:

            logger.error("Error: %s", e)
            if layout_parameters is not None:
                pos = nx.spring_layout(g, seed=seed, **layout_parameters)
            else:
                pos = nx.spring_layout(g, seed=seed)
            logger.warning(
                "Using standard layout algorithm, fa2 not present on the system."
            )

    else:
        if layout_parameters is not None:
            pos = nx.spring_layout(g, seed=seed, **layout_parameters)
        else:
            pos = nx.spring_layout(g, seed=seed)
        logger.warning(
            "Using standard layout algorithm, fa2 not present on the system."
        )

    # return positions
    result: Dict[Any, np.ndarray] = pos
    return result


@require(lambda g: g is not None, "graph must not be None")
@require(lambda g: isinstance(g, nx.Graph), "g must be a NetworkX graph")
@require(lambda g: g.number_of_nodes() > 0, "graph must have at least one node")
@ensure(lambda result: isinstance(result, dict), "result must be a dictionary")
@ensure(
    lambda g, result: len(result) == g.number_of_nodes(),
    "result must have positions for all nodes",
)
def compute_random_layout(
    g: nx.Graph, seed: Optional[int] = None
) -> Dict[Any, np.ndarray]:
    """
    Compute a random layout for the graph.

    Args:
        g: NetworkX graph
        seed: Random seed for reproducibility

    Returns:
        Dictionary mapping nodes to 2D positions

    Contracts:
        - Precondition: graph must not be None and be a NetworkX graph
        - Precondition: graph must have at least one node
        - Postcondition: result is a dictionary
        - Postcondition: result has positions for all nodes
    """
    from py3plex.utils import get_rng

    rng = get_rng(seed)
    result: Dict[Any, np.ndarray] = {n: rng.random(2) for n in g.nodes()}
    return result


if __name__ == "__main__":

    G = nx.gaussian_random_partition_graph(1000, 10, 10, 0.25, 0.1)
    logger.info("Graph info:\n%s", nx_info(G))
    compute_force_directed_layout(G)
    logger.info("Finished..")
