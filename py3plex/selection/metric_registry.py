"""Metric registry for community quality evaluation."""

import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class MetricSpec:
    """Specification for a quality metric.
    
    Attributes:
        name: Metric name
        callable: Function to compute metric
        direction: "max" or "min"
        bucket: Metric category
        requires_uq: Whether this metric requires UQ samples
        enabled_by_default: Whether to include in default metric set
    """
    
    name: str
    callable: Callable
    direction: str
    bucket: str
    requires_uq: bool = False
    enabled_by_default: bool = True
    
    def __post_init__(self):
        """Validate metric spec."""
        if self.direction not in ["max", "min"]:
            raise ValueError(f"Invalid direction: {self.direction}")
        
        valid_buckets = ["objective", "structure", "sanity", "stability", "runtime", "predictive"]
        if self.bucket not in valid_buckets:
            raise ValueError(f"Invalid bucket: {self.bucket}. Must be one of {valid_buckets}")


class MetricRegistry:
    """Registry of quality metrics for community evaluation."""
    
    # Bucket caps (max contribution per bucket)
    BUCKET_CAPS = {
        "objective": 30,
        "structure": 30,
        "sanity": 30,
        "stability": 30,
        "runtime": 10,
        "predictive": 30,
    }
    
    def __init__(self):
        self.metrics: Dict[str, MetricSpec] = {}
        self._register_builtin_metrics()
    
    def _register_builtin_metrics(self):
        """Register built-in metrics."""
        # Try to import and register metrics from existing modules
        self._register_objective_metrics()
        self._register_structure_metrics()
        self._register_sanity_metrics()
        self._register_stability_metrics()
        self._register_runtime_metrics()
        self._register_multilayer_metrics()
    
    def _register_objective_metrics(self):
        """Register objective function metrics."""
        # Modularity (if available)
        try:
            from py3plex.algorithms.community_detection.community_measures import modularity
            self.register(MetricSpec(
                name="modularity",
                callable=modularity,
                direction="max",
                bucket="objective",
                requires_uq=False,
            ))
        except ImportError:
            logger.debug("modularity not available")
        
        # Multilayer modularity (if available)
        try:
            from py3plex.algorithms.community_detection.multilayer_modularity import multilayer_modularity
            self.register(MetricSpec(
                name="multilayer_modularity",
                callable=multilayer_modularity,
                direction="max",
                bucket="objective",
                requires_uq=False,
            ))
        except ImportError:
            logger.debug("multilayer_modularity not available")
    
    def _register_structure_metrics(self):
        """Register structural metrics."""
        # Coverage
        def coverage(partition: Dict, net: Any, context: Dict) -> float:
            """Fraction of edges within communities."""
            if not hasattr(net, "core_network"):
                return 0.0
            
            intra = 0
            total = 0
            
            for edge in net.core_network.edges():
                total += 1
                u, v = edge
                if u in partition and v in partition:
                    if partition[u] == partition[v]:
                        intra += 1
            
            return intra / total if total > 0 else 0.0
        
        self.register(MetricSpec(
            name="coverage",
            callable=coverage,
            direction="max",
            bucket="structure",
            requires_uq=False,
        ))
        
        # Conductance proxy (cut ratio)
        def cut_ratio(partition: Dict, net: Any, context: Dict) -> float:
            """Ratio of cut edges to total edges (lower is better)."""
            if not hasattr(net, "core_network"):
                return 1.0
            
            cut = 0
            total = 0
            
            for edge in net.core_network.edges():
                total += 1
                u, v = edge
                if u in partition and v in partition:
                    if partition[u] != partition[v]:
                        cut += 1
            
            return cut / total if total > 0 else 0.0
        
        self.register(MetricSpec(
            name="cut_ratio",
            callable=cut_ratio,
            direction="min",
            bucket="structure",
            requires_uq=False,
        ))
    
    def _register_sanity_metrics(self):
        """Register sanity check metrics."""
        # Singleton fraction
        def singleton_fraction(partition: Dict, net: Any, context: Dict) -> float:
            """Fraction of communities with only one member."""
            from collections import Counter
            counts = Counter(partition.values())
            singletons = sum(1 for c in counts.values() if c == 1)
            total = len(counts)
            return singletons / total if total > 0 else 0.0
        
        self.register(MetricSpec(
            name="singleton_fraction",
            callable=singleton_fraction,
            direction="min",
            bucket="sanity",
            requires_uq=False,
        ))
        
        # Community size entropy
        def community_size_entropy(partition: Dict, net: Any, context: Dict) -> float:
            """Shannon entropy of community sizes (higher = more balanced)."""
            from collections import Counter
            counts = Counter(partition.values())
            sizes = np.array(list(counts.values()))
            probs = sizes / sizes.sum()
            entropy = -np.sum(probs * np.log(probs + 1e-10))
            return float(entropy)
        
        self.register(MetricSpec(
            name="community_size_entropy",
            callable=community_size_entropy,
            direction="max",
            bucket="sanity",
            requires_uq=False,
        ))
        
        # Number of communities deviation from target range
        def n_communities_deviation(partition: Dict, net: Any, context: Dict) -> float:
            """Deviation from target community count range (lower is better)."""
            from collections import Counter
            n_communities = len(Counter(partition.values()))
            
            # Default broad target range: sqrt(n) to n/10
            n_nodes = len(partition)
            target_min = max(2, int(np.sqrt(n_nodes)))
            target_max = max(target_min + 1, n_nodes // 10)
            
            # Override from context if provided
            target_min = context.get("target_n_communities_min", target_min)
            target_max = context.get("target_n_communities_max", target_max)
            
            if target_min <= n_communities <= target_max:
                return 0.0
            elif n_communities < target_min:
                return float(target_min - n_communities)
            else:
                return float(n_communities - target_max)
        
        self.register(MetricSpec(
            name="n_communities_deviation",
            callable=n_communities_deviation,
            direction="min",
            bucket="sanity",
            requires_uq=False,
        ))
    
    def _register_stability_metrics(self):
        """Register stability metrics (require UQ)."""
        # Mean node entropy
        def mean_node_entropy_from_uq(partition: Dict, net: Any, context: Dict) -> float:
            """Mean per-node entropy from UQ (lower = more stable)."""
            uq = context.get("uq")
            if uq is None:
                return float("nan")
            return float(np.mean(uq.membership_entropy))
        
        self.register(MetricSpec(
            name="mean_node_entropy",
            callable=mean_node_entropy_from_uq,
            direction="min",
            bucket="stability",
            requires_uq=True,
        ))
        
        # VI mean
        def vi_mean_from_uq(partition: Dict, net: Any, context: Dict) -> float:
            """Mean VI from UQ (lower = more stable)."""
            uq = context.get("uq")
            if uq is None:
                return float("nan")
            return float(uq.vi_mean)
        
        self.register(MetricSpec(
            name="vi_mean",
            callable=vi_mean_from_uq,
            direction="min",
            bucket="stability",
            requires_uq=True,
        ))
        
        # NMI mean
        def nmi_mean_from_uq(partition: Dict, net: Any, context: Dict) -> float:
            """Mean NMI from UQ (higher = more stable)."""
            uq = context.get("uq")
            if uq is None:
                return float("nan")
            return float(uq.nmi_mean)
        
        self.register(MetricSpec(
            name="nmi_mean",
            callable=nmi_mean_from_uq,
            direction="max",
            bucket="stability",
            requires_uq=True,
        ))
    
    def _register_runtime_metrics(self):
        """Register runtime metrics."""
        def runtime_ms(partition: Dict, net: Any, context: Dict) -> float:
            """Runtime in milliseconds (from context)."""
            return context.get("runtime_ms", 0.0)
        
        self.register(MetricSpec(
            name="runtime_ms",
            callable=runtime_ms,
            direction="min",
            bucket="runtime",
            requires_uq=False,
        ))
    
    def _register_multilayer_metrics(self):
        """Register multilayer-specific quality metrics (guardrails)."""
        try:
            from py3plex.algorithms.community_detection.multilayer_quality_metrics import (
                replica_consistency,
                layer_entropy,
            )
            
            # Replica consistency: multilayer coherence
            # Weight: 0.15 (moderate guardrail)
            def replica_consistency_wrapper(partition: Dict, net: Any, context: Dict) -> float:
                """Replica consistency: coherence of node assignments across layers."""
                try:
                    return replica_consistency(partition, net)
                except Exception as e:
                    logger.warning(f"Failed to compute replica_consistency: {e}")
                    return 0.0
            
            self.register(MetricSpec(
                name="replica_consistency",
                callable=replica_consistency_wrapper,
                direction="max",
                bucket="structure",
                requires_uq=False,
                enabled_by_default=True,
            ))
            
            # Layer entropy: degeneracy guardrail
            # Weight: 0.07 (light guardrail)
            def layer_entropy_wrapper(partition: Dict, net: Any, context: Dict) -> float:
                """Layer entropy: normalized entropy of community sizes per layer."""
                try:
                    return layer_entropy(partition, net)
                except Exception as e:
                    logger.warning(f"Failed to compute layer_entropy: {e}")
                    return 0.0
            
            self.register(MetricSpec(
                name="layer_entropy",
                callable=layer_entropy_wrapper,
                direction="max",
                bucket="sanity",
                requires_uq=False,
                enabled_by_default=True,
            ))
            
            logger.debug("Registered multilayer quality metrics")
            
        except ImportError as e:
            logger.debug(f"Multilayer quality metrics not available: {e}")
    
    def register(self, metric: MetricSpec):
        """Register a metric.
        
        Args:
            metric: MetricSpec to register
        """
        if metric.name in self.metrics:
            logger.warning(f"Overwriting existing metric: {metric.name}")
        self.metrics[metric.name] = metric
        logger.debug(f"Registered metric: {metric.name} ({metric.bucket}, {metric.direction})")
    
    def get_default_metrics(self, uq_enabled: bool = False) -> List[MetricSpec]:
        """Get default metric set.
        
        Args:
            uq_enabled: Whether UQ is enabled (affects stability metrics)
        
        Returns:
            List of MetricSpec objects
        """
        defaults = []
        for metric in self.metrics.values():
            if not metric.enabled_by_default:
                continue
            
            # Skip UQ metrics if UQ not enabled
            if metric.requires_uq and not uq_enabled:
                continue
            
            defaults.append(metric)
        
        return defaults
    
    def get_metrics_by_bucket(self, bucket: str) -> List[MetricSpec]:
        """Get metrics in a specific bucket.
        
        Args:
            bucket: Bucket name
        
        Returns:
            List of MetricSpec objects
        """
        return [m for m in self.metrics.values() if m.bucket == bucket]


# Global registry instance
_global_registry: Optional[MetricRegistry] = None


def get_metric_registry() -> MetricRegistry:
    """Get the global metric registry (singleton).
    
    Returns:
        MetricRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = MetricRegistry()
    return _global_registry
