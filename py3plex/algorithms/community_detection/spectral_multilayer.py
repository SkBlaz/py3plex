r"""
Multilayer Spectral Clustering for py3plex.

This module implements two variants of spectral clustering for multilayer networks:

1. **Supra-Laplacian Spectral Clustering**: Constructs a supra-adjacency matrix 
   with identity-weighted interlayer coupling, computes the supra-Laplacian, 
   and performs spectral embedding followed by k-means clustering.

2. **Multiplex (Aggregated) Laplacian Spectral Clustering**: Aggregates 
   normalized Laplacians from all layers with uniform or custom weights, 
   performs spectral embedding on the aggregate, and clusters.

Mathematical Formulation
------------------------

**Shared Definitions:**

- Nodes: :math:`V = \{v_1, ..., v_n\}`
- Layers: :math:`\\alpha \in \{1, ..., L\}`
- Intralayer adjacency matrices: :math:`A^{[\\alpha]} \in \mathbb{R}^{n \\times n}`
- Degree matrices: :math:`D^{[\\alpha]}_{ii} = \sum_j A^{[\\alpha]}_{ij}`
- Intralayer Laplacians:
  
  - Unnormalized: :math:`L^{[\\alpha]} = D^{[\\alpha]} - A^{[\\alpha]}`
  - Normalized: :math:`L^{[\\alpha]}_{\\text{norm}} = I - (D^{[\\alpha]})^{-1/2} A^{[\\alpha]} (D^{[\\alpha]})^{-1/2}`

All matrices are symmetric and real.

**Variant A: Supra-Laplacian Spectral Clustering**

1. Supra-adjacency construction:

   .. math::
   
       A^{\\text{supra}} = \\begin{pmatrix}
       A^{[1]} & \\omega I & \\cdots & \\omega I \\\\
       \\omega I & A^{[2]} & \\cdots & \\omega I \\\\
       \\vdots & \\vdots & \\ddots & \\vdots \\\\
       \\omega I & \\omega I & \\cdots & A^{[L]}
       \\end{pmatrix}

   where each block is :math:`n \\times n`, :math:`\\omega I` connects node replicas 
   across layers, and :math:`\\omega \\geq 0` is the interlayer coupling.

2. Supra-Laplacian:

   .. math::
   
       D^{\\text{supra}}_{ii} = \sum_j A^{\\text{supra}}_{ij}
       
       L^{\\text{supra}}_{\\text{norm}} = I - (D^{\\text{supra}})^{-1/2} A^{\\text{supra}} (D^{\\text{supra}})^{-1/2}

3. Spectral embedding:

   Compute the :math:`k` smallest non-trivial eigenvectors:
   
   .. math::
   
       L^{\\text{supra}}_{\\text{norm}} X = \\Lambda X, \\quad X \in \mathbb{R}^{(nL) \\times k}
   
   Reshape embedding to node-level by averaging replicas:
   
   .. math::
   
       \\bar{X}_i = \\frac{1}{L} \sum_{\\alpha=1}^L X_{(i,\\alpha)}

4. Clustering:

   Run k-means on rows of :math:`\\bar{X}`:
   
   .. math::
   
       c_i = \\text{kmeans}(\\bar{X}_i)

**Variant B: Multiplex (Aggregated) Laplacian Spectral Clustering**

This variant never constructs a supra-graph.

1. Aggregate Laplacian:

   Compute layer Laplacians :math:`L^{[\\alpha]}_{\\text{norm}}`.
   
   Aggregate:
   
   .. math::
   
       L^{\\text{multi}} = \sum_{\\alpha=1}^L w_\\alpha L^{[\\alpha]}_{\\text{norm}}
   
   Default: :math:`w_\\alpha = \\frac{1}{L}` (no adaptive or learned weights).

2. Spectral embedding:

   Solve:
   
   .. math::
   
       L^{\\text{multi}} X = \\Lambda X, \\quad X \in \mathbb{R}^{n \\times k}
   
   Take the :math:`k` smallest non-zero eigenvectors.

3. Clustering:

   Apply k-means on rows of :math:`X`:
   
   .. math::
   
       c_i = \\text{kmeans}(X_i)

Parameter Contract
------------------

**Shared:**

- `k`: int — number of communities (mandatory)
- `laplacian`: Literal["normalized"] — only normalized Laplacian allowed
- `random_state`: Optional[int] — random seed for k-means
- `eigen_solver`: Literal["dense", "lobpcg"] — eigensolver (default: auto by size)

**Variant-specific:**

- Supra variant: `omega`: float >= 0 — interlayer coupling
- Multiplex variant: no coupling parameter

Complexity Guarantees
---------------------

**Variant A (Supra-Laplacian):**

- Memory: :math:`O((nL)^2)` worst-case (warn in docs)
- Time: Dominated by eigen decomposition

**Variant B (Multiplex):**

- Memory: :math:`O(n^2)`
- Time: Comparable to single-layer spectral clustering

Comparison Table
----------------

+--------------------+---------------------------+---------------------------+
| Property           | Supra-Laplacian           | Multiplex (Aggregated)    |
+====================+===========================+===========================+
| Coupling           | Identity links (omega)    | Implicit via aggregation  |
+--------------------+---------------------------+---------------------------+
| Memory             | O((nL)^2)                 | O(n^2)                    |
+--------------------+---------------------------+---------------------------+
| Embedding dim      | nL, then averaged to n    | n                         |
+--------------------+---------------------------+---------------------------+
| Layer distinction  | Explicit via supra-graph  | Averaged out              |
+--------------------+---------------------------+---------------------------+
| Omega parameter    | Required                  | Not applicable            |
+--------------------+---------------------------+---------------------------+

Notes
-----

- **k must be provided; py3plex does not infer k automatically.**
- Both variants are deterministic given fixed random_state.
- For L=1, both variants reduce to standard spectral clustering.
- Omega=0 in supra variant treats layers independently (averaged embedding).
- Large omega in supra variant synchronizes replicas tightly.

References
----------

- Von Luxburg, U. (2007). A tutorial on spectral clustering. 
  Statistics and computing, 17(4), 395-416.
- Gomez, S., et al. (2013). Diffusion dynamics on multiplex networks. 
  Physical review letters, 110(2), 028701.

Examples
--------
>>> from py3plex.core import multinet
>>> from py3plex.dsl import Q, L
>>>
>>> # Create network
>>> net = multinet.multi_layer_network(directed=False)
>>> # ... add edges ...
>>>
>>> # Supra-Laplacian variant
>>> result = (
...     Q.nodes()
...      .from_layers(L["social"] + L["work"])
...      .community(
...          method="spectral_multilayer_supra",
...          k=3,
...          omega=0.8,
...          random_state=42,
...      )
...      .execute(net)
... )
>>>
>>> # Multiplex variant
>>> result = (
...     Q.nodes()
...      .from_layers(L["social"] + L["work"])
...      .community(
...          method="spectral_multilayer_multiplex",
...          k=3,
...          random_state=42,
...      )
...      .execute(net)
... )
>>>
>>> # Access embedding
>>> emb = result.meta["embedding_nodes"]  # ndarray (n × k)
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Tuple
import logging
import warnings

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh, lobpcg
from sklearn.cluster import KMeans

from py3plex.exceptions import AlgorithmError


logger = logging.getLogger(__name__)


def _validate_parameters(
    k: int,
    laplacian: str,
    omega: Optional[float],
    random_state: Optional[int],
    eigen_solver: str,
    variant: str,
) -> None:
    """Validate spectral clustering parameters.
    
    Parameters
    ----------
    k : int
        Number of communities
    laplacian : str
        Laplacian type
    omega : float, optional
        Interlayer coupling (supra variant only)
    random_state : int, optional
        Random seed
    eigen_solver : str
        Eigensolver method
    variant : str
        "supra" or "multiplex"
        
    Raises
    ------
    AlgorithmError
        If parameters are invalid
    """
    if not isinstance(k, int) or k < 1:
        raise AlgorithmError(
            "k must be a positive integer",
            suggestions=["Provide k >= 1"]
        )
    
    if laplacian != "normalized":
        raise AlgorithmError(
            f"Only 'normalized' Laplacian is supported, got '{laplacian}'",
            suggestions=["Use laplacian='normalized'"]
        )
    
    if eigen_solver not in ["dense", "lobpcg", "auto"]:
        raise AlgorithmError(
            f"Invalid eigen_solver '{eigen_solver}'",
            suggestions=["Use 'dense', 'lobpcg', or 'auto'"]
        )
    
    if variant == "supra":
        if omega is None:
            raise AlgorithmError(
                "omega parameter required for supra variant",
                suggestions=["Provide omega >= 0"]
            )
        if omega < 0:
            raise AlgorithmError(
                f"omega must be non-negative, got {omega}",
                suggestions=["Use omega >= 0"]
            )
    elif variant == "multiplex":
        if omega is not None:
            warnings.warn(
                "omega parameter is ignored for multiplex variant",
                UserWarning
            )


def _compute_normalized_laplacian(adjacency: np.ndarray) -> np.ndarray:
    """Compute normalized Laplacian from adjacency matrix.
    
    L_norm = I - D^{-1/2} A D^{-1/2}
    
    Parameters
    ----------
    adjacency : np.ndarray
        Adjacency matrix (n x n)
        
    Returns
    -------
    np.ndarray
        Normalized Laplacian matrix (n x n)
    """
    n = adjacency.shape[0]
    
    # Compute degree vector
    degree = np.array(adjacency.sum(axis=1)).flatten()
    
    # Handle isolated nodes (degree = 0)
    # Set D^{-1/2} to 0 for isolated nodes
    degree_inv_sqrt = np.zeros(n)
    mask = degree > 0
    degree_inv_sqrt[mask] = 1.0 / np.sqrt(degree[mask])
    
    # Create diagonal matrix D^{-1/2}
    D_inv_sqrt = sp.diags(degree_inv_sqrt)
    
    # Compute normalized adjacency: D^{-1/2} A D^{-1/2}
    if sp.issparse(adjacency):
        A_norm = D_inv_sqrt @ adjacency @ D_inv_sqrt
    else:
        A_norm = D_inv_sqrt @ adjacency @ D_inv_sqrt
    
    # Compute Laplacian: I - A_norm
    I = sp.eye(n) if sp.issparse(adjacency) else np.eye(n)
    L_norm = I - A_norm
    
    return L_norm


def _extract_layer_adjacency(
    network: Any,
    layer: Any,
    node_order: List[Any]
) -> np.ndarray:
    """Extract adjacency matrix for a single layer.
    
    Parameters
    ----------
    network : multi_layer_network
        Multilayer network
    layer : Any
        Layer identifier
    node_order : list
        Ordered list of node identifiers
        
    Returns
    -------
    np.ndarray
        Adjacency matrix (n x n) for the layer
    """
    n = len(node_order)
    node_to_idx = {node: i for i, node in enumerate(node_order)}
    
    # Initialize adjacency matrix
    adjacency = np.zeros((n, n))
    
    # Use core_network to get edges with data
    # Edges in core_network are stored as ((node, layer), (node, layer), data)
    for src, tgt, data in network.core_network.edges(data=True):
        src_node, src_layer = src
        tgt_node, tgt_layer = tgt
        
        # Only consider intralayer edges for this layer
        if src_layer == layer and tgt_layer == layer:
            if src_node in node_to_idx and tgt_node in node_to_idx:
                i = node_to_idx[src_node]
                j = node_to_idx[tgt_node]
                
                # Get weight (default 1.0)
                weight = data.get('weight', 1.0)
                
                adjacency[i, j] = weight
                # For undirected networks, add symmetric entry
                if not network.directed:
                    adjacency[j, i] = weight
    
    return adjacency


def _solve_eigenproblem(
    laplacian: np.ndarray,
    k: int,
    eigen_solver: str = "auto",
    random_state: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """Solve eigenvalue problem for Laplacian matrix.
    
    Computes k smallest non-trivial eigenvectors.
    
    Parameters
    ----------
    laplacian : np.ndarray
        Laplacian matrix
    k : int
        Number of eigenvectors to compute
    eigen_solver : str
        Solver method: "dense", "lobpcg", or "auto"
    random_state : int, optional
        Random seed for initialization
        
    Returns
    -------
    eigenvalues : np.ndarray
        Eigenvalues (k,)
    eigenvectors : np.ndarray
        Eigenvectors (n, k)
    """
    n = laplacian.shape[0]
    
    # Check if k is valid
    if k >= n:
        raise AlgorithmError(
            f"k={k} must be less than n={n}",
            suggestions=[f"Use k < {n}"]
        )
    
    # Choose solver
    if eigen_solver == "auto":
        # Use dense for small matrices, sparse for large
        eigen_solver = "dense" if n < 1000 else "lobpcg"
    
    try:
        if eigen_solver == "dense":
            # Dense eigensolver (full eigendecomposition)
            if sp.issparse(laplacian):
                laplacian = laplacian.toarray()
            
            eigenvalues, eigenvectors = np.linalg.eigh(laplacian)
            
            # Select k smallest eigenvalues (after the first one, which is ~0)
            # For normalized Laplacian, smallest eigenvalue is 0 (constant eigenvector)
            # We want the next k smallest
            idx = np.argsort(eigenvalues)[1:k+1]
            eigenvalues = eigenvalues[idx]
            eigenvectors = eigenvectors[:, idx]
            
        elif eigen_solver == "lobpcg":
            # Sparse eigensolver using LOBPCG
            # LOBPCG needs initial guess
            rng = np.random.RandomState(random_state)
            X_init = rng.randn(n, k)
            
            if not sp.issparse(laplacian):
                laplacian = sp.csr_matrix(laplacian)
            
            # Compute k+1 smallest eigenvalues to skip the trivial one
            eigenvalues, eigenvectors = eigsh(
                laplacian,
                k=k+1,
                which='SM',  # Smallest magnitude
                v0=X_init[:, 0],
            )
            
            # Skip the first (trivial) eigenvector
            eigenvalues = eigenvalues[1:]
            eigenvectors = eigenvectors[:, 1:]
        
        else:
            raise ValueError(f"Invalid eigen_solver: {eigen_solver}")
        
        return eigenvalues, eigenvectors
    
    except Exception as e:
        raise AlgorithmError(
            f"Eigenvalue computation failed: {str(e)}",
            suggestions=[
                "Try different eigen_solver",
                "Check network connectivity",
                "Reduce k"
            ]
        )


def _kmeans_clustering(
    embedding: np.ndarray,
    k: int,
    random_state: Optional[int] = None
) -> np.ndarray:
    """Perform k-means clustering on embedding.
    
    Parameters
    ----------
    embedding : np.ndarray
        Node embedding matrix (n, k)
    k : int
        Number of clusters
    random_state : int, optional
        Random seed
        
    Returns
    -------
    labels : np.ndarray
        Cluster labels (n,)
    """
    kmeans = KMeans(
        n_clusters=k,
        random_state=random_state,
        n_init=10,
    )
    labels = kmeans.fit_predict(embedding)
    return labels


def spectral_multilayer_supra(
    network: Any,
    k: int,
    omega: float = 1.0,
    laplacian: Literal["normalized"] = "normalized",
    random_state: Optional[int] = None,
    eigen_solver: Literal["dense", "lobpcg", "auto"] = "auto",
    **kwargs
) -> Dict[str, Any]:
    """Supra-Laplacian spectral clustering for multilayer networks.
    
    This variant constructs a supra-adjacency matrix with identity-weighted
    interlayer coupling, computes the normalized supra-Laplacian, performs
    spectral embedding, averages node replicas across layers, and applies
    k-means clustering.
    
    Parameters
    ----------
    network : multi_layer_network
        Multilayer network object
    k : int
        Number of communities (mandatory)
    omega : float, default=1.0
        Interlayer coupling strength (>= 0)
        - omega=0: independent layers (averaged embedding)
        - large omega: tight synchronization across layers
    laplacian : str, default="normalized"
        Laplacian type (only "normalized" supported)
    random_state : int, optional
        Random seed for k-means reproducibility
    eigen_solver : str, default="auto"
        Eigensolver: "dense", "lobpcg", or "auto"
        - "dense": Full eigendecomposition (small networks)
        - "lobpcg": Sparse solver (large networks)
        - "auto": Choose based on network size
    **kwargs
        Additional parameters (ignored)
        
    Returns
    -------
    dict
        Results dictionary containing:
        - partition_nodes: dict mapping node -> community_id
        - embedding_nodes: ndarray (n, k) — node-level embedding
        - embedding_supra: ndarray (nL, k) — full supra embedding
        - eigenvalues: ndarray (k,) — eigenvalues
        - metadata: dict with algorithm info
        
    Raises
    ------
    AlgorithmError
        If parameters are invalid or computation fails
        
    Warnings
    --------
    For large networks (n > 1000, L > 5), memory usage is O((nL)^2).
    Consider using multiplex variant for better scalability.
        
    Examples
    --------
    >>> from py3plex.core import multinet
    >>> from py3plex.algorithms.community_detection import spectral_multilayer_supra
    >>>
    >>> net = multinet.multi_layer_network(directed=False)
    >>> # ... add edges ...
    >>>
    >>> result = spectral_multilayer_supra(
    ...     net, k=3, omega=0.8, random_state=42
    ... )
    >>> partition = result["partition_nodes"]
    >>> embedding = result["embedding_nodes"]
    """
    # Validate parameters
    _validate_parameters(k, laplacian, omega, random_state, eigen_solver, "supra")
    
    # Get node and layer information
    all_nodes = list({node for node, layer in network.get_nodes()})
    layer_data = network.get_layers()
    all_layers = layer_data[0] if isinstance(layer_data, tuple) else layer_data
    n = len(all_nodes)
    L = len(all_layers)
    
    logger.info(
        f"Supra-Laplacian spectral clustering: n={n}, L={L}, k={k}, omega={omega}"
    )
    
    # Warn about memory usage for large networks
    supra_size = n * L
    if supra_size > 5000:
        warnings.warn(
            f"Supra-graph has {supra_size} nodes (n={n}, L={L}). "
            f"Memory usage: O({supra_size}^2) ≈ {supra_size**2 * 8 / 1e9:.2f} GB. "
            "Consider using spectral_multilayer_multiplex for better scalability.",
            UserWarning
        )
    
    # Build supra-adjacency matrix
    # Block structure: each block is n x n
    # Diagonal blocks: layer adjacency matrices
    # Off-diagonal blocks: omega * I (identity coupling)
    
    supra_adj = np.zeros((supra_size, supra_size))
    
    # Fill diagonal blocks with layer adjacencies
    for layer_idx, layer in enumerate(all_layers):
        start_idx = layer_idx * n
        end_idx = start_idx + n
        
        layer_adj = _extract_layer_adjacency(network, layer, all_nodes)
        supra_adj[start_idx:end_idx, start_idx:end_idx] = layer_adj
    
    # Fill off-diagonal blocks with omega * I (interlayer coupling)
    identity = np.eye(n)
    for i in range(L):
        for j in range(L):
            if i != j:
                start_i = i * n
                end_i = start_i + n
                start_j = j * n
                end_j = start_j + n
                supra_adj[start_i:end_i, start_j:end_j] = omega * identity
    
    # Compute normalized supra-Laplacian
    supra_laplacian = _compute_normalized_laplacian(supra_adj)
    
    # Solve eigenvalue problem
    eigenvalues, eigenvectors_supra = _solve_eigenproblem(
        supra_laplacian, k, eigen_solver, random_state
    )
    
    # Average node replicas across layers
    # eigenvectors_supra shape: (nL, k)
    # Reshape to (L, n, k), then average over L
    eigenvectors_reshaped = eigenvectors_supra.reshape((L, n, k))
    embedding_nodes = eigenvectors_reshaped.mean(axis=0)  # (n, k)
    
    # Perform k-means clustering
    labels = _kmeans_clustering(embedding_nodes, k, random_state)
    
    # Build partition dict
    partition_nodes = {node: int(labels[i]) for i, node in enumerate(all_nodes)}
    
    # Return results
    return {
        "partition_nodes": partition_nodes,
        "embedding_nodes": embedding_nodes,
        "embedding_supra": eigenvectors_supra,
        "eigenvalues": eigenvalues,
        "metadata": {
            "method": "spectral_multilayer_supra",
            "k": k,
            "omega": omega,
            "n_nodes": n,
            "n_layers": L,
            "supra_size": supra_size,
            "laplacian": laplacian,
            "eigen_solver": eigen_solver,
            "random_state": random_state,
        }
    }


def spectral_multilayer_multiplex(
    network: Any,
    k: int,
    laplacian: Literal["normalized"] = "normalized",
    random_state: Optional[int] = None,
    eigen_solver: Literal["dense", "lobpcg", "auto"] = "auto",
    layer_weights: Optional[Dict[Any, float]] = None,
    **kwargs
) -> Dict[str, Any]:
    """Multiplex (aggregated) Laplacian spectral clustering for multilayer networks.
    
    This variant aggregates normalized Laplacians from all layers with uniform
    or custom weights, performs spectral embedding on the aggregate Laplacian,
    and applies k-means clustering. Does NOT construct a supra-graph.
    
    Parameters
    ----------
    network : multi_layer_network
        Multilayer network object
    k : int
        Number of communities (mandatory)
    laplacian : str, default="normalized"
        Laplacian type (only "normalized" supported)
    random_state : int, optional
        Random seed for k-means reproducibility
    eigen_solver : str, default="auto"
        Eigensolver: "dense", "lobpcg", or "auto"
        - "dense": Full eigendecomposition (small networks)
        - "lobpcg": Sparse solver (large networks)
        - "auto": Choose based on network size
    layer_weights : dict, optional
        Custom weights for each layer. If None, uniform weights (1/L) are used.
        No adaptive or learned weights.
    **kwargs
        Additional parameters (ignored, omega is not used)
        
    Returns
    -------
    dict
        Results dictionary containing:
        - partition_nodes: dict mapping node -> community_id
        - embedding_nodes: ndarray (n, k) — node-level embedding
        - eigenvalues: ndarray (k,) — eigenvalues
        - metadata: dict with algorithm info
        
    Raises
    ------
    AlgorithmError
        If parameters are invalid or computation fails
        
    Notes
    -----
    Memory: O(n^2), Time: comparable to single-layer spectral clustering.
    More scalable than supra variant for large multilayer networks.
        
    Examples
    --------
    >>> from py3plex.core import multinet
    >>> from py3plex.algorithms.community_detection import spectral_multilayer_multiplex
    >>>
    >>> net = multinet.multi_layer_network(directed=False)
    >>> # ... add edges ...
    >>>
    >>> result = spectral_multilayer_multiplex(
    ...     net, k=3, random_state=42
    ... )
    >>> partition = result["partition_nodes"]
    >>> embedding = result["embedding_nodes"]
    >>>
    >>> # With custom layer weights
    >>> result = spectral_multilayer_multiplex(
    ...     net, k=3, layer_weights={"social": 0.6, "work": 0.4}, random_state=42
    ... )
    """
    # Validate parameters
    _validate_parameters(k, laplacian, None, random_state, eigen_solver, "multiplex")
    
    # Get node and layer information
    all_nodes = list({node for node, layer in network.get_nodes()})
    layer_data = network.get_layers()
    all_layers = layer_data[0] if isinstance(layer_data, tuple) else layer_data
    n = len(all_nodes)
    L = len(all_layers)
    
    logger.info(
        f"Multiplex spectral clustering: n={n}, L={L}, k={k}"
    )
    
    # Set up layer weights
    if layer_weights is None:
        # Uniform weights
        weights = {layer: 1.0 / L for layer in all_layers}
    else:
        # Validate custom weights
        if set(layer_weights.keys()) != set(all_layers):
            raise AlgorithmError(
                "layer_weights must include all layers",
                suggestions=[f"Provide weights for: {all_layers}"]
            )
        # Normalize weights
        total_weight = sum(layer_weights.values())
        weights = {layer: w / total_weight for layer, w in layer_weights.items()}
    
    # Aggregate Laplacians
    aggregated_laplacian = np.zeros((n, n))
    
    for layer in all_layers:
        layer_adj = _extract_layer_adjacency(network, layer, all_nodes)
        layer_laplacian = _compute_normalized_laplacian(layer_adj)
        
        # Add weighted contribution
        weight = weights[layer]
        aggregated_laplacian += weight * layer_laplacian
    
    # Solve eigenvalue problem
    eigenvalues, eigenvectors = _solve_eigenproblem(
        aggregated_laplacian, k, eigen_solver, random_state
    )
    
    # eigenvectors shape: (n, k)
    embedding_nodes = eigenvectors
    
    # Perform k-means clustering
    labels = _kmeans_clustering(embedding_nodes, k, random_state)
    
    # Build partition dict
    partition_nodes = {node: int(labels[i]) for i, node in enumerate(all_nodes)}
    
    # Return results
    return {
        "partition_nodes": partition_nodes,
        "embedding_nodes": embedding_nodes,
        "eigenvalues": eigenvalues,
        "metadata": {
            "method": "spectral_multilayer_multiplex",
            "k": k,
            "n_nodes": n,
            "n_layers": L,
            "layer_weights": weights,
            "laplacian": laplacian,
            "eigen_solver": eigen_solver,
            "random_state": random_state,
        }
    }


__all__ = [
    "spectral_multilayer_supra",
    "spectral_multilayer_multiplex",
]
