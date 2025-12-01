#!/usr/bin/env python3
"""
Multilayer/Multiplex Network Centrality Measures

This module implements various centrality measures for multilayer and multiplex networks,
following standard definitions from multilayer network analysis literature.

Weight Handling Notes:
----------------------
For path-based centralities (betweenness, closeness):
- Edge weights from the supra-adjacency matrix are converted to distances (inverse of weight)
- NetworkX algorithms use these distances for shortest path computation
- betweenness_centrality: weight parameter specifies the edge attribute for path computation
- closeness_centrality: distance parameter specifies the edge attribute for path computation

For disconnected graphs:
- closeness_centrality uses wf_improved parameter (Wasserman-Faust scaling) by default
- When wf_improved=True, scores are normalized by reachable nodes only
- When wf_improved=False, unreachable nodes contribute infinite distance

Weight Constraints:
- Weights should be positive (> 0) for shortest path algorithms
- Zero or negative weights will cause undefined behavior
- For unweighted analysis, use weighted=False parameters

Authors: py3plex contributors
Date: 2025
"""

from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple, Union

import networkx as nx
import numpy as np
import scipy.sparse as sp
from scipy.sparse import identity
from scipy.sparse.linalg import eigs

# Import supra matrix function centralities
from py3plex.algorithms.multilayer_algorithms.supra_matrix_function_centrality import (
    communicability_centrality,
    katz_centrality,
)


class MultilayerCentrality:
    """
    Class for computing centrality measures on multilayer networks.

    This class provides implementations of various centrality measures
    specifically designed for multilayer/multiplex networks, including
    degree-based, eigenvector-based, and path-based measures.
    """

    def __init__(self, network: Any) -> None:
        """
        Initialize the centrality calculator.

        Args:
            network: py3plex multi_layer_network object
        """
        self.network = network
        self._supra_matrix = None
        self._layer_matrices: Optional[Dict[str, np.ndarray]] = None
        self._node_layer_mapping: Optional[Dict[Any, int]] = None
        self._reverse_node_layer_mapping: Optional[Dict[int, Any]] = None
        self._nodes: Optional[List[str]] = None
        self._layers: Optional[List[str]] = None
        self._node_to_idx: Optional[Dict[str, int]] = None

    def _get_supra_adjacency_matrix(self) -> Any:
        """Get the supra-adjacency matrix."""
        if self._supra_matrix is None:
            self._supra_matrix = self.network.get_supra_adjacency_matrix()
        return self._supra_matrix

    def _get_layer_matrices(self) -> Dict[str, np.ndarray]:
        """Extract individual layer adjacency matrices."""
        if self._layer_matrices is None:
            self._layer_matrices = {}
            layers = set()
            nodes = set()

            # Get all unique layers and nodes
            for node in self.network.get_nodes():
                node_id, layer = node
                layers.add(layer)
                nodes.add(node_id)

            sorted_layers = sorted(layers)
            sorted_nodes = sorted(nodes)

            # Create mapping from node to index
            node_to_idx = {node: i for i, node in enumerate(sorted_nodes)}

            # Build layer matrices
            for layer in sorted_layers:
                n_nodes = len(sorted_nodes)
                matrix = np.zeros((n_nodes, n_nodes))

                for edge in self.network.get_edges(data=True):
                    (n1, l1), (n2, l2) = edge[0], edge[1]
                    if l1 == layer and l2 == layer:  # Intralayer edge
                        i, j = node_to_idx[n1], node_to_idx[n2]
                        weight = edge[2].get("weight", 1) if len(edge) > 2 else 1
                        matrix[i, j] = weight
                        if not self.network.directed:
                            matrix[j, i] = weight

                self._layer_matrices[layer] = matrix

            self._nodes = sorted_nodes
            self._layers = sorted_layers
            self._node_to_idx = node_to_idx

        return self._layer_matrices

    def _get_node_layer_mapping(self) -> Tuple[Dict, Dict]:
        """Get mapping between (node, layer) pairs and supra-matrix indices."""
        if self._node_layer_mapping is None:
            mapping = {}
            reverse_mapping = {}
            idx = 0

            for node in self.network.get_nodes():
                mapping[node] = idx
                reverse_mapping[idx] = node
                idx += 1

            self._node_layer_mapping = mapping
            self._reverse_node_layer_mapping = reverse_mapping

        return self._node_layer_mapping, self._reverse_node_layer_mapping

    # ==================== DEGREE/STRENGTH-BASED MEASURES ====================

    def layer_degree_centrality(
        self,
        layer: Optional[str] = None,
        weighted: bool = False,
        direction: str = "out",
    ) -> Dict[Union[str, Tuple[str, str]], float]:
        """
        Compute layer-specific degree (or strength) centrality.

        For undirected networks:
            k^[α]_i = Σ_j 1(A^[α]_ij > 0)  [unweighted]
            s^[α]_i = Σ_j A^[α]_ij         [weighted]

        For directed networks:
            k^[α,out]_i = Σ_j 1(A^[α]_ij > 0)  [out-degree]
            k^[α,in]_i = Σ_j 1(A^[α]_ji > 0)   [in-degree]

        Args:
            layer: Layer to compute centrality for. If None, compute for all layers.
            weighted: If True, compute strength instead of degree.
            direction: 'out', 'in', or 'both' for directed networks.

        Returns:
            dict: {(node, layer): centrality_value} if layer is None,
                  {node: centrality_value} if layer is specified.
        """
        layer_matrices = self._get_layer_matrices()

        if layer is not None:
            layers_to_process = [layer]
        else:
            layers_to_process = self._layers

        results: Dict[Union[str, Tuple[str, str]], float] = {}

        for layer_name in layers_to_process:
            if layer_name not in layer_matrices:
                continue

            matrix = layer_matrices[layer_name]

            if weighted:
                if self.network.directed:
                    if direction == "out":
                        centralities = np.sum(matrix, axis=1)
                    elif direction == "in":
                        centralities = np.sum(matrix, axis=0)
                    else:  # both
                        centralities = np.sum(matrix, axis=1) + np.sum(matrix, axis=0)
                else:
                    centralities = np.sum(matrix, axis=1)
            else:
                # Convert to binary matrix for degree calculation
                binary_matrix = (matrix > 0).astype(int)
                if self.network.directed:
                    if direction == "out":
                        centralities = np.sum(binary_matrix, axis=1)
                    elif direction == "in":
                        centralities = np.sum(binary_matrix, axis=0)
                    else:  # both
                        centralities = np.sum(binary_matrix, axis=1) + np.sum(
                            binary_matrix, axis=0
                        )
                else:
                    centralities = np.sum(binary_matrix, axis=1)

            # Map back to node names
            for i, node in enumerate(self._nodes):
                if layer is not None:
                    results[node] = centralities[i]
                else:
                    results[(node, layer_name)] = centralities[i]

        return results

    def supra_degree_centrality(self, weighted: bool = False) -> Dict:
        """
        Compute supra degree/strength centrality (node-layer level).

        k_{iα} = Σ_{j,β} 1(M_{(i,α),(j,β)} > 0)  [unweighted]
        s_{iα} = Σ_{j,β} M_{(i,α),(j,β)}          [weighted]

        Args:
            weighted: If True, compute strength instead of degree.

        Returns:
            dict: {(node, layer): centrality_value}
        """
        supra_matrix = self._get_supra_adjacency_matrix()
        node_layer_mapping, reverse_mapping = self._get_node_layer_mapping()

        if hasattr(supra_matrix, "toarray"):
            matrix = supra_matrix.toarray()
        else:
            matrix = supra_matrix

        results = {}

        if weighted:
            centralities = np.sum(matrix, axis=1)
        else:
            binary_matrix = (matrix > 0).astype(int)
            centralities = np.sum(binary_matrix, axis=1)

        for node_layer, idx in node_layer_mapping.items():
            results[node_layer] = centralities[idx]

        return results

    def overlapping_degree_centrality(self, weighted: bool = False) -> Dict:
        """
        Compute overlapping degree/strength centrality (node level).

        k^{over}_i = Σ_α k^[α]_i      [unweighted]
        s^{over}_i = Σ_α s^[α]_i      [weighted]

        Args:
            weighted: If True, compute overlapping strength.

        Returns:
            dict: {node: centrality_value}
        """
        layer_centralities = self.layer_degree_centrality(weighted=weighted)
        results: Dict[str, float] = defaultdict(float)

        for key, centrality in layer_centralities.items():
            if isinstance(key, tuple):
                node, _layer = key
                results[node] += centrality
            else:
                # Shouldn't happen when layer=None, but handle gracefully
                results[str(key)] += centrality

        return dict(results)

    def participation_coefficient(self, weighted: bool = False) -> Dict:
        """
        Compute participation coefficient across layers.

        Measures how evenly a node's degree is distributed across layers:
        P_i = 1 - Σ_α (k^[α]_i / k^{over}_i)^2

        Set P_i = 0 if k^{over}_i = 0.

        Args:
            weighted: If True, use strength instead of degree.

        Returns:
            dict: {node: participation_coefficient}
        """
        layer_centralities = self.layer_degree_centrality(weighted=weighted)
        overlapping_centralities = self.overlapping_degree_centrality(weighted=weighted)

        results = {}

        for node in self._nodes:
            total_degree = overlapping_centralities.get(node, 0)

            if total_degree == 0:
                results[node] = 0.0
                continue

            sum_squared_ratios = 0.0
            for layer in self._layers:
                layer_degree = layer_centralities.get((node, layer), 0)
                ratio = layer_degree / total_degree
                sum_squared_ratios += ratio**2

            results[node] = 1.0 - sum_squared_ratios

        return results

    # ==================== EIGENVECTOR-TYPE MEASURES ====================

    def multiplex_eigenvector_centrality(
        self, max_iter: int = 1000, tol: float = 1e-6
    ) -> Dict:
        """
        Compute multiplex eigenvector centrality (node-layer level).

        x = (1/λ_max) * M * x
        where x_{iα} is the centrality of node i in layer α,
        and λ_max is the spectral radius of the supra-adjacency matrix M.

        Args:
            max_iter: Maximum number of iterations.
            tol: Tolerance for convergence.

        Returns:
            dict: {(node, layer): centrality_value}
        """
        supra_matrix = self._get_supra_adjacency_matrix()
        node_layer_mapping, reverse_mapping = self._get_node_layer_mapping()

        # Convert to appropriate format for eigenvalue computation
        if hasattr(supra_matrix, "toarray"):
            matrix = supra_matrix
        else:
            matrix = sp.csr_matrix(supra_matrix)

        try:
            # Compute the principal eigenvector
            eigenval, eigenvec = eigs(
                matrix, k=1, which="LM", maxiter=max_iter, tol=tol
            )
            eigenvec = np.real(eigenvec.flatten())

            # Normalize to make values positive
            if np.sum(eigenvec) < 0:
                eigenvec = -eigenvec

            # Normalize
            eigenvec = eigenvec / np.linalg.norm(eigenvec)

        except (np.linalg.LinAlgError, ArithmeticError, RuntimeError):
            # Fallback to power iteration if eigenvalue computation fails
            n = matrix.shape[0]
            x = np.random.rand(n)
            x = x / np.linalg.norm(x)

            for _ in range(max_iter):
                x_new = matrix.dot(x)
                if np.linalg.norm(x_new) > 0:
                    x_new = x_new / np.linalg.norm(x_new)
                    if np.linalg.norm(x - x_new) < tol:
                        break
                    x = x_new
                else:
                    break
            eigenvec = x

        results = {}
        for node_layer, idx in node_layer_mapping.items():
            results[node_layer] = abs(eigenvec[idx])

        return results

    def multiplex_eigenvector_versatility(
        self, max_iter: int = 1000, tol: float = 1e-6
    ) -> Dict:
        """
        Compute node-level eigenvector versatility.

        x̄_i = Σ_α x_{iα}

        Args:
            max_iter: Maximum number of iterations.
            tol: Tolerance for convergence.

        Returns:
            dict: {node: versatility_value}
        """
        node_layer_centralities = self.multiplex_eigenvector_centrality(max_iter, tol)
        results: Dict[str, float] = defaultdict(float)

        for (node, _layer), centrality in node_layer_centralities.items():
            results[node] += centrality

        return dict(results)

    def katz_bonacich_centrality(self, alpha=0.1, beta=None):
        """
        Compute Katz-Bonacich centrality on the supra-graph.

        z = Σ_{t=0}^∞ α^t M^t b = (I - αM)^{-1} b

        Args:
            alpha: Attenuation parameter (should be < 1/ρ(M)). If None, automatically
                  computes a safe value as 0.85/ρ(M) where ρ(M) is the spectral radius.
            beta: Exogenous preference vector. If None, uses vector of ones.

        Returns:
            dict: {(node, layer): centrality_value}
        """
        supra_matrix = self._get_supra_adjacency_matrix()
        node_layer_mapping, reverse_mapping = self._get_node_layer_mapping()

        if hasattr(supra_matrix, "toarray"):
            matrix = sp.csr_matrix(supra_matrix)
        else:
            matrix = supra_matrix

        n = matrix.shape[0]

        # Auto-compute alpha if not provided
        if alpha is None:
            try:
                from scipy.sparse.linalg import eigs
                eigenvalues, _ = eigs(matrix, k=1, which='LM', maxiter=1000)
                rho = np.abs(eigenvalues[0])
                if rho > 0:
                    alpha = 0.85 / rho  # Conservative choice
                else:
                    alpha = 0.1  # Fallback for zero spectral radius
            except (ArithmeticError, RuntimeError, ValueError):
                alpha = 0.1  # Fallback value

        if beta is None:
            beta = np.ones(n)
        else:
            beta = np.array(beta)

        # Compute (I - αM)^{-1} b
        identity_matrix = identity(n, format="csr")
        try:
            centralities = sp.linalg.spsolve(identity_matrix - alpha * matrix, beta)
        except (np.linalg.LinAlgError, RuntimeError, ValueError):
            # Fallback: use series approximation if sparse solve fails
            centralities = beta.copy()
            current_term = beta.copy()
            for _ in range(100):  # Limit iterations
                current_term = alpha * matrix.dot(current_term)
                centralities += current_term
                if np.linalg.norm(current_term) < 1e-8:
                    break

        results = {}
        for node_layer, idx in node_layer_mapping.items():
            results[node_layer] = centralities[idx]

        return results

    def pagerank_centrality(self, damping=0.85, max_iter=1000, tol=1e-6):
        """
        Compute PageRank centrality on the supra-graph.

        Uses the standard PageRank algorithm on the supra-adjacency matrix
        representing the multilayer network. Properly handles dangling nodes
        (nodes with no outgoing edges) via teleportation.

        This implementation preserves sparsity when possible for memory efficiency.

        Args:
            damping: Damping parameter (typically 0.85).
            max_iter: Maximum number of iterations.
            tol: Tolerance for convergence.

        Returns:
            dict: {(node, layer): centrality_value}

        Mathematical Invariants:
            - PageRank values sum to 1.0 (within tol=1e-6)
            - All values are non-negative
            - Converges for strongly connected components or with teleportation
        """
        supra_matrix = self._get_supra_adjacency_matrix()
        node_layer_mapping, reverse_mapping = self._get_node_layer_mapping()

        # Keep as sparse if possible
        is_sparse = sp.issparse(supra_matrix)

        if is_sparse:
            # Sparse computation
            n = supra_matrix.shape[0]

            # Compute row sums efficiently
            row_sums = np.array(supra_matrix.sum(axis=1)).flatten()

            # Identify dangling nodes
            dangling_mask = row_sums == 0
            n_dangling = np.sum(dangling_mask)

            # Build sparse transition matrix
            # For non-dangling nodes: P = D^{-1} * A where D is diagonal matrix of row sums
            safe_row_sums = row_sums.copy()
            safe_row_sums[dangling_mask] = 1  # Temporary to avoid div/0

            # Create diagonal matrix for normalization
            D_inv = sp.diags(1.0 / safe_row_sums, format='csr')
            P_sparse = D_inv @ supra_matrix

            # For dangling nodes, we need to add uniform distribution
            # This breaks pure sparsity, but only for dangling rows
            if n_dangling > 0:
                # Build dangling node rows efficiently using sparse matrix construction
                uniform_prob = 1.0 / n

                # Create rows for dangling nodes as dense arrays (unavoidable for uniform distribution)
                dangling_indices = np.where(dangling_mask)[0]
                dangling_rows = sp.csr_matrix(
                    (np.full(n * n_dangling, uniform_prob),
                     (np.repeat(np.arange(n_dangling), n), np.tile(np.arange(n), n_dangling))),
                    shape=(n_dangling, n)
                )

                # Replace dangling rows in transition matrix
                # Convert to lil for efficient row assignment
                P_sparse = P_sparse.tolil()
                for i, idx in enumerate(dangling_indices):
                    P_sparse[idx] = dangling_rows[i]
                P_sparse = P_sparse.tocsr()

            # Initialize PageRank vector
            pagerank = np.ones(n) / n

            # Power iteration with sparse operations
            for iteration in range(max_iter):
                # Sparse matrix-vector multiply
                new_pagerank = (1 - damping) / n + damping * (P_sparse.T @ pagerank)

                if np.linalg.norm(pagerank - new_pagerank) < tol:
                    break
                pagerank = new_pagerank

        else:
            # Dense computation (original code path for small networks)
            if hasattr(supra_matrix, "toarray"):
                matrix = supra_matrix.toarray()
            else:
                matrix = np.array(supra_matrix)

            n = matrix.shape[0]

            # Create row-stochastic transition matrix with proper dangling node handling
            row_sums = np.sum(matrix, axis=1)

            # Identify dangling nodes (no outgoing edges)
            dangling_mask = row_sums == 0

            # Avoid division by zero: use reciprocal where safe
            safe_row_sums = row_sums.copy()
            safe_row_sums[dangling_mask] = 1  # Temporary value to avoid div/0
            transition_matrix = matrix / safe_row_sums[:, np.newaxis]

            # For dangling nodes, distribute probability uniformly (teleportation)
            # This ensures true stochasticity: each dangling node row sums to 1
            if dangling_mask.any():
                transition_matrix[dangling_mask, :] = 1.0 / n

            # Initialize PageRank vector
            pagerank = np.ones(n) / n

            # Power iteration with proper PageRank formula
            for _ in range(max_iter):
                # Standard PageRank: PR = (1-d)/n * 1 + d * P^T * PR
                # The teleportation is already built into P for dangling nodes
                new_pagerank = (1 - damping) / n + damping * transition_matrix.T.dot(
                    pagerank
                )

                if np.linalg.norm(pagerank - new_pagerank) < tol:
                    break
                pagerank = new_pagerank

        results = {}
        for node_layer, idx in node_layer_mapping.items():
            results[node_layer] = pagerank[idx]

        return results

    # ==================== PATH-BASED MEASURES ====================

    def multilayer_closeness_centrality(self, normalized=True, wf_improved=True, variant="standard"):
        """
        Compute closeness centrality on the supra-graph.

        For each node-layer pair (i,α), computes:

        Standard closeness:
            C_c(i,α) = (n-1) / Σ_{(j,β)} d((i,α), (j,β))

        Harmonic closeness (recommended for disconnected networks):
            HC(i,α) = Σ_{(j,β)≠(i,α)} 1/d((i,α), (j,β))

        where d((i,α), (j,β)) is the shortest path distance in the supra-graph.

        Args:
            normalized: This parameter is kept for API compatibility but has no effect.
                       Standard closeness is always normalized by (n-1) per the
                       NetworkX implementation. Harmonic closeness returns unnormalized
                       sums of reciprocal distances by definition.
            wf_improved: If True, use Wasserman-Faust improved closeness scaling
                        for disconnected graphs. Default is True. This affects
                        the magnitude and ordering of scores in graphs with
                        multiple components (e.g., low interlayer coupling).
                        See NetworkX documentation for details. Only used when
                        variant='standard'.
            variant: Closeness variant to use. Options:
                    - 'standard': Classic closeness (reciprocal of sum of distances).
                      For disconnected graphs, uses Wasserman-Faust scaling if
                      wf_improved=True. Can produce biased values for nodes in
                      small or disconnected components.
                    - 'harmonic': Harmonic closeness (sum of reciprocal distances).
                      Mathematically well-defined for disconnected networks:
                      unreachable nodes contribute 0 instead of infinity.
                      Recommended for disconnected multilayer networks.
                    - 'auto': Automatically selects 'harmonic' if the supra-graph
                      has multiple connected components, otherwise uses 'standard'.
                    Default is 'standard' for backward compatibility.

        Returns:
            dict: {(node, layer): closeness_centrality}

        Note:
            This implementation uses NetworkX's shortest path algorithms on
            the supra-graph representation. For large networks, this can be
            computationally expensive.

            For disconnected multilayer graphs (e.g., layers with no inter-layer
            coupling, or networks with isolated components), use variant='harmonic'
            or variant='auto' to get mathematically consistent closeness values.
            The harmonic variant naturally handles unreachable nodes by summing
            1/d for finite distances only (infinite distances contribute 0).

            Weight Interpretation: Edge weights from the supra-adjacency matrix
            are interpreted as connection strengths (larger weight = stronger
            connection). They are converted to distances via 1/weight for
            shortest path computation. If your edge weights already represent
            distances, use them directly without this function's weight inversion.

        Examples:
            >>> # For connected networks, standard closeness works well
            >>> closeness = calc.multilayer_closeness_centrality(variant='standard')

            >>> # For potentially disconnected networks, use harmonic
            >>> closeness = calc.multilayer_closeness_centrality(variant='harmonic')

            >>> # Let the algorithm decide based on connectivity
            >>> closeness = calc.multilayer_closeness_centrality(variant='auto')

        References:
            - Wasserman, S., & Faust, K. (1994). Social Network Analysis.
            - Boldi, P., & Vigna, S. (2014). Axioms for Centrality. Internet Math.
            - De Domenico, M., et al. (2015). Structural reducibility of multilayer networks.
        """
        # Convert supra-adjacency matrix to NetworkX graph
        supra_matrix = self._get_supra_adjacency_matrix()
        node_layer_mapping, reverse_mapping = self._get_node_layer_mapping()

        # Create NetworkX graph from supra-adjacency matrix
        if hasattr(supra_matrix, "toarray"):
            matrix = supra_matrix.toarray()
        else:
            matrix = np.array(supra_matrix)

        # Create directed/undirected graph based on network type
        if self.network.directed:
            G = nx.DiGraph()
        else:
            G = nx.Graph()

        # Add edges with weights (inverse of adjacency values for shortest paths)
        n = matrix.shape[0]
        for i in range(n):
            for j in range(n):
                if matrix[i, j] > 0:
                    # Use inverse of weight as edge length for shortest paths
                    edge_length = (
                        1.0 / matrix[i, j] if matrix[i, j] > 0 else float("inf")
                    )
                    G.add_edge(i, j, weight=edge_length)

        # Handle 'auto' variant: check if graph is disconnected
        if variant == "auto":
            if self.network.directed:
                is_connected = nx.is_weakly_connected(G) if G.number_of_nodes() > 0 else True
            else:
                is_connected = nx.is_connected(G) if G.number_of_nodes() > 0 else True

            if not is_connected:
                variant = "harmonic"
            else:
                variant = "standard"

        # Compute closeness centrality based on variant
        if variant == "harmonic":
            # Use harmonic centrality for disconnected-graph-aware computation
            try:
                nx_closeness = nx.harmonic_centrality(G, distance="weight")
            except (nx.NetworkXError, KeyError, AttributeError):
                # Fallback: compute manually
                nx_closeness = {}
                for source in G.nodes():
                    try:
                        lengths = nx.single_source_dijkstra_path_length(G, source, weight="weight")
                        harmonic = sum(1.0 / d for target, d in lengths.items() if d > 0)
                        nx_closeness[source] = harmonic
                    except (nx.NetworkXError, ZeroDivisionError):
                        nx_closeness[source] = 0.0
        else:
            # Use standard closeness centrality
            try:
                nx_closeness = nx.closeness_centrality(G, distance="weight", wf_improved=wf_improved)
            except (nx.NetworkXError, KeyError, ZeroDivisionError):
                # Fallback: use unweighted distances
                try:
                    nx_closeness = nx.closeness_centrality(G, wf_improved=wf_improved)
                except (nx.NetworkXError, ZeroDivisionError):
                    # If graph is disconnected, compute for each component
                    nx_closeness = {}
                    for node in G.nodes():
                        nx_closeness[node] = 0.0

        # Map back to node-layer pairs
        results = {}
        for node_layer, idx in node_layer_mapping.items():
            results[node_layer] = nx_closeness.get(idx, 0.0)

        return results

    def multilayer_betweenness_centrality(self, normalized=True, endpoints=False):
        """
        Compute betweenness centrality on the supra-graph.

        For each node-layer pair (i,α), computes the fraction of shortest
        paths between all pairs of nodes that pass through (i,α).

        Args:
            normalized: Whether to normalize the betweenness values.
            endpoints: Whether to include endpoints in path counts.

        Returns:
            dict: {(node, layer): betweenness_centrality}

        Note:
            This is computationally expensive for large networks as it
            requires computing shortest paths between all pairs of nodes.

            Weight handling: Edge weights from the supra-adjacency matrix are
            converted to distances (1/weight) for shortest path computation.
            Weights must be positive (> 0). Zero or negative weights will
            cause undefined behavior.
        """
        # Convert supra-adjacency matrix to NetworkX graph
        supra_matrix = self._get_supra_adjacency_matrix()
        node_layer_mapping, reverse_mapping = self._get_node_layer_mapping()

        # Create NetworkX graph from supra-adjacency matrix
        if hasattr(supra_matrix, "toarray"):
            matrix = supra_matrix.toarray()
        else:
            matrix = np.array(supra_matrix)

        # Create directed/undirected graph based on network type
        if self.network.directed:
            G = nx.DiGraph()
        else:
            G = nx.Graph()

        # Add edges with weights (inverse of adjacency values for shortest paths)
        n = matrix.shape[0]
        for i in range(n):
            for j in range(n):
                if matrix[i, j] > 0:
                    # Use inverse of weight as edge length for shortest paths
                    edge_length = (
                        1.0 / matrix[i, j] if matrix[i, j] > 0 else float("inf")
                    )
                    G.add_edge(i, j, weight=edge_length)

        # Compute betweenness centrality
        try:
            nx_betweenness = nx.betweenness_centrality(
                G, weight="weight", normalized=normalized, endpoints=endpoints
            )
        except (nx.NetworkXError, KeyError, ValueError):
            # Fallback: use unweighted betweenness
            try:
                nx_betweenness = nx.betweenness_centrality(
                    G, normalized=normalized, endpoints=endpoints
                )
            except (nx.NetworkXError, RuntimeError):
                # If computation fails, return zeros
                nx_betweenness = {}
                for node in G.nodes():
                    nx_betweenness[node] = 0.0

        # Map back to node-layer pairs
        results = {}
        for node_layer, idx in node_layer_mapping.items():
            results[node_layer] = nx_betweenness.get(idx, 0.0)

        return results

    # ==================== HITS ALGORITHM ====================

    def hits_centrality(self, max_iter=1000, tol=1e-6):
        """
        Compute HITS (hubs and authorities) centrality on the supra-graph.

        For undirected networks, this equals eigenvector centrality.
        For directed networks, computes separate hub and authority scores.

        Args:
            max_iter: Maximum number of iterations.
            tol: Tolerance for convergence.

        Returns:
            dict: If directed network: {'hubs': {(node, layer): score}, 'authorities': {(node, layer): score}}
                  If undirected network: {(node, layer): score} (equivalent to eigenvector centrality)
        """
        supra_matrix = self._get_supra_adjacency_matrix()
        node_layer_mapping, reverse_mapping = self._get_node_layer_mapping()

        # Create NetworkX graph from supra-adjacency matrix
        if hasattr(supra_matrix, "toarray"):
            matrix = supra_matrix.toarray()
        else:
            matrix = np.array(supra_matrix)

        # Create directed/undirected graph based on network type
        if self.network.directed:
            G = nx.DiGraph()
        else:
            G = nx.Graph()

        # Add edges
        n = matrix.shape[0]
        for i in range(n):
            for j in range(n):
                if matrix[i, j] > 0:
                    G.add_edge(i, j, weight=matrix[i, j])

        try:
            if self.network.directed:
                # Compute separate hub and authority scores
                hubs, authorities = nx.hits(G, max_iter=max_iter, tol=tol)

                # Map back to node-layer pairs
                results = {"hubs": {}, "authorities": {}}
                for node_layer, idx in node_layer_mapping.items():
                    results["hubs"][node_layer] = hubs.get(idx, 0.0)
                    results["authorities"][node_layer] = authorities.get(idx, 0.0)

                return results
            else:
                # For undirected networks, HITS equals eigenvector centrality
                return self.multiplex_eigenvector_centrality(max_iter, tol)

        except (nx.PowerIterationFailedConvergence, nx.NetworkXError, RuntimeError):
            # Fallback to eigenvector centrality if HITS fails
            if self.network.directed:
                eigenvec = self.multiplex_eigenvector_centrality(max_iter, tol)
                return {"hubs": eigenvec, "authorities": eigenvec}
            else:
                return self.multiplex_eigenvector_centrality(max_iter, tol)

    # ==================== CURRENT-FLOW CENTRALITY ====================

    def current_flow_closeness_centrality(self):
        """
        Compute current-flow closeness centrality via supra Laplacian pseudoinverse.

        This measure is based on the resistance distance in electrical networks.

        Returns:
            dict: {(node, layer): current_flow_closeness}
        """
        supra_matrix = self._get_supra_adjacency_matrix()
        node_layer_mapping, reverse_mapping = self._get_node_layer_mapping()

        if hasattr(supra_matrix, "toarray"):
            matrix = supra_matrix.toarray()
        else:
            matrix = np.array(supra_matrix)

        # Create NetworkX graph
        G = nx.Graph()  # Current flow is always on undirected graphs
        n = matrix.shape[0]
        for i in range(n):
            for j in range(n):
                if matrix[i, j] > 0:
                    G.add_edge(i, j, weight=matrix[i, j])

        try:
            nx_current_flow = nx.current_flow_closeness_centrality(G, weight="weight")
        except (nx.NetworkXError, np.linalg.LinAlgError, RuntimeError):
            # Fallback to regular closeness if current flow computation fails
            try:
                nx_current_flow = nx.closeness_centrality(G, distance="weight")
            except (nx.NetworkXError, ZeroDivisionError):
                nx_current_flow = {}
                for node in G.nodes():
                    nx_current_flow[node] = 0.0

        # Map back to node-layer pairs
        results = {}
        for node_layer, idx in node_layer_mapping.items():
            results[node_layer] = nx_current_flow.get(idx, 0.0)

        return results

    def current_flow_betweenness_centrality(self):
        """
        Compute current-flow betweenness centrality via supra Laplacian pseudoinverse.

        This measure is based on the electrical current flow through each node.

        Returns:
            dict: {(node, layer): current_flow_betweenness}
        """
        supra_matrix = self._get_supra_adjacency_matrix()
        node_layer_mapping, reverse_mapping = self._get_node_layer_mapping()

        if hasattr(supra_matrix, "toarray"):
            matrix = supra_matrix.toarray()
        else:
            matrix = np.array(supra_matrix)

        # Create NetworkX graph
        G = nx.Graph()  # Current flow is always on undirected graphs
        n = matrix.shape[0]
        for i in range(n):
            for j in range(n):
                if matrix[i, j] > 0:
                    G.add_edge(i, j, weight=matrix[i, j])

        try:
            nx_current_flow = nx.current_flow_betweenness_centrality(G, weight="weight")
        except (nx.NetworkXError, np.linalg.LinAlgError, RuntimeError):
            # Fallback to regular betweenness if current flow computation fails
            try:
                nx_current_flow = nx.betweenness_centrality(G, weight="weight")
            except (nx.NetworkXError, RuntimeError):
                nx_current_flow = {}
                for node in G.nodes():
                    nx_current_flow[node] = 0.0

        # Map back to node-layer pairs
        results = {}
        for node_layer, idx in node_layer_mapping.items():
            results[node_layer] = nx_current_flow.get(idx, 0.0)

        return results

    # ==================== COMMUNICABILITY-BASED MEASURES ====================

    def subgraph_centrality(self):
        """
        Compute subgraph centrality via matrix exponential of the supra-adjacency matrix.

        Subgraph centrality counts closed walks of all lengths starting and ending at each node.
        SC_i = (e^A)_ii where A is the adjacency matrix.

        Returns:
            dict: {(node, layer): subgraph_centrality}
        """
        supra_matrix = self._get_supra_adjacency_matrix()
        node_layer_mapping, reverse_mapping = self._get_node_layer_mapping()

        if hasattr(supra_matrix, "toarray"):
            matrix = supra_matrix.toarray()
        else:
            matrix = np.array(supra_matrix)

        try:
            # Compute matrix exponential
            from scipy.linalg import expm

            exp_matrix = expm(matrix)

            # Extract diagonal elements (subgraph centrality)
            results = {}
            for node_layer, idx in node_layer_mapping.items():
                results[node_layer] = exp_matrix[idx, idx]

            return results

        except (ImportError, np.linalg.LinAlgError, RuntimeError, MemoryError):
            # Fallback: approximate using eigendecomposition if matrix exponential fails
            try:
                eigenvals, eigenvecs = np.linalg.eigh(matrix)
                exp_eigenvals = np.exp(eigenvals)

                results = {}
                for node_layer, idx in node_layer_mapping.items():
                    # Subgraph centrality = sum_k (v_k[i])^2 * exp(lambda_k)
                    centrality = np.sum((eigenvecs[idx, :] ** 2) * exp_eigenvals)
                    results[node_layer] = centrality

                return results
            except (np.linalg.LinAlgError, MemoryError):
                # If all else fails, return degree centrality as approximation
                return self.supra_degree_centrality(weighted=True)

    def total_communicability(self):
        """
        Compute total communicability via matrix exponential.

        Total communicability is the row sum of the matrix exponential:
        TC_i = sum_j (e^A)_ij

        Returns:
            dict: {(node, layer): total_communicability}
        """
        supra_matrix = self._get_supra_adjacency_matrix()
        node_layer_mapping, reverse_mapping = self._get_node_layer_mapping()

        if hasattr(supra_matrix, "toarray"):
            matrix = supra_matrix.toarray()
        else:
            matrix = np.array(supra_matrix)

        try:
            # Compute matrix exponential
            from scipy.linalg import expm

            exp_matrix = expm(matrix)

            # Sum across rows
            results = {}
            for node_layer, idx in node_layer_mapping.items():
                results[node_layer] = np.sum(exp_matrix[idx, :])

            return results

        except (ImportError, np.linalg.LinAlgError, RuntimeError, MemoryError):
            # Fallback using Katz centrality as approximation if matrix exponential fails
            return self.katz_bonacich_centrality(alpha=0.1)

    # ==================== K-CORE MEASURES ====================

    def multiplex_k_core(self):
        """
        Compute multiplex k-core decomposition.

        A node belongs to the k-core if it has at least k neighbors in the multilayer network.
        This implementation computes the core number for each node-layer pair.

        Returns:
            dict: {(node, layer): core_number}
        """
        supra_matrix = self._get_supra_adjacency_matrix()
        node_layer_mapping, reverse_mapping = self._get_node_layer_mapping()

        if hasattr(supra_matrix, "toarray"):
            matrix = supra_matrix.toarray()
        else:
            matrix = np.array(supra_matrix)

        # Create NetworkX graph
        if self.network.directed:
            G = nx.DiGraph()
        else:
            G = nx.Graph()

        n = matrix.shape[0]
        for i in range(n):
            for j in range(n):
                if matrix[i, j] > 0:
                    G.add_edge(i, j)

        try:
            # Compute k-core decomposition
            core_numbers = nx.core_number(G)

            # Map back to node-layer pairs
            results = {}
            for node_layer, idx in node_layer_mapping.items():
                results[node_layer] = core_numbers.get(idx, 0)

            return results

        except (nx.NetworkXError, RuntimeError):
            # Fallback: use degree as approximation if k-core computation fails
            degree_centralities = self.supra_degree_centrality(weighted=False)
            return {k: int(v) for k, v in degree_centralities.items()}

    def multiplex_coreness(self):
        """
        Alias for multiplex_k_core for compatibility.

        Returns:
            dict: {(node, layer): core_number}
        """
        return self.multiplex_k_core()

    # ==================== INFORMATION CENTRALITY ====================

    def information_centrality(self):
        """
        Compute Information Centrality (Stephenson-Zelen style) on the supra-graph.

        Information centrality measures the importance of a node based on the
        information flow through the network. It uses the inverse of a modified
        Laplacian matrix.

        Returns:
            dict: {(node, layer): information_centrality}

        Note:
            This implementation returns values for each node-layer pair in the
            supra-graph, not aggregated physical node values. To obtain physical
            node-level information centrality, use the aggregate_to_node_level()
            method on the returned dictionary.

            The implementation uses NetworkX's information_centrality for computation.
            Falls back to harmonic closeness if information centrality computation fails.

            Information centrality is defined only for undirected graphs. For directed
            networks, the graph is symmetrized with a warning.

        References:
            - Stephenson, K., & Zelen, M. (1989). Rethinking centrality: Methods and
              examples. Social Networks, 11(1), 1-37.
        """
        supra_matrix = self._get_supra_adjacency_matrix()
        node_layer_mapping, reverse_mapping = self._get_node_layer_mapping()

        if hasattr(supra_matrix, "toarray"):
            matrix = supra_matrix.toarray()
        else:
            matrix = np.array(supra_matrix)

        # Create NetworkX graph
        # Information centrality requires undirected graphs
        if self.network.directed:
            import warnings
            warnings.warn(
                "Information centrality is defined for undirected graphs. "
                "Converting directed multilayer network to undirected by symmetrizing.",
                UserWarning,
                stacklevel=2
            )
        G = nx.Graph()
        n = matrix.shape[0]
        for i in range(n):
            for j in range(n):
                if matrix[i, j] > 0:
                    G.add_edge(i, j, weight=matrix[i, j])

        try:
            # Use NetworkX's information_centrality
            nx_info_cent = nx.information_centrality(G, weight="weight")
        except (nx.NetworkXError, np.linalg.LinAlgError, RuntimeError, AttributeError):
            # Fallback: use harmonic closeness as approximation
            try:
                nx_info_cent = {}
                for node in G.nodes():
                    # Harmonic centrality as approximation
                    lengths = nx.single_source_shortest_path_length(G, node)
                    harmonic = sum(1.0 / d for t, d in lengths.items() if d > 0)
                    nx_info_cent[node] = harmonic
            except (nx.NetworkXError, ZeroDivisionError):
                nx_info_cent = {}
                for node in G.nodes():
                    nx_info_cent[node] = 0.0

        # Map back to node-layer pairs
        results = {}
        for node_layer, idx in node_layer_mapping.items():
            results[node_layer] = nx_info_cent.get(idx, 0.0)

        return results

    # ==================== COMMUNICABILITY BETWEENNESS ====================

    def communicability_betweenness_centrality(self, normalized=True):
        """
        Compute communicability betweenness centrality on the supra-graph.

        This measure quantifies how much a node contributes to the communicability
        between other pairs of nodes. It uses the matrix exponential to account
        for all walks between nodes.

        Args:
            normalized: If True (default), normalize scores by dividing by the
                       maximum value (min-max scaling to [0, 1] range). Note that
                       this is simple rescaling, not the theoretical Estrada-Hatano
                       normalization from the original literature.

        Returns:
            dict: {(node, layer): communicability_betweenness}

        Note:
            This implementation uses NetworkX's communicability_betweenness_centrality,
            which operates on unweighted graphs. Edge weights from the supra-adjacency
            matrix are used only to determine edge existence (weight > 0), not for
            weighted communicability computation. For truly weighted communicability
            analysis, a custom implementation using the weighted matrix exponential
            would be required.

            This is computationally expensive as it requires computing the matrix
            exponential multiple times. For large networks, this may take significant time.
        """
        supra_matrix = self._get_supra_adjacency_matrix()
        node_layer_mapping, reverse_mapping = self._get_node_layer_mapping()

        if hasattr(supra_matrix, "toarray"):
            matrix = supra_matrix.toarray()
        else:
            matrix = np.array(supra_matrix)

        # Create NetworkX graph
        # Communicability betweenness requires undirected graphs
        if self.network.directed:
            import warnings
            warnings.warn(
                "Communicability betweenness is defined for undirected graphs. "
                "Converting directed multilayer network to undirected by symmetrizing.",
                UserWarning,
                stacklevel=2
            )
        G = nx.Graph()
        n = matrix.shape[0]
        for i in range(n):
            for j in range(n):
                if matrix[i, j] > 0:
                    G.add_edge(i, j, weight=matrix[i, j])

        try:
            # Use NetworkX's communicability_betweenness_centrality
            nx_comm_between = nx.communicability_betweenness_centrality(G)

            # Handle NaN values that can arise from numerical instability in matrix exponential
            # NaN typically occurs when exp(A) has very large values or numerical overflow
            nx_comm_between = {k: 0.0 if np.isnan(v) or np.isinf(v) else v
                             for k, v in nx_comm_between.items()}

            if normalized and nx_comm_between:
                max_val = max(nx_comm_between.values())
                if max_val > 0:
                    nx_comm_between = {k: v / max_val for k, v in nx_comm_between.items()}
        except (nx.NetworkXError, np.linalg.LinAlgError, RuntimeError, MemoryError, AttributeError):
            # Fallback: approximate using regular betweenness
            try:
                nx_comm_between = nx.betweenness_centrality(G, normalized=normalized)
            except (nx.NetworkXError, RuntimeError):
                nx_comm_between = {}
                for node in G.nodes():
                    nx_comm_between[node] = 0.0

        # Map back to node-layer pairs
        results = {}
        for node_layer, idx in node_layer_mapping.items():
            results[node_layer] = nx_comm_between.get(idx, 0.0)

        return results

    # ==================== ACCESSIBILITY ====================

    def accessibility_centrality(self, h=2):
        """
        Compute accessibility centrality (entropy-based reach within h steps).

        Accessibility measures the diversity of nodes reachable within h steps
        using entropy of the probability distribution.

        Access_r = exp(H_r) where H_r is the entropy of the h-step distribution

        Args:
            h: Number of steps (default: 2)

        Returns:
            dict: {(node, layer): accessibility}

        Note:
            Accessibility is measured as the effective number of h-step destinations,
            using the entropy of the random walk distribution.

            Dangling Node Handling: For nodes with no outgoing edges (dangling nodes),
            this implementation uses uniform teleportation to all nodes. This differs
            from the original Travencolo-Costa definition which does not include
            teleportation. The teleportation ensures a well-defined random walk
            distribution but may affect accessibility values for nodes near dangling
            nodes compared to implementations that handle dangling nodes differently.

        References:
            - Travencolo, B. A. N., & Costa, L. D. F. (2008). Accessibility in complex
              networks. Physics Letters A, 373(1), 89-95.
        """
        supra_matrix = self._get_supra_adjacency_matrix()
        node_layer_mapping, reverse_mapping = self._get_node_layer_mapping()

        if hasattr(supra_matrix, "toarray"):
            matrix = supra_matrix.toarray()
        else:
            matrix = np.array(supra_matrix)

        n = matrix.shape[0]

        # Create row-normalized transition matrix with proper dangling node handling
        row_sums = np.sum(matrix, axis=1)
        dangling_mask = row_sums == 0

        # Avoid division by zero
        safe_row_sums = row_sums.copy()
        safe_row_sums[dangling_mask] = 1
        P = matrix / safe_row_sums[:, np.newaxis]

        # For dangling nodes, use uniform distribution (teleportation)
        if dangling_mask.any():
            P[dangling_mask, :] = 1.0 / n

        # Compute P^h
        P_h = np.linalg.matrix_power(P, h)

        # Compute accessibility for each node
        results = {}
        epsilon = 1e-10

        for node_layer, idx in node_layer_mapping.items():
            p_r_h = P_h[idx, :]

            # Compute entropy
            p_r_h_safe = np.maximum(p_r_h, epsilon)
            entropy = -np.sum(p_r_h_safe * np.log(p_r_h_safe))

            # Accessibility is exp(entropy)
            accessibility = np.exp(entropy)

            results[node_layer] = accessibility

        return results

    # ==================== HARMONIC CLOSENESS ====================

    def harmonic_closeness_centrality(self):
        """
        Compute harmonic closeness centrality on the supra-graph.

        Harmonic closeness handles disconnected graphs better than standard closeness
        by summing the reciprocals of distances instead of taking reciprocal of sum.

        HC(u) = sum_{v≠u} (1 / d(u,v)) for finite distances

        Returns:
            dict: {(node, layer): harmonic_closeness}

        Note:
            This measure naturally handles disconnected components as unreachable
            nodes contribute 0 (instead of infinity) to the sum.

            Weight Interpretation: Edge weights from the supra-adjacency matrix
            are interpreted as connection strengths (larger weight = stronger
            connection = shorter distance). They are converted to distances via
            1/weight for shortest path computation. If your edge weights already
            represent distances, do not use this function directly—you would need
            to invert them first or use the distance values directly in a custom
            computation.
        """
        supra_matrix = self._get_supra_adjacency_matrix()
        node_layer_mapping, reverse_mapping = self._get_node_layer_mapping()

        if hasattr(supra_matrix, "toarray"):
            matrix = supra_matrix.toarray()
        else:
            matrix = np.array(supra_matrix)

        # Create NetworkX graph
        if self.network.directed:
            G = nx.DiGraph()
        else:
            G = nx.Graph()

        n = matrix.shape[0]
        for i in range(n):
            for j in range(n):
                if matrix[i, j] > 0:
                    # Use inverse of weight as edge length
                    edge_length = 1.0 / matrix[i, j] if matrix[i, j] > 0 else float("inf")
                    G.add_edge(i, j, weight=edge_length)

        try:
            # Use NetworkX's harmonic_centrality
            nx_harmonic = nx.harmonic_centrality(G, distance="weight")
        except (nx.NetworkXError, KeyError, AttributeError):
            # Fallback: compute manually
            nx_harmonic = {}
            for source in G.nodes():
                try:
                    lengths = nx.single_source_dijkstra_path_length(G, source, weight="weight")
                    harmonic = sum(1.0 / d for target, d in lengths.items() if d > 0)
                    nx_harmonic[source] = harmonic
                except (nx.NetworkXError, ZeroDivisionError):
                    nx_harmonic[source] = 0.0

        # Map back to node-layer pairs
        results = {}
        for node_layer, idx in node_layer_mapping.items():
            results[node_layer] = nx_harmonic.get(idx, 0.0)

        return results

    # ==================== LOCAL EFFICIENCY ====================

    def local_efficiency_centrality(self):
        """
        Compute local efficiency centrality.

        Local efficiency measures how efficiently information is exchanged among
        a node's neighbors when the node is removed. It quantifies the fault
        tolerance of the network.

        LE(u) = (1 / (|N_u|*(|N_u|-1))) * sum_{i≠j in N_u} [1 / d(i,j)]

        Returns:
            dict: {(node, layer): local_efficiency}

        Note:
            For nodes with less than 2 neighbors, local efficiency is 0.
        """
        supra_matrix = self._get_supra_adjacency_matrix()
        node_layer_mapping, reverse_mapping = self._get_node_layer_mapping()

        if hasattr(supra_matrix, "toarray"):
            matrix = supra_matrix.toarray()
        else:
            matrix = np.array(supra_matrix)

        # Create NetworkX graph
        # Local efficiency is typically computed on undirected graphs
        if self.network.directed:
            import warnings
            warnings.warn(
                "Local efficiency is typically defined for undirected graphs. "
                "Converting directed multilayer network to undirected by symmetrizing.",
                UserWarning,
                stacklevel=2
            )
        G = nx.Graph()
        n = matrix.shape[0]
        for i in range(n):
            for j in range(n):
                if matrix[i, j] > 0:
                    edge_length = 1.0 / matrix[i, j] if matrix[i, j] > 0 else float("inf")
                    G.add_edge(i, j, weight=edge_length)

        results = {}

        for node_layer, idx in node_layer_mapping.items():
            if idx not in G:
                results[node_layer] = 0.0
                continue

            neighbors = list(G.neighbors(idx))
            n_neighbors = len(neighbors)

            if n_neighbors < 2:
                results[node_layer] = 0.0
                continue

            # Create subgraph of neighbors
            subgraph = G.subgraph(neighbors)

            # Compute efficiency within subgraph
            efficiency_sum = 0.0
            count = 0

            for i in neighbors:
                for j in neighbors:
                    if i < j:  # Avoid double counting
                        try:
                            length = nx.shortest_path_length(
                                subgraph, i, j, weight="weight"
                            )
                            if length > 0:
                                efficiency_sum += 1.0 / length
                        except nx.NetworkXNoPath:
                            # No path between i and j
                            pass
                        count += 1

            if count > 0:
                local_eff = efficiency_sum / count
            else:
                local_eff = 0.0

            results[node_layer] = local_eff

        return results

    # ==================== EDGE BETWEENNESS & BRIDGING ====================

    def edge_betweenness_centrality(self, normalized=True):
        """
        Compute edge betweenness centrality on the supra-graph.

        Edge betweenness measures the fraction of shortest paths that pass
        through each edge.

        Returns:
            dict: {(source, target): edge_betweenness}

        Note:
            This returns edge-level centrality, not node-level.
        """
        supra_matrix = self._get_supra_adjacency_matrix()
        node_layer_mapping, reverse_mapping = self._get_node_layer_mapping()

        if hasattr(supra_matrix, "toarray"):
            matrix = supra_matrix.toarray()
        else:
            matrix = np.array(supra_matrix)

        # Create NetworkX graph
        if self.network.directed:
            G = nx.DiGraph()
        else:
            G = nx.Graph()

        n = matrix.shape[0]
        for i in range(n):
            for j in range(n):
                if matrix[i, j] > 0:
                    edge_length = 1.0 / matrix[i, j] if matrix[i, j] > 0 else float("inf")
                    G.add_edge(i, j, weight=edge_length)

        try:
            edge_between = nx.edge_betweenness_centrality(
                G, weight="weight", normalized=normalized
            )
        except (nx.NetworkXError, RuntimeError):
            # Fallback: return empty dict
            edge_between = {}

        # Map back to node-layer pairs
        results = {}
        for edge, value in edge_between.items():
            source_nl = reverse_mapping.get(edge[0])
            target_nl = reverse_mapping.get(edge[1])
            if source_nl and target_nl:
                results[(source_nl, target_nl)] = value

        return results

    def bridging_centrality(self):
        """
        Compute bridging centrality for nodes in the supra-graph.

        Bridging centrality combines betweenness with the bridging coefficient,
        which measures how much a node connects sparse regions of the network.

        Bridging(u) = B(u) * BCoeff(u)
        where BCoeff(u) = (1 / k_u) * sum_{v in N(u)} [1 / k_v]

        Returns:
            dict: {(node, layer): bridging_centrality}

        Note:
            Nodes with higher bridging centrality act as important bridges
            connecting different parts of the network.
        """
        # Get betweenness centrality
        betweenness = self.multilayer_betweenness_centrality(normalized=True)

        # Get degree centralities
        degrees = self.supra_degree_centrality(weighted=False)

        # Compute bridging coefficient
        supra_matrix = self._get_supra_adjacency_matrix()
        node_layer_mapping, reverse_mapping = self._get_node_layer_mapping()

        if hasattr(supra_matrix, "toarray"):
            matrix = supra_matrix.toarray()
        else:
            matrix = np.array(supra_matrix)

        results = {}

        for node_layer, idx in node_layer_mapping.items():
            k_u = degrees.get(node_layer, 0)

            if k_u == 0:
                results[node_layer] = 0.0
                continue

            # Find neighbors
            neighbors_sum = 0.0
            for j, adj_val in enumerate(matrix[idx, :]):
                if adj_val > 0:
                    neighbor_nl = reverse_mapping.get(j)
                    if neighbor_nl:
                        k_v = degrees.get(neighbor_nl, 0)
                        if k_v > 0:
                            neighbors_sum += 1.0 / k_v

            bridging_coeff = neighbors_sum / k_u if k_u > 0 else 0
            bridging_cent = betweenness.get(node_layer, 0) * bridging_coeff

            results[node_layer] = bridging_cent

        return results

    # ==================== PERCOLATION CENTRALITY ====================

    def percolation_centrality(self, edge_activation_prob=0.5, trials=100):
        """
        Compute percolation centrality using bond percolation Monte Carlo simulation.

        This implementation measures the average relative component size that a node
        belongs to across multiple bond percolation realizations, providing an estimate
        of a node's importance for network connectivity under random edge failures.

        Args:
            edge_activation_prob: Probability that an edge is active (default: 0.5)
            trials: Number of Monte Carlo trials (default: 100)

        Returns:
            dict: {(node, layer): percolation_centrality}

        Note:
            This is a component-size-based percolation measure, not the path-based
            percolation betweenness from the original Piraveenan et al. literature,
            which requires recomputing betweenness on each percolated realization.
            The original percolation centrality is computationally expensive (O(n³)
            per trial), so this implementation provides a more efficient alternative
            that captures related connectivity information.

            Values are normalized to [0, 1] range where higher values indicate nodes
            that tend to belong to larger connected components across percolation
            realizations.

        References:
            - Piraveenan, M., Prokopenko, M., & Hossain, L. (2013). Percolation
              centrality: Quantifying graph-theoretic impact of nodes during
              percolation in networks. PloS one, 8(1), e53095.
        """
        supra_matrix = self._get_supra_adjacency_matrix()
        node_layer_mapping, reverse_mapping = self._get_node_layer_mapping()

        if hasattr(supra_matrix, "toarray"):
            matrix = supra_matrix.toarray()
        else:
            matrix = np.array(supra_matrix)

        n = matrix.shape[0]

        # Initialize size tracking
        size_accumulator = dict.fromkeys(node_layer_mapping.keys(), 0.0)

        # Run Monte Carlo trials
        for _ in range(trials):
            # Create percolated graph
            G_trial = nx.Graph()

            # Sample edges with probability p
            for i in range(n):
                for j in range(i + 1, n):
                    if matrix[i, j] > 0:
                        if np.random.random() < edge_activation_prob:
                            G_trial.add_edge(i, j)

            # Compute connected components
            components = list(nx.connected_components(G_trial))

            # For each node, find the size of its component
            node_to_component_size = {}
            for component in components:
                size = len(component)
                for node in component:
                    node_to_component_size[node] = size

            # Accumulate sizes
            for node_layer, idx in node_layer_mapping.items():
                size_accumulator[node_layer] += node_to_component_size.get(idx, 1)

        # Compute average and normalize
        results = {}
        for node_layer in node_layer_mapping.keys():
            results[node_layer] = size_accumulator[node_layer] / (trials * n)

        return results

    # ==================== SPREADING (EPIDEMIC) CENTRALITY ====================

    def spreading_centrality(self, beta=0.2, mu=0.1, trials=50, steps=100):
        """
        Compute spreading (epidemic) centrality using SIR model.

        Spreading centrality measures how influential a node is in spreading
        information or disease through the network, based on Monte Carlo
        simulations of discrete-time SIR dynamics.

        Args:
            beta: Infection rate per edge per time step (default: 0.2)
            mu: Recovery rate per time step (default: 0.1)
            trials: Number of simulation trials per node (default: 50)
            steps: Maximum simulation steps (default: 100)

        Returns:
            dict: {(node, layer): spreading_centrality}

        Note:
            This measures the average outbreak size (fraction of nodes ever infected)
            when seeding the epidemic from each node. Values are normalized by the
            total number of nodes, producing scores in the range [1/n, 1] where n is
            the number of supra-graph nodes.

            This is an empirical simulation-based measure, not normalized by
            theoretical epidemic threshold or branching factor as in some literature
            definitions. The normalization allows comparison of relative spreading
            power within the network but may not be directly comparable across
            networks of different sizes or structures.

        References:
            - Kitsak, M., et al. (2010). Identification of influential spreaders
              in complex networks. Nature physics, 6(11), 888-893.
        """
        supra_matrix = self._get_supra_adjacency_matrix()
        node_layer_mapping, reverse_mapping = self._get_node_layer_mapping()

        if hasattr(supra_matrix, "toarray"):
            matrix = supra_matrix.toarray()
        else:
            matrix = np.array(supra_matrix)

        n = matrix.shape[0]

        # Create NetworkX graph for SIR simulation
        G = nx.Graph()
        for i in range(n):
            for j in range(i + 1, n):
                if matrix[i, j] > 0:
                    G.add_edge(i, j, weight=matrix[i, j])

        results = {}

        # Run SIR simulation starting from each node
        for node_layer, seed_idx in node_layer_mapping.items():
            total_outbreak = 0

            for _ in range(trials):
                # Initialize states: S=0, I=1, R=2
                state = np.zeros(n, dtype=int)  # All susceptible
                state[seed_idx] = 1  # Seed is infected

                infected_ever = {seed_idx}

                # Run discrete-time SIR
                for step in range(steps):
                    new_infections = set()
                    new_recoveries = set()

                    # Process infections
                    infected_nodes = np.where(state == 1)[0]
                    if len(infected_nodes) == 0:
                        break

                    for i in infected_nodes:
                        # Try to infect neighbors
                        for j in G.neighbors(i):
                            if state[j] == 0:  # Susceptible
                                if np.random.random() < beta:
                                    new_infections.add(j)
                                    infected_ever.add(j)

                        # Try to recover
                        if np.random.random() < mu:
                            new_recoveries.add(i)

                    # Update states
                    for j in new_infections:
                        state[j] = 1
                    for i in new_recoveries:
                        state[i] = 2

                total_outbreak += len(infected_ever)

            # Normalize by trials and number of nodes
            results[node_layer] = total_outbreak / (trials * n)

        return results

    # ==================== COLLECTIVE INFLUENCE ====================

    def collective_influence(self, radius=2):
        """
        Compute collective influence (CI_ℓ) for multiplex networks.

        Collective influence identifies influential spreaders by considering
        not just immediate neighbors but also nodes at distance ℓ.

        CI_ℓ(u) = (k_u - 1) * sum_{v in ∂Ball_ℓ(u)} (k_v - 1)

        Args:
            radius: Radius ℓ for the ball boundary (default: 2)

        Returns:
            dict: {(node, layer): collective_influence}

        Note:
            Uses overlapping degree across all layers for each physical node.
        """
        supra_matrix = self._get_supra_adjacency_matrix()
        node_layer_mapping, reverse_mapping = self._get_node_layer_mapping()

        if hasattr(supra_matrix, "toarray"):
            matrix = supra_matrix.toarray()
        else:
            matrix = np.array(supra_matrix)

        # Get degrees
        degrees = self.supra_degree_centrality(weighted=False)

        # Create NetworkX graph for BFS
        G = nx.Graph()
        n = matrix.shape[0]
        for i in range(n):
            for j in range(i + 1, n):
                if matrix[i, j] > 0:
                    G.add_edge(i, j)

        results = {}

        for node_layer, idx in node_layer_mapping.items():
            k_u = degrees.get(node_layer, 0)

            if k_u <= 1:
                results[node_layer] = 0.0
                continue

            # Find nodes at distance exactly radius (boundary of ball)
            try:
                lengths = nx.single_source_shortest_path_length(G, idx, cutoff=radius)
                frontier = [node for node, dist in lengths.items() if dist == radius]
            except nx.NetworkXError:
                frontier = []

            # Compute collective influence
            ci_sum = 0.0
            for v in frontier:
                v_nl = reverse_mapping.get(v)
                if v_nl:
                    k_v = degrees.get(v_nl, 0)
                    ci_sum += max(k_v - 1, 0)

            ci = (k_u - 1) * ci_sum
            results[node_layer] = ci

        return results

    # ==================== LOAD CENTRALITY ====================

    def load_centrality(self):
        """
        Compute load centrality (shortest-path load).

        Load centrality measures the fraction of shortest paths that pass
        through each node, counting all paths (not just unique pairs).

        Load[k] = sum over all (s,t) pairs of [number of shortest paths through k / total shortest paths]

        Returns:
            dict: {(node, layer): load_centrality}

        Note:
            This is similar to betweenness but counts all paths rather than
            normalizing by the number of node pairs.
        """
        supra_matrix = self._get_supra_adjacency_matrix()
        node_layer_mapping, reverse_mapping = self._get_node_layer_mapping()

        if hasattr(supra_matrix, "toarray"):
            matrix = supra_matrix.toarray()
        else:
            matrix = np.array(supra_matrix)

        # Create NetworkX graph
        if self.network.directed:
            G = nx.DiGraph()
        else:
            G = nx.Graph()

        n = matrix.shape[0]
        for i in range(n):
            for j in range(n):
                if matrix[i, j] > 0:
                    edge_length = 1.0 / matrix[i, j]
                    G.add_edge(i, j, weight=edge_length)

        # Initialize load
        load = dict.fromkeys(range(n), 0.0)

        # Compute shortest paths for all pairs
        for source in G.nodes():
            try:
                paths = nx.single_source_shortest_path(G, source)
                for target, path in paths.items():
                    if source != target and len(path) > 2:
                        # Add load to intermediate nodes
                        for node in path[1:-1]:
                            load[node] += 1.0
            except (nx.NetworkXError, KeyError):
                pass

        # Map back to node-layer pairs
        results = {}
        for node_layer, idx in node_layer_mapping.items():
            results[node_layer] = load.get(idx, 0.0)

        return results

    # ==================== FLOW BETWEENNESS ====================

    def flow_betweenness_centrality(self, samples=100):
        """
        Compute flow betweenness based on maximum flow sampling.

        Flow betweenness measures how much flow passes through a node when
        maximizing flow between randomly sampled source-target pairs.

        Args:
            samples: Number of source-target pairs to sample (default: 100)

        Returns:
            dict: {(node, layer): flow_betweenness}

        Note:
            This is a sampling-based approximation of flow betweenness. The
            implementation samples random pairs of supra-graph nodes and computes
            the maximum flow through each intermediate node.

            Unlike classical Freeman flow betweenness which uses a normalization
            factor based on the number of nodes, this implementation returns the
            average flow per sampled pair without additional normalization. For
            multilayer networks, the number of supra-graph nodes (N * L for N
            physical nodes and L layers) affects the raw values.

            For large networks, this sampling approach is more computationally
            feasible than computing exact flow betweenness for all pairs.
        """
        supra_matrix = self._get_supra_adjacency_matrix()
        node_layer_mapping, reverse_mapping = self._get_node_layer_mapping()

        if hasattr(supra_matrix, "toarray"):
            matrix = supra_matrix.toarray()
        else:
            matrix = np.array(supra_matrix)

        # Create NetworkX graph with capacities
        if self.network.directed:
            G = nx.DiGraph()
        else:
            G = nx.Graph()

        n = matrix.shape[0]
        for i in range(n):
            for j in range(n):
                if matrix[i, j] > 0:
                    G.add_edge(i, j, capacity=matrix[i, j])

        # Initialize flow betweenness
        flow_between = dict.fromkeys(range(n), 0.0)

        # Sample source-target pairs
        nodes_list = list(G.nodes())
        if len(nodes_list) < 2:
            results = dict.fromkeys(node_layer_mapping.keys(), 0.0)
            return results

        # Ensure unique nodes for sampling
        nodes_list = list(set(nodes_list))
        if len(nodes_list) < 2:
            results = dict.fromkeys(node_layer_mapping.keys(), 0.0)
            return results

        for _ in range(samples):
            # Sample distinct source and target
            source, target = np.random.choice(nodes_list, size=2, replace=False)

            try:
                # Compute maximum flow
                flow_value, flow_dict = nx.maximum_flow(G, source, target, capacity="capacity")

                # Count flow through each node
                is_directed = G.is_directed()  # Cache result
                for node in G.nodes():
                    if node != source and node != target:
                        # Sum incoming or outgoing flow
                        total_flow = 0.0
                        if node in flow_dict:
                            total_flow += sum(flow_dict[node].values())
                        for pred in G.predecessors(node) if is_directed else G.neighbors(node):
                            if pred in flow_dict:
                                total_flow += flow_dict[pred].get(node, 0)

                        flow_between[node] += total_flow / 2  # Avoid double counting

            except (nx.NetworkXError, ValueError, nx.NetworkXUnbounded):
                # If flow computation fails, skip this pair
                pass

        # Normalize by number of samples
        if samples > 0:
            for idx in flow_between:
                flow_between[idx] /= samples

        # Map back to node-layer pairs
        results = {}
        for node_layer, idx in node_layer_mapping.items():
            results[node_layer] = flow_between.get(idx, 0.0)

        return results

    # ==================== LP-AGGREGATED CENTRALITY ====================

    def lp_aggregated_centrality(self, layer_centralities, p=2, weights=None,
                                   exclude_missing=True):
        """
        Compute Lp-aggregated per-layer centrality.

        Aggregates per-layer centrality values using Lp norm.

        C_i = (sum_{ℓ in L_i} w_ℓ * |c^ℓ[i]|^p)^{1/p}  for p < ∞
        C_i = max_{ℓ in L_i} (w_ℓ * |c^ℓ[i]|)          for p = ∞

        where L_i is the set of layers where node i exists.

        Args:
            layer_centralities: dict of {layer: {node: centrality}} or
                               {(node, layer): centrality}
            p: Lp norm parameter (default: 2). Use float('inf') for L-infinity norm.
            weights: dict of {layer: weight}. If None, uniform weights are used.
            exclude_missing: If True (default), only aggregate over layers where
                           the node exists (has a centrality value). If False,
                           treat nodes absent from a layer as having zero centrality,
                           which may bias scores for nodes with sparse layer
                           participation.

        Returns:
            dict: {node: aggregated_centrality}

        Note:
            This is a framework for aggregating any per-layer centrality measure.
            Input can be degree, PageRank, eigenvector, etc.

            Sparse Layer Participation: When exclude_missing=True (default), nodes
            that only appear in a subset of layers are aggregated only over those
            layers where they exist. This prevents bias against nodes with sparse
            layer participation. When exclude_missing=False, missing layers contribute
            zero to the aggregation, which may penalize nodes that don't appear in
            all layers.
        """
        # Ensure layer matrices are computed to get layer and node info
        self._get_layer_matrices()

        # Parse input format
        if not layer_centralities:
            return {}

        # Check format: nested dict or flat dict with tuples
        first_key = next(iter(layer_centralities.keys()))

        if isinstance(first_key, tuple):
            # Format: {(node, layer): centrality}
            # Convert to nested dict
            nested_centralities = defaultdict(dict)
            for (node, layer), value in layer_centralities.items():
                nested_centralities[layer][node] = value
            layer_centralities = dict(nested_centralities)

        # Get layers
        layers = list(layer_centralities.keys())
        if not layers:
            return {}

        # Get all nodes
        all_nodes = set()
        for layer_dict in layer_centralities.values():
            all_nodes.update(layer_dict.keys())

        # Set uniform weights if not provided
        if weights is None:
            weights = {layer: 1.0 / len(layers) for layer in layers}

        results = {}

        # Helper function to get layers where node exists
        def get_node_layers(node):
            if exclude_missing:
                return [layer for layer in layers
                       if node in layer_centralities[layer]]
            else:
                return layers

        if p == float("inf"):
            # L-infinity norm: maximum
            for node in all_nodes:
                max_val = 0.0
                for layer in get_node_layers(node):
                    val = layer_centralities[layer].get(node, 0)
                    weighted_val = weights.get(layer, 0) * abs(val)
                    max_val = max(max_val, weighted_val)
                results[node] = max_val
        else:
            # Lp norm
            for node in all_nodes:
                node_layers = get_node_layers(node)
                if not node_layers:
                    results[node] = 0.0
                    continue

                lp_sum = 0.0
                for layer in node_layers:
                    val = layer_centralities[layer].get(node, 0)
                    layer_weight = weights.get(layer, 0)
                    weighted_val = layer_weight * abs(val)
                    lp_sum += weighted_val**p

                results[node] = lp_sum ** (1.0 / p)

        return results

    # ==================== AGGREGATION METHODS ====================

    def aggregate_to_node_level(
        self, node_layer_centralities, method="sum", weights=None
    ):
        """
        Aggregate node-layer centralities to node level.

        Args:
            node_layer_centralities: dict with {(node, layer): value} entries
            method: 'sum', 'mean', 'max', 'weighted_sum'
            weights: dict with {layer: weight} for weighted_sum method

        Returns:
            dict: {node: aggregated_value}
        """
        results = defaultdict(list)

        # Group by node
        for (node, layer), value in node_layer_centralities.items():
            results[node].append((layer, value))

        aggregated = {}

        for node, layer_values in results.items():
            values = [value for layer, value in layer_values]

            if method == "sum":
                aggregated[node] = sum(values)
            elif method == "mean":
                aggregated[node] = sum(values) / len(values)
            elif method == "max":
                aggregated[node] = max(values)
            elif method == "weighted_sum":
                if weights is None:
                    raise ValueError("Weights must be provided for weighted_sum method")
                weighted_sum = sum(
                    weights.get(layer, 1) * value for layer, value in layer_values
                )
                aggregated[node] = weighted_sum
            else:
                raise ValueError(f"Unknown aggregation method: {method}")

        return aggregated


def compute_all_centralities(network, include_path_based=False, include_advanced=False,
                           include_extended=False, preset=None, wf_improved=True,
                           closeness_variant="standard"):
    """
    Compute all available centrality measures for a multilayer network.

    Args:
        network: py3plex multi_layer_network object
        include_path_based: Whether to include computationally expensive path-based measures
                           (betweenness, closeness). Default: False
        include_advanced: Whether to include advanced measures (HITS, current-flow,
                         communicability, k-core). Default: False
        include_extended: Whether to include extended measures (information, accessibility,
                         percolation, spreading, collective influence, load, flow betweenness,
                         harmonic, bridging, local efficiency). Default: False
        preset: Convenience parameter to set all inclusion flags at once. Options:
                - 'basic': Only degree and eigenvector-based measures (default behavior)
                - 'standard': Includes path-based measures
                - 'advanced': Includes path-based and advanced measures
                - 'all': Includes all measures (path-based, advanced, and extended)
                - None: Use individual flags (default)
        wf_improved: If True, use Wasserman-Faust improved scaling for closeness
                    centrality in disconnected graphs. Default: True. Only used when
                    closeness_variant='standard'.
        closeness_variant: Variant of closeness centrality to use. Options:
                          - 'standard': Classic closeness (reciprocal of sum of distances).
                            Uses Wasserman-Faust scaling if wf_improved=True.
                          - 'harmonic': Harmonic closeness (sum of reciprocal distances).
                            Recommended for disconnected multilayer networks.
                          - 'auto': Automatically selects 'harmonic' if the network has
                            disconnected components, otherwise uses 'standard'.
                          Default: 'standard' for backward compatibility.

    Returns:
        dict: Dictionary containing all computed centrality measures with keys:
              - Degree-based: "layer_degree", "layer_strength", "supra_degree",
                "supra_strength", "overlapping_degree", "overlapping_strength",
                "participation_coefficient", "participation_coefficient_strength"
              - Eigenvector-based: "multiplex_eigenvector", "eigenvector_versatility",
                "katz_bonacich", "pagerank"
              - Path-based (if include_path_based=True): "closeness", "betweenness"
              - Advanced (if include_advanced=True): "hits", "current_flow_closeness",
                "current_flow_betweenness", "subgraph_centrality",
                "total_communicability", "multiplex_k_core"
              - Extended (if include_extended=True): "information", "communicability_betweenness",
                "accessibility", "harmonic_closeness", "local_efficiency", "edge_betweenness",
                "bridging", "percolation", "spreading", "collective_influence", "load",
                "flow_betweenness"

    Note:
        Path-based, advanced, and extended measures are computationally expensive for large
        networks. Use flags or presets to control which measures are computed.

        For disconnected multilayer graphs (e.g., networks without inter-layer coupling,
        or with isolated components), use closeness_variant='harmonic' or 'auto' to
        get mathematically consistent closeness values.

    Examples:
        >>> # Compute only basic measures (fast)
        >>> results = compute_all_centralities(network)

        >>> # Use preset for standard analysis
        >>> results = compute_all_centralities(network, preset='standard')

        >>> # Compute everything
        >>> results = compute_all_centralities(network, preset='all')

        >>> # Fine-grained control
        >>> results = compute_all_centralities(
        ...     network,
        ...     include_path_based=True,
        ...     include_extended=True
        ... )

        >>> # For disconnected multilayer networks, use harmonic closeness
        >>> results = compute_all_centralities(
        ...     network,
        ...     include_path_based=True,
        ...     closeness_variant='harmonic'
        ... )
    """
    # Handle preset parameter
    if preset is not None:
        preset = preset.lower()
        if preset == 'basic':
            include_path_based = False
            include_advanced = False
            include_extended = False
        elif preset == 'standard':
            include_path_based = True
            include_advanced = False
            include_extended = False
        elif preset == 'advanced':
            include_path_based = True
            include_advanced = True
            include_extended = False
        elif preset == 'all':
            include_path_based = True
            include_advanced = True
            include_extended = True
        else:
            raise ValueError(
                f"Unknown preset '{preset}'. "
                "Valid options: 'basic', 'standard', 'advanced', 'all'"
            )

    calc = MultilayerCentrality(network)
    results = {}

    # Degree-based measures
    results["layer_degree"] = calc.layer_degree_centrality(weighted=False)
    results["layer_strength"] = calc.layer_degree_centrality(weighted=True)
    results["supra_degree"] = calc.supra_degree_centrality(weighted=False)
    results["supra_strength"] = calc.supra_degree_centrality(weighted=True)
    results["overlapping_degree"] = calc.overlapping_degree_centrality(weighted=False)
    results["overlapping_strength"] = calc.overlapping_degree_centrality(weighted=True)
    results["participation_coefficient"] = calc.participation_coefficient(
        weighted=False
    )
    results["participation_coefficient_strength"] = calc.participation_coefficient(
        weighted=True
    )

    # Eigenvector-based measures
    results["multiplex_eigenvector"] = calc.multiplex_eigenvector_centrality()
    results["eigenvector_versatility"] = calc.multiplex_eigenvector_versatility()
    results["katz_bonacich"] = calc.katz_bonacich_centrality()
    results["pagerank"] = calc.pagerank_centrality()

    # Path-based measures (optional due to computational cost)
    if include_path_based:
        results["closeness"] = calc.multilayer_closeness_centrality(
            wf_improved=wf_improved, variant=closeness_variant
        )
        results["betweenness"] = calc.multilayer_betweenness_centrality()

    # Advanced measures (optional due to computational cost)
    if include_advanced:
        results["hits"] = calc.hits_centrality()
        results["current_flow_closeness"] = calc.current_flow_closeness_centrality()
        results["current_flow_betweenness"] = calc.current_flow_betweenness_centrality()
        results["subgraph_centrality"] = calc.subgraph_centrality()
        results["total_communicability"] = calc.total_communicability()
        results["multiplex_k_core"] = calc.multiplex_k_core()

    # Extended measures (optional due to computational cost)
    if include_extended:
        results["information"] = calc.information_centrality()
        results["communicability_betweenness"] = calc.communicability_betweenness_centrality()
        results["accessibility"] = calc.accessibility_centrality()
        results["harmonic_closeness"] = calc.harmonic_closeness_centrality()
        results["local_efficiency"] = calc.local_efficiency_centrality()
        results["edge_betweenness"] = calc.edge_betweenness_centrality()
        results["bridging"] = calc.bridging_centrality()
        results["percolation"] = calc.percolation_centrality()
        results["spreading"] = calc.spreading_centrality()
        results["collective_influence"] = calc.collective_influence()
        results["load"] = calc.load_centrality()
        results["flow_betweenness"] = calc.flow_betweenness_centrality()

    return results


# Export public API including supra matrix function centralities
__all__ = [
    "MultilayerCentrality",
    "compute_all_centralities",
    "communicability_centrality",
    "katz_centrality",
]
