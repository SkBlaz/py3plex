"""Bundle export/import for provenance and results.

This module handles packaging query results with provenance into
portable bundles that can be saved and loaded.
"""

import gzip
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .schema import ProvenanceSchema
from .capture import NetworkCapture, compress_snapshot, decompress_snapshot


class BundleError(Exception):
    """Exception raised during bundle operations."""
    pass


def export_bundle(
    result: Any,
    path: Union[str, Path],
    compress: bool = True,
    include_results: bool = True
) -> None:
    """Export query result with provenance as a bundle.
    
    Args:
        result: QueryResult object
        path: Output path (file or directory)
        compress: Whether to compress the bundle
        include_results: Whether to include query results in bundle
        
    Raises:
        BundleError: If export fails
    """
    path = Path(path)
    
    # Get provenance from result
    if not hasattr(result, 'meta') or 'provenance' not in result.meta:
        raise BundleError("Result does not have provenance metadata")
    
    prov_dict = result.meta['provenance']
    
    # Build bundle data
    bundle = {
        "version": "1.0",
        "provenance": prov_dict,
    }
    
    # Include results if requested
    if include_results:
        bundle["result"] = {
            "target": result.target,
            "items": _serialize_items(result.items),
            "attributes": _serialize_attributes(result.attributes),
            "count": result.count,
        }
    
    # Serialize to JSON
    try:
        json_str = json.dumps(bundle, indent=2, default=str)
        json_bytes = json_str.encode('utf-8')
    except Exception as e:
        raise BundleError(f"Failed to serialize bundle: {e}")
    
    # Write to file
    try:
        if compress:
            if not str(path).endswith('.gz'):
                path = Path(str(path) + '.json.gz')
            compressed = gzip.compress(json_bytes)
            path.write_bytes(compressed)
        else:
            if not str(path).endswith('.json'):
                path = Path(str(path) + '.json')
            path.write_text(json_str, encoding='utf-8')
    except Exception as e:
        raise BundleError(f"Failed to write bundle to {path}: {e}")


def load_bundle(
    path: Union[str, Path],
    validate: bool = True
) -> Dict[str, Any]:
    """Load bundle from file.
    
    Args:
        path: Bundle file path
        validate: Whether to validate provenance schema
        
    Returns:
        Bundle dictionary with provenance and optionally results
        
    Raises:
        BundleError: If loading fails
    """
    path = Path(path)
    
    if not path.exists():
        raise BundleError(f"Bundle file not found: {path}")
    
    # Read file
    try:
        if str(path).endswith('.gz'):
            compressed = path.read_bytes()
            json_bytes = gzip.decompress(compressed)
            json_str = json_bytes.decode('utf-8')
        else:
            json_str = path.read_text(encoding='utf-8')
        
        bundle = json.loads(json_str)
    except Exception as e:
        raise BundleError(f"Failed to read bundle from {path}: {e}")
    
    # Validate structure
    if "provenance" not in bundle:
        raise BundleError("Bundle does not contain provenance data")
    
    # Validate provenance schema if requested
    if validate:
        try:
            prov_dict = bundle["provenance"]
            # Check schema version
            schema_version = prov_dict.get("schema_version", "unknown")
            if schema_version != "1.0":
                import warnings
                warnings.warn(
                    f"Bundle has schema version {schema_version}, expected 1.0. "
                    "Loading may fail or produce unexpected results.",
                    UserWarning
                )
            
            # Try to construct ProvenanceSchema
            ProvenanceSchema.from_dict(prov_dict)
        except Exception as e:
            raise BundleError(f"Invalid provenance schema in bundle: {e}")
    
    return bundle


def _serialize_items(items: Any) -> Any:
    """Serialize query result items.
    
    Args:
        items: List of nodes/edges
        
    Returns:
        Serializable representation
    """
    # Convert tuples to lists for JSON serialization
    if isinstance(items, list):
        return [_serialize_item(item) for item in items]
    return items


def _serialize_item(item: Any) -> Any:
    """Serialize a single item.
    
    Args:
        item: Node or edge tuple
        
    Returns:
        Serializable representation
    """
    if isinstance(item, tuple):
        return list(item)
    return item


def _serialize_attributes(attributes: Dict[str, Any]) -> Dict[str, Any]:
    """Serialize query result attributes.
    
    Args:
        attributes: Attribute dictionary
        
    Returns:
        Serializable representation
    """
    serialized = {}
    
    for key, value in attributes.items():
        if isinstance(value, dict):
            # Convert tuple keys to strings
            serialized[key] = {str(k): v for k, v in value.items()}
        else:
            serialized[key] = value
    
    return serialized


def create_replay_bundle(
    result: Any,
    path: Union[str, Path],
    compress: bool = True
) -> None:
    """Create a bundle optimized for replay.
    
    This is a convenience wrapper around export_bundle that ensures
    the result has replayable provenance.
    
    Args:
        result: QueryResult with replayable provenance
        path: Output path
        compress: Whether to compress bundle
        
    Raises:
        BundleError: If result is not replayable
    """
    # Check if result is replayable
    if not hasattr(result, 'is_replayable') or not result.is_replayable:
        raise BundleError(
            "Result does not have replayable provenance. "
            "Use .provenance(mode='replayable') when creating the query."
        )
    
    export_bundle(result, path, compress=compress, include_results=True)
