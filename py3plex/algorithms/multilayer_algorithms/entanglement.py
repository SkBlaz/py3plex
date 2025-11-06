#!/usr/bin/env python3
"""Authors: Benjamin Renoust (github.com/renoust)
Date: 2018/02/13
Description: Loads a Detangler JSON format graph and compute unweighted entanglement analysis with Py3Plex
"""
import itertools
import math
import sys
from typing import Any, Dict, List, Tuple

import numpy as np
from scipy import spatial
from scipy.sparse.csgraph import connected_components, csgraph_from_dense

from ...logging_config import get_logger

logger = get_logger(__name__)
logger.info("Python version: %s", sys.version)


# Build the R and C matrix
def build_occurrence_matrix(network: Any) -> Tuple[np.ndarray, List[Any]]:
    """
    Build occurrence matrix from multilayer network.

    Args:
        network: Multilayer network object

    Returns:
        Tuple of (c_matrix, layers) where c_matrix is the normalized occurrence matrix
        and layers is the list of layer names
    """

    multiedges = network.get_edges()
    layers = []
    edge_list = []
    for e in multiedges:
        (n1, l1), (n2, l2) = e
        if l1 == l2:
            if l1 not in layers:
                layers += [l1]
            edge_list.append([n1, n2, l1])

    edge_list = sorted(edge_list, key=lambda x: [x[0], x[1]])

    nb_layers = len(layers)
    r_matrix = np.zeros((nb_layers, nb_layers)).astype(float)

    def count_overlap(overlap: List[List[Any]]) -> None:
        """Count overlaps between layers."""
        prev_layers: List[int] = []
        for e in overlap:
            layer = e[2]
            layer_index = layers.index(layer)
            r_matrix[layer_index, layer_index] += 1.0
            for l in prev_layers:
                r_matrix[l, layer_index] += 1.0
                r_matrix[layer_index, l] += 1.0

            prev_layers.append(layer_index)

    current_edge = None
    flat_pairs = 0.0
    overlap: List[List[Any]] = []

    for e in edge_list:
        node_pair = [e[0], e[1]]
        if current_edge != node_pair:
            flat_pairs += 1.0
            current_edge = node_pair
            count_overlap(overlap)
            overlap = []
        overlap.append(e)
    count_overlap(overlap)
    flat_pairs += 1

    c_matrix = r_matrix.copy()

    for i in range(nb_layers):
        c_matrix[i, i] /= flat_pairs

    for i, j in itertools.combinations(range(nb_layers), 2):
        c_matrix[i, j] /= r_matrix[j][j]
        c_matrix[j, i] /= r_matrix[i][i]

    return c_matrix, layers


# proceeds with block decomposition
def compute_blocks(c_matrix: np.ndarray) -> Tuple[List[List[int]], List[np.ndarray]]:
    """
    Compute block decomposition of occurrence matrix.

    Args:
        c_matrix: Occurrence matrix

    Returns:
        Tuple of (indices, blocks) where indices are the layer indices in each block
        and blocks are the submatrices for each block
    """
    c_sparse = csgraph_from_dense(c_matrix)
    nb_components, labels = connected_components(
        c_sparse, directed=False, return_labels=True
    )

    v2i: Dict[Any, List[int]] = {}
    for i, v in enumerate(labels):
        v2i[v] = v2i.get(v, []) + [i]

    blocks: List[np.ndarray] = []
    indices: List[List[int]] = []
    for v, idx_list in v2i.items():
        indices.append(idx_list)
        blocks.append(c_matrix[np.ix_(idx_list, idx_list)])

    return indices, blocks


# computes entanglement for one block
def compute_entanglement(block_matrix: np.ndarray) -> Tuple[List[float], List[float]]:
    """
    Compute entanglement metrics for a block.

    Args:
        block_matrix: Block submatrix

    Returns:
        Tuple of ([intensity, homogeneity, normalized_homogeneity], gamma_layers)
    """
    eigenvals, eigenvects = np.linalg.eig(block_matrix)
    max_eigenval = max(eigenvals.real)
    index_first_eigenvect = np.argmax(eigenvals)

    nb_layers = len(block_matrix)
    # normalizes the max eigenval to dimensions
    entanglement_intensity = max_eigenval / nb_layers

    gamma_layers = []
    for i in range(nb_layers):
        gamma_layers.append(
            abs(eigenvects[i][index_first_eigenvect].real)
        )  # because of approx.

    # computes entanglement homogeneity, cosine distance with the [1...1] vector
    entanglement_homogeneity = 1 - spatial.distance.cosine(
        gamma_layers, np.ones(nb_layers)
    )
    # normalizes within the top right quadrant (sorts of flatten the [0-1] value distribution)
    normalized_entanglement_homogeneity = 1 - math.acos(entanglement_homogeneity) / (
        math.pi / 2
    )

    return [
        entanglement_intensity,
        entanglement_homogeneity,
        normalized_entanglement_homogeneity,
    ], gamma_layers


def compute_entanglement_analysis(network: Any) -> List[Dict[str, Any]]:
    """
    Compute full entanglement analysis for a multilayer network.

    Args:
        network: Multilayer network object

    Returns:
        List of block analysis dictionaries with entanglement metrics
    """

    matrix, layers = build_occurrence_matrix(network)
    indices, blocks = compute_blocks(matrix)

    analysis = []
    for i, b in enumerate(blocks):
        layer_labels = [layers[x] for x in indices[i]]
        [I, H, H_norm], gamma = compute_entanglement(b)
        block_analysis = {
            "Entanglement intensity": I,
            "Layer entanglement": {
                layer_labels[x]: gamma[x] for x in range(len(gamma))
            },
            "Entanglement homogeneity": H,
            "Normalized homogeneity": H_norm,
        }
        analysis.append(block_analysis)
    return analysis


if __name__ == "__main__":
    # Example usage - requires a network object to be defined
    #
    # logger.info("%d connected components of layers", len(analysis))
    # for i, b in enumerate(analysis):
    #     logger.info("--- block %d", i)
    #     logger.info("Covering layers: %s", layer_labels)
    #
    #     logger.info("Entanglement intensity: %f", b["Entanglement intensity"])
    #     logger.info("Layer entanglement: %s", b["Layer entanglement"])
    #     logger.info("Entanglement homogeneity: %f", b["Entanglement homogeneity"])
    #     logger.info("Normalized homogeneity: %f", b["Normalized homogeneity"])
    pass
