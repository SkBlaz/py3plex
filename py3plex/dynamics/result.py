"""Simulation result container for dynamics module.

This module provides a rich result object designed for statistical analysis,
supporting multiple export formats (pandas, xarray, etc.).
"""

from typing import Any, Dict, List, Optional
import numpy as np


class SimulationResult:
    """Rich result object from simulation execution.

    Core storage:
    - Panel-style data for each measure
    - Metadata about process, params, network, etc.

    Standard DataFrame schemas:
    - For scalar global measures: ["replicate", "t", "value"]
    - For layer-based measures: ["replicate", "t", "layer", "value"]
    - For node-based measures: ["replicate", "t", "node", "layer", "value"]

    Attributes:
        process_name: Name of the simulated process
        measures: List of measure names collected
        data: Nested dict mapping measure names to DataFrames or arrays
        meta: Metadata dictionary (params, network info, etc.)
    """

    def __init__(self, process_name: str, measures: List[str],
                 data: Dict[str, Any], meta: Optional[Dict[str, Any]] = None):
        """Initialize SimulationResult.

        Args:
            process_name: Name of the simulated process
            measures: List of measure names
            data: Dictionary mapping measure names to data
            meta: Optional metadata dictionary
        """
        self.process_name = process_name
        self.measures = measures
        self.data = data
        self.meta = meta or {}

    def to_pandas(self, measure: Optional[str] = None):
        """Export results to pandas DataFrame(s).

        Args:
            measure: If provided, return DataFrame for that measure only.
                    If None, return dict mapping measure names to DataFrames.

        Returns:
            pandas.DataFrame or dict of DataFrames

        Raises:
            ImportError: If pandas is not available
            KeyError: If measure is not found
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required for to_pandas(). Install with: pip install pandas")

        def _to_dataframe(measure_name: str):
            """Convert a single measure to DataFrame."""
            measure_data = self.data.get(measure_name)
            if measure_data is None:
                return pd.DataFrame()

            if isinstance(measure_data, pd.DataFrame):
                return measure_data

            if isinstance(measure_data, dict):
                # Already structured data
                return pd.DataFrame(measure_data)

            if isinstance(measure_data, (list, np.ndarray)):
                # Time series data: shape (replicates, steps) or (steps,)
                arr = np.array(measure_data)
                if arr.ndim == 1:
                    # Single replicate
                    return pd.DataFrame({
                        "replicate": [0] * len(arr),
                        "t": list(range(len(arr))),
                        "value": arr.tolist(),
                    })
                elif arr.ndim == 2:
                    # Multiple replicates: (replicates, steps)
                    rows = []
                    for rep in range(arr.shape[0]):
                        for t in range(arr.shape[1]):
                            rows.append({
                                "replicate": rep,
                                "t": t,
                                "value": arr[rep, t],
                            })
                    return pd.DataFrame(rows)

            return pd.DataFrame()

        if measure is not None:
            if measure not in self.measures and measure not in self.data:
                raise KeyError(f"Unknown measure '{measure}'. Available: {self.measures}")
            return _to_dataframe(measure)

        return {m: _to_dataframe(m) for m in self.measures}

    def to_xarray(self, measure: Optional[str] = None):
        """Export results to xarray Dataset.

        Args:
            measure: If provided, return DataArray for that measure only.
                    If None, return Dataset with all measures.

        Returns:
            xarray.Dataset or xarray.DataArray

        Raises:
            ImportError: If xarray is not available
        """
        try:
            import xarray as xr
        except ImportError:
            raise ImportError("xarray is required for to_xarray(). Install with: pip install xarray")

        def _to_dataarray(measure_name: str):
            """Convert a single measure to DataArray."""
            measure_data = self.data.get(measure_name)
            if measure_data is None:
                return xr.DataArray()

            if isinstance(measure_data, np.ndarray):
                if measure_data.ndim == 1:
                    return xr.DataArray(
                        measure_data,
                        dims=["t"],
                        name=measure_name,
                    )
                elif measure_data.ndim == 2:
                    return xr.DataArray(
                        measure_data,
                        dims=["replicate", "t"],
                        name=measure_name,
                    )

            if isinstance(measure_data, list):
                return _to_dataarray(np.array(measure_data))

            return xr.DataArray(name=measure_name)

        if measure is not None:
            return _to_dataarray(measure)

        data_vars = {m: _to_dataarray(m) for m in self.measures}
        return xr.Dataset(data_vars, attrs=self.meta)

    def to_dict(self) -> Dict[str, Any]:
        """Export results as a dictionary.

        Returns:
            Dictionary with process_name, measures, data, and metadata
        """
        # Convert numpy arrays to lists for JSON serialization
        serializable_data = {}
        for key, value in self.data.items():
            if isinstance(value, np.ndarray):
                serializable_data[key] = value.tolist()
            else:
                serializable_data[key] = value

        return {
            "process_name": self.process_name,
            "measures": self.measures,
            "data": serializable_data,
            "meta": self.meta,
        }

    def plot(self, measure: str, ax=None, **kwargs):
        """Convenience plotting wrapper.

        Plots mean with confidence interval across replicates.

        Args:
            measure: Measure name to plot
            ax: Optional matplotlib axes to plot on
            **kwargs: Additional arguments passed to plot

        Returns:
            matplotlib axes object

        Raises:
            ImportError: If matplotlib is not available
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            raise ImportError("matplotlib is required for plot(). Install with: pip install matplotlib")

        if ax is None:
            _, ax = plt.subplots()

        df = self.to_pandas(measure)

        if df.empty:
            ax.set_title(f"{measure} (no data)")
            return ax

        if "replicate" in df.columns and df["replicate"].nunique() > 1:
            # Multiple replicates: plot mean with CI
            grouped = df.groupby("t")["value"]
            mean = grouped.mean()
            std = grouped.std()

            ax.plot(mean.index, mean.values, label=f"{measure} (mean)", **kwargs)
            ax.fill_between(
                mean.index,
                mean.values - 1.96 * std.values / np.sqrt(df["replicate"].nunique()),
                mean.values + 1.96 * std.values / np.sqrt(df["replicate"].nunique()),
                alpha=0.3,
                label="95% CI"
            )
        else:
            # Single replicate
            ax.plot(df["t"], df["value"], label=measure, **kwargs)

        ax.set_xlabel("Time step")
        ax.set_ylabel(measure)
        ax.set_title(f"{self.process_name}: {measure}")
        ax.legend()

        return ax

    def summary(self) -> Dict[str, Any]:
        """Get summary statistics for all measures.

        Returns:
            Dictionary with summary statistics per measure
        """
        summary = {
            "process_name": self.process_name,
            "replicates": self.meta.get("replicates", 1),
            "steps": self.meta.get("steps", 0),
            "measures": {},
        }

        for measure in self.measures:
            measure_data = self.data.get(measure)
            if measure_data is None:
                continue

            arr = np.array(measure_data) if not isinstance(measure_data, np.ndarray) else measure_data

            if arr.size > 0:
                summary["measures"][measure] = {
                    "mean": float(np.mean(arr)),
                    "std": float(np.std(arr)),
                    "min": float(np.min(arr)),
                    "max": float(np.max(arr)),
                    "final_mean": float(np.mean(arr[..., -1])) if arr.ndim > 0 else float(arr),
                }

        return summary

    def __repr__(self) -> str:
        return (f"SimulationResult(process_name='{self.process_name}', "
                f"measures={self.measures}, "
                f"replicates={self.meta.get('replicates', 1)}, "
                f"steps={self.meta.get('steps', 0)})")
