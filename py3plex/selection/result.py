"""Result data structures for AutoCommunity selection."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import numpy as np


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
            Human-readable explanation with structured sections
        """
        # Check if this is a Pareto-mode result
        if hasattr(self, 'pareto_front') and hasattr(self, 'community_stats'):
            return self._explain_pareto(n)
        
        # Standard wins-mode explanation
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
        
        # Runtime
        runtime_ms = self.chosen.runtime_ms
        if runtime_ms < 1000:  # Less than 1 second
            reasons.append(f"Fast execution ({runtime_ms:.0f} ms)")
        
        # UQ metrics
        if self.chosen.uq_meta:
            if "stability" in self.chosen.uq_meta:
                stability = self.chosen.uq_meta["stability"]
                if stability > 0.8:
                    reasons.append(f"High stability ({stability:.3f})")
        
        # Limit to n reasons
        reasons = reasons[:n]
        
        # Build explanation
        sections = []
        sections.append(f"Selection: '{self.chosen.contestant_id}' (mode=wins)\n")
        
        if reasons:
            sections.append("Rationale:")
            for i, reason in enumerate(reasons, 1):
                sections.append(f"  {i}. {reason}")
        else:
            sections.append("Rationale:")
            sections.append("  (No specific reasons available)")
        
        # Add reproducibility footer
        if "seed" in self.provenance.get("selection_config", {}):
            seed = self.provenance["selection_config"]["seed"]
            sections.append(f"\nReproducibility: seed={seed}")
        
        return "\n".join(sections)
    
    def _explain_pareto(self, n: int = 5) -> str:
        """Generate explanation for Pareto-mode result.
        
        Args:
            n: Maximum number of reasons per section
        
        Returns:
            Structured explanation with all required sections
        """
        sections = []
        
        # Section 1: Winner summary
        sections.append("=" * 70)
        sections.append("AutoCommunity v2 Selection Report (Pareto Mode)")
        sections.append("=" * 70)
        sections.append(f"\nWinner: {self.algorithm['name']}")
        
        if hasattr(self, 'community_stats'):
            stats = self.community_stats
            sections.append(f"Communities detected: {stats.n_communities}")
            sections.append(f"Coverage: {stats.coverage:.3f}")
        
        # Section 2: Why it won
        sections.append("\n--- Why This Algorithm Won ---")
        
        pareto_front = getattr(self, 'pareto_front', [])
        if len(pareto_front) == 1:
            sections.append("✓ Dominated all other algorithms (sole Pareto-optimal solution)")
        elif len(pareto_front) > 1:
            sections.append(f"✓ Part of Pareto front with {len(pareto_front)} non-dominated algorithms")
            sections.append("✓ Consensus partition computed from co-assignment matrix")
        
        # Top metrics
        if hasattr(self, 'evaluation_matrix') and not self.evaluation_matrix.empty:
            eval_matrix = self.evaluation_matrix
            # Find winner's row (use iloc for positional indexing)
            winner_id = self.algorithm['contestant_id']
            winner_rows = eval_matrix[eval_matrix['algorithm_id'] == winner_id]
            
            if not winner_rows.empty:
                winner_row = winner_rows.iloc[0]
                
                # Show top 3 metrics
                metric_cols = [c for c in eval_matrix.columns if c != 'algorithm_id']
                shown = 0
                for metric in metric_cols[:3]:
                    if metric in winner_row.index:
                        value = winner_row[metric]
                        if not pd.isna(value):
                            sections.append(f"  • {metric}: {value:.3f}")
                            shown += 1
                
                if shown == 0:
                    sections.append("  (Metrics not available)")
            else:
                sections.append("  (Winner metrics not found in evaluation matrix)")
        else:
            sections.append("  (Evaluation matrix not available)")
        
        # Section 3: Trade-offs
        sections.append("\n--- Trade-offs ---")
        
        if hasattr(self, 'evaluation_matrix') and not self.evaluation_matrix.empty:
            eval_matrix = self.evaluation_matrix
            # Compare to other algorithms
            winner_id = self.algorithm['contestant_id']
            other_algos = eval_matrix[eval_matrix['algorithm_id'] != winner_id]
            
            if not other_algos.empty:
                sections.append("  Compared to other candidates:")
                # Find metrics where others were better
                winner_rows = eval_matrix[eval_matrix['algorithm_id'] == winner_id]
                
                if not winner_rows.empty:
                    winner_row = winner_rows.iloc[0]
                    
                    tradeoffs_found = False
                    for metric in ['modularity', 'coverage', 'stability'][:2]:
                        if metric in winner_row.index and metric in other_algos.columns:
                            winner_val = winner_row[metric]
                            max_other = other_algos[metric].max()
                            if not pd.isna(max_other) and not pd.isna(winner_val) and max_other > winner_val:
                                sections.append(f"  • {metric}: {winner_val:.3f} (best: {max_other:.3f})")
                                tradeoffs_found = True
                    
                    if not tradeoffs_found:
                        sections.append("  • Winner is best or tied on all key metrics")
                else:
                    sections.append("  (Winner data not found)")
            else:
                sections.append("  (No other algorithms to compare)")
        else:
            sections.append("  (Trade-off analysis not available)")
        
        # Section 4: Stability & UQ
        sections.append("\n--- Stability & Uncertainty ---")
        
        if hasattr(self, 'community_stats'):
            stats = self.community_stats
            if stats.stability_score is not None:
                stability = stats.stability_score
                sections.append(f"  Partition stability: {stability:.3f}")
                if stability > 0.8:
                    sections.append("  → High confidence in community assignments")
                elif stability < 0.5:
                    sections.append("  ⚠ Low stability - consider increasing UQ samples")
            
            if stats.node_confidence:
                confidences = list(stats.node_confidence.values())
                mean_conf = sum(confidences) / len(confidences)
                sections.append(f"  Mean node confidence: {mean_conf:.3f}")
        else:
            sections.append("  (UQ not enabled)")
        
        # Section 5: Null-model calibration
        sections.append("\n--- Null-Model Calibration ---")
        
        if hasattr(self, 'null_model_results') and self.null_model_results:
            z_scores = self.null_model_results.get('z_scores', {})
            if z_scores:
                max_z = max(z_scores.values()) if z_scores else 0
                sections.append(f"  Max Z-score vs null models: {max_z:.2f}")
                
                if max_z > 3.0:
                    sections.append("  → Highly significant structure (p < 0.001)")
                elif max_z > 2.0:
                    sections.append("  → Significant structure (p < 0.05)")
                else:
                    sections.append("  ⚠ Weak signal relative to null models")
            else:
                sections.append("  (Z-scores not computed)")
        else:
            sections.append("  (Null-model calibration not enabled)")
        
        # Section 6: Graph regime
        sections.append("\n--- Graph Regime Interpretation ---")
        
        if hasattr(self, 'graph_regime') and self.graph_regime:
            regime = self.graph_regime
            if 'degree_heterogeneity' in regime:
                het = regime['degree_heterogeneity']
                sections.append(f"  Degree heterogeneity: {het:.3f}")
                if het > 2.0:
                    sections.append("  → High variation in node degrees (scale-free-like)")
            
            if 'coupling_strength' in regime:
                coupling = regime['coupling_strength']
                sections.append(f"  Inter-layer coupling: {coupling:.3f}")
                if coupling > 0.5:
                    sections.append("  → Strong inter-layer connections")
                elif coupling < 0.1:
                    sections.append("  → Weakly coupled layers")
        else:
            sections.append("  (Regime diagnostics not available)")
        
        # Section 7: Reproducibility footer
        sections.append("\n--- Reproducibility ---")
        
        if "seed" in self.provenance:
            seed = self.provenance["seed"]
            sections.append(f"  Random seed: {seed}")
        
        if "pareto_enabled" in self.provenance:
            sections.append(f"  Pareto selection: {self.provenance['pareto_enabled']}")
        
        if "uq_enabled" in self.provenance:
            sections.append(f"  UQ enabled: {self.provenance['uq_enabled']}")
        
        sections.append("\n" + "=" * 70)
        
        return "\n".join(sections)
    
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
