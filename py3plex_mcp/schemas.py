"""Schema helpers for structured responses.

Provides utilities for creating consistent, JSON-serializable responses.
"""

import json
import time
from typing import Any, Dict, List, Optional

import py3plex


def make_meta(
    tool: str,
    ok: bool = True,
    truncated: bool = False,
    count: Optional[int] = None,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    """Create metadata dict.

    Args:
        tool: Tool name
        ok: Success status
        truncated: Whether results were truncated
        count: Total count before truncation
        limit: Truncation limit

    Returns:
        Metadata dict
    """
    meta = {
        "ok": ok,
        "tool": tool,
        "version": {
            "py3plex": py3plex.__version__,
            "mcp_server": "1.0.0",
        },
        "timestamp": time.time(),
    }

    if truncated:
        meta["truncated"] = True
        if count is not None:
            meta["total_count"] = count
        if limit is not None:
            meta["limit"] = limit

    return meta


def make_success_response(
    tool: str, data: Dict[str, Any], **meta_kwargs
) -> Dict[str, Any]:
    """Create success response.

    Args:
        tool: Tool name
        data: Response data
        **meta_kwargs: Additional meta fields

    Returns:
        Response dict with meta and data
    """
    response = {
        "meta": make_meta(tool, ok=True, **meta_kwargs),
    }
    response.update(data)
    return response


def truncate_list(items: list, limit: int) -> tuple:
    """Truncate list to limit.

    Args:
        items: List to truncate
        limit: Maximum length

    Returns:
        Tuple of (truncated_list, was_truncated, original_count)
    """
    original_count = len(items)
    truncated = original_count > limit
    result = items[:limit] if truncated else items
    return result, truncated, original_count


def serialize_json(obj: Any) -> Any:
    """Convert object to JSON-serializable form.

    Handles numpy types, sets, etc.

    Args:
        obj: Object to serialize

    Returns:
        JSON-serializable object
    """
    # Handle numpy types
    if hasattr(obj, "item"):  # numpy scalar
        return obj.item()
    elif hasattr(obj, "tolist"):  # numpy array
        return obj.tolist()

    # Handle sets
    if isinstance(obj, set):
        return list(obj)

    # Handle dicts recursively
    if isinstance(obj, dict):
        return {k: serialize_json(v) for k, v in obj.items()}

    # Handle lists recursively
    if isinstance(obj, (list, tuple)):
        return [serialize_json(item) for item in obj]

    # Default
    return obj


def format_stats(network: Any) -> Dict[str, Any]:
    """Format network statistics.

    Args:
        network: multi_layer_network instance

    Returns:
        Dict with node_count, edge_count, layer_count, layers
    """
    try:
        # Get layers first
        layers = network.get_layers()

        # Get nodes and edges - they return generators, so convert to list
        nodes = list(network.get_nodes())
        edges = list(network.get_edges())

        node_count = len(nodes)
        edge_count = len(edges)

        # Layer preview (first 10)
        layer_list = list(layers)
        layer_preview = layer_list[:10]
        if len(layer_list) > 10:
            layer_preview.append(f"... and {len(layer_list) - 10} more")

        return {
            "node_count": node_count,
            "edge_count": edge_count,
            "layer_count": len(layers),
            "layers_preview": layer_preview,
        }
    except Exception as e:
        return {
            "node_count": 0,
            "edge_count": 0,
            "layer_count": 0,
            "layers_preview": [],
            "error": f"Failed to compute stats: {str(e)}",
        }


def format_query_result(result: Any, limit: int = 200) -> Dict[str, Any]:
    """Format DSL query result with truncation.

    Args:
        result: QueryResult from DSL v2 or dict from legacy DSL
        limit: Maximum items to include

    Returns:
        Dict with result data and truncation info
    """
    # Handle QueryResult objects from DSL v2
    if hasattr(result, "to_dict"):
        # DSL v2 QueryResult object
        result_dict = result.to_dict()
        
        # DSL v2 uses 'target' field to determine nodes vs edges
        # Convert to legacy format for backward compatibility
        target = result_dict.get("target", "nodes")
        formatted_dict = {
            target: result_dict.get(target, []),
            "computed": result_dict.get("computed", {}),
            "meta": result_dict.get("meta", {}),
        }
        
        # Truncate nodes or edges
        truncated = False
        original_count = 0
        
        if target == "nodes":
            nodes, truncated, original_count = truncate_list(formatted_dict["nodes"], limit)
            formatted_dict["nodes"] = nodes
        elif target == "edges":
            edges, truncated, original_count = truncate_list(formatted_dict["edges"], limit)
            formatted_dict["edges"] = edges
        
        # Serialize to JSON-safe types
        formatted_dict = serialize_json(formatted_dict)
        
        return {
            "result": formatted_dict,
            "truncated": truncated,
            "total_count": original_count if truncated else len(result_dict.get(target, [])),
        }
    else:
        # Legacy DSL result (dict)
        result_dict = result

        # Truncate nodes or edges
        truncated = False
        original_count = 0

        if "nodes" in result_dict:
            nodes, truncated, original_count = truncate_list(result_dict["nodes"], limit)
            result_dict["nodes"] = nodes
        elif "edges" in result_dict:
            edges, truncated, original_count = truncate_list(result_dict["edges"], limit)
            result_dict["edges"] = edges

        # Serialize to JSON-safe types
        result_dict = serialize_json(result_dict)

        return {
            "result": result_dict,
            "truncated": truncated,
            "total_count": original_count if truncated else None,
        }
