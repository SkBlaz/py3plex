#!/bin/bash
# Example 1: Basic CLI workflow with piping
#
# This example demonstrates basic command-line operations with py3plex,
# including network creation, loading, and querying with Unix pipes.
#
# Usage: bash example_1_basic_workflow.sh

set -e

echo "==================================================================="
echo "py3plex CLI Example 1: Basic Workflow with Piping"
echo "==================================================================="
echo

# Create a temporary directory for our work
WORK_DIR=$(mktemp -d)
echo "Working directory: $WORK_DIR"
echo

# Step 1: Create a random multilayer network
echo "Step 1: Creating a random multilayer network..."
py3plex create \
    --nodes 50 \
    --layers 3 \
    --type er \
    --probability 0.1 \
    --seed 42 \
    --output "$WORK_DIR/network.edgelist"
echo

# Step 2: Load and display network info
echo "Step 2: Loading network and displaying info..."
py3plex load "$WORK_DIR/network.edgelist" --info
echo

# Step 3: Query the network for node degrees
echo "Step 3: Querying for node degrees (table format)..."
py3plex query "$WORK_DIR/network.edgelist" "SELECT nodes COMPUTE degree" --format table 2>/dev/null | head -20
echo

# Step 4: Pipe network data and query
echo "Step 4: Piping network data directly to query command..."
cat "$WORK_DIR/network.edgelist" | py3plex query - "SELECT nodes COMPUTE degree" --format json 2>/dev/null | head -30
echo

# Step 5: Using Python DSL builder syntax
echo "Step 5: Using Python DSL builder syntax for advanced queries..."
py3plex query "$WORK_DIR/network.edgelist" \
    'Q.nodes().compute("degree", "clustering").order_by("-degree").limit(10)' \
    --dsl \
    --format table 2>/dev/null
echo

# Cleanup
echo "Cleaning up..."
rm -rf "$WORK_DIR"
echo

echo "==================================================================="
echo "Example completed!"
echo "==================================================================="
