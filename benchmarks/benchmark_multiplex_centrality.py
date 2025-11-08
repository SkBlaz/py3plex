#!/usr/bin/env python3
"""
Performance Benchmark: Multiplex Network Construction and Centrality Computation

This micro-benchmark evaluates the performance of py3plex for the workflow:
1. Build multiplex network (random ER graphs)
2. Compute centrality measures
3. Serialize network to disk

Benchmarked for N ∈ {1e3, 1e4, 1e5} edges with performance metrics:
- Construction time
- Algorithm execution time (centrality computation)
- Serialization time
- RSS memory usage

Usage:
    python benchmark_multiplex_centrality.py

Output:
    - Formatted table with timing and memory metrics
    - Flamegraph generation instructions
    - Optimization suggestions with complexity analysis
"""

import gc
import os
import sys
import tempfile
import time
from typing import Dict, List, Tuple

import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from py3plex.algorithms.multilayer_algorithms.centrality import MultilayerCentrality
from py3plex.core import multinet, random_generators


def get_rss_memory_mb() -> float:
    """
    Get current RSS (Resident Set Size) memory usage in MB.
    
    Returns:
        Memory usage in megabytes
    """
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # KB to MB on Linux
    except (ImportError, AttributeError):
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)  # bytes to MB
        except ImportError:
            return -1.0  # Unable to measure


class BenchmarkResult:
    """Container for benchmark results."""
    
    def __init__(self, n_edges: int):
        self.n_edges = n_edges
        self.n_nodes = 0
        self.n_layers = 0
        self.construction_time = 0.0
        self.centrality_time = 0.0
        self.serialization_time = 0.0
        self.memory_before_mb = 0.0
        self.memory_after_mb = 0.0
        self.memory_peak_mb = 0.0


def estimate_network_params(target_edges: int, n_layers: int = 4) -> Tuple[int, float]:
    """
    Estimate number of nodes and edge probability for target edge count.
    
    For a complete graph: max_edges = n*(n-1)/2
    For random ER graph: expected_edges ≈ n*(n-1)*p/2
    
    Args:
        target_edges: Desired number of edges
        n_layers: Number of layers in the multiplex network
        
    Returns:
        (n_nodes, edge_probability)
    """
    # For multiplex with L layers, total edges ≈ L * n*(n-1)*p/2
    # Solve for n given target_edges
    # Using quadratic formula: n^2 - n ≈ 2*target_edges/(L*p)
    # Start with p=0.1 and adjust
    
    p = 0.1
    n_squared_approx = 2 * target_edges / (n_layers * p)
    n = int(np.sqrt(n_squared_approx)) + 1
    
    # Refine p to get closer to target
    max_edges_per_layer = n * (n - 1) / 2
    p = target_edges / (n_layers * max_edges_per_layer)
    p = min(max(p, 0.01), 0.95)  # Keep p in reasonable range
    
    return n, p


def build_multiplex_network(n_nodes: int, n_layers: int, edge_prob: float) -> multinet.multi_layer_network:
    """
    Build a multiplex network using random ER graphs.
    
    Args:
        n_nodes: Number of nodes
        n_layers: Number of layers
        edge_prob: Edge probability for ER graphs
        
    Returns:
        multi_layer_network object
    """
    return random_generators.random_multilayer_ER(n_nodes, n_layers, edge_prob, directed=False)


def compute_centralities(network: multinet.multi_layer_network) -> Dict[str, Dict]:
    """
    Compute multiple centrality measures for the multiplex network.
    
    Args:
        network: Input multiplex network
        
    Returns:
        Dictionary of centrality measures
    """
    calc = MultilayerCentrality(network)
    
    results = {}
    
    # Fast degree-based measures
    results['degree'] = calc.layer_degree_centrality(weighted=False)
    results['overlapping_degree'] = calc.overlapping_degree_centrality(weighted=False)
    results['participation'] = calc.participation_coefficient(weighted=False)
    
    # Eigenvector-based measures (moderate cost)
    # Skip eigenvector centrality due to compatibility issues with scipy sparse matrix types
    # results['eigenvector'] = calc.multiplex_eigenvector_centrality()
    results['pagerank'] = calc.pagerank_centrality(damping=0.85)
    
    # Path-based measures (more expensive)
    results['closeness'] = calc.multilayer_closeness_centrality()
    
    return results


def serialize_network(network: multinet.multi_layer_network, filepath: str) -> None:
    """
    Serialize network to disk.
    
    Args:
        network: Network to serialize
        filepath: Output file path
    """
    network.save_network(output_file=filepath, output_type="edgelist")


def run_benchmark(target_edges: int, n_layers: int = 4) -> BenchmarkResult:
    """
    Run complete benchmark for a given edge count.
    
    Args:
        target_edges: Target number of edges
        n_layers: Number of layers in multiplex network
        
    Returns:
        BenchmarkResult with timing and memory metrics
    """
    result = BenchmarkResult(target_edges)
    result.n_layers = n_layers
    
    # Force garbage collection before starting
    gc.collect()
    
    # Estimate network parameters
    n_nodes, edge_prob = estimate_network_params(target_edges, n_layers)
    result.n_nodes = n_nodes
    
    print(f"  Parameters: {n_nodes} nodes, {n_layers} layers, p={edge_prob:.4f}")
    
    # Measure initial memory
    result.memory_before_mb = get_rss_memory_mb()
    
    # ==================== CONSTRUCTION ====================
    print(f"  Building multiplex network...", end=" ", flush=True)
    t0 = time.perf_counter()
    network = build_multiplex_network(n_nodes, n_layers, edge_prob)
    result.construction_time = time.perf_counter() - t0
    print(f"{result.construction_time:.4f}s")
    
    # Count actual edges
    actual_edges = len(list(network.get_edges()))
    print(f"  Actual edges: {actual_edges}")
    
    # Measure memory after construction
    mem_after_construction = get_rss_memory_mb()
    result.memory_peak_mb = mem_after_construction
    
    # ==================== CENTRALITY ====================
    print(f"  Computing centrality measures...", end=" ", flush=True)
    t0 = time.perf_counter()
    centralities = compute_centralities(network)
    result.centrality_time = time.perf_counter() - t0
    print(f"{result.centrality_time:.4f}s")
    
    # Update peak memory if needed
    mem_after_centrality = get_rss_memory_mb()
    result.memory_peak_mb = max(result.memory_peak_mb, mem_after_centrality)
    
    # ==================== SERIALIZATION ====================
    with tempfile.NamedTemporaryFile(mode='w', suffix='.edgelist', delete=False) as f:
        temp_file = f.name
    
    try:
        print(f"  Serializing to disk...", end=" ", flush=True)
        t0 = time.perf_counter()
        serialize_network(network, temp_file)
        result.serialization_time = time.perf_counter() - t0
        print(f"{result.serialization_time:.4f}s")
    finally:
        # Clean up temp file
        if os.path.exists(temp_file):
            os.remove(temp_file)
    
    # Final memory measurement
    result.memory_after_mb = get_rss_memory_mb()
    
    return result


def print_results_table(results: List[BenchmarkResult]) -> None:
    """
    Print formatted results table.
    
    Args:
        results: List of benchmark results
    """
    print("\n" + "="*80)
    print(" BENCHMARK RESULTS: Multiplex Network Construction & Centrality")
    print("="*80)
    print()
    
    # Table header
    print(f"{'Edges':<10} {'Nodes':<8} {'Layers':<8} {'Construct(s)':<14} {'Centrality(s)':<15} {'Serialize(s)':<14} {'Peak Mem(MB)':<12}")
    print("-" * 80)
    
    # Table rows
    for r in results:
        print(f"{r.n_edges:<10} {r.n_nodes:<8} {r.n_layers:<8} "
              f"{r.construction_time:<14.4f} {r.centrality_time:<15.4f} "
              f"{r.serialization_time:<14.4f} {r.memory_peak_mb:<12.1f}")
    
    print("-" * 80)
    print()
    
    # Summary statistics
    print("SUMMARY:")
    print(f"  Total edges tested: {sum(r.n_edges for r in results):,}")
    print(f"  Total time: {sum(r.construction_time + r.centrality_time + r.serialization_time for r in results):.4f}s")
    print(f"  Peak memory: {max(r.memory_peak_mb for r in results):.1f} MB")
    print()
    
    # Time breakdown for largest benchmark
    if results:
        largest = results[-1]
        total_time = largest.construction_time + largest.centrality_time + largest.serialization_time
        print(f"TIME BREAKDOWN (N={largest.n_edges:,} edges):")
        print(f"  Construction:  {largest.construction_time:8.4f}s ({100*largest.construction_time/total_time:5.1f}%)")
        print(f"  Centrality:    {largest.centrality_time:8.4f}s ({100*largest.centrality_time/total_time:5.1f}%)")
        print(f"  Serialization: {largest.serialization_time:8.4f}s ({100*largest.serialization_time/total_time:5.1f}%)")
        print()


def print_flamegraph_instructions() -> None:
    """Print instructions for generating flamegraphs."""
    print("="*80)
    print(" FLAMEGRAPH GENERATION INSTRUCTIONS")
    print("="*80)
    print()
    print("To generate flamegraphs for detailed performance profiling:")
    print()
    print("1. Install py-spy:")
    print("   pip install py-spy")
    print()
    print("2. Run benchmark with profiling:")
    print("   sudo py-spy record -o flamegraph.svg --format speedscope -- python benchmark_multiplex_centrality.py")
    print()
    print("3. Alternative: Use cProfile + flameprof:")
    print("   python -m cProfile -o profile.out benchmark_multiplex_centrality.py")
    print("   flameprof profile.out > flamegraph.svg")
    print()
    print("4. View SVG flamegraph in browser or speedscope.app")
    print()


def print_optimization_suggestions() -> None:
    """Print optimization suggestions with complexity analysis."""
    print("="*80)
    print(" OPTIMIZATION SUGGESTIONS")
    print("="*80)
    print()
    
    print("1. SPARSE MATRIX REPRESENTATION FOR CENTRALITY")
    print("   " + "-"*76)
    print("   Current: Dense matrix operations in some centrality algorithms")
    print("   Optimization: Use scipy.sparse throughout for large networks")
    print("   Complexity Impact:")
    print("     • Space: O(n²) → O(e) where e = number of edges")
    print("     • Time (matrix ops): O(n²) → O(e) for sparse operations")
    print("   Expected Speedup: 2-5× for networks with e << n²")
    print("   Implementation: Replace np.array with scipy.sparse.csr_matrix")
    print()
    
    print("2. PARALLELIZED LAYER-WISE CENTRALITY")
    print("   " + "-"*76)
    print("   Current: Sequential computation across layers")
    print("   Optimization: Use multiprocessing/joblib for independent layer calculations")
    print("   Complexity Impact:")
    print("     • Time: O(L × T_centrality) → O(T_centrality) with L cores")
    print("     • Space: O(L × S) → O(L × S) [no improvement, but acceptable]")
    print("   Expected Speedup: Linear with number of layers (up to L×)")
    print("   Implementation: Use joblib.Parallel for layer_degree_centrality")
    print()
    
    print("3. INCREMENTAL NETWORK CONSTRUCTION")
    print("   " + "-"*76)
    print("   Current: Full graph generation then layer assignment")
    print("   Optimization: Stream edges during construction, avoid intermediate storage")
    print("   Complexity Impact:")
    print("     • Memory: Reduce peak by ~30-40% (avoid duplicate edge storage)")
    print("     • Time: O(e) → O(e) but with lower constant factor")
    print("   Expected Speedup: 1.3-1.5× construction time, significant memory reduction")
    print("   Implementation: Generator-based edge creation with immediate insertion")
    print()
    
    print("ADDITIONAL NOTES:")
    print("  • For N > 1e6 edges, consider graph databases (Neo4j, NetworkX with SQLite)")
    print("  • Eigenvector centrality can use power iteration with early stopping")
    print("  • Consider approximation algorithms (sampling-based) for betweenness centrality")
    print()


def main() -> None:
    """Main benchmark execution."""
    print("="*80)
    print(" py3plex PERFORMANCE BENCHMARK")
    print(" Workflow: Build Multiplex → Compute Centrality → Serialize")
    print("="*80)
    print()
    
    # Test sizes: N ∈ {1e3, 1e4, 1e5}
    test_sizes = [1000, 10000, 100000]
    n_layers = 4
    
    results = []
    
    for target_edges in test_sizes:
        print(f"\n[Benchmark: {target_edges:,} edges target]")
        try:
            result = run_benchmark(target_edges, n_layers)
            results.append(result)
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Print results
    if results:
        print_results_table(results)
        print_flamegraph_instructions()
        print_optimization_suggestions()
    else:
        print("\nNo successful benchmarks completed.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
