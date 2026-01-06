"""Counterfactual execution engine.

This module implements the core execution logic for counterfactual
analysis, with deterministic seeding and optional streaming mode.
"""

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from .spec import InterventionSpec
from .result import CounterfactualResult


class CounterfactualEngine:
    """Engine for executing counterfactual analyses.
    
    The engine:
    - Executes the baseline query once
    - Applies intervention specs repeatedly with deterministic seeding
    - Aggregates results into CounterfactualResult
    - Optionally streams results to avoid memory issues
    """
    
    def __init__(self, 
                 network: Any,
                 query: Any,  # AST Query object
                 spec: InterventionSpec,
                 repeats: int = 30,
                 seed: Optional[int] = None,
                 streaming: bool = False):
        """Initialize counterfactual engine.
        
        Args:
            network: Network to analyze
            query: AST Query object or QueryBuilder
            spec: Intervention specification
            repeats: Number of counterfactual runs
            seed: Master seed for reproducibility
            streaming: If True, don't store all counterfactual results
        """
        self.network = network
        self.query = query
        self.spec = spec
        self.repeats = repeats
        self.seed = seed
        self.streaming = streaming
        
        # Initialize seed sequence for deterministic child seeds
        if seed is not None:
            self.seed_seq = np.random.SeedSequence(seed)
        else:
            self.seed_seq = np.random.SeedSequence()
    
    def run(self) -> CounterfactualResult:
        """Execute the counterfactual analysis.
        
        Returns:
            CounterfactualResult with baseline, counterfactuals, and summary
        """
        # Execute baseline once
        baseline_result = self._execute_baseline()
        
        # Execute counterfactuals
        cf_results = []
        cf_dataframes = []
        
        # Generate child seeds deterministically
        child_seeds = self.seed_seq.spawn(self.repeats)
        
        for i, child_seed in enumerate(child_seeds):
            # Apply intervention to create modified network
            seed_int = child_seed.entropy  # Get integer seed
            modified_network = self.spec.apply(self.network, seed_int)
            
            # Execute query on modified network
            cf_result = self._execute_query(modified_network)
            
            if not self.streaming:
                cf_results.append(cf_result)
            
            # Convert to DataFrame for aggregation
            cf_df = cf_result.to_pandas()
            cf_dataframes.append(cf_df)
        
        # Aggregate results
        summary = self._aggregate_results(baseline_result, cf_dataframes)
        
        # Build metadata
        meta = self._build_metadata(baseline_result)
        
        return CounterfactualResult(
            baseline=baseline_result,
            counterfactuals=cf_results if not self.streaming else [],
            summary=summary,
            meta=meta
        )
    
    def _execute_baseline(self) -> Any:
        """Execute baseline query on original network.
        
        Returns:
            QueryResult from baseline execution
        """
        from py3plex.dsl.executor import execute_ast
        
        # Handle QueryBuilder vs AST
        if hasattr(self.query, 'to_ast'):
            ast = self.query.to_ast()
        else:
            ast = self.query
        
        return execute_ast(self.network, ast, params={})
    
    def _execute_query(self, network: Any) -> Any:
        """Execute query on a modified network.
        
        Args:
            network: Modified network
            
        Returns:
            QueryResult
        """
        from py3plex.dsl.executor import execute_ast
        
        # Handle QueryBuilder vs AST
        if hasattr(self.query, 'to_ast'):
            ast = self.query.to_ast()
        else:
            ast = self.query
        
        return execute_ast(network, ast, params={})
    
    def _aggregate_results(self, 
                          baseline: Any,
                          cf_dataframes: List[pd.DataFrame]) -> pd.DataFrame:
        """Aggregate counterfactual results into summary DataFrame.
        
        Args:
            baseline: Baseline QueryResult
            cf_dataframes: List of DataFrames from counterfactual runs
            
        Returns:
            DataFrame with aggregated statistics
        """
        if not cf_dataframes:
            return pd.DataFrame()
        
        # Get baseline DataFrame
        baseline_df = baseline.to_pandas()
        
        # Identify metric columns (exclude id, layer, etc.)
        exclude_cols = {"id", "layer", "type"}
        metric_cols = [c for c in baseline_df.columns 
                      if c not in exclude_cols and not c.startswith("_")]
        
        # Build summary DataFrame
        summary_data = []
        
        # Get unique items (using id column or index)
        if "id" in baseline_df.columns:
            items = baseline_df["id"].unique()
            id_col = "id"
        else:
            items = baseline_df.index.unique()
            id_col = "index"
        
        for item in items:
            row = {id_col: item}
            
            # Get baseline values
            if "id" in baseline_df.columns:
                baseline_row = baseline_df[baseline_df["id"] == item]
            else:
                baseline_row = baseline_df[baseline_df.index == item]
            
            if len(baseline_row) == 0:
                continue
            
            baseline_row = baseline_row.iloc[0]
            
            # Add layer if present
            if "layer" in baseline_row:
                row["layer"] = baseline_row["layer"]
            
            # Collect counterfactual values for each metric
            for metric in metric_cols:
                baseline_val = baseline_row.get(metric)
                row[f"{metric}_baseline"] = baseline_val
                
                # Collect CF values
                cf_values = []
                for cf_df in cf_dataframes:
                    if "id" in cf_df.columns:
                        cf_row = cf_df[cf_df["id"] == item]
                    else:
                        cf_row = cf_df[cf_df.index == item]
                    
                    if len(cf_row) > 0 and metric in cf_row.columns:
                        cf_values.append(cf_row.iloc[0][metric])
                
                if cf_values:
                    cf_array = np.array(cf_values)
                    row[f"{metric}_mean"] = float(np.mean(cf_array))
                    row[f"{metric}_std"] = float(np.std(cf_array))
                    row[f"{metric}_min"] = float(np.min(cf_array))
                    row[f"{metric}_max"] = float(np.max(cf_array))
                    
                    # Coefficient of variation
                    mean_val = row[f"{metric}_mean"]
                    if mean_val != 0:
                        row[f"{metric}_cv"] = row[f"{metric}_std"] / abs(mean_val)
                    else:
                        row[f"{metric}_cv"] = 0.0
                    
                    # Delta from baseline
                    if baseline_val is not None:
                        row[f"{metric}_delta"] = row[f"{metric}_mean"] - baseline_val
                        row[f"{metric}_delta_pct"] = (row[f"{metric}_delta"] / (abs(baseline_val) + 1e-10)) * 100
                else:
                    row[f"{metric}_mean"] = None
                    row[f"{metric}_std"] = None
                    row[f"{metric}_min"] = None
                    row[f"{metric}_max"] = None
                    row[f"{metric}_cv"] = None
                    row[f"{metric}_delta"] = None
                    row[f"{metric}_delta_pct"] = None
            
            summary_data.append(row)
        
        summary_df = pd.DataFrame(summary_data)
        
        # Set index
        if id_col == "id":
            summary_df = summary_df.set_index("id", drop=False)
        
        return summary_df
    
    def _build_metadata(self, baseline: Any) -> Dict[str, Any]:
        """Build provenance metadata.
        
        Args:
            baseline: Baseline QueryResult
            
        Returns:
            Metadata dictionary
        """
        # Get network fingerprint
        baseline_df = baseline.to_pandas()
        n_items = len(baseline_df)
        
        # Try to get network info
        try:
            n_nodes = len(list(self.network.get_nodes()))
        except:
            n_nodes = None
        
        try:
            n_edges = len(list(self.network.get_edges()))
        except:
            n_edges = None
        
        try:
            n_layers = len(self.network.get_layers())
        except:
            n_layers = None
        
        meta = {
            "provenance": {
                "intervention_type": self.spec.to_dict()["type"],
                "intervention_spec": self.spec.to_dict(),
                "intervention_hash": self.spec.spec_hash(),
                "repeats": self.repeats,
                "seed": self.seed,
                "streaming": self.streaming,
                "baseline_network": {
                    "n_nodes": n_nodes,
                    "n_edges": n_edges,
                    "n_layers": n_layers,
                },
                "baseline_results": {
                    "n_items": n_items,
                },
            }
        }
        
        return meta


def run_counterfactual(network: Any,
                      query: Any,
                      spec: InterventionSpec,
                      repeats: int = 30,
                      seed: Optional[int] = None) -> CounterfactualResult:
    """Convenience function to run a counterfactual analysis.
    
    Args:
        network: Network to analyze
        query: Query (AST or QueryBuilder)
        spec: Intervention specification
        repeats: Number of counterfactual runs
        seed: Random seed for reproducibility
        
    Returns:
        CounterfactualResult
    """
    engine = CounterfactualEngine(
        network=network,
        query=query,
        spec=spec,
        repeats=repeats,
        seed=seed,
        streaming=False
    )
    return engine.run()
