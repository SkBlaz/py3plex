"""Provenance schema definitions for replayable queries.

This module defines the structured provenance record format that enables
deterministic replay of query results.

Schema Version: 1.0

The schema includes:
- Query AST and execution plan
- Network snapshot or fingerprint
- Randomness configuration (seeds)
- Environment information
- Size guardrails and warnings
"""

import platform
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union


# Schema version for provenance records
PROVENANCE_SCHEMA_VERSION = "1.0"

# Size thresholds for auto-capture policy
DEFAULT_NODE_THRESHOLD = 10000  # Max nodes for inline snapshot
DEFAULT_EDGE_THRESHOLD = 50000  # Max edges for inline snapshot
DEFAULT_SIZE_BYTES_THRESHOLD = 10 * 1024 * 1024  # 10MB


class ProvenanceMode(str, Enum):
    """Provenance tracking mode."""
    LOG = "log"  # Lightweight logging (current behavior)
    REPLAYABLE = "replayable"  # Full replayable provenance


class CaptureMethod(str, Enum):
    """Network capture method."""
    AUTO = "auto"  # Automatic selection based on size
    FINGERPRINT_ONLY = "fingerprint_only"  # Just counts and layers
    SNAPSHOT_GRAPH = "snapshot_graph"  # Full graph snapshot
    DELTA_FROM_DATASET = "delta_from_dataset"  # Delta from known dataset
    DELTA_FROM_BASE = "delta_from_base"  # Delta from base reference


@dataclass
class QueryInfo:
    """Query execution information."""
    engine: str  # "dsl_v2_executor", "dsl_legacy", "graph_ops", "pipeline"
    target: str  # "nodes", "edges", "communities"
    ast_hash: str  # Stable hash of query AST
    ast_summary: str  # Human-readable summary
    ast_serialized: Optional[Dict[str, Any]] = None  # Serialized AST for replay
    params: Dict[str, Any] = field(default_factory=dict)  # Parameter bindings
    execution_plan: Optional[List[Dict[str, Any]]] = None  # Execution stages


@dataclass
class RandomnessInfo:
    """Randomness configuration for replay."""
    used: bool = False  # Whether any randomness was used
    base_seed: Optional[int] = None  # Base seed for reproducibility
    derived_seeds: Dict[str, int] = field(default_factory=dict)  # Stage -> seed mapping
    seed_sequence_entropy: Optional[List[int]] = None  # SeedSequence entropy for advanced replay
    components: List[str] = field(default_factory=list)  # Components that used randomness


@dataclass
class NetworkCaptureInfo:
    """Network capture metadata."""
    capture_method: CaptureMethod
    node_count: int
    edge_count: int
    layer_count: int
    layers: List[str]
    base_reference: Optional[str] = None  # Dataset ID or file hash
    snapshot_data: Optional[Dict[str, Any]] = None  # Inline snapshot if small enough
    snapshot_external_path: Optional[str] = None  # Path to external snapshot file
    delta_ops: Optional[List[Dict[str, Any]]] = None  # Mutation operations log
    network_version: Optional[int] = None  # Network version counter if available
    encoding: Dict[str, str] = field(default_factory=lambda: {"format": "json", "compression": None})


@dataclass
class EnvironmentInfo:
    """Execution environment information."""
    py3plex_version: str
    python_version: str
    platform: str
    dependency_versions: Dict[str, str] = field(default_factory=dict)  # Key libraries


@dataclass
class ProvenanceSchema:
    """Complete provenance record for replayable queries.
    
    This is the main structure that captures all information needed to
    deterministically replay a query result.
    
    Attributes:
        schema_version: Schema version string (currently "1.0")
        mode: Provenance mode (log or replayable)
        timestamp_utc: ISO8601 timestamp of query execution
        query: Query execution information
        randomness: Randomness configuration
        network_capture: Network snapshot/fingerprint
        environment: Execution environment
        performance: Timing information per stage
        warnings: List of warnings or notes
        size_bytes_estimate: Estimated size of provenance payload
    """
    schema_version: str
    mode: ProvenanceMode
    timestamp_utc: str
    query: QueryInfo
    randomness: RandomnessInfo
    network_capture: NetworkCaptureInfo
    environment: EnvironmentInfo
    performance: Dict[str, float] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    size_bytes_estimate: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        # Convert enums to strings
        result["mode"] = self.mode.value
        result["network_capture"]["capture_method"] = self.network_capture.capture_method.value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProvenanceSchema":
        """Create from dictionary."""
        # Make a copy to avoid mutating input
        data = dict(data)
        
        # Convert string enums back
        if isinstance(data.get("mode"), str):
            data["mode"] = ProvenanceMode(data["mode"])
        
        # Handle network_capture - it might already be a NetworkCaptureInfo object
        if "network_capture" in data:
            nc = data["network_capture"]
            if isinstance(nc, dict):
                if isinstance(nc.get("capture_method"), str):
                    nc["capture_method"] = CaptureMethod(nc["capture_method"])
                data["network_capture"] = NetworkCaptureInfo(**nc)
            # else: already a NetworkCaptureInfo object, leave it as is
        
        # Reconstruct nested dataclasses only if they're dicts
        if "query" in data and isinstance(data["query"], dict):
            data["query"] = QueryInfo(**data["query"])
        # else: already a QueryInfo object
        
        if "randomness" in data and isinstance(data["randomness"], dict):
            data["randomness"] = RandomnessInfo(**data["randomness"])
        # else: already a RandomnessInfo object
        
        if "environment" in data and isinstance(data["environment"], dict):
            data["environment"] = EnvironmentInfo(**data["environment"])
        # else: already an EnvironmentInfo object
        
        return cls(**data)


def create_provenance_record(
    mode: ProvenanceMode = ProvenanceMode.LOG,
    engine: str = "dsl_v2_executor",
    target: str = "nodes",
    ast_hash: str = "",
    ast_summary: str = "",
    network_fingerprint: Optional[Dict[str, Any]] = None,
    **kwargs: Any
) -> ProvenanceSchema:
    """Create a provenance record with default values.
    
    Args:
        mode: Provenance mode (log or replayable)
        engine: Engine name
        target: Query target
        ast_hash: Query AST hash
        ast_summary: Query summary
        network_fingerprint: Network fingerprint dict
        **kwargs: Additional fields to override
        
    Returns:
        ProvenanceSchema instance
    """
    network_fingerprint = network_fingerprint or {}
    
    # Create query info
    query_info = QueryInfo(
        engine=engine,
        target=target,
        ast_hash=ast_hash,
        ast_summary=ast_summary,
        ast_serialized=kwargs.get("ast_serialized"),
        params=kwargs.get("params", {}),
        execution_plan=kwargs.get("execution_plan"),
    )
    
    # Create randomness info
    randomness_info = RandomnessInfo(
        used=kwargs.get("randomness_used", False),
        base_seed=kwargs.get("base_seed"),
        derived_seeds=kwargs.get("derived_seeds", {}),
        seed_sequence_entropy=kwargs.get("seed_sequence_entropy"),
        components=kwargs.get("randomness_components", []),
    )
    
    # Determine capture method
    capture_method = kwargs.get("capture_method", CaptureMethod.FINGERPRINT_ONLY)
    if mode == ProvenanceMode.REPLAYABLE and capture_method == CaptureMethod.FINGERPRINT_ONLY:
        # Upgrade to auto for replayable mode
        capture_method = CaptureMethod.AUTO
    
    # Create network capture info
    network_capture = NetworkCaptureInfo(
        capture_method=capture_method,
        node_count=network_fingerprint.get("node_count", 0),
        edge_count=network_fingerprint.get("edge_count", 0),
        layer_count=network_fingerprint.get("layer_count", 0),
        layers=network_fingerprint.get("layers", []),
        base_reference=kwargs.get("base_reference"),
        snapshot_data=kwargs.get("snapshot_data"),
        snapshot_external_path=kwargs.get("snapshot_external_path"),
        delta_ops=kwargs.get("delta_ops"),
        network_version=kwargs.get("network_version"),
        encoding=kwargs.get("encoding", {"format": "json", "compression": None}),
    )
    
    # Get environment info
    from py3plex.dsl.provenance import get_py3plex_version
    
    env_info = EnvironmentInfo(
        py3plex_version=get_py3plex_version(),
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        platform=platform.platform(),
        dependency_versions=_get_dependency_versions() if mode == ProvenanceMode.REPLAYABLE else {},
    )
    
    # Create provenance record
    record = ProvenanceSchema(
        schema_version=PROVENANCE_SCHEMA_VERSION,
        mode=mode,
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        query=query_info,
        randomness=randomness_info,
        network_capture=network_capture,
        environment=env_info,
        performance=kwargs.get("performance", {}),
        warnings=kwargs.get("warnings", []),
        size_bytes_estimate=0,  # Will be calculated after serialization
    )
    
    return record


def _get_dependency_versions() -> Dict[str, str]:
    """Get versions of key dependencies.
    
    Returns:
        Dictionary mapping package name to version
    """
    versions = {}
    key_packages = [
        "numpy",
        "scipy",
        "networkx",
        "pandas",
        "matplotlib",
    ]
    
    for package in key_packages:
        try:
            module = __import__(package)
            version = getattr(module, "__version__", "unknown")
            versions[package] = version
        except ImportError:
            versions[package] = "not installed"
    
    return versions


def estimate_provenance_size(prov: ProvenanceSchema) -> int:
    """Estimate the size of a provenance record in bytes.
    
    Args:
        prov: Provenance schema instance
        
    Returns:
        Estimated size in bytes
    """
    import json
    
    # Convert to dict and serialize to JSON to estimate size
    try:
        json_str = json.dumps(prov.to_dict(), default=str)
        return len(json_str.encode('utf-8'))
    except Exception:
        # Fallback: rough estimate
        return 10000  # 10KB baseline


def should_capture_inline(
    node_count: int,
    edge_count: int,
    node_threshold: int = DEFAULT_NODE_THRESHOLD,
    edge_threshold: int = DEFAULT_EDGE_THRESHOLD
) -> bool:
    """Determine if network should be captured inline.
    
    Args:
        node_count: Number of nodes
        edge_count: Number of edges
        node_threshold: Max nodes for inline capture
        edge_threshold: Max edges for inline capture
        
    Returns:
        True if network should be captured inline
    """
    return node_count <= node_threshold and edge_count <= edge_threshold
