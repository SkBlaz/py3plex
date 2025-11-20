#!/usr/bin/env python3
"""
MultiRank and Multiplex PageRank Variants for Multilayer Networks

This module implements co-ranking algorithms and multiplex PageRank variants
as specified in the literature:

1. MultiRank: Co-ranking nodes and layers iteratively (Halu et al. 2013)
2. Multiplex PageRank variants (Halu et al. 2013):
   - Neutral (baseline, no cross-layer influence)
   - Additive (cross-layer influence via sum)
   - Multiplicative (cross-layer influence via product)
   - Combined (additive + multiplicative)

References:
    Halu, A., Mondragon, R. J., Panzarasa, P., & Bianconi, G. (2013).
    Multiplex PageRank. PloS one, 8(10), e78293.

Authors: py3plex contributors
Date: November 2025
"""

from typing import Dict, List, Optional, Tuple

import numpy as np
import scipy.sparse as sp


def multirank(
    layer_adjacencies: List[np.ndarray],
    alpha: float = 0.85,
    tol: float = 1e-6,
    max_iter: int = 1000,
    interlayer_coupling: Optional[np.ndarray] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    MultiRank: Co-rank nodes and layers iteratively.

    This algorithm simultaneously computes node scores x[i] and layer scores y[ℓ]
    by iteratively updating:
    1. Node scores based on layer-weighted supra-adjacency
    2. Layer scores based on node activity in each layer

    Args:
        layer_adjacencies: List of L adjacency matrices (N x N) for each layer.
        alpha: Damping parameter in (0, 1), typically 0.85.
        tol: Convergence tolerance for score changes.
        max_iter: Maximum number of iterations.
        interlayer_coupling: Optional interlayer coupling matrix (L x L).
                            If None, uses identity (no inter-layer edges).

    Returns:
        Tuple of:
        - node_scores: np.ndarray of shape (N,) with node scores
        - layer_scores: np.ndarray of shape (L,) with layer scores

    Raises:
        ValueError: If inputs are invalid (empty layers, inconsistent sizes, etc.)

    Example:
        >>> import numpy as np
        >>> # Create 2 layers with 3 nodes each
        >>> L1 = np.array([[0, 1, 1], [1, 0, 1], [1, 1, 0]])
        >>> L2 = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]])
        >>> node_scores, layer_scores = multirank([L1, L2])
        >>> node_scores.shape
        (3,)
        >>> layer_scores.shape
        (2,)
    """
    if not layer_adjacencies:
        raise ValueError("At least one layer is required")

    # Validate all layers have the same shape
    N = layer_adjacencies[0].shape[0]
    L = len(layer_adjacencies)

    for i, layer in enumerate(layer_adjacencies):
        if layer.shape[0] != layer.shape[1]:
            raise ValueError(f"Layer {i} is not square: {layer.shape}")
        if layer.shape[0] != N:
            raise ValueError(
                f"Layer {i} has different size {layer.shape[0]} vs {N}"
            )

    if N == 0:
        raise ValueError("Layers must have at least one node")

    # Initialize node and layer scores
    node_scores = np.ones(N) / N
    layer_scores = np.ones(L) / L

    # Convert to numpy arrays if needed
    layer_adjacencies = [np.asarray(layer) for layer in layer_adjacencies]

    # If no interlayer coupling provided, use identity (no inter-layer edges)
    if interlayer_coupling is None:
        interlayer_coupling = np.eye(L)

    for iteration in range(max_iter):
        # === Update node scores ===
        # Build layer-weighted supra-adjacency matrix using sparse operations
        # For each layer ℓ: A_y[ℓ] = y[ℓ] * A[ℓ]
        # Use sparse block matrix construction for memory efficiency: O(E + N*L) vs O(N²*L²)

        # Convert layers to sparse if needed and scale by layer scores
        weighted_layers_sparse = []
        for ell in range(L):
            layer_csr = sp.csr_matrix(layer_adjacencies[ell])
            weighted_layers_sparse.append(layer_scores[ell] * layer_csr)

        # Build block-diagonal supra matrix using sparse blocks
        # Diagonal blocks: intralayer edges weighted by layer scores
        diagonal_blocks = [[None for _ in range(L)] for _ in range(L)]
        for ell in range(L):
            diagonal_blocks[ell][ell] = weighted_layers_sparse[ell]

        # Off-diagonal blocks: interlayer replica couplings (sparse identity matrices)
        for ell1 in range(L):
            for ell2 in range(L):
                if ell1 != ell2:
                    coupling_weight = interlayer_coupling[ell1, ell2]
                    if coupling_weight != 0:
                        # Sparse identity for replica-to-replica coupling
                        diagonal_blocks[ell1][ell2] = sp.identity(N, format='csr') * coupling_weight
                    else:
                        # Zero block if no coupling
                        diagonal_blocks[ell1][ell2] = sp.csr_matrix((N, N))

        # Construct sparse supra-adjacency matrix
        supra_matrix = sp.bmat(diagonal_blocks, format='csr')

        # Create row-stochastic transition matrix (sparse operations)
        row_sums = np.array(supra_matrix.sum(axis=1)).flatten()
        row_sums[row_sums == 0] = 1  # Handle dangling nodes

        # Normalize rows to create transition matrix
        row_sums_inv = sp.diags(1.0 / row_sums, format='csr')
        transition_matrix = row_sums_inv @ supra_matrix

        # PageRank-style update on supra-matrix (sparse matrix-vector products)
        replica_scores = np.ones(N * L) / (N * L)
        for _ in range(100):  # Inner PageRank iterations
            new_replica_scores = (1 - alpha) / (N * L) + alpha * (
                transition_matrix.T @ replica_scores
            )
            if np.linalg.norm(replica_scores - new_replica_scores) < tol:
                break
            replica_scores = new_replica_scores

        # Aggregate replica scores to node scores (sum across layers)
        # Vectorized: reshape and sum instead of nested loops
        replica_scores_reshaped = replica_scores.reshape(L, N)
        new_node_scores = np.sum(replica_scores_reshaped, axis=0)

        # Normalize node scores
        if np.sum(new_node_scores) > 0:
            new_node_scores = new_node_scores / np.sum(new_node_scores)

        # === Update layer scores ===
        # Vectorized computation: for each layer ℓ, compute edge activity
        # edge_activity = sum_{i,j} A[ℓ]_{ij} * (x[i] + x[j])
        new_layer_scores = np.zeros(L)
        for ell in range(L):
            layer_adj = layer_adjacencies[ell]
            # Vectorized: A @ x gives column sums weighted by x
            # A.T @ x gives row sums weighted by x
            # Total activity = sum of both (counts each edge twice for undirected)
            edge_activity = np.sum(layer_adj @ new_node_scores) + np.sum(layer_adj.T @ new_node_scores)
            new_layer_scores[ell] = edge_activity

        # Normalize layer scores
        if np.sum(new_layer_scores) > 0:
            new_layer_scores = new_layer_scores / np.sum(new_layer_scores)
        else:
            # If all layers have zero edges, uniform distribution
            new_layer_scores = np.ones(L) / L

        # Check convergence
        node_change = np.linalg.norm(node_scores - new_node_scores)
        layer_change = np.linalg.norm(layer_scores - new_layer_scores)

        node_scores = new_node_scores
        layer_scores = new_layer_scores

        if node_change + layer_change < tol:
            break

    return node_scores, layer_scores


def multiplex_pagerank(
    layer_adjacencies: List[np.ndarray],
    alpha: float = 0.85,
    variant: str = "neutral",
    c: float = 1.0,
    c1: float = 1.0,
    c2: float = 1.0,
    epsilon: float = 1e-12,
    tol: float = 1e-6,
    max_iter: int = 1000,
) -> Dict[str, np.ndarray]:
    """
    Multiplex PageRank with various cross-layer coupling variants (Halu et al. 2013).

    This function computes PageRank scores for nodes across multiple layers with
    different coupling functions:

    - **Neutral**: No cross-layer influence (baseline)
        F_i^ℓ(...) = 1

    - **Additive**: Cross-layer influence via sum
        F_i^ℓ(r) = 1 + c * sum_{ℓ'≠ℓ} r_i^{ℓ'}

    - **Multiplicative**: Cross-layer influence via product
        F_i^ℓ(r) = Π_{ℓ'≠ℓ} (r_i^{ℓ'} + ε)^{c}

    - **Combined**: Both additive and multiplicative
        F_i^ℓ(r) = (1 + c1 * sum_{ℓ'≠ℓ} r_i^{ℓ'}) * Π_{ℓ'≠ℓ} (r_i^{ℓ'} + ε)^{c2}

    Args:
        layer_adjacencies: List of L adjacency matrices (N x N) for each layer.
        alpha: Damping parameter in (0, 1), typically 0.85.
        variant: Coupling variant: 'neutral', 'additive', 'multiplicative', 'combined'.
        c: Coupling strength for additive/multiplicative variants.
        c1: Additive coupling strength for combined variant.
        c2: Multiplicative coupling strength for combined variant.
        epsilon: Small constant for numerical stability (e.g., 1e-12).
        tol: Convergence tolerance for score changes.
        max_iter: Maximum number of iterations.

    Returns:
        Dictionary with keys:
        - 'node_scores': np.ndarray of shape (N,) with aggregated node scores
        - 'replica_scores': np.ndarray of shape (N, L) with per-layer node scores

    Raises:
        ValueError: If inputs are invalid or variant is unknown.

    Example:
        >>> import numpy as np
        >>> L1 = np.array([[0, 1, 1], [1, 0, 1], [1, 1, 0]])
        >>> L2 = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]])
        >>> result = multiplex_pagerank([L1, L2], variant='additive', c=0.5)
        >>> result['node_scores'].shape
        (3,)
        >>> result['replica_scores'].shape
        (3, 2)
    """
    if not layer_adjacencies:
        raise ValueError("At least one layer is required")

    valid_variants = ["neutral", "additive", "multiplicative", "combined"]
    if variant not in valid_variants:
        raise ValueError(
            f"Invalid variant '{variant}'. Must be one of {valid_variants}"
        )

    # Validate all layers have the same shape
    N = layer_adjacencies[0].shape[0]
    L = len(layer_adjacencies)

    for i, layer in enumerate(layer_adjacencies):
        if layer.shape[0] != layer.shape[1]:
            raise ValueError(f"Layer {i} is not square: {layer.shape}")
        if layer.shape[0] != N:
            raise ValueError(
                f"Layer {i} has different size {layer.shape[0]} vs {N}"
            )

    if N == 0:
        raise ValueError("Layers must have at least one node")

    # Convert to numpy arrays
    layer_adjacencies = [np.asarray(layer) for layer in layer_adjacencies]

    # Create row-stochastic transition matrices for each layer
    transition_matrices = []
    for layer in layer_adjacencies:
        row_sums = np.sum(layer, axis=1)
        row_sums[row_sums == 0] = 1  # Handle dangling nodes
        P = layer / row_sums[:, np.newaxis]
        transition_matrices.append(P)

    # Initialize PageRank scores: r_i^ℓ = 1/N for all i, ℓ
    replica_scores = np.ones((N, L)) / N

    for iteration in range(max_iter):
        new_replica_scores = np.zeros((N, L))

        # Update each layer and node
        for ell in range(L):
            for i in range(N):
                # Compute coupling function F_i^ℓ
                if variant == "neutral":
                    F = 1.0

                elif variant == "additive":
                    # F = 1 + c * sum_{ℓ'≠ℓ} r_i^{ℓ'}
                    cross_layer_sum = 0.0
                    for ell_prime in range(L):
                        if ell_prime != ell:
                            cross_layer_sum += replica_scores[i, ell_prime]
                    F = 1.0 + c * cross_layer_sum

                elif variant == "multiplicative":
                    # F = Π_{ℓ'≠ℓ} (r_i^{ℓ'} + ε)^{c}
                    F = 1.0
                    for ell_prime in range(L):
                        if ell_prime != ell:
                            F *= (replica_scores[i, ell_prime] + epsilon) ** c

                elif variant == "combined":
                    # F = (1 + c1 * sum) * Π (r + ε)^{c2}
                    cross_layer_sum = 0.0
                    cross_layer_prod = 1.0
                    for ell_prime in range(L):
                        if ell_prime != ell:
                            cross_layer_sum += replica_scores[i, ell_prime]
                            cross_layer_prod *= (
                                replica_scores[i, ell_prime] + epsilon
                            ) ** c2
                    F = (1.0 + c1 * cross_layer_sum) * cross_layer_prod

                # PageRank update with coupling function
                # r_i^ℓ_new = (1-α)/N + α * [ Σ_j P^ℓ_{j→i} * r_j^ℓ ] * F
                incoming_pr = 0.0
                for j in range(N):
                    incoming_pr += (
                        transition_matrices[ell][j, i] * replica_scores[j, ell]
                    )

                new_replica_scores[i, ell] = (
                    (1 - alpha) / N + alpha * incoming_pr
                ) * F

        # Normalize scores in each layer
        for ell in range(L):
            layer_sum = np.sum(new_replica_scores[:, ell])
            if layer_sum > 0:
                new_replica_scores[:, ell] /= layer_sum
            else:
                new_replica_scores[:, ell] = np.ones(N) / N

        # Check convergence
        change = np.linalg.norm(replica_scores - new_replica_scores)
        replica_scores = new_replica_scores

        if change < tol:
            break

    # Aggregate to node-level: r_i = sum_ℓ r_i^ℓ
    node_scores = np.sum(replica_scores, axis=1)

    return {"node_scores": node_scores, "replica_scores": replica_scores}
