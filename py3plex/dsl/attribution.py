"""Attribution explanation module for DSL queries.

This module implements Shapley attribution for node scores and ranks. It supports:
- Layer attribution (exact and Monte Carlo Shapley)
- Edge attribution (with candidate selection)
- Deterministic computation with seed control
"""

from collections import OrderedDict
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple
from itertools import combinations
from statistics import median
import math
import random

import networkx as nx


@dataclass
class AttributionConfig:
    """Configuration for attribution explanations.

    This is the stable, public schema for attribution requests.
    All fields are JSON-serializable and included in provenance.

    Attributes:
        metric: Which computed metric to explain (required)
        objective: "value" (explain score) or "rank" (explain rank position)
        levels: List of attribution levels - ["layer", "edge"]
        method: "shapley" (exact) or "shapley_mc" (Monte Carlo)
        feature_space: Layer attribution uses "layers"
        n_permutations: Positive number of permutations for Monte Carlo (default 128)
        max_exact_features: Maximum features for exact Shapley (default 8)
        seed: Random seed for reproducibility
        n_jobs: Reserved
        edge_scope: Edge attribution uses "incident"
        k_hop: Reserved
        max_edges: Maximum candidate edges (default 40)
        top_k_layers: Number of layer contributions to return (default 10)
        top_k_edges: Number of edge contributions to return (default 20)
        include_negative: Include negative contributions (default True)
        cache: Enable subset computation caching (default True)
        uq: Attribution requires "off"
        ci_level: Reserved
    """

    metric: Optional[str] = None
    objective: str = "value"  # "value" or "rank"
    levels: List[str] = field(default_factory=lambda: ["layer"])
    method: str = "shapley_mc"
    feature_space: str = "layers"
    n_permutations: int = 128
    max_exact_features: int = 8
    seed: Optional[int] = None
    n_jobs: Optional[int] = None
    edge_scope: str = "incident"
    k_hop: int = 2
    max_edges: int = 40
    top_k_layers: int = 10
    top_k_edges: int = 20
    include_negative: bool = True
    cache: bool = True
    uq: str = "off"
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
    layer_baseline_value: Optional[float] = None
    edge_baseline_value: Optional[float] = None
    layer_residual: Optional[float] = None
    edge_residual: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Export as dictionary (JSON-serializable)."""
        return asdict(self)


class AttributionEngine:
    """Evaluate Shapley games on layer-induced or edge-restricted graphs."""

    def __init__(self, network: Any, config: AttributionConfig, context: Dict[str, Any]):
        from .registry import measure_registry

        self.config = config
        self.context = context
        self.graph = network.core_network
        self.measure = None
        if "measure_graphs" in context:
            if config.metric not in context["measure_graphs"]:
                raise ValueError(
                    f"Attribution requires an exact, graph-based node measure: {config.metric!r}"
                )
            self.graph, self.measure = context["measure_graphs"][config.metric]
        else:
            self.measure = measure_registry.get(config.metric, target="nodes")
        self.layers = tuple(dict.fromkeys(node[1] for node in self.graph))
        self.rng = random.Random(config.seed)
        self.cache = OrderedDict() if config.cache else None
        self.cache_hits = 0
        self.cache_misses = 0

    def _scores(self, layers, hidden_edges):
        """Compute the registered measure once per distinct coalition."""
        key = layers, hidden_edges
        if self.cache is not None and key in self.cache:
            self.cache_hits += 1
            self.cache.move_to_end(key)
            return self.cache[key]
        self.cache_misses += 1
        graph = self.graph
        if layers is not None:
            graph = graph.subgraph(node for node in graph if node[1] in layers)
        if hidden_edges:
            graph = nx.restricted_view(graph, (), hidden_edges)
        scores = self.measure(graph) if graph else {}
        if self.cache is not None:
            self.cache[key] = scores
            if len(self.cache) > 256:
                self.cache.popitem(last=False)
        return scores

    @staticmethod
    def _point_score(scores, item):
        value = float(scores.get(item, 0.0))
        if not math.isfinite(value):
            raise ValueError(f"Attribution measure returned a non-finite score for {item!r}.")
        return value

    def _utility(self, scores, item, ranking_items):
        value = self._point_score(scores, item)
        if self.config.objective == "value":
            return value
        direction = -1 if self.context.get("ascending") else 1
        ranked_scores = sorted(
            (direction * self._point_score(scores, node) for node in ranking_items),
            reverse=True,
        )
        limit = self.context.get("limit")
        cutoff = ranked_scores[limit] if limit and limit < len(ranked_scores) else median(ranked_scores)
        return direction * value - cutoff

    def _shapley(self, features, utility, warnings):
        count = len(features)
        contributions = dict.fromkeys(features, 0.0)
        if self.config.method == "shapley" and count <= self.config.max_exact_features:
            for feature in features:
                others = [other for other in features if other != feature]
                for size in range(count):
                    weight = 1 / (count * math.comb(count - 1, size))
                    for subset in combinations(others, size):
                        coalition = frozenset(subset)
                        marginal = utility(coalition | {feature}) - utility(coalition)
                        contributions[feature] += weight * marginal
        else:
            if self.config.method == "shapley":
                warnings.append(f"Using Monte Carlo for {count} features")
            for _ in range(self.config.n_permutations):
                coalition = frozenset()
                previous = utility(coalition)
                for feature in self.rng.sample(features, count):
                    coalition = coalition | {feature}
                    current = utility(coalition)
                    contributions[feature] += current - previous
                    previous = current
            contributions = {
                feature: value / self.config.n_permutations
                for feature, value in contributions.items()
            }
        return contributions

    def _incident_edges(self, item):
        if item not in self.graph:
            return []
        graph = self.graph
        kwargs = {"keys": True} if graph.is_multigraph() else {}
        edges = list(graph.edges(item, **kwargs))
        if graph.is_directed():
            edges = list(dict.fromkeys(edges + list(graph.in_edges(item, **kwargs))))
        return edges

    def _edge_weight(self, edge):
        return float(self.graph.edges[edge].get("weight", 1.0))

    def _display_contributions(self, raw, label, limit):
        ordered = sorted(raw, key=lambda feature: abs(raw[feature]), reverse=True)
        rows = []
        for feature in ordered:
            if not self.config.include_negative and raw[feature] < 0:
                continue
            rows.append({label: feature, "phi": raw[feature]})
        return rows[:limit]

    def compute_attribution(
        self, item: Tuple[Any, ...], metric_values: Dict[Any, Any]
    ) -> AttributionResult:
        warnings = []
        observed = metric_values[self.config.metric]
        ranking_items = self.context.get("ranking_items", tuple(observed))
        full_value = self._utility(observed, item, ranking_items)
        empty = frozenset()
        layer_rows, edge_rows = [], []
        layer_baseline, edge_baseline = None, None
        layer_residual, edge_residual = None, None
        candidate_count, used_count = None, None
        sampled = self.config.method == "shapley_mc"

        if "layer" in self.config.levels:
            def layer_utility(layers):
                return self._utility(self._scores(layers, empty), item, ranking_items)

            sampled |= len(self.layers) > self.config.max_exact_features
            layers = self._shapley(self.layers, layer_utility, warnings)
            layer_baseline = layer_utility(empty)
            layer_residual = full_value - layer_baseline - math.fsum(layers.values())
            layer_rows = self._display_contributions(layers, "layer", self.config.top_k_layers)

        if "edge" in self.config.levels:
            edges = self._incident_edges(item)
            candidate_count = len(edges)
            if len(edges) > self.config.max_edges:
                warnings.append(f"Using {self.config.max_edges} of {len(edges)} incident edges")
                edges = sorted(edges, key=self._edge_weight, reverse=True)[:self.config.max_edges]
            used_count = len(edges)
            sampled |= used_count > self.config.max_exact_features
            all_edges = frozenset(edges)

            def edge_utility(kept):
                return self._utility(self._scores(None, all_edges - kept), item, ranking_items)

            contributions = self._shapley(edges, edge_utility, warnings)
            edge_baseline = edge_utility(empty)
            edge_residual = full_value - edge_baseline - math.fsum(contributions.values())
            edge_rows = self._display_contributions(contributions, "edge", self.config.top_k_edges)
            for row in edge_rows:
                source, target, *key = row["edge"]
                row["edge"] = [source[0], target[0], source[1], target[1], *key]

        primary_baseline = layer_baseline if layer_baseline is not None else edge_baseline
        primary_residual = layer_residual if layer_residual is not None else edge_residual
        utility_def = None
        if self.config.objective == "rank":
            limit = self.context.get("limit")
            utility_def = (
                f"margin_to_cutoff(limit={limit})"
                if limit and limit < len(ranking_items) else "margin_to_median"
            )
        cache_rate = None
        if self.cache is not None and self.cache_hits + self.cache_misses:
            cache_rate = self.cache_hits / (self.cache_hits + self.cache_misses)

        return AttributionResult(
            metric=self.config.metric,
            objective=self.config.objective,
            utility_def=utility_def,
            levels=self.config.levels,
            method=self.config.method,
            seed=self.config.seed,
            n_permutations=self.config.n_permutations if sampled else None,
            feature_space=self.config.feature_space,
            full_value=full_value,
            baseline_value=primary_baseline,
            delta=full_value - primary_baseline,
            residual=primary_residual,
            layer_contrib=layer_rows,
            edge_contrib=edge_rows,
            warnings=warnings,
            cache_hit_rate=cache_rate,
            candidate_edge_count=candidate_count,
            used_edge_count=used_count,
            edge_scope=self.config.edge_scope if used_count is not None else None,
            layer_baseline_value=layer_baseline,
            edge_baseline_value=edge_baseline,
            layer_residual=layer_residual,
            edge_residual=edge_residual,
        )


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

    errors = [warning for warning in config.validate() if warning.startswith("Invalid")]
    if config.method == "influence":
        errors.append("method must be 'shapley' or 'shapley_mc'")
    if config.n_permutations <= 0:
        errors.append("n_permutations must be positive")
    if not config.levels or set(config.levels) - {"layer", "edge"}:
        errors.append("levels must contain 'layer', 'edge', or both")
    if "layer" in config.levels and config.feature_space != "layers":
        errors.append("feature_space must be 'layers'")
    if "edge" in config.levels and config.edge_scope != "incident":
        errors.append("edge_scope must be 'incident'")
    if config.uq != "off":
        errors.append("uq must be 'off' for deterministic attribution")
    if min(config.max_exact_features, config.max_edges, config.top_k_layers, config.top_k_edges) < 0:
        errors.append("feature and output limits must be non-negative")
    if errors:
        raise Py3plexException(f"Attribution configuration errors: {'; '.join(errors)}")

    if config.metric is None:
        if "order_by" in context and context["order_by"] in metric_values:
            config.metric = context["order_by"]
        elif len(metric_values) == 1:
            config.metric = next(iter(metric_values))
        else:
            raise Py3plexException(
                "Attribution requires one computed metric or an explicit metric. "
                f"Available metrics: {list(metric_values)}"
            )

    if config.metric not in metric_values:
        raise Py3plexException(
            f"Metric '{config.metric}' not found in computed metrics. "
            f"Available metrics: {list(metric_values)}"
        )
    if any(isinstance(value, dict) for value in metric_values[config.metric].values()):
        raise Py3plexException("Attribution requires point estimates from a deterministic measure.")
    if config.objective == "rank" and context.get("order_by", config.metric) != config.metric:
        raise Py3plexException("Rank attribution requires ordering by the explained metric.")

    engine = AttributionEngine(network, config, context)
    enriched_rows = []
    for row in rows:
        item = (row["id"], row["layer"])
        attribution = engine.compute_attribution(item, metric_values)
        enriched_rows.append({**row, "attribution": attribution.to_dict()})

    return enriched_rows, {"config": config.to_dict(), "n_items": len(rows)}
