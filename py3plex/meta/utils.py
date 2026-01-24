"""Utility functions for meta-analysis.

This module provides helper functions for:
- Effect extraction from query results
- Standard error resolution
- Network fingerprinting
- Provenance aggregation
"""

import hashlib
import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Union
from py3plex.exceptions import MetaAnalysisError


def compute_network_fingerprint(network: Any) -> Dict[str, Any]:
    """Compute network fingerprint for provenance.

    Args:
        network: Network object

    Returns:
        Dictionary with node_count, edge_count, layer_count, layers
    """
    try:
        nodes = network.get_nodes()
        edges = network.get_edges()
        layers = network.get_layers()

        return {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "layer_count": len(layers),
            "layers": sorted(layers)[:10],  # First 10 layers for brevity
        }
    except Exception as e:
        raise MetaAnalysisError(
            f"Failed to compute network fingerprint: {e}",
            hint="Ensure network object has get_nodes(), get_edges(), and get_layers() methods",
        )


def extract_effect_from_result(
    result: Any,
    effect: str,
    group_by: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Extract effect values from QueryResult.

    Args:
        result: QueryResult object
        effect: Name of effect column
        group_by: Optional list of grouping columns

    Returns:
        DataFrame with effect values and grouping columns

    Raises:
        MetaAnalysisError: If effect column not found or cardinality issues
    """
    # Convert result to pandas
    try:
        df = result.to_pandas()
    except Exception as e:
        raise MetaAnalysisError(
            f"Failed to convert QueryResult to pandas: {e}",
            hint="Ensure QueryResult has valid data",
        )

    # Check if effect column exists
    if effect not in df.columns:
        available = ", ".join(df.columns[:10])
        raise MetaAnalysisError(
            f"Effect column '{effect}' not found in query result",
            hint=f"Available columns: {available}",
        )

    # Check cardinality
    if group_by is None:
        # No grouping: expect exactly 1 row
        if len(df) != 1:
            raise MetaAnalysisError(
                f"Query returned {len(df)} rows but group_by not provided",
                hint="Either provide group_by parameter or ensure query returns exactly 1 row",
            )
        # Return single-row dataframe
        return df[[effect]]
    else:
        # With grouping: verify all group columns exist
        missing = [col for col in group_by if col not in df.columns]
        if missing:
            available = ", ".join(df.columns[:10])
            raise MetaAnalysisError(
                f"Group columns not found: {missing}",
                hint=f"Available columns: {available}",
            )

        # Return dataframe with group columns and effect
        return df[group_by + [effect]]


def resolve_standard_error(
    result: Any,
    effect: str,
    se: Optional[str] = None,
    allow_unweighted: bool = False,
) -> Optional[Union[pd.Series, float]]:
    """Resolve standard error from QueryResult.

    Priority order:
    1. Explicit se="column_name" if column exists
    2. Expression se="se(effect_col)" if variance available
    3. Auto-infer from UQ if query used .uq(...)
    4. Error unless allow_unweighted=True

    Args:
        result: QueryResult object
        effect: Name of effect column
        se: Standard error specification (column name or expression)
        allow_unweighted: Allow unweighted pooling if SE not available

    Returns:
        Series or scalar of standard errors, or None if allow_unweighted and no SE

    Raises:
        MetaAnalysisError: If SE cannot be resolved and not allow_unweighted
    """
    df = result.to_pandas()

    # Priority 1: Explicit column name
    if se is not None and se in df.columns:
        return df[se]

    # Priority 2: Expression se="se(effect_col)" or "std(effect_col)"
    if se is not None and (se.startswith("se(") or se.startswith("std(")):
        # Extract column name from expression
        import re

        match = re.match(r"(se|std)\(([^)]+)\)", se)
        if match:
            col_name = match.group(2)
            std_col = f"{col_name}_std"
            if std_col in df.columns:
                return df[std_col]

    # Priority 3: Auto-infer from UQ
    if hasattr(result, "meta") and result.meta:
        provenance = result.meta.get("provenance", {})
        randomness = provenance.get("randomness", {})

        if randomness.get("n_samples") is not None:
            # Query used UQ, try to find std column
            std_col = f"{effect}_std"
            if std_col in df.columns:
                return df[std_col]

    # Priority 4: Error or allow unweighted
    if allow_unweighted:
        return None
    else:
        raise MetaAnalysisError(
            f"Cannot resolve standard error for effect '{effect}'",
            hint="Provide se parameter, use .uq() in query, or set allow_unweighted=True",
        )


def validate_group_consistency(
    dfs: List[pd.DataFrame], group_by: List[str]
) -> None:
    """Validate that all dataframes have consistent groups.

    Args:
        dfs: List of dataframes with group columns
        group_by: List of grouping column names

    Raises:
        MetaAnalysisError: If groups are inconsistent across networks
    """
    if not dfs:
        return

    # Get unique groups from first dataframe
    first_groups = set(tuple(row) for row in dfs[0][group_by].values)

    # Check all other dataframes
    for i, df in enumerate(dfs[1:], start=1):
        groups = set(tuple(row) for row in df[group_by].values)
        if groups != first_groups:
            raise MetaAnalysisError(
                f"Group mismatch: Network {i} has different groups than network 0",
                hint="Ensure all networks have the same groups when using group_by",
            )


def prepare_effect_table(
    results: Dict[str, Any],
    effect: str,
    se: Optional[str] = None,
    group_by: Optional[List[str]] = None,
    allow_unweighted: bool = False,
) -> pd.DataFrame:
    """Prepare combined effect table from multiple network results.

    Args:
        results: Dictionary mapping network_name -> QueryResult
        effect: Effect column name
        se: Standard error specification
        group_by: Optional grouping columns
        allow_unweighted: Allow unweighted pooling

    Returns:
        DataFrame with columns: network_name, [group columns], effect, se

    Raises:
        MetaAnalysisError: If effect extraction or SE resolution fails
    """
    rows = []

    for net_name, result in results.items():
        # Extract effect
        effect_df = extract_effect_from_result(result, effect, group_by)

        # Resolve SE
        se_values = resolve_standard_error(result, effect, se, allow_unweighted)

        # Combine
        for idx, row in effect_df.iterrows():
            row_dict = {"network_name": net_name}

            if group_by:
                for col in group_by:
                    row_dict[col] = row[col]

            row_dict["effect"] = row[effect]

            if se_values is not None:
                if isinstance(se_values, (pd.Series, pd.DataFrame)):
                    row_dict["se"] = se_values.iloc[idx] if hasattr(se_values, "iloc") else se_values[idx]
                else:
                    row_dict["se"] = se_values
            else:
                row_dict["se"] = None

            rows.append(row_dict)

    df = pd.DataFrame(rows)

    # Validate group consistency if group_by provided
    if group_by:
        network_groups = {}
        for net_name in results.keys():
            net_df = df[df["network_name"] == net_name]
            groups = set(tuple(row) for row in net_df[group_by].values)
            network_groups[net_name] = groups

        # Check consistency
        first_groups = list(network_groups.values())[0]
        for net_name, groups in network_groups.items():
            if groups != first_groups:
                raise MetaAnalysisError(
                    f"Group mismatch: Network '{net_name}' has different groups",
                    hint="Ensure all networks have the same groups when using group_by",
                )

    return df


def aggregate_provenance(
    network_names: List[str],
    results: Dict[str, Any],
    networks_fingerprints: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """Aggregate provenance from multiple network query results.

    Args:
        network_names: Ordered list of network names
        results: Dictionary mapping network_name -> QueryResult
        networks_fingerprints: Dictionary mapping network_name -> fingerprint

    Returns:
        Aggregated provenance dictionary
    """
    import datetime

    networks_provenance = []

    for net_name in network_names:
        result = results[net_name]
        fingerprint = networks_fingerprints[net_name]

        prov = {}
        prov["name"] = net_name
        prov["network_fingerprint"] = fingerprint

        # Extract provenance from result if available
        if hasattr(result, "meta") and result.meta:
            result_prov = result.meta.get("provenance", {})
            query = result_prov.get("query", {})
            prov["query_ast_hash"] = query.get("ast_hash", None)

            randomness = result_prov.get("randomness", {})
            prov["randomness"] = {
                "seed": randomness.get("seed"),
                "method": randomness.get("method"),
                "n_samples": randomness.get("n_samples"),
            }

            performance = result_prov.get("performance", {})
            prov["performance"] = {
                "total_ms": performance.get("total_ms"),
            }

            prov["warnings"] = result_prov.get("warnings", [])
        else:
            prov["query_ast_hash"] = None
            prov["randomness"] = {}
            prov["performance"] = {}
            prov["warnings"] = []

        networks_provenance.append(prov)

    # Get py3plex version
    try:
        import py3plex

        version = py3plex.__version__
    except:
        version = "unknown"

    return {
        "engine": "dsl_v2_meta",
        "timestamp_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "py3plex_version": version,
        "networks": networks_provenance,
    }
