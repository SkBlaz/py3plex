"""MCP Server implementation using FastMCP.

Provides stdio-based MCP server exposing py3plex tools and resources.

Requires Python 3.10 or higher due to MCP SDK dependency.
"""

import json
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

# Check Python version first
if sys.version_info < (3, 10):
    print(
        "ERROR: MCP server requires Python 3.10 or higher.\n"
        f"Current version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}\n"
        "Please upgrade Python or use the base py3plex package without MCP.",
        file=sys.stderr,
    )
    sys.exit(1)

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp import types
except ImportError:
    print(
        "ERROR: MCP SDK not installed. Install with: pip install py3plex[mcp]",
        file=sys.stderr,
    )
    sys.exit(1)

from py3plex.core import multinet
from py3plex.dsl_legacy import execute_query
from py3plex.dsl import Q, L, Param, QueryResult  # DSL v2 support
from py3plex_mcp.errors import (
    MCPError,
    NetworkNotFoundError,
    PathAccessError,
    QueryParseError,
    UnsupportedAlgorithmError,
    UnsupportedFormatError,
    make_error_response,
)
from py3plex_mcp.registry import get_registry
from py3plex_mcp.safe_paths import (
    DEFAULT_OUTPUT_DIR,
    make_unique_filename,
    resolve_out_dir,
    resolve_read_path,
)
from py3plex_mcp.schemas import (
    format_query_result,
    format_stats,
    make_meta,
    make_success_response,
    serialize_json,
)

# Supported formats
SUPPORTED_FORMATS = [
    "multiedgelist",
    "edgelist",
    "gml",
    "graphml",
    "pajek",
]

# Supported community detection algorithms
SUPPORTED_ALGORITHMS = [
    "louvain",
    "leiden",
    "label_propagation",
]


# Create server
app = Server("py3plex-mcp")


# ============================================================================
# TOOLS
# ============================================================================


@app.call_tool()
async def py3plex_load_network(
    path: str,
    input_type: str = "multiedgelist",
    directed: bool = False,
    layer_separator: Optional[str] = None,
) -> List[types.TextContent]:
    """Load a network from file and store in registry.

    Args:
        path: File or directory path to load
        input_type: Input format (default: multiedgelist)
        directed: Whether network is directed (default: False)
        layer_separator: Layer separator character for multi-edgelist format

    Returns:
        Network ID and statistics
    """
    try:
        # Validate format
        if input_type not in SUPPORTED_FORMATS:
            raise UnsupportedFormatError(input_type, SUPPORTED_FORMATS)

        # Validate path
        resolved_path = resolve_read_path(path)

        # Create network
        net = multinet.multi_layer_network(directed=directed)

        # Load network
        load_kwargs = {"input_type": input_type}
        if layer_separator:
            load_kwargs["layer_delimiter"] = layer_separator

        net.load_network(str(resolved_path), **load_kwargs)

        # Store in registry
        registry = get_registry()
        net_id = registry.add(
            network=net,
            source=str(resolved_path),
            metadata={
                "input_type": input_type,
                "directed": directed,
                "layer_separator": layer_separator,
            },
        )

        # Get stats
        stats = format_stats(net)

        response = make_success_response(
            tool="py3plex.load_network",
            data={
                "net_id": net_id,
                "source": str(resolved_path),
                "stats": stats,
            },
        )

        return [types.TextContent(type="text", text=json.dumps(response, indent=2))]

    except Exception as e:
        error_response = make_error_response(e)
        error_response["meta"] = make_meta("py3plex.load_network", ok=False)
        return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]


@app.call_tool()
async def py3plex_stats(net_id: str) -> List[types.TextContent]:
    """Get network statistics.

    Args:
        net_id: Network handle ID

    Returns:
        Network statistics
    """
    try:
        registry = get_registry()
        net = registry.get(net_id)

        stats = format_stats(net)
        info = registry.get_info(net_id)

        response = make_success_response(
            tool="py3plex.stats",
            data={
                "net_id": net_id,
                "source": info["source"],
                "stats": stats,
            },
        )

        return [types.TextContent(type="text", text=json.dumps(response, indent=2))]

    except Exception as e:
        error_response = make_error_response(e)
        error_response["meta"] = make_meta("py3plex.stats", ok=False)
        return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]


@app.call_tool()
async def py3plex_run_query(
    net_id: str, query: str, limit: int = 200, use_v2: bool = False
) -> List[types.TextContent]:
    """Execute DSL query on network.

    Supports both legacy (string-based) and DSL v2 (builder-based) queries.

    Args:
        net_id: Network handle ID
        query: DSL query string (legacy syntax) or DSL v2 builder expression
        limit: Maximum items to return (default: 200)
        use_v2: If True, interpret query as DSL v2 Python expression (default: False)

    Returns:
        Query results with truncation info

    Examples:
        Legacy: 'SELECT nodes WHERE degree > 5 COMPUTE pagerank'
        DSL v2: 'Q.nodes().where(degree__gt=5).compute("pagerank").limit(20)'
    """
    try:
        registry = get_registry()
        net = registry.get(net_id)

        # Execute query based on DSL version
        try:
            if use_v2:
                # DSL v2: Evaluate Python expression to build query
                # Security: We only expose Q, L, Param from dsl module
                safe_globals = {
                    "Q": Q,
                    "L": L,
                    "Param": Param,
                    "__builtins__": {},
                }
                # Evaluate the query expression
                query_builder = eval(query, safe_globals, {})
                
                # Execute the query
                result = query_builder.execute(net, progress=False)
            else:
                # Legacy DSL: String-based query
                result = execute_query(net, query)
        except Exception as query_error:
            raise QueryParseError(query, str(query_error))

        # Format and truncate
        formatted = format_query_result(result, limit=limit)

        response = make_success_response(
            tool="py3plex.run_query",
            data={
                "net_id": net_id,
                "query": query,
                "dsl_version": "v2" if use_v2 else "legacy",
                **formatted,
            },
            truncated=formatted["truncated"],
            count=formatted["total_count"],
            limit=limit if formatted["truncated"] else None,
        )

        return [types.TextContent(type="text", text=json.dumps(response, indent=2))]

    except Exception as e:
        error_response = make_error_response(e)
        error_response["meta"] = make_meta("py3plex.run_query", ok=False)
        return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]


@app.call_tool()
async def py3plex_community_detect(
    net_id: str,
    algorithm: str = "louvain",
    layer_mode: str = "aggregate",
    params: Optional[Dict[str, Any]] = None,
) -> List[types.TextContent]:
    """Detect communities in network.

    Args:
        net_id: Network handle ID
        algorithm: Algorithm name (louvain, leiden, label_propagation)
        layer_mode: How to handle layers (aggregate, per_layer, multiplex)
        params: Optional algorithm parameters

    Returns:
        Community assignments and quality metrics
    """
    try:
        registry = get_registry()
        net = registry.get(net_id)

        # Validate algorithm
        if algorithm not in SUPPORTED_ALGORITHMS:
            raise UnsupportedAlgorithmError(algorithm, SUPPORTED_ALGORITHMS)

        start_time = time.time()

        # Import algorithm
        if algorithm == "louvain":
            from py3plex.algorithms.community_detection import (
                community_louvain as louvain_module,
            )

            algo_func = louvain_module.louvain
        elif algorithm == "leiden":
            try:
                from py3plex.algorithms.community_detection import leiden_wrapper

                algo_func = leiden_wrapper.leiden
            except ImportError:
                raise MCPError(
                    "Leiden algorithm not available",
                    hint="Install with: pip install leidenalg",
                )
        else:  # label_propagation
            from py3plex.algorithms.community_detection import label_propagation

            algo_func = label_propagation.label_propagation

        # Run algorithm
        algo_params = params or {}
        if "seed" not in algo_params:
            algo_params["seed"] = 42  # Default seed for reproducibility

        communities = algo_func(net, **algo_params)

        runtime_ms = (time.time() - start_time) * 1000

        # Format communities
        community_dict = serialize_json(communities)

        # Compute basic quality metrics
        num_communities = len(set(community_dict.values()))
        community_sizes = {}
        for node, comm in community_dict.items():
            community_sizes[comm] = community_sizes.get(comm, 0) + 1

        response = make_success_response(
            tool="py3plex.community_detect",
            data={
                "net_id": net_id,
                "algorithm": algorithm,
                "layer_mode": layer_mode,
                "communities": community_dict,
                "quality": {
                    "num_communities": num_communities,
                    "community_sizes": serialize_json(community_sizes),
                },
                "runtime_ms": runtime_ms,
            },
        )

        return [types.TextContent(type="text", text=json.dumps(response, indent=2))]

    except Exception as e:
        error_response = make_error_response(e)
        error_response["meta"] = make_meta("py3plex.community_detect", ok=False)
        return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]


@app.call_tool()
async def py3plex_export(
    data: Dict[str, Any],
    out_dir: Optional[str] = None,
    format: str = "json",
    filename: Optional[str] = None,
) -> List[types.TextContent]:
    """Export data to file.

    Args:
        data: Data to export (dict)
        out_dir: Output directory (default: ~/.py3plex_mcp/out)
        format: Output format (json or csv)
        filename: Optional filename (auto-generated if not provided)

    Returns:
        Written file paths
    """
    try:
        # Resolve output directory
        target_dir = resolve_out_dir(out_dir)

        # Generate filename
        if filename is None:
            timestamp = int(time.time())
            base_name = f"export_{timestamp}"
        else:
            base_name = Path(filename).stem

        extension = "json" if format == "json" else "csv"
        output_path = make_unique_filename(target_dir, base_name, extension)

        # Write file
        if format == "json":
            with open(output_path, "w") as f:
                json.dump(serialize_json(data), f, indent=2)
        elif format == "csv":
            import csv

            # Try to extract tabular data
            if "result" in data and "nodes" in data["result"]:
                items = data["result"]["nodes"]
            elif "result" in data and "edges" in data["result"]:
                items = data["result"]["edges"]
            elif isinstance(data, list):
                items = data
            else:
                # Fallback to JSON for non-tabular data
                with open(output_path, "w") as f:
                    json.dump(serialize_json(data), f, indent=2)
                items = None

            if items:
                with open(output_path, "w", newline="") as f:
                    if items:
                        writer = csv.DictWriter(f, fieldnames=items[0].keys())
                        writer.writeheader()
                        writer.writerows(serialize_json(items))
        else:
            raise MCPError(
                f"Unsupported format: {format}",
                hint="Supported formats: json, csv",
            )

        response = make_success_response(
            tool="py3plex.export",
            data={
                "written_paths": [str(output_path)],
                "format": format,
                "size_bytes": output_path.stat().st_size,
            },
        )

        return [types.TextContent(type="text", text=json.dumps(response, indent=2))]

    except Exception as e:
        error_response = make_error_response(e)
        error_response["meta"] = make_meta("py3plex.export", ok=False)
        return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]


@app.call_tool()
async def py3plex_close(net_id: str) -> List[types.TextContent]:
    """Close network handle and free memory.

    Args:
        net_id: Network handle ID

    Returns:
        Confirmation
    """
    try:
        registry = get_registry()
        registry.remove(net_id)

        response = make_success_response(
            tool="py3plex.close",
            data={
                "net_id": net_id,
                "message": f"Network '{net_id}' closed successfully",
            },
        )

        return [types.TextContent(type="text", text=json.dumps(response, indent=2))]

    except Exception as e:
        error_response = make_error_response(e)
        error_response["meta"] = make_meta("py3plex.close", ok=False)
        return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]


@app.call_tool()
async def py3plex_list_handles() -> List[types.TextContent]:
    """List all network handles.

    Returns:
        List of network handles with metadata
    """
    try:
        registry = get_registry()
        handles = registry.list_all()

        response = make_success_response(
            tool="py3plex.list_handles",
            data={
                "handles": serialize_json(handles),
                "count": len(handles),
            },
        )

        return [types.TextContent(type="text", text=json.dumps(response, indent=2))]

    except Exception as e:
        error_response = make_error_response(e)
        error_response["meta"] = make_meta("py3plex.list_handles", ok=False)
        return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]


# ============================================================================
# RESOURCES
# ============================================================================


@app.list_resources()
async def list_resources() -> List[types.Resource]:
    """List available resources."""
    return [
        types.Resource(
            uri="py3plex://agents",
            name="py3plex Agent Documentation",
            mimeType="text/markdown",
            description="Complete AI agent documentation for py3plex",
        ),
        types.Resource(
            uri="py3plex://help/dsl",
            name="DSL Reference",
            mimeType="text/markdown",
            description="py3plex DSL query language reference",
        ),
        types.Resource(
            uri="py3plex://help/tools",
            name="MCP Tools Reference",
            mimeType="application/json",
            description="Available MCP tools with schemas and examples",
        ),
    ]


@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read resource by URI."""
    if uri == "py3plex://agents":
        # Read AGENTS.md from repository root
        agents_path = Path(__file__).parent.parent / "AGENTS.md"
        if agents_path.exists():
            return agents_path.read_text()
        else:
            return "# py3plex Agent Documentation\n\n(AGENTS.md not found)"

    elif uri == "py3plex://help/dsl":
        return """# py3plex DSL Reference

## DSL v2 (Builder API) - Recommended

DSL v2 provides a Pythonic, chainable query builder with type hints and IDE support.

### Basic Query Construction

```python
from py3plex.dsl import Q, L, Param

# Query all nodes
Q.nodes().execute(network)

# Query edges
Q.edges().execute(network)
```

### Layer Selection

```python
# Single layer
Q.nodes().where(layer="social").execute(network)

# Multiple layers with algebra
Q.nodes().from_layers(L["social"] + L["work"]).execute(network)  # Union
Q.nodes().from_layers(L["social"] - L["work"]).execute(network)  # Difference
Q.nodes().from_layers(L["social"] & L["work"]).execute(network)  # Intersection
```

### WHERE Conditions (Django-style)

```python
# Exact match
Q.nodes().where(layer="social").execute(network)

# Comparisons
Q.nodes().where(degree__gt=5).execute(network)       # degree > 5
Q.nodes().where(degree__gte=5).execute(network)      # degree >= 5
Q.nodes().where(degree__lt=10).execute(network)      # degree < 10
Q.nodes().where(degree__lte=10).execute(network)     # degree <= 10
Q.nodes().where(degree__ne=0).execute(network)       # degree != 0

# Range
Q.nodes().where(degree__between=(5, 10)).execute(network)

# Containment
Q.nodes().where(layer__in=["social", "work"]).execute(network)
Q.nodes().where(layer__nin=["hobby"]).execute(network)

# Intralayer/interlayer edges
Q.edges().where(intralayer=True).execute(network)
Q.edges().where(interlayer=True).execute(network)

# Combine conditions
Q.nodes().where(layer="social", degree__gt=5).execute(network)
```

### COMPUTE Metrics

```python
# Single metric
Q.nodes().compute("degree").execute(network)

# Multiple metrics
Q.nodes().compute("degree", "pagerank", "betweenness_centrality").execute(network)

# With alias
Q.nodes().compute("betweenness_centrality", alias="bc").execute(network)

# Available metrics:
# - degree, in_degree, out_degree
# - betweenness_centrality, closeness_centrality
# - pagerank, eigenvector_centrality
# - clustering, triangles
# - katz_centrality, load_centrality
```

### ORDER BY and LIMIT

```python
# Order by computed metric
Q.nodes().compute("degree").order_by("degree", desc=True).limit(10).execute(network)

# Multiple sort keys
Q.nodes().compute("degree", "pagerank").order_by("degree", "pagerank").execute(network)
```

### Parameterized Queries

```python
# Define parameter
k = Param("k", default=5)

# Use in query
query = Q.nodes().where(degree__gt=k).compute("pagerank").limit(20)

# Execute with different values
result1 = query.execute(network, k=3)
result2 = query.execute(network, k=10)
```

### Grouping (per_layer, per_layer_pair)

```python
# Group nodes by layer
Q.nodes().per_layer().compute("degree").execute(network)

# Group edges by layer pair
Q.edges().per_layer_pair().where(interlayer=True).execute(network)
```

### Exporting Results

```python
result = Q.nodes().compute("degree", "pagerank").execute(network)

# To pandas DataFrame
df = result.to_pandas()

# To dict
data = result.to_dict()

# To NetworkX graph
G = result.to_networkx(network)

# To JSON
result.to_json("output.json")
```

### Query Execution Options

```python
# Disable progress logging
Q.nodes().execute(network, progress=False)

# Use specific parameters
Q.nodes().where(degree__gt=k).execute(network, k=10)
```

### Examples

```python
# Find influential nodes in social layer
Q.nodes().where(layer="social", degree__gt=5).compute("betweenness_centrality", alias="bc").order_by("bc", desc=True).limit(10).execute(network)

# Find interlayer edges
Q.edges().where(interlayer=True).execute(network)

# Compare layers by average degree
Q.nodes().per_layer().compute("degree").execute(network).group_summary()

# Complex filtering
Q.nodes().from_layers(L["social"] + L["work"]).where(degree__between=(3, 10)).compute("pagerank", "clustering").order_by("pagerank", desc=True).limit(20).execute(network)
```

---

## Legacy DSL (String-Based)

The legacy DSL uses SQL-like syntax for querying networks. **Use DSL v2 for new queries.**

### Basic Syntax

```
SELECT <target> [FROM layer="<layer>"] [WHERE <conditions>] [COMPUTE <measures>] [ORDER BY <key>] [LIMIT <n>]
```

### Targets
- `nodes` - Query nodes
- `edges` - Query edges

### Conditions
- `layer="<name>"` - Filter by layer
- `degree > <n>` - Filter by degree
- `<metric> > <value>` - Filter by computed metric

### Measures
Compute metrics on selected items:
- `degree` - Node degree
- `betweenness_centrality` - Betweenness centrality
- `pagerank` - PageRank
- `closeness_centrality` - Closeness centrality
- `clustering` - Clustering coefficient

### Examples

```sql
-- All nodes in social layer
SELECT nodes FROM layer="social"

-- High-degree nodes
SELECT nodes WHERE degree > 5

-- Compute centrality
SELECT nodes COMPUTE betweenness_centrality

-- Top 10 by degree
SELECT nodes COMPUTE degree ORDER BY degree LIMIT 10

-- Filter on layer and degree
SELECT nodes FROM layer="social" WHERE degree > 3 COMPUTE pagerank
```

### Tips
- Always use double quotes for string values
- Metrics are auto-computed if referenced in WHERE but not in COMPUTE
- Use LIMIT to control result size
- ORDER BY supports ascending (default) or descending with `-` prefix
"""

    elif uri == "py3plex://help/tools":
        tools_doc = {
            "tools": [
                {
                    "name": "py3plex.load_network",
                    "description": "Load network from file",
                    "parameters": {
                        "path": {"type": "string", "required": True, "description": "File path"},
                        "input_type": {"type": "string", "default": "multiedgelist", "description": "Input format"},
                        "directed": {"type": "boolean", "default": False, "description": "Directed network"},
                        "layer_separator": {"type": "string", "optional": True, "description": "Layer separator"},
                    },
                    "returns": {"net_id": "string", "source": "string", "stats": "object"},
                    "example": {
                        "path": "/path/to/network.csv",
                        "input_type": "multiedgelist",
                        "directed": False,
                    },
                },
                {
                    "name": "py3plex.stats",
                    "description": "Get network statistics",
                    "parameters": {
                        "net_id": {"type": "string", "required": True, "description": "Network handle"},
                    },
                    "returns": {"stats": "object"},
                    "example": {"net_id": "abc12345"},
                },
                {
                    "name": "py3plex.run_query",
                    "description": "Execute DSL query (supports both legacy and v2)",
                    "parameters": {
                        "net_id": {"type": "string", "required": True, "description": "Network handle"},
                        "query": {"type": "string", "required": True, "description": "DSL query string (legacy) or Python expression (v2)"},
                        "limit": {"type": "integer", "default": 200, "description": "Max items to return"},
                        "use_v2": {"type": "boolean", "default": False, "description": "Use DSL v2 builder API (eval Python expression)"},
                    },
                    "returns": {"result": "object", "truncated": "boolean", "dsl_version": "string"},
                    "examples": [
                        {
                            "description": "Legacy DSL query",
                            "net_id": "abc12345",
                            "query": 'SELECT nodes WHERE degree > 5 COMPUTE pagerank',
                            "limit": 200,
                            "use_v2": False,
                        },
                        {
                            "description": "DSL v2 query",
                            "net_id": "abc12345",
                            "query": 'Q.nodes().where(degree__gt=5).compute("pagerank").limit(20)',
                            "limit": 200,
                            "use_v2": True,
                        },
                    ],
                },
                {
                    "name": "py3plex.community_detect",
                    "description": "Detect communities",
                    "parameters": {
                        "net_id": {"type": "string", "required": True},
                        "algorithm": {"type": "string", "default": "louvain", "options": SUPPORTED_ALGORITHMS},
                        "layer_mode": {"type": "string", "default": "aggregate"},
                        "params": {"type": "object", "optional": True},
                    },
                    "returns": {"communities": "object", "quality": "object"},
                    "example": {
                        "net_id": "abc12345",
                        "algorithm": "louvain",
                        "params": {"seed": 42},
                    },
                },
                {
                    "name": "py3plex.export",
                    "description": "Export data to file",
                    "parameters": {
                        "data": {"type": "object", "required": True},
                        "out_dir": {"type": "string", "optional": True, "default": str(DEFAULT_OUTPUT_DIR)},
                        "format": {"type": "string", "default": "json", "options": ["json", "csv"]},
                        "filename": {"type": "string", "optional": True},
                    },
                    "returns": {"written_paths": "array"},
                    "example": {
                        "data": {"nodes": []},
                        "format": "json",
                    },
                },
                {
                    "name": "py3plex.close",
                    "description": "Close network handle",
                    "parameters": {
                        "net_id": {"type": "string", "required": True},
                    },
                    "returns": {"message": "string"},
                    "example": {"net_id": "abc12345"},
                },
                {
                    "name": "py3plex.list_handles",
                    "description": "List all network handles",
                    "parameters": {},
                    "returns": {"handles": "array", "count": "integer"},
                    "example": {},
                },
            ]
        }
        return json.dumps(tools_doc, indent=2)

    else:
        raise ValueError(f"Unknown resource URI: {uri}")


# ============================================================================
# MAIN ENTRYPOINT
# ============================================================================


def main():
    """Start MCP server with stdio transport."""
    import asyncio

    async def run_server():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options(),
            )

    asyncio.run(run_server())


if __name__ == "__main__":
    main()
