"""Predicates for robustness contracts.

Predicates define what it means for a conclusion to be "stable" under
perturbations. Each predicate evaluates curves of metrics over perturbation
strengths and returns pass/fail with evidence.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np


class Predicate(ABC):
    """Base class for contract predicates.
    
    Predicates evaluate stability by comparing baseline results with
    perturbed results across a grid of perturbation strengths.
    """
    
    @abstractmethod
    def evaluate(
        self,
        baseline: Any,
        perturbed_results: List[Tuple[float, Any]],
        domain: str = "all_p_leq_pmax"
    ) -> Tuple[bool, Dict[str, Any]]:
        """Evaluate predicate over perturbation curve.
        
        Args:
            baseline: Baseline query result (unperturbed)
            perturbed_results: List of (p, result) pairs where p is perturbation strength
            domain: Domain semantics ("all_p_leq_pmax", "exists_p_leq_pmax", etc.)
            
        Returns:
            Tuple of (passed: bool, evidence: dict)
        """
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Serialize predicate to dictionary."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get predicate name for display."""
        pass


@dataclass
class JaccardAtK(Predicate):
    """Jaccard similarity for top-k set stability.
    
    Evaluates Jaccard(baseline_top_k, perturbed_top_k) >= threshold
    for all perturbation strengths in the domain.
    
    Attributes:
        k: Size of top-k set
        threshold: Minimum Jaccard similarity (0.0 to 1.0)
        metric: Metric name to rank by (e.g., "pagerank", "degree")
    """
    
    k: int
    threshold: float = 0.85
    metric: Optional[str] = None
    
    def __post_init__(self):
        """Validate parameters."""
        if self.k <= 0:
            raise ValueError(f"k must be positive, got {self.k}")
        if not (0.0 <= self.threshold <= 1.0):
            raise ValueError(f"threshold must be in [0, 1], got {self.threshold}")
    
    def evaluate(
        self,
        baseline: Any,
        perturbed_results: List[Tuple[float, Any]],
        domain: str = "all_p_leq_pmax"
    ) -> Tuple[bool, Dict[str, Any]]:
        """Evaluate Jaccard similarity for top-k sets.
        
        Args:
            baseline: QueryResult with items ranked by metric
            perturbed_results: List of (p, QueryResult) pairs
            domain: Domain semantics
            
        Returns:
            (passed, evidence) where evidence contains jaccard scores per p
        """
        # Extract baseline top-k
        baseline_top_k = self._extract_top_k(baseline)
        if baseline_top_k is None or len(baseline_top_k) < self.k:
            return False, {
                "error": "insufficient_baseline",
                "baseline_size": len(baseline_top_k) if baseline_top_k else 0,
                "required_k": self.k
            }
        
        baseline_set = set(baseline_top_k[:self.k])
        
        # Compute Jaccard for each perturbation strength
        jaccard_scores = {}
        for p, result in perturbed_results:
            perturbed_top_k = self._extract_top_k(result)
            if perturbed_top_k is None or len(perturbed_top_k) == 0:
                jaccard_scores[p] = 0.0
                continue
            
            perturbed_set = set(perturbed_top_k[:min(self.k, len(perturbed_top_k))])
            intersection = baseline_set & perturbed_set
            union = baseline_set | perturbed_set
            
            if len(union) == 0:
                jaccard_scores[p] = 1.0  # Both empty
            else:
                jaccard_scores[p] = len(intersection) / len(union)
        
        # Evaluate domain semantics
        if domain == "all_p_leq_pmax":
            passed = all(score >= self.threshold for score in jaccard_scores.values())
        elif domain == "exists_p_leq_pmax":
            passed = any(score >= self.threshold for score in jaccard_scores.values())
        else:
            passed = False
        
        evidence = {
            "predicate": "jaccard_at_k",
            "k": self.k,
            "threshold": self.threshold,
            "jaccard_scores": jaccard_scores,
            "min_jaccard": min(jaccard_scores.values()) if jaccard_scores else None,
            "mean_jaccard": np.mean(list(jaccard_scores.values())) if jaccard_scores else None,
            "passed": passed,
            "domain": domain,
        }
        
        return passed, evidence
    
    def _extract_top_k(self, result: Any) -> Optional[List]:
        """Extract ordered list of items from QueryResult.
        
        Handles both QueryResult objects and raw lists/DataFrames.
        """
        if result is None:
            return None
        
        # Try QueryResult interface
        if hasattr(result, "to_pandas"):
            df = result.to_pandas()
            if df is None or len(df) == 0:
                return None
            
            # Get node/edge identifiers (first column or tuple of (node, layer))
            if "node" in df.columns:
                items = df["node"].tolist()
            elif "edge" in df.columns:
                items = df["edge"].tolist()
            elif len(df.columns) > 0:
                items = df[df.columns[0]].tolist()
            else:
                return None
            
            return items
        
        # Try list-like
        if isinstance(result, list):
            return result
        
        # Try DataFrame-like
        if hasattr(result, "iloc"):
            if len(result) == 0:
                return None
            if "node" in result.columns:
                return result["node"].tolist()
            return result.iloc[:, 0].tolist()
        
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "type": "jaccard_at_k",
            "k": self.k,
            "threshold": self.threshold,
            "metric": self.metric,
        }
    
    def get_name(self) -> str:
        """Get predicate name."""
        return f"Jaccard@{self.k} >= {self.threshold}"


@dataclass
class KendallTau(Predicate):
    """Kendall's tau rank correlation for ranking stability.
    
    Evaluates tau(baseline_ranking, perturbed_ranking) >= threshold
    for all perturbation strengths in the domain.
    
    Attributes:
        threshold: Minimum Kendall's tau (-1.0 to 1.0)
        tie_policy: How to handle ties ("break", "undefined")
        metric: Metric name to rank by
    """
    
    threshold: float = 0.8
    tie_policy: str = "break"
    metric: Optional[str] = None
    
    def __post_init__(self):
        """Validate parameters."""
        if not (-1.0 <= self.threshold <= 1.0):
            raise ValueError(f"threshold must be in [-1, 1], got {self.threshold}")
        if self.tie_policy not in ("break", "undefined"):
            raise ValueError(f"tie_policy must be 'break' or 'undefined', got {self.tie_policy}")
    
    def evaluate(
        self,
        baseline: Any,
        perturbed_results: List[Tuple[float, Any]],
        domain: str = "all_p_leq_pmax"
    ) -> Tuple[bool, Dict[str, Any]]:
        """Evaluate Kendall's tau for rankings.
        
        Args:
            baseline: QueryResult with ranked items
            perturbed_results: List of (p, QueryResult) pairs
            domain: Domain semantics
            
        Returns:
            (passed, evidence) where evidence contains tau scores per p
        """
        from scipy.stats import kendalltau
        
        # Extract baseline ranking
        baseline_ranking = self._extract_ranking(baseline)
        if baseline_ranking is None or len(baseline_ranking) < 2:
            return False, {
                "error": "insufficient_baseline",
                "baseline_size": len(baseline_ranking) if baseline_ranking else 0
            }
        
        # Check for excessive ties
        if self._has_excessive_ties(baseline_ranking) and self.tie_policy == "undefined":
            return False, {
                "error": "metric_undefined",
                "reason": "excessive_ties",
                "tie_policy": self.tie_policy
            }
        
        # Compute Kendall's tau for each perturbation strength
        tau_scores = {}
        for p, result in perturbed_results:
            perturbed_ranking = self._extract_ranking(result)
            if perturbed_ranking is None or len(perturbed_ranking) < 2:
                tau_scores[p] = 0.0
                continue
            
            # Align rankings by common items
            common_items = set(baseline_ranking.keys()) & set(perturbed_ranking.keys())
            if len(common_items) < 2:
                tau_scores[p] = 0.0
                continue
            
            baseline_ranks = [baseline_ranking[item] for item in sorted(common_items)]
            perturbed_ranks = [perturbed_ranking[item] for item in sorted(common_items)]
            
            tau, _ = kendalltau(baseline_ranks, perturbed_ranks)
            tau_scores[p] = tau if not np.isnan(tau) else 0.0
        
        # Evaluate domain semantics
        if domain == "all_p_leq_pmax":
            passed = all(score >= self.threshold for score in tau_scores.values())
        elif domain == "exists_p_leq_pmax":
            passed = any(score >= self.threshold for score in tau_scores.values())
        else:
            passed = False
        
        evidence = {
            "predicate": "kendall_tau",
            "threshold": self.threshold,
            "tau_scores": tau_scores,
            "min_tau": min(tau_scores.values()) if tau_scores else None,
            "mean_tau": np.mean(list(tau_scores.values())) if tau_scores else None,
            "passed": passed,
            "domain": domain,
        }
        
        return passed, evidence
    
    def _extract_ranking(self, result: Any) -> Optional[Dict]:
        """Extract ranking as dict mapping item -> rank.
        
        Returns dictionary where keys are items and values are rank positions (0-indexed).
        """
        if result is None:
            return None
        
        # Try QueryResult interface
        if hasattr(result, "to_pandas"):
            df = result.to_pandas()
            if df is None or len(df) == 0:
                return None
            
            # Get item column
            if "node" in df.columns:
                items = df["node"].tolist()
            elif "edge" in df.columns:
                items = df["edge"].tolist()
            elif len(df.columns) > 0:
                items = df[df.columns[0]].tolist()
            else:
                return None
            
            # Rank is position in DataFrame (already sorted)
            return {item: rank for rank, item in enumerate(items)}
        
        # Try list
        if isinstance(result, list):
            return {item: rank for rank, item in enumerate(result)}
        
        return None
    
    def _has_excessive_ties(self, ranking: Dict, threshold: float = 0.5) -> bool:
        """Check if ranking has excessive ties.
        
        Returns True if more than threshold fraction of items share the same rank.
        """
        if not ranking:
            return False
        
        from collections import Counter
        rank_counts = Counter(ranking.values())
        max_tie_size = max(rank_counts.values())
        
        return max_tie_size / len(ranking) > threshold
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "type": "kendall_tau",
            "threshold": self.threshold,
            "tie_policy": self.tie_policy,
            "metric": self.metric,
        }
    
    def get_name(self) -> str:
        """Get predicate name."""
        return f"Kendall's τ >= {self.threshold}"


@dataclass
class PartitionVI(Predicate):
    """Variation of Information for community/partition stability.
    
    Evaluates VI(baseline_partition, perturbed_partition) <= threshold
    for all perturbation strengths in the domain.
    
    Attributes:
        threshold: Maximum variation of information (lower is more stable)
    """
    
    threshold: float = 0.25
    
    def __post_init__(self):
        """Validate parameters."""
        if self.threshold < 0.0:
            raise ValueError(f"threshold must be non-negative, got {self.threshold}")
    
    def evaluate(
        self,
        baseline: Any,
        perturbed_results: List[Tuple[float, Any]],
        domain: str = "all_p_leq_pmax"
    ) -> Tuple[bool, Dict[str, Any]]:
        """Evaluate VI for partitions.
        
        Args:
            baseline: QueryResult with community assignments
            perturbed_results: List of (p, QueryResult) pairs
            domain: Domain semantics
            
        Returns:
            (passed, evidence) where evidence contains VI scores per p
        """
        # Extract baseline partition
        baseline_partition = self._extract_partition(baseline)
        if baseline_partition is None or len(baseline_partition) == 0:
            return False, {
                "error": "insufficient_baseline",
                "baseline_size": len(baseline_partition) if baseline_partition else 0
            }
        
        # Compute VI for each perturbation strength
        vi_scores = {}
        for p, result in perturbed_results:
            perturbed_partition = self._extract_partition(result)
            if perturbed_partition is None or len(perturbed_partition) == 0:
                vi_scores[p] = float('inf')
                continue
            
            vi = self._compute_vi(baseline_partition, perturbed_partition)
            vi_scores[p] = vi
        
        # Evaluate domain semantics
        if domain == "all_p_leq_pmax":
            passed = all(score <= self.threshold for score in vi_scores.values() if score != float('inf'))
        elif domain == "exists_p_leq_pmax":
            passed = any(score <= self.threshold for score in vi_scores.values() if score != float('inf'))
        else:
            passed = False
        
        evidence = {
            "predicate": "partition_vi",
            "threshold": self.threshold,
            "vi_scores": {k: v for k, v in vi_scores.items() if v != float('inf')},
            "max_vi": max((v for v in vi_scores.values() if v != float('inf')), default=None),
            "mean_vi": np.mean([v for v in vi_scores.values() if v != float('inf')]) if any(v != float('inf') for v in vi_scores.values()) else None,
            "passed": passed,
            "domain": domain,
        }
        
        return passed, evidence
    
    def _extract_partition(self, result: Any) -> Optional[Dict]:
        """Extract partition as dict mapping node -> community_id."""
        if result is None:
            return None
        
        # Try QueryResult interface
        if hasattr(result, "to_pandas"):
            df = result.to_pandas()
            if df is None or len(df) == 0:
                return None
            
            if "node" in df.columns and "community" in df.columns:
                return dict(zip(df["node"], df["community"]))
            elif "community" in df.columns and len(df.columns) >= 2:
                return dict(zip(df[df.columns[0]], df["community"]))
        
        # Try dict
        if isinstance(result, dict):
            return result
        
        return None
    
    def _compute_vi(self, partition1: Dict, partition2: Dict) -> float:
        """Compute variation of information between two partitions.
        
        VI = H(partition1) + H(partition2) - 2 * MI(partition1, partition2)
        where H is entropy and MI is mutual information.
        """
        from collections import Counter
        
        # Align partitions by common nodes
        common_nodes = set(partition1.keys()) & set(partition2.keys())
        if len(common_nodes) == 0:
            return float('inf')
        
        n = len(common_nodes)
        
        # Compute cluster sizes
        clusters1 = Counter(partition1[node] for node in common_nodes)
        clusters2 = Counter(partition2[node] for node in common_nodes)
        
        # Compute entropies
        h1 = -sum((count / n) * np.log2(count / n) for count in clusters1.values())
        h2 = -sum((count / n) * np.log2(count / n) for count in clusters2.values())
        
        # Compute joint distribution
        joint = Counter()
        for node in common_nodes:
            joint[(partition1[node], partition2[node])] += 1
        
        # Compute mutual information
        mi = 0.0
        for (c1, c2), count in joint.items():
            p_joint = count / n
            p1 = clusters1[c1] / n
            p2 = clusters2[c2] / n
            if p_joint > 0:
                mi += p_joint * np.log2(p_joint / (p1 * p2))
        
        vi = h1 + h2 - 2 * mi
        return max(0.0, vi)  # Ensure non-negative due to numerical errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "type": "partition_vi",
            "threshold": self.threshold,
        }
    
    def get_name(self) -> str:
        """Get predicate name."""
        return f"VI <= {self.threshold}"


@dataclass
class PartitionARI(Predicate):
    """Adjusted Rand Index for community/partition stability.
    
    Evaluates ARI(baseline_partition, perturbed_partition) >= threshold
    for all perturbation strengths in the domain.
    
    Attributes:
        threshold: Minimum adjusted rand index (0.0 to 1.0)
    """
    
    threshold: float = 0.8
    
    def __post_init__(self):
        """Validate parameters."""
        if not (0.0 <= self.threshold <= 1.0):
            raise ValueError(f"threshold must be in [0, 1], got {self.threshold}")
    
    def evaluate(
        self,
        baseline: Any,
        perturbed_results: List[Tuple[float, Any]],
        domain: str = "all_p_leq_pmax"
    ) -> Tuple[bool, Dict[str, Any]]:
        """Evaluate ARI for partitions.
        
        Args:
            baseline: QueryResult with community assignments
            perturbed_results: List of (p, QueryResult) pairs
            domain: Domain semantics
            
        Returns:
            (passed, evidence) where evidence contains ARI scores per p
        """
        from sklearn.metrics import adjusted_rand_score
        
        # Extract baseline partition
        baseline_partition = self._extract_partition(baseline)
        if baseline_partition is None or len(baseline_partition) == 0:
            return False, {
                "error": "insufficient_baseline",
                "baseline_size": len(baseline_partition) if baseline_partition else 0
            }
        
        # Compute ARI for each perturbation strength
        ari_scores = {}
        for p, result in perturbed_results:
            perturbed_partition = self._extract_partition(result)
            if perturbed_partition is None or len(perturbed_partition) == 0:
                ari_scores[p] = 0.0
                continue
            
            # Align by common nodes
            common_nodes = sorted(set(baseline_partition.keys()) & set(perturbed_partition.keys()))
            if len(common_nodes) == 0:
                ari_scores[p] = 0.0
                continue
            
            labels1 = [baseline_partition[node] for node in common_nodes]
            labels2 = [perturbed_partition[node] for node in common_nodes]
            
            ari = adjusted_rand_score(labels1, labels2)
            ari_scores[p] = ari
        
        # Evaluate domain semantics
        if domain == "all_p_leq_pmax":
            passed = all(score >= self.threshold for score in ari_scores.values())
        elif domain == "exists_p_leq_pmax":
            passed = any(score >= self.threshold for score in ari_scores.values())
        else:
            passed = False
        
        evidence = {
            "predicate": "partition_ari",
            "threshold": self.threshold,
            "ari_scores": ari_scores,
            "min_ari": min(ari_scores.values()) if ari_scores else None,
            "mean_ari": np.mean(list(ari_scores.values())) if ari_scores else None,
            "passed": passed,
            "domain": domain,
        }
        
        return passed, evidence
    
    def _extract_partition(self, result: Any) -> Optional[Dict]:
        """Extract partition as dict mapping node -> community_id."""
        if result is None:
            return None
        
        # Try QueryResult interface
        if hasattr(result, "to_pandas"):
            df = result.to_pandas()
            if df is None or len(df) == 0:
                return None
            
            if "node" in df.columns and "community" in df.columns:
                return dict(zip(df["node"], df["community"]))
            elif "community" in df.columns and len(df.columns) >= 2:
                return dict(zip(df[df.columns[0]], df["community"]))
        
        # Try dict
        if isinstance(result, dict):
            return result
        
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "type": "partition_ari",
            "threshold": self.threshold,
        }
    
    def get_name(self) -> str:
        """Get predicate name."""
        return f"ARI >= {self.threshold}"
