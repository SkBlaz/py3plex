"""Provenance tracking and replay for py3plex queries.

This module provides tools for tracking query provenance and enabling
deterministic replay of query results.

Key Features:
- Versioned provenance schema
- Network snapshot/delta capture
- Deterministic randomness tracking
- Query replay API
- Bundle export/import

Main Classes:
    ProvenanceSchema: Structured provenance record
    NetworkCapture: Network snapshot/delta serialization
    ReplayContext: Context for replaying queries

Main Functions:
    export_bundle: Export query result with provenance
    load_bundle: Load and optionally replay a bundled result
    replay_from_bundle: Convenience function to load and replay
"""

from .schema import (
    ProvenanceSchema,
    ProvenanceMode,
    CaptureMethod,
    create_provenance_record,
)
from .capture import (
    NetworkCapture,
    capture_network,
    restore_network,
)
from .replay import (
    ReplayContext,
    replay_query,
    ReplayError,
)
from .bundle import (
    export_bundle,
    load_bundle,
    BundleError,
)

__all__ = [
    # Schema
    "ProvenanceSchema",
    "ProvenanceMode",
    "CaptureMethod",
    "create_provenance_record",
    # Capture
    "NetworkCapture",
    "capture_network",
    "restore_network",
    # Replay
    "ReplayContext",
    "replay_query",
    "ReplayError",
    # Bundle I/O
    "export_bundle",
    "load_bundle",
    "BundleError",
    # Convenience
    "replay_from_bundle",
]


def replay_from_bundle(path, strict=True):
    """Load a bundle and replay the query.
    
    Convenience function that combines load_bundle and replay_query.
    
    Args:
        path: Bundle file path
        strict: If True, enforce strict version compatibility
        
    Returns:
        QueryResult from replayed query
        
    Raises:
        BundleError: If bundle cannot be loaded
        ReplayError: If replay fails
    """
    bundle = load_bundle(path)
    prov_dict = bundle["provenance"]
    prov_schema = ProvenanceSchema.from_dict(prov_dict)
    return replay_query(prov_schema, strict=strict)
