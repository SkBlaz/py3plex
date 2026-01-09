"""Most-wins decision engine for AutoCommunity."""

import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from .result import ContestantResult
from .metric_registry import MetricRegistry, MetricSpec

logger = logging.getLogger(__name__)


def compute_pairwise_wins(
    contestants: List[ContestantResult],
    metrics: List[MetricSpec],
    bucket_caps: Optional[Dict[str, float]] = None,
    win_confidence: float = 0.95,
) -> Tuple[Dict[str, float], Dict[str, Dict[str, float]], pd.DataFrame]:
    """Compute pairwise wins for each contestant.
    
    Uses "most wins" logic:
    - For each metric, compare all pairs of contestants
    - Winner gets 1 point, loser gets 0, ties get 0.5 each
    - Aggregate wins across metrics with bucket caps
    
    Args:
        contestants: List of ContestantResult objects
        metrics: List of MetricSpec objects
        bucket_caps: Optional bucket caps (defaults from MetricRegistry)
        win_confidence: Confidence threshold for UQ-gated wins (default: 0.95)
    
    Returns:
        Tuple of:
            - total_wins: Dict[contestant_id -> total_wins]
            - wins_by_bucket: Dict[contestant_id -> Dict[bucket -> wins]]
            - leaderboard: DataFrame with rankings
    """
    if bucket_caps is None:
        bucket_caps = MetricRegistry.BUCKET_CAPS
    
    # Initialize wins tracking
    total_wins: Dict[str, float] = {c.contestant_id: 0.0 for c in contestants}
    wins_by_bucket: Dict[str, Dict[str, float]] = {
        c.contestant_id: {bucket: 0.0 for bucket in bucket_caps.keys()}
        for c in contestants
    }
    wins_by_metric: Dict[str, Dict[str, float]] = {}
    
    # Compute wins for each metric
    for metric_spec in metrics:
        metric_name = metric_spec.name
        direction = metric_spec.direction
        bucket = metric_spec.bucket
        
        # Get metric values for all contestants
        metric_values = {}
        for contestant in contestants:
            value = contestant.metrics.get(metric_name)
            
            # Handle NaN / NA
            if value is None or (isinstance(value, float) and np.isnan(value)):
                continue
            
            # Extract scalar value (handle dicts from UQ)
            if isinstance(value, dict) and "mean" in value:
                value = value["mean"]
            
            metric_values[contestant.contestant_id] = value
        
        # Skip if too few valid values
        if len(metric_values) < 2:
            logger.debug(f"Skipping {metric_name}: insufficient valid values")
            continue
        
        # Compute pairwise wins for this metric
        metric_wins = _compute_metric_wins(
            metric_values=metric_values,
            direction=direction,
            win_confidence=win_confidence,
        )
        
        wins_by_metric[metric_name] = metric_wins
        
        # Add to bucket wins (before capping)
        for contestant_id, wins in metric_wins.items():
            wins_by_bucket[contestant_id][bucket] += wins
    
    # Apply bucket caps
    for contestant_id in wins_by_bucket:
        for bucket, cap in bucket_caps.items():
            if wins_by_bucket[contestant_id][bucket] > cap:
                logger.debug(
                    f"Capping {contestant_id} {bucket} wins: "
                    f"{wins_by_bucket[contestant_id][bucket]:.1f} -> {cap}"
                )
                wins_by_bucket[contestant_id][bucket] = cap
    
    # Compute total wins (after caps)
    for contestant_id in total_wins:
        total_wins[contestant_id] = sum(wins_by_bucket[contestant_id].values())
    
    # Build leaderboard
    leaderboard = _build_leaderboard(
        contestants=contestants,
        total_wins=total_wins,
        wins_by_bucket=wins_by_bucket,
    )
    
    return total_wins, wins_by_bucket, leaderboard


def _compute_metric_wins(
    metric_values: Dict[str, float],
    direction: str,
    win_confidence: float = 0.95,
) -> Dict[str, float]:
    """Compute pairwise wins for a single metric.
    
    Args:
        metric_values: Dict[contestant_id -> metric_value]
        direction: "max" or "min"
        win_confidence: Confidence threshold (for future UQ gating)
    
    Returns:
        Dict[contestant_id -> wins]
    """
    contestant_ids = list(metric_values.keys())
    n = len(contestant_ids)
    
    wins = {cid: 0.0 for cid in contestant_ids}
    
    # Compare all pairs
    for i in range(n):
        for j in range(i + 1, n):
            cid_i = contestant_ids[i]
            cid_j = contestant_ids[j]
            
            val_i = metric_values[cid_i]
            val_j = metric_values[cid_j]
            
            # Determine winner
            if direction == "max":
                if val_i > val_j:
                    wins[cid_i] += 1.0
                elif val_j > val_i:
                    wins[cid_j] += 1.0
                else:
                    # Tie
                    wins[cid_i] += 0.5
                    wins[cid_j] += 0.5
            else:  # min
                if val_i < val_j:
                    wins[cid_i] += 1.0
                elif val_j < val_i:
                    wins[cid_j] += 1.0
                else:
                    # Tie
                    wins[cid_i] += 0.5
                    wins[cid_j] += 0.5
    
    return wins


def _build_leaderboard(
    contestants: List[ContestantResult],
    total_wins: Dict[str, float],
    wins_by_bucket: Dict[str, Dict[str, float]],
) -> pd.DataFrame:
    """Build leaderboard DataFrame.
    
    Args:
        contestants: List of ContestantResult
        total_wins: Dict[contestant_id -> total_wins]
        wins_by_bucket: Dict[contestant_id -> Dict[bucket -> wins]]
    
    Returns:
        DataFrame with leaderboard
    """
    rows = []
    
    for contestant in contestants:
        cid = contestant.contestant_id
        
        row = {
            "contestant_id": cid,
            "algorithm": contestant.algo_name,
            "params": str(contestant.params),
            "wins_total": total_wins[cid],
            "runtime_ms": contestant.runtime_ms,
        }
        
        # Add bucket wins
        for bucket, wins in wins_by_bucket[cid].items():
            row[f"wins_{bucket}"] = wins
        
        # Add key metrics
        for metric_name in ["modularity", "coverage", "singleton_fraction"]:
            if metric_name in contestant.metrics:
                value = contestant.metrics[metric_name]
                if isinstance(value, dict) and "mean" in value:
                    value = value["mean"]
                row[metric_name] = value
        
        rows.append(row)
    
    df = pd.DataFrame(rows)
    
    # Sort by total wins (descending), then runtime (ascending)
    df = df.sort_values(
        by=["wins_total", "runtime_ms"],
        ascending=[False, True]
    ).reset_index(drop=True)
    
    # Add rank
    df.insert(0, "rank", range(1, len(df) + 1))
    
    return df


def select_winner(
    contestants: List[ContestantResult],
    total_wins: Dict[str, float],
    wins_by_bucket: Dict[str, Dict[str, float]],
) -> ContestantResult:
    """Select winner with deterministic tie-breaking.
    
    Tie-breaking rules:
    1. Higher total wins
    2. Higher stability wins (if available)
    3. Lower runtime
    4. Lexicographic by contestant_id
    
    Args:
        contestants: List of ContestantResult
        total_wins: Dict[contestant_id -> total_wins]
        wins_by_bucket: Dict[contestant_id -> Dict[bucket -> wins]]
    
    Returns:
        Winning ContestantResult
    """
    # Sort contestants by tie-breaking rules
    def sort_key(c: ContestantResult):
        cid = c.contestant_id
        return (
            -total_wins[cid],  # Higher wins first (negate for descending)
            -wins_by_bucket[cid].get("stability", 0.0),  # Higher stability wins
            c.runtime_ms,  # Lower runtime first
            cid,  # Lexicographic
        )
    
    sorted_contestants = sorted(contestants, key=sort_key)
    winner = sorted_contestants[0]
    
    logger.info(f"Winner: {winner.contestant_id} with {total_wins[winner.contestant_id]:.1f} wins")
    
    return winner
