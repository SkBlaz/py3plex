#!/bin/bash
# Example 2: Unix Piping Workflows
#
# This example demonstrates advanced Unix piping patterns with py3plex,
# including chaining commands and combining with other Unix tools.
#
# Usage: bash example_2_piping_workflows.sh

set -e

echo "==================================================================="
echo "py3plex CLI Example 2: Unix Piping Workflows"
echo "==================================================================="
echo

WORK_DIR=$(mktemp -d)
echo "Working directory: $WORK_DIR"
echo

# Create a network for testing
echo "Creating test network..."
py3plex create --nodes 30 --layers 2 --probability 0.15 --seed 123 --output "$WORK_DIR/network.edgelist"
echo

# Example 1: Pipe from stdin
echo "--- Example 1: Load network from stdin ---"
cat "$WORK_DIR/network.edgelist" | py3plex load - --info 2>&1 | grep -E "(Nodes|Edges|Layers)"
echo

# Example 2: Query with JSON output, process with grep
echo "--- Example 2: Query and filter JSON output ---"
py3plex query "$WORK_DIR/network.edgelist" "SELECT nodes COMPUTE degree" --format json 2>/dev/null | \
    grep -o '"count": [0-9]*' | head -1
echo

# Example 3: Export to CSV and count lines
echo "--- Example 3: Export to CSV format ---"
py3plex query "$WORK_DIR/network.edgelist" "SELECT nodes COMPUTE degree" --format csv 2>/dev/null | \
    head -5
echo
echo "Total rows (including header):"
py3plex query "$WORK_DIR/network.edgelist" "SELECT nodes COMPUTE degree" --format csv 2>/dev/null | wc -l
echo

# Example 4: Chain create and query
echo "--- Example 4: Chain create and query (no intermediate file) ---"
# Note: We create a network and immediately analyze it
py3plex create --nodes 20 --layers 2 --probability 0.2 --seed 456 --output /dev/stdout 2>/dev/null | \
    py3plex query - "SELECT nodes COMPUTE degree" --format table 2>/dev/null | head -10
echo

# Example 5: Compare multiple queries using DSL
echo "--- Example 5: Multiple DSL queries on same network ---"
echo "Top 5 by degree:"
py3plex query "$WORK_DIR/network.edgelist" \
    'Q.nodes().compute("degree").order_by("-degree").limit(5)' \
    --dsl --format table 2>/dev/null

echo
echo "Top 5 by clustering coefficient:"
py3plex query "$WORK_DIR/network.edgelist" \
    'Q.nodes().compute("clustering").order_by("-clustering").limit(5)' \
    --dsl --format table 2>/dev/null
echo

# Example 6: Save query results to files
echo "--- Example 6: Save results to files ---"
py3plex query "$WORK_DIR/network.edgelist" "SELECT nodes COMPUTE degree" \
    --format json -o "$WORK_DIR/degrees.json" 2>/dev/null
py3plex query "$WORK_DIR/network.edgelist" "SELECT nodes COMPUTE betweenness_centrality" \
    --format csv -o "$WORK_DIR/betweenness.csv" 2>/dev/null

echo "Created files:"
ls -la "$WORK_DIR"/*.json "$WORK_DIR"/*.csv 2>/dev/null || true
echo

# Cleanup
rm -rf "$WORK_DIR"

echo "==================================================================="
echo "Piping examples completed!"
echo "==================================================================="
