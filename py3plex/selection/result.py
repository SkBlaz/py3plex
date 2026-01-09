"""Result data structures for AutoCommunity selection."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd


@dataclass
class ContestantResult:
    """Result for a single contestant (algorithm + params combination).
    
    Attributes:
        contestant_id: Unique identifier (e.g., "leiden:gamma=1.2")
        algo_name: Algorithm name
        params: Algorithm parameters
        partition: Resulting partition dict
        metrics: Computed metrics {name -> value or {mean, ci, ...}}
        uq_meta: Optional UQ metadata
        runtime_ms: Execution time in milliseconds
        errors: Any errors encountered
        warnings: Any warnings
        seed_used: Random seed used
    """
    
    contestant_id: str
    algo_name: str
    params: Dict[str, Any]
    partition: Dict[Tuple[Any, Any], int]
    metrics: Dict[str, Any]
    runtime_ms: float
    seed_used: Optional[int] = None
    uq_meta: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def __repr__(self) -> str:
        return f"ContestantResult({self.contestant_id}, metrics={len(self.metrics)})"


@dataclass
class AutoCommunityResult:
    """Result of automatic community selection.
    
    This is the main result object returned by auto_select().
    
    Attributes:
        chosen: The winning contestant
        partition: The winning partition
        algorithm: Algorithm info {name, params}
        leaderboard: DataFrame with rankings
        win_matrix: Optional pairwise win matrix
        report: Per-metric summaries
        provenance: Detection and selection metadata
    """
    
    chosen: ContestantResult
    partition: Dict[Tuple[Any, Any], int]
    algorithm: Dict[str, Any]
    leaderboard: pd.DataFrame
    report: Dict[str, Any]
    provenance: Dict[str, Any]
    win_matrix: Optional[Dict[str, Dict[str, float]]] = None
    
    def explain(self, n: int = 5) -> str:
        """Generate natural language explanation of why this algorithm won.
        
        Args:
            n: Maximum number of reasons to include (default: 5)
        
        Returns:
            Human-readable explanation
        """
        reasons = []
        
        # Get wins by bucket from provenance
        if "wins_by_bucket" in self.provenance:
            wins_by_bucket = self.provenance["wins_by_bucket"]
            # Sort buckets by wins
            sorted_buckets = sorted(
                wins_by_bucket.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            # Add top bucket wins
            for bucket, wins in sorted_buckets[:3]:
                if wins > 0:
                    reasons.append(f"Won {wins:.1f} points in {bucket} metrics")
        
        # Check for key metric values
        chosen_metrics = self.chosen.metrics
        
        # Modularity
        if "modularity" in chosen_metrics:
            mod = chosen_metrics["modularity"]
            if isinstance(mod, dict) and "mean" in mod:
                mod = mod["mean"]
            if mod > 0.3:  # Reasonable threshold
                reasons.append(f"High modularity ({mod:.3f})")
        
        # Low singleton fraction
        if "singleton_fraction" in chosen_metrics:
            sf = chosen_metrics["singleton_fraction"]
            if isinstance(sf, dict) and "mean" in sf:
                sf = sf["mean"]
            if sf < 0.1:
                reasons.append(f"Low singleton fraction ({sf:.3f})")
        
        # Stability (if UQ enabled)
        if "mean_node_entropy" in chosen_metrics:
            ent = chosen_metrics["mean_node_entropy"]
            if isinstance(ent, dict) and "mean" in ent:
                ent = ent["mean"]
            if ent < 0.5:
                reasons.append(f"High stability (entropy={ent:.3f})")
        
        # UQ gating info
        if self.provenance.get("uq_enabled", False):
            reasons.append("Wins were significance-gated under perturbation")
        
        # Limit to n reasons
        reasons = reasons[:n]
        
        # Build explanation
        explanation = f"Algorithm '{self.algorithm['name']}' was selected because:\n"
        for i, reason in enumerate(reasons, 1):
            explanation += f"  {i}. {reason}\n"
        
        if not reasons:
            explanation += "  (No specific reasons available - default winner)\n"
        
        return explanation.strip()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for saving.
        
        Returns:
            Dictionary representation
        """
        return {
            "algorithm": self.algorithm,
            "partition": {
                str(k): v for k, v in self.partition.items()
            },
            "leaderboard": self.leaderboard.to_dict(orient="records"),
            "report": self.report,
            "provenance": self.provenance,
        }
    
    def __repr__(self) -> str:
        algo_name = self.algorithm["name"]
        n_communities = len(set(self.partition.values()))
        return f"AutoCommunityResult(algorithm='{algo_name}', n_communities={n_communities})"
