"""Statistical comparison utilities for counterfactual analysis.

This module provides functions to compare baseline and counterfactual
results using various statistical measures.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats


def compute_delta_stats(baseline: pd.DataFrame,
                       counterfactuals: List[pd.DataFrame],
                       metric: str) -> Dict[str, float]:
    """Compute delta statistics between baseline and counterfactuals.
    
    Args:
        baseline: Baseline DataFrame
        counterfactuals: List of counterfactual DataFrames
        metric: Metric column name
        
    Returns:
        Dictionary with delta_mean, delta_std, delta_ci_low, delta_ci_high
    """
    if metric not in baseline.columns:
        return {}
    
    # Get baseline values
    baseline_vals = baseline[metric].values
    
    # Collect counterfactual deltas
    deltas = []
    for cf_df in counterfactuals:
        if metric in cf_df.columns:
            # Align by index/id
            merged = baseline.merge(cf_df, left_index=True, right_index=True, 
                                   suffixes=('_base', '_cf'))
            delta = merged[f"{metric}_cf"] - merged[f"{metric}_base"]
            deltas.append(delta.values)
    
    if not deltas:
        return {}
    
    # Aggregate deltas
    all_deltas = np.concatenate(deltas)
    
    return {
        "delta_mean": float(np.mean(all_deltas)),
        "delta_std": float(np.std(all_deltas)),
        "delta_ci_low": float(np.percentile(all_deltas, 2.5)),
        "delta_ci_high": float(np.percentile(all_deltas, 97.5)),
    }


def compute_empirical_pvalue(baseline: pd.DataFrame,
                            counterfactuals: List[pd.DataFrame],
                            metric: str,
                            item_id: Any) -> float:
    """Compute empirical p-value for a specific item.
    
    The p-value represents the fraction of counterfactual runs where
    the metric value is more extreme than the baseline.
    
    Args:
        baseline: Baseline DataFrame
        counterfactuals: List of counterfactual DataFrames
        metric: Metric column name
        item_id: Item ID to analyze
        
    Returns:
        Empirical p-value (0 to 1)
    """
    # Get baseline value
    if "id" in baseline.columns:
        baseline_row = baseline[baseline["id"] == item_id]
    else:
        baseline_row = baseline[baseline.index == item_id]
    
    if len(baseline_row) == 0 or metric not in baseline_row.columns:
        return np.nan
    
    baseline_val = baseline_row.iloc[0][metric]
    
    # Collect counterfactual values
    cf_vals = []
    for cf_df in counterfactuals:
        if "id" in cf_df.columns:
            cf_row = cf_df[cf_df["id"] == item_id]
        else:
            cf_row = cf_df[cf_df.index == item_id]
        
        if len(cf_row) > 0 and metric in cf_row.columns:
            cf_vals.append(cf_row.iloc[0][metric])
    
    if not cf_vals:
        return np.nan
    
    # Compute p-value (two-tailed)
    cf_array = np.array(cf_vals)
    n_more_extreme = np.sum(np.abs(cf_array - np.mean(cf_array)) >= 
                            np.abs(baseline_val - np.mean(cf_array)))
    
    return float(n_more_extreme / len(cf_vals))


def compute_rank_correlation(baseline: pd.DataFrame,
                            counterfactual: pd.DataFrame,
                            metric: str,
                            method: str = "kendall") -> float:
    """Compute rank correlation between baseline and counterfactual.
    
    Args:
        baseline: Baseline DataFrame
        counterfactual: Single counterfactual DataFrame
        metric: Metric column name
        method: "kendall" (tau) or "spearman"
        
    Returns:
        Correlation coefficient (-1 to 1)
    """
    if metric not in baseline.columns or metric not in counterfactual.columns:
        return np.nan
    
    # Merge on index
    merged = baseline.merge(counterfactual, left_index=True, right_index=True,
                           suffixes=('_base', '_cf'))
    
    base_vals = merged[f"{metric}_base"].values
    cf_vals = merged[f"{metric}_cf"].values
    
    # Remove NaN values
    valid_mask = ~(np.isnan(base_vals) | np.isnan(cf_vals))
    base_vals = base_vals[valid_mask]
    cf_vals = cf_vals[valid_mask]
    
    if len(base_vals) < 2:
        return np.nan
    
    if method == "kendall":
        corr, _ = stats.kendalltau(base_vals, cf_vals)
    elif method == "spearman":
        corr, _ = stats.spearmanr(base_vals, cf_vals)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return float(corr)


def compute_topk_overlap(baseline: pd.DataFrame,
                        counterfactual: pd.DataFrame,
                        metric: str,
                        k: int) -> float:
    """Compute Jaccard overlap of top-k items.
    
    Args:
        baseline: Baseline DataFrame
        counterfactual: Single counterfactual DataFrame
        metric: Metric column name to rank by
        k: Size of top-k set
        
    Returns:
        Jaccard coefficient (0 to 1)
    """
    if metric not in baseline.columns or metric not in counterfactual.columns:
        return np.nan
    
    # Get top-k from baseline
    baseline_topk = set(baseline.nlargest(k, metric).index)
    
    # Get top-k from counterfactual
    cf_topk = set(counterfactual.nlargest(k, metric).index)
    
    # Compute Jaccard
    intersection = len(baseline_topk & cf_topk)
    union = len(baseline_topk | cf_topk)
    
    if union == 0:
        return 0.0
    
    return float(intersection / union)


def compute_community_stability(baseline: pd.DataFrame,
                                counterfactual: pd.DataFrame,
                                community_col: str = "community",
                                metric: str = "vi") -> float:
    """Compute community stability using variation of information or ARI.
    
    Args:
        baseline: Baseline DataFrame with community assignments
        counterfactual: Counterfactual DataFrame with community assignments
        community_col: Column name for community assignments
        metric: "vi" (variation of information) or "ari" (adjusted Rand index)
        
    Returns:
        Stability score (VI: lower is better, ARI: 1 is perfect)
    """
    if community_col not in baseline.columns or community_col not in counterfactual.columns:
        return np.nan
    
    # Merge on index
    merged = baseline.merge(counterfactual, left_index=True, right_index=True,
                           suffixes=('_base', '_cf'))
    
    base_communities = merged[f"{community_col}_base"].values
    cf_communities = merged[f"{community_col}_cf"].values
    
    # Remove NaN values
    valid_mask = ~(pd.isna(base_communities) | pd.isna(cf_communities))
    base_communities = base_communities[valid_mask]
    cf_communities = cf_communities[valid_mask]
    
    if len(base_communities) == 0:
        return np.nan
    
    if metric == "vi":
        # Variation of Information
        from sklearn.metrics import normalized_mutual_info_score
        nmi = normalized_mutual_info_score(base_communities, cf_communities)
        return float(1.0 - nmi)  # Convert to distance metric
    elif metric == "ari":
        # Adjusted Rand Index
        from sklearn.metrics import adjusted_rand_score
        return float(adjusted_rand_score(base_communities, cf_communities))
    else:
        raise ValueError(f"Unknown metric: {metric}")


def stable_top_k(baseline: pd.DataFrame,
                counterfactuals: List[pd.DataFrame],
                metric: str,
                k: int,
                threshold: float = 0.8) -> List[Any]:
    """Find items stably in top-k across counterfactuals.
    
    Args:
        baseline: Baseline DataFrame
        counterfactuals: List of counterfactual DataFrames
        metric: Metric to rank by
        k: Size of top-k set
        threshold: Minimum fraction of runs to be in (0-1)
        
    Returns:
        List of item IDs that are stably in top-k
    """
    if metric not in baseline.columns:
        return []
    
    # Get baseline top-k
    baseline_topk = set(baseline.nlargest(k, metric).index)
    
    # Count appearances in counterfactual top-k
    appearances = {item: 0 for item in baseline_topk}
    
    for cf_df in counterfactuals:
        if metric not in cf_df.columns:
            continue
        
        cf_topk = set(cf_df.nlargest(k, metric).index)
        
        for item in baseline_topk:
            if item in cf_topk:
                appearances[item] += 1
    
    # Filter by threshold
    n_runs = len(counterfactuals)
    stable_items = [item for item, count in appearances.items()
                   if count / n_runs >= threshold]
    
    return stable_items


def fragile_nodes(baseline: pd.DataFrame,
                 counterfactuals: List[pd.DataFrame],
                 metric: str,
                 n: int = 5) -> List[Any]:
    """Find the n most fragile items (highest CV).
    
    Args:
        baseline: Baseline DataFrame
        counterfactuals: List of counterfactual DataFrames
        metric: Metric to analyze
        n: Number of fragile items to return
        
    Returns:
        List of item IDs with highest coefficient of variation
    """
    if metric not in baseline.columns:
        return []
    
    # Get all item IDs
    item_ids = baseline.index.tolist()
    
    # Compute CV for each item
    cv_scores = []
    for item_id in item_ids:
        # Get baseline value
        baseline_val = baseline.loc[item_id, metric]
        
        # Collect counterfactual values
        cf_vals = []
        for cf_df in counterfactuals:
            if item_id in cf_df.index and metric in cf_df.columns:
                cf_vals.append(cf_df.loc[item_id, metric])
        
        if cf_vals:
            cf_array = np.array(cf_vals)
            mean_val = np.mean(cf_array)
            std_val = np.std(cf_array)
            
            if mean_val != 0:
                cv = std_val / abs(mean_val)
            else:
                cv = 0.0
            
            cv_scores.append((item_id, cv))
    
    # Sort by CV and return top n
    cv_scores.sort(key=lambda x: x[1], reverse=True)
    return [item_id for item_id, cv in cv_scores[:n]]


def layer_sensitivity(baseline: pd.DataFrame,
                     counterfactuals: List[pd.DataFrame],
                     metric: str,
                     layer_col: str = "layer") -> pd.DataFrame:
    """Compute per-layer sensitivity statistics.
    
    Args:
        baseline: Baseline DataFrame with layer column
        counterfactuals: List of counterfactual DataFrames
        metric: Metric to analyze
        layer_col: Column name for layer information
        
    Returns:
        DataFrame with per-layer statistics
    """
    if layer_col not in baseline.columns or metric not in baseline.columns:
        return pd.DataFrame()
    
    layers = baseline[layer_col].unique()
    
    layer_stats = []
    for layer in layers:
        # Filter to this layer
        baseline_layer = baseline[baseline[layer_col] == layer]
        
        # Collect CV values for items in this layer
        cvs = []
        for item_id in baseline_layer.index:
            cf_vals = []
            for cf_df in counterfactuals:
                if layer_col in cf_df.columns and item_id in cf_df.index:
                    cf_row = cf_df[cf_df.index == item_id]
                    if len(cf_row) > 0 and metric in cf_row.columns:
                        cf_vals.append(cf_row.iloc[0][metric])
            
            if cf_vals:
                mean_val = np.mean(cf_vals)
                std_val = np.std(cf_vals)
                if mean_val != 0:
                    cvs.append(std_val / abs(mean_val))
        
        if cvs:
            layer_stats.append({
                "layer": layer,
                "n_items": len(baseline_layer),
                f"{metric}_avg_cv": np.mean(cvs),
                f"{metric}_max_cv": np.max(cvs),
            })
    
    return pd.DataFrame(layer_stats)
