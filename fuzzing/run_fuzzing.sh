#!/usr/bin/env bash
#
# Run fuzzing campaigns for py3plex
#
# Usage:
#   ./run_fuzzing.sh [duration_seconds]
#
# Examples:
#   ./run_fuzzing.sh 60       # Quick 1-minute test
#   ./run_fuzzing.sh 300      # 5-minute campaign
#   ./run_fuzzing.sh 3600     # 1-hour campaign

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Default duration: 5 minutes
DURATION="${1:-300}"

echo "=================================="
echo "Py3plex Fuzzing Campaign"
echo "=================================="
echo "Duration: ${DURATION} seconds"
echo "Seed corpus: fuzzing/seeds/"
echo "=================================="

# Check if atheris is installed
if ! python3 -c "import atheris" 2>/dev/null; then
    echo "ERROR: Atheris not installed"
    echo "Install with: pip install atheris"
    exit 1
fi

# Check if py3plex is installed
if ! python3 -c "import py3plex" 2>/dev/null; then
    echo "ERROR: py3plex not installed"
    echo "Install with: pip install -e ."
    exit 1
fi

echo ""
echo "Starting fuzzing campaign..."
echo ""

# Create output directory for crashes
mkdir -p fuzzing/crashes

# Fuzzer 1: Network loading
echo "-----------------------------------"
echo "Fuzzer 1/3: Network Loading"
echo "-----------------------------------"
python3 fuzzing/fuzz_load_network.py \
    fuzzing/seeds/ \
    -max_total_time="$DURATION" \
    -artifact_prefix=fuzzing/crashes/ \
    -print_final_stats=1 \
    2>&1 | tee fuzzing/fuzz_load_network.log

echo ""
echo "-----------------------------------"
echo "Fuzzer 2/3: Line Parsing"
echo "-----------------------------------"
python3 fuzzing/fuzz_parse_line.py \
    fuzzing/seeds/ \
    -max_total_time="$DURATION" \
    -artifact_prefix=fuzzing/crashes/ \
    -print_final_stats=1 \
    2>&1 | tee fuzzing/fuzz_parse_line.log

echo ""
echo "-----------------------------------"
echo "Fuzzer 3/3: DSL Query Parsing"
echo "-----------------------------------"
python3 fuzzing/fuzz_dsl.py \
    fuzzing/seeds/ \
    -max_total_time="$DURATION" \
    -artifact_prefix=fuzzing/crashes/ \
    -print_final_stats=1 \
    2>&1 | tee fuzzing/fuzz_dsl.log

echo ""
echo "=================================="
echo "Fuzzing Campaign Complete"
echo "=================================="
echo "Logs saved to:"
echo "  - fuzzing/fuzz_load_network.log"
echo "  - fuzzing/fuzz_parse_line.log"
echo "  - fuzzing/fuzz_dsl.log"
echo ""

# Check for crashes
if ls fuzzing/crashes/crash-* 1>/dev/null 2>&1; then
    echo "⚠️  CRASHES FOUND!"
    echo "Crash files saved to fuzzing/crashes/"
    ls -lh fuzzing/crashes/crash-*
    echo ""
    echo "To reproduce a crash:"
    echo "  python3 fuzzing/fuzz_load_network.py fuzzing/seeds/ fuzzing/crashes/crash-XXXXX"
    exit 1
else
    echo "✅ No crashes found"
    echo "Fuzzing completed successfully"
    exit 0
fi
