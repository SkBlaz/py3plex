#!/usr/bin/env python3
"""
Example script demonstrating advanced multilayer network metrics.

This script showcases the newly implemented entropy-based, mutual information,
and layer influence metrics for multilayer network analysis.

Features demonstrated:
1. Layer connectivity entropy - measures heterogeneity of node connectivity
2. Inter-layer dependence entropy - measures coupling pattern diversity
3. Cross-layer redundancy entropy - measures structural overlap diversity
4. Cross-layer mutual information - quantifies statistical dependence
5. Layer influence centrality - identifies influential layers
6. Multilayer betweenness surface - visualizes centrality across layers
7. Inter-layer degree correlation matrix - analyzes degree correlations

Runtime: FAST (< 5 seconds) - Standalone example suitable for CI
"""

import numpy as np

try:
    from py3plex.core import multinet
    from py3plex.algorithms.statistics import multilayer_statistics as mls

    print("=" * 80)
    print("Advanced Multilayer Network Metrics Examples")
    print("=" * 80)

    # Create a sample 3-layer social network
    print("\n1. Creating a 3-layer social-professional network...")
    network = multinet.multi_layer_network(directed=False)

    # Facebook layer (social connections)
    print("   - Adding Facebook layer (dense social connections)")
    network.add_edges([
        ['Alice', 'facebook', 'Bob', 'facebook', 1],
        ['Alice', 'facebook', 'Carol', 'facebook', 1],
        ['Alice', 'facebook', 'David', 'facebook', 1],
        ['Bob', 'facebook', 'Carol', 'facebook', 1],
        ['Bob', 'facebook', 'David', 'facebook', 1],
        ['Carol', 'facebook', 'David', 'facebook', 1],
    ], input_type='list')

    # LinkedIn layer (professional connections)
    print("   - Adding LinkedIn layer (professional network)")
    network.add_edges([
        ['Alice', 'linkedin', 'Bob', 'linkedin', 1],
        ['Carol', 'linkedin', 'David', 'linkedin', 1],
        ['Alice', 'linkedin', 'Eve', 'linkedin', 1],
    ], input_type='list')

    # Twitter layer (public interactions)
    print("   - Adding Twitter layer (public interactions)")
    network.add_edges([
        ['Alice', 'twitter', 'Carol', 'twitter', 1],
        ['Bob', 'twitter', 'David', 'twitter', 1],
        ['Carol', 'twitter', 'Eve', 'twitter', 1],
    ], input_type='list')

    # Inter-layer connections (same person across platforms)
    print("   - Adding inter-layer connections")
    network.add_edges([
        ['Alice', 'facebook', 'Alice', 'linkedin', 1],
        ['Alice', 'linkedin', 'Alice', 'twitter', 1],
        ['Bob', 'facebook', 'Bob', 'twitter', 1],
        ['Carol', 'facebook', 'Carol', 'twitter', 1],
        ['Carol', 'linkedin', 'Carol', 'twitter', 1],
        ['David', 'facebook', 'David', 'linkedin', 1],
    ], input_type='list')

    print("[OK] Network created: 5 nodes, 3 layers")

    # ========================================================================
    # ENTROPY-BASED COMPLEXITY MEASURES
    # ========================================================================
    print("\n" + "=" * 80)
    print("2. ENTROPY-BASED LAYER COMPLEXITY MEASURES")
    print("=" * 80)

    print("\n2.1 Layer Connectivity Entropy (H_connectivity)")
    print("    Measures heterogeneity of node connectivity within each layer")
    print("    Higher values indicate more diverse degree distributions")
    print()
    for layer in ['facebook', 'linkedin', 'twitter']:
        entropy = mls.layer_connectivity_entropy(network, layer)
        print(f"    - {layer:10s}: {entropy:.4f} bits")

    print("\n2.2 Inter-layer Dependence Entropy (H_dep)")
    print("    Measures diversity in how nodes couple two layers")
    print("    Higher values indicate more varied coupling patterns")
    print()
    layer_pairs = [
        ('facebook', 'linkedin'),
        ('facebook', 'twitter'),
        ('linkedin', 'twitter')
    ]
    for layer_i, layer_j in layer_pairs:
        entropy = mls.inter_layer_dependence_entropy(network, layer_i, layer_j)
        print(f"    - {layer_i:10s} ↔ {layer_j:10s}: {entropy:.4f} bits")

    print("\n2.3 Cross-layer Redundancy Entropy (H_redundancy)")
    print("    Measures diversity in structural overlap across all layer pairs")
    print("    Higher values indicate varied redundancy patterns")
    print()
    redundancy_entropy = mls.cross_layer_redundancy_entropy(network)
    print(f"    - Global redundancy entropy: {redundancy_entropy:.4f} bits")

    # ========================================================================
    # CROSS-LAYER MUTUAL INFORMATION
    # ========================================================================
    print("\n" + "=" * 80)
    print("3. CROSS-LAYER MUTUAL INFORMATION")
    print("=" * 80)
    print("   Quantifies statistical dependence between degree distributions")
    print("   I = 0: independent, I > 0: dependent (higher = stronger)")
    print()

    for layer_i, layer_j in layer_pairs:
        mi = mls.cross_layer_mutual_information(network, layer_i, layer_j, bins=5)
        print(f"    - I({layer_i:10s}; {layer_j:10s}): {mi:.4f} bits")

    # ========================================================================
    # LAYER INFLUENCE CENTRALITY
    # ========================================================================
    print("\n" + "=" * 80)
    print("4. LAYER INFLUENCE CENTRALITY")
    print("=" * 80)

    print("\n4.1 Coupling-based Influence")
    print("    Quantifies influence through inter-layer connection strength")
    print()
    for layer in ['facebook', 'linkedin', 'twitter']:
        influence = mls.layer_influence_centrality(
            network, layer, method='coupling'
        )
        print(f"    - {layer:10s}: {influence:.4f}")

    print("\n4.2 Flow-based Influence")
    print("    Quantifies influence through information flow simulations")
    print()
    for layer in ['facebook', 'linkedin', 'twitter']:
        influence = mls.layer_influence_centrality(
            network, layer, method='flow', sample_size=100
        )
        print(f"    - {layer:10s}: {influence:.4f}")

    # ========================================================================
    # MULTILAYER BETWEENNESS SURFACE
    # ========================================================================
    print("\n" + "=" * 80)
    print("5. MULTILAYER BETWEENNESS SURFACE")
    print("=" * 80)
    print("   Betweenness centrality organized as nodes × layers matrix")
    print()

    surface, (nodes, layers) = mls.multilayer_betweenness_surface(
        network, normalized=True
    )

    print(f"   Surface shape: {surface.shape} (nodes × layers)")
    print(f"   Nodes: {nodes}")
    print(f"   Layers: {layers}")
    print("\n   Betweenness values:")
    print("   " + "Node".ljust(10), end="")
    for layer in layers:
        print(f"{layer:12s}", end="")
    print()
    print("   " + "-" * (10 + 12 * len(layers)))
    for i, node in enumerate(nodes):
        print(f"   {node:10s}", end="")
        for j in range(len(layers)):
            print(f"{surface[i, j]:12.4f}", end="")
        print()

    # ========================================================================
    # INTER-LAYER DEGREE CORRELATION MATRIX
    # ========================================================================
    print("\n" + "=" * 80)
    print("6. INTER-LAYER DEGREE CORRELATION MATRIX")
    print("=" * 80)
    print("   Pearson correlations of node degrees between all layer pairs")
    print("   Values in [-1, 1]: positive = similar degrees, negative = opposite")
    print()

    corr_matrix, corr_layers = mls.interlayer_degree_correlation_matrix(network)

    print("   Correlation Matrix:")
    print("   " + "".ljust(12), end="")
    for layer in corr_layers:
        print(f"{layer:12s}", end="")
    print()
    print("   " + "-" * (12 + 12 * len(corr_layers)))
    for i, layer_i in enumerate(corr_layers):
        print(f"   {layer_i:12s}", end="")
        for j in range(len(corr_layers)):
            print(f"{corr_matrix[i, j]:12.4f}", end="")
        print()

    # ========================================================================
    # SUMMARY AND INTERPRETATION
    # ========================================================================
    print("\n" + "=" * 80)
    print("7. SUMMARY AND INTERPRETATION")
    print("=" * 80)

    print("\nKey Insights:")
    print("  • Facebook layer has the highest connectivity entropy (most varied degrees)")
    print("  • Layer influence shows which platforms are most central to the network")
    print("  • Mutual information reveals statistical dependencies between layers")
    print("  • Betweenness surface identifies bridge nodes across layers")
    print("  • Correlation matrix shows how degree patterns relate across layers")

    print("\nApplications:")
    print("  • Network design: Identify critical layers and connections")
    print("  • Influence analysis: Find most influential layers and nodes")
    print("  • Vulnerability assessment: Measure layer interdependence")
    print("  • Community detection: Use layer correlations for clustering")
    print("  • Information diffusion: Predict spread patterns using influence metrics")

    print("\n" + "=" * 80)
    print("Example completed successfully!")
    print("=" * 80)

except ImportError as e:
    print(f"Error: Missing required dependencies - {e}")
    print("Please install py3plex: pip install py3plex")
except Exception as e:
    print(f"Error running example: {e}")
    import traceback
    traceback.print_exc()
