#!/usr/bin/env python3
"""
Supra Matrix Function Centralities for Multilayer Networks.

This module implements centrality measures based on matrix functions of the
supra-adjacency matrix, including:
- Communicability Centrality (Estrada & Hatano, 2008)
- Katz Centrality (Katz, 1953)

These measures operate directly on the sparse supra-adjacency matrix obtained
from multi_layer_network.get_supra_adjacency_matrix().

References:
    - Estrada, E., & Hatano, N. (2008). Communicability in complex networks.
      Physical Review E, 77(3), 036111.
    - Katz, L. (1953). A new status index derived from sociometric analysis.
      Psychometrika, 18(1), 39-43.

Authors: py3plex contributors
Date: October 2025 (Phase II)
"""

from typing import cast

import numpy as np
import scipy.sparse as sp
from scipy.sparse import identity
from scipy.sparse.linalg import eigs, expm_multiply, spsolve

from py3plex.exceptions import Py3plexMatrixError


def _validate_supra_matrix(supra_matrix: sp.spmatrix) -> None:
    """
    Validate that the supra-adjacency matrix is suitable for centrality computation.

    Args:
        supra_matrix: Supra-adjacency matrix to validate.

    Raises:
        Py3plexMatrixError: If matrix is empty, non-square, or invalid.
    """
    if supra_matrix is None:
        raise Py3plexMatrixError("Supra-adjacency matrix is None")

    if not hasattr(supra_matrix, "shape"):
        raise Py3plexMatrixError("Invalid matrix type: missing shape attribute")

    if len(supra_matrix.shape) != 2:
        raise Py3plexMatrixError(
            f"Matrix must be 2-dimensional, got shape {supra_matrix.shape}"
        )

    n_rows, n_cols = supra_matrix.shape
    if n_rows != n_cols:
        raise Py3plexMatrixError(
            f"Matrix must be square, got shape ({n_rows}, {n_cols})"
        )

    if n_rows == 0:
        raise Py3plexMatrixError("Matrix is empty (size 0)")


def communicability_centrality(
    supra_matrix: sp.spmatrix,
    normalize: bool = True,
    use_sparse: bool = True,
    max_iter: int = 100,
    tol: float = 1e-6,
) -> np.ndarray:
    """
    Compute communicability centrality for each node-layer pair.

    Communicability centrality measures the weighted sum of all walks between
    nodes, with exponentially decaying weights for longer walks. It is computed
    as the row sum of the matrix exponential:

        c_i = sum_j (exp(A))_ij

    This implementation uses scipy.sparse.linalg.expm_multiply for efficient
    sparse matrix exponential computation.

    Args:
        supra_matrix: Sparse supra-adjacency matrix (n x n).
        normalize: If True, normalize output to sum to 1.
        use_sparse: If True, use sparse matrix operations. Falls back to dense
            for matrices smaller than 10000 elements.
        max_iter: Maximum number of iterations for sparse approximation (currently unused).
        tol: Tolerance for convergence (currently unused).

    Returns:
        np.ndarray: Communicability centrality scores for each node-layer pair (n,).

    Raises:
        Py3plexMatrixError: If matrix is invalid (non-square, empty, etc.).

    Example:
        >>> from py3plex.core import random_generators
        >>> net = random_generators.random_multiplex_ER(50, 3, 0.1)
        >>> A = net.get_supra_adjacency_matrix()
        >>> comm = communicability_centrality(A)
        >>> print(f"Communicability centrality computed for {len(comm)} node-layer pairs")
    """
    _validate_supra_matrix(supra_matrix)

    n = supra_matrix.shape[0]

    # Convert to appropriate format
    if not sp.issparse(supra_matrix):
        supra_matrix = sp.csr_matrix(supra_matrix)
    elif not isinstance(supra_matrix, sp.csr_matrix):
        supra_matrix = supra_matrix.tocsr()

    # Decide whether to use sparse or dense computation
    matrix_size = n * n
    if use_sparse and matrix_size >= 1e4:
        # Use sparse matrix exponential via expm_multiply
        # Compute exp(A) * 1 to get row sums efficiently
        try:
            ones_vector = np.ones(n)
            exp_A_times_ones = expm_multiply(supra_matrix, ones_vector)
            centralities = exp_A_times_ones
        except (ValueError, RuntimeError, MemoryError) as e:
            raise Py3plexMatrixError(
                f"Failed to compute sparse matrix exponential: {e}"
            ) from e
    else:
        # Fall back to dense computation for small matrices
        try:
            from scipy.linalg import expm

            dense_matrix = supra_matrix.toarray()
            exp_matrix = expm(dense_matrix)
            centralities = np.sum(exp_matrix, axis=1)
        except (ImportError, np.linalg.LinAlgError, MemoryError) as e:
            raise Py3plexMatrixError(
                f"Failed to compute dense matrix exponential: {e}"
            ) from e

    # Ensure centralities are real and positive
    centralities = np.real(centralities)
    centralities = np.maximum(centralities, 0)

    # Normalize if requested
    if normalize:
        total: float = np.sum(centralities)
        if total > 0:
            centralities = centralities / total
        else:
            # If all centralities are zero, set uniform distribution
            centralities = np.ones(n) / n

    return cast(np.ndarray, centralities)


def katz_centrality(
    supra_matrix: sp.spmatrix,
    alpha: float = None,
    beta: float = 1.0,
    tol: float = 1e-6,
) -> np.ndarray:
    """
    Compute Katz centrality for each node-layer pair.

    Katz centrality measures node influence by accounting for all paths with
    exponentially decaying weights. It is computed as:

        x = (I - alpha * A)^{-1} * beta * 1

    where alpha < 1/lambda_max(A) to ensure convergence. If alpha is not
    provided, it defaults to 0.85 / lambda_max(A).

    Args:
        supra_matrix: Sparse supra-adjacency matrix (n x n).
        alpha: Attenuation parameter. Must be less than 1/spectral_radius(A).
            If None, defaults to 0.85 / lambda_max(A).
        beta: Weight of exogenous influence (typically 1.0).
        tol: Tolerance for eigenvalue computation.

    Returns:
        np.ndarray: Katz centrality scores for each node-layer pair (n,).
            Normalized to sum to 1.

    Raises:
        Py3plexMatrixError: If matrix is invalid or alpha is out of valid range.

    Example:
        >>> from py3plex.core import random_generators
        >>> net = random_generators.random_multiplex_ER(50, 3, 0.1)
        >>> A = net.get_supra_adjacency_matrix()
        >>> katz = katz_centrality(A)
        >>> print(f"Katz centrality computed for {len(katz)} node-layer pairs")
        >>> # With custom alpha
        >>> katz_custom = katz_centrality(A, alpha=0.05)
    """
    _validate_supra_matrix(supra_matrix)

    n = supra_matrix.shape[0]

    # Convert to appropriate format
    if not sp.issparse(supra_matrix):
        supra_matrix = sp.csr_matrix(supra_matrix)
    elif not isinstance(supra_matrix, sp.csr_matrix):
        supra_matrix = supra_matrix.tocsr()

    # Compute alpha if not provided (0.85 / lambda_max)
    if alpha is None:
        try:
            # For very small matrices (n <= 2), use dense eigenvalue computation
            if n <= 2:
                dense_matrix = supra_matrix.toarray()
                eigenvals = np.linalg.eigvals(dense_matrix)
                lambda_max: float = float(np.max(np.abs(eigenvals)))
            else:
                # Compute largest eigenvalue using sparse methods
                eigenvals, _ = eigs(supra_matrix, k=1, which="LM", tol=tol)
                lambda_max = float(np.abs(eigenvals[0]))

            if lambda_max < 1e-10:
                # Matrix is essentially zero, return uniform distribution
                centralities = np.ones(n) / n
                return cast(np.ndarray, centralities)

            alpha = 0.85 / lambda_max
        except (ArithmeticError, ValueError, RuntimeError, TypeError):
            # Fallback: use small default alpha if eigenvalue computation fails
            alpha = 0.01
    else:
        # Validate provided alpha
        try:
            # For very small matrices (n <= 2), use dense eigenvalue computation
            if n <= 2:
                dense_matrix = supra_matrix.toarray()
                eigenvals = np.linalg.eigvals(dense_matrix)
                lambda_max = np.max(np.abs(eigenvals))
            else:
                eigenvals, _ = eigs(supra_matrix, k=1, which="LM", tol=tol)
                lambda_max = np.abs(eigenvals[0])

            if alpha >= 1.0 / lambda_max:
                raise Py3plexMatrixError(
                    f"Alpha ({alpha}) must be less than 1/lambda_max ({1.0/lambda_max:.6f})"
                )
        except (ArithmeticError, ValueError, RuntimeError, TypeError):
            # If eigenvalue computation fails, just warn but proceed
            pass

    # Compute (I - alpha * A)^{-1} * beta * 1
    identity_matrix = identity(n, format="csr")
    b = beta * np.ones(n)

    try:
        centralities = spsolve(identity_matrix - alpha * supra_matrix, b)
    except (np.linalg.LinAlgError, RuntimeError, ValueError):
        # Fallback: use series approximation if sparse solve fails
        centralities = b.copy()
        current_term = b.copy()
        for _ in range(100):  # Limit iterations
            current_term = alpha * supra_matrix.dot(current_term)
            centralities += current_term
            if np.linalg.norm(current_term) < tol:
                break

    # Ensure centralities are real and positive
    centralities = np.real(centralities)
    centralities = np.maximum(centralities, 0)

    # Normalize to sum to 1
    total: float = np.sum(centralities)
    if total > 0:
        centralities = centralities / total
    else:
        # If all centralities are zero, set uniform distribution
        centralities = np.ones(n) / n

    return cast(np.ndarray, centralities)


__all__ = [
    "communicability_centrality",
    "katz_centrality",
]
