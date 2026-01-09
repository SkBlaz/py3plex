"""PartitionUQ: Canonical uncertainty quantification for community partitions.

This module provides the PartitionUQ class - the canonical result type for
uncertainty quantification over discrete partitions.

PartitionUQ stores:
- Consensus partition (mode or Leiden-style consensus)
- Per-node membership entropy
- Per-node maximum membership probability
- Co-assignment probabilities (sparse, thresholded)
- Global stability metrics (VI/NMI distributions)

Examples
--------
>>> from py3plex.uncertainty.partition_uq import PartitionUQ
>>> import numpy as np
>>> 
>>> # Create from sample partitions
>>> partitions = [
...     np.array([0, 0, 1, 1]),
...     np.array([0, 0, 0, 1]),
...     np.array([0, 1, 0, 1]),
... ]
>>> 
>>> uq = PartitionUQ.from_samples(
...     partitions=partitions,
...     node_ids=['A', 'B', 'C', 'D'],
...     store="sketch"
... )
>>> 
>>> print(uq.consensus_partition)
>>> print(uq.membership_entropy)
>>> print(uq.stability_summary())
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import warnings

import numpy as np

from py3plex.uncertainty.partition_reducers import (
    NodeEntropyReducer,
    CoAssignmentReducer,
    PartitionDistanceReducer,
    ConsensusReducer,
)
from py3plex.uncertainty.partition_metrics import (
    variation_of_information,
    normalized_mutual_information,
)


@dataclass
class PartitionUQ:
    """Uncertainty quantification for community partitions.
    
    This class stores canonical UQ outputs for partitions without
    requiring storage of all samples.
    
    Attributes
    ----------
    node_ids : list
        Ordered list of node identifiers
    n_samples : int
        Number of partition samples used
    consensus_partition : np.ndarray
        Consensus partition (mode or medoid), shape (n_nodes,)
    membership_entropy : np.ndarray
        Per-node entropy, shape (n_nodes,). Higher = more uncertain.
    p_max_membership : np.ndarray
        Maximum membership probability per node, shape (n_nodes,)
    coassoc_matrix : np.ndarray, optional
        Co-assignment probability matrix (sparse or dense)
    vi_mean : float
        Mean variation of information between partitions
    vi_std : float
        Std of variation of information
    nmi_mean : float
        Mean normalized mutual information
    nmi_std : float
        Std of normalized mutual information
    store_mode : str
        Storage mode: "none", "samples", or "sketch"
    samples : list of np.ndarray, optional
        Raw partition samples (only if store_mode="samples")
    meta : dict
        Additional metadata (algorithm, parameters, provenance)
        
    Examples
    --------
    >>> uq = PartitionUQ.from_samples(
    ...     partitions=[...],
    ...     node_ids=['A', 'B', 'C'],
    ...     store="sketch"
    ... )
    >>> 
    >>> # Access consensus
    >>> print(uq.consensus_partition)
    >>> 
    >>> # Check uncertain nodes
    >>> uncertain = uq.boundary_nodes(threshold=0.5)
    >>> 
    >>> # Get stability summary
    >>> summary = uq.stability_summary()
    """
    
    node_ids: List[Any]
    n_samples: int
    consensus_partition: np.ndarray
    membership_entropy: np.ndarray
    p_max_membership: np.ndarray
    vi_mean: float = 0.0
    vi_std: float = 0.0
    nmi_mean: float = 1.0
    nmi_std: float = 0.0
    coassoc_matrix: Optional[np.ndarray] = None
    store_mode: str = "sketch"
    samples: Optional[List[np.ndarray]] = None
    meta: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and convert arrays."""
        n_nodes = len(self.node_ids)
        
        # Validate shapes
        if len(self.consensus_partition) != n_nodes:
            raise ValueError(
                f"consensus_partition length {len(self.consensus_partition)} != "
                f"n_nodes {n_nodes}"
            )
        if len(self.membership_entropy) != n_nodes:
            raise ValueError(
                f"membership_entropy length {len(self.membership_entropy)} != "
                f"n_nodes {n_nodes}"
            )
        if len(self.p_max_membership) != n_nodes:
            raise ValueError(
                f"p_max_membership length {len(self.p_max_membership)} != "
                f"n_nodes {n_nodes}"
            )
        
        # Ensure arrays are numpy arrays
        self.consensus_partition = np.asarray(self.consensus_partition, dtype=int)
        self.membership_entropy = np.asarray(self.membership_entropy, dtype=float)
        self.p_max_membership = np.asarray(self.p_max_membership, dtype=float)
        
        if self.coassoc_matrix is not None:
            self.coassoc_matrix = np.asarray(self.coassoc_matrix, dtype=float)
            if self.coassoc_matrix.shape != (n_nodes, n_nodes):
                raise ValueError(
                    f"coassoc_matrix shape {self.coassoc_matrix.shape} != "
                    f"({n_nodes}, {n_nodes})"
                )
    
    @property
    def n_nodes(self) -> int:
        """Number of nodes."""
        return len(self.node_ids)
    
    @property
    def n_communities(self) -> int:
        """Number of communities in consensus partition."""
        return len(np.unique(self.consensus_partition))
    
    def boundary_nodes(
        self,
        threshold: float = 0.5,
        metric: str = "entropy"
    ) -> List[Any]:
        """Get boundary nodes (high uncertainty).
        
        Parameters
        ----------
        threshold : float
            Threshold for boundary classification
        metric : str
            Metric to use: "entropy" or "confidence"
            
        Returns
        -------
        list
            Node IDs with high uncertainty
            
        Examples
        --------
        >>> boundary = uq.boundary_nodes(threshold=0.5, metric="entropy")
        """
        if metric == "entropy":
            # High entropy = boundary
            mask = self.membership_entropy > threshold
        elif metric == "confidence":
            # Low confidence = boundary
            mask = self.p_max_membership < threshold
        else:
            raise ValueError(f"Unknown metric: {metric}")
        
        indices = np.where(mask)[0]
        return [self.node_ids[i] for i in indices]
    
    def stability_summary(self) -> Dict[str, float]:
        """Get partition stability summary.
        
        Returns
        -------
        dict
            Statistics:
            - vi_mean, vi_std: Variation of information
            - nmi_mean, nmi_std: Normalized mutual information
            - n_samples: Number of samples
            - n_communities: Number of communities in consensus
            - mean_entropy: Mean node entropy
            - mean_confidence: Mean node confidence
        """
        return {
            "vi_mean": self.vi_mean,
            "vi_std": self.vi_std,
            "nmi_mean": self.nmi_mean,
            "nmi_std": self.nmi_std,
            "n_samples": self.n_samples,
            "n_communities": self.n_communities,
            "mean_entropy": float(np.mean(self.membership_entropy)),
            "mean_confidence": float(np.mean(self.p_max_membership)),
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary.
        
        Returns
        -------
        dict
            Serializable representation
        """
        result = {
            "node_ids": self.node_ids,
            "n_samples": self.n_samples,
            "n_nodes": self.n_nodes,
            "n_communities": self.n_communities,
            "consensus_partition": self.consensus_partition.tolist(),
            "membership_entropy": self.membership_entropy.tolist(),
            "p_max_membership": self.p_max_membership.tolist(),
            "vi_mean": self.vi_mean,
            "vi_std": self.vi_std,
            "nmi_mean": self.nmi_mean,
            "nmi_std": self.nmi_std,
            "store_mode": self.store_mode,
            "meta": self.meta,
        }
        
        if self.coassoc_matrix is not None:
            result["coassoc_matrix"] = self.coassoc_matrix.tolist()
        
        if self.samples is not None:
            result["samples"] = [s.tolist() for s in self.samples]
        
        return result
    
    @classmethod
    def from_samples(
        cls,
        partitions: List[np.ndarray],
        node_ids: List[Any],
        store: str = "sketch",
        sparse_topk: int = 50,
        sparse_threshold: float = 0.7,
        weights: Optional[np.ndarray] = None,
        meta: Optional[Dict[str, Any]] = None
    ) -> PartitionUQ:
        """Create PartitionUQ from partition samples.
        
        This is the main constructor that processes samples through reducers.
        
        Parameters
        ----------
        partitions : list of np.ndarray
            List of partition samples, each shape (n_nodes,)
        node_ids : list
            Ordered node identifiers
        store : str, default="sketch"
            Storage mode:
            - "none": Only summary statistics
            - "samples": Store all samples
            - "sketch": Store sparse co-assignment
        sparse_topk : int, default=50
            Top-k neighbors to keep in sparse co-assignment
        sparse_threshold : float, default=0.7
            Minimum co-assignment probability to store
        weights : np.ndarray, optional
            Per-sample weights (default: uniform)
        meta : dict, optional
            Metadata to attach
            
        Returns
        -------
        PartitionUQ
            Constructed PartitionUQ object
            
        Examples
        --------
        >>> partitions = [
        ...     np.array([0, 0, 1, 1]),
        ...     np.array([0, 0, 0, 1]),
        ... ]
        >>> uq = PartitionUQ.from_samples(
        ...     partitions=partitions,
        ...     node_ids=['A', 'B', 'C', 'D'],
        ...     store="sketch"
        ... )
        """
        if not partitions:
            raise ValueError("Cannot create PartitionUQ from empty partition list")
        
        n_nodes = len(node_ids)
        n_samples = len(partitions)
        
        # Validate all partitions
        for i, p in enumerate(partitions):
            if len(p) != n_nodes:
                raise ValueError(
                    f"Partition {i} has length {len(p)}, expected {n_nodes}"
                )
        
        # Default weights
        if weights is None:
            weights = np.ones(n_samples) / n_samples
        else:
            weights = np.asarray(weights)
            if len(weights) != n_samples:
                raise ValueError(
                    f"Weights length {len(weights)} != n_samples {n_samples}"
                )
            # Normalize
            weights = weights / np.sum(weights)
        
        # Initialize reducers
        entropy_reducer = NodeEntropyReducer(n_nodes, node_ids)
        consensus_reducer = ConsensusReducer(n_nodes)
        
        # Co-assignment reducer (conditional on store mode)
        coassoc_reducer = None
        if store in ("sketch", "samples"):
            coassoc_reducer = CoAssignmentReducer(
                n_nodes,
                sparse=(store == "sketch"),
                topk=sparse_topk,
                threshold=sparse_threshold
            )
        
        # Distance reducer for VI/NMI
        vi_reducer = PartitionDistanceReducer(metric="vi", store_samples=True)
        nmi_reducer = PartitionDistanceReducer(metric="nmi", store_samples=True)
        
        # Process samples
        for partition, weight in zip(partitions, weights):
            partition = np.asarray(partition, dtype=int)
            
            entropy_reducer.update(partition, weight)
            consensus_reducer.update(partition, weight)
            
            if coassoc_reducer is not None:
                coassoc_reducer.update(partition, weight)
            
            vi_reducer.update(partition, weight)
            nmi_reducer.update(partition, weight)
        
        # Finalize reducers
        membership_entropy = entropy_reducer.finalize()
        consensus_partition = consensus_reducer.finalize()
        _, p_max_membership = entropy_reducer.get_max_membership()
        
        coassoc_matrix = None
        if coassoc_reducer is not None:
            coassoc_matrix = coassoc_reducer.finalize()
        
        vi_stats = vi_reducer.finalize()
        nmi_stats = nmi_reducer.finalize()
        
        # Determine what to store
        samples_to_store = None
        if store == "samples":
            samples_to_store = [p.copy() for p in partitions]
        
        # Create PartitionUQ
        return cls(
            node_ids=node_ids,
            n_samples=n_samples,
            consensus_partition=consensus_partition,
            membership_entropy=membership_entropy,
            p_max_membership=p_max_membership,
            vi_mean=vi_stats["vi_mean"],
            vi_std=vi_stats["vi_std"],
            nmi_mean=nmi_stats["nmi_mean"],
            nmi_std=nmi_stats["nmi_std"],
            coassoc_matrix=coassoc_matrix,
            store_mode=store,
            samples=samples_to_store,
            meta=meta or {}
        )
    
    @classmethod
    def from_uq_result(
        cls,
        uq_result,
        node_ids: List[Any],
        meta: Optional[Dict[str, Any]] = None
    ) -> PartitionUQ:
        """Create PartitionUQ from UQResult (UQ spine integration).
        
        This factory method creates a PartitionUQ from a UQResult produced
        by run_uq() with the appropriate reducers. It expects:
        - NodeMarginalReducer output (required)
        - StabilityReducer output (optional)
        
        Note: Co-assignment matrix computation
        --------------------------------------
        By default, the co-assignment matrix is NOT computed when using the
        UQ spine approach. This is intentional for memory efficiency. If you
        need the co-assignment matrix, you must:
        1. Add CoAssignmentReducer to your UQPlan.reducers list
        2. Extract the result from uq_result.reducer_outputs['CoAssignmentReducer']
        3. Manually set it on the PartitionUQ object after construction
        
        Parameters
        ----------
        uq_result : UQResult
            Result from run_uq() execution
        node_ids : list
            Ordered node identifiers
        meta : dict, optional
            Additional metadata to attach
            
        Returns
        -------
        PartitionUQ
            Constructed PartitionUQ object
            
        Examples
        --------
        >>> from py3plex.uncertainty.runner import run_uq
        >>> from py3plex.uncertainty.plan import UQPlan
        >>> from py3plex.uncertainty.partition_reducers import NodeMarginalReducer
        >>> 
        >>> # Create plan with reducers
        >>> marginal_reducer = NodeMarginalReducer(n_nodes=4, node_ids=['A', 'B', 'C', 'D'])
        >>> plan = UQPlan(
        ...     base_callable=my_algorithm,
        ...     strategy="seed",
        ...     noise_model=NoNoise(),
        ...     n_samples=50,
        ...     seed=42,
        ...     reducers=[marginal_reducer]
        ... )
        >>> 
        >>> # Execute UQ
        >>> result = run_uq(plan, network)
        >>> 
        >>> # Create PartitionUQ from result
        >>> partition_uq = PartitionUQ.from_uq_result(
        ...     uq_result=result,
        ...     node_ids=['A', 'B', 'C', 'D']
        ... )
        """
        from py3plex.uncertainty.plan import UQResult
        
        if not isinstance(uq_result, UQResult):
            raise TypeError(f"Expected UQResult, got {type(uq_result)}")
        
        n_nodes = len(node_ids)
        
        # Extract marginal reducer output
        if 'NodeMarginalReducer' not in uq_result.reducer_outputs:
            raise ValueError(
                "UQResult must contain NodeMarginalReducer output. "
                "Ensure NodeMarginalReducer was included in UQPlan.reducers"
            )
        
        marginal_output = uq_result.reducer_outputs['NodeMarginalReducer']
        
        # Extract node-level statistics
        entropy = marginal_output['entropy']
        p_max = marginal_output['p_max']
        consensus = marginal_output['consensus_labels']
        
        # Extract stability statistics if available
        vi_mean = 0.0
        vi_std = 0.0
        nmi_mean = 1.0
        nmi_std = 0.0
        
        if 'StabilityReducer' in uq_result.reducer_outputs:
            stability_output = uq_result.reducer_outputs['StabilityReducer']
            vi_mean = stability_output.get('vi_mean', 0.0)
            vi_std = stability_output.get('vi_std', 0.0)
            nmi_mean = stability_output.get('nmi_mean', 1.0)
            nmi_std = stability_output.get('nmi_std', 0.0)
        
        # Get storage mode from provenance
        store_mode = "sketch"
        if 'execution' in uq_result.provenance:
            store_mode = uq_result.provenance['execution'].get('storage_mode', 'sketch')
        
        # Merge metadata
        merged_meta = meta or {}
        if uq_result.provenance:
            merged_meta['provenance'] = uq_result.provenance
        
        # Create PartitionUQ
        return cls(
            node_ids=node_ids,
            n_samples=uq_result.n_samples,
            consensus_partition=consensus,
            membership_entropy=entropy,
            p_max_membership=p_max,
            vi_mean=vi_mean,
            vi_std=vi_std,
            nmi_mean=nmi_mean,
            nmi_std=nmi_std,
            coassoc_matrix=None,  # Not computed by default
            store_mode=store_mode,
            samples=uq_result.samples,
            meta=merged_meta
        )
    
    def node_summary(self, node_id: Any) -> Dict[str, Any]:
        """Get UQ summary for a specific node.
        
        Parameters
        ----------
        node_id : any
            Node identifier
            
        Returns
        -------
        dict
            Summary with keys:
            - consensus: Consensus community label
            - entropy: Node entropy
            - confidence: Maximum membership probability
            - coassoc_neighbors: Top co-associated nodes (if available)
        """
        if node_id not in self.node_ids:
            raise ValueError(f"Node {node_id} not found")
        
        idx = self.node_ids.index(node_id)
        
        summary = {
            "consensus": int(self.consensus_partition[idx]),
            "entropy": float(self.membership_entropy[idx]),
            "confidence": float(self.p_max_membership[idx]),
        }
        
        if self.coassoc_matrix is not None:
            # Get top co-associated neighbors
            coassoc = self.coassoc_matrix[idx]
            # Exclude self
            coassoc_copy = coassoc.copy()
            coassoc_copy[idx] = 0.0
            
            # Get top-10
            top_indices = np.argsort(coassoc_copy)[::-1][:10]
            top_neighbors = [
                (self.node_ids[i], float(coassoc[i]))
                for i in top_indices
                if coassoc[i] > 0
            ]
            
            summary["coassoc_neighbors"] = top_neighbors
        
        return summary
