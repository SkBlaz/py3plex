#!/usr/bin/env python3
"""
Versatility: Multilayer Eigenvector Centrality

This module implements versatility, a multilayer centrality that ranks nodes by
aggregating their eigenvector-based importance across layers of an interconnected
(multiplex) network.

The implementation follows the canonical tensor/supra-matrix formulation for
multilayer eigenvector centrality as defined in:

- De Domenico et al. (2013) "Mathematical Formulation of Multilayer Networks"
  Physical Review X 3, 041022. DOI: 10.1103/PhysRevX.3.041022

- De Domenico et al. (2015) "Ranking in interconnected multilayer networks reveals
  versatile nodes" Nature Communications 6, 6868. DOI: 10.1038/ncomms7868

The key distinction from heuristic approaches is that versatility computes the
eigenvector on the supra-adjacency (not on an aggregated single-layer graph),
then sums per node across layers to obtain the versatility vector.

Authors: py3plex contributors
Date: 2025
"""

from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigs


def build_supra_adjacency(
    layers: List[sp.csr_matrix],
    interlayer: Union[float, Dict, np.ndarray],
) -> sp.csr_matrix:
    """
    Build the supra-adjacency matrix for a multilayer network.

    The supra-adjacency matrix S is an (N·L)×(N·L) block matrix where:
    - Diagonal blocks contain the intra-layer adjacency matrices
    - Off-diagonal blocks contain the interlayer coupling matrices

    Args:
        layers: List of N×N SciPy sparse adjacency matrices (one per layer).
                Can be directed or undirected, weighted ≥0.
        interlayer: Interlayer coupling specification:
                   - scalar omega: Couples node i across any distinct layer pair
                     (α≠β) with weight omega via identity couplings
                   - dict: Full specification of N×N interlayer blocks C[α,β]
                   - array: Full interlayer coupling matrix

    Returns:
        (N·L)×(N·L) sparse CSR matrix representing the supra-adjacency.

    Raises:
        ValueError: If layer dimensions don't match or interlayer spec is invalid.

    Examples:
        >>> import scipy.sparse as sp
        >>> # Create 2 layers with 3 nodes each
        >>> L1 = sp.csr_matrix([[0, 1, 1], [1, 0, 1], [1, 1, 0]])
        >>> L2 = sp.csr_matrix([[0, 1, 0], [1, 0, 1], [0, 1, 0]])
        >>> S = build_supra_adjacency([L1, L2], interlayer=0.1)
        >>> S.shape
        (6, 6)
    """
    if not layers:
        raise ValueError("At least one layer is required")

    # Validate all layers have the same shape
    N = layers[0].shape[0]
    L = len(layers)

    for i, layer in enumerate(layers):
        if layer.shape[0] != layer.shape[1]:
            raise ValueError(f"Layer {i} is not square: {layer.shape}")
        if layer.shape[0] != N:
            raise ValueError(f"Layer {i} has different size {layer.shape[0]} vs {N}")

    # Convert all layers to CSR format for efficiency
    layers = [sp.csr_matrix(layer) for layer in layers]

    # Build the block matrix
    blocks = [[None for _ in range(L)] for _ in range(L)]

    # Fill diagonal blocks with intra-layer adjacencies
    for i in range(L):
        blocks[i][i] = layers[i]

    # Fill off-diagonal blocks with interlayer couplings
    if isinstance(interlayer, (int, float)):
        # Scalar omega: identity coupling with weight omega
        omega = float(interlayer)
        identity_coupling = sp.identity(N, format='csr') * omega

        for i in range(L):
            for j in range(L):
                if i != j:
                    blocks[i][j] = identity_coupling

    elif isinstance(interlayer, dict):
        # Dictionary specification: C[(alpha, beta)] = N×N matrix
        for (alpha, beta), coupling in interlayer.items():
            if alpha >= L or beta >= L or alpha < 0 or beta < 0:
                raise ValueError(f"Invalid layer indices ({alpha}, {beta}) for {L} layers")
            if alpha == beta:
                raise ValueError(f"Diagonal block ({alpha}, {beta}) should not be in interlayer dict")
            blocks[alpha][beta] = sp.csr_matrix(coupling)

        # Fill remaining off-diagonal blocks with zeros
        for i in range(L):
            for j in range(L):
                if i != j and blocks[i][j] is None:
                    blocks[i][j] = sp.csr_matrix((N, N))

    elif isinstance(interlayer, np.ndarray):
        # Array specification: interpret as full interlayer structure
        if interlayer.shape != (N * L, N * L):
            raise ValueError(f"Interlayer array shape {interlayer.shape} doesn't match expected {(N*L, N*L)}")
        # Extract blocks from the array
        for i in range(L):
            for j in range(L):
                if i != j:
                    block = interlayer[i*N:(i+1)*N, j*N:(j+1)*N]
                    blocks[i][j] = sp.csr_matrix(block)
    else:
        raise ValueError(f"Invalid interlayer type: {type(interlayer)}")

    # Construct the supra-adjacency matrix using bmat
    supra_matrix = sp.bmat(blocks, format='csr')

    return supra_matrix


def _power_iteration(
    S: sp.csr_matrix,
    tol: float = 1e-9,
    max_iter: int = 1000,
    seed: int = 0,
) -> np.ndarray:
    """
    Compute the dominant eigenvector using power iteration.

    This method iteratively applies the matrix S to a random vector and
    normalizes until convergence. Works well for non-negative, irreducible
    matrices (Perron-Frobenius theorem).

    Args:
        S: Sparse supra-adjacency matrix
        tol: Convergence tolerance (L1 norm of difference)
        max_iter: Maximum number of iterations
        seed: Random seed for reproducibility

    Returns:
        Dominant eigenvector (non-negative, normalized)

    Raises:
        ValueError: If zero vector encountered (disconnected graph)
        RuntimeWarning: If not converged within max_iter
    """
    rng = np.random.default_rng(seed)
    x = rng.random(S.shape[0])
    x = x / x.sum()

    prev = x.copy()

    for iteration in range(max_iter):
        # Apply matrix
        y = S @ x

        # Check for zero vector (absorbing state or disconnected)
        s = y.sum()
        if s == 0 or np.isnan(s):
            raise ValueError(
                "Zero or NaN vector encountered during power iteration. "
                "The supra-adjacency may be disconnected or have absorbing states. "
                "Consider using versatility_katz instead."
            )

        # Normalize
        x = y / s

        # Check convergence
        diff = np.linalg.norm(x - prev, 1)
        if diff < tol:
            break

        prev = x.copy()
    else:
        # Did not converge
        import warnings
        warnings.warn(
            f"Power iteration did not converge within {max_iter} iterations "
            f"(final diff={diff:.2e}). Results may be inaccurate.",
            RuntimeWarning,
            stacklevel=2
        )

    return x


def versatility(
    A_layers: List[sp.csr_matrix],
    interlayer: Union[float, Dict, np.ndarray],
    *,
    normalize: Optional[str] = "l1",
    return_layer_scores: bool = False,
    tol: float = 1e-9,
    max_iter: int = 1000,
    seed: int = 0,
    use_scipy_eigs: bool = False,
) -> Union[np.ndarray, Tuple[np.ndarray, np.ndarray]]:
    """
    Compute versatility (multilayer eigenvector centrality) for nodes.

    Versatility ranks nodes by aggregating their eigenvector-based importance
    across layers. It computes the dominant eigenvector of the supra-adjacency
    matrix and contracts over layers to produce per-node scores.

    This is the key distinction from heuristic approaches: the eigenvector is
    computed on the interconnected multilayer structure (supra-adjacency), not
    on individual layers or an aggregated single-layer graph.

    Args:
        A_layers: List of N×N sparse adjacency matrices, one per layer.
                 Can be directed or undirected, weighted ≥0.
        interlayer: Interlayer coupling. Either:
                   - scalar omega for identity coupling with weight omega
                   - dict mapping (layer_i, layer_j) to N×N coupling matrices
                   - array specifying full interlayer structure
        normalize: Normalization method for versatility scores:
                  - "l1": Normalize to sum to 1 (default)
                  - "l2": Normalize to unit L2 norm
                  - None: No normalization
        return_layer_scores: If True, also return per-layer scores X[i, α]
        tol: Convergence tolerance for power iteration
        max_iter: Maximum iterations for power iteration
        seed: Random seed for reproducibility
        use_scipy_eigs: If True, use scipy.sparse.linalg.eigs instead of
                       power iteration (slower but more robust for difficult cases)

    Returns:
        If return_layer_scores=False:
            v: Array of shape (N,) with versatility scores per node
        If return_layer_scores=True:
            (v, X): Tuple where:
                - v: Array of shape (N,) with versatility scores
                - X: Array of shape (N, L) with per-layer scores

    Raises:
        ValueError: If layers have mismatched dimensions or convergence fails

    Examples:
        >>> import scipy.sparse as sp
        >>> # Create 2 layers
        >>> L1 = sp.csr_matrix([[0, 1, 1], [1, 0, 1], [1, 1, 0]])
        >>> L2 = sp.csr_matrix([[0, 1, 0], [1, 0, 1], [0, 1, 0]])
        >>> v = versatility([L1, L2], interlayer=0.1)
        >>> v.shape
        (3,)
        >>> # Node rankings reflect both intra-layer and inter-layer importance

    Notes:
        - For irreducible, non-negative S, Perron-Frobenius guarantees a unique
          dominant eigenvector with positive entries
        - If S is reducible (disconnected components), the dominant eigenvector
          may concentrate on one component; use versatility_katz as alternative
        - Handles nodes absent from some layers via zero rows/columns in those layers

    References:
        - De Domenico et al. (2013) Physical Review X 3, 041022
        - De Domenico et al. (2015) Nature Communications 6, 6868
    """
    # Validate inputs (raise proper exceptions for user-facing errors)
    if not A_layers:
        raise ValueError("At least one layer is required")

    # crosshair: analysis_kind=asserts
    # Preconditions for static analysis tools like CrossHair
    # Note: These assertions are redundant at runtime after the above check,
    # but are kept for formal verification tools that analyze assertions
    assert isinstance(interlayer, (int, float, dict, np.ndarray)), \
        "interlayer must be scalar, dict, or array"
    if isinstance(interlayer, (int, float)):
        assert interlayer >= 0.0, "interlayer coupling must be non-negative"

    N = A_layers[0].shape[0]
    L = len(A_layers)

    # Precondition: all layers must be square and same size
    for i, layer in enumerate(A_layers):
        assert layer.shape[0] == layer.shape[1], f"Layer {i} must be square"
        assert layer.shape[0] == N, f"Layer {i} must have size {N}"

    # Build supra-adjacency matrix
    S = build_supra_adjacency(A_layers, interlayer)

    # Compute dominant eigenvector
    if use_scipy_eigs:
        # Use scipy's eigenvalue solver (more robust, slower)
        try:
            eigenvalues, eigenvectors = eigs(S, k=1, which='LM', maxiter=max_iter, tol=tol)
            x = np.abs(eigenvectors[:, 0].real)  # Take absolute value to ensure non-negative
            x = x / x.sum()  # Normalize
        except Exception as e:
            raise ValueError(f"scipy.sparse.linalg.eigs failed: {e}")
    else:
        # Use power iteration (faster, works well for most cases)
        x = _power_iteration(S, tol=tol, max_iter=max_iter, seed=seed)

    # Validate eigenvector dimension matches expected size
    if len(x) != N * L:
        raise ValueError(
            f"Eigenvector length {len(x)} does not match expected size N*L = {N*L}. "
            "This indicates an internal error in eigenvector computation."
        )

    # Reshape to (N, L) with Fortran order
    # Fortran order ensures node indices within each layer are contiguous in memory,
    # matching how the supra-adjacency was constructed with bmat() where the first
    # N entries correspond to layer 0, next N to layer 1, etc.
    X = x.reshape((N, L), order='F')

    # Contract over layers: sum across layer dimension
    v = X.sum(axis=1)

    # Normalize versatility scores
    if normalize == "l1":
        v = v / v.sum()
    elif normalize == "l2":
        v = v / np.linalg.norm(v)
    elif normalize is not None:
        raise ValueError(f"Invalid normalize option: {normalize}. Use 'l1', 'l2', or None")

    # Postconditions
    assert isinstance(v, np.ndarray), "Result must be numpy array"
    assert v.shape == (N,), f"Result shape must be ({N},), got {v.shape}"
    assert np.all(np.isfinite(v)), "All values must be finite"

    if normalize == "l1":
        assert np.isclose(np.sum(np.abs(v)), 1.0, atol=1e-6), "L1 norm should be 1"
    elif normalize == "l2":
        assert np.isclose(np.linalg.norm(v), 1.0, atol=1e-6), "L2 norm should be 1"

    if return_layer_scores:
        return v, X
    else:
        return v


def versatility_katz(
    A_layers: List[sp.csr_matrix],
    interlayer: Union[float, Dict, np.ndarray],
    *,
    alpha: Optional[float] = None,
    normalize: Optional[str] = "l1",
    return_layer_scores: bool = False,
    max_iter: int = 1000,
) -> Union[np.ndarray, Tuple[np.ndarray, np.ndarray]]:
    """
    Compute versatility using Katz-like damping for reducible graphs.

    This is a damping-based alternative for cases where the supra-adjacency
    is not strongly connected (has multiple components, sinks, or sources).
    It solves (I - αS)^{-1} 1 where α < 1/ρ(S) and ρ(S) is the spectral radius.

    Args:
        A_layers: List of N×N sparse adjacency matrices
        interlayer: Interlayer coupling specification
        alpha: Damping factor. If None, auto-computed as 0.85/ρ(S)
        normalize: Normalization method ("l1", "l2", or None)
        return_layer_scores: If True, return per-layer scores
        max_iter: Maximum iterations for spectral radius estimation

    Returns:
        Versatility scores (and optionally layer scores)

    Examples:
        >>> import scipy.sparse as sp
        >>> # Graph with disconnected component
        >>> L1 = sp.csr_matrix([[0, 1, 0], [1, 0, 0], [0, 0, 0]])
        >>> L2 = sp.csr_matrix([[0, 1, 0], [1, 0, 0], [0, 0, 1]])
        >>> v = versatility_katz([L1, L2], interlayer=0.1)

    Notes:
        - More robust for reducible graphs than standard eigenvector centrality
        - Damping ensures convergence even with absorbing states or sinks
        - Higher alpha gives more weight to longer paths

    References:
        - Katz (1953) "A new status index derived from sociometric analysis"
        - De Domenico et al. (2013) for multilayer extension
    """
    if not A_layers:
        raise ValueError("At least one layer is required")

    N = A_layers[0].shape[0]
    L = len(A_layers)

    # Build supra-adjacency
    S = build_supra_adjacency(A_layers, interlayer)

    # Estimate spectral radius if alpha not provided
    if alpha is None:
        # Use power iteration to estimate largest eigenvalue
        try:
            eigenvalues, _ = eigs(S, k=1, which='LM', maxiter=max_iter)
            rho = np.abs(eigenvalues[0])
            alpha = 0.85 / rho  # Conservative damping
        except (ArithmeticError, RuntimeError, ValueError):
            # Fallback: use a small fixed alpha
            alpha = 0.01

    # Solve (I - αS)^{-1} 1
    I = sp.identity(S.shape[0], format='csr')
    b = np.ones(S.shape[0])

    try:
        from scipy.sparse.linalg import spsolve
        x = spsolve(I - alpha * S, b)
        x = np.abs(x)  # Ensure non-negative
    except (ArithmeticError, RuntimeError, ValueError) as e:
        raise ValueError(f"Failed to solve Katz system. Try reducing alpha. Error: {e}") from e

    # Reshape and contract
    X = x.reshape((N, L), order='F')
    v = X.sum(axis=1)

    # Normalize
    if normalize == "l1":
        v = v / v.sum()
    elif normalize == "l2":
        v = v / np.linalg.norm(v)
    elif normalize is not None:
        raise ValueError(f"Invalid normalize option: {normalize}")

    if return_layer_scores:
        return v, X
    else:
        return v
