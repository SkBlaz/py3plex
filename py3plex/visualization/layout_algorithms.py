# set of layout wrappers and algorithms used for visualization.

import itertools
from typing import Any, Dict, Optional

import networkx as nx
import numpy as np

from py3plex.core.nx_compat import nx_info

from ..logging_config import get_logger

logger = get_logger(__name__)

try:
    from .fa2.forceatlas2 import ForceAtlas2

    forceImport = True
except ImportError:
    forceImport = False


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
) -> Dict[Any, np.ndarray]:

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

            norm = np.max([np.abs(x) for x in itertools.chain(zip(*pos.values()))])
            pos_pairs = [np.array([(a / norm), (b / norm)]) for a, b in pos.values()]
            pos = dict(zip(pos.keys(), pos_pairs))

        except Exception as e:

            logger.error("Error: %s", e)
            if layout_parameters is not None:
                pos = nx.spring_layout(g, **layout_parameters)
            else:
                pos = nx.spring_layout(g)
            logger.warning("Using standard layout algorithm, fa2 not present on the system.")

    else:
        if layout_parameters is not None:
            pos = nx.spring_layout(g, **layout_parameters)
        else:
            pos = nx.spring_layout(g)
        logger.warning("Using standard layout algorithm, fa2 not present on the system.")

    # return positions

    return pos


def compute_random_layout(g: nx.Graph) -> Dict[Any, np.ndarray]:
    tuple(np.random.rand(1, 2))
    pos = {n: np.array(tuple(np.random.rand(1, 2).tolist()[0])) for n in g.nodes()}
    return pos


if __name__ == "__main__":

    G = nx.gaussian_random_partition_graph(1000, 10, 10, 0.25, 0.1)
    logger.info("Graph info:\n%s", nx_info(G))
    compute_force_directed_layout(G)
    logger.info("Finished..")
