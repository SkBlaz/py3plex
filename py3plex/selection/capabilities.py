"""Capabilities scanner for AutoCommunity.

Detects available community detection algorithms, metrics, and UQ support.
"""

import importlib
import inspect
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class AlgorithmInfo:
    """Information about a detected community detection algorithm."""
    
    name: str
    callable: Callable
    module_path: str
    supports_multilayer: bool = False
    params: List[str] = field(default_factory=list)
    accepts_seed: bool = False
    seed_param_name: Optional[str] = None
    notes: str = ""


@dataclass
class MetricInfo:
    """Information about a detected quality metric."""
    
    name: str
    callable: Callable
    module_path: str
    direction: str  # "max" or "min"
    bucket: str  # "objective", "structure", "sanity", "stability", "runtime", "predictive"
    requires_uq: bool = False
    enabled_by_default: bool = True


@dataclass
class CapabilitiesReport:
    """Report of detected capabilities."""
    
    algorithms_found: Dict[str, AlgorithmInfo]
    metrics_found: Dict[str, MetricInfo]
    uq_available: bool
    uq_invocation_info: Optional[Dict[str, Any]] = None
    dsl_operator_available: bool = False
    dsl_operator_info: Optional[Dict[str, Any]] = None


class CapabilitiesScanner:
    """Scanner to detect available community detection capabilities."""
    
    # Known algorithm candidates to search for
    KNOWN_ALGORITHMS = [
        "leiden_multilayer",
        "multilayer_leiden",
        "louvain_multilayer",
        "multilayer_louvain",
        "infomap",
        "label_propagation",
        "spectral_clustering",
        "sbm_fit",
        "fit_multilayer_sbm",
    ]
    
    # Modules to search for algorithms
    ALGORITHM_MODULES = [
        "py3plex.algorithms.community_detection",
        "py3plex.algorithms.community_detection.leiden_multilayer",
        "py3plex.algorithms.community_detection.leiden_uq",
        "py3plex.algorithms.community_detection.multilayer_modularity",
        "py3plex.algorithms.community_detection.sbm_wrapper",
        "py3plex.algorithms.sbm",
    ]
    
    # Modules to search for metrics
    METRIC_MODULES = [
        "py3plex.algorithms.community_detection.community_measures",
        "py3plex.uncertainty.partition_metrics",
    ]
    
    def __init__(self):
        self.algorithms: Dict[str, AlgorithmInfo] = {}
        self.metrics: Dict[str, MetricInfo] = {}
        self.uq_available: bool = False
        self.uq_info: Optional[Dict[str, Any]] = None
    
    def scan(self) -> CapabilitiesReport:
        """Perform comprehensive scan of capabilities.
        
        Returns:
            CapabilitiesReport with detected algorithms, metrics, and UQ support
        """
        self._scan_algorithms()
        self._scan_metrics()
        self._scan_uq()
        dsl_available = self._scan_dsl_operator()
        
        return CapabilitiesReport(
            algorithms_found=self.algorithms,
            metrics_found=self.metrics,
            uq_available=self.uq_available,
            uq_invocation_info=self.uq_info,
            dsl_operator_available=dsl_available,
        )
    
    def _scan_algorithms(self):
        """Scan for available community detection algorithms."""
        for module_name in self.ALGORITHM_MODULES:
            try:
                module = importlib.import_module(module_name)
                self._inspect_module_for_algorithms(module, module_name)
            except ImportError as e:
                logger.debug(f"Could not import {module_name}: {e}")
                continue
    
    def _inspect_module_for_algorithms(self, module: Any, module_path: str):
        """Inspect a module for algorithm functions."""
        for name, obj in inspect.getmembers(module):
            if not callable(obj):
                continue
            
            # Check if it's a known algorithm or looks like one
            is_candidate = (
                name in self.KNOWN_ALGORITHMS or
                any(keyword in name.lower() for keyword in ["leiden", "louvain", "community", "partition"])
            )
            
            if not is_candidate:
                continue
            
            # Get signature
            try:
                sig = inspect.signature(obj)
            except (ValueError, TypeError):
                continue
            
            # Check parameters
            params = list(sig.parameters.keys())
            
            # Skip if doesn't look like a community detection function
            if "network" not in params and "net" not in params and "G" not in params:
                continue
            
            # Detect seed parameter
            seed_param = None
            accepts_seed = False
            for p in ["random_state", "seed", "rng"]:
                if p in params:
                    seed_param = p
                    accepts_seed = True
                    break
            
            # Detect if multilayer-capable
            supports_multilayer = (
                "multilayer" in name.lower() or
                "multilayer" in module_path.lower() or
                any(p in params for p in ["gamma", "omega", "coupling"])
            )
            
            # Store algorithm info
            algo_info = AlgorithmInfo(
                name=name,
                callable=obj,
                module_path=module_path,
                supports_multilayer=supports_multilayer,
                params=params,
                accepts_seed=accepts_seed,
                seed_param_name=seed_param,
            )
            
            self.algorithms[name] = algo_info
            logger.debug(f"Detected algorithm: {name} (multilayer={supports_multilayer})")
    
    def _scan_metrics(self):
        """Scan for available quality metrics."""
        # Try to import community measures
        try:
            from py3plex.algorithms.community_detection import community_measures
            
            # Modularity
            if hasattr(community_measures, "modularity"):
                self.metrics["modularity"] = MetricInfo(
                    name="modularity",
                    callable=community_measures.modularity,
                    module_path="py3plex.algorithms.community_detection.community_measures",
                    direction="max",
                    bucket="objective",
                    requires_uq=False,
                )
            
            # Size distribution
            if hasattr(community_measures, "size_distribution"):
                self.metrics["size_distribution"] = MetricInfo(
                    name="size_distribution",
                    callable=community_measures.size_distribution,
                    module_path="py3plex.algorithms.community_detection.community_measures",
                    direction="max",
                    bucket="sanity",
                    requires_uq=False,
                )
            
        except ImportError:
            logger.debug("Could not import community_measures")
        
        # Try to import partition metrics (for UQ stability)
        try:
            from py3plex.uncertainty import partition_metrics
            
            if hasattr(partition_metrics, "variation_of_information"):
                self.metrics["variation_of_information"] = MetricInfo(
                    name="variation_of_information",
                    callable=partition_metrics.variation_of_information,
                    module_path="py3plex.uncertainty.partition_metrics",
                    direction="min",
                    bucket="stability",
                    requires_uq=True,
                )
            
            if hasattr(partition_metrics, "normalized_mutual_information"):
                self.metrics["normalized_mutual_information"] = MetricInfo(
                    name="normalized_mutual_information",
                    callable=partition_metrics.normalized_mutual_information,
                    module_path="py3plex.uncertainty.partition_metrics",
                    direction="max",
                    bucket="stability",
                    requires_uq=True,
                )
        
        except ImportError:
            logger.debug("Could not import partition_metrics")
    
    def _scan_uq(self):
        """Scan for PartitionUQ support."""
        try:
            from py3plex.uncertainty import PartitionUQ
            self.uq_available = True
            self.uq_info = {
                "class": PartitionUQ,
                "module_path": "py3plex.uncertainty.partition_uq",
                "from_samples_method": "from_samples",
            }
            logger.debug("PartitionUQ detected and available")
        except ImportError:
            self.uq_available = False
            logger.debug("PartitionUQ not available")
    
    def _scan_dsl_operator(self) -> bool:
        """Check if DSL community operator is available."""
        try:
            from py3plex.dsl import Q
            # Check if Q has communities method
            has_communities = hasattr(Q, "communities")
            if has_communities:
                logger.debug("DSL community operator detected")
            return has_communities
        except ImportError:
            logger.debug("DSL not available")
            return False


def scan_capabilities() -> CapabilitiesReport:
    """Convenience function to scan capabilities.
    
    Returns:
        CapabilitiesReport with detected algorithms, metrics, and UQ support
    """
    scanner = CapabilitiesScanner()
    return scanner.scan()


def print_report(report: Optional[CapabilitiesReport] = None):
    """Print a human-readable capabilities report.
    
    This is a developer-facing helper for debugging.
    
    Args:
        report: Optional pre-computed report. If None, scans now.
    """
    if report is None:
        report = scan_capabilities()
    
    print("=" * 60)
    print("AutoCommunity Capabilities Report")
    print("=" * 60)
    
    print(f"\nAlgorithms Found: {len(report.algorithms_found)}")
    for name, info in sorted(report.algorithms_found.items()):
        seed_info = f"seed={info.seed_param_name}" if info.accepts_seed else "no-seed"
        ml_info = "multilayer" if info.supports_multilayer else "single-layer"
        print(f"  - {name:30s} [{ml_info:12s}] [{seed_info}]")
    
    print(f"\nMetrics Found: {len(report.metrics_found)}")
    for bucket in ["objective", "structure", "sanity", "stability", "runtime", "predictive"]:
        bucket_metrics = [m for m in report.metrics_found.values() if m.bucket == bucket]
        if bucket_metrics:
            print(f"  [{bucket}]")
            for m in bucket_metrics:
                uq_info = " (requires UQ)" if m.requires_uq else ""
                print(f"    - {m.name} ({m.direction}){uq_info}")
    
    print(f"\nUQ Available: {report.uq_available}")
    if report.uq_available and report.uq_invocation_info:
        print(f"  Module: {report.uq_invocation_info.get('module_path', 'N/A')}")
    
    print(f"\nDSL Operator Available: {report.dsl_operator_available}")
    print("=" * 60)
