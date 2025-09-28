#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multilayer/Multiplex Network Centrality Measures

This module implements various centrality measures for multilayer and multiplex networks,
following standard definitions from multilayer network analysis literature.

Authors: py3plex contributors
Date: 2025
"""

import numpy as np
import networkx as nx
from collections import defaultdict
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh, eigs
from scipy.linalg import norm
from scipy.sparse import diags, identity


class MultilayerCentrality:
    """
    Class for computing centrality measures on multilayer networks.
    
    This class provides implementations of various centrality measures 
    specifically designed for multilayer/multiplex networks, including
    degree-based, eigenvector-based, and path-based measures.
    """
    
    def __init__(self, network):
        """
        Initialize the centrality calculator.
        
        Args:
            network: py3plex multi_layer_network object
        """
        self.network = network
        self._supra_matrix = None
        self._layer_matrices = None
        self._node_layer_mapping = None
        
    def _get_supra_adjacency_matrix(self):
        """Get the supra-adjacency matrix."""
        if self._supra_matrix is None:
            self._supra_matrix = self.network.get_supra_adjacency_matrix()
        return self._supra_matrix
    
    def _get_layer_matrices(self):
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
            
            layers = sorted(list(layers))
            nodes = sorted(list(nodes))
            
            # Create mapping from node to index
            node_to_idx = {node: i for i, node in enumerate(nodes)}
            
            # Build layer matrices
            for layer in layers:
                n_nodes = len(nodes)
                matrix = np.zeros((n_nodes, n_nodes))
                
                for edge in self.network.get_edges(data=True):
                    (n1, l1), (n2, l2) = edge[0], edge[1]
                    if l1 == layer and l2 == layer:  # Intralayer edge
                        i, j = node_to_idx[n1], node_to_idx[n2]
                        weight = edge[2].get('weight', 1) if len(edge) > 2 else 1
                        matrix[i, j] = weight
                        if not self.network.directed:
                            matrix[j, i] = weight
                
                self._layer_matrices[layer] = matrix
            
            self._nodes = nodes
            self._layers = layers
            self._node_to_idx = node_to_idx
            
        return self._layer_matrices
    
    def _get_node_layer_mapping(self):
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
    
    def layer_degree_centrality(self, layer=None, weighted=False, direction='out'):
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
        
        results = {}
        
        for layer_name in layers_to_process:
            if layer_name not in layer_matrices:
                continue
                
            matrix = layer_matrices[layer_name]
            
            if weighted:
                if self.network.directed:
                    if direction == 'out':
                        centralities = np.sum(matrix, axis=1)
                    elif direction == 'in':
                        centralities = np.sum(matrix, axis=0)
                    else:  # both
                        centralities = np.sum(matrix, axis=1) + np.sum(matrix, axis=0)
                else:
                    centralities = np.sum(matrix, axis=1)
            else:
                # Convert to binary matrix for degree calculation
                binary_matrix = (matrix > 0).astype(int)
                if self.network.directed:
                    if direction == 'out':
                        centralities = np.sum(binary_matrix, axis=1)
                    elif direction == 'in':
                        centralities = np.sum(binary_matrix, axis=0)
                    else:  # both
                        centralities = np.sum(binary_matrix, axis=1) + np.sum(binary_matrix, axis=0)
                else:
                    centralities = np.sum(binary_matrix, axis=1)
            
            # Map back to node names
            for i, node in enumerate(self._nodes):
                if layer is not None:
                    results[node] = centralities[i]
                else:
                    results[(node, layer_name)] = centralities[i]
        
        return results
    
    def supra_degree_centrality(self, weighted=False):
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
        
        if hasattr(supra_matrix, 'toarray'):
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
    
    def overlapping_degree_centrality(self, weighted=False):
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
        results = defaultdict(float)
        
        for (node, layer), centrality in layer_centralities.items():
            results[node] += centrality
        
        return dict(results)
    
    def participation_coefficient(self, weighted=False):
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
                sum_squared_ratios += ratio ** 2
            
            results[node] = 1.0 - sum_squared_ratios
        
        return results
    
    # ==================== EIGENVECTOR-TYPE MEASURES ====================
    
    def multiplex_eigenvector_centrality(self, max_iter=1000, tol=1e-6):
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
        if hasattr(supra_matrix, 'toarray'):
            matrix = supra_matrix
        else:
            matrix = sp.csr_matrix(supra_matrix)
        
        try:
            # Compute the principal eigenvector
            eigenval, eigenvec = eigs(matrix, k=1, which='LM', maxiter=max_iter, tol=tol)
            eigenvec = np.real(eigenvec.flatten())
            
            # Normalize to make values positive
            if np.sum(eigenvec) < 0:
                eigenvec = -eigenvec
            
            # Normalize
            eigenvec = eigenvec / np.linalg.norm(eigenvec)
            
        except:
            # Fallback to power iteration
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
    
    def multiplex_eigenvector_versatility(self, max_iter=1000, tol=1e-6):
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
        results = defaultdict(float)
        
        for (node, layer), centrality in node_layer_centralities.items():
            results[node] += centrality
        
        return dict(results)
    
    def katz_bonacich_centrality(self, alpha=0.1, beta=None):
        """
        Compute Katz-Bonacich centrality on the supra-graph.
        
        z = Σ_{t=0}^∞ α^t M^t b = (I - αM)^{-1} b
        
        Args:
            alpha: Attenuation parameter (should be < 1/ρ(M)).
            beta: Exogenous preference vector. If None, uses vector of ones.
            
        Returns:
            dict: {(node, layer): centrality_value}
        """
        supra_matrix = self._get_supra_adjacency_matrix()
        node_layer_mapping, reverse_mapping = self._get_node_layer_mapping()
        
        if hasattr(supra_matrix, 'toarray'):
            matrix = sp.csr_matrix(supra_matrix)
        else:
            matrix = supra_matrix
        
        n = matrix.shape[0]
        
        if beta is None:
            beta = np.ones(n)
        else:
            beta = np.array(beta)
        
        # Compute (I - αM)^{-1} b
        identity_matrix = identity(n, format='csr')
        try:
            centralities = sp.linalg.spsolve(identity_matrix - alpha * matrix, beta)
        except:
            # Fallback: use series approximation
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
        representing the multilayer network.
        
        Args:
            damping: Damping parameter (typically 0.85).
            max_iter: Maximum number of iterations.
            tol: Tolerance for convergence.
            
        Returns:
            dict: {(node, layer): centrality_value}
        """
        supra_matrix = self._get_supra_adjacency_matrix()
        node_layer_mapping, reverse_mapping = self._get_node_layer_mapping()
        
        if hasattr(supra_matrix, 'toarray'):
            matrix = supra_matrix.toarray()
        else:
            matrix = np.array(supra_matrix)
        
        n = matrix.shape[0]
        
        # Create row-stochastic transition matrix
        row_sums = np.sum(matrix, axis=1)
        # Handle nodes with no outgoing edges
        row_sums[row_sums == 0] = 1
        transition_matrix = matrix / row_sums[:, np.newaxis]
        
        # Initialize PageRank vector
        pagerank = np.ones(n) / n
        
        # Power iteration
        for _ in range(max_iter):
            new_pagerank = (1 - damping) / n + damping * transition_matrix.T.dot(pagerank)
            
            if np.linalg.norm(pagerank - new_pagerank) < tol:
                break
            pagerank = new_pagerank
        
        results = {}
        for node_layer, idx in node_layer_mapping.items():
            results[node_layer] = pagerank[idx]
        
        return results
    
    # ==================== AGGREGATION METHODS ====================
    
    def aggregate_to_node_level(self, node_layer_centralities, method='sum', weights=None):
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
            
            if method == 'sum':
                aggregated[node] = sum(values)
            elif method == 'mean':
                aggregated[node] = sum(values) / len(values)
            elif method == 'max':
                aggregated[node] = max(values)
            elif method == 'weighted_sum':
                if weights is None:
                    raise ValueError("Weights must be provided for weighted_sum method")
                weighted_sum = sum(weights.get(layer, 1) * value 
                                 for layer, value in layer_values)
                aggregated[node] = weighted_sum
            else:
                raise ValueError(f"Unknown aggregation method: {method}")
        
        return aggregated


def compute_all_centralities(network, include_path_based=False):
    """
    Compute all available centrality measures for a multilayer network.
    
    Args:
        network: py3plex multi_layer_network object
        include_path_based: Whether to include computationally expensive path-based measures
        
    Returns:
        dict: Dictionary containing all computed centrality measures
    """
    calc = MultilayerCentrality(network)
    results = {}
    
    # Degree-based measures
    results['layer_degree'] = calc.layer_degree_centrality(weighted=False)
    results['layer_strength'] = calc.layer_degree_centrality(weighted=True)
    results['supra_degree'] = calc.supra_degree_centrality(weighted=False)
    results['supra_strength'] = calc.supra_degree_centrality(weighted=True)
    results['overlapping_degree'] = calc.overlapping_degree_centrality(weighted=False)
    results['overlapping_strength'] = calc.overlapping_degree_centrality(weighted=True)
    results['participation_coefficient'] = calc.participation_coefficient(weighted=False)
    results['participation_coefficient_strength'] = calc.participation_coefficient(weighted=True)
    
    # Eigenvector-based measures
    results['multiplex_eigenvector'] = calc.multiplex_eigenvector_centrality()
    results['eigenvector_versatility'] = calc.multiplex_eigenvector_versatility()
    results['katz_bonacich'] = calc.katz_bonacich_centrality()
    results['pagerank'] = calc.pagerank_centrality()
    
    return results