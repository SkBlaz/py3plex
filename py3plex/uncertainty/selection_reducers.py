"""Reducers for SelectionUQ.

This module provides online reducers that aggregate selection outputs across
multiple UQ samples without storing all raw data.
"""

from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .selection_types import SelectionOutput


class SelectionReducer(ABC):
    """Base class for selection reducers.
    
    Reducers process SelectionOutput samples incrementally and compute
    summary statistics without storing all samples.
    """
    
    @abstractmethod
    def update(self, selection: SelectionOutput) -> None:
        """Update reducer with a new selection sample.
        
        Parameters
        ----------
        selection : SelectionOutput
            A single selection query result
        """
        pass
    
    @abstractmethod
    def finalize(self) -> Dict[str, Any]:
        """Compute final statistics.
        
        Returns
        -------
        dict
            Summary statistics computed from all updates
        """
        pass


class InclusionReducer(SelectionReducer):
    """Track item inclusion probabilities across samples.
    
    Maintains count of how many times each item appears in selections.
    
    Attributes
    ----------
    n_samples : int
        Total number of samples processed
    item_counts : dict
        Count of appearances per item
    """
    
    def __init__(self):
        self.n_samples = 0
        self.item_counts = defaultdict(int)
    
    def update(self, selection: SelectionOutput) -> None:
        """Update with a new selection."""
        self.n_samples += 1
        for item in selection.items:
            self.item_counts[item] += 1
    
    def finalize(self) -> Dict[str, Any]:
        """Compute inclusion probabilities.
        
        Returns
        -------
        dict
            Keys:
            - present_prob : dict mapping item -> probability
            - n_samples : int
            - items_universe : list of all items seen
        """
        if self.n_samples == 0:
            return {
                "present_prob": {},
                "n_samples": 0,
                "items_universe": [],
            }
        
        present_prob = {
            item: count / self.n_samples 
            for item, count in self.item_counts.items()
        }
        
        return {
            "present_prob": present_prob,
            "n_samples": self.n_samples,
            "items_universe": list(self.item_counts.keys()),
        }


class SizeReducer(SelectionReducer):
    """Track selection set size distribution.
    
    Maintains online mean/variance of selection size.
    
    Attributes
    ----------
    n_samples : int
        Number of samples
    size_sum : float
        Sum of sizes
    size_sq_sum : float
        Sum of squared sizes
    sizes : list, optional
        Raw sizes if storing samples
    """
    
    def __init__(self, store_samples: bool = False):
        self.n_samples = 0
        self.size_sum = 0.0
        self.size_sq_sum = 0.0
        self.store_samples = store_samples
        self.sizes = [] if store_samples else None
    
    def update(self, selection: SelectionOutput) -> None:
        """Update with a new selection."""
        size = len(selection.items)
        self.n_samples += 1
        self.size_sum += size
        self.size_sq_sum += size ** 2
        if self.store_samples:
            self.sizes.append(size)
    
    def finalize(self) -> Dict[str, Any]:
        """Compute size statistics.
        
        Returns
        -------
        dict
            Keys:
            - mean : float
            - std : float
            - min : int (if samples stored)
            - max : int (if samples stored)
            - q05 : float (if samples stored)
            - q95 : float (if samples stored)
        """
        if self.n_samples == 0:
            return {"mean": 0.0, "std": 0.0}
        
        mean = self.size_sum / self.n_samples
        variance = (self.size_sq_sum / self.n_samples) - mean ** 2
        std = np.sqrt(max(0, variance))
        
        result = {
            "mean": float(mean),
            "std": float(std),
        }
        
        if self.store_samples and self.sizes:
            result["min"] = int(min(self.sizes))
            result["max"] = int(max(self.sizes))
            result["q05"] = float(np.quantile(self.sizes, 0.05))
            result["q95"] = float(np.quantile(self.sizes, 0.95))
        
        return result


class StabilityReducer(SelectionReducer):
    """Track stability via Jaccard similarity to consensus selection.
    
    Maintains a running consensus and computes Jaccard similarities.
    
    Attributes
    ----------
    n_samples : int
        Number of samples
    item_counts : dict
        Count of appearances per item
    jaccard_sum : float
        Sum of Jaccard similarities
    jaccard_sq_sum : float
        Sum of squared Jaccard similarities
    jaccards : list, optional
        Raw Jaccard values if storing samples
    """
    
    def __init__(self, consensus_threshold: float = 0.5, store_samples: bool = False):
        self.n_samples = 0
        self.item_counts = defaultdict(int)
        self.consensus_threshold = consensus_threshold
        self.jaccard_sum = 0.0
        self.jaccard_sq_sum = 0.0
        self.store_samples = store_samples
        self.jaccards = [] if store_samples else None
        self._selections_cache = []  # Store selections for deferred Jaccard computation
    
    def update(self, selection: SelectionOutput) -> None:
        """Update with a new selection."""
        self.n_samples += 1
        for item in selection.items:
            self.item_counts[item] += 1
        
        # Store selection for later Jaccard computation
        self._selections_cache.append(set(selection.items))
    
    def _compute_consensus(self) -> set:
        """Compute consensus selection based on inclusion threshold."""
        if self.n_samples == 0:
            return set()
        
        threshold_count = self.consensus_threshold * self.n_samples
        consensus = {
            item for item, count in self.item_counts.items()
            if count >= threshold_count
        }
        return consensus
    
    def finalize(self) -> Dict[str, Any]:
        """Compute stability statistics.
        
        Returns
        -------
        dict
            Keys:
            - jaccard_mean : float
            - jaccard_std : float
            - q05 : float (if samples stored)
            - q95 : float (if samples stored)
        """
        if self.n_samples == 0:
            return {"jaccard_mean": 1.0, "jaccard_std": 0.0}
        
        # Compute consensus selection
        consensus = self._compute_consensus()
        
        # Compute Jaccard with each selection vs consensus
        jaccards = []
        for selection_set in self._selections_cache:
            if len(consensus) == 0 and len(selection_set) == 0:
                jaccard = 1.0
            elif len(consensus) == 0 or len(selection_set) == 0:
                jaccard = 0.0
            else:
                intersection = len(consensus & selection_set)
                union = len(consensus | selection_set)
                jaccard = intersection / union if union > 0 else 0.0
            
            jaccards.append(jaccard)
            self.jaccard_sum += jaccard
            self.jaccard_sq_sum += jaccard ** 2
            if self.store_samples:
                self.jaccards.append(jaccard)
        
        mean = self.jaccard_sum / self.n_samples
        variance = (self.jaccard_sq_sum / self.n_samples) - mean ** 2
        std = np.sqrt(max(0, variance))
        
        result = {
            "jaccard_mean": float(mean),
            "jaccard_std": float(std),
            "consensus_size": len(consensus),
        }
        
        if self.store_samples and self.jaccards:
            result["q05"] = float(np.quantile(self.jaccards, 0.05))
            result["q95"] = float(np.quantile(self.jaccards, 0.95))
        
        return result


class RankReducer(SelectionReducer):
    """Track rank statistics for items when ranking is available.
    
    Maintains online mean/variance of ranks per item, and p_in_topk.
    
    Attributes
    ----------
    n_samples : int
        Number of samples
    k : int, optional
        Top-k parameter if relevant
    rank_sums : dict
        Sum of ranks per item (when present)
    rank_sq_sums : dict
        Sum of squared ranks per item
    rank_counts : dict
        Count of samples where item had a rank
    topk_counts : dict
        Count of times item was in top-k
    rank_samples : dict, optional
        Raw rank arrays per item if storing samples
    """
    
    def __init__(self, k: Optional[int] = None, store_samples: bool = False):
        self.n_samples = 0
        self.k = k
        self.rank_sums = defaultdict(float)
        self.rank_sq_sums = defaultdict(float)
        self.rank_counts = defaultdict(int)
        self.topk_counts = defaultdict(int)
        self.store_samples = store_samples
        self.rank_samples = defaultdict(list) if store_samples else None
    
    def update(self, selection: SelectionOutput) -> None:
        """Update with a new selection."""
        if selection.ranks is None:
            return  # No ranks to process
        
        self.n_samples += 1
        
        # Update k if not set
        if self.k is None and selection.k is not None:
            self.k = selection.k
        
        for item, rank in selection.ranks.items():
            self.rank_sums[item] += rank
            self.rank_sq_sums[item] += rank ** 2
            self.rank_counts[item] += 1
            
            if self.k is not None and rank <= self.k:
                self.topk_counts[item] += 1
            
            if self.store_samples:
                self.rank_samples[item].append(rank)
    
    def finalize(self) -> Dict[str, Any]:
        """Compute rank statistics.
        
        Returns
        -------
        dict
            Keys per item:
            - rank_mean : dict
            - rank_std : dict
            - p_in_topk : dict (if k is set)
            - rank_ci_low : dict (if samples stored)
            - rank_ci_high : dict (if samples stored)
        """
        if self.n_samples == 0:
            return {
                "rank_mean": {},
                "rank_std": {},
                "p_in_topk": {},
            }
        
        rank_mean = {}
        rank_std = {}
        p_in_topk = {}
        rank_ci_low = {}
        rank_ci_high = {}
        
        for item in self.rank_counts:
            count = self.rank_counts[item]
            if count == 0:
                continue
            
            # Conditional rank statistics (only when item was present)
            mean = self.rank_sums[item] / count
            variance = (self.rank_sq_sums[item] / count) - mean ** 2
            std = np.sqrt(max(0, variance))
            
            rank_mean[item] = float(mean)
            rank_std[item] = float(std)
            
            # p_in_topk: probability item appears in top-k
            # This is across ALL samples, not just when present
            if self.k is not None:
                p_in_topk[item] = self.topk_counts[item] / self.n_samples
            
            # CI from empirical quantiles if samples stored
            if self.store_samples and item in self.rank_samples:
                ranks_arr = np.array(self.rank_samples[item])
                if len(ranks_arr) > 0:
                    rank_ci_low[item] = float(np.quantile(ranks_arr, 0.025))
                    rank_ci_high[item] = float(np.quantile(ranks_arr, 0.975))
        
        result = {
            "rank_mean": rank_mean,
            "rank_std": rank_std,
        }
        
        if self.k is not None:
            result["p_in_topk"] = p_in_topk
        
        if self.store_samples:
            result["rank_ci_low"] = rank_ci_low
            result["rank_ci_high"] = rank_ci_high
        
        return result


class TopKOverlapReducer(SelectionReducer):
    """Track overlap between top-k sets across samples.
    
    Computes expected overlap size and distribution.
    
    Attributes
    ----------
    n_pairs : int
        Number of pairs compared
    overlap_sum : float
        Sum of overlap sizes
    overlap_sq_sum : float
        Sum of squared overlap sizes
    overlaps : list, optional
        Raw overlap values if storing samples
    """
    
    def __init__(self, store_samples: bool = False):
        self.n_pairs = 0
        self.overlap_sum = 0.0
        self.overlap_sq_sum = 0.0
        self.store_samples = store_samples
        self.overlaps = [] if store_samples else None
        self._topk_sets = []  # Cache top-k sets
    
    def update(self, selection: SelectionOutput) -> None:
        """Update with a new selection."""
        if selection.k is not None:
            # Store top-k items (first k items by rank)
            if selection.ranks:
                sorted_items = sorted(selection.ranks.items(), key=lambda x: x[1])
                topk_items = {item for item, rank in sorted_items[:selection.k]}
            else:
                topk_items = set(selection.items[:selection.k])
            
            self._topk_sets.append(topk_items)
    
    def finalize(self) -> Dict[str, Any]:
        """Compute top-k overlap statistics.
        
        Returns
        -------
        dict
            Keys:
            - overlap_mean : float
            - overlap_std : float
            - q05 : float (if samples stored)
            - q95 : float (if samples stored)
        """
        if len(self._topk_sets) < 2:
            return {"overlap_mean": 0.0, "overlap_std": 0.0}
        
        # Compute pairwise overlaps
        overlaps = []
        for i in range(len(self._topk_sets)):
            for j in range(i + 1, len(self._topk_sets)):
                overlap = len(self._topk_sets[i] & self._topk_sets[j])
                overlaps.append(overlap)
                self.n_pairs += 1
                self.overlap_sum += overlap
                self.overlap_sq_sum += overlap ** 2
                if self.store_samples:
                    self.overlaps.append(overlap)
        
        mean = self.overlap_sum / self.n_pairs if self.n_pairs > 0 else 0.0
        variance = (self.overlap_sq_sum / self.n_pairs - mean ** 2) if self.n_pairs > 0 else 0.0
        std = np.sqrt(max(0, variance))
        
        result = {
            "overlap_mean": float(mean),
            "overlap_std": float(std),
        }
        
        if self.store_samples and self.overlaps:
            result["q05"] = float(np.quantile(self.overlaps, 0.05))
            result["q95"] = float(np.quantile(self.overlaps, 0.95))
        
        return result


class GroupedReducer(SelectionReducer):
    """Wrapper to maintain separate reducers per group.
    
    Parameters
    ----------
    reducer_class : type
        Reducer class to instantiate per group
    reducer_kwargs : dict, optional
        Keyword arguments for reducer instantiation
    """
    
    def __init__(self, reducer_class: type, reducer_kwargs: Optional[Dict] = None):
        self.reducer_class = reducer_class
        self.reducer_kwargs = reducer_kwargs or {}
        self.reducers = {}  # group_key -> reducer instance
    
    def update(self, selection: SelectionOutput) -> None:
        """Update the appropriate grouped reducer."""
        group_key = selection.group_key or ()
        
        if group_key not in self.reducers:
            self.reducers[group_key] = self.reducer_class(**self.reducer_kwargs)
        
        self.reducers[group_key].update(selection)
    
    def finalize(self) -> Dict[Tuple, Dict[str, Any]]:
        """Finalize all group reducers.
        
        Returns
        -------
        dict
            Maps group_key -> reducer results
        """
        return {
            group_key: reducer.finalize()
            for group_key, reducer in self.reducers.items()
        }
