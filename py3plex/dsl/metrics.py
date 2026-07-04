"""DSL metric registry.

Provides :class:`MetricSpec` — a frozen dataclass that declares metadata about
each supported DSL compute metric — and :data:`METRIC_REGISTRY`, a dict mapping
canonical metric names to their specs.

Alias lookups are handled internally by :func:`get_metric` — the registry itself
only contains canonical names so that ``METRIC_REGISTRY.items()`` iterates
canonical (key → spec) pairs.

Usage::

    from py3plex.dsl.metrics import get_metric, find_metric, is_known_metric, METRIC_REGISTRY

    spec = get_metric("betweenness_centrality")
    print(spec.cost_class)   # "quadratic"

    spec = get_metric("betweenness")    # alias lookup → same spec
    print(spec.name)                    # "betweenness_centrality"

    get_metric("unknown")    # raises ValueError
    find_metric("unknown")   # returns None (safe variant)
    is_known_metric("degree")  # True
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Literal, Optional, Tuple

__all__ = [
    "MetricSpec",
    "METRIC_REGISTRY",
    "get_metric",
    "find_metric",
    "is_known_metric",
]

CostClass = Literal[
    "constant",
    "linear",
    "near_linear",
    "quadratic",
    "cubic",
    "unknown",
]

Target = Literal["nodes", "edges", "any"]


@dataclass(frozen=True)
class MetricSpec:
    """Metadata for a single DSL compute metric.

    Attributes:
        name: Canonical metric name (e.g. ``"betweenness_centrality"``).
        target: Which query target the metric can be applied to.
        output_type: Numeric output type descriptor (``"float"`` etc.).
        requires: Tuple of other metric names that must be computed first.
        cost_class: Computational cost class.
        supports_uq: Whether the metric supports uncertainty quantification.
        supports_approx: Whether an approximate variant is available.
        deterministic: Whether the metric always produces the same result on the
            same graph.
        aliases: Additional names that resolve to this spec.
    """

    name: str
    target: Target = "nodes"
    output_type: str = "float"
    requires: Tuple[str, ...] = field(default_factory=tuple)
    cost_class: CostClass = "unknown"
    supports_uq: bool = False
    supports_approx: bool = False
    deterministic: bool = True
    aliases: Tuple[str, ...] = field(default_factory=tuple)

    def is_expensive(self) -> bool:
        """Return ``True`` when the metric has quadratic or worse cost."""
        return self.cost_class in ("quadratic", "cubic")


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_CORE_METRICS: Tuple[MetricSpec, ...] = (
    MetricSpec(
        name="degree",
        target="nodes",
        output_type="int",
        cost_class="linear",
        supports_uq=True,
        deterministic=True,
        aliases=("node_degree",),
    ),
    MetricSpec(
        name="degree_centrality",
        target="nodes",
        output_type="float",
        cost_class="linear",
        supports_uq=True,
        deterministic=True,
    ),
    MetricSpec(
        name="betweenness_centrality",
        target="nodes",
        output_type="float",
        cost_class="quadratic",
        supports_uq=True,
        supports_approx=True,
        deterministic=True,
        aliases=("betweenness",),
    ),
    MetricSpec(
        name="closeness_centrality",
        target="nodes",
        output_type="float",
        cost_class="quadratic",
        supports_uq=True,
        supports_approx=True,
        deterministic=True,
        aliases=("closeness",),
    ),
    MetricSpec(
        name="eigenvector_centrality",
        target="nodes",
        output_type="float",
        cost_class="near_linear",
        supports_uq=True,
        deterministic=False,
        aliases=("eigenvector",),
    ),
    MetricSpec(
        name="pagerank",
        target="nodes",
        output_type="float",
        cost_class="near_linear",
        supports_uq=True,
        supports_approx=True,
        deterministic=False,
        aliases=("page_rank",),
    ),
    MetricSpec(
        name="clustering",
        target="nodes",
        output_type="float",
        cost_class="linear",
        supports_uq=False,
        deterministic=True,
        aliases=("clustering_coefficient",),
    ),
    MetricSpec(
        name="strength",
        target="nodes",
        output_type="float",
        cost_class="linear",
        supports_uq=False,
        deterministic=True,
    ),
    MetricSpec(
        name="louvain_community",
        target="nodes",
        output_type="int",
        cost_class="near_linear",
        supports_uq=True,
        deterministic=False,
        aliases=("community",),
    ),
)


def _build_canonical_registry(
    specs: Tuple[MetricSpec, ...]
) -> Dict[str, MetricSpec]:
    """Build lookup containing ONLY canonical names as keys.

    Aliases are stored on the :class:`MetricSpec` objects themselves; they are
    resolved at lookup time by :func:`get_metric`.
    """
    registry: Dict[str, MetricSpec] = {}
    for spec in specs:
        registry[spec.name] = spec
    return registry


#: Flat mapping from **canonical** metric name to :class:`MetricSpec`.
#: Keys are canonical names only — use :func:`get_metric` for alias lookups.
#: Do not mutate this dict at runtime.
METRIC_REGISTRY: Dict[str, MetricSpec] = _build_canonical_registry(_CORE_METRICS)

# Pre-built alias → spec map for O(1) alias lookups (not exposed publicly).
_ALIAS_MAP: Dict[str, MetricSpec] = {
    alias: spec for spec in _CORE_METRICS for alias in spec.aliases
}


def find_metric(name: str) -> Optional[MetricSpec]:
    """Return the :class:`MetricSpec` for *name*, or ``None`` if unknown.

    Handles canonical names as well as registered aliases.

    Args:
        name: Metric name to look up.

    Returns:
        :class:`MetricSpec` or ``None``.
    """
    return METRIC_REGISTRY.get(name) or _ALIAS_MAP.get(name)


def get_metric(name: str) -> MetricSpec:
    """Return the :class:`MetricSpec` for *name*, raising if unknown.

    Handles canonical names as well as registered aliases.

    Args:
        name: Metric name to look up.

    Returns:
        :class:`MetricSpec`

    Raises:
        ValueError: If *name* is not a known canonical name or alias.
    """
    spec = find_metric(name)
    if spec is None:
        raise ValueError(
            f"Unknown metric {name!r}. "
            f"Known metrics: {sorted(METRIC_REGISTRY.keys())}"
        )
    return spec


def is_known_metric(name: str) -> bool:
    """Return ``True`` if *name* is a known metric (canonical or alias).

    Args:
        name: Metric name to check.

    Returns:
        bool
    """
    return name in METRIC_REGISTRY or name in _ALIAS_MAP
