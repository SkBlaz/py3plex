"""SelectionUQ: Canonical uncertainty quantification for discrete selections.

This module provides the SelectionUQ class - the canonical result type for
uncertainty quantification over discrete query outputs (top-k rankings,
filtered selections).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .ci_utils import binomial_proportion_ci


@dataclass
class SelectionUQ:
    """Uncertainty quantification for selection queries.
    
    This class stores canonical UQ outputs for selections (top-k, filters)
    without requiring storage of all samples.
    
    Attributes
    ----------
    n_samples : int
        Number of selection samples used
    items_universe : list
        All items seen across samples
    samples_seen : int
        Effective number of samples (same as n_samples usually)
    present_prob : dict
        Inclusion probability per item: Pr(item ∈ result)
    present_ci_low : dict, optional
        Lower CI bound for present_prob
    present_ci_high : dict, optional
        Upper CI bound for present_prob
    size_stats : dict
        Selection set size statistics (mean, std, quantiles)
    stability_stats : dict
        Stability metrics (Jaccard vs consensus)
    rank_mean : dict, optional
        Mean rank per item (if ranking exists)
    rank_std : dict, optional
        Std of rank per item
    rank_ci_low : dict, optional
        Lower CI bound for rank
    rank_ci_high : dict, optional
        Upper CI bound for rank
    p_in_topk : dict, optional
        Pr(rank ≤ k) per item
    topk_overlap_stats : dict, optional
        Top-k overlap statistics
    consensus_items : set
        Items in consensus selection (present_prob ≥ threshold)
    borderline_items : list
        Items with uncertain inclusion (near threshold)
    target : str
        Type of items: "nodes" or "edges"
    k : int, optional
        Top-k parameter if relevant
    store_mode : str
        Storage mode: "none", "sketch", or "samples"
    ci_method : str
        Method used for confidence intervals
    meta : dict
        Additional metadata (method, noise_model, provenance)
        
    Examples
    --------
    >>> from py3plex.uncertainty.selection_uq import SelectionUQ
    >>> # Created internally by execute_selection_uq
    >>> uq = SelectionUQ(...)
    >>> 
    >>> # Access inclusion probabilities
    >>> print(uq.present_prob)
    >>> 
    >>> # Check borderline items
    >>> print(uq.borderline_items)
    >>> 
    >>> # Get summary
    >>> summary = uq.summary()
    """
    
    n_samples: int
    items_universe: List[Any]
    samples_seen: int
    present_prob: Dict[Any, float]
    present_ci_low: Dict[Any, float] = field(default_factory=dict)
    present_ci_high: Dict[Any, float] = field(default_factory=dict)
    size_stats: Dict[str, float] = field(default_factory=dict)
    stability_stats: Dict[str, float] = field(default_factory=dict)
    rank_mean: Optional[Dict[Any, float]] = None
    rank_std: Optional[Dict[Any, float]] = None
    rank_ci_low: Optional[Dict[Any, float]] = None
    rank_ci_high: Optional[Dict[Any, float]] = None
    p_in_topk: Optional[Dict[Any, float]] = None
    topk_overlap_stats: Optional[Dict[str, float]] = None
    consensus_items: set = field(default_factory=set)
    borderline_items: List[Any] = field(default_factory=list)
    target: str = "nodes"
    k: Optional[int] = None
    store_mode: str = "sketch"
    ci_method: str = "wilson"
    meta: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and compute derived attributes."""
        if self.n_samples <= 0:
            raise ValueError(f"n_samples must be positive, got {self.n_samples}")
        
        # Ensure items_universe is list
        if not isinstance(self.items_universe, list):
            self.items_universe = list(self.items_universe)
        
        # Validate probabilities
        for item, prob in self.present_prob.items():
            if not 0 <= prob <= 1:
                raise ValueError(f"Invalid probability for item {item}: {prob}")
    
    @classmethod
    def from_reducers(
        cls,
        inclusion_result: Dict[str, Any],
        size_result: Dict[str, Any],
        stability_result: Dict[str, Any],
        rank_result: Optional[Dict[str, Any]] = None,
        topk_overlap_result: Optional[Dict[str, Any]] = None,
        consensus_threshold: float = 0.5,
        borderline_epsilon: float = 0.1,
        ci_method: str = "wilson",
        ci_alpha: float = 0.05,
        target: str = "nodes",
        k: Optional[int] = None,
        store_mode: str = "sketch",
        meta: Optional[Dict[str, Any]] = None,
    ) -> SelectionUQ:
        """Construct SelectionUQ from reducer results.
        
        Parameters
        ----------
        inclusion_result : dict
            Output from InclusionReducer.finalize()
        size_result : dict
            Output from SizeReducer.finalize()
        stability_result : dict
            Output from StabilityReducer.finalize()
        rank_result : dict, optional
            Output from RankReducer.finalize()
        topk_overlap_result : dict, optional
            Output from TopKOverlapReducer.finalize()
        consensus_threshold : float
            Threshold for consensus inclusion (default: 0.5)
        borderline_epsilon : float
            Tolerance for borderline detection (default: 0.1)
        ci_method : str
            CI method: "wilson" or "clopper-pearson"
        ci_alpha : float
            Significance level for CI (default: 0.05)
        target : str
            "nodes" or "edges"
        k : int, optional
            Top-k parameter
        store_mode : str
            Storage mode used
        meta : dict, optional
            Additional metadata
            
        Returns
        -------
        SelectionUQ
            Constructed instance
        """
        n_samples = inclusion_result["n_samples"]
        items_universe = inclusion_result["items_universe"]
        present_prob = inclusion_result["present_prob"]
        
        # Compute CIs for present_prob
        present_ci_low = {}
        present_ci_high = {}
        
        for item, prob in present_prob.items():
            successes = int(round(prob * n_samples))
            ci_low, ci_high = binomial_proportion_ci(
                successes, n_samples, alpha=ci_alpha, method=ci_method
            )
            present_ci_low[item] = ci_low
            present_ci_high[item] = ci_high
        
        # Compute consensus selection
        consensus_items = {
            item for item, prob in present_prob.items()
            if prob >= consensus_threshold
        }
        
        # Detect borderline items
        borderline_items = [
            item for item, prob in present_prob.items()
            if abs(prob - consensus_threshold) < borderline_epsilon
        ]
        
        # Extract rank stats if available
        rank_mean = None
        rank_std = None
        rank_ci_low = None
        rank_ci_high = None
        p_in_topk = None
        
        if rank_result is not None:
            rank_mean = rank_result.get("rank_mean", {})
            rank_std = rank_result.get("rank_std", {})
            rank_ci_low = rank_result.get("rank_ci_low")
            rank_ci_high = rank_result.get("rank_ci_high")
            p_in_topk = rank_result.get("p_in_topk")
        
        return cls(
            n_samples=n_samples,
            items_universe=items_universe,
            samples_seen=n_samples,
            present_prob=present_prob,
            present_ci_low=present_ci_low,
            present_ci_high=present_ci_high,
            size_stats=size_result,
            stability_stats=stability_result,
            rank_mean=rank_mean,
            rank_std=rank_std,
            rank_ci_low=rank_ci_low,
            rank_ci_high=rank_ci_high,
            p_in_topk=p_in_topk,
            topk_overlap_stats=topk_overlap_result,
            consensus_items=consensus_items,
            borderline_items=borderline_items,
            target=target,
            k=k,
            store_mode=store_mode,
            ci_method=ci_method,
            meta=meta or {},
        )
    
    def summary(self) -> Dict[str, Any]:
        """Generate human-readable summary.
        
        Returns
        -------
        dict
            Compact summary with key statistics
        """
        summary = {
            "n_samples": self.n_samples,
            "n_items_universe": len(self.items_universe),
            "target": self.target,
            "set_size": self.size_stats,
            "stability": {
                "jaccard_mean": self.stability_stats.get("jaccard_mean"),
                "jaccard_std": self.stability_stats.get("jaccard_std"),
            },
            "consensus": {
                "threshold": 0.5,  # Default from meta if available
                "size": len(self.consensus_items),
                "items_preview": list(self.consensus_items)[:10],
            },
            "borderline": {
                "count": len(self.borderline_items),
                "items_preview": self.borderline_items[:10],
            },
        }
        
        if self.k is not None:
            summary["topk"] = {
                "k": self.k,
                "overlap": self.topk_overlap_stats,
            }
        
        return summary
    
    def to_pandas(self, expand: bool = True) -> pd.DataFrame:
        """Convert to tidy pandas DataFrame.
        
        Parameters
        ----------
        expand : bool
            If True, include all UQ columns (probabilities, CIs, ranks)
            
        Returns
        -------
        pd.DataFrame
            Tidy table with one row per item
        """
        data = []
        
        for item in self.items_universe:
            row = {
                "item": item,
                "present_prob": self.present_prob.get(item, 0.0),
            }
            
            if expand:
                row["present_ci_low"] = self.present_ci_low.get(item, np.nan)
                row["present_ci_high"] = self.present_ci_high.get(item, np.nan)
                
                if self.rank_mean is not None:
                    row["rank_mean"] = self.rank_mean.get(item, np.nan)
                    row["rank_std"] = self.rank_std.get(item, np.nan)
                    
                    if self.rank_ci_low is not None:
                        row["rank_ci_low"] = self.rank_ci_low.get(item, np.nan)
                        row["rank_ci_high"] = self.rank_ci_high.get(item, np.nan)
                
                if self.p_in_topk is not None:
                    row["p_in_topk"] = self.p_in_topk.get(item, 0.0)
            
            data.append(row)
        
        return pd.DataFrame(data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary.
        
        Returns
        -------
        dict
            Serializable representation
        """
        result = {
            "n_samples": self.n_samples,
            "samples_seen": self.samples_seen,
            "items_universe": self.items_universe,
            "present_prob": self.present_prob,
            "present_ci_low": self.present_ci_low,
            "present_ci_high": self.present_ci_high,
            "size_stats": self.size_stats,
            "stability_stats": self.stability_stats,
            "consensus_items": list(self.consensus_items),
            "borderline_items": self.borderline_items,
            "target": self.target,
            "k": self.k,
            "store_mode": self.store_mode,
            "ci_method": self.ci_method,
            "meta": self.meta,
        }
        
        if self.rank_mean is not None:
            result["rank_mean"] = self.rank_mean
            result["rank_std"] = self.rank_std
            
            if self.rank_ci_low is not None:
                result["rank_ci_low"] = self.rank_ci_low
                result["rank_ci_high"] = self.rank_ci_high
        
        if self.p_in_topk is not None:
            result["p_in_topk"] = self.p_in_topk
        
        if self.topk_overlap_stats is not None:
            result["topk_overlap_stats"] = self.topk_overlap_stats
        
        return result
    
    def get_top_stable(self, n: int = 10) -> List[Tuple[Any, float]]:
        """Get top n most stable items by present_prob.
        
        Parameters
        ----------
        n : int
            Number of items to return
            
        Returns
        -------
        list of (item, present_prob)
            Sorted by present_prob descending
        """
        sorted_items = sorted(
            self.present_prob.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_items[:n]
    
    def get_uncertain(self, threshold: float = 0.2) -> List[Tuple[Any, float]]:
        """Get items with uncertain inclusion (low present_prob).
        
        Parameters
        ----------
        threshold : float
            Items with present_prob < threshold
            
        Returns
        -------
        list of (item, present_prob)
            Sorted by present_prob ascending
        """
        uncertain = [
            (item, prob) for item, prob in self.present_prob.items()
            if prob < threshold
        ]
        uncertain.sort(key=lambda x: x[1])
        return uncertain
