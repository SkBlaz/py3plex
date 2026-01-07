"""Candidate generation for claim learning.

This module enumerates candidate antecedents and consequents from node metrics,
using quantile-based thresholds for interpretability and determinism.
"""

import numpy as np
from typing import Any, Dict, List, Set, Tuple

from .types import Antecedent, Consequent


def generate_antecedent_candidates(
    metrics_data: Dict[str, List[float]],
    cheap_metrics: List[str],
    quantiles: List[float] = [0.7, 0.8, 0.9],
    top_p_values: List[float] = [0.05, 0.1, 0.2],
    max_layer_count: int = 10,
    seed: int = 42,
) -> List[Antecedent]:
    """Generate candidate antecedent predicates.
    
    Generates simple, interpretable predicates over cheap-to-compute metrics:
    - Threshold predicates: metric >= threshold (at quantiles)
    - Top-p predicates: top_p(metric, p)
    - Layer count predicates: layer_count >= k
    
    Args:
        metrics_data: Dictionary mapping metric names to lists of values
        cheap_metrics: List of metric names to use (e.g., ["degree", "strength"])
        quantiles: Quantile values for threshold selection (default: [0.7, 0.8, 0.9])
        top_p_values: Percentile values for top_p predicates (default: [0.05, 0.1, 0.2])
        max_layer_count: Maximum layer count threshold to test
        seed: Random seed for determinism (currently unused but reserved)
        
    Returns:
        List of Antecedent objects
    """
    candidates = []
    
    # Deterministic ordering by sorting metric names
    sorted_metrics = sorted(cheap_metrics)
    
    for metric in sorted_metrics:
        if metric not in metrics_data:
            continue
        
        values = metrics_data[metric]
        if not values:
            continue
        
        # Remove NaN/None values
        values = [v for v in values if v is not None and not (isinstance(v, float) and np.isnan(v))]
        if not values:
            continue
        
        # Threshold predicates at quantiles
        for q in sorted(quantiles):
            threshold = float(np.quantile(values, q))
            candidates.append(
                Antecedent(
                    metric=metric,
                    predicate_type="threshold",
                    threshold=round(threshold, 6),
                    operator=">=",
                )
            )
        
        # Top-p predicates
        for p in sorted(top_p_values):
            candidates.append(
                Antecedent(
                    metric=metric,
                    predicate_type="top_p",
                    percentile=p,
                )
            )
    
    # Layer count predicates (if layer_count is available)
    if "layer_count" in metrics_data:
        layer_counts = metrics_data["layer_count"]
        layer_counts = [v for v in layer_counts if v is not None and not (isinstance(v, float) and np.isnan(v))]
        if layer_counts:
            unique_counts = sorted(set(layer_counts))
            for count in unique_counts:
                if count > 0 and count <= max_layer_count:
                    candidates.append(
                        Antecedent(
                            metric="layer_count",
                            predicate_type="layer_count",
                            threshold=int(count),
                            operator=">=",
                        )
                    )
    
    return candidates


def generate_consequent_candidates(
    metrics_data: Dict[str, List[float]],
    target_metrics: List[str],
    quantiles: List[float] = [0.7, 0.8, 0.9],
    rank_thresholds: List[int] = [20, 50, 100],
    seed: int = 42,
) -> List[Consequent]:
    """Generate candidate consequent predicates.
    
    Generates predicates over target metrics (typically centrality measures):
    - Threshold predicates: metric >= threshold (at quantiles)
    - Rank predicates: rank(metric) <= r
    
    Args:
        metrics_data: Dictionary mapping metric names to lists of values
        target_metrics: List of metric names to use (e.g., ["pagerank", "betweenness"])
        quantiles: Quantile values for threshold selection
        rank_thresholds: Rank threshold values (e.g., [20, 50, 100] for top-20, top-50, etc.)
        seed: Random seed for determinism
        
    Returns:
        List of Consequent objects
    """
    candidates = []
    
    # Deterministic ordering
    sorted_metrics = sorted(target_metrics)
    
    for metric in sorted_metrics:
        if metric not in metrics_data:
            continue
        
        values = metrics_data[metric]
        if not values:
            continue
        
        # Remove NaN/None values
        values = [v for v in values if v is not None and not (isinstance(v, float) and np.isnan(v))]
        if not values:
            continue
        
        # Threshold predicates at quantiles
        for q in sorted(quantiles):
            threshold = float(np.quantile(values, q))
            candidates.append(
                Consequent(
                    metric=metric,
                    predicate_type="threshold",
                    threshold=round(threshold, 6),
                    operator=">=",
                )
            )
        
        # Rank predicates
        for rank in sorted(rank_thresholds):
            if rank <= len(values):
                candidates.append(
                    Consequent(
                        metric=metric,
                        predicate_type="rank",
                        rank=rank,
                        rank_operator="<=",
                    )
                )
    
    return candidates


def extract_metrics_from_result(result: Any) -> Tuple[Dict[str, List[float]], List[Tuple[Any, str]]]:
    """Extract metric values from DSL query result.
    
    Args:
        result: QueryResult from DSL execution
        
    Returns:
        Tuple of (metrics_data, node_ids):
            - metrics_data: Dict mapping metric names to lists of values
            - node_ids: List of (node, layer) tuples in same order as metrics
    """
    # Convert to pandas for easier processing
    df = result.to_pandas()
    
    metrics_data = {}
    node_ids = []
    
    # Extract node identifiers
    for _, row in df.iterrows():
        node_id = (row.get("id"), row.get("layer"))
        node_ids.append(node_id)
    
    # Extract all numeric columns as potential metrics
    for col in df.columns:
        if col in ["id", "layer", "type"]:
            continue
        
        # Try to extract numeric values
        try:
            values = df[col].tolist()
            # Filter to numeric values
            numeric_values = []
            for v in values:
                if isinstance(v, (int, float)) and not (isinstance(v, float) and np.isnan(v)):
                    numeric_values.append(float(v))
                elif v is not None:
                    try:
                        numeric_values.append(float(v))
                    except (ValueError, TypeError):
                        numeric_values.append(None)
                else:
                    numeric_values.append(None)
            
            metrics_data[col] = numeric_values
        except Exception:
            continue
    
    return metrics_data, node_ids


def build_node_data_records(
    metrics_data: Dict[str, List[float]],
    node_ids: List[Tuple[Any, str]]
) -> List[Dict[str, Any]]:
    """Build list of node data records from metrics data.
    
    Args:
        metrics_data: Dict mapping metric names to lists of values
        node_ids: List of (node, layer) tuples
        
    Returns:
        List of dictionaries, one per node, with all metric values
    """
    records = []
    n_nodes = len(node_ids)
    
    for i in range(n_nodes):
        record = {
            "node": node_ids[i][0],
            "layer": node_ids[i][1],
        }
        
        for metric_name, values in metrics_data.items():
            if i < len(values):
                record[metric_name] = values[i]
            else:
                record[metric_name] = None
        
        records.append(record)
    
    return records
