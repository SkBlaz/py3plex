"""Multilayer Spectral Clustering Algorithms.

This module implements two variants of spectral clustering for multilayer networks:

1. **Supra-Laplacian Spectral Clustering**: Constructs the full supra-Laplacian
   matrix with interlayer coupling, then performs spectral embedding on the
   node-layer replicas and averages to get node-level communities.

2. **Multiplex (Aggregated) Laplacian Spectral Clustering**: Aggregates the
   normalized Laplacians of individual layers, then performs spectral
   clustering directly on nodes without constructing a supra-graph.

Mathematical Definitions
------------------------

Shared notation:
- Nodes: n nodes
- Layers: L layers
- Intralayer adjacency matrices: A^[α] for layer α
- Degree matrices: D^[α] where D^[α]_ii = Σ_j A^[α]_ij
- Intralayer Laplacians:
  - Unnormalized: L^[α] = D^[α] - A^[α]
  - Normalized (default): L^[α]_norm = I - (D^[α])^{-1/2} A^[α] (D^[α])^{-1/2}

Variant A: Supra-Laplacian Spectral Clustering
-----------------------------------------------
1. **Supra-adjacency matrix**:
   A^{supra} is an (nL × nL) block matrix where:
   - Diagonal blocks contain the layer adjacency matrices A^[α]
   - Off-diagonal blocks contain ωI (interlayer coupling)

2. **Supra-Laplacian**:
   - Compute degree matrix D^{supra} where D^{supra}_{ii} = Σ_j A^{supra}_{ij}
   - Normalized supra-Laplacian: L^{supra}_norm = I - (D^{supra})^{-1/2} A^{supra} (D^{supra})^{-1/2}

3. **Spectral embedding**:
   - Compute k smallest non-trivial eigenvectors of L^{supra}_norm
   - Embedding matrix X ∈ R^{(nL) × k}

4. **Node-level embedding**:
   - Average replicas across layers: X̄_i = (1/L) Σ_{α=1}^L X_{(i,α)}

5. **Clustering**:
   - Run k-means on rows of X̄ to get node partition c_i

Outputs:
- partition_nodes: Dict mapping (node, layer) -> community_id
- embedding_nodes: ndarray (n × k) - node-level embeddings
- embedding_supra: ndarray (nL × k) - full supra-embeddings (in metadata)

Variant B: Multiplex Laplacian Spectral Clustering
---------------------------------------------------
This variant never constructs a supra-graph.

1. **Aggregate Laplacian**:
   - Compute layer Laplacians L^[α]_norm
   - Aggregate: L^{multi} = Σ_{α=1}^L w_α L^[α]_norm
   - Default: w_α = 1/L (uniform weights)

2. **Spectral embedding**:
   - Solve: L^{multi} X = Λ X, where X ∈ R^{n × k}
   - Take k smallest non-zero eigenvectors

3. **Clustering**:
   - Apply k-means on rows of X to get c_i = kmeans(X_i)

Outputs:
- partition_nodes: Dict mapping (node, layer) -> community_id
- embedding_nodes: ndarray (n × k)

Parameter Contract
------------------
Shared parameters:
- k: int (mandatory) - number of communities
- laplacian: Literal["normalized"] (only normalized supported)
- random_state: Optional[int] - for k-means reproducibility
- eigen_solver: Literal["dense","lobpcg"] (default: auto by size)

Variant-specific:
- Supra variant: omega (float >= 0) - interlayer coupling strength
- Multiplex variant: no coupling parameter

Complexity Guarantees
---------------------
Variant A (Supra):
- Memory: O((nL)^2) worst-case (dense matrices)
- Time: O((nL)^3) for dense eigen decomposition

Variant B (Multiplex):
- Memory: O(n^2)
- Time: O(n^3) for eigen decomposition

References
----------
- Kivelä, M., et al. (2014). Multilayer networks. Journal of Complex Networks.
- Ng, A. Y., Jordan, M. I., & Weiss, Y. (2002). On spectral clustering.
  Advances in Neural Information Processing Systems.

Examples
--------
>>> from py3plex.core import multinet
>>> from py3plex.algorithms.community_detection.spectral_multilayer import (
...     spectral_multilayer_supra, spectral_multilayer_multiplex
... )
>>>
>>> # Create network
>>> net = multinet.multi_layer_network(directed=False)
>>> # ... add edges ...
>>>
>>> # Supra-Laplacian variant
>>> partition, metadata = spectral_multilayer_supra(
...     net, k=3, omega=0.8, random_state=42
... )
>>>
>>> # Multiplex variant
>>> partition, metadata = spectral_multilayer_multiplex(
...     net, k=3, random_state=42
... )
"""

from typing import Any, Dict, Literal, Optional, Tuple

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh
from sklearn.cluster import KMeans

from py3plex.exceptions import Py3plexException, AlgorithmError


def _validate_parameters(
    k: int,
    laplacian: str,
    random_state: Optional[int],
    eigen_solver: Optional[str],
) -> None:
    """Validate common parameters for spectral clustering.

    Args:
        k: Number of communities
        laplacian: Laplacian type
        random_state: Random seed
        eigen_solver: Eigen solver type

    Raises:
        AlgorithmError: If parameters are invalid
    """
    if not isinstance(k, int) or k < 1:
        raise AlgorithmError(
            f"k must be a positive integer, got {k}",
            suggestions=["Provide k >= 1"]
        )

    if laplacian != "normalized":
        raise AlgorithmError(
            f"Only 'normalized' Laplacian is supported, got '{laplacian}'",
            suggestions=["Use laplacian='normalized'"]
        )

    if random_state is not None and (not isinstance(random_state, int) or random_state < 0):
        raise AlgorithmError(
            f"random_state must be a non-negative integer or None, got {random_state}",
            suggestions=["Provide random_state >= 0 or None"]
        )

    if eigen_solver is not None and eigen_solver not in ["dense", "lobpcg"]:
        raise AlgorithmError(
            f"eigen_solver must be 'dense' or 'lobpcg', got '{eigen_solver}'",
            suggestions=["Use eigen_solver='dense' or 'lobpcg'"]
        )


def _compute_normalized_laplacian(
    adjacency: sp.spmatrix,
    eps: float = 1e-10
) -> sp.spmatrix:
    """Compute normalized Laplacian: L_norm = I - D^{-1/2} A D^{-1/2}.

    Args:
        adjacency: Adjacency matrix (sparse)
        eps: Small value to avoid division by zero

    Returns:
        Normalized Laplacian matrix (sparse)
    """
    n = adjacency.shape[0]

    # Compute degree vector
    degrees = np.asarray(adjacency.sum(axis=1)).flatten()

    # D^{-1/2} with safe division
    degrees_sqrt_inv = np.zeros_like(degrees)
    nonzero = degrees > eps
    degrees_sqrt_inv[nonzero] = 1.0 / np.sqrt(degrees[nonzero])

    # Create diagonal matrix D^{-1/2}
    D_sqrt_inv = sp.diags(degrees_sqrt_inv, format='csr')

    # L_norm = I - D^{-1/2} A D^{-1/2}
    I = sp.identity(n, format='csr')
    L_norm = I - D_sqrt_inv @ adjacency @ D_sqrt_inv

    return L_norm


def _spectral_embedding(
    laplacian: sp.spmatrix,
    k: int,
    eigen_solver: Optional[str] = None,
    random_state: Optional[int] = None,
) -> np.ndarray:
    """Compute spectral embedding from Laplacian.

    Args:
        laplacian: Normalized Laplacian matrix
        k: Number of eigenvectors to compute
        eigen_solver: 'dense', 'lobpcg', or None (auto)
        random_state: Random seed for reproducibility

    Returns:
        Embedding matrix (n × k)
    """
    n = laplacian.shape[0]

    # Auto-select solver
    if eigen_solver is None:
        # Use lobpcg for large matrices, dense for small
        eigen_solver = "lobpcg" if n > 1000 else "dense"

    # Add 1 to k since we'll discard the first (trivial) eigenvector
    k_compute = min(k + 1, n)

    if eigen_solver == "dense":
        # Convert to dense and use standard eigendecomposition
        L_dense = laplacian.toarray() if sp.issparse(laplacian) else laplacian
        eigenvalues, eigenvectors = np.linalg.eigh(L_dense)

        # Sort by eigenvalue (smallest first)
        idx = np.argsort(eigenvalues)
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]

        # Take k smallest non-trivial eigenvectors (skip first if it's ~0)
        if eigenvalues[0] < 1e-10:
            embedding = eigenvectors[:, 1:k_compute]
        else:
            embedding = eigenvectors[:, :k]

    elif eigen_solver == "lobpcg":
        # Use sparse eigendecomposition
        # LOBPCG needs initial guess
        if random_state is not None:
            rng = np.random.RandomState(random_state)
        else:
            rng = np.random.RandomState(0)

        X_init = rng.randn(n, k_compute)

        # Compute k smallest eigenvalues/vectors
        eigenvalues, eigenvectors = eigsh(
            laplacian, k=k_compute, which='SM', v0=X_init[:, 0]
        )

        # Sort by eigenvalue (smallest first)
        idx = np.argsort(eigenvalues)
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]

        # Take k smallest non-trivial eigenvectors
        if eigenvalues[0] < 1e-10:
            embedding = eigenvectors[:, 1:k_compute]
        else:
            embedding = eigenvectors[:, :k]

    else:
        raise AlgorithmError(
            f"Unknown eigen_solver: {eigen_solver}",
            suggestions=["Use 'dense' or 'lobpcg'"]
        )

    # Ensure we have exactly k dimensions
    if embedding.shape[1] < k:
        # Pad with zeros if needed (shouldn't happen in practice)
        padding = k - embedding.shape[1]
        embedding = np.hstack([embedding, np.zeros((n, padding))])
    elif embedding.shape[1] > k:
        embedding = embedding[:, :k]

    return embedding


def _kmeans_clustering(
    embedding: np.ndarray,
    k: int,
    random_state: Optional[int] = None,
) -> np.ndarray:
    """Run k-means on embedding to get cluster assignments.

    Args:
        embedding: Embedding matrix (n × k)
        k: Number of clusters
        random_state: Random seed

    Returns:
        Cluster labels (n,)
    """
    kmeans = KMeans(
        n_clusters=k,
        random_state=random_state if random_state is not None else 0,
        n_init=10
    )
    labels = kmeans.fit_predict(embedding)
    return labels


def spectral_multilayer_supra(
    network: Any,
    k: int,
    omega: float = 1.0,
    laplacian: Literal["normalized"] = "normalized",
    random_state: Optional[int] = None,
    eigen_solver: Optional[Literal["dense", "lobpcg"]] = None,
) -> Tuple[Dict[Tuple[Any, Any], int], Dict[str, Any]]:
    """Supra-Laplacian Spectral Clustering.

    This variant constructs the full supra-Laplacian matrix with interlayer
    coupling ω, performs spectral embedding on node-layer replicas, averages
    across layers, and clusters the resulting node-level embeddings.

    Mathematical formulation:
    1. Build supra-adjacency A^{supra} (nL × nL) with diagonal blocks A^[α]
       and off-diagonal blocks ωI
    2. Compute normalized supra-Laplacian L^{supra}_norm
    3. Get k smallest eigenvectors → X ∈ R^{(nL) × k}
    4. Average replicas: X̄_i = (1/L) Σ_{α} X_{(i,α)}
    5. Run k-means on X̄

    Args:
        network: Multilayer network object
        k: Number of communities (mandatory)
        omega: Interlayer coupling strength (default: 1.0)
        laplacian: Laplacian type, only "normalized" supported (default: "normalized")
        random_state: Random seed for k-means reproducibility (default: None)
        eigen_solver: Eigenvalue solver ("dense" or "lobpcg", default: auto)

    Returns:
        partition: Dict mapping (node, layer) -> community_id
        metadata: Dict with:
            - embedding_nodes: ndarray (n × k) - node-level embeddings
            - embedding_supra: ndarray (nL × k) - full supra-embeddings
            - n_communities: int - number of communities (equals k)
            - omega: float - coupling strength used

    Raises:
        AlgorithmError: If parameters are invalid
        Py3plexException: If network is empty or invalid

    Examples:
        >>> partition, meta = spectral_multilayer_supra(
        ...     net, k=3, omega=0.8, random_state=42
        ... )
        >>> embedding = meta["embedding_nodes"]  # Node-level embedding
    """
    # Validate parameters
    _validate_parameters(k, laplacian, random_state, eigen_solver)

    if omega < 0:
        raise AlgorithmError(
            f"omega must be non-negative, got {omega}",
            suggestions=["Use omega >= 0"]
        )

    # Get nodes and layers
    try:
        nodes_list = list(network.get_nodes())
    except (AttributeError, TypeError):
        # Handle case where core_network is None
        raise Py3plexException("Network has no nodes")

    if len(nodes_list) == 0:
        raise Py3plexException("Network has no nodes")

    # Extract unique nodes and layers
    unique_nodes = sorted({node for node, layer in nodes_list})
    sorted({layer for node, layer in nodes_list})
    n = len(unique_nodes)

    if k > n:
        raise AlgorithmError(
            f"k ({k}) cannot exceed number of nodes ({n})",
            suggestions=[f"Use k <= {n}"]
        )

    # Build node-layer to index mapping
    idx_to_node_layer = {i: (node, layer) for i, (node, layer) in enumerate(nodes_list)}

    # Get supra-adjacency matrix
    A_supra = network.get_supra_adjacency_matrix(mtype="sparse")
    n_supra = A_supra.shape[0]

    # Add interlayer coupling if omega > 0
    if omega > 0:
        # Build interlayer coupling matrix: ωI connecting same nodes across layers
        # For each node, connect its replicas across layers
        node_to_indices = {}
        for idx, (node, layer) in idx_to_node_layer.items():
            if node not in node_to_indices:
                node_to_indices[node] = []
            node_to_indices[node].append(idx)

        # Create coupling edges
        rows, cols, data = [], [], []
        for node, indices in node_to_indices.items():
            # Connect all pairs of replicas for this node
            for i in range(len(indices)):
                for j in range(i + 1, len(indices)):
                    rows.extend([indices[i], indices[j]])
                    cols.extend([indices[j], indices[i]])
                    data.extend([omega, omega])

        if len(rows) > 0:
            coupling = sp.coo_matrix(
                (data, (rows, cols)), shape=(n_supra, n_supra)
            ).tocsr()
            A_supra = A_supra + coupling

    # Compute normalized Laplacian
    L_supra = _compute_normalized_laplacian(A_supra)

    # Spectral embedding
    embedding_supra = _spectral_embedding(
        L_supra, k, eigen_solver=eigen_solver, random_state=random_state
    )

    # Average replicas across layers to get node-level embeddings
    node_to_idx_map = {node: i for i, node in enumerate(unique_nodes)}
    embedding_nodes = np.zeros((n, k))
    node_counts = np.zeros(n)

    for supra_idx, (node, layer) in idx_to_node_layer.items():
        node_idx = node_to_idx_map[node]
        embedding_nodes[node_idx] += embedding_supra[supra_idx]
        node_counts[node_idx] += 1

    # Average (divide by number of layers each node appears in)
    for i in range(n):
        if node_counts[i] > 0:
            embedding_nodes[i] /= node_counts[i]

    # K-means clustering on node-level embeddings
    node_labels = _kmeans_clustering(embedding_nodes, k, random_state=random_state)

    # Build partition: assign same community to all replicas of a node
    partition = {}
    for node, layer in nodes_list:
        node_idx = node_to_idx_map[node]
        partition[(node, layer)] = int(node_labels[node_idx])

    # Metadata
    metadata = {
        "embedding_nodes": embedding_nodes,
        "embedding_supra": embedding_supra,
        "n_communities": k,
        "omega": omega,
        "method": "spectral_multilayer_supra",
    }

    return partition, metadata


def spectral_multilayer_multiplex(
    network: Any,
    k: int,
    laplacian: Literal["normalized"] = "normalized",
    random_state: Optional[int] = None,
    eigen_solver: Optional[Literal["dense", "lobpcg"]] = None,
) -> Tuple[Dict[Tuple[Any, Any], int], Dict[str, Any]]:
    """Multiplex (Aggregated) Laplacian Spectral Clustering.

    This variant aggregates the normalized Laplacians of individual layers,
    then performs spectral clustering directly on nodes without constructing
    a supra-graph.

    Mathematical formulation:
    1. Compute layer Laplacians L^[α]_norm for each layer α
    2. Aggregate: L^{multi} = (1/L) Σ_{α} L^[α]_norm
    3. Get k smallest eigenvectors of L^{multi} → X ∈ R^{n × k}
    4. Run k-means on X

    Args:
        network: Multilayer network object
        k: Number of communities (mandatory)
        laplacian: Laplacian type, only "normalized" supported (default: "normalized")
        random_state: Random seed for k-means reproducibility (default: None)
        eigen_solver: Eigenvalue solver ("dense" or "lobpcg", default: auto)

    Returns:
        partition: Dict mapping (node, layer) -> community_id
        metadata: Dict with:
            - embedding_nodes: ndarray (n × k) - node-level embeddings
            - n_communities: int - number of communities (equals k)

    Raises:
        AlgorithmError: If parameters are invalid
        Py3plexException: If network is empty or invalid

    Examples:
        >>> partition, meta = spectral_multilayer_multiplex(
        ...     net, k=3, random_state=42
        ... )
        >>> embedding = meta["embedding_nodes"]  # Node-level embedding
    """
    # Validate parameters
    _validate_parameters(k, laplacian, random_state, eigen_solver)

    # Get nodes and layers
    try:
        nodes_list = list(network.get_nodes())
    except (AttributeError, TypeError):
        # Handle case where core_network is None
        raise Py3plexException("Network has no nodes")

    if len(nodes_list) == 0:
        raise Py3plexException("Network has no nodes")

    # Extract unique nodes and layers
    unique_nodes = sorted({node for node, layer in nodes_list})
    unique_layers = sorted({layer for node, layer in nodes_list})
    n = len(unique_nodes)

    if k > n:
        raise AlgorithmError(
            f"k ({k}) cannot exceed number of nodes ({n})",
            suggestions=[f"Use k <= {n}"]
        )

    # Build node to index mapping
    node_to_idx = {node: i for i, node in enumerate(unique_nodes)}

    # Initialize aggregated Laplacian
    L_multi = sp.csr_matrix((n, n), dtype=float)

    # Get network core for layer extraction
    G = network.core_network

    # Aggregate Laplacians across layers
    for layer in unique_layers:
        # Get nodes in this layer
        layer_nodes = [(node, l) for node, l in nodes_list if l == layer]
        if len(layer_nodes) == 0:
            continue

        # Build adjacency matrix for this layer
        layer_size = len(layer_nodes)
        node_layer_to_local = {nl: i for i, nl in enumerate(layer_nodes)}
        local_to_node = {i: node for i, (node, _) in enumerate(layer_nodes)}

        # Extract edges for this layer
        rows, cols, data = [], [], []
        for node1, l1 in layer_nodes:
            if (node1, l1) in G:
                for node2, l2 in G.neighbors((node1, l1)):
                    if l2 == layer:  # Only intralayer edges
                        local_idx1 = node_layer_to_local[(node1, l1)]
                        local_idx2 = node_layer_to_local[(node2, l2)]
                        # Get edge weight if available
                        edge_data = G.get_edge_data((node1, l1), (node2, l2))
                        weight = edge_data.get('weight', 1.0) if edge_data else 1.0
                        rows.append(local_idx1)
                        cols.append(local_idx2)
                        data.append(weight)

        if len(rows) == 0:
            # Empty layer - skip
            continue

        # Build sparse adjacency for this layer
        A_layer = sp.coo_matrix(
            (data, (rows, cols)), shape=(layer_size, layer_size)
        ).tocsr()

        # Make symmetric (for undirected networks)
        A_layer = (A_layer + A_layer.T) / 2

        # Compute normalized Laplacian for this layer
        L_layer = _compute_normalized_laplacian(A_layer)

        # Map to full node space
        L_full = sp.lil_matrix((n, n), dtype=float)
        for i in range(layer_size):
            for j in range(layer_size):
                if L_layer[i, j] != 0:
                    node_i = local_to_node[i]
                    node_j = local_to_node[j]
                    idx_i = node_to_idx[node_i]
                    idx_j = node_to_idx[node_j]
                    L_full[idx_i, idx_j] += L_layer[i, j]

        L_multi = L_multi + L_full.tocsr()

    # Average by number of layers
    if L > 0:
        L_multi = L_multi / L

    # Spectral embedding
    embedding_nodes = _spectral_embedding(
        L_multi, k, eigen_solver=eigen_solver, random_state=random_state
    )

    # K-means clustering
    node_labels = _kmeans_clustering(embedding_nodes, k, random_state=random_state)

    # Build partition: assign same community to all replicas of a node
    partition = {}
    for node, layer in nodes_list:
        node_idx = node_to_idx[node]
        partition[(node, layer)] = int(node_labels[node_idx])

    # Metadata
    metadata = {
        "embedding_nodes": embedding_nodes,
        "n_communities": k,
        "method": "spectral_multilayer_multiplex",
    }

    return partition, metadata


__all__ = [
    "spectral_multilayer_supra",
    "spectral_multilayer_multiplex",
]
