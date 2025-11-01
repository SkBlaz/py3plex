#!/usr/bin/env python3
"""
Validation script for extended centrality metrics.

This script verifies that all newly implemented centrality metrics
(18-30) are working correctly with a simple test network.

Run this after installing all dependencies:
    pip install numpy scipy networkx
    python validate_centrality_metrics.py
"""

import sys


def main():
    """Run validation tests for extended centrality metrics."""
    try:
        import numpy as np
        from py3plex.core import multinet
        from py3plex.algorithms.multilayer_algorithms.centrality import (
            MultilayerCentrality,
            compute_all_centralities,
        )
    except ImportError as e:
        print(f"Error: Missing dependencies: {e}")
        print("\nPlease install required packages:")
        print("    pip install numpy scipy networkx")
        sys.exit(1)

    print("=" * 70)
    print("Validating Extended Centrality Metrics (18-30)")
    print("=" * 70)

    # Create a simple test network
    print("\n1. Creating test network...")
    network = multinet.multi_layer_network(directed=False)

    # Layer 1: A square
    network.add_edges(
        [
            ["A", "L1", "B", "L1", 1],
            ["B", "L1", "C", "L1", 1],
            ["C", "L1", "D", "L1", 1],
            ["D", "L1", "A", "L1", 1],
        ],
        input_type="list",
    )

    # Layer 2: A line with a star
    network.add_edges(
        [
            ["A", "L2", "B", "L2", 1],
            ["B", "L2", "C", "L2", 1],
            ["B", "L2", "D", "L2", 1],
        ],
        input_type="list",
    )

    print("   ✓ Network created with 4 nodes and 2 layers")

    calc = MultilayerCentrality(network)

    # Test each new centrality metric
    metrics_to_test = [
        ("18. Information Centrality", lambda: calc.information_centrality()),
        (
            "20. Communicability Betweenness",
            lambda: calc.communicability_betweenness_centrality(),
        ),
        ("21. Accessibility", lambda: calc.accessibility_centrality(h=2)),
        ("22. Percolation Centrality", lambda: calc.percolation_centrality(trials=10)),
        (
            "23. Spreading Centrality",
            lambda: calc.spreading_centrality(trials=5, steps=20),
        ),
        ("24. Collective Influence", lambda: calc.collective_influence(radius=2)),
        ("25. Load Centrality", lambda: calc.load_centrality()),
        (
            "26. Flow Betweenness",
            lambda: calc.flow_betweenness_centrality(samples=10),
        ),
        ("27. Harmonic Closeness", lambda: calc.harmonic_closeness_centrality()),
        ("28a. Edge Betweenness", lambda: calc.edge_betweenness_centrality()),
        ("28b. Bridging Centrality", lambda: calc.bridging_centrality()),
        ("29. Local Efficiency", lambda: calc.local_efficiency_centrality()),
    ]

    print("\n2. Testing individual metrics:")
    failed_tests = []

    for name, metric_func in metrics_to_test:
        try:
            result = metric_func()
            if isinstance(result, dict) and len(result) > 0:
                # Check that all values are numeric and finite
                all_valid = all(
                    isinstance(v, (int, float)) and np.isfinite(v)
                    for v in result.values()
                )
                if all_valid:
                    print(f"   ✓ {name}: {len(result)} values computed")
                else:
                    print(f"   ✗ {name}: Contains invalid values")
                    failed_tests.append(name)
            else:
                print(f"   ✗ {name}: Invalid result format")
                failed_tests.append(name)
        except Exception as e:
            print(f"   ✗ {name}: Failed with error: {e}")
            failed_tests.append(name)

    # Test Lp-aggregated centrality
    print("\n3. Testing Lp-aggregated centrality:")
    try:
        layer_degrees = calc.layer_degree_centrality(weighted=False)

        # Test L2 norm
        l2_result = calc.lp_aggregated_centrality(layer_degrees, p=2)
        if isinstance(l2_result, dict) and len(l2_result) > 0:
            print(f"   ✓ 30a. Lp-aggregated (L2): {len(l2_result)} values computed")
        else:
            print("   ✗ 30a. Lp-aggregated (L2): Invalid result")
            failed_tests.append("30a. Lp-aggregated (L2)")

        # Test L-infinity norm
        linf_result = calc.lp_aggregated_centrality(layer_degrees, p=float("inf"))
        if isinstance(linf_result, dict) and len(linf_result) > 0:
            print(f"   ✓ 30b. Lp-aggregated (L∞): {len(linf_result)} values computed")
        else:
            print("   ✗ 30b. Lp-aggregated (L∞): Invalid result")
            failed_tests.append("30b. Lp-aggregated (L∞)")
    except Exception as e:
        print(f"   ✗ 30. Lp-aggregated: Failed with error: {e}")
        failed_tests.append("30. Lp-aggregated")

    # Test compute_all_centralities with extended flag
    print("\n4. Testing compute_all_centralities with extended flag:")
    try:
        results = compute_all_centralities(network, include_extended=True)

        expected_keys = [
            "information",
            "communicability_betweenness",
            "accessibility",
            "harmonic_closeness",
            "local_efficiency",
            "edge_betweenness",
            "bridging",
            "percolation",
            "spreading",
            "collective_influence",
            "load",
            "flow_betweenness",
        ]

        missing_keys = [key for key in expected_keys if key not in results]

        if not missing_keys:
            print(f"   ✓ All {len(expected_keys)} extended metrics included")
        else:
            print(f"   ✗ Missing keys: {missing_keys}")
            failed_tests.append("compute_all_centralities")
    except Exception as e:
        print(f"   ✗ compute_all_centralities: Failed with error: {e}")
        failed_tests.append("compute_all_centralities")

    # Summary
    print("\n" + "=" * 70)
    if not failed_tests:
        print("✓ SUCCESS: All extended centrality metrics validated!")
        print("=" * 70)
        return 0
    else:
        print(f"✗ FAILED: {len(failed_tests)} test(s) failed:")
        for test in failed_tests:
            print(f"    - {test}")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
