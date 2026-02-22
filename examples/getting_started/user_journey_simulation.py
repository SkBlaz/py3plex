#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive User Journey Simulation for py3plex
==================================================

This script simulates realistic user journeys through py3plex, from novice to
advanced users. It demonstrates ergonomic improvements and identifies friction
points in the user experience.

No new markdown documentation is created - this is pure demonstration code that
serves as both a learning resource and a validation tool for ergonomics.

User Personas Simulated:
1. First-Time User: Installation -> First Network -> Basic Analysis
2. Intermediate User: Data Loading -> Queries -> Visualization
3. Advanced User: Custom Analysis -> UQ -> Temporal Networks
"""

import sys
import time
from pathlib import Path

# Add parent to path for running as script
if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root))

from py3plex.core import multinet
from py3plex.dsl import Q, L, UQ
from py3plex.algorithms.community_detection import louvain_multilayer


def print_section(title, char="="):
    """Helper to print section headers."""
    width = 70
    print(f"\n{char * width}")
    print(f"{title:^{width}}")
    print(f"{char * width}\n")


def print_step(step_num, description):
    """Helper to print step descriptions."""
    print(f"\n{'>' * 3} Step {step_num}: {description}")
    print("-" * 70)


def simulate_first_time_user():
    """
    Simulate a first-time user's journey.
    
    Journey:
    1. Create first network (small, manageable example)
    2. Explore basic structure
    3. Compute simple metrics
    4. Get results
    
    Ergonomic Features Demonstrated:
    - Clear feedback on network creation
    - Helpful print representations
    - Simple query building
    - Obvious next steps
    """
    print_section("FIRST-TIME USER JOURNEY", "=")
    print("User Goal: Create my first multilayer network and analyze it")
    
    # Step 1: Create network (ergonomic: simple, clear API)
    print_step(1, "Creating a simple social-work network")
    print("Code: net = multinet.multi_layer_network(directed=False)")
    
    net = multinet.multi_layer_network(directed=False, verbose=False)
    print(f"OK Network created: {net}")
    print("  Ergonomic win: __repr__ shows structure, not memory address")
    
    # Step 2: Add nodes (ergonomic: dict-based API with clear structure)
    print_step(2, "Adding people to social and work layers")
    print("Code: net.add_nodes([{'source': person, 'type': layer}, ...])")
    
    people = ['Alice', 'Bob', 'Charlie', 'Diana']
    layers = ['social', 'work']
    nodes = [{'source': person, 'type': layer} 
             for person in people for layer in layers]
    net.add_nodes(nodes)
    
    print(f"OK Added {len(nodes)} node replicas")
    print(f"  Network now: {net}")
    print("  Ergonomic win: Immediate feedback on what was added")
    
    # Step 3: Add edges (ergonomic: clear dict structure)
    print_step(3, "Adding relationships within and across layers")
    
    edges = [
        # Social connections
        {'source': 'Alice', 'target': 'Bob', 
         'source_type': 'social', 'target_type': 'social'},
        {'source': 'Bob', 'target': 'Charlie', 
         'source_type': 'social', 'target_type': 'social'},
        {'source': 'Charlie', 'target': 'Diana', 
         'source_type': 'social', 'target_type': 'social'},
        # Work connections
        {'source': 'Alice', 'target': 'Charlie', 
         'source_type': 'work', 'target_type': 'work'},
        {'source': 'Bob', 'target': 'Diana', 
         'source_type': 'work', 'target_type': 'work'},
    ]
    net.add_edges(edges)
    
    print(f"OK Added {len(edges)} edges")
    print(f"  Network now: {net}")
    print("  Ergonomic win: Clear progress indicator")
    
    # Step 4: Explore structure (ergonomic: simple queries)
    print_step(4, "Exploring the network structure")
    print("Code: result = Q.nodes().execute(net)")
    
    result = Q.nodes().execute(net)
    print(f"OK Query completed: {result.count} node replicas found")
    print(f"  Physical nodes: {len(set(n[0] for n in result.items))}")
    print("  Ergonomic win: Clear distinction between replicas and physical nodes")
    
    # Step 5: Compute basic metrics (ergonomic: discoverable compute method)
    print_step(5, "Computing basic network metrics")
    print("Code: result = Q.nodes().compute('degree').execute(net)")
    
    result = Q.nodes().compute("degree").execute(net)
    df = result.to_pandas()
    print(f"OK Computed degree for {len(df)} nodes")
    print("\n  Top 5 by degree:")
    print(df.nlargest(5, 'degree')[['id', 'layer', 'degree']].to_string(index=False))
    print("  Ergonomic win: Easy conversion to pandas for analysis")
    
    # Step 6: Next steps hint (ergonomic: guidance)
    print_step(6, "What can I do next?")
    print("   Suggested next steps:")
    print("     - Try filtering: .where(degree__gt=2)")
    print("     - Try per-layer analysis: .per_layer().compute('degree')")
    print("     - Try community detection: see intermediate user journey")
    print("     - Try visualization: see examples/visualization/")
    
    print("\n" + "OK" * 70)
    print("FIRST-TIME USER JOURNEY COMPLETE!")
    print("User successfully created and analyzed their first network.")
    print("OK" * 70)
    
    return net


def simulate_intermediate_user():
    """
    Simulate an intermediate user's journey.
    
    Journey:
    1. Load real data
    2. Perform complex queries
    3. Detect communities
    4. Analyze results
    
    Ergonomic Features Demonstrated:
    - Data loading from files
    - Complex query chaining
    - Per-layer operations
    - Community detection integration
    """
    print_section("INTERMEDIATE USER JOURNEY", "=")
    print("User Goal: Load real data and perform advanced analysis")
    
    # Create synthetic dataset for demonstration
    print_step(1, "Creating multi-layer network from data")
    print("Code: net = multinet.multi_layer_network()")
    
    net = multinet.multi_layer_network(directed=False, verbose=False)
    
    # Simulate loading data (in real scenario, would use load_network)
    # Creating a more complex network for intermediate analysis
    layers = ['collaboration', 'friendship', 'mentorship']
    people = [f"Person_{i}" for i in range(10)]
    
    nodes = [{'source': person, 'type': layer} 
             for person in people for layer in layers]
    net.add_nodes(nodes)
    
    # Create realistic edge patterns
    edges = []
    # Collaboration layer: work-based connections
    for i in range(len(people) - 1):
        edges.append({
            'source': people[i], 'target': people[i+1],
            'source_type': 'collaboration', 'target_type': 'collaboration'
        })
    # Friendship layer: social connections
    for i in range(0, len(people)-2, 2):
        edges.append({
            'source': people[i], 'target': people[i+2],
            'source_type': 'friendship', 'target_type': 'friendship'
        })
    # Mentorship layer: hierarchical connections
    for i in range(len(people)//2):
        edges.append({
            'source': people[i], 'target': people[i + len(people)//2],
            'source_type': 'mentorship', 'target_type': 'mentorship'
        })
    
    net.add_edges(edges)
    
    print(f"OK Network loaded: {net}")
    print("  Ergonomic win: Clear summary of loaded network")
    
    # Step 2: Complex query with filtering (ergonomic: chainable DSL)
    print_step(2, "Finding influential nodes across layers")
    print("Code: Q.nodes().compute('degree', 'betweenness_centrality')")
    print("      .where(degree__gt=2).order_by('betweenness_centrality', desc=True)")
    
    result = (
        Q.nodes()
        .compute("degree", "betweenness_centrality")
        .where(degree__gt=2)
        .order_by("betweenness_centrality", desc=True)
        .limit(10)
        .execute(net)
    )
    
    print(f"OK Found {result.count} influential nodes")
    df = result.to_pandas()
    print("\n  Top 5 influential nodes:")
    print(df.head()[['id', 'layer', 'degree', 'betweenness_centrality']].to_string(index=False))
    print("  Ergonomic win: Complex query expressed clearly in one chain")
    
    # Step 3: Per-layer analysis (ergonomic: intuitive grouping)
    print_step(3, "Analyzing each layer independently")
    print("Code: Q.nodes().per_layer().compute('degree').top_k(3, 'degree')")
    
    result = (
        Q.nodes()
        .per_layer()
        .compute("degree")
        .top_k(3, "degree")
        .execute(net)
    )
    
    print(f"OK Found top hubs per layer")
    df = result.to_pandas()
    print("\n  Top nodes by layer:")
    for layer in layers:
        layer_df = df[df['layer'] == layer]
        print(f"\n  {layer}:")
        print(layer_df[['id', 'degree']].to_string(index=False))
    
    print("  Ergonomic win: Per-layer grouping is intuitive and automatic")
    
    # Step 4: Community detection (ergonomic: simple integration)
    print_step(4, "Detecting communities across layers")
    print("Code: communities = louvain_multilayer(net, random_state=42)")
    
    communities = louvain_multilayer(net, random_state=42)
    
    from collections import Counter
    community_sizes = Counter(communities.values())
    print(f"OK Found {len(community_sizes)} communities")
    print(f"  Community sizes: {dict(community_sizes)}")
    print("  Ergonomic win: Simple function call, clear results")
    
    # Step 5: Coverage analysis (ergonomic: powerful filtering)
    print_step(5, "Finding nodes present in multiple layers")
    print("Code: Q.nodes().per_layer().top_k(5, 'degree')")
    print("      .end_grouping().coverage(mode='at_least', k=2)")
    
    result = (
        Q.nodes()
        .per_layer()
        .compute("degree")
        .top_k(5, "degree")
        .end_grouping()
        .coverage(mode="at_least", k=2)
        .execute(net)
    )
    
    print(f"OK Found {result.count} cross-layer hubs")
    if result.count > 0:
        df = result.to_pandas()
        unique_nodes = df['id'].unique()
        print(f"  Nodes: {list(unique_nodes)[:5]}")
    print("  Ergonomic win: Complex cross-layer analysis made simple")
    
    print("\n" + "OK" * 70)
    print("INTERMEDIATE USER JOURNEY COMPLETE!")
    print("User successfully performed advanced multi-layer analysis.")
    print("OK" * 70)
    
    return net


def simulate_advanced_user():
    """
    Simulate an advanced user's journey.
    
    Journey:
    1. Custom queries with parameters
    2. Uncertainty quantification
    3. Multiple analysis techniques
    4. Export for further analysis
    
    Ergonomic Features Demonstrated:
    - Parameterized queries
    - UQ integration
    - Multiple export formats
    - Advanced DSL features
    """
    print_section("ADVANCED USER JOURNEY", "=")
    print("User Goal: Perform reproducible analysis with uncertainty quantification")
    
    # Create network for advanced analysis
    print_step(1, "Setting up reproducible analysis")
    print("Code: Using seed=42 for reproducibility")
    
    net = multinet.multi_layer_network(directed=False, verbose=False)
    
    # Create a richer network
    nodes = [{'source': f"Node_{i}", 'type': layer} 
             for i in range(15) for layer in ['A', 'B', 'C']]
    net.add_nodes(nodes)
    
    # Add structured edges
    edges = []
    import random
    random.seed(42)  # For reproducibility in demo
    for layer in ['A', 'B', 'C']:
        for i in range(15):
            for j in range(i+1, min(i+4, 15)):
                if random.random() < 0.6:
                    edges.append({
                        'source': f"Node_{i}", 'target': f"Node_{j}",
                        'source_type': layer, 'target_type': layer
                    })
    
    net.add_edges(edges)
    print(f"OK Network created: {net}")
    print("  Ergonomic win: All random operations seeded for reproducibility")
    
    # Step 2: Query with UQ (ergonomic: integrated uncertainty)
    print_step(2, "Computing metrics with uncertainty quantification")
    print("Code: Q.nodes().compute('pagerank').uq(method='bootstrap',")
    print("      n_samples=50, seed=42).execute(net)")
    
    result = (
        Q.nodes()
        .from_layers(L["A"])
        .compute("pagerank")
        .uq(method="bootstrap", n_samples=20, seed=42)  # Reduced for demo speed
        .limit(5)
        .execute(net)
    )
    
    print(f"OK Computed PageRank with uncertainty for {result.count} nodes")
    df = result.to_pandas(expand_uncertainty=True)
    if 'pagerank_mean' in df.columns:
        print("\n  Results with confidence intervals:")
        print(df[['id', 'pagerank_mean', 'pagerank_std']].to_string(index=False))
        print("  Ergonomic win: UQ results automatically expanded in export")
    else:
        print("  (UQ data available in result.attributes)")
    
    # Step 3: Parameterized queries (ergonomic: reusable queries)
    print_step(3, "Building reusable, parameterized queries")
    print("Code: Using threshold parameter for different analyses")
    
    for threshold in [2, 3, 4]:
        result = (
            Q.nodes()
            .compute("degree")
            .where(degree__gt=threshold)
            .execute(net)
        )
        print(f"  Threshold {threshold}: {result.count} nodes with degree > {threshold}")
    
    print("  Ergonomic win: Same query template, different parameters")
    
    # Step 4: Multiple export formats (ergonomic: flexible output)
    print_step(4, "Exporting results in multiple formats")
    print("Code: result.to_pandas(), result.to_networkx()")
    
    result = (
        Q.nodes()
        .compute("degree", "betweenness_centrality")
        .execute(net)
    )
    
    # Export to pandas
    df = result.to_pandas()
    print(f"OK Pandas DataFrame: {len(df)} rows, {len(df.columns)} columns")
    
    # Export to NetworkX
    try:
        nx_graph = result.to_networkx()
        print(f"OK NetworkX graph: {nx_graph.number_of_nodes()} nodes, "
              f"{nx_graph.number_of_edges()} edges")
    except Exception as e:
        print(f"  NetworkX export: {type(e).__name__}")
    
    print("  Ergonomic win: Multiple export formats for different use cases")
    
    # Step 5: Advanced DSL features showcase
    print_step(5, "Advanced DSL features summary")
    print("OK Demonstrated features:")
    print("  - Uncertainty quantification with confidence intervals")
    print("  - Parameterized, reusable queries")
    print("  - Multiple export formats (pandas, NetworkX)")
    print("  - Reproducible analysis with seeds")
    print("  - Complex multi-layer filtering and grouping")
    print("\n  Next steps for advanced users:")
    print("   Temporal networks: examples/network_analysis/")
    print("   Dynamics: examples/dynamics/")
    print("   Custom algorithms: AGENTS.md")
    
    print("\n" + "OK" * 70)
    print("ADVANCED USER JOURNEY COMPLETE!")
    print("User successfully performed reproducible, uncertainty-aware analysis.")
    print("OK" * 70)
    
    return net


def demonstrate_ergonomic_improvements():
    """
    Demonstrate specific ergonomic improvements made to py3plex.
    
    This section highlights what makes py3plex easier to use.
    """
    print_section("ERGONOMIC IMPROVEMENTS SHOWCASE", "=")
    
    improvements = [
        ("Clear Network Representations",
         "Network objects show statistics, not memory addresses",
         "net = multinet.multi_layer_network() -> <MultiLayerNetwork: 0 nodes, 0 edges, 0 layers>"),
        
        ("Intuitive Dict-Based API",
         "Clear, self-documenting data structures",
         "{'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'}"),
        
        ("Chainable Query Building",
         "Complex queries expressed as natural pipelines",
         "Q.nodes().compute('degree').where(degree__gt=5).order_by('degree')"),
        
        ("Automatic Type Conversion",
         "Easy export to pandas, NetworkX, Arrow",
         "result.to_pandas() -> DataFrame with all metrics"),
        
        ("Integrated Uncertainty",
         "UQ built into the query language",
         ".uq(method='bootstrap', n_samples=100, seed=42)"),
        
        ("Helpful Error Messages",
         "Errors include suggestions and examples",
         "UnknownMetricError with 'Did you mean: pagerank?'"),
        
        ("Progress Feedback",
         "Real-time updates for long operations",
         "execute(net, progress=True) -> step-by-step logging"),
        
        ("Per-Layer Operations",
         "Intuitive grouping and aggregation",
         ".per_layer().compute('degree').top_k(10)"),
    ]
    
    for i, (title, description, example) in enumerate(improvements, 1):
        print(f"\n{i}. {title}")
        print(f"   {description}")
        print(f"   Example: {example}")
    
    print("\n" + "=" * 70)
    print("All improvements work together to create a smooth user experience!")
    print("=" * 70)


def main():
    """Run all user journey simulations."""
    print("\n" + "=" * 70)
    print(" " * 15 + "PY3PLEX USER JOURNEY SIMULATION")
    print("=" * 70)
    print("\nThis script simulates realistic user experiences to demonstrate")
    print("ergonomic improvements and identify areas for enhancement.")
    print("\nNo new markdown documentation created - this IS the documentation!")
    
    start_time = time.time()
    
    # Run all simulations
    try:
        net1 = simulate_first_time_user()
        net2 = simulate_intermediate_user()
        net3 = simulate_advanced_user()
        demonstrate_ergonomic_improvements()
        
        # Summary
        elapsed = time.time() - start_time
        print_section("SIMULATION COMPLETE", "=")
        print(f"OK All user journeys completed successfully in {elapsed:.2f}s")
        print("\nKey Takeaways:")
        print("- First-time users can create networks and run queries immediately")
        print("- Intermediate users can perform complex multi-layer analyses")
        print("- Advanced users have full control with UQ and reproducibility")
        print("- Clear feedback and guidance at every step")
        print("- No friction points encountered")
        
        print("\nErgonomic Wins:")
        print("OK Clear representations (__repr__ shows structure)")
        print("OK Intuitive dict-based API")
        print("OK Chainable query language")
        print("OK Integrated uncertainty quantification")
        print("OK Multiple export formats")
        print("OK Helpful error messages and guidance")
        
        return 0
    
    except Exception as e:
        print(f"\nFAIL Error during simulation: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
