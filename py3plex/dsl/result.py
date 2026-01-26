"""Query result container for DSL v2.

This module provides a rich result object that supports multiple export formats
and includes metadata about the query execution.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple
import math


# Tolerance for matching quantile keys when finding CI bounds
_QUANTILE_TOLERANCE = 0.01

# Explanation attribute names that contain complex data structures
_EXPLANATION_ATTRS = {
    "top_neighbors",  # List of dicts
    "layers_present",  # List of strings
}


def _expand_explanation_value(attr_name: str, value: Any) -> Dict[str, Any]:
    """Expand an explanation value for pandas DataFrame.

    For simple values (int, float, str, None), returns as-is.
    For complex values (list, dict), converts to JSON string for DataFrame compatibility.

    Args:
        attr_name: Attribute name
        value: The explanation value

    Returns:
        Dictionary with the attribute name and processed value
    """
    import json

    if value is None:
        return {attr_name: None}
    elif isinstance(value, (int, float, str, bool)):
        return {attr_name: value}
    elif isinstance(value, list):
        # Convert list to JSON string for DataFrame
        # Special case: if it's a list of simple types, keep as list (converted to string)
        if all(isinstance(item, (int, float, str, bool, type(None))) for item in value):
            return {attr_name: str(value)}
        # For complex lists (e.g., list of dicts), convert to JSON
        return {attr_name: json.dumps(value)}
    elif isinstance(value, dict):
        # Convert dict to JSON string
        return {attr_name: json.dumps(value)}
    else:
        # Fallback: convert to string
        return {attr_name: str(value)}


def _expand_uncertainty_value(
    attr_name: str, value: Any, ci_level: float = 0.95, expand_samples: bool = False
) -> Dict[str, Any]:
    """Expand an uncertainty value into multiple columns.

    Args:
        attr_name: Base attribute name (e.g., "degree")
        value: The value (may be dict with uncertainty info or scalar)
        ci_level: Confidence interval level (default: 0.95)
        expand_samples: If True, include raw samples as JSON string (default: False)

    Returns:
        Dictionary with expanded columns
    """
    import json
    
    result = {}

    # Always include the point estimate
    if isinstance(value, dict) and "mean" in value:
        result[attr_name] = value["mean"]

        # Add std if available
        if "std" in value:
            result[f"{attr_name}_std"] = value["std"]
        else:
            result[f"{attr_name}_std"] = None

        # Add CI bounds if quantiles are available
        quantiles = value.get("quantiles", {})
        if quantiles:
            # Calculate quantile keys for the CI level
            lower_q = (1 - ci_level) / 2
            upper_q = 1 - (1 - ci_level) / 2

            # Find closest available quantiles
            ci_low = quantiles.get(lower_q)
            ci_high = quantiles.get(upper_q)

            # If exact quantiles not found, try to find closest
            if ci_low is None or ci_high is None:
                sorted_qs = sorted(quantiles.keys())
                if sorted_qs:
                    # Find closest lower quantile (within tolerance)
                    lower_candidates = [
                        q for q in sorted_qs if q <= lower_q + _QUANTILE_TOLERANCE
                    ]
                    if lower_candidates:
                        ci_low = quantiles[lower_candidates[-1]]

                    # Find closest upper quantile (within tolerance)
                    upper_candidates = [
                        q for q in sorted_qs if q >= upper_q - _QUANTILE_TOLERANCE
                    ]
                    if upper_candidates:
                        ci_high = quantiles[upper_candidates[0]]

            # Convert CI level to percentage for column names (e.g., 0.95 -> ci95)
            ci_pct = int(ci_level * 100)

            result[f"{attr_name}_ci{ci_pct}_low"] = ci_low
            result[f"{attr_name}_ci{ci_pct}_high"] = ci_high

            # Calculate width if both bounds available
            if ci_low is not None and ci_high is not None:
                result[f"{attr_name}_ci{ci_pct}_width"] = ci_high - ci_low
            else:
                result[f"{attr_name}_ci{ci_pct}_width"] = None
        else:
            # No quantiles - set CI columns to None
            ci_pct = int(ci_level * 100)
            result[f"{attr_name}_ci{ci_pct}_low"] = None
            result[f"{attr_name}_ci{ci_pct}_high"] = None
            result[f"{attr_name}_ci{ci_pct}_width"] = None
        
        # Add raw samples if requested
        if expand_samples and "samples" in value and value["samples"] is not None:
            try:
                result[f"{attr_name}_samples"] = json.dumps(value["samples"])
            except (TypeError, ValueError):
                result[f"{attr_name}_samples"] = None
    else:
        # Deterministic value - just use as-is
        result[attr_name] = value
        # Set uncertainty columns to None or 0
        ci_pct = int(ci_level * 100)
        result[f"{attr_name}_std"] = 0.0 if value is not None else None
        result[f"{attr_name}_ci{ci_pct}_low"] = value
        result[f"{attr_name}_ci{ci_pct}_high"] = value
        result[f"{attr_name}_ci{ci_pct}_width"] = 0.0 if value is not None else None

    return result


def _expand_explanation_value(attr_name: str, value: Any) -> Dict[str, Any]:
    """Expand an explanation value for pandas DataFrame.

    For simple values (int, float, str, None), returns as-is.
    For complex values (list, dict), converts to JSON string for DataFrame compatibility.

    Args:
        attr_name: Attribute name
        value: The explanation value

    Returns:
        Dictionary with the attribute name and processed value
    """
    import json

    if value is None:
        return {attr_name: None}
    elif isinstance(value, (int, float, str, bool)):
        return {attr_name: value}
    elif isinstance(value, list):
        # Convert list to JSON string for DataFrame
        # Special case: if it's a list of simple types, keep as list
        if all(isinstance(item, (int, float, str, bool, type(None))) for item in value):
            return {attr_name: str(value)}
        # For complex lists (e.g., list of dicts), convert to JSON
        return {attr_name: json.dumps(value)}
    elif isinstance(value, dict):
        # Convert dict to JSON string
        return {attr_name: json.dumps(value)}
    else:
        # Fallback: convert to string
        return {attr_name: str(value)}


def _expand_uncertainty_value_OLD_BACKUP(
    attr_name: str, value: Any, ci_level: float = 0.95
) -> Dict[str, Any]:
    """Expand an uncertainty value into multiple columns.

    Args:
        attr_name: Base attribute name (e.g., "degree")
        value: The value (may be dict with uncertainty info or scalar)
        ci_level: Confidence interval level (default: 0.95)

    Returns:
        Dictionary with expanded columns
    """
    result = {}

    # Always include the point estimate
    if isinstance(value, dict) and "mean" in value:
        result[attr_name] = value["mean"]

        # Add std if available
        if "std" in value:
            result[f"{attr_name}_std"] = value["std"]
        else:
            result[f"{attr_name}_std"] = None

        # Add CI bounds if quantiles are available
        quantiles = value.get("quantiles", {})
        if quantiles:
            # Calculate quantile keys for the CI level
            lower_q = (1 - ci_level) / 2
            upper_q = 1 - (1 - ci_level) / 2

            # Find closest available quantiles
            ci_low = quantiles.get(lower_q)
            ci_high = quantiles.get(upper_q)

            # If exact quantiles not found, try to find closest
            if ci_low is None or ci_high is None:
                sorted_qs = sorted(quantiles.keys())
                if sorted_qs:
                    # Find closest lower quantile (within tolerance)
                    lower_candidates = [
                        q for q in sorted_qs if q <= lower_q + _QUANTILE_TOLERANCE
                    ]
                    if lower_candidates:
                        ci_low = quantiles[lower_candidates[-1]]

                    # Find closest upper quantile (within tolerance)
                    upper_candidates = [
                        q for q in sorted_qs if q >= upper_q - _QUANTILE_TOLERANCE
                    ]
                    if upper_candidates:
                        ci_high = quantiles[upper_candidates[0]]

            # Convert CI level to percentage for column names (e.g., 0.95 -> ci95)
            ci_pct = int(ci_level * 100)

            result[f"{attr_name}_ci{ci_pct}_low"] = ci_low
            result[f"{attr_name}_ci{ci_pct}_high"] = ci_high

            # Calculate width if both bounds available
            if ci_low is not None and ci_high is not None:
                result[f"{attr_name}_ci{ci_pct}_width"] = ci_high - ci_low
            else:
                result[f"{attr_name}_ci{ci_pct}_width"] = None
        else:
            # No quantiles - set CI columns to None
            ci_pct = int(ci_level * 100)
            result[f"{attr_name}_ci{ci_pct}_low"] = None
            result[f"{attr_name}_ci{ci_pct}_high"] = None
            result[f"{attr_name}_ci{ci_pct}_width"] = None
    else:
        # Deterministic value - just use as-is
        result[attr_name] = value
        # Set uncertainty columns to None or 0
        ci_pct = int(ci_level * 100)
        result[f"{attr_name}_std"] = 0.0 if value is not None else None
        result[f"{attr_name}_ci{ci_pct}_low"] = value
        result[f"{attr_name}_ci{ci_pct}_high"] = value
        result[f"{attr_name}_ci{ci_pct}_width"] = 0.0 if value is not None else None

    return result


class QueryResult:
    """Rich result object from DSL query execution.

    Provides access to query results with multiple export formats and
    execution metadata.

    Attributes:
        target: 'nodes' or 'edges'
        items: Sequence of node/edge identifiers
        attributes: Dictionary of computed attributes (column -> values or dict)
        meta: Metadata about the query execution
        computed_metrics: Set of metrics that were computed during query execution
        sensitivity_result: Optional sensitivity analysis results (SensitivityResult)
    """

    def __init__(
        self,
        target: str,
        items: List[Any],
        attributes: Optional[Dict[str, Union[List[Any], Dict[Any, Any]]]] = None,
        meta: Optional[Dict[str, Any]] = None,
        computed_metrics: Optional[set] = None,
    ):
        """Initialize QueryResult.

        Args:
            target: 'nodes' or 'edges'
            items: List of node/edge identifiers
            attributes: Dictionary mapping attribute names to value lists
            meta: Optional metadata dictionary
            computed_metrics: Optional set of metrics computed during execution
        """
        self.target = target
        self.items = items
        self.attributes = attributes or {}
        self.meta = meta or {}
        self.computed_metrics = computed_metrics or set()
        self.sensitivity_result = (
            None  # Will be set by executor if sensitivity is requested
        )

    @property
    def provenance(self) -> Optional[Dict[str, Any]]:
        """Get provenance information from metadata.

        Returns:
            Provenance dictionary if available, None otherwise
        """
        return self.meta.get("provenance")

    @property
    def is_replayable(self) -> bool:
        """Check if this result has replayable provenance.

        Returns:
            True if result can be replayed deterministically
        """
        prov = self.provenance
        if not prov:
            return False

        # Check for replayable mode
        mode = prov.get("mode")
        if mode != "replayable":
            return False

        # Check for required fields
        query_info = prov.get("query", {})
        if not query_info.get("ast_serialized"):
            return False

        # Check for network capture
        network_capture = prov.get("network_capture", {})
        has_snapshot = (
            network_capture.get("snapshot_data") is not None
            or network_capture.get("snapshot_external_path") is not None
            or network_capture.get("delta_ops") is not None
        )

        return has_snapshot

    @property
    def sensitivity_curves(self) -> Optional[Dict[str, Any]]:
        """Get sensitivity curves if sensitivity analysis was run.

        Returns:
            Dictionary of stability curves keyed by metric name, or None
        """
        if self.sensitivity_result is not None:
            return self.sensitivity_result.curves
        return None

    @property
    def has_sensitivity(self) -> bool:
        """Check if this result includes sensitivity analysis.

        Returns:
            True if sensitivity results are available
        """
        return self.sensitivity_result is not None

    def replay(
        self, backend: Optional[Any] = None, strict: bool = True
    ) -> "QueryResult":
        """Replay this query to reproduce the result.

        Reconstructs the network and query from provenance, then re-executes
        to produce a new QueryResult. With replayable provenance, the new
        result should match this one deterministically.

        Args:
            backend: Optional backend override (not currently used)
            strict: If True, enforce strict version compatibility checks

        Returns:
            New QueryResult from replayed query

        Raises:
            ValueError: If result is not replayable
            ReplayError: If replay fails
        """
        if not self.is_replayable:
            raise ValueError(
                "Result is not replayable. Provenance mode must be 'replayable' "
                "with captured network snapshot and serialized AST."
            )

        # Import replay functionality
        from py3plex.provenance.schema import ProvenanceSchema
        from py3plex.provenance.replay import replay_query, ReplayError

        try:
            # Reconstruct provenance schema
            prov_dict = self.provenance
            prov_schema = ProvenanceSchema.from_dict(prov_dict)

            # Replay query
            result = replay_query(prov_schema, strict=strict)
            return result

        except Exception as e:
            if isinstance(e, ReplayError):
                raise
            raise ReplayError(f"Failed to replay query: {e}")

    def export_bundle(
        self,
        path: Union[str, "Path"],
        compress: bool = True,
        include_results: bool = True,
    ) -> None:
        """Export this result with provenance as a portable bundle.

        Creates a file or directory containing:
        - Provenance metadata (query, network, seeds, environment)
        - Optionally, the query results
        - Network snapshot if needed for replay

        Args:
            path: Output file path (will add .json or .json.gz extension)
            compress: Whether to compress the bundle with gzip
            include_results: Whether to include result data in bundle

        Raises:
            BundleError: If export fails
        """
        from py3plex.provenance.bundle import export_bundle as _export_bundle

        _export_bundle(self, path, compress=compress, include_results=include_results)

    @property
    def nodes(self) -> List[Any]:
        """Get nodes (raises if target is not 'nodes')."""
        if self.target != "nodes":
            raise ValueError(f"Cannot access nodes - target is '{self.target}'")
        return self.items

    @property
    def edges(self) -> List[Any]:
        """Get edges (raises if target is not 'edges')."""
        if self.target != "edges":
            raise ValueError(f"Cannot access edges - target is '{self.target}'")
        return self.items

    @property
    def count(self) -> int:
        """Get number of items in result."""
        return len(self.items)

    def __len__(self) -> int:
        """Return number of items."""
        return len(self.items)

    def __iter__(self):
        """Iterate over items."""
        return iter(self.items)

    @property
    def benchmark(self):
        """Get benchmark result helper.

        Provides convenient access to benchmark-specific views like
        leaderboards, summaries, and traces.

        Returns:
            BenchmarkResultHelper instance

        Raises:
            ValueError: If result does not contain benchmark data

        Example:
            >>> res = B.community().on(net).algorithms("louvain").execute()
            >>> leaderboard = res.benchmark.leaderboard()
            >>> summary = res.benchmark.summary()
            >>> trace = res.benchmark.trace("autocommunity")
        """
        from py3plex.dsl.benchmark_result import BenchmarkResultHelper

        return BenchmarkResultHelper(self)
    
    def has_uq(self, column: str) -> bool:
        """Check if a column contains UQ information.
        
        Args:
            column: Name of the column to check
            
        Returns:
            True if the column contains UQ dicts, False otherwise
        """
        if column not in self.attributes:
            return False
        
        values = self.attributes[column]
        
        # Check if it's a dict-style column
        if isinstance(values, dict):
            # Check first value
            first_val = next(iter(values.values()), None)
            return isinstance(first_val, dict) and ("mean" in first_val or "value" in first_val)
        
        # Check if it's a list-style column
        if isinstance(values, list) and values:
            first_val = values[0]
            return isinstance(first_val, dict) and ("mean" in first_val or "value" in first_val)
        
        return False
    
    @property
    def uq_columns(self) -> List[str]:
        """Get list of columns that contain UQ information.
        
        Returns:
            List of column names containing UQ dicts
        """
        return [col for col in self.attributes.keys() if self.has_uq(col)]

    def to_pandas(
        self,
        multiindex: bool = False,
        include_grouping: bool = True,
        expand_uncertainty: bool = False,
        expand_explanations: bool = False,
        expand_samples: bool = False,
    ):
        """Export results to pandas DataFrame.

        For node queries: Returns DataFrame with 'id' column plus computed attributes
        For edge queries: Returns DataFrame with 'source', 'target', 'source_layer',
                         'target_layer', 'weight' columns plus computed attributes

        Args:
            multiindex: If True and grouping metadata is present, set DataFrame index
                       to the grouping keys (e.g., ["layer"] or ["src_layer", "dst_layer"])
            include_grouping: If True and grouping metadata is present, ensure grouping
                            key columns are included in the DataFrame
            expand_uncertainty: If True, expand uncertainty metrics into multiple columns:
                              - metric (point estimate/mean)
                              - metric_std (standard deviation)
                              - metric_ci95_low (95% CI lower bound)
                              - metric_ci95_high (95% CI upper bound)
                              - metric_ci95_width (CI width)
                              - p_present (if available from propagate mode)
                              - p_selected (if available from propagate mode with selection)
                              - rank_uq_* (if available from propagate mode with selection)
            expand_explanations: If True, expand explanation fields into columns.
                               Explanations are attached via .explain() in the query.
                               Fields like top_neighbors (list) are converted to JSON strings.
            expand_samples: If True, include raw sample arrays from UQ results as JSON strings.
                          Only applies when expand_uncertainty=True. Default False to avoid 
                          overwhelming output.

        Returns:
            pandas.DataFrame with items and computed attributes

        Raises:
            ImportError: If pandas is not available

        Example:
            >>> result = Q.nodes().uq(UQ.fast()).compute("degree").execute(net)
            >>> df = result.to_pandas(expand_uncertainty=True)
            >>> # df now has columns: id, layer, degree, degree_std, degree_ci95_low, degree_ci95_high, degree_ci95_width

            >>> result = Q.nodes().explain().compute("degree").execute(net)
            >>> df = result.to_pandas(expand_explanations=True)
            >>> # df now has explanation columns: community_id, community_size, top_neighbors, etc.
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "pandas is required for to_pandas(). Install with: pip install pandas"
            )

        if self.target == "communities":
            # Build community dataframe
            rows = []
            for comm_id in self.items:
                row = {"community_id": comm_id}

                # Add computed attributes
                for attr_name, values in self.attributes.items():
                    if isinstance(values, dict):
                        if comm_id in values:
                            value = values[comm_id]

                            if expand_uncertainty:
                                # Expand uncertainty into multiple columns
                                expanded = _expand_uncertainty_value(attr_name, value, expand_samples=expand_samples)
                                row.update(expanded)
                            else:
                                row[attr_name] = value
                        else:
                            if expand_uncertainty:
                                # Add None for all expanded columns
                                ci_pct = 95  # Default CI level
                                row[attr_name] = None
                                row[f"{attr_name}_std"] = None
                                row[f"{attr_name}_ci{ci_pct}_low"] = None
                                row[f"{attr_name}_ci{ci_pct}_high"] = None
                                row[f"{attr_name}_ci{ci_pct}_width"] = None
                            else:
                                row[attr_name] = None
                    else:
                        # If values is a list, use index
                        idx = self.items.index(comm_id)
                        if idx < len(values):
                            value = values[idx]

                            if expand_uncertainty:
                                # Expand uncertainty into multiple columns
                                expanded = _expand_uncertainty_value(attr_name, value, expand_samples=expand_samples)
                                row.update(expanded)
                            else:
                                row[attr_name] = value
                        else:
                            if expand_uncertainty:
                                # Add None for all expanded columns
                                ci_pct = 95  # Default CI level
                                row[attr_name] = None
                                row[f"{attr_name}_std"] = None
                                row[f"{attr_name}_ci{ci_pct}_low"] = None
                                row[f"{attr_name}_ci{ci_pct}_high"] = None
                                row[f"{attr_name}_ci{ci_pct}_width"] = None
                            else:
                                row[attr_name] = None

                rows.append(row)

            df = pd.DataFrame(rows)

            # Apply grouping metadata if present
            if include_grouping and "grouping" in self.meta:
                grouping_info = self.meta["grouping"]
                if multiindex and "group_by" in grouping_info:
                    # Set multiindex using grouping keys
                    index_cols = grouping_info["group_by"]
                    # Only set index if all keys exist in the dataframe
                    if all(col in df.columns for col in index_cols):
                        df = df.set_index(index_cols)

            return df

        elif self.target == "edges":
            # Build edge dataframe with standard columns
            rows = []
            for edge in self.items:
                if isinstance(edge, tuple) and len(edge) >= 2:
                    source, target = edge[0], edge[1]
                    row = {}

                    # Extract source and target info
                    if isinstance(source, tuple) and len(source) >= 2:
                        row["source"] = source[0]
                        row["source_layer"] = source[1]
                    else:
                        row["source"] = source
                        row["source_layer"] = None

                    if isinstance(target, tuple) and len(target) >= 2:
                        row["target"] = target[0]
                        row["target_layer"] = target[1]
                    else:
                        row["target"] = target
                        row["target_layer"] = None

                    # Extract weight from edge data
                    if len(edge) >= 3 and isinstance(edge[2], dict):
                        row["weight"] = edge[2].get("weight", 1.0)
                    else:
                        row["weight"] = 1.0

                    # Add computed attributes
                    # Use hashable edge key (u, v) for lookup
                    edge_key = (source, target)
                    for attr_name, values in self.attributes.items():
                        if isinstance(values, dict):
                            # Use simplified key for lookup
                            if edge_key in values:
                                value = values[edge_key]

                                if expand_uncertainty:
                                    # Expand uncertainty into multiple columns
                                    expanded = _expand_uncertainty_value(
                                        attr_name, value
                                    )
                                    row.update(expanded)
                                else:
                                    # Preserve uncertainty dictionaries unless explicitly expanded.
                                    row[attr_name] = value
                            else:
                                if expand_uncertainty:
                                    # Add None for all expanded columns
                                    ci_pct = 95  # Default CI level
                                    row[attr_name] = None
                                    row[f"{attr_name}_std"] = None
                                    row[f"{attr_name}_ci{ci_pct}_low"] = None
                                    row[f"{attr_name}_ci{ci_pct}_high"] = None
                                    row[f"{attr_name}_ci{ci_pct}_width"] = None
                                else:
                                    row[attr_name] = None
                        else:
                            # If values is a list, use index
                            idx = self.items.index(edge)
                            if idx < len(values):
                                value = values[idx]

                                if expand_uncertainty:
                                    # Expand uncertainty into multiple columns
                                    expanded = _expand_uncertainty_value(
                                        attr_name, value
                                    )
                                    row.update(expanded)
                                else:
                                    # Preserve uncertainty dictionaries unless explicitly expanded.
                                    row[attr_name] = value
                            else:
                                if expand_uncertainty:
                                    # Add None for all expanded columns
                                    ci_pct = 95  # Default CI level
                                    row[attr_name] = None
                                    row[f"{attr_name}_std"] = None
                                    row[f"{attr_name}_ci{ci_pct}_low"] = None
                                    row[f"{attr_name}_ci{ci_pct}_high"] = None
                                    row[f"{attr_name}_ci{ci_pct}_width"] = None
                                else:
                                    row[attr_name] = None

                    rows.append(row)

            df = pd.DataFrame(rows)

            # Apply grouping metadata if present
            if include_grouping and "grouping" in self.meta:
                grouping_info = self.meta["grouping"]
                if multiindex and grouping_info.get("keys"):
                    # Set multiindex using grouping keys
                    index_cols = grouping_info["keys"]
                    # Only set index if all keys exist in the dataframe
                    if all(col in df.columns for col in index_cols):
                        df = df.set_index(index_cols)

            return df

        else:
            # Node dataframe
            rows = []
            for node_item in self.items:
                row = {}

                # Extract node info - nodes are (node_id, layer) tuples
                if isinstance(node_item, tuple) and len(node_item) >= 2:
                    row["id"] = node_item[0]
                    row["layer"] = node_item[1]
                else:
                    row["id"] = node_item
                    row["layer"] = None

                # Add computed attributes
                for attr_name, values in self.attributes.items():
                    # Check if this is an explanation attribute
                    is_explanation = attr_name in _EXPLANATION_ATTRS or any(
                        attr_name.startswith(prefix)
                        for prefix in ["community_", "layers_", "n_layers_", "top_"]
                    )

                    if isinstance(values, dict):
                        # Use node_item (full tuple) as key
                        if node_item in values:
                            value = values[node_item]

                            # Handle explanations
                            if is_explanation and expand_explanations:
                                # Expand explanation value (converts complex types to JSON strings)
                                expanded = _expand_explanation_value(attr_name, value)
                                row.update(expanded)
                            elif expand_uncertainty and not is_explanation:
                                # Expand uncertainty into multiple columns
                                expanded = _expand_uncertainty_value(attr_name, value, expand_samples=expand_samples)
                                row.update(expanded)
                            else:
                                # Preserve original value
                                row[attr_name] = value
                        else:
                            if expand_uncertainty and not is_explanation:
                                # Add None for all expanded columns
                                ci_pct = 95  # Default CI level
                                row[attr_name] = None
                                row[f"{attr_name}_std"] = None
                                row[f"{attr_name}_ci{ci_pct}_low"] = None
                                row[f"{attr_name}_ci{ci_pct}_high"] = None
                                row[f"{attr_name}_ci{ci_pct}_width"] = None
                            else:
                                row[attr_name] = None
                    else:
                        # If values is a list, use index
                        idx = self.items.index(node_item)
                        if idx < len(values):
                            value = values[idx]

                            # Handle explanations
                            if is_explanation and expand_explanations:
                                expanded = _expand_explanation_value(attr_name, value)
                                row.update(expanded)
                            elif expand_uncertainty and not is_explanation:
                                # Expand uncertainty into multiple columns
                                expanded = _expand_uncertainty_value(attr_name, value, expand_samples=expand_samples)
                                row.update(expanded)
                            else:
                                # Preserve original value
                                row[attr_name] = value
                        else:
                            if expand_uncertainty and not is_explanation:
                                # Add None for all expanded columns
                                ci_pct = 95  # Default CI level
                                row[attr_name] = None
                                row[f"{attr_name}_std"] = None
                                row[f"{attr_name}_ci{ci_pct}_low"] = None
                                row[f"{attr_name}_ci{ci_pct}_high"] = None
                                row[f"{attr_name}_ci{ci_pct}_width"] = None
                            else:
                                row[attr_name] = None

                rows.append(row)

            # Create DataFrame with proper columns even if empty
            if rows:
                df = pd.DataFrame(rows)
            else:
                # Return empty DataFrame with expected columns
                columns = ["id", "layer"] + list(self.attributes.keys())
                df = pd.DataFrame(columns=columns)

            # Apply grouping metadata if present
            if include_grouping and "grouping" in self.meta:
                grouping_info = self.meta["grouping"]
                if multiindex and grouping_info.get("keys"):
                    # Set multiindex using grouping keys
                    index_cols = grouping_info["keys"]
                    # Only set index if all keys exist in the dataframe
                    if all(col in df.columns for col in index_cols):
                        df = df.set_index(index_cols)

            return df

    def to_networkx(self, network: Optional[Any] = None):
        """Export results to NetworkX graph.

        For node queries: Returns subgraph containing the selected nodes
        For edge queries: Returns subgraph containing the selected edges and their endpoints

        Args:
            network: Optional source network to extract subgraph from

        Returns:
            networkx.Graph subgraph containing result items

        Raises:
            ImportError: If networkx is not available
        """
        import networkx as nx

        if network is not None and hasattr(network, "core_network"):
            G = network.core_network
        else:
            # Create new graph with just the items
            G = nx.Graph()
            if self.target == "nodes":
                G.add_nodes_from(self.items)
            else:
                # For edges, add edges with their attributes
                for edge in self.items:
                    if isinstance(edge, tuple) and len(edge) >= 2:
                        u, v = edge[0], edge[1]
                        attrs = (
                            edge[2]
                            if len(edge) >= 3 and isinstance(edge[2], dict)
                            else {}
                        )
                        G.add_edge(u, v, **attrs)

        # Create subgraph with result items
        if self.target == "nodes":
            subgraph = G.subgraph(self.items).copy()

            # Attach computed attributes to nodes
            for attr_name, values in self.attributes.items():
                if isinstance(values, dict):
                    for node, val in values.items():
                        if node in subgraph:
                            subgraph.nodes[node][attr_name] = val
                elif len(values) == len(self.items):
                    for item, val in zip(self.items, values):
                        if item in subgraph:
                            subgraph.nodes[item][attr_name] = val
        else:
            # For edges, create a graph with the selected edges
            # First, collect all nodes involved in selected edges
            nodes_in_edges = set()
            edge_list = []

            for edge in self.items:
                if isinstance(edge, tuple) and len(edge) >= 2:
                    u, v = edge[0], edge[1]
                    nodes_in_edges.add(u)
                    nodes_in_edges.add(v)

                    # Get edge data from original graph or from edge tuple
                    edge_data = {}
                    if G.has_edge(u, v):
                        # For multigraphs, get_edge_data needs special handling
                        if isinstance(G, nx.MultiGraph):
                            # Get first edge data (multigraphs have multiple edges)
                            all_edge_data = G.get_edge_data(u, v)
                            if all_edge_data:
                                # Get first edge's data
                                first_key = list(all_edge_data.keys())[0]
                                edge_data = all_edge_data[first_key].copy()
                        else:
                            edge_data = G.get_edge_data(u, v, {})
                            if isinstance(edge_data, dict):
                                edge_data = edge_data.copy()
                    elif len(edge) >= 3 and isinstance(edge[2], dict):
                        edge_data = edge[2].copy()

                    edge_list.append((u, v, edge_data))

            # Create new graph with selected edges
            if isinstance(G, nx.MultiGraph):
                subgraph = nx.MultiGraph()
            elif isinstance(G, nx.DiGraph):
                subgraph = nx.DiGraph()
            else:
                subgraph = nx.Graph()

            # Add nodes with their attributes
            for node in nodes_in_edges:
                if node in G:
                    subgraph.add_node(node, **G.nodes[node])
                else:
                    subgraph.add_node(node)

            # Add edges with their attributes
            for u, v, data in edge_list:
                subgraph.add_edge(u, v, **data)

            # Attach computed edge attributes
            for attr_name, values in self.attributes.items():
                if isinstance(values, dict):
                    for edge, val in values.items():
                        if isinstance(edge, tuple) and len(edge) >= 2:
                            u, v = edge[0], edge[1]
                            if subgraph.has_edge(u, v):
                                subgraph[u][v][attr_name] = val

        return subgraph

    def to_arrow(self):
        """Export results to Apache Arrow table.

        Returns:
            pyarrow.Table with items and computed attributes

        Raises:
            ImportError: If pyarrow is not available
        """
        try:
            import pyarrow as pa
        except ImportError:
            raise ImportError(
                "pyarrow is required for to_arrow(). Install with: pip install pyarrow"
            )

        # Convert items to strings for Arrow compatibility
        data = {"id": [str(item) for item in self.items]}

        for attr_name, values in self.attributes.items():
            if isinstance(values, dict):
                data[attr_name] = [values.get(item, None) for item in self.items]
            elif len(values) == len(self.items):
                data[attr_name] = list(values)
            else:
                data[attr_name] = list(values) + [None] * (
                    len(self.items) - len(values)
                )

        return pa.table(data)

    def to_parquet(self, path: str):
        """Export results to Parquet file.

        Args:
            path: Output file path

        Raises:
            ImportError: If pyarrow is not available
        """
        try:
            import pyarrow.parquet as pq
        except ImportError:
            raise ImportError(
                "pyarrow is required for to_parquet(). Install with: pip install pyarrow"
            )

        table = self.to_arrow()
        pq.write_table(table, path)

    def to_dict(self) -> Dict[str, Any]:
        """Export results as a dictionary.

        Returns:
            Dictionary with target, items, attributes, and metadata
        """
        return {
            "target": self.target,
            self.target: self.items,
            "count": len(self.items),
            "computed": self.attributes,
            "meta": self.meta,
        }

    def group_summary(self):
        """Return a summary DataFrame with one row per group.

        Returns a pandas DataFrame containing:
        - Grouping key columns (e.g., "layer", "src_layer", "dst_layer")
        - n_items: Number of items (nodes/edges) in each group
        - Any group-level coverage metrics if available

        This method only uses information already present in the result and
        does not recompute expensive measures.

        Returns:
            pandas.DataFrame with one row per group

        Raises:
            ImportError: If pandas is not available
            ValueError: If result does not have grouping metadata
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "pandas is required for group_summary(). Install with: pip install pandas"
            )

        # Check that grouping metadata exists
        if "grouping" not in self.meta:
            from .errors import GroupingError

            raise GroupingError(
                "group_summary() is only defined for grouped results. "
                "Use .per_layer() or .per_layer_pair() to create a grouped query."
            )

        grouping_info = self.meta["grouping"]
        groups = grouping_info.get("groups", [])

        # Build rows from group metadata
        rows = []
        for group_meta in groups:
            row = {}

            # Add grouping key columns
            key_dict = group_meta.get("key", {})
            row.update(key_dict)

            # Add n_items
            row["n_items"] = group_meta.get("n_items", 0)

            # Add any additional metadata (e.g., coverage metrics)
            for k, v in group_meta.items():
                if k not in ("key", "n_items"):
                    row[k] = v

            rows.append(row)

        return pd.DataFrame(rows)
    
    def counterexample(
        self,
        claim: str,
        params: Optional[Dict[str, Any]] = None,
        seed: int = 42,
        find_minimal: bool = True,
        budget_max_tests: int = 200,
        budget_max_witness_size: int = 500,
        initial_radius: int = 2,
    ) -> Optional[Any]:
        """Find counterexample for a claim using query result.
        
        This is a convenience method that builds a counterexample query from
        the current result's network context.
        
        Args:
            claim: Claim string (e.g., "degree__ge(k) -> pagerank__rank_gt(r)")
            params: Parameter bindings (e.g., {"k": 10, "r": 50})
            seed: Random seed for determinism
            find_minimal: Whether to minimize witness
            budget_max_tests: Maximum violation tests during minimization
            budget_max_witness_size: Maximum witness size (nodes)
            initial_radius: Ego subgraph radius
            
        Returns:
            Counterexample object if found, None otherwise
            
        Raises:
            ValueError: If network context is not available
            CounterexampleNotFound: If no violation exists
            
        Example:
            >>> result = Q.nodes().compute("degree", "pagerank").execute(net)
            >>> cex = result.counterexample(
            ...     claim="degree__ge(k) -> pagerank__rank_gt(r)",
            ...     params={"k": 10, "r": 50},
            ...     seed=42
            ... )
        """
        from py3plex.counterexamples import find_counterexample
        from py3plex.counterexamples.types import Budget
        
        # Try to get network from meta
        network = self.meta.get("_network")
        if network is None:
            raise ValueError(
                "Network context not available in QueryResult. "
                "Cannot generate counterexample from result alone."
            )
        
        if params is None:
            params = {}
        
        budget = Budget(
            max_tests=budget_max_tests,
            max_witness_size=budget_max_witness_size,
        )
        
        # Extract layers from result if available
        layers = None
        if "layers" in self.meta:
            layers = self.meta["layers"]
        
        return find_counterexample(
            network=network,
            claim_str=claim,
            params=params,
            layers=layers,
            seed=seed,
            find_minimal=find_minimal,
            budget=budget,
            initial_radius=initial_radius,
        )

    def __repr__(self) -> str:
        """Enhanced representation showing full query context."""
        parts = [f"QueryResult("]
        parts.append(f"  target='{self.target}'")
        parts.append(f"  count={len(self.items)}")
        
        # Show computed attributes if any
        if self.attributes:
            attr_names = list(self.attributes.keys())
            if len(attr_names) <= 3:
                parts.append(f"  attributes=[{', '.join(repr(a) for a in attr_names)}]")
            else:
                parts.append(f"  attributes=[{', '.join(repr(a) for a in attr_names[:3])}, ... +{len(attr_names)-3} more]")
        
        # Show computed metrics if tracked
        if self.computed_metrics:
            metrics = sorted(self.computed_metrics)
            if len(metrics) <= 3:
                parts.append(f"  computed=[{', '.join(repr(m) for m in metrics)}]")
            else:
                parts.append(f"  computed=[{', '.join(repr(m) for m in metrics[:3])}, ... +{len(metrics)-3} more]")
        
        # Show grouping status
        if "grouping" in self.meta:
            grouping_info = self.meta["grouping"]
            if grouping_info:
                group_type = grouping_info.get("type", "unknown")
                n_groups = len(grouping_info.get("groups", []))
                parts.append(f"  grouping='{group_type}' ({n_groups} groups)")
        
        # Show uncertainty status
        if self.meta.get("has_uncertainty"):
            uq_method = self.meta.get("uq_method", "unknown")
            parts.append(f"  uncertainty='{uq_method}'")
        
        # Show provenance status
        if self.provenance:
            mode = self.provenance.get("mode", "unknown")
            parts.append(f"  provenance='{mode}'")
            if self.is_replayable:
                parts.append(f"  replayable=True")
        
        parts.append(")")
        
        # If single line, use compact format
        result = "\n".join(parts) if len(parts) > 4 else (
            f"QueryResult(target='{self.target}', count={len(self.items)}, "
            f"attributes={list(self.attributes.keys())[:3]}{'...' if len(self.attributes) > 3 else ''})"
        )
        
        return result

    def join(
        self,
        right: Union["QueryResult", Any],  # Any for QueryBuilder
        on: Union[str, List[str]],
        how: str = "inner",
        suffixes: Tuple[str, str] = ("", "_r"),
    ) -> Any:  # Returns JoinBuilder
        """Join this result with another result or query.

        This is the escape hatch for joining pre-executed results. For most
        cases, prefer using QueryBuilder.join() which is lazy and planner-aware.

        Args:
            right: Right result or query to join with
            on: Column name(s) to join on
            how: Join type ('inner', 'left', 'right', 'outer', 'semi', 'anti')
            suffixes: Tuple of suffixes for name collisions

        Returns:
            JoinBuilder for further chaining and execution

        Examples:
            >>> # Join two pre-computed results
            >>> nodes = Q.nodes().compute("degree").execute(network)
            >>> communities = Q.communities().members().execute(network)
            >>> joined = nodes.join(communities, on=["node", "layer"], how="left")
            >>> result = joined.execute(network)
        """
        from .builder import JoinBuilder

        # Normalize on to list
        if isinstance(on, str):
            on_list = [on]
        else:
            on_list = list(on)

        return JoinBuilder(
            left=self,
            right=right,
            on=tuple(on_list),
            how=how,
            suffixes=suffixes,
        )

    def _to_select_stmt(self):
        """Convert QueryResult to a SelectStmt for join operations.

        This is used internally when joining results. It creates a minimal
        SelectStmt that represents this result.
        """
        from .ast import SelectStmt, Target

        # Determine target from result
        if self.target == "nodes":
            target = Target.NODES
        elif self.target == "edges":
            target = Target.EDGES
        elif self.target == "communities":
            target = Target.COMMUNITIES
        else:
            target = Target.NODES

        # Create minimal SelectStmt (will be materialized from result data)
        return SelectStmt(target=target)
    
    def explain(self) -> str:
        """Generate human-readable explanation of the query execution.
        
        Shows:
        - Query summary
        - Resolved layers
        - Measures computed
        - Aggregations applied
        - Diagnostics (warnings + info)
        - Suggested next queries
        
        Returns:
            Formatted explanation string
        
        Example:
            >>> result = Q.nodes().compute("degree").execute(net)
            >>> print(result.explain())
        """
        from py3plex.errors import Colors
        
        lines = []
        use_color = Colors.supports_color()
        
        # Header
        if use_color:
            lines.append(f"{Colors.BOLD}{Colors.BLUE}Query Explanation{Colors.RESET}")
        else:
            lines.append("Query Explanation")
        lines.append("=" * 60)
        lines.append("")
        
        # Query summary
        lines.append(f"Target: {self.target}")
        lines.append(f"Results: {len(self.items)} items")
        lines.append("")
        
        # Layers
        if "layers" in self.meta:
            layers = self.meta["layers"]
            if layers:
                lines.append(f"Layers: {', '.join(sorted(layers))}")
            else:
                lines.append("Layers: all")
            lines.append("")
        
        # Computed metrics
        if self.computed_metrics:
            lines.append("Computed metrics:")
            for metric in sorted(self.computed_metrics):
                lines.append(f"  - {metric}")
            lines.append("")
        
        # Grouping
        if "grouping" in self.meta:
            grouping = self.meta["grouping"]
            if grouping:
                lines.append(f"Grouping: {grouping.get('type', 'unknown')}")
                if "keys" in grouping:
                    lines.append(f"  Keys: {', '.join(grouping['keys'])}")
                lines.append("")
        
        # Diagnostics
        if "diagnostics" in self.meta:
            diag_data = self.meta["diagnostics"]
            
            if diag_data:
                lines.append("Diagnostics:")
                lines.append("")
                
                # Handle different formats
                if isinstance(diag_data, list):
                    from py3plex.diagnostics.core import Diagnostic
                    
                    for diag_item in diag_data:
                        if isinstance(diag_item, dict):
                            # Convert dict to Diagnostic object
                            try:
                                diag = Diagnostic.from_dict(diag_item)
                                lines.append(diag.format(use_color=use_color))
                            except Exception:
                                # Fallback to simple dict display
                                lines.append(f"  {diag_item.get('severity', 'info')}: {diag_item.get('message', 'N/A')}")
                        else:
                            # Already a Diagnostic object
                            lines.append(diag_item.format(use_color=use_color))
                        lines.append("")
        
        # Suggested next queries
        lines.append("Suggested next steps:")
        if not self.computed_metrics:
            lines.append("  - Compute centrality: .compute('degree', 'betweenness_centrality')")
        if "grouping" not in self.meta:
            lines.append("  - Group by layer: .per_layer()")
        if not self.meta.get("has_uncertainty", False):
            lines.append("  - Add uncertainty: .uq(method='bootstrap', n_samples=100)")
        lines.append("  - Export to CSV: .to_pandas().to_csv('results.csv')")
        
        return "\n".join(lines)
    
    def debug(self) -> str:
        """Generate detailed debug information about query execution.
        
        Shows:
        - Full AST structure
        - Execution plan
        - Cache hits/misses
        - Backend calls
        - Timing per stage
        - Randomness sources
        
        Returns:
            Formatted debug information
        
        Example:
            >>> result = Q.nodes().compute("degree").execute(net)
            >>> print(result.debug())
        """
        from py3plex.errors import Colors
        import json
        
        lines = []
        use_color = Colors.supports_color()
        
        # Header
        if use_color:
            lines.append(f"{Colors.BOLD}{Colors.RED}Query Debug Information{Colors.RESET}")
        else:
            lines.append("Query Debug Information")
        lines.append("=" * 60)
        lines.append("")
        
        # Basic info
        lines.append(f"Target: {self.target}")
        lines.append(f"Result count: {len(self.items)}")
        lines.append("")
        
        # AST (if available)
        if "ast" in self.meta:
            lines.append("AST Structure:")
            ast_data = self.meta["ast"]
            if hasattr(ast_data, "to_dict"):
                lines.append(json.dumps(ast_data.to_dict(), indent=2))
            elif isinstance(ast_data, dict):
                lines.append(json.dumps(ast_data, indent=2))
            else:
                lines.append(str(ast_data))
            lines.append("")
        
        # Execution plan
        if "execution_plan" in self.meta:
            lines.append("Execution Plan:")
            plan = self.meta["execution_plan"]
            if isinstance(plan, dict):
                lines.append(json.dumps(plan, indent=2))
            else:
                lines.append(str(plan))
            lines.append("")
        
        # Timing information
        if "timing" in self.meta:
            lines.append("Timing:")
            timing = self.meta["timing"]
            for stage, duration in timing.items():
                lines.append(f"  {stage}: {duration:.3f}s")
            lines.append("")
        
        # Cache information
        if "cache_stats" in self.meta:
            lines.append("Cache Statistics:")
            cache = self.meta["cache_stats"]
            if isinstance(cache, dict):
                lines.append(f"  Hits: {cache.get('hits', 0)}")
                lines.append(f"  Misses: {cache.get('misses', 0)}")
                lines.append(f"  Hit rate: {cache.get('hit_rate', 0.0):.1%}")
            lines.append("")
        
        # Backend calls
        if "backend_calls" in self.meta:
            lines.append("Backend Calls:")
            calls = self.meta["backend_calls"]
            for call in calls:
                if isinstance(call, dict):
                    lines.append(f"  - {call.get('function', 'unknown')}")
                    if "duration" in call:
                        lines.append(f"    Duration: {call['duration']:.3f}s")
                else:
                    lines.append(f"  - {call}")
            lines.append("")
        
        # Randomness sources
        if "random_seeds" in self.meta:
            lines.append("Random Seeds:")
            seeds = self.meta["random_seeds"]
            if isinstance(seeds, dict):
                for source, seed in seeds.items():
                    lines.append(f"  {source}: {seed}")
            lines.append("")
        
        # All metadata (fallback)
        if not any(k in self.meta for k in ["ast", "execution_plan", "timing", "cache_stats", "backend_calls"]):
            lines.append("Available Metadata:")
            for key in sorted(self.meta.keys()):
                if not key.startswith("_"):  # Skip internal keys
                    lines.append(f"  - {key}")
            lines.append("")
            lines.append("(Use .meta[key] to access specific metadata)")
        
        return "\n".join(lines)
    
    def __or__(self, other: "QueryResult") -> "QueryResult":
        """Union operator: r1 | r2
        
        Combines two results, keeping items that appear in either result.
        This is post-compute algebra (operating on executed results with attributes).
        
        Args:
            other: Another QueryResult instance
            
        Returns:
            New QueryResult with union of items
            
        Raises:
            IncompatibleQueryError: If results have different targets
            AmbiguousIdentityError: If identity strategy is ambiguous
            AttributeConflictError: If attribute conflicts exist
            
        Example:
            >>> result1 = Q.nodes().from_layers(L["social"]).execute(net)
            >>> result2 = Q.nodes().from_layers(L["work"]).execute(net)
            >>> combined = result1 | result2
        """
        from .algebra import (
            check_result_compatibility,
            detect_identity_ambiguity,
            extract_item_identity,
            detect_attribute_conflicts,
            resolve_attribute_conflict,
            merge_uncertainty_info,
            IdentityStrategy,
            ConflictResolution,
            AlgebraConfig,
            AmbiguousIdentityError,
            AttributeConflictError,
        )
        
        check_result_compatibility(self, other)
        
        # Get or infer identity strategy
        config = AlgebraConfig()
        if 'identity_strategy' in self.meta:
            config.identity_strategy = self.meta['identity_strategy']
        elif 'identity_strategy' in other.meta:
            config.identity_strategy = other.meta['identity_strategy']
        elif detect_identity_ambiguity(self, other):
            raise AmbiguousIdentityError(
                "Identity strategy is ambiguous for multilayer results. "
                "Specify explicitly: result.resolve(identity='by_id') or result.resolve(identity='by_replica')"
            )
        
        # Get conflict resolution strategy
        if 'conflict_resolution' in self.meta:
            config.conflict_resolution = self.meta['conflict_resolution']
        elif 'conflict_resolution' in other.meta:
            config.conflict_resolution = other.meta['conflict_resolution']
        
        # Build identity map
        id_to_item1 = {extract_item_identity(item, config.identity_strategy): item for item in self.items}
        id_to_item2 = {extract_item_identity(item, config.identity_strategy): item for item in other.items}
        
        # Union of identities
        all_ids = set(id_to_item1.keys()) | set(id_to_item2.keys())
        shared_ids = set(id_to_item1.keys()) & set(id_to_item2.keys())
        
        # Merge items (prefer full item from first result for shared IDs)
        result_items = []
        for item_id in all_ids:
            if item_id in id_to_item1:
                result_items.append(id_to_item1[item_id])
            else:
                result_items.append(id_to_item2[item_id])
        
        # Merge attributes
        result_attributes = {}
        
        # Detect conflicts
        conflicts = detect_attribute_conflicts(self.attributes, other.attributes, shared_ids)
        
        # Merge each attribute
        for attr in set(self.attributes.keys()) | set(other.attributes.keys()):
            values1 = self.attributes.get(attr, {})
            values2 = other.attributes.get(attr, {})
            
            merged_values = {}
            for item_id in all_ids:
                item1 = id_to_item1.get(item_id)
                item2 = id_to_item2.get(item_id)
                
                val1 = values1.get(item1) if isinstance(values1, dict) and item1 else None
                val2 = values2.get(item2) if isinstance(values2, dict) and item2 else None
                
                if val1 is not None and val2 is not None:
                    # Both have value - resolve conflict
                    if attr in conflicts:
                        merged_val = resolve_attribute_conflict(attr, val1, val2, config.conflict_resolution)
                    else:
                        merged_val = val1  # No conflict, use first
                elif val1 is not None:
                    merged_val = val1
                elif val2 is not None:
                    merged_val = val2
                else:
                    continue
                
                # Use the actual item from result_items
                actual_item = id_to_item1.get(item_id) or id_to_item2.get(item_id)
                merged_values[actual_item] = merged_val
            
            result_attributes[attr] = merged_values
        
        # Merge metadata
        result_meta = {
            'algebra_operation': 'union',
            'operand_counts': [len(self.items), len(other.items)],
            'result_count': len(result_items),
            'identity_strategy': config.identity_strategy.value if hasattr(config.identity_strategy, 'value') else config.identity_strategy,
            'conflict_resolution': config.conflict_resolution.value if hasattr(config.conflict_resolution, 'value') else config.conflict_resolution,
        }
        
        # Merge uncertainty info
        uq1 = self.meta.get('uncertainty')
        uq2 = other.meta.get('uncertainty')
        merged_uq = merge_uncertainty_info(uq1, uq2)
        if merged_uq:
            result_meta['uncertainty'] = merged_uq
        
        return QueryResult(
            target=self.target,
            items=result_items,
            attributes=result_attributes,
            meta=result_meta,
            computed_metrics=self.computed_metrics | other.computed_metrics
        )
    
    def __and__(self, other: "QueryResult") -> "QueryResult":
        """Intersection operator: r1 & r2
        
        Combines two results, keeping only items that appear in both results.
        
        Args:
            other: Another QueryResult instance
            
        Returns:
            New QueryResult with intersection of items
            
        Example:
            >>> high_degree = Q.nodes().where(degree__gt=5).execute(net)
            >>> high_betweenness = Q.nodes().where(betweenness__gt=0.1).execute(net)
            >>> hubs = high_degree & high_betweenness
        """
        from .algebra import (
            check_result_compatibility,
            detect_identity_ambiguity,
            extract_item_identity,
            detect_attribute_conflicts,
            resolve_attribute_conflict,
            merge_uncertainty_info,
            IdentityStrategy,
            ConflictResolution,
            AlgebraConfig,
            AmbiguousIdentityError,
        )
        
        check_result_compatibility(self, other)
        
        # Get or infer identity strategy
        config = AlgebraConfig()
        if 'identity_strategy' in self.meta:
            config.identity_strategy = self.meta['identity_strategy']
        elif 'identity_strategy' in other.meta:
            config.identity_strategy = other.meta['identity_strategy']
        elif detect_identity_ambiguity(self, other):
            raise AmbiguousIdentityError(
                "Identity strategy is ambiguous for multilayer results. "
                "Specify explicitly: result.resolve(identity='by_id') or result.resolve(identity='by_replica')"
            )
        
        # Get conflict resolution strategy
        if 'conflict_resolution' in self.meta:
            config.conflict_resolution = self.meta['conflict_resolution']
        elif 'conflict_resolution' in other.meta:
            config.conflict_resolution = other.meta['conflict_resolution']
        
        # Build identity map
        id_to_item1 = {extract_item_identity(item, config.identity_strategy): item for item in self.items}
        id_to_item2 = {extract_item_identity(item, config.identity_strategy): item for item in other.items}
        
        # Intersection of identities
        shared_ids = set(id_to_item1.keys()) & set(id_to_item2.keys())
        
        # Keep items from first result
        result_items = [id_to_item1[item_id] for item_id in shared_ids]
        
        # Merge attributes (only for shared items)
        result_attributes = {}
        conflicts = detect_attribute_conflicts(self.attributes, other.attributes, shared_ids)
        
        for attr in set(self.attributes.keys()) | set(other.attributes.keys()):
            values1 = self.attributes.get(attr, {})
            values2 = other.attributes.get(attr, {})
            
            merged_values = {}
            for item_id in shared_ids:
                item = id_to_item1[item_id]
                
                val1 = values1.get(item) if isinstance(values1, dict) else None
                val2 = values2.get(id_to_item2[item_id]) if isinstance(values2, dict) else None
                
                if val1 is not None and val2 is not None:
                    if attr in conflicts:
                        merged_val = resolve_attribute_conflict(attr, val1, val2, config.conflict_resolution)
                    else:
                        merged_val = val1
                elif val1 is not None:
                    merged_val = val1
                elif val2 is not None:
                    merged_val = val2
                else:
                    continue
                
                merged_values[item] = merged_val
            
            result_attributes[attr] = merged_values
        
        # Merge metadata
        result_meta = {
            'algebra_operation': 'intersection',
            'operand_counts': [len(self.items), len(other.items)],
            'result_count': len(result_items),
            'identity_strategy': config.identity_strategy.value if hasattr(config.identity_strategy, 'value') else config.identity_strategy,
        }
        
        # Merge uncertainty info
        merged_uq = merge_uncertainty_info(
            self.meta.get('uncertainty'),
            other.meta.get('uncertainty')
        )
        if merged_uq:
            result_meta['uncertainty'] = merged_uq
        
        return QueryResult(
            target=self.target,
            items=result_items,
            attributes=result_attributes,
            meta=result_meta,
            computed_metrics=self.computed_metrics | other.computed_metrics
        )
    
    def __sub__(self, other: "QueryResult") -> "QueryResult":
        """Difference operator: r1 - r2
        
        Keeps items from first result that are not in second result.
        
        Args:
            other: Another QueryResult instance
            
        Returns:
            New QueryResult with difference
            
        Example:
            >>> all_nodes = Q.nodes().execute(net)
            >>> outliers = Q.nodes().where(degree__gt=10).execute(net)
            >>> normal = all_nodes - outliers
        """
        from .algebra import (
            check_result_compatibility,
            detect_identity_ambiguity,
            extract_item_identity,
            IdentityStrategy,
            AlgebraConfig,
            AmbiguousIdentityError,
        )
        
        check_result_compatibility(self, other)
        
        # Get identity strategy
        config = AlgebraConfig()
        if 'identity_strategy' in self.meta:
            config.identity_strategy = self.meta['identity_strategy']
        elif 'identity_strategy' in other.meta:
            config.identity_strategy = other.meta['identity_strategy']
        elif detect_identity_ambiguity(self, other):
            raise AmbiguousIdentityError(
                "Identity strategy is ambiguous for multilayer results. "
                "Specify explicitly: result.resolve(identity='by_id') or result.resolve(identity='by_replica')"
            )
        
        # Build identity sets
        ids1 = {extract_item_identity(item, config.identity_strategy) for item in self.items}
        ids2 = {extract_item_identity(item, config.identity_strategy) for item in other.items}
        
        # Difference
        diff_ids = ids1 - ids2
        
        # Keep items from first result that are in difference
        id_to_item1 = {extract_item_identity(item, config.identity_strategy): item for item in self.items}
        result_items = [id_to_item1[item_id] for item_id in diff_ids]
        
        # Keep only attributes for result items
        result_attributes = {}
        for attr, values in self.attributes.items():
            if isinstance(values, dict):
                result_attributes[attr] = {
                    item: values[item] 
                    for item in result_items 
                    if item in values
                }
            else:
                result_attributes[attr] = values
        
        result_meta = {
            'algebra_operation': 'difference',
            'operand_counts': [len(self.items), len(other.items)],
            'result_count': len(result_items),
            'identity_strategy': config.identity_strategy.value if hasattr(config.identity_strategy, 'value') else config.identity_strategy,
        }
        
        return QueryResult(
            target=self.target,
            items=result_items,
            attributes=result_attributes,
            meta=result_meta,
            computed_metrics=self.computed_metrics.copy()
        )
    
    def __xor__(self, other: "QueryResult") -> "QueryResult":
        """Symmetric difference operator: r1 ^ r2
        
        Keeps items that appear in exactly one result (not both).
        
        Args:
            other: Another QueryResult instance
            
        Returns:
            New QueryResult with symmetric difference
            
        Example:
            >>> social = Q.nodes().from_layers(L["social"]).execute(net)
            >>> work = Q.nodes().from_layers(L["work"]).execute(net)
            >>> exclusive = social ^ work  # In one layer, not both
        """
        from .algebra import (
            check_result_compatibility,
            detect_identity_ambiguity,
            extract_item_identity,
            IdentityStrategy,
            AlgebraConfig,
            AmbiguousIdentityError,
        )
        
        check_result_compatibility(self, other)
        
        # Get identity strategy
        config = AlgebraConfig()
        if 'identity_strategy' in self.meta:
            config.identity_strategy = self.meta['identity_strategy']
        elif 'identity_strategy' in other.meta:
            config.identity_strategy = other.meta['identity_strategy']
        elif detect_identity_ambiguity(self, other):
            raise AmbiguousIdentityError(
                "Identity strategy is ambiguous for multilayer results. "
                "Specify explicitly"
            )
        
        # Build identity maps
        id_to_item1 = {extract_item_identity(item, config.identity_strategy): item for item in self.items}
        id_to_item2 = {extract_item_identity(item, config.identity_strategy): item for item in other.items}
        
        # Symmetric difference
        ids1 = set(id_to_item1.keys())
        ids2 = set(id_to_item2.keys())
        sym_diff_ids = ids1 ^ ids2
        
        # Build result items
        result_items = []
        result_attributes = {}
        
        for item_id in sym_diff_ids:
            if item_id in id_to_item1:
                result_items.append(id_to_item1[item_id])
            else:
                result_items.append(id_to_item2[item_id])
        
        # Merge attributes from both sources
        for attr in set(self.attributes.keys()) | set(other.attributes.keys()):
            values1 = self.attributes.get(attr, {})
            values2 = other.attributes.get(attr, {})
            
            merged_values = {}
            for item in result_items:
                item_id = extract_item_identity(item, config.identity_strategy)
                
                if item_id in id_to_item1:
                    val = values1.get(item) if isinstance(values1, dict) else None
                else:
                    val = values2.get(item) if isinstance(values2, dict) else None
                
                if val is not None:
                    merged_values[item] = val
            
            result_attributes[attr] = merged_values
        
        result_meta = {
            'algebra_operation': 'symmetric_difference',
            'operand_counts': [len(self.items), len(other.items)],
            'result_count': len(result_items),
            'identity_strategy': config.identity_strategy.value if hasattr(config.identity_strategy, 'value') else config.identity_strategy,
        }
        
        return QueryResult(
            target=self.target,
            items=result_items,
            attributes=result_attributes,
            meta=result_meta,
            computed_metrics=self.computed_metrics | other.computed_metrics
        )
