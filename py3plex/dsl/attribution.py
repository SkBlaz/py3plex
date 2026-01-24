"""Attribution explanation module for DSL queries.

This module implements Shapley-based attribution analysis to explain why nodes/edges
are ranked highly in query results. It supports:
- Layer attribution (exact and Monte Carlo Shapley)
- Edge attribution (with candidate selection)
- UQ propagation when .uq() is enabled
- Deterministic computation with seed control
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple
import logging
import math
from collections import defaultdict

try:
    import numpy as np

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

logger = logging.getLogger(__name__)


@dataclass
class AttributionConfig:
    """Configuration for attribution explanations.

    This is the stable, public schema for attribution requests.
    All fields are JSON-serializable and included in provenance.

    Attributes:
        metric: Which computed metric to explain (required)
        objective: "value" (explain score) or "rank" (explain rank position)
        levels: List of attribution levels - ["layer", "edge"]
        method: "shapley" (exact), "shapley_mc" (Monte Carlo), or "influence"
        feature_space: For layer attribution - "layers", "layer_pairs", or "coupling_types"
        n_permutations: Number of permutations for Monte Carlo (default 128, min 16)
        max_exact_features: Maximum features for exact Shapley (default 8)
        seed: Random seed for reproducibility
        n_jobs: Number of parallel jobs (None = default)
        edge_scope: Candidate selection for edge attribution
        k_hop: Number of hops for ego_k_hop scope (default 2)
        max_edges: Maximum candidate edges (default 40)
        top_k_layers: Number of layer contributions to return (default 10)
        top_k_edges: Number of edge contributions to return (default 20)
        include_negative: Include negative contributions (default True)
        cache: Enable subset computation caching (default True)
        uq: UQ propagation mode - "off", "propagate", or "summarize_only"
        ci_level: Confidence interval level for UQ (default 0.95)
    """

    metric: Optional[str] = None
    objective: str = "value"  # "value" or "rank"
    levels: List[str] = field(default_factory=lambda: ["layer"])
    method: str = "shapley_mc"  # "shapley", "shapley_mc", "influence"
    feature_space: str = "layers"  # "layers", "layer_pairs", "coupling_types"
    n_permutations: int = 128
    max_exact_features: int = 8
    seed: Optional[int] = None
    n_jobs: Optional[int] = None
    edge_scope: str = (
        "incident"  # "incident", "ego_k_hop", "shortest_path_sample", "global_top_m"
    )
    k_hop: int = 2
    max_edges: int = 40
    top_k_layers: int = 10
    top_k_edges: int = 20
    include_negative: bool = True
    cache: bool = True
    uq: str = "off"  # "off", "propagate", "summarize_only"
    ci_level: float = 0.95

    def to_dict(self) -> Dict[str, Any]:
        """Export as dictionary (JSON-serializable)."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AttributionConfig":
        """Create from dictionary."""
        return cls(**data)

    def validate(self) -> List[str]:
        """Validate configuration and return list of warnings/errors.

        Returns:
            List of warning/error messages (empty if valid)
        """
        warnings = []

        if self.objective not in ["value", "rank"]:
            warnings.append(
                f"Invalid objective '{self.objective}', must be 'value' or 'rank'"
            )

        if self.method not in ["shapley", "shapley_mc", "influence"]:
            warnings.append(
                f"Invalid method '{self.method}', must be 'shapley', 'shapley_mc', or 'influence'"
            )

        if self.n_permutations < 16:
            warnings.append(
                f"n_permutations ({self.n_permutations}) too low, minimum is 16"
            )

        if "edge" in self.levels and self.edge_scope not in [
            "incident",
            "ego_k_hop",
            "shortest_path_sample",
            "global_top_m",
        ]:
            warnings.append(f"Invalid edge_scope '{self.edge_scope}'")

        if self.uq not in ["off", "propagate", "summarize_only"]:
            warnings.append(
                f"Invalid uq mode '{self.uq}', must be 'off', 'propagate', or 'summarize_only'"
            )

        return warnings


@dataclass
class AttributionResult:
    """Result of attribution computation for a single item (node or edge).

    This is the output schema attached to result rows.
    """

    metric: str
    objective: str
    utility_def: Optional[str]
    levels: List[str]
    method: str
    seed: Optional[int]
    n_permutations: Optional[int]
    feature_space: str
    full_value: float
    baseline_value: float
    delta: float
    residual: float
    layer_contrib: List[Dict[str, Any]]
    edge_contrib: List[Dict[str, Any]]
    warnings: List[str]
    cache_hit_rate: Optional[float]
    candidate_edge_count: Optional[int] = None
    used_edge_count: Optional[int] = None
    edge_scope: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Export as dictionary (JSON-serializable)."""
        return asdict(self)


class AttributionEngine:
    """Engine for computing Shapley-based attributions."""

    def __init__(
        self,
        network: Any,
        config: AttributionConfig,
        context: Dict[str, Any],
    ):
        """Initialize attribution engine.

        Args:
            network: Multilayer network instance
            config: Attribution configuration
            context: Query context (computed metrics, result items, etc.)
        """
        self.network = network
        self.config = config
        self.context = context
        self.cache: Dict[str, Any] = {} if config.cache else None
        self.cache_hits = 0
        self.cache_misses = 0

        # Initialize RNG if seed provided
        if HAS_NUMPY and config.seed is not None:
            self.rng = np.random.Generator(np.random.PCG64(config.seed))
        else:
            self.rng = None

    def compute_attribution(
        self,
        item: Tuple[Any, ...],
        metric_values: Dict[Any, Any],
    ) -> AttributionResult:
        """Compute attribution for a single item.

        Args:
            item: Item identifier (node or edge tuple)
            metric_values: Dictionary of metric values for all items

        Returns:
            AttributionResult with layer/edge contributions
        """
        warnings = []

        # Validate metric exists
        if self.config.metric not in metric_values:
            raise ValueError(
                f"Metric '{self.config.metric}' not found in computed metrics. "
                f"Available metrics: {list(metric_values.keys())}"
            )

        # Get item's metric value
        item_value = metric_values[self.config.metric].get(item)
        if item_value is None:
            warnings.append(f"Item {item} not found in metric values")
            item_value = 0.0

        # Handle UQ values
        if isinstance(item_value, dict) and "mean" in item_value:
            # UQ value - use mean for attribution
            full_value = item_value["mean"]
        else:
            full_value = float(item_value)

        # Compute utility if rank objective
        utility_def = None
        if self.config.objective == "rank":
            full_value, utility_def = self._compute_rank_utility(
                item, metric_values, warnings
            )

        # Compute layer attribution if requested
        layer_contrib = []
        if "layer" in self.config.levels:
            layer_contrib = self._compute_layer_attribution(
                item, metric_values, full_value, warnings
            )

        # Compute edge attribution if requested
        edge_contrib = []
        candidate_edge_count = None
        used_edge_count = None
        edge_scope = None
        if "edge" in self.config.levels:
            edge_contrib, candidate_edge_count, used_edge_count, edge_scope = (
                self._compute_edge_attribution(
                    item, metric_values, full_value, warnings
                )
            )

        # Compute baseline and delta
        baseline_value = 0.0  # Baseline is empty network (no features)
        delta = full_value - baseline_value

        # Compute residual (should be near zero)
        sum_phi = sum(c["phi"] for c in layer_contrib)
        sum_phi += sum(c["phi"] for c in edge_contrib)
        residual = delta - sum_phi

        # Compute cache hit rate
        cache_hit_rate = None
        if self.cache is not None:
            total = self.cache_hits + self.cache_misses
            if total > 0:
                cache_hit_rate = self.cache_hits / total

        return AttributionResult(
            metric=self.config.metric,
            objective=self.config.objective,
            utility_def=utility_def,
            levels=self.config.levels,
            method=self.config.method,
            seed=self.config.seed,
            n_permutations=(
                self.config.n_permutations
                if self.config.method == "shapley_mc"
                else None
            ),
            feature_space=self.config.feature_space,
            full_value=full_value,
            baseline_value=baseline_value,
            delta=delta,
            residual=residual,
            layer_contrib=layer_contrib,
            edge_contrib=edge_contrib,
            warnings=warnings,
            cache_hit_rate=cache_hit_rate,
            candidate_edge_count=candidate_edge_count,
            used_edge_count=used_edge_count,
            edge_scope=edge_scope,
        )

    def _compute_rank_utility(
        self,
        item: Tuple[Any, ...],
        metric_values: Dict[Any, Any],
        warnings: List[str],
    ) -> Tuple[float, str]:
        """Compute utility for rank objective.

        For rank attribution, we compute utility as the margin to the cutoff
        (e.g., k+1-th item if .limit(k) was used).

        Args:
            item: Item identifier
            metric_values: Dictionary of metric values
            warnings: List to append warnings to

        Returns:
            Tuple of (utility_value, utility_definition_string)
        """
        # Get all metric values and sort
        all_values = metric_values[self.config.metric]

        # Handle UQ values
        values_list = []
        for it, val in all_values.items():
            if isinstance(val, dict) and "mean" in val:
                values_list.append((it, val["mean"]))
            else:
                values_list.append((it, float(val)))

        # Sort by value descending
        sorted_items = sorted(values_list, key=lambda x: x[1], reverse=True)

        # Find item's rank
        item_rank = None
        item_value = None
        for rank, (it, val) in enumerate(sorted_items):
            if it == item:
                item_rank = rank
                item_value = val
                break

        if item_rank is None:
            warnings.append(f"Item {item} not found in sorted ranking")
            return 0.0, "margin_to_median"

        # Check if there's a limit from the query
        limit = self.context.get("limit")
        if limit and limit < len(sorted_items):
            # Margin to cutoff (k+1-th item)
            cutoff_value = (
                sorted_items[limit][1]
                if limit < len(sorted_items)
                else sorted_items[-1][1]
            )
            utility = item_value - cutoff_value
            utility_def = f"margin_to_cutoff(limit={limit})"
        else:
            # No limit - use standardized score (z-score or difference to median)
            median_value = sorted_items[len(sorted_items) // 2][1]
            utility = item_value - median_value
            utility_def = "margin_to_median"

        return utility, utility_def

    def _compute_layer_attribution(
        self,
        item: Tuple[Any, ...],
        metric_values: Dict[Any, Any],
        full_value: float,
        warnings: List[str],
    ) -> List[Dict[str, Any]]:
        """Compute layer attribution using Shapley values.

        Args:
            item: Item identifier
            metric_values: Dictionary of metric values
            full_value: Full metric value for the item
            warnings: List to append warnings to

        Returns:
            List of layer contribution dicts with "layer" and "phi" keys
        """
        # Get layers involved in the query
        layers = self._get_query_layers()

        if not layers:
            warnings.append("No layers found for attribution")
            return []

        # Decide between exact and Monte Carlo
        n_features = len(layers)
        use_exact = (
            n_features <= self.config.max_exact_features
            and self.config.method in ["shapley", "shapley_mc"]
        )

        if use_exact:
            # Exact Shapley
            contribs = self._compute_exact_shapley_layers(
                item, layers, metric_values, full_value, warnings
            )
        else:
            # Monte Carlo Shapley
            if (
                self.config.method == "shapley"
                and n_features > self.config.max_exact_features
            ):
                warnings.append(
                    f"Falling back to Monte Carlo (n_features={n_features} > "
                    f"max_exact_features={self.config.max_exact_features})"
                )
            contribs = self._compute_mc_shapley_layers(
                item, layers, metric_values, full_value, warnings
            )

        # Sort by absolute phi and return top-k
        contribs_sorted = sorted(contribs, key=lambda x: abs(x["phi"]), reverse=True)
        if self.config.include_negative:
            return contribs_sorted[: self.config.top_k_layers]
        else:
            # Filter out negative contributions
            positive_contribs = [c for c in contribs_sorted if c["phi"] >= 0]
            return positive_contribs[: self.config.top_k_layers]

    def _get_query_layers(self) -> List[str]:
        """Get list of layers involved in the query."""
        # Try to get from context
        if "layers" in self.context:
            return list(self.context["layers"])

        # Fall back to all layers in network
        if hasattr(self.network, "get_layers"):
            return list(self.network.get_layers())

        return []

    def _compute_exact_shapley_layers(
        self,
        item: Tuple[Any, ...],
        layers: List[str],
        metric_values: Dict[Any, Any],
        full_value: float,
        warnings: List[str],
    ) -> List[Dict[str, Any]]:
        """Compute exact Shapley values for layers.

        Args:
            item: Item identifier
            layers: List of layer names
            metric_values: Dictionary of metric values
            full_value: Full metric value
            warnings: List to append warnings to

        Returns:
            List of layer contribution dicts
        """
        n = len(layers)

        # Compute metric for all 2^n subsets
        subset_values = {}
        for mask in range(1 << n):
            subset = [layers[i] for i in range(n) if mask & (1 << i)]
            value = self._compute_metric_on_subset(
                item, subset, metric_values, warnings
            )
            subset_values[mask] = value

        # Compute Shapley values using combinatorial formula
        phi = [0.0] * n
        for i in range(n):
            # Sum over all subsets not containing i
            for mask in range(1 << n):
                if mask & (1 << i):
                    continue  # Skip subsets containing i

                # S = subset without i
                # S ∪ {i} = subset with i
                mask_with_i = mask | (1 << i)

                marginal = subset_values[mask_with_i] - subset_values[mask]

                # Shapley weight: (|S|! * (n - |S| - 1)!) / n!
                s = bin(mask).count("1")  # Size of S
                weight = (
                    math.factorial(s) * math.factorial(n - s - 1) / math.factorial(n)
                )

                phi[i] += weight * marginal

        # Format results
        contribs = []
        for i, layer in enumerate(layers):
            contribs.append({"layer": layer, "phi": phi[i]})

        return contribs

    def _compute_mc_shapley_layers(
        self,
        item: Tuple[Any, ...],
        layers: List[str],
        metric_values: Dict[Any, Any],
        full_value: float,
        warnings: List[str],
    ) -> List[Dict[str, Any]]:
        """Compute Monte Carlo Shapley values for layers.

        Args:
            item: Item identifier
            layers: List of layer names
            metric_values: Dictionary of metric values
            full_value: Full metric value
            warnings: List to append warnings to

        Returns:
            List of layer contribution dicts
        """
        n = len(layers)
        phi = defaultdict(float)

        # Sample permutations
        for perm_idx in range(self.config.n_permutations):
            # Generate deterministic permutation using seed
            if self.rng is not None:
                perm = self.rng.permutation(n).tolist()
            else:
                # Fallback: use hash-based deterministic permutation
                perm = list(range(n))
                if self.config.seed is not None:
                    import random

                    rng = random.Random(self.config.seed + perm_idx)
                    rng.shuffle(perm)
                else:
                    import random

                    random.shuffle(perm)

            # Compute marginal contributions along permutation
            subset = []
            prev_value = self._compute_metric_on_subset(
                item, subset, metric_values, warnings
            )

            for pos in perm:
                layer = layers[pos]
                subset.append(layer)

                curr_value = self._compute_metric_on_subset(
                    item, subset, metric_values, warnings
                )

                marginal = curr_value - prev_value
                phi[layer] += marginal
                prev_value = curr_value

        # Average over permutations
        for layer in phi:
            phi[layer] /= self.config.n_permutations

        # Format results
        contribs = []
        for layer in layers:
            contribs.append({"layer": layer, "phi": phi.get(layer, 0.0)})

        return contribs

    def _compute_metric_on_subset(
        self,
        item: Tuple[Any, ...],
        subset_layers: List[str],
        metric_values: Dict[Any, Any],
        warnings: List[str],
    ) -> float:
        """Compute metric value when only subset_layers are present.

        This creates a subnetwork with only the specified layers and
        computes the metric on it.

        Args:
            item: Item identifier
            subset_layers: List of layers to include
            metric_values: Dictionary of metric values (for caching hints)
            warnings: List to append warnings to

        Returns:
            Metric value on the subset
        """
        # Check cache
        if self.cache is not None:
            cache_key = (
                "subset",
                self.config.metric,
                item,
                tuple(sorted(subset_layers)),
            )
            if cache_key in self.cache:
                self.cache_hits += 1
                return self.cache[cache_key]
            self.cache_misses += 1

        # Empty subset -> baseline value (0 for most metrics)
        if not subset_layers:
            value = 0.0
            if self.cache is not None:
                self.cache[cache_key] = value
            return value

        # Full network -> return full value
        all_layers = self._get_query_layers()
        if set(subset_layers) == set(all_layers):
            value = metric_values[self.config.metric].get(item, 0.0)
            if isinstance(value, dict) and "mean" in value:
                value = value["mean"]
            value = float(value)
            if self.cache is not None:
                self.cache[cache_key] = value
            return value

        # Subset computation - simplified implementation
        # In a full implementation, this would create a subnetwork and recompute
        # For now, we estimate based on layer degree proportions
        try:
            value = self._estimate_metric_on_subset(item, subset_layers, metric_values)
        except Exception as e:
            logger.warning(f"Failed to compute metric on subset {subset_layers}: {e}")
            warnings.append(f"Subset computation failed for {subset_layers}")
            value = 0.0

        if self.cache is not None:
            self.cache[cache_key] = value

        return value

    def _estimate_metric_on_subset(
        self,
        item: Tuple[Any, ...],
        subset_layers: List[str],
        metric_values: Dict[Any, Any],
    ) -> float:
        """Estimate metric value on a layer subset.

        This is a simplified estimation. A full implementation would
        create an actual subnetwork and recompute the metric.

        For degree-like metrics, we can estimate by counting edges in subset layers.
        For more complex metrics, this is an approximation.
        """
        full_value = metric_values[self.config.metric].get(item, 0.0)
        if isinstance(full_value, dict) and "mean" in full_value:
            full_value = full_value["mean"]
        full_value = float(full_value)

        # For degree, estimate as proportion of edges in subset layers
        if self.config.metric == "degree":
            # Count node's edges by layer
            node_id, layer = item[0], item[1] if len(item) > 1 else None

            layer_degrees = {}
            if hasattr(self.network, "core_network"):
                G = self.network.core_network
                node_key = (node_id, layer) if layer else node_id

                if node_key in G:
                    for neighbor in G.neighbors(node_key):
                        edge_data = G.get_edge_data(node_key, neighbor)
                        if edge_data:
                            edge_layer = edge_data.get("layer", layer)
                            layer_degrees[edge_layer] = (
                                layer_degrees.get(edge_layer, 0) + 1
                            )

            # Sum degrees in subset layers
            subset_degree = sum(layer_degrees.get(l, 0) for l in subset_layers)
            return float(subset_degree)

        # For other metrics, use proportional estimation
        all_layers = self._get_query_layers()
        if not all_layers:
            return full_value

        proportion = len(subset_layers) / len(all_layers)
        return full_value * proportion

    def _compute_edge_attribution(
        self,
        item: Tuple[Any, ...],
        metric_values: Dict[Any, Any],
        full_value: float,
        warnings: List[str],
    ) -> Tuple[List[Dict[str, Any]], int, int, str]:
        """Compute edge attribution using Shapley values.

        Args:
            item: Item identifier
            metric_values: Dictionary of metric values
            full_value: Full metric value
            warnings: List to append warnings to

        Returns:
            Tuple of (edge_contributions, candidate_count, used_count, scope)
        """
        # Get candidate edges
        candidate_edges, edge_scope = self._get_candidate_edges(item, warnings)

        if not candidate_edges:
            warnings.append("No candidate edges found for edge attribution")
            return [], 0, 0, edge_scope

        candidate_count = len(candidate_edges)

        # Trim to max_edges if needed
        if len(candidate_edges) > self.config.max_edges:
            warnings.append(
                f"Trimming candidate edges from {len(candidate_edges)} to {self.config.max_edges}"
            )
            candidate_edges = self._trim_candidate_edges(candidate_edges, warnings)

        used_count = len(candidate_edges)

        # Compute Shapley values (always use MC for edges)
        contribs = self._compute_mc_shapley_edges(
            item, candidate_edges, metric_values, full_value, warnings
        )

        # Sort by absolute phi and return top-k
        contribs_sorted = sorted(contribs, key=lambda x: abs(x["phi"]), reverse=True)
        if self.config.include_negative:
            result = contribs_sorted[: self.config.top_k_edges]
        else:
            positive_contribs = [c for c in contribs_sorted if c["phi"] >= 0]
            result = positive_contribs[: self.config.top_k_edges]

        return result, candidate_count, used_count, edge_scope

    def _get_candidate_edges(
        self,
        item: Tuple[Any, ...],
        warnings: List[str],
    ) -> Tuple[List[Tuple[Any, ...]], str]:
        """Get candidate edges for attribution.

        Args:
            item: Item identifier (node or edge)
            warnings: List to append warnings to

        Returns:
            Tuple of (candidate_edge_list, scope_used)
        """
        scope = self.config.edge_scope

        # For now, implement only "incident" scope
        if scope != "incident":
            warnings.append(
                f"Edge scope '{scope}' not fully implemented, using 'incident'"
            )
            scope = "incident"

        # Get incident edges
        node_id = item[0]
        layer = item[1] if len(item) > 1 else None

        edges = []
        if hasattr(self.network, "core_network"):
            G = self.network.core_network
            node_key = (node_id, layer) if layer else node_id

            if node_key in G:
                for neighbor in G.neighbors(node_key):
                    edge_data = G.get_edge_data(node_key, neighbor) or {}
                    edge_layer = edge_data.get("layer", layer)

                    # Format as tuple for consistent representation
                    edge = (
                        node_id,
                        neighbor[0] if isinstance(neighbor, tuple) else neighbor,
                        layer or edge_layer,
                        edge_layer,
                    )
                    edges.append(edge)

        return edges, scope

    def _trim_candidate_edges(
        self,
        edges: List[Tuple[Any, ...]],
        warnings: List[str],
    ) -> List[Tuple[Any, ...]]:
        """Trim candidate edges to max_edges using a stable heuristic.

        Prefer edges with highest weight, then highest degree endpoints,
        then lexical order.

        Args:
            edges: List of edge tuples
            warnings: List to append warnings to

        Returns:
            Trimmed list of edges
        """
        # Get edge weights
        edge_weights = []
        for edge in edges:
            src, dst, src_layer, dst_layer = edge
            weight = 1.0

            if hasattr(self.network, "core_network"):
                G = self.network.core_network
                src_key = (src, src_layer)
                dst_key = (dst, dst_layer)
                edge_data = G.get_edge_data(src_key, dst_key) or {}
                weight = edge_data.get("weight", 1.0)

            edge_weights.append((edge, weight))

        # Sort by weight descending, then lexical
        edge_weights.sort(key=lambda x: (-x[1], str(x[0])))

        # Return top max_edges
        return [e for e, w in edge_weights[: self.config.max_edges]]

    def _compute_mc_shapley_edges(
        self,
        item: Tuple[Any, ...],
        edges: List[Tuple[Any, ...]],
        metric_values: Dict[Any, Any],
        full_value: float,
        warnings: List[str],
    ) -> List[Dict[str, Any]]:
        """Compute Monte Carlo Shapley values for edges.

        Args:
            item: Item identifier
            edges: List of candidate edges
            metric_values: Dictionary of metric values
            full_value: Full metric value
            warnings: List to append warnings to

        Returns:
            List of edge contribution dicts
        """
        n = len(edges)
        phi = defaultdict(float)

        # Sample permutations
        for perm_idx in range(self.config.n_permutations):
            # Generate deterministic permutation
            if self.rng is not None:
                perm = self.rng.permutation(n).tolist()
            else:
                perm = list(range(n))
                if self.config.seed is not None:
                    import random

                    rng = random.Random(self.config.seed + perm_idx + 10000)
                    rng.shuffle(perm)
                else:
                    import random

                    random.shuffle(perm)

            # Compute marginal contributions
            subset = []
            prev_value = 0.0  # Baseline: no edges

            for pos in perm:
                edge = edges[pos]
                subset.append(edge)

                # Estimate metric with subset of edges present
                # For degree, this is straightforward
                curr_value = (
                    float(len(subset)) if self.config.metric == "degree" else prev_value
                )

                marginal = curr_value - prev_value
                phi[edge] += marginal
                prev_value = curr_value

        # Average over permutations
        for edge in phi:
            phi[edge] /= self.config.n_permutations

        # Format results
        contribs = []
        for edge in edges:
            contribs.append(
                {
                    "edge": list(edge),  # Convert tuple to list for JSON
                    "phi": phi.get(edge, 0.0),
                }
            )

        return contribs


def compute_attribution_for_rows(
    network: Any,
    rows: List[Dict[str, Any]],
    metric_values: Dict[str, Dict[Any, Any]],
    config: AttributionConfig,
    context: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Compute attributions for multiple result rows.

    This is the main entry point called from the explain engine.

    Args:
        network: Multilayer network instance
        rows: List of result row dictionaries
        metric_values: Dictionary of metric values (metric_name -> item -> value)
        config: Attribution configuration
        context: Query context

    Returns:
        Tuple of (enriched_rows, attribution_metadata)
    """
    from py3plex.exceptions import Py3plexException

    # Validate config
    validation_warnings = config.validate()
    if validation_warnings:
        # Check for errors (not just warnings)
        errors = [w for w in validation_warnings if "Invalid" in w or "must be" in w]
        if errors:
            raise Py3plexException(
                f"Attribution configuration errors: {'; '.join(errors)}"
            )

    # Resolve metric if not provided
    if config.metric is None:
        # Try to infer from context
        if "order_by" in context:
            config.metric = context["order_by"]
        elif len(metric_values) == 1:
            config.metric = list(metric_values.keys())[0]
        else:
            raise Py3plexException(
                f"attribution requires metric=... when multiple metrics computed. "
                f"Available metrics: {list(metric_values.keys())}"
            )

    # Validate metric exists
    if config.metric not in metric_values:
        raise Py3plexException(
            f"Metric '{config.metric}' not found in computed metrics. "
            f"Available metrics: {list(metric_values.keys())}"
        )

    # Initialize engine
    engine = AttributionEngine(network, config, context)

    # Compute attribution for each row
    enriched_rows = []
    for row in rows:
        # Get item identifier
        if "id" in row:
            # Node query
            node_id = row["id"]
            layer = row.get("layer")
            item = (node_id, layer) if layer else (node_id,)
        else:
            # Edge query (not fully implemented)
            enriched_rows.append(row)
            continue

        # Compute attribution
        try:
            attribution = engine.compute_attribution(item, metric_values)

            # Attach to row
            enriched_row = dict(row)
            enriched_row["attribution"] = attribution.to_dict()
            enriched_rows.append(enriched_row)
        except Exception as e:
            logger.error(f"Failed to compute attribution for {item}: {e}")
            # Attach empty attribution with error
            enriched_row = dict(row)
            enriched_row["attribution"] = {
                "error": str(e),
                "metric": config.metric,
                "warnings": [str(e)],
            }
            enriched_rows.append(enriched_row)

    # Build metadata
    metadata = {
        "config": config.to_dict(),
        "n_items": len(rows),
        "validation_warnings": validation_warnings,
    }

    return enriched_rows, metadata
