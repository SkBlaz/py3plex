"""Probabilistic community detection result with uncertainty quantification.

This module provides ProbabilisticCommunityResult, which extends CommunityDistribution
to provide a backward-compatible interface for DSL v2 community queries with UQ.

The key design principle: maintain deterministic behavior by default, enable
probabilistic behavior when UQ is explicitly requested.

Examples
--------
>>> from py3plex.uncertainty import ProbabilisticCommunityResult
>>> from py3plex.core import multinet
>>> 
>>> # Create network
>>> net = multinet.multi_layer_network(directed=False)
>>> # ... add nodes/edges ...
>>> 
>>> # Deterministic (backward compatible)
>>> result = detect_communities_probabilistic(net, n_runs=1)
>>> result.labels  # Hard labels: Dict[node, community_id]
>>> 
>>> # Probabilistic (UQ-enabled)
>>> result = detect_communities_probabilistic(net, n_runs=50, seed=42)
>>> result.probs  # Membership probabilities: Dict[node, Dict[comm_id, prob]]
>>> result.entropy  # Per-node entropy: Dict[node, float]
>>> result.confidence  # Per-node confidence: Dict[node, float]
>>> result.to_pandas(expand_uncertainty=True)  # Full uncertainty columns
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import warnings

import numpy as np
import pandas as pd

from .partition import CommunityDistribution, partition_array_to_dict
from py3plex.exceptions import AlgorithmError


class ProbabilisticCommunityResult:
    """Probabilistic community detection result with backward compatibility.
    
    This class wraps CommunityDistribution to provide:
    1. Backward-compatible hard labels (deterministic view)
    2. Probabilistic membership distributions (uncertainty view)
    3. Node-level uncertainty metrics (entropy, confidence)
    4. Community-level stability metrics
    5. Partition-space variability metrics
    
    Parameters
    ----------
    distribution : CommunityDistribution
        The underlying distribution of community partitions.
    consensus_method : str, default='medoid'
        Method for computing consensus partition ('medoid' or 'cluster_coassoc').
    
    Attributes
    ----------
    n_nodes : int
        Number of nodes in the network.
    n_partitions : int
        Number of partitions in the ensemble.
    is_deterministic : bool
        True if only one partition (no uncertainty).
    
    Examples
    --------
    >>> # Create from CommunityDistribution
    >>> dist = CommunityDistribution(partitions=[...], nodes=[...])
    >>> result = ProbabilisticCommunityResult(dist)
    >>> 
    >>> # Access deterministic labels (backward compatible)
    >>> labels = result.labels  # Dict[node, community_id]
    >>> 
    >>> # Access probabilistic information (if n_partitions > 1)
    >>> if not result.is_deterministic:
    ...     probs = result.probs  # Dict[node, Dict[comm_id, prob]]
    ...     entropy = result.entropy  # Dict[node, float]
    ...     confidence = result.confidence  # Dict[node, float]
    """
    
    def __init__(
        self,
        distribution: CommunityDistribution,
        consensus_method: str = 'medoid',
    ):
        """Initialize probabilistic community result."""
        self._dist = distribution
        self._consensus_method = consensus_method
        
        # Lazy evaluation caches
        self._consensus_partition: Optional[np.ndarray] = None
        self._labels_dict: Optional[Dict[Any, int]] = None
        self._probs_dict: Optional[Dict[Any, Dict[int, float]]] = None
        self._entropy_dict: Optional[Dict[Any, float]] = None
        self._confidence_dict: Optional[Dict[Any, float]] = None
        self._margin_dict: Optional[Dict[Any, float]] = None
        
        # Community-level metrics cache
        self._community_stability: Optional[Dict[int, Dict[str, float]]] = None
        
        # Partition-space metrics cache
        self._partition_metrics: Optional[Dict[str, Any]] = None
    
    @property
    def n_nodes(self) -> int:
        """Number of nodes."""
        return self._dist.n_nodes
    
    @property
    def n_partitions(self) -> int:
        """Number of partitions in the ensemble."""
        return self._dist.n_partitions
    
    @property
    def is_deterministic(self) -> bool:
        """True if this is a deterministic result (single partition)."""
        return self.n_partitions == 1
    
    @property
    def nodes(self) -> List[Any]:
        """List of node identifiers."""
        return self._dist.nodes
    
    @property
    def labels(self) -> Dict[Any, int]:
        """Hard community labels (consensus partition).
        
        This provides backward-compatible deterministic labels.
        For n_partitions=1, returns the single partition.
        For n_partitions>1, returns consensus (medoid or cluster-based).
        
        Returns
        -------
        dict
            Mapping from node to community ID.
        
        Examples
        --------
        >>> result = ProbabilisticCommunityResult(dist)
        >>> labels = result.labels
        >>> labels[('A', 'social')]
        0
        """
        if self._labels_dict is None:
            if self._consensus_partition is None:
                self._consensus_partition = self._dist.consensus_partition(
                    method=self._consensus_method
                )
            self._labels_dict = partition_array_to_dict(
                self._consensus_partition,
                self._dist.nodes
            )
        return self._labels_dict
    
    @property
    def probs(self) -> Dict[Any, Dict[int, float]]:
        """Membership probabilities P(node in community).
        
        Requires n_partitions > 1. For deterministic results (n_partitions=1),
        returns probabilities of 1.0 for assigned community.
        
        Returns
        -------
        dict
            Nested dict: {node: {community_id: probability}}
        
        Raises
        ------
        AlgorithmError
            If label alignment has not been performed for n_partitions > 1.
        
        Examples
        --------
        >>> result = ProbabilisticCommunityResult(dist)
        >>> probs = result.probs
        >>> probs[('A', 'social')]
        {0: 0.8, 1: 0.15, 2: 0.05}
        """
        if self._probs_dict is None:
            if self.is_deterministic:
                # Deterministic case: probability 1.0 for assigned community
                self._probs_dict = {}
                labels = self.labels
                for node in self.nodes:
                    comm_id = labels[node]
                    self._probs_dict[node] = {comm_id: 1.0}
            else:
                # Probabilistic case: requires alignment
                try:
                    # Check if alignment already done
                    if self._dist._membership_probs is None:
                        # Perform alignment
                        self._dist.align_labels(
                            reference=self._consensus_method,
                            metric='overlap'
                        )
                    
                    # Get membership probabilities matrix
                    probs_matrix = self._dist.node_membership_probs()
                    
                    # Convert to nested dict format
                    self._probs_dict = {}
                    for i, node in enumerate(self.nodes):
                        node_probs = probs_matrix[i]
                        # Only include non-zero probabilities
                        comm_probs = {
                            comm_id: float(prob)
                            for comm_id, prob in enumerate(node_probs)
                            if prob > 0.0
                        }
                        self._probs_dict[node] = comm_probs
                
                except AlgorithmError:
                    warnings.warn(
                        "Could not compute membership probabilities. "
                        "Label alignment may have failed. "
                        "Falling back to consensus labels with prob=1.0",
                        stacklevel=2
                    )
                    # Fallback: deterministic labels with prob=1.0
                    self._probs_dict = {}
                    labels = self.labels
                    for node in self.nodes:
                        comm_id = labels[node]
                        self._probs_dict[node] = {comm_id: 1.0}
        
        return self._probs_dict
    
    @property
    def entropy(self) -> Dict[Any, float]:
        """Per-node entropy H(community assignment).
        
        Higher entropy indicates more uncertainty in community assignment.
        For deterministic results, entropy is 0.0.
        
        Returns
        -------
        dict
            Mapping from node to entropy value (in bits).
        
        Examples
        --------
        >>> result = ProbabilisticCommunityResult(dist)
        >>> entropy = result.entropy
        >>> entropy[('A', 'social')]
        0.75  # Some uncertainty in assignment
        """
        if self._entropy_dict is None:
            if self.is_deterministic:
                # Deterministic: entropy is 0
                self._entropy_dict = {node: 0.0 for node in self.nodes}
            else:
                # Compute entropy from distribution
                # Ensure alignment is done
                _ = self.probs  # Trigger alignment if needed
                
                entropy_array = self._dist.node_entropy(aligned=True, base=2.0)
                self._entropy_dict = {
                    node: float(entropy_array[i])
                    for i, node in enumerate(self.nodes)
                }
        
        return self._entropy_dict
    
    @property
    def confidence(self) -> Dict[Any, float]:
        """Per-node confidence (max membership probability).
        
        Confidence is the probability of the most likely community.
        For deterministic results, confidence is 1.0.
        
        Returns
        -------
        dict
            Mapping from node to confidence value in [0, 1].
        
        Examples
        --------
        >>> result = ProbabilisticCommunityResult(dist)
        >>> confidence = result.confidence
        >>> confidence[('A', 'social')]
        0.85  # 85% probability of consensus community
        """
        if self._confidence_dict is None:
            if self.is_deterministic:
                # Deterministic: confidence is 1.0
                self._confidence_dict = {node: 1.0 for node in self.nodes}
            else:
                # Use CommunityDistribution's node_confidence
                if self._consensus_partition is None:
                    self._consensus_partition = self._dist.consensus_partition(
                        method=self._consensus_method
                    )
                
                confidence_array = self._dist.node_confidence(self._consensus_partition)
                self._confidence_dict = {
                    node: float(confidence_array[i])
                    for i, node in enumerate(self.nodes)
                }
        
        return self._confidence_dict
    
    @property
    def margin(self) -> Dict[Any, float]:
        """Per-node margin (difference between top 2 membership probabilities).
        
        Margin measures how much more likely the top community is compared to
        the second most likely. Higher margin = more confident assignment.
        For deterministic results, margin is 1.0.
        
        Returns
        -------
        dict
            Mapping from node to margin value in [0, 1].
        
        Examples
        --------
        >>> result = ProbabilisticCommunityResult(dist)
        >>> margin = result.margin
        >>> margin[('A', 'social')]
        0.65  # Top community 65% more likely than second
        """
        if self._margin_dict is None:
            if self.is_deterministic:
                # Deterministic: margin is 1.0
                self._margin_dict = {node: 1.0 for node in self.nodes}
            else:
                if self._consensus_partition is None:
                    self._consensus_partition = self._dist.consensus_partition(
                        method=self._consensus_method
                    )
                
                margin_array = self._dist.node_margin(self._consensus_partition)
                self._margin_dict = {
                    node: float(margin_array[i])
                    for i, node in enumerate(self.nodes)
                }
        
        return self._margin_dict
    
    @property
    def community_stability(self) -> Dict[int, Dict[str, float]]:
        """Per-community stability metrics.
        
        For each community in the consensus partition, computes:
        - persistence: Fraction of partitions where community exists
        - size_mean: Mean community size across partitions
        - size_std: Standard deviation of community size
        - size_cv: Coefficient of variation (std/mean)
        
        Returns
        -------
        dict
            Nested dict: {community_id: {metric: value}}
        
        Examples
        --------
        >>> result = ProbabilisticCommunityResult(dist)
        >>> stability = result.community_stability
        >>> stability[0]
        {'persistence': 0.95, 'size_mean': 12.5, 'size_std': 1.2, 'size_cv': 0.096}
        """
        if self._community_stability is None:
            self._community_stability = self._compute_community_stability()
        return self._community_stability
    
    def _compute_community_stability(self) -> Dict[int, Dict[str, float]]:
        """Compute community-level stability metrics."""
        if self.is_deterministic:
            # For deterministic results, all communities have perfect stability
            labels = self.labels
            unique_comms = set(labels.values())
            
            # Count nodes per community
            comm_sizes = {}
            for comm_id in unique_comms:
                size = sum(1 for label in labels.values() if label == comm_id)
                comm_sizes[comm_id] = size
            
            return {
                comm_id: {
                    'persistence': 1.0,
                    'size_mean': float(size),
                    'size_std': 0.0,
                    'size_cv': 0.0,
                }
                for comm_id, size in comm_sizes.items()
            }
        
        # Probabilistic case: compute from ensemble
        partitions = self._dist.partitions
        consensus = self._consensus_partition
        if consensus is None:
            consensus = self._dist.consensus_partition(method=self._consensus_method)
        
        # Get unique community IDs in consensus
        unique_comms = np.unique(consensus)
        
        stability = {}
        for comm_id in unique_comms:
            # Nodes in this community (consensus)
            comm_nodes_mask = (consensus == comm_id)
            comm_node_indices = np.where(comm_nodes_mask)[0]
            
            if len(comm_node_indices) == 0:
                continue
            
            # Track this community across partitions
            # A community "persists" if a similar group appears
            sizes_across_partitions = []
            persistence_count = 0
            
            for partition in partitions:
                # Find which community in this partition best matches our consensus community
                # Use overlap: how many of our consensus community nodes are together?
                
                # Get assignments for our consensus community nodes
                partition_labels = partition[comm_node_indices]
                
                # Find the most common label among these nodes
                if len(partition_labels) == 0:
                    continue
                
                unique_labels, counts = np.unique(partition_labels, return_counts=True)
                most_common_label = unique_labels[np.argmax(counts)]
                most_common_count = counts.max()
                
                # Persistence: if >50% of our nodes are together in some community
                if most_common_count >= len(comm_node_indices) * 0.5:
                    persistence_count += 1
                    
                    # Get size of that community in this partition
                    community_size = np.sum(partition == most_common_label)
                    sizes_across_partitions.append(community_size)
            
            # Compute statistics
            persistence = persistence_count / len(partitions)
            
            if len(sizes_across_partitions) > 0:
                size_mean = np.mean(sizes_across_partitions)
                size_std = np.std(sizes_across_partitions)
                size_cv = size_std / size_mean if size_mean > 0 else 0.0
            else:
                # Community doesn't persist well
                size_mean = float(len(comm_node_indices))
                size_std = 0.0
                size_cv = 0.0
            
            stability[int(comm_id)] = {
                'persistence': float(persistence),
                'size_mean': float(size_mean),
                'size_std': float(size_std),
                'size_cv': float(size_cv),
            }
        
        return stability
    
    @property
    def partition_metrics(self) -> Dict[str, Any]:
        """Partition-space variability metrics.
        
        Computes distribution of partition similarity metrics:
        - vi_mean, vi_std: Variation of Information statistics
        - ari_mean, ari_std: Adjusted Rand Index statistics
        - nmi_mean, nmi_std: Normalized Mutual Information statistics
        
        Returns
        -------
        dict
            Dictionary with summary statistics for partition similarities.
        
        Examples
        --------
        >>> result = ProbabilisticCommunityResult(dist)
        >>> metrics = result.partition_metrics
        >>> metrics['vi_mean']
        0.25  # Average VI distance between partitions
        """
        if self._partition_metrics is None:
            self._partition_metrics = self._compute_partition_metrics()
        return self._partition_metrics
    
    def _compute_partition_metrics(self) -> Dict[str, Any]:
        """Compute partition-space variability metrics."""
        if self.is_deterministic:
            # Deterministic: perfect agreement
            return {
                'vi_mean': 0.0,
                'vi_std': 0.0,
                'vi_quantiles': {0.025: 0.0, 0.5: 0.0, 0.975: 0.0},
                'ari_mean': 1.0,
                'ari_std': 0.0,
                'ari_quantiles': {0.025: 1.0, 0.5: 1.0, 0.975: 1.0},
                'nmi_mean': 1.0,
                'nmi_std': 0.0,
                'nmi_quantiles': {0.025: 1.0, 0.5: 1.0, 0.975: 1.0},
            }
        
        # Compute pairwise VI, ARI, NMI
        partitions = self._dist.partitions
        n_partitions = len(partitions)
        
        # Sample pairs if too many
        max_pairs = 1000
        if n_partitions * (n_partitions - 1) // 2 > max_pairs:
            # Sample random pairs
            rng = np.random.default_rng(0)
            n_samples = max_pairs
            pairs = []
            seen = set()
            while len(pairs) < n_samples:
                i, j = rng.integers(0, n_partitions, size=2)
                if i != j:
                    key = (min(i, j), max(i, j))
                    if key not in seen:
                        pairs.append(key)
                        seen.add(key)
        else:
            # All pairs
            pairs = [(i, j) for i in range(n_partitions) for j in range(i + 1, n_partitions)]
        
        # Compute metrics
        vi_values = []
        ari_values = []
        nmi_values = []
        
        for i, j in pairs:
            p1 = partitions[i]
            p2 = partitions[j]
            
            # VI (use method from CommunityDistribution)
            vi = self._dist._partition_vi_distance(p1, p2)
            vi_values.append(vi)
            
            # ARI and NMI (need sklearn)
            try:
                from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
                ari = adjusted_rand_score(p1, p2)
                nmi = normalized_mutual_info_score(p1, p2)
                ari_values.append(ari)
                nmi_values.append(nmi)
            except ImportError:
                # Skip ARI/NMI if sklearn not available
                pass
        
        # Compute statistics
        metrics = {
            'vi_mean': float(np.mean(vi_values)),
            'vi_std': float(np.std(vi_values)),
            'vi_quantiles': {
                0.025: float(np.quantile(vi_values, 0.025)),
                0.5: float(np.quantile(vi_values, 0.5)),
                0.975: float(np.quantile(vi_values, 0.975)),
            }
        }
        
        if len(ari_values) > 0:
            metrics['ari_mean'] = float(np.mean(ari_values))
            metrics['ari_std'] = float(np.std(ari_values))
            metrics['ari_quantiles'] = {
                0.025: float(np.quantile(ari_values, 0.025)),
                0.5: float(np.quantile(ari_values, 0.5)),
                0.975: float(np.quantile(ari_values, 0.975)),
            }
        
        if len(nmi_values) > 0:
            metrics['nmi_mean'] = float(np.mean(nmi_values))
            metrics['nmi_std'] = float(np.std(nmi_values))
            metrics['nmi_quantiles'] = {
                0.025: float(np.quantile(nmi_values, 0.025)),
                0.5: float(np.quantile(nmi_values, 0.5)),
                0.975: float(np.quantile(nmi_values, 0.975)),
            }
        
        return metrics
    
    def to_dict(self, include_probs: bool = False) -> Dict[str, Any]:
        """Export result as dictionary.
        
        Parameters
        ----------
        include_probs : bool, default=False
            If True, include full membership probability distributions.
        
        Returns
        -------
        dict
            Dictionary with community information.
        
        Examples
        --------
        >>> result = ProbabilisticCommunityResult(dist)
        >>> d = result.to_dict(include_probs=True)
        >>> d.keys()
        dict_keys(['labels', 'entropy', 'confidence', 'probs', ...])
        """
        result = {
            'labels': self.labels,
            'entropy': self.entropy,
            'confidence': self.confidence,
            'margin': self.margin,
            'is_deterministic': self.is_deterministic,
            'n_partitions': self.n_partitions,
        }
        
        if include_probs or not self.is_deterministic:
            result['probs'] = self.probs
        
        if not self.is_deterministic:
            result['community_stability'] = self.community_stability
            result['partition_metrics'] = self.partition_metrics
        
        return result
    
    def to_pandas(self, expand_uncertainty: bool = False) -> pd.DataFrame:
        """Export result as pandas DataFrame.
        
        Parameters
        ----------
        expand_uncertainty : bool, default=False
            If True, expand uncertainty information into separate columns:
            - community_id: Hard label
            - community_confidence: Max probability
            - membership_entropy: Entropy
            - membership_margin: Margin
            - p_comm_0, p_comm_1, ...: Top-k membership probabilities
        
        Returns
        -------
        pd.DataFrame
            DataFrame with one row per node.
        
        Examples
        --------
        >>> result = ProbabilisticCommunityResult(dist)
        >>> df = result.to_pandas(expand_uncertainty=True)
        >>> df.columns
        Index(['id', 'community_id', 'community_confidence', 
               'membership_entropy', 'membership_margin', 
               'p_comm_0', 'p_comm_1', ...])
        """
        labels = self.labels
        entropy = self.entropy
        confidence = self.confidence
        margin = self.margin
        
        data = []
        for node in self.nodes:
            row = {
                'id': node,
                'community_id': labels[node],
            }
            
            if expand_uncertainty:
                row['community_confidence'] = confidence[node]
                row['membership_entropy'] = entropy[node]
                row['membership_margin'] = margin[node]
                
                # Add top-k membership probabilities
                if not self.is_deterministic:
                    node_probs = self.probs[node]
                    # Sort by probability descending
                    sorted_probs = sorted(
                        node_probs.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )
                    # Add top-k (e.g., top 3)
                    topk = min(3, len(sorted_probs))
                    for k in range(topk):
                        if k < len(sorted_probs):
                            comm_id, prob = sorted_probs[k]
                            row[f'p_comm_{comm_id}'] = prob
            
            data.append(row)
        
        return pd.DataFrame(data)
