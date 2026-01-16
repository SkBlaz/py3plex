"""Benchmark result helper for QueryResult.

Provides convenient access to benchmark-specific views like leaderboards,
summaries, and traces.
"""

from typing import Any, Dict, List, Optional
import pandas as pd


class BenchmarkResultHelper:
    """Helper for accessing benchmark results.

    This class provides convenient methods for accessing benchmark-specific
    data from a QueryResult, including summary statistics, leaderboards,
    and algorithm traces.

    Attributes:
        result: Parent QueryResult object
    """

    def __init__(self, result: "QueryResult"):  # noqa: F821
        """Initialize helper.

        Args:
            result: Parent QueryResult
        """
        self.result = result

        # Check if this is a benchmark result
        if "benchmark" not in result.meta:
            raise ValueError("QueryResult does not contain benchmark data")

        self._meta = result.meta["benchmark"]

    def runs(self) -> pd.DataFrame:
        """Get run-level results as DataFrame.

        Returns all individual algorithm runs with full provenance.

        Returns:
            DataFrame with one row per (dataset, layer, algorithm, config, repeat)
        """
        return self.result.to_pandas()

    def summary(self) -> pd.DataFrame:
        """Get summary statistics across repeats.

        Aggregates runs by (dataset, layer, algorithm, config) and computes
        mean, std, and CI across repeats.

        Returns:
            DataFrame with aggregated statistics
        """
        return self._meta.get("summary", pd.DataFrame())

    def best_by_algo(self) -> pd.DataFrame:
        """Get best configuration per algorithm.

        For each algorithm, returns the configuration that performed best
        according to the selection mode.

        Returns:
            DataFrame with best config per algorithm
        """
        return self._meta.get("best_by_algo", pd.DataFrame())

    def leaderboard(self) -> pd.DataFrame:
        """Get compact leaderboard view.

        Shows algorithm rankings with key metrics, highlighting winners.

        Returns:
            DataFrame with ranked algorithms
        """
        return self._meta.get("leaderboard", pd.DataFrame())

    def pareto_front(self) -> Optional[pd.DataFrame]:
        """Get Pareto front solutions.

        Returns non-dominated solutions when using Pareto selection.

        Returns:
            DataFrame with Pareto optimal solutions, or None if not applicable
        """
        if "pareto_front" in self._meta:
            return self._meta["pareto_front"]
        return None

    def trace(self, algorithm: str) -> Optional[pd.DataFrame]:
        """Get algorithm trace (e.g., AutoCommunity candidates).

        Args:
            algorithm: Algorithm name (e.g., "autocommunity")

        Returns:
            DataFrame with trace data, or None if not available
        """
        traces = self._meta.get("traces", {})
        algo_traces = traces.get(algorithm, {})

        if not algo_traces:
            return None

        # Combine traces from all datasets/layers/repeats
        all_rows = []
        for key, trace in algo_traces.items():
            if isinstance(trace, list):
                for row in trace:
                    row_copy = row.copy()
                    if isinstance(key, tuple):
                        # Key is (dataset_id, layer_expr, repeat_id)
                        if len(key) == 3:
                            row_copy["dataset_id"] = key[0]
                            row_copy["layer_expr"] = key[1]
                            row_copy["repeat_id"] = key[2]
                    else:
                        row_copy["key"] = str(key)
                    all_rows.append(row_copy)

        if not all_rows:
            return None

        return pd.DataFrame(all_rows)

    def protocol(self) -> Dict[str, Any]:
        """Get protocol configuration.

        Returns:
            Dictionary with protocol settings (repeat, seed, budgets, etc.)
        """
        return self._meta.get("protocol", {})

    def budget_summary(self) -> pd.DataFrame:
        """Get budget usage summary per algorithm.

        Returns:
            DataFrame with budget accounting per algorithm
        """
        runs_df = self.runs()

        if "budget_used_ms" not in runs_df.columns:
            return pd.DataFrame()

        # Aggregate by algorithm
        summary = runs_df.groupby("algorithm").agg({
            "budget_limit_ms": "first",
            "budget_used_ms": "max",
            "eval_count": "max",
            "timed_out": "sum",
        }).reset_index()

        summary.columns = [
            "algorithm",
            "budget_limit_ms",
            "budget_used_ms",
            "eval_count",
            "configs_skipped",
        ]

        return summary
