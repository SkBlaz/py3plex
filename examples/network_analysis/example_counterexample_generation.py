"""Example: Network Counterexample Generation

This script demonstrates the counterexample generation feature for finding
violations of network invariants.
"""

from py3plex.core import multinet
from py3plex.dsl import Q, L
from py3plex.counterexamples.engine import CounterexampleNotFound


def build_sample_network():
    """Build a sample multilayer network with interesting properties."""
    net = multinet.multi_layer_network(directed=False)
    
    # Create a network where node A has high degree but low PageRank
    # (isolated hub pattern)
    nodes = [
        {"source": "A", "type": "social"},
        {"source": "B", "type": "social"},
        {"source": "C", "type": "social"},
        {"source": "D", "type": "social"},
        {"source": "E", "type": "social"},
        {"source": "F", "type": "social"},
    ]
    net.add_nodes(nodes)
    
    # A is connected to everyone but they form a clique without A
    edges = [
        # A connections (hub)
        {"source": "A", "target": "B", "source_type": "social", "target_type": "social", "weight": 1.0},
        {"source": "A", "target": "C", "source_type": "social", "target_type": "social", "weight": 1.0},
        {"source": "A", "target": "D", "source_type": "social", "target_type": "social", "weight": 1.0},
        {"source": "A", "target": "E", "source_type": "social", "target_type": "social", "weight": 1.0},
        # B-C-D-E form a clique (higher PageRank)
        {"source": "B", "target": "C", "source_type": "social", "target_type": "social", "weight": 1.0},
        {"source": "B", "target": "D", "source_type": "social", "target_type": "social", "weight": 1.0},
        {"source": "B", "target": "E", "source_type": "social", "target_type": "social", "weight": 1.0},
        {"source": "C", "target": "D", "source_type": "social", "target_type": "social", "weight": 1.0},
        {"source": "C", "target": "E", "source_type": "social", "target_type": "social", "weight": 1.0},
        {"source": "D", "target": "E", "source_type": "social", "target_type": "social", "weight": 1.0},
        # F is isolated
        {"source": "F", "target": "E", "source_type": "social", "target_type": "social", "weight": 1.0},
    ]
    net.add_edges(edges)
    
    return net


def example_basic():
    """Basic counterexample generation."""
    print("=" * 70)
    print("EXAMPLE 1: Basic Counterexample Generation")
    print("=" * 70)
    print()
    
    net = build_sample_network()
    
    # Claim: High degree implies high PageRank rank (top 2)
    # This should fail because A has high degree but low PageRank
    claim = "degree__ge(k) -> pagerank__rank_le(r)"
    params = {"k": 3, "r": 2}
    
    print(f"Claim: {claim}")
    print(f"Parameters: {params}")
    print()
    
    try:
        cex = (Q.counterexample()
                 .claim(claim)
                 .params(**params)
                 .seed(42)
                 .find_minimal(True)
                 .execute(net))
        
        print(cex.explain())
        
    except CounterexampleNotFound:
        print("No counterexample found - claim holds for this network")
    
    print()


def example_with_minimization():
    """Demonstrate minimization."""
    print("=" * 70)
    print("EXAMPLE 2: With Minimization")
    print("=" * 70)
    print()
    
    net = build_sample_network()
    
    claim = "degree__ge(k) -> pagerank__rank_le(r)"
    params = {"k": 3, "r": 2}
    
    print("Finding counterexample with minimization...")
    print()
    
    cex = (Q.counterexample()
             .claim(claim)
             .params(**params)
             .seed(42)
             .find_minimal(True)
             .budget(max_tests=100, max_witness_size=50)
             .execute(net))
    
    print(f"Initial witness: {cex.minimization.initial_edges} edges, "
          f"{cex.minimization.initial_nodes} nodes")
    print(f"Final witness: {cex.minimization.final_edges} edges, "
          f"{cex.minimization.final_nodes} nodes")
    print(f"Minimization tests used: {cex.minimization.tests_used}")
    print(f"Is minimal: {cex.minimization.is_minimal}")
    print()
    
    # Show witness subgraph
    print("Witness subgraph nodes:")
    for node in cex.witness_nodes:
        print(f"  {node}")
    print()


def example_query_result_integration():
    """Demonstrate QueryResult.counterexample() integration."""
    print("=" * 70)
    print("EXAMPLE 3: QueryResult Integration")
    print("=" * 70)
    print()
    
    net = build_sample_network()
    
    # First, run a regular query
    result = Q.nodes().compute("degree", "pagerank").execute(net)
    
    print("Query result (first 5 rows):")
    df = result.to_pandas()
    print(df.head())
    print()
    
    # Now find counterexample from result
    print("Finding counterexample from query result...")
    print()
    
    try:
        # Note: result.counterexample() requires network in meta (not always available)
        # So we use Q.counterexample() instead for this example
        cex = (Q.counterexample()
                 .claim("degree__ge(k) -> pagerank__rank_le(r)")
                 .params(k=3, r=2)
                 .seed(42)
                 .execute(net))
        
        print(f"Found violation at node: {cex.violation.node}")
        print(f"Layer: {cex.violation.layer}")
        print(f"Degree: {cex.violation.antecedent_values.get('degree', 'N/A')}")
        print(f"PageRank rank: {cex.violation.consequent_values.get('pagerank_rank', 'N/A')}")
        print()
    except CounterexampleNotFound:
        print("No counterexample found")


def example_determinism():
    """Demonstrate deterministic behavior."""
    print("=" * 70)
    print("EXAMPLE 4: Determinism")
    print("=" * 70)
    print()
    
    net = build_sample_network()
    
    claim = "degree__ge(k) -> pagerank__rank_le(r)"
    params = {"k": 3, "r": 2}
    
    print("Running counterexample generation twice with same seed...")
    print()
    
    cex1 = (Q.counterexample()
              .claim(claim)
              .params(**params)
              .seed(42)
              .find_minimal(False)
              .execute(net))
    
    cex2 = (Q.counterexample()
              .claim(claim)
              .params(**params)
              .seed(42)
              .find_minimal(False)
              .execute(net))
    
    print(f"Run 1 violating node: {cex1.violation.node}")
    print(f"Run 2 violating node: {cex2.violation.node}")
    print(f"Same violating node: {cex1.violation.node == cex2.violation.node}")
    print()
    
    print(f"Run 1 witness size: {len(cex1.witness_nodes)} nodes, {len(cex1.witness_edges)} edges")
    print(f"Run 2 witness size: {len(cex2.witness_nodes)} nodes, {len(cex2.witness_edges)} edges")
    print(f"Same witness size: {len(cex1.witness_nodes) == len(cex2.witness_nodes)}")
    print()


def example_provenance():
    """Demonstrate provenance tracking."""
    print("=" * 70)
    print("EXAMPLE 5: Provenance")
    print("=" * 70)
    print()
    
    net = build_sample_network()
    
    cex = (Q.counterexample()
             .claim("degree__ge(k) -> pagerank__rank_le(r)")
             .params(k=3, r=2)
             .seed(42)
             .execute(net))
    
    prov = cex.meta["provenance"]
    
    print("Provenance information:")
    print(f"  Engine: {prov['engine']}")
    print(f"  py3plex version: {prov['py3plex_version']}")
    print(f"  Timestamp: {prov['timestamp_utc']}")
    print(f"  Seed: {prov['randomness']['seed']}")
    print(f"  Claim hash: {prov['claim']['claim_hash'][:16]}...")
    print()
    
    print("Performance timings:")
    perf = prov['performance']
    print(f"  Find violation: {perf['find_violation_ms']:.2f} ms")
    print(f"  Extract witness: {perf['extract_witness_ms']:.2f} ms")
    print(f"  Minimize: {perf['minimize_ms']:.2f} ms")
    print(f"  Total: {perf['total_ms']:.2f} ms")
    print()


if __name__ == "__main__":
    example_basic()
    example_with_minimization()
    example_query_result_integration()
    example_determinism()
    example_provenance()
    
    print("=" * 70)
    print("All examples completed!")
    print("=" * 70)
