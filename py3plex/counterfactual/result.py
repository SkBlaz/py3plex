"""Result containers for counterfactual analysis.

This module provides structured result containers for counterfactual
queries, with human-friendly reporting interfaces.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import pandas as pd


@dataclass
class CounterfactualResult:
    """Result of a counterfactual analysis.
    
    Attributes:
        baseline: QueryResult from the original network
        counterfactuals: List of QueryResult from modified networks
        summary: DataFrame with aggregated statistics across runs
        meta: Metadata dictionary with provenance information
    """
    baseline: Any  # QueryResult
    counterfactuals: List[Any]  # List[QueryResult]
    summary: pd.DataFrame
    meta: Dict[str, Any]
    
    def to_report(self) -> "RobustnessReport":
        """Convert to a RobustnessReport for human-friendly display.
        
        Returns:
            RobustnessReport wrapping this result
        """
        return RobustnessReport(self)


class RobustnessReport:
    """Human-friendly wrapper for counterfactual results.
    
    This class provides intuitive methods for exploring robustness
    without requiring deep knowledge of the underlying data structures.
    """
    
    def __init__(self, result: CounterfactualResult):
        """Initialize report from a CounterfactualResult.
        
        Args:
            result: CounterfactualResult to wrap
        """
        self.result = result
        self._summary_cache = None
    
    def show(self, top_n: int = 20, precision: int = 4) -> None:
        """Display a human-readable summary of robustness.
        
        Args:
            top_n: Number of top items to display
            precision: Decimal places for floating point values
        """
        print("=" * 70)
        print("ROBUSTNESS REPORT")
        print("=" * 70)
        
        # Show provenance
        prov = self.result.meta.get("provenance", {})
        print(f"\nIntervention: {prov.get('intervention_type', 'unknown')}")
        print(f"Repeats: {prov.get('repeats', 0)}")
        print(f"Seed: {prov.get('seed', 'none')}")
        
        # Show summary statistics
        print(f"\nBaseline network:")
        baseline_info = prov.get("baseline_network", {})
        print(f"  Nodes: {baseline_info.get('n_nodes', '?')}")
        print(f"  Edges: {baseline_info.get('n_edges', '?')}")
        print(f"  Layers: {baseline_info.get('n_layers', '?')}")
        
        # Show metric stability
        print(f"\n{'-' * 70}")
        print("METRIC STABILITY")
        print("-" * 70)
        
        df = self.to_pandas()
        if len(df) > 0:
            # Display top N rows
            display_cols = [c for c in df.columns if not c.startswith("_")]
            print(df[display_cols].head(top_n).to_string(index=False, 
                                                         float_format=f'%.{precision}f'))
        else:
            print("(No results)")
        
        print("\n" + "=" * 70)
    
    def describe(self) -> pd.DataFrame:
        """Get statistical summary of all metrics.
        
        Returns:
            DataFrame with mean, std, min, max, etc. for each metric
        """
        df = self.to_pandas()
        numeric_cols = df.select_dtypes(include=['number']).columns
        return df[numeric_cols].describe()
    
    def stable_top_k(self, k: int = 10, threshold: float = 0.8, 
                    metric: Optional[str] = None) -> List[Any]:
        """Find items that consistently appear in top-k across counterfactuals.
        
        Args:
            k: Size of top-k set
            threshold: Minimum fraction of runs where item must appear in top-k (0-1)
            metric: Metric to rank by (if None, uses first computed metric)
            
        Returns:
            List of item IDs that are stably in top-k
        """
        if self.result.summary.empty:
            return []
        
        # Determine metric to use
        if metric is None:
            # Find first metric with _mean suffix
            metric_cols = [c for c in self.result.summary.columns if c.endswith("_mean")]
            if not metric_cols:
                return []
            metric = metric_cols[0].replace("_mean", "")
        
        # Check if we have the stability column
        stability_col = f"{metric}_top{k}_stability"
        if stability_col not in self.result.summary.columns:
            # Compute it on the fly
            return self._compute_stable_topk(k, threshold, metric)
        
        # Filter by threshold
        df = self.result.summary
        stable = df[df[stability_col] >= threshold]
        return stable["id"].tolist() if "id" in stable.columns else stable.index.tolist()
    
    def _compute_stable_topk(self, k: int, threshold: float, metric: str) -> List[Any]:
        """Compute stable top-k on the fly."""
        # Get baseline top-k
        baseline_df = self.result.baseline.to_pandas()
        if metric not in baseline_df.columns:
            return []
        
        baseline_topk = set(baseline_df.nlargest(k, metric)["id"].tolist() 
                           if "id" in baseline_df.columns 
                           else baseline_df.nlargest(k, metric).index.tolist())
        
        # Count appearances in counterfactual top-k
        appearances = {item: 0 for item in baseline_topk}
        
        for cf_result in self.result.counterfactuals:
            cf_df = cf_result.to_pandas()
            if metric not in cf_df.columns:
                continue
            
            cf_topk = set(cf_df.nlargest(k, metric)["id"].tolist()
                         if "id" in cf_df.columns
                         else cf_df.nlargest(k, metric).index.tolist())
            
            for item in baseline_topk:
                if item in cf_topk:
                    appearances[item] += 1
        
        # Filter by threshold
        n_runs = len(self.result.counterfactuals)
        stable_items = [item for item, count in appearances.items() 
                       if count / n_runs >= threshold]
        
        return stable_items
    
    def fragile(self, n: int = 5, metric: Optional[str] = None) -> List[Any]:
        """Find the n most fragile items (highest variability across runs).
        
        Args:
            n: Number of fragile items to return
            metric: Metric to analyze (if None, uses first computed metric)
            
        Returns:
            List of item IDs with highest coefficient of variation
        """
        if self.result.summary.empty:
            return []
        
        # Determine metric
        if metric is None:
            metric_cols = [c for c in self.result.summary.columns if c.endswith("_mean")]
            if not metric_cols:
                return []
            metric = metric_cols[0].replace("_mean", "")
        
        # Look for coefficient of variation column
        cv_col = f"{metric}_cv"
        if cv_col in self.result.summary.columns:
            df = self.result.summary.nlargest(n, cv_col)
            return df["id"].tolist() if "id" in df.columns else df.index.tolist()
        
        # Compute CV on the fly
        mean_col = f"{metric}_mean"
        std_col = f"{metric}_std"
        
        if mean_col not in self.result.summary.columns or std_col not in self.result.summary.columns:
            return []
        
        df = self.result.summary.copy()
        df["_cv"] = df[std_col] / (df[mean_col] + 1e-10)  # Avoid division by zero
        df = df.nlargest(n, "_cv")
        return df["id"].tolist() if "id" in df.columns else df.index.tolist()
    
    def layer_sensitivity(self) -> Optional[pd.DataFrame]:
        """Analyze sensitivity by layer (if layer information is available).
        
        Returns:
            DataFrame with per-layer sensitivity statistics, or None if not available
        """
        # Check if layer information is in summary
        if "layer" not in self.result.summary.columns:
            return None
        
        # Group by layer and compute statistics
        layer_groups = self.result.summary.groupby("layer")
        
        # Compute mean CV for each metric
        metrics = [c.replace("_mean", "") for c in self.result.summary.columns 
                  if c.endswith("_mean")]
        
        sensitivity_data = []
        for layer, group in layer_groups:
            row = {"layer": layer, "n_items": len(group)}
            
            for metric in metrics:
                mean_col = f"{metric}_mean"
                std_col = f"{metric}_std"
                
                if mean_col in group.columns and std_col in group.columns:
                    cv = (group[std_col] / (group[mean_col] + 1e-10)).mean()
                    row[f"{metric}_avg_cv"] = cv
            
            sensitivity_data.append(row)
        
        return pd.DataFrame(sensitivity_data)
    
    def to_pandas(self) -> pd.DataFrame:
        """Export full summary as pandas DataFrame.
        
        Returns:
            DataFrame with all summary statistics
        """
        return self.result.summary.copy()
    
    def get_baseline(self) -> Any:
        """Get the baseline QueryResult.
        
        Returns:
            QueryResult from the unmodified network
        """
        return self.result.baseline
    
    def get_counterfactuals(self) -> List[Any]:
        """Get all counterfactual QueryResults.
        
        Returns:
            List of QueryResult objects from modified networks
        """
        return self.result.counterfactuals
    
    def compare_items(self, item_id: Any, metric: Optional[str] = None) -> Dict[str, Any]:
        """Compare a specific item across baseline and counterfactuals.
        
        Args:
            item_id: ID of the item to compare
            metric: Metric to compare (if None, compares all metrics)
            
        Returns:
            Dictionary with baseline value, counterfactual distribution, and statistics
        """
        # Get baseline value
        baseline_df = self.result.baseline.to_pandas()
        
        if "id" in baseline_df.columns:
            baseline_row = baseline_df[baseline_df["id"] == item_id]
        else:
            baseline_row = baseline_df[baseline_df.index == item_id]
        
        if len(baseline_row) == 0:
            return {"error": f"Item {item_id} not found in baseline"}
        
        baseline_row = baseline_row.iloc[0]
        
        # Get counterfactual values
        cf_values = {}
        for cf_result in self.result.counterfactuals:
            cf_df = cf_result.to_pandas()
            
            if "id" in cf_df.columns:
                cf_row = cf_df[cf_df["id"] == item_id]
            else:
                cf_row = cf_df[cf_df.index == item_id]
            
            if len(cf_row) > 0:
                cf_row = cf_row.iloc[0]
                for col in cf_df.columns:
                    if col not in ("id", "layer") and not col.startswith("_"):
                        if col not in cf_values:
                            cf_values[col] = []
                        cf_values[col].append(cf_row[col])
        
        # Build comparison
        comparison = {
            "item_id": item_id,
            "baseline": {},
            "counterfactuals": {},
        }
        
        for col in baseline_row.index:
            if col not in ("id", "layer") and not col.startswith("_"):
                comparison["baseline"][col] = baseline_row[col]
                
                if col in cf_values:
                    import numpy as np
                    vals = cf_values[col]
                    comparison["counterfactuals"][col] = {
                        "mean": float(np.mean(vals)),
                        "std": float(np.std(vals)),
                        "min": float(np.min(vals)),
                        "max": float(np.max(vals)),
                        "values": vals,
                    }
        
        return comparison
