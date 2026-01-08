"""Online reducers for partition uncertainty quantification.

This module provides memory-efficient reducers that accumulate statistics
about partitions sample-by-sample, without storing all samples.

Reducers follow the online aggregation pattern:
1. update(partition) - accumulate statistics from one sample
2. finalize() - compute final statistics

Examples
--------
>>> from py3plex.uncertainty.partition_reducers import NodeEntropyReducer
>>> import numpy as np
>>> 
>>> reducer = NodeEntropyReducer(n_nodes=4, node_ids=['A', 'B', 'C', 'D'])
>>> reducer.update(np.array([0, 0, 1, 1]))
>>> reducer.update(np.array([0, 0, 0, 1]))
>>> reducer.update(np.array([0, 1, 0, 1]))
>>> 
>>> entropy = reducer.finalize()
>>> entropy.shape
(4,)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple
import warnings

import numpy as np
from scipy.sparse import csr_matrix, lil_matrix

from py3plex.uncertainty.partition_metrics import (
    variation_of_information,
    normalized_mutual_information,
)


class PartitionReducer(ABC):
    """Base class for partition reducers.
    
    A reducer accumulates statistics from a stream of partitions
    without storing all partitions in memory.
    """
    
    @abstractmethod
    def update(self, partition: np.ndarray, weight: float = 1.0):
        """Update reducer with a new partition sample.
        
        Parameters
        ----------
        partition : np.ndarray
            Partition array, shape (n_nodes,) with integer labels
        weight : float, default=1.0
            Weight for this sample (for weighted aggregation)
        """
        pass
    
    @abstractmethod
    def finalize(self) -> Any:
        """Finalize and return accumulated statistics.
        
        Returns
        -------
        Any
            Reducer-specific statistics
        """
        pass
    
    @abstractmethod
    def reset(self):
        """Reset reducer to initial state."""
        pass


class NodeEntropyReducer(PartitionReducer):
    """Compute per-node entropy across partitions.
    
    Entropy H(node) = -sum_k p_k * log(p_k)
    where p_k is the probability that node is in community k.
    
    This requires tracking community label frequencies per node.
    
    Parameters
    ----------
    n_nodes : int
        Number of nodes
    node_ids : list, optional
        Node identifiers (for mapping back to nodes)
        
    Examples
    --------
    >>> reducer = NodeEntropyReducer(n_nodes=3)
    >>> reducer.update(np.array([0, 0, 1]))
    >>> reducer.update(np.array([0, 1, 1]))
    >>> entropy = reducer.finalize()
    >>> entropy.shape
    (3,)
    """
    
    def __init__(self, n_nodes: int, node_ids: Optional[List[Any]] = None):
        """Initialize reducer."""
        self.n_nodes = n_nodes
        self.node_ids = node_ids if node_ids is not None else list(range(n_nodes))
        
        # Track label frequencies per node
        # counts[node][label] = count
        self.counts: List[Dict[int, float]] = [
            defaultdict(float) for _ in range(n_nodes)
        ]
        self.total_weight = 0.0
    
    def update(self, partition: np.ndarray, weight: float = 1.0):
        """Update with partition sample.
        
        Parameters
        ----------
        partition : np.ndarray
            Partition labels, shape (n_nodes,)
        weight : float
            Sample weight
        """
        if len(partition) != self.n_nodes:
            raise ValueError(
                f"Partition length {len(partition)} != n_nodes {self.n_nodes}"
            )
        
        for i in range(self.n_nodes):
            label = int(partition[i])
            self.counts[i][label] += weight
        
        self.total_weight += weight
    
    def finalize(self) -> np.ndarray:
        """Compute per-node entropy.
        
        Returns
        -------
        np.ndarray
            Entropy values, shape (n_nodes,)
        """
        entropy = np.zeros(self.n_nodes)
        
        if self.total_weight == 0:
            return entropy
        
        for i in range(self.n_nodes):
            # Get normalized probabilities
            counts = self.counts[i]
            if not counts:
                entropy[i] = 0.0
                continue
            
            probs = np.array(list(counts.values())) / self.total_weight
            probs = probs[probs > 0]  # Remove zeros
            
            # Compute entropy
            entropy[i] = -np.sum(probs * np.log(probs))
        
        return entropy
    
    def reset(self):
        """Reset reducer."""
        self.counts = [defaultdict(float) for _ in range(self.n_nodes)]
        self.total_weight = 0.0
    
    def get_membership_probs(self) -> np.ndarray:
        """Get membership probability matrix.
        
        Returns
        -------
        np.ndarray
            Probability matrix, shape (n_nodes, n_communities)
            where entry [i, k] is P(node i in community k)
        """
        if self.total_weight == 0:
            raise ValueError("No samples accumulated")
        
        # Find maximum label across all nodes
        max_label = max(
            max(counts.keys()) if counts else 0
            for counts in self.counts
        )
        n_communities = max_label + 1
        
        probs = np.zeros((self.n_nodes, n_communities))
        
        for i in range(self.n_nodes):
            for label, count in self.counts[i].items():
                probs[i, label] = count / self.total_weight
        
        return probs
    
    def get_max_membership(self) -> Tuple[np.ndarray, np.ndarray]:
        """Get maximum membership probability per node.
        
        Returns
        -------
        labels : np.ndarray
            Most frequent label per node
        probs : np.ndarray
            Probability of most frequent label
        """
        labels = np.zeros(self.n_nodes, dtype=int)
        probs = np.zeros(self.n_nodes)
        
        if self.total_weight == 0:
            return labels, probs
        
        for i in range(self.n_nodes):
            counts = self.counts[i]
            if not counts:
                labels[i] = 0
                probs[i] = 0.0
            else:
                max_label = max(counts.keys(), key=lambda k: counts[k])
                labels[i] = max_label
                probs[i] = counts[max_label] / self.total_weight
        
        return labels, probs


class CoAssignmentReducer(PartitionReducer):
    """Compute co-assignment probability matrix.
    
    P(i, j) = probability that nodes i and j are in the same community.
    
    This can be computed in sparse mode (top-k neighbors only) to save memory.
    
    Parameters
    ----------
    n_nodes : int
        Number of nodes
    sparse : bool, default=True
        If True, store only top-k co-assignments per node
    topk : int, default=50
        Number of top co-assignments to keep per node (if sparse=True)
    threshold : float, default=0.0
        Minimum co-assignment probability to store (if sparse=True)
        
    Examples
    --------
    >>> reducer = CoAssignmentReducer(n_nodes=4, sparse=False)
    >>> reducer.update(np.array([0, 0, 1, 1]))
    >>> reducer.update(np.array([0, 0, 0, 1]))
    >>> coassoc = reducer.finalize()
    >>> coassoc.shape
    (4, 4)
    """
    
    def __init__(
        self,
        n_nodes: int,
        sparse: bool = True,
        topk: int = 50,
        threshold: float = 0.0
    ):
        """Initialize reducer."""
        self.n_nodes = n_nodes
        self.sparse = sparse
        self.topk = topk
        self.threshold = threshold
        
        if sparse:
            # Store as dict of dicts: counts[i][j] = count
            self.counts: Dict[int, Dict[int, float]] = defaultdict(
                lambda: defaultdict(float)
            )
        else:
            # Store as dense matrix
            self.counts_dense = np.zeros((n_nodes, n_nodes), dtype=float)
        
        self.total_weight = 0.0
    
    def update(self, partition: np.ndarray, weight: float = 1.0):
        """Update with partition sample.
        
        Parameters
        ----------
        partition : np.ndarray
            Partition labels, shape (n_nodes,)
        weight : float
            Sample weight
        """
        if len(partition) != self.n_nodes:
            raise ValueError(
                f"Partition length {len(partition)} != n_nodes {self.n_nodes}"
            )
        
        # Update co-assignment counts
        if self.sparse:
            # Only update non-zero entries
            for i in range(self.n_nodes):
                for j in range(i, self.n_nodes):
                    if partition[i] == partition[j]:
                        self.counts[i][j] += weight
                        if i != j:
                            self.counts[j][i] += weight
        else:
            # Update dense matrix
            for i in range(self.n_nodes):
                for j in range(i, self.n_nodes):
                    if partition[i] == partition[j]:
                        self.counts_dense[i, j] += weight
                        if i != j:
                            self.counts_dense[j, i] += weight
        
        self.total_weight += weight
    
    def finalize(self) -> np.ndarray:
        """Compute co-assignment probabilities.
        
        Returns
        -------
        np.ndarray
            Co-assignment matrix, shape (n_nodes, n_nodes)
            If sparse=True, only top-k entries per row are non-zero
        """
        if self.total_weight == 0:
            return np.zeros((self.n_nodes, self.n_nodes))
        
        if self.sparse:
            # Convert to dense, keeping only top-k per row
            coassoc = np.zeros((self.n_nodes, self.n_nodes))
            
            for i in range(self.n_nodes):
                # Get neighbors with their counts
                neighbors = self.counts.get(i, {})
                
                if not neighbors:
                    # Diagonal is always 1
                    coassoc[i, i] = 1.0
                    continue
                
                # Convert to probabilities
                neighbor_probs = {
                    j: count / self.total_weight
                    for j, count in neighbors.items()
                }
                
                # Filter by threshold
                if self.threshold > 0:
                    neighbor_probs = {
                        j: p for j, p in neighbor_probs.items()
                        if p >= self.threshold
                    }
                
                # Keep top-k
                if self.topk > 0 and len(neighbor_probs) > self.topk:
                    sorted_neighbors = sorted(
                        neighbor_probs.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )
                    neighbor_probs = dict(sorted_neighbors[:self.topk])
                
                # Store in matrix
                for j, prob in neighbor_probs.items():
                    coassoc[i, j] = prob
                
                # Ensure diagonal is 1
                coassoc[i, i] = 1.0
            
            return coassoc
        else:
            # Normalize dense matrix
            coassoc = self.counts_dense / self.total_weight
            # Ensure diagonal is 1
            np.fill_diagonal(coassoc, 1.0)
            return coassoc
    
    def reset(self):
        """Reset reducer."""
        if self.sparse:
            self.counts = defaultdict(lambda: defaultdict(float))
        else:
            self.counts_dense = np.zeros((self.n_nodes, self.n_nodes), dtype=float)
        self.total_weight = 0.0


class PartitionDistanceReducer(PartitionReducer):
    """Compute pairwise partition distances (VI, NMI).
    
    This reducer accumulates all pairwise distances between partitions
    to compute statistics (mean, std) of partition stability.
    
    Parameters
    ----------
    metric : str, default="vi"
        Distance metric: "vi" or "nmi"
    store_samples : bool, default=False
        If True, store all partition samples for later analysis
        
    Examples
    --------
    >>> reducer = PartitionDistanceReducer(metric="vi")
    >>> reducer.update(np.array([0, 0, 1, 1]))
    >>> reducer.update(np.array([0, 0, 0, 1]))
    >>> stats = reducer.finalize()
    >>> stats.keys()
    dict_keys(['vi_mean', 'vi_std', 'vi_min', 'vi_max'])
    """
    
    def __init__(self, metric: str = "vi", store_samples: bool = False):
        """Initialize reducer."""
        valid_metrics = {"vi", "nmi"}
        if metric not in valid_metrics:
            raise ValueError(f"metric must be one of {valid_metrics}, got {metric}")
        
        self.metric = metric
        self.store_samples = store_samples
        
        # Store distances
        self.distances: List[float] = []
        
        # Optionally store partition samples
        self.samples: List[np.ndarray] = [] if store_samples else None
    
    def update(self, partition: np.ndarray, weight: float = 1.0):
        """Update with partition sample.
        
        Computes distances to all previously seen partitions.
        
        Parameters
        ----------
        partition : np.ndarray
            Partition labels
        weight : float
            Sample weight (currently unused, for future weighting)
        """
        partition = np.asarray(partition, dtype=int)
        
        # Compute distances to all previous samples
        if self.store_samples:
            for prev in self.samples:
                if self.metric == "vi":
                    d = variation_of_information(partition, prev)
                elif self.metric == "nmi":
                    # NMI is similarity, convert to distance
                    d = 1.0 - normalized_mutual_information(partition, prev)
                
                self.distances.append(d)
            
            # Store this sample
            self.samples.append(partition.copy())
        else:
            # If not storing samples, compute against temporary buffer
            # This is less memory-efficient but avoids storing all samples
            # For now, we require store_samples=True for proper operation
            warnings.warn(
                "PartitionDistanceReducer requires store_samples=True for accurate "
                "distance computation. Computing distances only against last sample.",
                stacklevel=2
            )
    
    def finalize(self) -> Dict[str, float]:
        """Compute distance statistics.
        
        Returns
        -------
        dict
            Statistics with keys:
            - {metric}_mean: Mean distance
            - {metric}_std: Standard deviation of distance
            - {metric}_min: Minimum distance
            - {metric}_max: Maximum distance
        """
        if not self.distances:
            return {
                f"{self.metric}_mean": 0.0,
                f"{self.metric}_std": 0.0,
                f"{self.metric}_min": 0.0,
                f"{self.metric}_max": 0.0,
            }
        
        distances = np.array(self.distances)
        
        return {
            f"{self.metric}_mean": float(np.mean(distances)),
            f"{self.metric}_std": float(np.std(distances)),
            f"{self.metric}_min": float(np.min(distances)),
            f"{self.metric}_max": float(np.max(distances)),
        }
    
    def reset(self):
        """Reset reducer."""
        self.distances = []
        if self.store_samples:
            self.samples = []


class ConsensusReducer(PartitionReducer):
    """Compute consensus partition (mode of labels per node).
    
    The consensus partition assigns each node to its most frequent
    community label across samples.
    
    Parameters
    ----------
    n_nodes : int
        Number of nodes
        
    Examples
    --------
    >>> reducer = ConsensusReducer(n_nodes=4)
    >>> reducer.update(np.array([0, 0, 1, 1]))
    >>> reducer.update(np.array([0, 0, 0, 1]))
    >>> reducer.update(np.array([0, 0, 0, 1]))
    >>> consensus = reducer.finalize()
    >>> consensus
    array([0, 0, 0, 1])
    """
    
    def __init__(self, n_nodes: int):
        """Initialize reducer."""
        self.n_nodes = n_nodes
        
        # Use NodeEntropyReducer internally (it tracks label frequencies)
        self.entropy_reducer = NodeEntropyReducer(n_nodes)
    
    def update(self, partition: np.ndarray, weight: float = 1.0):
        """Update with partition sample.
        
        Parameters
        ----------
        partition : np.ndarray
            Partition labels
        weight : float
            Sample weight
        """
        self.entropy_reducer.update(partition, weight)
    
    def finalize(self) -> np.ndarray:
        """Compute consensus partition.
        
        Returns
        -------
        np.ndarray
            Consensus partition, shape (n_nodes,)
        """
        labels, _ = self.entropy_reducer.get_max_membership()
        return labels
    
    def reset(self):
        """Reset reducer."""
        self.entropy_reducer.reset()


# ============================================================================
# Updated reducers for UQ spine integration
# ============================================================================


class NodeMarginalReducer(PartitionReducer):
    """Compute per-node marginal membership distributions (UQ spine version).
    
    This reducer is the canonical implementation for the UQ execution spine.
    It tracks the frequency of each community label for each node across
    samples and computes:
    - Node entropy: H(node) = -sum_k p_k * log(p_k)
    - Maximum membership probability: max_c p(node, c)  
    - Consensus labels: argmax_c p(node, c)
    
    This replaces NodeEntropyReducer as the primary reducer for partition UQ.
    
    Parameters
    ----------
    n_nodes : int
        Number of nodes
    node_ids : list, optional
        Node identifiers (for mapping back to nodes)
        
    Examples
    --------
    >>> reducer = NodeMarginalReducer(n_nodes=3)
    >>> from py3plex.uncertainty.partition_types import PartitionOutput
    >>> reducer.update(PartitionOutput(labels={'A': 0, 'B': 0, 'C': 1}))
    >>> reducer.update(PartitionOutput(labels={'A': 0, 'B': 1, 'C': 1}))
    >>> result = reducer.finalize()
    >>> result['entropy'].shape
    (3,)
    """
    
    def __init__(self, n_nodes: int, node_ids: Optional[List[Any]] = None):
        """Initialize reducer."""
        self.n_nodes = n_nodes
        self.node_ids = node_ids if node_ids is not None else list(range(n_nodes))
        
        # Create mapping from node_id to index
        self.node_to_idx = {nid: i for i, nid in enumerate(self.node_ids)}
        
        # Track label frequencies per node
        # counts[node_idx][label] = count
        self.counts: List[Dict[int, float]] = [
            defaultdict(float) for _ in range(n_nodes)
        ]
        self.total_weight = 0.0
    
    def update(self, sample_output: Any, weight: float = 1.0):
        """Update with partition sample.
        
        Parameters
        ----------
        sample_output : PartitionOutput or np.ndarray
            If PartitionOutput: dict mapping node_id -> community_id
            If np.ndarray: partition labels, shape (n_nodes,)
        weight : float
            Sample weight
        """
        # Handle PartitionOutput
        if hasattr(sample_output, 'labels') and isinstance(sample_output.labels, dict):
            labels_dict = sample_output.labels
            for node_id, community_id in labels_dict.items():
                if node_id in self.node_to_idx:
                    idx = self.node_to_idx[node_id]
                    self.counts[idx][int(community_id)] += weight
        # Handle raw numpy array
        elif isinstance(sample_output, np.ndarray):
            partition = sample_output
            if len(partition) != self.n_nodes:
                raise ValueError(
                    f"Partition length {len(partition)} != n_nodes {self.n_nodes}"
                )
            for i in range(self.n_nodes):
                label = int(partition[i])
                self.counts[i][label] += weight
        else:
            raise TypeError(
                f"Expected PartitionOutput or np.ndarray, got {type(sample_output)}"
            )
        
        self.total_weight += weight
    
    def finalize(self) -> Dict[str, np.ndarray]:
        """Compute node-level statistics.
        
        Returns
        -------
        dict
            Dictionary with keys:
            - 'entropy': Node entropy, shape (n_nodes,)
            - 'p_max': Maximum membership probability, shape (n_nodes,)
            - 'consensus_labels': Most frequent label per node, shape (n_nodes,)
        """
        entropy = np.zeros(self.n_nodes)
        p_max = np.zeros(self.n_nodes)
        consensus_labels = np.zeros(self.n_nodes, dtype=int)
        
        if self.total_weight == 0:
            return {
                'entropy': entropy,
                'p_max': p_max,
                'consensus_labels': consensus_labels,
            }
        
        for i in range(self.n_nodes):
            # Get normalized probabilities
            counts = self.counts[i]
            if not counts:
                entropy[i] = 0.0
                p_max[i] = 0.0
                consensus_labels[i] = 0
                continue
            
            probs = np.array(list(counts.values())) / self.total_weight
            probs = probs[probs > 0]  # Remove zeros
            
            # Compute entropy
            entropy[i] = -np.sum(probs * np.log(probs))
            
            # Get max probability and consensus label
            max_label = max(counts.keys(), key=lambda k: counts[k])
            consensus_labels[i] = max_label
            p_max[i] = counts[max_label] / self.total_weight
        
        return {
            'entropy': entropy,
            'p_max': p_max,
            'consensus_labels': consensus_labels,
        }
    
    def reset(self):
        """Reset reducer."""
        self.counts = [defaultdict(float) for _ in range(self.n_nodes)]
        self.total_weight = 0.0


class ConsensusPartitionReducer(PartitionReducer):
    """Compute consensus partition using node marginals (UQ spine version).
    
    This reducer depends on NodeMarginalReducer to provide marginal
    distributions. It extracts the consensus labels from the marginals.
    
    This is a thin wrapper that extracts consensus from NodeMarginalReducer
    output, following the design principle that ConsensusReducer uses
    marginals from NodeMarginalReducer.
    
    Parameters
    ----------
    marginal_reducer : NodeMarginalReducer
        NodeMarginalReducer instance to use for marginals
        
    Examples
    --------
    >>> marginal_reducer = NodeMarginalReducer(n_nodes=3)
    >>> consensus_reducer = ConsensusPartitionReducer(marginal_reducer)
    >>> # Updates are handled by marginal_reducer
    >>> consensus = consensus_reducer.finalize()
    """
    
    def __init__(self, marginal_reducer: NodeMarginalReducer):
        """Initialize reducer."""
        self.marginal_reducer = marginal_reducer
    
    def update(self, sample_output: Any, weight: float = 1.0):
        """Update is delegated to marginal_reducer.
        
        Parameters
        ----------
        sample_output : PartitionOutput or np.ndarray
            Partition sample
        weight : float
            Sample weight
        """
        # Delegate to marginal reducer
        self.marginal_reducer.update(sample_output, weight)
    
    def finalize(self) -> np.ndarray:
        """Compute consensus partition from marginals.
        
        Returns
        -------
        np.ndarray
            Consensus partition, shape (n_nodes,)
        """
        marginals = self.marginal_reducer.finalize()
        return marginals['consensus_labels']
    
    def reset(self):
        """Reset is delegated to marginal_reducer."""
        self.marginal_reducer.reset()


class StabilityReducer(PartitionReducer):
    """Compute partition stability using consensus as fixed reference.
    
    This reducer computes VI and NMI between each sample partition and
    a fixed consensus partition. This avoids the O(n^2) cost of pairwise
    distances and provides a clearer interpretation: how far is each
    sample from the consensus?
    
    Parameters
    ----------
    consensus_partition : np.ndarray
        Fixed consensus partition to use as reference
        
    Examples
    --------
    >>> consensus = np.array([0, 0, 1, 1])
    >>> reducer = StabilityReducer(consensus_partition=consensus)
    >>> reducer.update(PartitionOutput(labels={'A': 0, 'B': 0, 'C': 1, 'D': 1}))
    >>> reducer.update(PartitionOutput(labels={'A': 0, 'B': 0, 'C': 0, 'D': 1}))
    >>> stats = reducer.finalize()
    >>> stats.keys()
    dict_keys(['vi_mean', 'vi_std', 'nmi_mean', 'nmi_std'])
    """
    
    def __init__(self, consensus_partition: Optional[np.ndarray] = None):
        """Initialize reducer."""
        self.consensus_partition = consensus_partition
        self.vi_values: List[float] = []
        self.nmi_values: List[float] = []
    
    def set_consensus(self, consensus_partition: np.ndarray):
        """Set consensus partition after construction.
        
        This allows constructing the reducer before consensus is computed.
        """
        self.consensus_partition = np.asarray(consensus_partition, dtype=int)
    
    def update(self, sample_output: Any, weight: float = 1.0):
        """Update with partition sample.
        
        Computes VI and NMI between sample and consensus.
        
        Parameters
        ----------
        sample_output : PartitionOutput or np.ndarray
            Partition sample
        weight : float
            Sample weight (currently unused)
        """
        if self.consensus_partition is None:
            raise RuntimeError(
                "Consensus partition not set. Call set_consensus() before update()."
            )
        
        # Convert sample to array
        if hasattr(sample_output, 'labels') and isinstance(sample_output.labels, dict):
            # Convert dict to array (assumes node_ids are ordered)
            labels_dict = sample_output.labels
            node_ids = sorted(labels_dict.keys())
            partition = np.array([labels_dict[nid] for nid in node_ids], dtype=int)
        elif isinstance(sample_output, np.ndarray):
            partition = np.asarray(sample_output, dtype=int)
        else:
            raise TypeError(
                f"Expected PartitionOutput or np.ndarray, got {type(sample_output)}"
            )
        
        # Compute distances
        vi = variation_of_information(partition, self.consensus_partition)
        nmi_val = normalized_mutual_information(partition, self.consensus_partition)
        
        self.vi_values.append(vi)
        self.nmi_values.append(nmi_val)
    
    def finalize(self) -> Dict[str, float]:
        """Compute stability statistics.
        
        Returns
        -------
        dict
            Statistics with keys:
            - vi_mean: Mean VI to consensus
            - vi_std: Standard deviation of VI
            - nmi_mean: Mean NMI to consensus
            - nmi_std: Standard deviation of NMI
        """
        if not self.vi_values:
            return {
                'vi_mean': 0.0,
                'vi_std': 0.0,
                'nmi_mean': 1.0,
                'nmi_std': 0.0,
            }
        
        vi_arr = np.array(self.vi_values)
        nmi_arr = np.array(self.nmi_values)
        
        return {
            'vi_mean': float(np.mean(vi_arr)),
            'vi_std': float(np.std(vi_arr)),
            'nmi_mean': float(np.mean(nmi_arr)),
            'nmi_std': float(np.std(nmi_arr)),
        }
    
    def reset(self):
        """Reset reducer."""
        self.vi_values = []
        self.nmi_values = []
