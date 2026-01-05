"""Distribution over community partitions with uncertainty quantification.

This module provides types and utilities for representing and analyzing
distributional community detection results - a collection of partitions
obtained through resampling or algorithm stochasticity, along with
summary statistics and co-association matrices.

Key concepts:
- **Co-association matrix**: P(node_i and node_j in same community)
- **Consensus partition**: Representative partition (e.g., medoid)
- **Node confidence**: Per-node stability measures
- **Label alignment**: Hungarian matching for membership probabilities

Examples
--------
>>> from py3plex.algorithms.community_detection import multilayer_louvain_distribution
>>> from py3plex.core import multinet
>>> 
>>> net = multinet.multi_layer_network(directed=False)
>>> net.add_edges([
...     ['A', 'L1', 'B', 'L1', 1],
...     ['B', 'L1', 'C', 'L1', 1],
... ], input_type='list')
>>> 
>>> dist = multilayer_louvain_distribution(net, n_runs=100, seed=42)
>>> consensus = dist.consensus_partition()
>>> confidence = dist.node_confidence()
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Union
import warnings

import numpy as np
from scipy.optimize import linear_sum_assignment

from py3plex.exceptions import AlgorithmError


class CommunityDistribution:
    """Distribution over community partitions with lazy evaluation.
    
    Represents a collection of community detection runs, providing methods
    to compute summary statistics like co-association matrices, consensus
    partitions, and node-level confidence metrics.
    
    All expensive computations (co-association, consensus, alignment) are
    performed lazily and cached for efficiency.
    
    Parameters
    ----------
    partitions : list of np.ndarray
        List of partition arrays. Each array has shape (n_nodes,) with
        integer community labels. All arrays must have the same length
        and correspond to the same node ordering.
    nodes : list
        Ordered list of node identifiers corresponding to partition indices.
    weights : np.ndarray, optional
        Per-partition weights (e.g., modularity scores), shape (n_partitions,).
        If None, all partitions are weighted equally.
    meta : dict, optional
        Metadata about the distribution generation:
        - method: Algorithm name (e.g., "multilayer_louvain")
        - n_runs: Number of partitions
        - resampling: Resampling strategy ("seed", "bootstrap", "perturbation")
        - gamma: Resolution parameter(s) used
        - seed: Base random seed
        - n_jobs: Number of parallel jobs
        - layers: List of layer names (for multilayer networks)
        
    Attributes
    ----------
    n_nodes : int
        Number of nodes in the network.
    n_partitions : int
        Number of partitions in the distribution.
    
    Examples
    --------
    >>> partitions = [
    ...     np.array([0, 0, 1]),
    ...     np.array([0, 0, 1]),
    ...     np.array([0, 1, 1]),
    ... ]
    >>> dist = CommunityDistribution(
    ...     partitions=partitions,
    ...     nodes=['A', 'B', 'C'],
    ...     meta={'method': 'louvain', 'n_runs': 3}
    ... )
    >>> dist.n_nodes
    3
    >>> coassoc = dist.coassociation(mode='dense')
    >>> coassoc.shape
    (3, 3)
    """
    
    def __init__(
        self,
        partitions: List[np.ndarray],
        nodes: List[Any],
        weights: Optional[np.ndarray] = None,
        meta: Optional[Dict[str, Any]] = None,
    ):
        """Initialize CommunityDistribution."""
        # Validate inputs
        if not partitions:
            raise AlgorithmError(
                "Cannot create CommunityDistribution with empty partition list",
                suggestions=["Provide at least one partition"]
            )
        
        # Convert partitions to arrays and validate
        self._partitions = []
        n_nodes = len(nodes)
        
        for i, partition in enumerate(partitions):
            p = np.asarray(partition, dtype=np.int32)
            if len(p) != n_nodes:
                raise AlgorithmError(
                    f"Partition {i} has length {len(p)}, expected {n_nodes}",
                    suggestions=["Ensure all partitions correspond to the same node set"]
                )
            self._partitions.append(p)
        
        self._nodes = list(nodes)
        self._node_to_idx = {node: i for i, node in enumerate(nodes)}
        
        # Validate or create weights
        if weights is not None:
            self._weights = np.asarray(weights, dtype=float)
            if len(self._weights) != len(partitions):
                raise AlgorithmError(
                    f"Weights length {len(weights)} != partitions length {len(partitions)}",
                    suggestions=["Provide one weight per partition or set weights=None"]
                )
            # Normalize weights
            if np.sum(self._weights) > 0:
                self._weights = self._weights / np.sum(self._weights)
            else:
                self._weights = np.ones(len(partitions)) / len(partitions)
        else:
            # Uniform weights
            self._weights = np.ones(len(partitions)) / len(partitions)
        
        self.meta = meta or {}
        
        # Lazy caches
        self._coassoc_dense: Optional[np.ndarray] = None
        self._coassoc_sparse: Optional[Dict[int, List[Tuple[int, float]]]] = None
        self._consensus: Optional[np.ndarray] = None
        self._aligned_partitions: Optional[List[np.ndarray]] = None
        self._membership_probs: Optional[np.ndarray] = None
    
    @property
    def n_nodes(self) -> int:
        """Number of nodes."""
        return len(self._nodes)
    
    @property
    def n_partitions(self) -> int:
        """Number of partitions in the distribution."""
        return len(self._partitions)
    
    @property
    def nodes(self) -> List[Any]:
        """Ordered list of node identifiers."""
        return self._nodes.copy()
    
    @property
    def partitions(self) -> List[np.ndarray]:
        """List of partition arrays (copies for safety)."""
        return [p.copy() for p in self._partitions]
    
    @property
    def weights(self) -> np.ndarray:
        """Normalized partition weights."""
        return self._weights.copy()
    
    def coassociation(
        self,
        mode: str = "auto",
        topk: int = 50,
        sample_pairs: Optional[int] = None,
    ) -> Union[np.ndarray, Dict[int, List[Tuple[int, float]]]]:
        """Compute co-association matrix: P(node_i and node_j in same community).
        
        The co-association matrix measures how often each pair of nodes appears
        in the same community across all partitions. This is label-permutation
        invariant (does not require alignment).
        
        Parameters
        ----------
        mode : {'auto', 'dense', 'sparse'}
            Output mode:
            - 'dense': Return full n×n numpy array
            - 'sparse': Return dict mapping node_idx to list of (neighbor_idx, prob)
            - 'auto': Choose based on n_nodes (sparse if > 2000)
        topk : int, default=50
            For sparse mode, keep only top-k highest co-association neighbors
            per node. Set to -1 to keep all non-zero entries.
        sample_pairs : int, optional
            For very large graphs, approximate co-association by sampling this
            many node pairs uniformly. If None, compute exactly.
        
        Returns
        -------
        np.ndarray or dict
            If mode='dense': Array of shape (n_nodes, n_nodes) with co-assoc probs.
            If mode='sparse': Dict mapping node_idx to list of (neighbor_idx, prob).
        
        Examples
        --------
        >>> dist = CommunityDistribution([...], nodes=[...])
        >>> coassoc_dense = dist.coassociation(mode='dense')
        >>> coassoc_dense[0, 1]  # P(node 0 and 1 in same community)
        0.75
        >>> 
        >>> coassoc_sparse = dist.coassociation(mode='sparse', topk=10)
        >>> coassoc_sparse[0]  # Top 10 most co-associated nodes with node 0
        [(2, 0.9), (5, 0.85), ...]
        """
        # Resolve auto mode
        if mode == "auto":
            mode = "sparse" if self.n_nodes > 2000 else "dense"
        
        if mode == "dense":
            if self._coassoc_dense is None:
                self._coassoc_dense = self._compute_coassoc_dense(sample_pairs)
            return self._coassoc_dense.copy()
        
        elif mode == "sparse":
            if self._coassoc_sparse is None:
                # Compute from dense if already cached and small enough
                if self._coassoc_dense is not None:
                    self._coassoc_sparse = self._dense_to_sparse(
                        self._coassoc_dense, topk
                    )
                else:
                    self._coassoc_sparse = self._compute_coassoc_sparse(
                        topk, sample_pairs
                    )
            return {k: list(v) for k, v in self._coassoc_sparse.items()}
        
        else:
            raise AlgorithmError(
                f"Invalid coassociation mode: {mode}",
                suggestions=["Use mode='dense', 'sparse', or 'auto'"]
            )
    
    def _compute_coassoc_dense(
        self,
        sample_pairs: Optional[int] = None
    ) -> np.ndarray:
        """Compute dense co-association matrix."""
        n = self.n_nodes
        coassoc = np.zeros((n, n), dtype=float)
        
        if sample_pairs is not None and sample_pairs < n * (n - 1) // 2:
            # Approximate via sampling
            rng = np.random.default_rng(self.meta.get('seed', None))
            pairs = set()
            while len(pairs) < sample_pairs:
                i, j = rng.integers(0, n, size=2)
                if i != j:
                    pairs.add((min(i, j), max(i, j)))
            
            for i, j in pairs:
                same_count = sum(
                    w for p, w in zip(self._partitions, self._weights)
                    if p[i] == p[j]
                )
                coassoc[i, j] = same_count
                coassoc[j, i] = same_count
            
            # Diagonal is always 1
            np.fill_diagonal(coassoc, 1.0)
        else:
            # Exact computation
            for partition, weight in zip(self._partitions, self._weights):
                # Find pairs in same community
                for i in range(n):
                    for j in range(i, n):
                        if partition[i] == partition[j]:
                            coassoc[i, j] += weight
                            if i != j:
                                coassoc[j, i] += weight
        
        return coassoc
    
    def _compute_coassoc_sparse(
        self,
        topk: int,
        sample_pairs: Optional[int] = None
    ) -> Dict[int, List[Tuple[int, float]]]:
        """Compute sparse co-association representation."""
        # For sparse mode, compute dense first then convert
        # (More efficient than maintaining sparse during accumulation)
        dense = self._compute_coassoc_dense(sample_pairs)
        return self._dense_to_sparse(dense, topk)
    
    def _dense_to_sparse(
        self,
        dense: np.ndarray,
        topk: int
    ) -> Dict[int, List[Tuple[int, float]]]:
        """Convert dense co-association to sparse top-k format."""
        sparse = {}
        n = dense.shape[0]
        
        for i in range(n):
            # Get neighbors (exclude self)
            neighbors = [(j, dense[i, j]) for j in range(n) if i != j]
            
            # Sort by co-association probability (descending)
            neighbors.sort(key=lambda x: x[1], reverse=True)
            
            # Keep top-k or all if topk == -1
            if topk > 0:
                neighbors = neighbors[:topk]
            
            sparse[i] = neighbors
        
        return sparse
    
    def consensus_partition(
        self,
        method: str = "medoid",
        **kwargs
    ) -> np.ndarray:
        """Compute consensus partition from the distribution.
        
        The consensus partition is a representative partition that best
        summarizes the distribution. Multiple methods are supported.
        
        Parameters
        ----------
        method : {'medoid', 'cluster_coassoc'}
            Consensus method:
            - 'medoid': Choose partition with minimum VI distance to all others
              (always available, parameter-free)
            - 'cluster_coassoc': Cluster the co-association matrix using
              spectral clustering or hierarchical clustering (requires scipy)
        **kwargs
            Additional arguments for the consensus method:
            - metric : str, for 'medoid' method ('vi' or 'pair_agreement')
            - n_clusters : int, for 'cluster_coassoc' method
        
        Returns
        -------
        np.ndarray
            Consensus partition array, shape (n_nodes,)
        
        Examples
        --------
        >>> dist = CommunityDistribution([...], nodes=[...])
        >>> consensus = dist.consensus_partition(method='medoid')
        >>> consensus.shape
        (100,)
        """
        if self._consensus is not None:
            return self._consensus.copy()
        
        if method == "medoid":
            metric = kwargs.get('metric', 'vi')
            medoid_idx = self._medoid_partition_index(metric)
            self._consensus = self._partitions[medoid_idx].copy()
        
        elif method == "cluster_coassoc":
            # Cluster co-association matrix
            n_clusters = kwargs.get('n_clusters', None)
            if n_clusters is None:
                # Use mode of number of communities across partitions
                n_comms = [len(np.unique(p)) for p in self._partitions]
                n_clusters = int(np.median(n_comms))
            
            coassoc = self.coassociation(mode='dense')
            self._consensus = self._cluster_coassoc_matrix(coassoc, n_clusters)
        
        else:
            raise AlgorithmError(
                f"Unknown consensus method: {method}",
                algorithm_name=method,
                valid_algorithms=['medoid', 'cluster_coassoc'],
            )
        
        return self._consensus.copy()
    
    def _medoid_partition_index(self, metric: str = 'vi') -> int:
        """Find index of medoid partition (minimal average distance)."""
        n_partitions = len(self._partitions)
        
        if metric == 'vi':
            # Variation of information
            distances = np.zeros((n_partitions, n_partitions))
            for i in range(n_partitions):
                for j in range(i + 1, n_partitions):
                    d = self._partition_vi_distance(
                        self._partitions[i],
                        self._partitions[j]
                    )
                    distances[i, j] = d
                    distances[j, i] = d
        
        elif metric == 'pair_agreement':
            # Pair agreement (fraction of node pairs with same relationship)
            distances = np.zeros((n_partitions, n_partitions))
            for i in range(n_partitions):
                for j in range(i + 1, n_partitions):
                    d = 1.0 - self._partition_pair_agreement(
                        self._partitions[i],
                        self._partitions[j]
                    )
                    distances[i, j] = d
                    distances[j, i] = d
        
        else:
            raise AlgorithmError(
                f"Unknown partition distance metric: {metric}",
                suggestions=["Use 'vi' or 'pair_agreement'"]
            )
        
        # Find medoid (partition with minimum average distance)
        avg_distances = distances.mean(axis=1)
        medoid_idx = int(np.argmin(avg_distances))
        
        return medoid_idx
    
    def _partition_vi_distance(self, p1: np.ndarray, p2: np.ndarray) -> float:
        """Compute variation of information between two partitions."""
        # VI = H(p1) + H(p2) - 2*I(p1, p2)
        # where H is entropy and I is mutual information
        n = len(p1)
        
        # Build contingency table
        c1_max = p1.max() + 1
        c2_max = p2.max() + 1
        contingency = np.zeros((c1_max, c2_max), dtype=int)
        
        for i in range(n):
            contingency[p1[i], p2[i]] += 1
        
        # Compute entropies and mutual information
        p_i = contingency.sum(axis=1) / n  # P(C1=i)
        p_j = contingency.sum(axis=0) / n  # P(C2=j)
        p_ij = contingency / n  # P(C1=i, C2=j)
        
        # H(p1) = -sum_i p_i log(p_i)
        h1 = -np.sum(p_i[p_i > 0] * np.log(p_i[p_i > 0]))
        
        # H(p2) = -sum_j p_j log(p_j)
        h2 = -np.sum(p_j[p_j > 0] * np.log(p_j[p_j > 0]))
        
        # I(p1, p2) = sum_ij p_ij log(p_ij / (p_i * p_j))
        mi = 0.0
        for i in range(c1_max):
            for j in range(c2_max):
                if p_ij[i, j] > 0 and p_i[i] > 0 and p_j[j] > 0:
                    mi += p_ij[i, j] * np.log(p_ij[i, j] / (p_i[i] * p_j[j]))
        
        vi = h1 + h2 - 2 * mi
        return float(vi)
    
    def _partition_pair_agreement(
        self,
        p1: np.ndarray,
        p2: np.ndarray
    ) -> float:
        """Compute pair agreement between two partitions."""
        # Fraction of node pairs with same relationship in both partitions
        n = len(p1)
        if n < 2:
            return 1.0
        
        agreement = 0
        total = 0
        
        # Sample pairs to avoid O(n^2) for large n
        if n > 1000:
            rng = np.random.default_rng(0)
            sample_size = min(10000, n * (n - 1) // 2)
            pairs = []
            seen = set()
            while len(pairs) < sample_size:
                i, j = rng.integers(0, n, size=2)
                if i != j:
                    key = (min(i, j), max(i, j))
                    if key not in seen:
                        pairs.append(key)
                        seen.add(key)
            
            for i, j in pairs:
                same_in_p1 = (p1[i] == p1[j])
                same_in_p2 = (p2[i] == p2[j])
                if same_in_p1 == same_in_p2:
                    agreement += 1
                total += 1
        else:
            # Exact computation for small n
            for i in range(n):
                for j in range(i + 1, n):
                    same_in_p1 = (p1[i] == p1[j])
                    same_in_p2 = (p2[i] == p2[j])
                    if same_in_p1 == same_in_p2:
                        agreement += 1
                    total += 1
        
        return agreement / total if total > 0 else 1.0
    
    def _cluster_coassoc_matrix(
        self,
        coassoc: np.ndarray,
        n_clusters: int
    ) -> np.ndarray:
        """Cluster co-association matrix to get consensus partition."""
        try:
            from sklearn.cluster import SpectralClustering
            
            # Convert co-association to distance (1 - similarity)
            affinity = coassoc
            
            clustering = SpectralClustering(
                n_clusters=n_clusters,
                affinity='precomputed',
                random_state=self.meta.get('seed', None)
            )
            labels = clustering.fit_predict(affinity)
            return labels.astype(np.int32)
        
        except ImportError:
            # Fallback: use hierarchical clustering from scipy
            try:
                from scipy.cluster.hierarchy import fcluster, linkage
                
                # Convert to distance matrix
                distance = 1.0 - coassoc
                np.fill_diagonal(distance, 0.0)
                
                # Hierarchical clustering
                # Convert to condensed distance matrix
                from scipy.spatial.distance import squareform
                condensed = squareform(distance, checks=False)
                
                linkage_matrix = linkage(condensed, method='average')
                labels = fcluster(linkage_matrix, n_clusters, criterion='maxclust')
                
                return (labels - 1).astype(np.int32)  # Zero-indexed
            
            except ImportError:
                warnings.warn(
                    "Neither sklearn nor scipy.cluster available. "
                    "Falling back to medoid consensus.",
                    stacklevel=2
                )
                medoid_idx = self._medoid_partition_index('vi')
                return self._partitions[medoid_idx].copy()
    
    def node_confidence(
        self,
        consensus: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """Compute per-node confidence scores.
        
        Confidence measures how consistently a node is assigned to its
        consensus community across all partitions. Computed as the mean
        co-association with other nodes in the same consensus community.
        
        Parameters
        ----------
        consensus : np.ndarray, optional
            Consensus partition to use. If None, computed automatically.
        
        Returns
        -------
        np.ndarray
            Confidence scores, shape (n_nodes,). Values in [0, 1] where
            1 = always in same community, 0 = never consistent.
        
        Examples
        --------
        >>> dist = CommunityDistribution([...], nodes=[...])
        >>> confidence = dist.node_confidence()
        >>> low_conf_nodes = np.where(confidence < 0.7)[0]
        """
        if consensus is None:
            consensus = self.consensus_partition()
        
        coassoc = self.coassociation(mode='dense')
        confidence = np.zeros(self.n_nodes)
        
        for i in range(self.n_nodes):
            # Find nodes in same community as i
            same_comm = np.where(consensus == consensus[i])[0]
            
            # Exclude self
            same_comm = same_comm[same_comm != i]
            
            if len(same_comm) > 0:
                # Mean co-association with community members
                confidence[i] = coassoc[i, same_comm].mean()
            else:
                # Singleton community - high confidence by definition
                confidence[i] = 1.0
        
        return confidence
    
    def node_entropy(
        self,
        aligned: bool = False,
        base: float = 2.0
    ) -> np.ndarray:
        """Compute per-node entropy across partitions.
        
        Entropy measures the uncertainty in community assignment. Higher
        entropy indicates more disagreement across partitions.
        
        Parameters
        ----------
        aligned : bool, default=False
            If True, use aligned membership probabilities (requires alignment).
            If False, compute proxy entropy from co-association.
        base : float, default=2.0
            Logarithm base for entropy (2.0 = bits, e = nats).
        
        Returns
        -------
        np.ndarray
            Entropy values, shape (n_nodes,). Higher = more uncertain.
        
        Examples
        --------
        >>> dist = CommunityDistribution([...], nodes=[...])
        >>> entropy = dist.node_entropy()
        >>> uncertain_nodes = np.where(entropy > 1.5)[0]
        """
        if aligned and self._membership_probs is not None:
            # True entropy from membership probabilities
            probs = self._membership_probs
            entropy = np.zeros(self.n_nodes)
            
            for i in range(self.n_nodes):
                p = probs[i]
                p = p[p > 0]  # Remove zeros
                entropy[i] = -np.sum(p * np.log(p) / np.log(base))
            
            return entropy
        
        else:
            # Proxy entropy from co-association variance
            coassoc = self.coassociation(mode='dense')
            
            # For each node, compute entropy based on co-assoc distribution
            entropy = np.zeros(self.n_nodes)
            
            for i in range(self.n_nodes):
                # Get co-association with all other nodes
                co_i = coassoc[i, :]
                
                # Exclude self (always 1.0)
                co_i = co_i[np.arange(len(co_i)) != i]
                
                if len(co_i) > 0:
                    # Proxy: higher variance in co-assoc = higher entropy
                    # Normalize to [0, log(n_nodes)]
                    variance = np.var(co_i)
                    # Map variance [0, 0.25] to entropy-like score
                    entropy[i] = np.sqrt(variance) * np.log(self.n_nodes) / np.log(base)
                else:
                    entropy[i] = 0.0
            
            return entropy
    
    def node_margin(
        self,
        consensus: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """Compute per-node margin (confidence gap).
        
        Margin is the difference between the two most frequent community
        assignments. Requires label alignment if using membership probs.
        
        If alignment not available, uses consensus confidence as proxy.
        
        Parameters
        ----------
        consensus : np.ndarray, optional
            Consensus partition to use for proxy margin.
        
        Returns
        -------
        np.ndarray
            Margin values, shape (n_nodes,). Higher = more confident.
        
        Examples
        --------
        >>> dist = CommunityDistribution([...], nodes=[...])
        >>> margin = dist.node_margin()
        >>> boundary_nodes = np.where(margin < 0.2)[0]
        """
        if self._membership_probs is not None:
            # True margin from aligned membership probs
            probs = self._membership_probs
            margin = np.zeros(self.n_nodes)
            
            for i in range(self.n_nodes):
                p = probs[i]
                p_sorted = np.sort(p)[::-1]
                if len(p_sorted) >= 2:
                    margin[i] = p_sorted[0] - p_sorted[1]
                else:
                    margin[i] = 1.0
            
            return margin
        
        else:
            # Proxy: use 2 * (confidence - 0.5) to map [0.5, 1] -> [0, 1]
            confidence = self.node_confidence(consensus)
            margin = 2.0 * (confidence - 0.5)
            margin = np.clip(margin, 0.0, 1.0)
            
            return margin
    
    def align_labels(
        self,
        reference: Union[str, np.ndarray] = "medoid",
        metric: str = "overlap"
    ):
        """Align partition labels to a reference using Hungarian matching.
        
        After alignment, membership probabilities P(node_i in community_k)
        can be computed meaningfully. Alignment solves the label correspondence
        problem (community 0 in partition A may correspond to community 3 in B).
        
        This method modifies internal state and caches aligned partitions.
        
        Parameters
        ----------
        reference : {'medoid', 'first'} or np.ndarray
            Reference partition for alignment:
            - 'medoid': Use medoid partition as reference
            - 'first': Use first partition as reference
            - np.ndarray: Use provided partition as reference
        metric : {'overlap', 'nmi'}
            Metric for computing cost matrix for Hungarian algorithm:
            - 'overlap': Maximize overlap (intersection) between communities
            - 'nmi': Maximize normalized mutual information
        
        Returns
        -------
        self
            Returns self for method chaining.
        
        Examples
        --------
        >>> dist = CommunityDistribution([...], nodes=[...])
        >>> dist.align_labels(reference='medoid')
        >>> probs = dist.node_membership_probs()
        """
        # Get reference partition
        if isinstance(reference, str):
            if reference == "medoid":
                ref = self._partitions[self._medoid_partition_index('vi')]
            elif reference == "first":
                ref = self._partitions[0]
            else:
                raise AlgorithmError(
                    f"Unknown reference type: {reference}",
                    suggestions=["Use 'medoid', 'first', or provide array"]
                )
        else:
            ref = np.asarray(reference, dtype=np.int32)
            if len(ref) != self.n_nodes:
                raise AlgorithmError(
                    f"Reference partition length {len(ref)} != n_nodes {self.n_nodes}"
                )
        
        # Align all partitions to reference
        aligned = []
        for partition in self._partitions:
            aligned_p = self._align_partition_to_reference(
                partition, ref, metric
            )
            aligned.append(aligned_p)
        
        self._aligned_partitions = aligned
        
        # Compute membership probabilities
        self._compute_membership_probs()
        
        return self
    
    def _align_partition_to_reference(
        self,
        partition: np.ndarray,
        reference: np.ndarray,
        metric: str
    ) -> np.ndarray:
        """Align a single partition to reference using Hungarian algorithm."""
        # Build contingency table
        labels_p = np.unique(partition)
        labels_r = np.unique(reference)
        
        n_p = len(labels_p)
        n_r = len(labels_r)
        
        # Ensure square matrix (pad if needed)
        n_max = max(n_p, n_r)
        
        # Build cost matrix (negative overlap for minimization)
        cost = np.zeros((n_max, n_max))
        
        for i, lp in enumerate(labels_p):
            for j, lr in enumerate(labels_r):
                mask_p = (partition == lp)
                mask_r = (reference == lr)
                
                if metric == "overlap":
                    # Maximize intersection
                    overlap = np.sum(mask_p & mask_r)
                    cost[i, j] = -overlap  # Negative for minimization
                
                elif metric == "nmi":
                    # Approximate NMI contribution
                    n_ij = np.sum(mask_p & mask_r)
                    n_i = np.sum(mask_p)
                    n_j = np.sum(mask_r)
                    
                    if n_ij > 0 and n_i > 0 and n_j > 0:
                        # Contribution to NMI (simplified)
                        nmi_contrib = n_ij * np.log(n_ij * self.n_nodes / (n_i * n_j))
                        cost[i, j] = -nmi_contrib
                
                else:
                    raise AlgorithmError(
                        f"Unknown alignment metric: {metric}",
                        suggestions=["Use 'overlap' or 'nmi'"]
                    )
        
        # Solve assignment problem
        row_ind, col_ind = linear_sum_assignment(cost)
        
        # Build label mapping
        label_map = {}
        for i, j in zip(row_ind, col_ind):
            if i < n_p:
                label_map[labels_p[i]] = labels_r[j] if j < n_r else max(labels_r) + 1
        
        # Apply mapping
        aligned = np.array([label_map.get(label, label) for label in partition])
        
        return aligned.astype(np.int32)
    
    def _compute_membership_probs(self):
        """Compute membership probabilities from aligned partitions."""
        if self._aligned_partitions is None:
            warnings.warn(
                "Cannot compute membership probs without alignment. "
                "Call align_labels() first.",
                stacklevel=2
            )
            return
        
        # Find maximum label across all partitions
        max_label = max(p.max() for p in self._aligned_partitions)
        n_communities = max_label + 1
        
        # Count weighted frequency for each (node, community) pair
        probs = np.zeros((self.n_nodes, n_communities))
        
        for partition, weight in zip(self._aligned_partitions, self._weights):
            for i in range(self.n_nodes):
                probs[i, partition[i]] += weight
        
        self._membership_probs = probs
    
    def node_membership_probs(self) -> np.ndarray:
        """Get per-node membership probabilities P(node_i in community_k).
        
        Requires label alignment via align_labels(). Returns array of shape
        (n_nodes, n_communities) where entry [i, k] is the probability that
        node i belongs to community k across all aligned partitions.
        
        Returns
        -------
        np.ndarray
            Membership probability matrix, shape (n_nodes, n_communities).
        
        Raises
        ------
        AlgorithmError
            If labels have not been aligned. Call align_labels() first.
        
        Examples
        --------
        >>> dist = CommunityDistribution([...], nodes=[...])
        >>> dist.align_labels(reference='medoid')
        >>> probs = dist.node_membership_probs()
        >>> probs.shape
        (100, 5)  # 100 nodes, 5 communities
        >>> probs[0]  # Membership probabilities for node 0
        array([0.8, 0.15, 0.05, 0.0, 0.0])
        """
        if self._membership_probs is None:
            raise AlgorithmError(
                "Membership probabilities not available without label alignment",
                suggestions=[
                    "Call dist.align_labels() before requesting membership probs",
                    "Use dist.node_confidence() for alignment-free confidence scores"
                ]
            )
        
        return self._membership_probs.copy()
    
    def to_dict(self, node_id: Any) -> Dict[str, Any]:
        """Get community assignment info for a specific node.
        
        Parameters
        ----------
        node_id : any
            Node identifier.
        
        Returns
        -------
        dict
            Dictionary with keys:
            - 'consensus': Consensus community label
            - 'confidence': Node confidence score
            - 'entropy': Node entropy score
            - 'margin': Node margin score
            - 'membership_probs': Membership probabilities (if aligned)
        
        Examples
        --------
        >>> dist = CommunityDistribution([...], nodes=['A', 'B', 'C'])
        >>> info = dist.to_dict('A')
        >>> info['consensus']
        0
        >>> info['confidence']
        0.85
        """
        if node_id not in self._node_to_idx:
            raise AlgorithmError(
                f"Node '{node_id}' not found in distribution",
                suggestions=[f"Available nodes: {self._nodes[:5]}..."]
            )
        
        idx = self._node_to_idx[node_id]
        consensus = self.consensus_partition()
        confidence = self.node_confidence(consensus)
        entropy = self.node_entropy()
        margin = self.node_margin(consensus)
        
        result = {
            'consensus': int(consensus[idx]),
            'confidence': float(confidence[idx]),
            'entropy': float(entropy[idx]),
            'margin': float(margin[idx]),
        }
        
        if self._membership_probs is not None:
            result['membership_probs'] = self._membership_probs[idx].tolist()
        
        return result


def partition_dict_to_array(
    partition_dict: Dict[Any, int],
    node_index: List[Any]
) -> np.ndarray:
    """Convert partition dictionary to array with canonical node ordering.
    
    Parameters
    ----------
    partition_dict : dict
        Mapping from node (or node-layer tuple) to community ID.
    node_index : list
        Ordered list of nodes defining the canonical ordering.
    
    Returns
    -------
    np.ndarray
        Partition array with shape (len(node_index),).
    
    Examples
    --------
    >>> partition = {('A', 'L1'): 0, ('B', 'L1'): 0, ('C', 'L1'): 1}
    >>> nodes = [('A', 'L1'), ('B', 'L1'), ('C', 'L1')]
    >>> arr = partition_dict_to_array(partition, nodes)
    >>> arr
    array([0, 0, 1])
    """
    return np.array([partition_dict[node] for node in node_index], dtype=np.int32)


def partition_array_to_dict(
    partition_array: np.ndarray,
    node_index: List[Any]
) -> Dict[Any, int]:
    """Convert partition array to dictionary.
    
    Parameters
    ----------
    partition_array : np.ndarray
        Partition labels, shape (n_nodes,).
    node_index : list
        Ordered list of node identifiers.
    
    Returns
    -------
    dict
        Mapping from node to community ID.
    
    Examples
    --------
    >>> arr = np.array([0, 0, 1])
    >>> nodes = [('A', 'L1'), ('B', 'L1'), ('C', 'L1')]
    >>> d = partition_array_to_dict(arr, nodes)
    >>> d[('A', 'L1')]
    0
    """
    return {node: int(label) for node, label in zip(node_index, partition_array)}
