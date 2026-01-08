"""Selection UQ integration for DSL.

This module provides functions to execute selection queries (top-k, filters)
with uncertainty quantification, integrated with the DSL executor.
"""

import copy
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from py3plex.uncertainty import (
    SelectionOutput,
    execute_selection_uq,
    SelectionUQ,
)
from py3plex.uncertainty.noise_models import NoiseModel
from py3plex.dsl.ast import SelectStmt, Target
from py3plex.dsl.result import QueryResult


logger = logging.getLogger(__name__)


def is_selection_query(select: SelectStmt) -> bool:
    """Determine if a query is a selection query suitable for SelectionUQ.
    
    A query is considered a selection query if:
    - It has grouping with per-group top-k (limit_per_group is set)
    - It has global ordering + limit (effectively top-k)
    - It has filters but no computed measures with uncertainty
    
    Parameters
    ----------
    select : SelectStmt
        The SELECT statement to check
        
    Returns
    -------
    bool
        True if this is a selection query
    """
    # Has grouped top-k
    if select.limit_per_group is not None:
        return True
    
    # Has global top-k (ordered + limited)
    if select.order_by and select.limit:
        return True
    
    # Filter-only query (no computed measures, just filtering)
    # This is a weaker criterion - we could enable it if needed
    # if select.where and not select.compute:
    #     return True
    
    return False


def execute_selection_with_uq(
    network: Any,
    select: SelectStmt,
    params: Optional[Dict[str, Any]] = None,
    progress: bool = False,
) -> QueryResult:
    """Execute a selection query with UQ.
    
    This function wraps a selection query and runs it multiple times under
    perturbation/resampling to compute selection uncertainty.
    
    Parameters
    ----------
    network : multi_layer_network
        Input network
    select : SelectStmt
        SELECT statement with uq_config
    params : dict, optional
        Query parameters
    progress : bool
        Whether to log progress
        
    Returns
    -------
    QueryResult
        Result with SelectionUQ columns and metadata
    """
    from .executor import _execute_select
    
    params = params or {}
    uq_config = select.uq_config
    
    if uq_config is None:
        raise ValueError("execute_selection_with_uq requires uq_config")
    
    # Extract UQ parameters
    uq_method = uq_config.method or "perturbation"
    n_samples = uq_config.n_samples or 50
    seed = uq_config.seed
    ci = uq_config.ci or 0.95
    noise_model = uq_config.kwargs.get("noise_model") if uq_config.kwargs else None
    store_mode = uq_config.kwargs.get("store", "sketch") if uq_config.kwargs else "sketch"
    
    # Determine if grouped
    is_grouped = (select.limit_per_group is not None or 
                  select.group_by is not None or 
                  select.coverage_mode is not None)
    
    if progress:
        logger.info(
            f"Running selection query with UQ "
            f"(method={uq_method}, n_samples={n_samples}, grouped={is_grouped})"
        )
    
    # Define base callable that executes query once
    def base_callable(net: Any, params_copy: Dict) -> SelectionOutput:
        """Execute the selection query once and return SelectionOutput."""
        # Clone select to avoid side effects
        select_copy = copy.deepcopy(select)
        
        # Clear UQ config to avoid recursion
        select_copy.uq_config = None
        
        # Execute query
        result = _execute_select(
            net, select_copy, params_copy, progress=False
        )
        
        # Extract selection information
        items = result.items
        target = result.meta.get("target", "nodes")
        
        # Warn if no items were selected
        if not items:
            logger.debug("Query produced no items in this sample")
        
        # Extract scores if available (from order_by attribute)
        scores = None
        ranks = None
        k = None
        group_key = None
        
        # Check if this is an ordered result
        if select.order_by and len(select.order_by) > 0:
            order_key = select.order_by[0].key
            
            # Extract scores from attributes
            if order_key in result.attributes:
                attr_vals = result.attributes[order_key]
                scores = {}
                
                for item in items:
                    val = attr_vals.get(item)
                    if val is not None:
                        # Handle uncertainty values
                        if isinstance(val, dict) and "mean" in val:
                            scores[item] = val["mean"]
                        else:
                            try:
                                scores[item] = float(val)
                            except (TypeError, ValueError):
                                pass
                
                # Assign ranks based on scores
                if scores:
                    sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=select.order_by[0].desc)
                    ranks = {item: rank + 1 for rank, (item, _) in enumerate(sorted_items)}
            
            # Determine k
            if select.limit_per_group is not None:
                k = select.limit_per_group
            elif select.limit is not None:
                k = select.limit
        
        # Extract group key if grouped result
        if is_grouped and "grouping" in result.meta:
            # For now, we'll process ungrouped
            # Grouped processing would require iterating over groups
            pass
        
        return SelectionOutput(
            items=items,
            scores=scores,
            ranks=ranks,
            k=k,
            target=target,
            group_key=group_key,
        )
    
    # Run SelectionUQ
    start_time = time.monotonic()
    
    selection_uq_result = execute_selection_uq(
        base_callable=base_callable,
        network=network,
        params=params,
        method=uq_method,
        n_samples=n_samples,
        seed=seed,
        noise_model=noise_model,
        ci=ci,
        store_mode=store_mode,
        grouped=is_grouped,
    )
    
    # Handle grouped vs ungrouped results
    if isinstance(selection_uq_result, dict):
        # Grouped result - for now, we'll take the first group or aggregate
        # TODO: Proper grouped handling
        if len(selection_uq_result) > 0:
            selection_uq = list(selection_uq_result.values())[0]
        else:
            # Empty result - query produced no groups (e.g., no items, no matches)
            # Fall back to creating an empty SelectionUQ
            logger.warning(
                "Query configured for grouping but produced no groups. "
                "This may indicate no items matched the selection criteria."
            )
            from py3plex.uncertainty import SelectionUQ
            # Create an empty SelectionUQ with safe defaults
            selection_uq = SelectionUQ(
                n_samples=n_samples,
                items_universe=[],
                samples_seen=0,
                present_prob={},
                size_stats={"mean": 0.0, "std": 0.0},
                stability_stats={"jaccard_mean": 1.0, "jaccard_std": 0.0, "consensus_size": 0},
                target="nodes",
                store_mode=store_mode,
                ci_method="wilson",
                meta={
                    "method": uq_method,
                    "n_samples": n_samples,
                    "seed": seed,
                    "ci_level": ci,
                    "noise_model": str(noise_model) if noise_model else None,
                    "warning": "No groups produced by query"
                }
            )
    else:
        # Ungrouped result
        selection_uq = selection_uq_result
    
    uq_duration_ms = (time.monotonic() - start_time) * 1000
    
    if progress:
        logger.info(
            f"SelectionUQ complete in {uq_duration_ms:.0f}ms: "
            f"{len(selection_uq.items_universe)} items tracked"
        )
    
    # Execute query once more to get base result
    # (This gives us the reference point for comparison)
    select_copy = copy.deepcopy(select)
    select_copy.uq_config = None
    
    result = _execute_select(network, select_copy, params, progress=False)
    
    # Add SelectionUQ columns to result
    _add_selection_uq_to_result(result, selection_uq)
    
    # Add UQ metadata
    result.meta["uq"] = {
        "type": "selection",
        "n_samples": n_samples,
        "method": uq_method,
        "noise_model": str(noise_model) if noise_model else None,
        "set_size": selection_uq.size_stats,
        "stability": selection_uq.stability_stats,
        "consensus": {
            "threshold": 0.5,
            "size": len(selection_uq.consensus_items),
            "items_preview": list(selection_uq.consensus_items)[:10],
        },
        "borderline_items": selection_uq.borderline_items[:10],
        "duration_ms": uq_duration_ms,
    }
    
    if selection_uq.k is not None:
        result.meta["uq"]["topk"] = {
            "k": selection_uq.k,
            "overlap": selection_uq.topk_overlap_stats,
        }
    
    # Store full SelectionUQ object
    result.meta["selection_uq"] = selection_uq
    
    return result


def _add_selection_uq_to_result(result: QueryResult, selection_uq: SelectionUQ) -> None:
    """Add SelectionUQ columns to QueryResult.
    
    Parameters
    ----------
    result : QueryResult
        Result to augment
    selection_uq : SelectionUQ
        UQ data to add
    """
    # Add present_prob for all items
    result.attributes["present_prob"] = {
        item: selection_uq.present_prob.get(item, 0.0)
        for item in result.items
    }
    
    result.attributes["present_ci_low"] = {
        item: selection_uq.present_ci_low.get(item, 0.0)
        for item in result.items
    }
    
    result.attributes["present_ci_high"] = {
        item: selection_uq.present_ci_high.get(item, 1.0)
        for item in result.items
    }
    
    # Add rank columns if available
    if selection_uq.rank_mean is not None:
        result.attributes["rank_mean"] = {
            item: selection_uq.rank_mean.get(item, float('inf'))
            for item in result.items
        }
        
        result.attributes["rank_std"] = {
            item: selection_uq.rank_std.get(item, 0.0)
            for item in result.items
        }
        
        if selection_uq.rank_ci_low is not None:
            result.attributes["rank_ci_low"] = {
                item: selection_uq.rank_ci_low.get(item, float('inf'))
                for item in result.items
            }
            
            result.attributes["rank_ci_high"] = {
                item: selection_uq.rank_ci_high.get(item, float('inf'))
                for item in result.items
            }
    
    # Add p_in_topk if available
    if selection_uq.p_in_topk is not None:
        result.attributes["p_in_topk"] = {
            item: selection_uq.p_in_topk.get(item, 0.0)
            for item in result.items
        }
