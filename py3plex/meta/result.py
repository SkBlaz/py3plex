"""Result class for meta-analysis.

This module defines the MetaResult class which stores and provides
access to meta-analysis results.
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field


@dataclass
class MetaResult:
    """Result of meta-analysis pooling.

    Attributes:
        pooled_effects: DataFrame with pooled results
        network_effects: DataFrame with per-network effects
        meta_provenance: Aggregated provenance dictionary
        model: "fixed" or "random"
        subgroup_column: Column used for subgroup analysis (if any)
    """

    pooled_effects: pd.DataFrame
    network_effects: pd.DataFrame
    meta_provenance: Dict[str, Any]
    model: str
    subgroup_column: Optional[str] = None

    def to_pandas(self) -> pd.DataFrame:
        """Return pooled effects as tidy DataFrame.

        Returns:
            DataFrame with columns:
                - group keys (if any)
                - model
                - pooled_effect
                - pooled_se
                - ci_low
                - ci_high
                - k (number of studies)
                - tau2 (random-effects only)
                - Q (Cochran's Q)
                - I2 (I-squared percentage)
                - H (H statistic)
                - subgroup (if subgroup analysis)
        """
        return self.pooled_effects.copy()

    def network_table(self) -> pd.DataFrame:
        """Return per-network effects table.

        Returns:
            DataFrame with columns:
                - network_name
                - effect
                - se
                - weight_fixed
                - weight_random (if model is random)
                - group keys (if any)
                - network metadata fields (if any)
                - provenance pointers (ast_hash, etc.)
        """
        return self.network_effects.copy()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary.

        Returns:
            Dictionary with pooled_effects, network_effects, and meta_provenance
        """
        return {
            "pooled_effects": self.pooled_effects.to_dict(orient="records"),
            "network_effects": self.network_effects.to_dict(orient="records"),
            "meta_provenance": self.meta_provenance,
            "model": self.model,
            "subgroup_column": self.subgroup_column,
        }

    def __repr__(self) -> str:
        """String representation of MetaResult."""
        k = len(self.network_effects["network_name"].unique())
        n_groups = len(self.pooled_effects)

        parts = [
            f"MetaResult(",
            f"  model='{self.model}'",
            f"  k={k} networks",
        ]

        if n_groups > 1:
            parts.append(f"  {n_groups} groups")

        if self.subgroup_column:
            parts.append(f"  subgroup_by='{self.subgroup_column}'")

        # Show first pooled effect
        if not self.pooled_effects.empty:
            first_effect = self.pooled_effects.iloc[0]
            pooled = first_effect.get("pooled_effect", None)
            se = first_effect.get("pooled_se", None)
            if pooled is not None and se is not None:
                parts.append(f"  pooled_effect={pooled:.4f} (SE={se:.4f})")

        parts.append(")")
        return "\n".join(parts)
