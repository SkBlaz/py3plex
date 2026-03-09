"""Example MCP interactions for py3plex.

This file demonstrates how to use py3plex via the MCP server.

NOTE: These are conceptual examples showing the JSON payloads.
To actually run these, you need an MCP client (Claude Desktop, Gemini, etc.)
with the py3plex-mcp server configured.

SKIP_CI: true - This is a documentation file showing JSON examples, not executable code
"""

if __name__ == "__main__":
    print("This file is documentation-only. Use it as an MCP payload reference.")
    raise SystemExit(0)

# ==============================================================================
# Example 1: Load Network and Get Statistics
# ==============================================================================

# Tool call: py3plex.load_network
{
    "path": "/home/user/data/social_network.csv",
    "input_type": "multiedgelist",
    "directed": False
}

# Response:
{
    "meta": {
        "ok": True,
        "tool": "py3plex.load_network",
        "version": {
            "py3plex": "1.1.2",
            "mcp_server": "1.0.0"
        },
        "timestamp": 1704988800.0
    },
    "net_id": "abc12345",
    "source": "/home/user/data/social_network.csv",
    "stats": {
        "node_count": 150,
        "edge_count": 430,
        "layer_count": 2,
        "layers_preview": ["social", "work"]
    }
}

# Tool call: py3plex.stats
{
    "net_id": "abc12345"
}

# Response: (same stats as above)


# ==============================================================================
# Example 2: Query Network (Legacy DSL)
# ==============================================================================

# Tool call: py3plex.run_query (legacy DSL)
{
    "net_id": "abc12345",
    "query": "SELECT nodes WHERE degree > 10 COMPUTE pagerank",
    "limit": 50,
    "use_v2": False
}

# Response:
{
    "meta": {
        "ok": True,
        "tool": "py3plex.run_query",
        "truncated": False,
        "timestamp": 1704988810.0
    },
    "net_id": "abc12345",
    "query": "SELECT nodes WHERE degree > 10 COMPUTE pagerank",
    "dsl_version": "legacy",
    "result": {
        "nodes": [
            {"node": "Alice", "layer": "social", "degree": 15, "pagerank": 0.023},
            {"node": "Bob", "layer": "social", "degree": 12, "pagerank": 0.019},
            # ... more nodes
        ],
        "computed": {
            "pagerank": {...}
        },
        "meta": {}
    },
    "truncated": False
}


# ==============================================================================
# Example 3: Query Network (DSL v2 - Recommended)
# ==============================================================================

# Tool call: py3plex.run_query (DSL v2)
{
    "net_id": "abc12345",
    "query": "Q.nodes().where(degree__gt=10).compute('pagerank').order_by('pagerank', desc=True).limit(20)",
    "limit": 50,
    "use_v2": True
}

# Response:
{
    "meta": {
        "ok": True,
        "tool": "py3plex.run_query",
        "truncated": False,
        "timestamp": 1704988815.0
    },
    "net_id": "abc12345",
    "query": "Q.nodes().where(degree__gt=10).compute('pagerank').order_by('pagerank', desc=True).limit(20)",
    "dsl_version": "v2",
    "result": {
        "nodes": [
            ["Alice", "social"],
            ["Bob", "social"],
            ["Charlie", "social"],
            # ... more nodes
        ],
        "computed": {
            "pagerank": {
                ("Alice", "social"): 0.025,
                ("Bob", "social"): 0.021,
                # ...
            }
        },
        "meta": {}
    },
    "truncated": False
}


# ==============================================================================
# Example 4: DSL v2 Advanced Queries
# ==============================================================================

# Layer selection with algebra
{
    "net_id": "abc12345",
    "query": "Q.nodes().from_layers(L['social'] + L['work']).compute('degree')",
    "use_v2": True
}

# Django-style filtering
{
    "net_id": "abc12345",
    "query": "Q.nodes().where(layer='social', degree__between=(5, 15)).compute('betweenness_centrality', alias='bc').order_by('bc', desc=True).limit(10)",
    "use_v2": True
}

# Edge queries
{
    "net_id": "abc12345",
    "query": "Q.edges().where(interlayer=True).limit(100)",
    "use_v2": True
}

# Grouped queries
{
    "net_id": "abc12345",
    "query": "Q.nodes().per_layer().compute('degree')",
    "use_v2": True
}


# ==============================================================================
# Example 5: Community Detection
# ==============================================================================

# Tool call: py3plex.community_detect
{
    "net_id": "abc12345",
    "algorithm": "louvain",
    "layer_mode": "aggregate",
    "params": {
        "seed": 42,
        "resolution": 1.0
    }
}

# Response:
{
    "meta": {
        "ok": True,
        "tool": "py3plex.community_detect",
        "timestamp": 1704988820.0
    },
    "net_id": "abc12345",
    "algorithm": "louvain",
    "layer_mode": "aggregate",
    "communities": {
        "Alice": 0,
        "Bob": 0,
        "Charlie": 1,
        "David": 1,
        # ... more nodes
    },
    "quality": {
        "num_communities": 5,
        "community_sizes": {
            "0": 45,
            "1": 38,
            "2": 32,
            "3": 20,
            "4": 15
        }
    },
    "runtime_ms": 125.3
}


# ==============================================================================
# Example 4: Export Results
# ==============================================================================

# Tool call: py3plex.export
{
    "data": {
        "nodes": [
            {"id": "Alice", "degree": 15, "pagerank": 0.023},
            {"id": "Bob", "degree": 12, "pagerank": 0.019}
        ]
    },
    "format": "csv",
    "filename": "high_degree_nodes.csv"
}

# Response:
{
    "meta": {
        "ok": True,
        "tool": "py3plex.export",
        "timestamp": 1704988830.0
    },
    "written_paths": [
        "/home/user/.py3plex_mcp/out/high_degree_nodes.csv"
    ],
    "format": "csv",
    "size_bytes": 1234
}


# ==============================================================================
# Example 5: Complete Workflow
# ==============================================================================

# Step 1: Load network
load_response = py3plex.load_network(
    path="/data/collaboration_network.csv",
    input_type="multiedgelist"
)
net_id = load_response["net_id"]  # e.g., "xyz98765"

# Step 2: Get statistics
stats = py3plex.stats(net_id=net_id)
print(f"Loaded network with {stats['node_count']} nodes")

# Step 3: Find influential nodes
query_result = py3plex.run_query(
    net_id=net_id,
    query='SELECT nodes COMPUTE degree, betweenness_centrality ORDER BY betweenness_centrality LIMIT 20'
)

# Step 4: Detect communities
communities = py3plex.community_detect(
    net_id=net_id,
    algorithm="leiden",
    params={"seed": 42}
)

# Step 5: Export results
py3plex.export(
    data=query_result["result"],
    format="json",
    filename="influential_nodes.json"
)

py3plex.export(
    data=communities,
    format="json",
    filename="communities.json"
)

# Step 6: Clean up
py3plex.close(net_id=net_id)


# ==============================================================================
# Example 6: Error Handling
# ==============================================================================

# Tool call with invalid network ID
{
    "net_id": "invalid_id"
}

# Error response:
{
    "ok": False,
    "error": {
        "type": "NetworkNotFoundError",
        "message": "Network 'invalid_id' not found",
        "hint": "Use py3plex.list_handles to see available networks"
    },
    "meta": {
        "ok": False,
        "tool": "py3plex.stats",
        "timestamp": 1704988840.0
    }
}


# ==============================================================================
# Example 7: List Active Networks
# ==============================================================================

# Tool call: py3plex.list_handles
{}

# Response:
{
    "meta": {
        "ok": True,
        "tool": "py3plex.list_handles",
        "timestamp": 1704988850.0
    },
    "handles": [
        {
            "net_id": "abc12345",
            "source": "/home/user/data/social_network.csv",
            "created_at": 1704988800.0
        },
        {
            "net_id": "xyz98765",
            "source": "/data/collaboration_network.csv",
            "created_at": 1704988820.0
        }
    ],
    "count": 2
}


# ==============================================================================
# Resources
# ==============================================================================

# Resource: py3plex://agents
# Returns the complete AGENTS.md documentation

# Resource: py3plex://help/dsl
# Returns DSL reference with syntax examples

# Resource: py3plex://help/tools
# Returns tool schemas and usage examples
