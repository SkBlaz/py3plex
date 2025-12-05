#!/bin/bash
# Example 3: DSL Query Examples
#
# This example demonstrates various DSL query patterns available
# in py3plex, both the string syntax and Python builder syntax.
#
# Usage: bash example_3_dsl_queries.sh

set -e

echo "==================================================================="
echo "py3plex CLI Example 3: DSL Query Examples"
echo "==================================================================="
echo

WORK_DIR=$(mktemp -d)

# Create a test network with meaningful structure
echo "Creating test network..."
py3plex create --nodes 40 --layers 3 --probability 0.12 --seed 789 --output "$WORK_DIR/network.edgelist"
echo

# ===========================
# STRING DSL SYNTAX EXAMPLES
# ===========================
echo "==========================================="
echo "STRING DSL SYNTAX EXAMPLES"
echo "==========================================="
echo

echo "--- 1. Select all nodes ---"
py3plex query "$WORK_DIR/network.edgelist" "SELECT nodes" --format json 2>/dev/null | \
    python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Found {d[\"count\"]} nodes')"
echo

echo "--- 2. Compute single measure ---"
py3plex query "$WORK_DIR/network.edgelist" "SELECT nodes COMPUTE degree" --format table 2>/dev/null | head -12
echo

echo "--- 3. Compute multiple measures ---"
py3plex query "$WORK_DIR/network.edgelist" "SELECT nodes COMPUTE degree, clustering" --format table 2>/dev/null | head -12
echo

echo "--- 4. Filter by layer ---"
py3plex query "$WORK_DIR/network.edgelist" 'SELECT nodes WHERE layer="layer1"' --format json 2>/dev/null | \
    python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Nodes in layer1: {d[\"count\"]}')"
echo

# ===========================
# PYTHON DSL BUILDER EXAMPLES
# ===========================
echo "==========================================="
echo "PYTHON DSL BUILDER SYNTAX EXAMPLES (--dsl)"
echo "==========================================="
echo

echo "--- 5. Basic query with builder ---"
py3plex query "$WORK_DIR/network.edgelist" \
    'Q.nodes()' \
    --dsl --format json 2>/dev/null | \
    python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Found {d[\"count\"]} nodes')"
echo

echo "--- 6. Compute with alias ---"
py3plex query "$WORK_DIR/network.edgelist" \
    'Q.nodes().compute("betweenness_centrality", alias="bc")' \
    --dsl --format table 2>/dev/null | head -12
echo

echo "--- 7. Order by descending ---"
py3plex query "$WORK_DIR/network.edgelist" \
    'Q.nodes().compute("degree").order_by("-degree").limit(10)' \
    --dsl --format table 2>/dev/null
echo

echo "--- 8. Filter with where clause ---"
py3plex query "$WORK_DIR/network.edgelist" \
    'Q.nodes().where(degree__gt=3).compute("degree")' \
    --dsl --format table 2>/dev/null | head -12
echo

echo "--- 9. Layer algebra - union ---"
py3plex query "$WORK_DIR/network.edgelist" \
    'Q.nodes().from_layers(L["layer1"] + L["layer2"]).compute("degree")' \
    --dsl --format json 2>/dev/null | \
    python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Nodes in layer1+layer2: {d[\"count\"]}')"
echo

echo "--- 10. Complete analysis pipeline ---"
echo "Top 5 highest-degree nodes across all layers:"
py3plex query "$WORK_DIR/network.edgelist" \
    'Q.nodes().compute("degree", "clustering", "betweenness_centrality").order_by("-degree").limit(5)' \
    --dsl --format table 2>/dev/null
echo

# Cleanup
rm -rf "$WORK_DIR"

echo "==================================================================="
echo "DSL query examples completed!"
echo "==================================================================="
echo
echo "Quick Reference:"
echo "  String DSL:   py3plex query file.edgelist \"SELECT nodes COMPUTE degree\""
echo "  Builder DSL:  py3plex query file.edgelist 'Q.nodes().compute(\"degree\")' --dsl"
echo
