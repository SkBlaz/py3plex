"""Meta-analysis builder for DSL v2.

This module provides the MetaBuilder class for conducting meta-analyses
across multiple networks using DSL v2 queries.

Example:
    >>> from py3plex.dsl import Q, M
    >>>
    >>> meta = (
    ...     M.meta("avg_degree_meta")
    ...      .on_networks({"n1": net1, "n2": net2, "n3": net3})
    ...      .run(
    ...         Q.nodes().compute("degree").summarize(avg_degree="mean(degree)"),
    ...         effect="avg_degree",
    ...      )
    ...      .model("random")
    ...      .execute()
    ... )
    >>> df = meta.to_pandas()
"""

import warnings
import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Union, Callable
from py3plex.exceptions import MetaAnalysisError

from .result import MetaResult
from .stats import meta_analysis, weighted_least_squares, PooledEffect
from .utils import (
    compute_network_fingerprint,
    prepare_effect_table,
    aggregate_provenance,
)


class MetaBuilder:
    """Builder for meta-analysis queries.

    Execution contract (NON-NEGOTIABLE):
    - .on_networks(...) MUST be called exactly once
    - .run(...) MUST be called exactly once
    - .execute() without both MUST raise MetaAnalysisError
    - Re-calling .on_networks() or .run() overwrites previous values but emits warning

    Default model is random-effects unless .model("fixed") is specified.
    """

    def __init__(self, name: Optional[str] = None):
        """Initialize MetaBuilder.

        Args:
            name: Optional name for this meta-analysis
        """
        self.name = name
        self._networks: Optional[Dict[str, Any]] = None
        self._network_meta: Optional[Dict[str, Dict[str, Any]]] = None
        self._query: Optional[Any] = None
        self._effect: Optional[str] = None
        self._se: Optional[str] = None
        self._group_by: Optional[List[str]] = None
        self._model_type: str = "random"  # Default
        self._subgroup_by: Optional[str] = None
        self._meta_regress_formula: Optional[str] = None
        self._allow_unweighted: bool = False
        self._preserve_order: bool = False
        self._seed: Optional[int] = None
        self._ci_level: float = 0.95

        # Track if methods were called
        self._on_networks_called = False
        self._run_called = False

    def on_networks(
        self,
        networks: Union[Dict[str, Any], List[Any]],
    ) -> "MetaBuilder":
        """Specify networks for meta-analysis.

        Args:
            networks: Dictionary mapping name -> network, or list of networks

        Returns:
            Self for chaining

        Raises:
            MetaAnalysisError: If networks is empty
        """
        if self._on_networks_called:
            warnings.warn(
                "MetaBuilder.on_networks() called multiple times. Previous networks overwritten.",
                UserWarning,
                stacklevel=2,
            )

        if isinstance(networks, dict):
            if not networks:
                raise MetaAnalysisError(
                    "Empty networks dictionary provided",
                    hint="Provide at least one network",
                )
            # Sort by key unless preserve_order is True
            if not self._preserve_order:
                self._networks = dict(sorted(networks.items()))
            else:
                self._networks = dict(networks)
        elif isinstance(networks, list):
            if not networks:
                raise MetaAnalysisError(
                    "Empty networks list provided",
                    hint="Provide at least one network",
                )
            # Auto-name as net_0, net_1, ...
            self._networks = {f"net_{i}": net for i, net in enumerate(networks)}
        else:
            raise MetaAnalysisError(
                f"Invalid networks type: {type(networks)}",
                hint="Provide dict or list of networks",
            )

        self._on_networks_called = True
        return self

    def with_network_meta(
        self, meta: Dict[str, Dict[str, Any]]
    ) -> "MetaBuilder":
        """Provide network-level metadata for subgroup analysis or meta-regression.

        Args:
            meta: Dictionary mapping network_name -> metadata dict

        Returns:
            Self for chaining
        """
        self._network_meta = meta
        return self

    def run(
        self,
        query: Any,
        effect: str,
        se: Optional[str] = None,
        group_by: Optional[List[str]] = None,
    ) -> "MetaBuilder":
        """Specify query and effect to pool.

        Args:
            query: DSL v2 QueryBuilder or legacy DSL string
            effect: Name of effect column to pool
            se: Standard error specification (column name or expression)
            group_by: Optional list of grouping columns for node-level pooling

        Returns:
            Self for chaining
        """
        if self._run_called:
            warnings.warn(
                "MetaBuilder.run() called multiple times. Previous query overwritten.",
                UserWarning,
                stacklevel=2,
            )

        self._query = query
        self._effect = effect
        self._se = se
        self._group_by = group_by
        self._run_called = True
        return self

    def model(self, model_type: str) -> "MetaBuilder":
        """Specify meta-analysis model.

        Args:
            model_type: "fixed" or "random"

        Returns:
            Self for chaining

        Raises:
            MetaAnalysisError: If model_type is invalid
        """
        if model_type not in ["fixed", "random"]:
            raise MetaAnalysisError(
                f"Invalid model type: {model_type}",
                hint="Use 'fixed' or 'random'",
            )
        self._model_type = model_type
        return self

    def subgroup(self, by: str) -> "MetaBuilder":
        """Enable subgroup meta-analysis.

        Args:
            by: Field in network metadata to partition by

        Returns:
            Self for chaining
        """
        self._subgroup_by = by
        return self

    def meta_regress(self, formula: str) -> "MetaBuilder":
        """Enable meta-regression (v1 constrained scope).

        Args:
            formula: Regression formula (e.g., "y ~ x1 + x2")

        Returns:
            Self for chaining

        Raises:
            NotImplementedError: If formula contains unsupported features
        """
        # Check for unsupported features
        if ":" in formula or "*" in formula:
            raise NotImplementedError(
                "Interaction terms not supported in meta-regression v1"
            )

        self._meta_regress_formula = formula
        return self

    def allow_unweighted(self, allow: bool = True) -> "MetaBuilder":
        """Allow unweighted pooling if SE not available.

        Args:
            allow: Whether to allow unweighted pooling

        Returns:
            Self for chaining
        """
        self._allow_unweighted = allow
        return self

    def preserve_order(self, preserve: bool = True) -> "MetaBuilder":
        """Preserve input order for networks dict (don't sort by key).

        Args:
            preserve: Whether to preserve order

        Returns:
            Self for chaining
        """
        self._preserve_order = preserve
        return self

    def seed(self, seed: int) -> "MetaBuilder":
        """Set seed for any stochastic operations (optional).

        Only fills missing seeds in queries. Never overrides explicit seeds.

        Args:
            seed: Random seed

        Returns:
            Self for chaining
        """
        self._seed = seed
        return self

    def execute(self) -> MetaResult:
        """Execute meta-analysis.

        Returns:
            MetaResult with pooled effects and provenance

        Raises:
            MetaAnalysisError: If execution contract violated
        """
        # Validate execution contract
        if not self._on_networks_called:
            raise MetaAnalysisError(
                "MetaBuilder.on_networks() must be called before execute()",
                hint="Call .on_networks({...}) to specify networks",
            )

        if not self._run_called:
            raise MetaAnalysisError(
                "MetaBuilder.run() must be called before execute()",
                hint="Call .run(query, effect=...) to specify analysis",
            )

        # Execute query on each network
        results = {}
        fingerprints = {}

        for net_name, network in self._networks.items():
            # Compute fingerprint
            fingerprints[net_name] = compute_network_fingerprint(network)

            # Execute query
            try:
                if hasattr(self._query, "execute"):
                    # DSL v2 builder
                    result = self._query.execute(network)
                else:
                    # Legacy DSL string
                    from py3plex.dsl_legacy import execute_query

                    result = execute_query(network, self._query)
            except Exception as e:
                raise MetaAnalysisError(
                    f"Query execution failed on network '{net_name}': {e}",
                    hint="Check query syntax and network compatibility",
                )

            results[net_name] = result

        # Prepare effect table
        effect_table = prepare_effect_table(
            results,
            self._effect,
            self._se,
            self._group_by,
            self._allow_unweighted,
        )

        # Check if unweighted
        has_se = effect_table["se"].notna().any()
        if not has_se:
            if not self._allow_unweighted:
                raise MetaAnalysisError(
                    "Standard errors not available and allow_unweighted=False",
                    hint="Set allow_unweighted=True or provide SE via .uq() or se parameter",
                )
            # Use unweighted pooling (sample SD)
            warnings.warn(
                "Using unweighted pooling: SE = sample SD / sqrt(k)",
                UserWarning,
            )

        # Aggregate provenance
        meta_provenance = aggregate_provenance(
            list(self._networks.keys()), results, fingerprints
        )
        meta_provenance["meta_model"] = {
            "type": self._model_type,
            "tau2_estimator": "DL",
            "k": len(self._networks),
        }

        # Perform meta-analysis
        if self._subgroup_by:
            return self._execute_subgroup(effect_table, meta_provenance)
        elif self._meta_regress_formula:
            return self._execute_meta_regression(effect_table, meta_provenance)
        else:
            return self._execute_simple(effect_table, meta_provenance)

    def _execute_simple(
        self, effect_table: pd.DataFrame, meta_provenance: Dict[str, Any]
    ) -> MetaResult:
        """Execute simple meta-analysis (no subgroups, no regression)."""
        pooled_rows = []
        network_rows = []

        # Determine grouping
        if self._group_by:
            groups = effect_table[self._group_by].drop_duplicates().values
        else:
            groups = [None]

        for group in groups:
            if group is not None:
                # Filter to group
                mask = (effect_table[self._group_by] == group).all(axis=1)
                group_df = effect_table[mask]
            else:
                group_df = effect_table

            # Extract effects and SEs
            effects = group_df["effect"].values
            ses = group_df["se"].values if group_df["se"].notna().any() else None

            # Handle unweighted case
            if ses is None:
                # Unweighted: arithmetic mean and sample SD
                pooled_effect = float(np.mean(effects))
                se_pooled = float(np.std(effects, ddof=1) / np.sqrt(len(effects)))
                z = 1.96
                ci_low = pooled_effect - z * se_pooled
                ci_high = pooled_effect + z * se_pooled

                pooled_row = {
                    "model": self._model_type,
                    "pooled_effect": pooled_effect,
                    "pooled_se": se_pooled,
                    "ci_low": ci_low,
                    "ci_high": ci_high,
                    "k": len(effects),
                    "tau2": np.nan,
                    "Q": np.nan,
                    "I2": np.nan,
                    "H": np.nan,
                }

                # Add unweighted flag to provenance
                meta_provenance["meta_model"]["unweighted"] = True
            else:
                # Weighted pooling
                pooled = meta_analysis(
                    effects, ses, model=self._model_type, ci_level=self._ci_level
                )

                pooled_row = {
                    "model": pooled.model,
                    "pooled_effect": pooled.pooled_effect,
                    "pooled_se": pooled.pooled_se,
                    "ci_low": pooled.ci_low,
                    "ci_high": pooled.ci_high,
                    "k": pooled.k,
                    "tau2": pooled.tau2,
                    "Q": pooled.Q,
                    "I2": pooled.I2,
                    "H": pooled.H,
                }

                # Add warnings to provenance
                if pooled.warnings:
                    if "warnings" not in meta_provenance:
                        meta_provenance["warnings"] = []
                    meta_provenance["warnings"].extend(pooled.warnings)

            # Add group columns
            if group is not None:
                for i, col in enumerate(self._group_by):
                    pooled_row[col] = group[i] if isinstance(group, (list, tuple)) else group

            pooled_rows.append(pooled_row)

            # Prepare network table
            for _, net_row in group_df.iterrows():
                net_dict = {
                    "network_name": net_row["network_name"],
                    "effect": net_row["effect"],
                    "se": net_row["se"],
                }

                # Add weights
                if ses is not None:
                    weight_fixed = 1.0 / (net_row["se"] ** 2)
                    net_dict["weight_fixed"] = weight_fixed

                    if self._model_type == "random" and not np.isnan(pooled_row["tau2"]):
                        weight_random = 1.0 / (net_row["se"] ** 2 + pooled_row["tau2"])
                        net_dict["weight_random"] = weight_random

                # Add group columns
                if group is not None:
                    for i, col in enumerate(self._group_by):
                        net_dict[col] = group[i] if isinstance(group, (list, tuple)) else group

                # Add network metadata if available
                if self._network_meta and net_row["network_name"] in self._network_meta:
                    net_meta = self._network_meta[net_row["network_name"]]
                    for key, val in net_meta.items():
                        net_dict[f"meta_{key}"] = val

                network_rows.append(net_dict)

        pooled_df = pd.DataFrame(pooled_rows)
        network_df = pd.DataFrame(network_rows)

        return MetaResult(
            pooled_effects=pooled_df,
            network_effects=network_df,
            meta_provenance=meta_provenance,
            model=self._model_type,
            subgroup_column=None,
        )

    def _execute_subgroup(
        self, effect_table: pd.DataFrame, meta_provenance: Dict[str, Any]
    ) -> MetaResult:
        """Execute subgroup meta-analysis."""
        if not self._network_meta:
            raise MetaAnalysisError(
                "Subgroup analysis requires network metadata",
                hint="Call .with_network_meta({...}) before .subgroup(...)",
            )

        # Add subgroup column to effect_table
        effect_table["subgroup"] = effect_table["network_name"].map(
            lambda name: self._network_meta.get(name, {}).get(self._subgroup_by, "NA")
        )

        pooled_rows = []
        network_rows = []

        # Get unique subgroups
        subgroups = effect_table["subgroup"].unique()

        # Pool each subgroup
        for subgroup in subgroups:
            subgroup_df = effect_table[effect_table["subgroup"] == subgroup]

            # Determine grouping within subgroup
            if self._group_by:
                groups = subgroup_df[self._group_by].drop_duplicates().values
            else:
                groups = [None]

            for group in groups:
                if group is not None:
                    mask = (subgroup_df[self._group_by] == group).all(axis=1)
                    group_df = subgroup_df[mask]
                else:
                    group_df = subgroup_df

                # Extract effects and SEs
                effects = group_df["effect"].values
                ses = group_df["se"].values if group_df["se"].notna().any() else None

                if ses is None:
                    # Unweighted
                    pooled_effect = float(np.mean(effects))
                    se_pooled = float(np.std(effects, ddof=1) / np.sqrt(len(effects)))
                    z = 1.96
                    ci_low = pooled_effect - z * se_pooled
                    ci_high = pooled_effect + z * se_pooled

                    pooled_row = {
                        "subgroup": subgroup,
                        "model": self._model_type,
                        "pooled_effect": pooled_effect,
                        "pooled_se": se_pooled,
                        "ci_low": ci_low,
                        "ci_high": ci_high,
                        "k": len(effects),
                        "tau2": np.nan,
                        "Q": np.nan,
                        "I2": np.nan,
                        "H": np.nan,
                    }
                else:
                    # Weighted
                    pooled = meta_analysis(
                        effects, ses, model=self._model_type, ci_level=self._ci_level
                    )

                    pooled_row = {
                        "subgroup": subgroup,
                        "model": pooled.model,
                        "pooled_effect": pooled.pooled_effect,
                        "pooled_se": pooled.pooled_se,
                        "ci_low": pooled.ci_low,
                        "ci_high": pooled.ci_high,
                        "k": pooled.k,
                        "tau2": pooled.tau2,
                        "Q": pooled.Q,
                        "I2": pooled.I2,
                        "H": pooled.H,
                    }

                if group is not None:
                    for i, col in enumerate(self._group_by):
                        pooled_row[col] = group[i] if isinstance(group, (list, tuple)) else group

                pooled_rows.append(pooled_row)

                # Network table rows
                for _, net_row in group_df.iterrows():
                    net_dict = {
                        "network_name": net_row["network_name"],
                        "subgroup": subgroup,
                        "effect": net_row["effect"],
                        "se": net_row["se"],
                    }

                    if ses is not None:
                        weight_fixed = 1.0 / (net_row["se"] ** 2)
                        net_dict["weight_fixed"] = weight_fixed

                        if self._model_type == "random" and not np.isnan(pooled_row["tau2"]):
                            weight_random = 1.0 / (net_row["se"] ** 2 + pooled_row["tau2"])
                            net_dict["weight_random"] = weight_random

                    if group is not None:
                        for i, col in enumerate(self._group_by):
                            net_dict[col] = group[i] if isinstance(group, (list, tuple)) else group

                    network_rows.append(net_dict)

        # Also compute overall pooling
        overall_df = effect_table.copy()
        effects = overall_df["effect"].values
        ses = overall_df["se"].values if overall_df["se"].notna().any() else None

        if ses is None:
            pooled_effect = float(np.mean(effects))
            se_pooled = float(np.std(effects, ddof=1) / np.sqrt(len(effects)))
            z = 1.96
            ci_low = pooled_effect - z * se_pooled
            ci_high = pooled_effect + z * se_pooled

            overall_row = {
                "subgroup": "Overall",
                "model": self._model_type,
                "pooled_effect": pooled_effect,
                "pooled_se": se_pooled,
                "ci_low": ci_low,
                "ci_high": ci_high,
                "k": len(effects),
                "tau2": np.nan,
                "Q": np.nan,
                "I2": np.nan,
                "H": np.nan,
            }
        else:
            pooled = meta_analysis(effects, ses, model=self._model_type, ci_level=self._ci_level)
            overall_row = {
                "subgroup": "Overall",
                "model": pooled.model,
                "pooled_effect": pooled.pooled_effect,
                "pooled_se": pooled.pooled_se,
                "ci_low": pooled.ci_low,
                "ci_high": pooled.ci_high,
                "k": pooled.k,
                "tau2": pooled.tau2,
                "Q": pooled.Q,
                "I2": pooled.I2,
                "H": pooled.H,
            }

        pooled_rows.append(overall_row)

        pooled_df = pd.DataFrame(pooled_rows)
        network_df = pd.DataFrame(network_rows)

        return MetaResult(
            pooled_effects=pooled_df,
            network_effects=network_df,
            meta_provenance=meta_provenance,
            model=self._model_type,
            subgroup_column=self._subgroup_by,
        )

    def _execute_meta_regression(
        self, effect_table: pd.DataFrame, meta_provenance: Dict[str, Any]
    ) -> MetaResult:
        """Execute meta-regression (v1 constrained scope)."""
        if self._group_by:
            raise NotImplementedError(
                "Meta-regression with group_by not supported in v1"
            )

        if not self._network_meta:
            raise MetaAnalysisError(
                "Meta-regression requires network metadata",
                hint="Call .with_network_meta({...}) before .meta_regress(...)",
            )

        # Parse formula: y ~ x1 + x2
        import re

        match = re.match(r"(\w+)\s*~\s*(.+)", self._meta_regress_formula)
        if not match:
            raise MetaAnalysisError(
                f"Invalid regression formula: {self._meta_regress_formula}",
                hint="Use format 'y ~ x1 + x2'",
            )

        outcome = match.group(1).strip()
        predictors_str = match.group(2).strip()
        predictors = [p.strip() for p in predictors_str.split("+")]

        # Build design matrix
        y = effect_table["effect"].values
        n = len(y)

        # Intercept
        X = np.ones((n, 1))

        # Add predictors
        for pred in predictors:
            # Get predictor from network metadata
            values = []
            for net_name in effect_table["network_name"]:
                if net_name not in self._network_meta:
                    raise MetaAnalysisError(
                        f"Network '{net_name}' missing from metadata",
                        hint="Ensure all networks have metadata for regression",
                    )
                meta = self._network_meta[net_name]
                if pred not in meta:
                    raise MetaAnalysisError(
                        f"Predictor '{pred}' not found in metadata for network '{net_name}'",
                        hint=f"Available fields: {', '.join(meta.keys())}",
                    )
                val = meta[pred]
                if not isinstance(val, (int, float)):
                    raise MetaAnalysisError(
                        f"Predictor '{pred}' must be numeric, got {type(val)}",
                        hint="Categorical predictors not supported in v1",
                    )
                values.append(val)

            X = np.column_stack([X, np.array(values)])

        # Get weights
        ses = effect_table["se"].values if effect_table["se"].notna().any() else None

        if ses is None:
            # Unweighted regression
            weights = np.ones(n)
        else:
            # Use model weights
            if self._model_type == "fixed":
                weights = 1.0 / (ses**2)
            else:
                # For random-effects, first estimate tau2 from simple pooling
                pooled = meta_analysis(y, ses, model="random", ci_level=self._ci_level)
                tau2 = pooled.tau2
                weights = 1.0 / (ses**2 + tau2)

        # Weighted least squares
        coef, se_coef, z_scores, p_values = weighted_least_squares(y, X, weights)

        # Create results table
        coef_names = ["Intercept"] + predictors
        regression_df = pd.DataFrame(
            {
                "predictor": coef_names,
                "coef": coef,
                "se": se_coef,
                "z": z_scores,
                "p": p_values,
            }
        )

        # Store regression results in provenance
        meta_provenance["meta_regression"] = {
            "formula": self._meta_regress_formula,
            "coefficients": regression_df.to_dict(orient="records"),
        }

        # For now, return empty pooled_effects and network_effects
        # Since regression is a different type of analysis
        pooled_df = pd.DataFrame(
            [
                {
                    "model": self._model_type,
                    "note": "Meta-regression results in meta_provenance",
                }
            ]
        )

        network_df = effect_table.copy()

        return MetaResult(
            pooled_effects=pooled_df,
            network_effects=network_df,
            meta_provenance=meta_provenance,
            model=self._model_type,
            subgroup_column=None,
        )


class MetaProxy:
    """Factory proxy for creating MetaBuilder instances."""

    @staticmethod
    def meta(name: Optional[str] = None) -> MetaBuilder:
        """Create a new MetaBuilder.

        Args:
            name: Optional name for the meta-analysis

        Returns:
            New MetaBuilder instance
        """
        return MetaBuilder(name=name)


# Singleton instance for import
M = MetaProxy()
